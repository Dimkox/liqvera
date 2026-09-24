"""Classify a sealed frozen package into the closed Stage A decision set."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

from mee_contracts.decision import StageADecision, StageADecisionCode, StageAReasonCode
from mee_contracts.economics import SealedStageAEconomics
from mee_contracts.evidence import CaptureManifest, CaptureTerminal, QualityMinuteRecord
from mee_contracts.exact import ExactDecimal, ExactError

from mee_readonly_analyzer.frozen_package.reader import FrozenPackageEvidenceReader
from mee_readonly_analyzer.frozen_package.types import (
    FrozenPackageError,
    FrozenPackageErrorCode,
)
from mee_readonly_analyzer.identity import IdentityBindError, bind_reconstructed_books
from mee_readonly_analyzer.reconstruction import ReconstructionError, reconstruct_books

_MS_PER_MINUTE = 60_000
_MS_PER_DAY = 86_400_000
_MINUTES_PER_DAY = 1_440
_REQUIRED_ACQUISITION_DAYS = 7
_REQUIRED_COMPLETE_UTC_DAYS = 5
_REQUIRED_HEALTHY_RATIO = 95
_REQUIRED_INDEPENDENT_EPISODES = 20
_REQUIRED_WINDOW_MS = _REQUIRED_ACQUISITION_DAYS * _MS_PER_DAY
_REQUIRED_WINDOW_MINUTES = _REQUIRED_ACQUISITION_DAYS * _MINUTES_PER_DAY
_ZERO = ExactDecimal(0)
_CONCENTRATION_LIMIT = ExactDecimal.parse("0.25")
_ECONOMICS_MEMBER = "economics.json"

_ERROR_TO_REASON = {
    FrozenPackageErrorCode.INVALID_ARGUMENT: StageAReasonCode.INVALID_PATH,
    FrozenPackageErrorCode.MANIFEST_MISSING: StageAReasonCode.INVALID_MANIFEST,
    FrozenPackageErrorCode.MANIFEST_NON_CANONICAL: StageAReasonCode.INVALID_MANIFEST,
    FrozenPackageErrorCode.MANIFEST_HASH_INVALID: StageAReasonCode.INVALID_MANIFEST,
    FrozenPackageErrorCode.MANIFEST_HASH_MISMATCH: StageAReasonCode.INVALID_MANIFEST,
    FrozenPackageErrorCode.UNSUPPORTED_VERSION: StageAReasonCode.INVALID_UNSUPPORTED_VERSION,
    FrozenPackageErrorCode.MEMBER_SET_MISMATCH: StageAReasonCode.INVALID_MEMBER_SET_MISMATCH,
    FrozenPackageErrorCode.MEMBER_HASH_MISMATCH: StageAReasonCode.INVALID_MEMBER_HASH_MISMATCH,
    FrozenPackageErrorCode.MEMBER_HASH_INVALID: StageAReasonCode.INVALID_MEMBER_HASH_MISMATCH,
    FrozenPackageErrorCode.SYMLINK_FORBIDDEN: StageAReasonCode.INVALID_SYMLINK,
    FrozenPackageErrorCode.PATH_INVALID: StageAReasonCode.INVALID_PATH,
    FrozenPackageErrorCode.RECORD_INVALID: StageAReasonCode.INVALID_RECORD,
    FrozenPackageErrorCode.RUN_MISMATCH: StageAReasonCode.INVALID_RECORD,
}


def _map_error(code: FrozenPackageErrorCode) -> StageAReasonCode:
    try:
        return _ERROR_TO_REASON[code]
    except KeyError as error:
        raise RuntimeError(f"unmapped frozen-package error {code}") from error


def _invalid(code: FrozenPackageErrorCode, capture_run_id: UUID | None) -> StageADecision:
    return StageADecision(
        decision=StageADecisionCode.INVALID_DATASET,
        reasons=(_map_error(code),),
        capture_run_id=capture_run_id,
    )


def _complete_utc_days(minutes: tuple[QualityMinuteRecord, ...]) -> int:
    covered: dict[int, set[int]] = {}
    for record in minutes:
        day = record.minute_start_ms // _MS_PER_DAY
        minute_of_day = (record.minute_start_ms // _MS_PER_MINUTE) % _MINUTES_PER_DAY
        covered.setdefault(day, set()).add(minute_of_day)
    return sum(1 for indexes in covered.values() if len(indexes) >= _MINUTES_PER_DAY)


def _strict_healthy_minutes(minutes: tuple[QualityMinuteRecord, ...]) -> int:
    seen: set[tuple[int, str]] = set()
    healthy = 0
    for record in minutes:
        key = (record.minute_start_ms, record.venue)
        if key in seen:
            continue
        seen.add(key)
        if record.accepted > 0 and record.rejected == 0:
            healthy += 1
    return healthy


def _insufficiency_reasons(
    manifest: CaptureManifest,
    terminal: CaptureTerminal,
    minutes: tuple[QualityMinuteRecord, ...],
    independent_episodes: int,
) -> tuple[StageAReasonCode, ...]:
    reasons: list[StageAReasonCode] = []
    window_ms = terminal.terminated_at_ms - manifest.started_at_ms
    if window_ms < _REQUIRED_WINDOW_MS:
        reasons.append(StageAReasonCode.INSUFFICIENT_ACQUISITION_WINDOW)
    if _complete_utc_days(minutes) < _REQUIRED_COMPLETE_UTC_DAYS:
        reasons.append(StageAReasonCode.INSUFFICIENT_COMPLETE_UTC_DAYS)
    healthy = _strict_healthy_minutes(minutes)
    if healthy * 100 < _REQUIRED_HEALTHY_RATIO * _REQUIRED_WINDOW_MINUTES:
        reasons.append(StageAReasonCode.INSUFFICIENT_STRICT_HEALTHY_MINUTES)
    if independent_episodes < _REQUIRED_INDEPENDENT_EPISODES:
        reasons.append(StageAReasonCode.INSUFFICIENT_INDEPENDENT_EPISODES)
    return tuple(reasons)


def _stop_reasons(economics: SealedStageAEconomics) -> tuple[StageAReasonCode, ...]:
    reasons: list[StageAReasonCode] = []
    if economics.total_net <= _ZERO:
        reasons.append(StageAReasonCode.STOP_TOTAL_NET_NON_POSITIVE)
    if economics.median_net <= _ZERO:
        reasons.append(StageAReasonCode.STOP_MEDIAN_NET_NON_POSITIVE)
    if economics.usd_1000_net <= _ZERO:
        reasons.append(StageAReasonCode.STOP_USD_1000_NET_NON_POSITIVE)
    if economics.usd_5000_net < _ZERO:
        reasons.append(StageAReasonCode.STOP_USD_5000_NET_NEGATIVE)
    if economics.survived_delay_300ms is not True:
        reasons.append(StageAReasonCode.STOP_DELAY_300MS_NOT_SURVIVED)
    if economics.survived_delay_500ms is not True:
        reasons.append(StageAReasonCode.STOP_DELAY_500MS_NOT_SURVIVED)
    if economics.survived_both_fee_cases is not True:
        reasons.append(StageAReasonCode.STOP_FEE_CASE_NOT_SURVIVED)
    if not (economics.largest_episode_concentration < _CONCENTRATION_LIMIT):
        reasons.append(StageAReasonCode.STOP_CONCENTRATION_NOT_BELOW_25_PERCENT)
    return tuple(reasons)


def _decode_economics(raw: bytes) -> SealedStageAEconomics:
    return SealedStageAEconomics.from_document(json.loads(raw.decode("utf-8")))


def evaluate_frozen_package(root: Path) -> StageADecision:
    """Read a sealed package and return one closed Stage A decision."""
    try:
        reader = FrozenPackageEvidenceReader(root)
    except FrozenPackageError as error:
        return _invalid(error.code, None)
    run_id = reader.capture_run_id
    try:
        manifest = reader.read_capture_manifest(run_id)
        terminal = reader.capture_terminal(run_id)
        _ = tuple(reader.iter_control_evidence(run_id))
        _ = tuple(reader.iter_raw_batches(run_id))
        envelopes = tuple(reader.iter_raw_envelopes(run_id))
        minutes = tuple(reader.iter_quality_minutes(run_id))
        mapping_snapshot = reader.read_mapping_snapshot(run_id)
    except FrozenPackageError as error:
        return _invalid(error.code, run_id)
    try:
        books = reconstruct_books(envelopes, mapping_snapshot.mappings)
        bind_reconstructed_books(books, mapping_snapshot.mappings)
    except ReconstructionError:
        return _invalid(FrozenPackageErrorCode.RECORD_INVALID, run_id)
    except IdentityBindError:
        return _invalid(FrozenPackageErrorCode.RECORD_INVALID, run_id)
    except (UnicodeDecodeError, json.JSONDecodeError, ExactError):
        return _invalid(FrozenPackageErrorCode.RECORD_INVALID, run_id)
    raw = reader.optional_member_bytes(_ECONOMICS_MEMBER)
    economics: SealedStageAEconomics | None = None
    if raw is not None:
        try:
            economics = _decode_economics(raw)
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
            TypeError,
            ValueError,
            ExactError,
        ):
            return _invalid(FrozenPackageErrorCode.RECORD_INVALID, run_id)
    episodes = 0 if economics is None else economics.independent_episode_count
    insufficient = _insufficiency_reasons(manifest, terminal, minutes, episodes)
    if insufficient:
        return StageADecision(
            decision=StageADecisionCode.INSUFFICIENT_EVIDENCE,
            reasons=insufficient,
            capture_run_id=run_id,
        )
    if economics is None:
        raise RuntimeError("STOP/EXTEND reached without sealed economics")
    stop = _stop_reasons(economics)
    if stop:
        return StageADecision(
            decision=StageADecisionCode.STOP,
            reasons=stop,
            capture_run_id=run_id,
        )
    return StageADecision(
        decision=StageADecisionCode.EXTEND_LONGER_SHADOW,
        reasons=(StageAReasonCode.EXTEND_ALL_V2_GATES_PASS,),
        capture_run_id=run_id,
    )
