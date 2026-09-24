"""Fail-closed FrozenPackageEvidenceReader.

Rewritten from PR #21 `_frozen_reader.py` onto `mee_contracts.evidence`.
The package contains no writer and opens no network sockets.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from decimal import Decimal, InvalidOperation
from pathlib import Path
from uuid import UUID

from mee_contracts.evidence import (
    CaptureManifest,
    CaptureTerminal,
    ControlEvidenceRecord,
    EvidenceReader,
    MappingSnapshot,
    QualityMinuteRecord,
    RawBatchRecord,
    RawPublicEnvelope,
)
from mee_contracts.market import InstrumentIdentity
from mee_contracts.provenance import MappingDecision, MarketMappingEvidence

from mee_readonly_analyzer.frozen_package.codec import (
    canonical_json_bytes,
    decode_canonical_json,
    hash_file,
    require_relative_member,
    scan_regular_files,
    sha256_bytes,
)
from mee_readonly_analyzer.frozen_package.types import (
    PACKAGE_SCHEMA,
    FrozenPackageError,
    FrozenPackageErrorCode,
)

_REQUIRED_MEMBERS = (
    "control_evidence/records.ndjson",
    "raw_batches/0.bin",
    "raw_envelopes/records.ndjson",
    "quality_minutes/records.ndjson",
    "mapping_snapshot.json",
    "terminal.json",
)


class FrozenPackageEvidenceReader:
    """Read a package only after complete fail-closed structural verification."""

    def __init__(self, root: Path) -> None:
        if not isinstance(root, Path) or not root.exists() or not root.is_dir():
            raise FrozenPackageError(FrozenPackageErrorCode.MANIFEST_MISSING)
        if root.is_symlink():
            raise FrozenPackageError(FrozenPackageErrorCode.SYMLINK_FORBIDDEN)
        manifest_path = root / "manifest.json"
        if not manifest_path.exists() or not manifest_path.is_file():
            raise FrozenPackageError(FrozenPackageErrorCode.MANIFEST_MISSING)
        if manifest_path.is_symlink():
            raise FrozenPackageError(FrozenPackageErrorCode.SYMLINK_FORBIDDEN)
        document = decode_canonical_json(manifest_path.read_bytes())
        if type(document) is not dict:
            raise FrozenPackageError(FrozenPackageErrorCode.MANIFEST_NON_CANONICAL)
        if document.get("schema") != PACKAGE_SCHEMA:
            raise FrozenPackageError(FrozenPackageErrorCode.UNSUPPORTED_VERSION)
        manifest_hash = document.get("manifest_sha256")
        if type(manifest_hash) is not str or len(manifest_hash) != 64:
            raise FrozenPackageError(FrozenPackageErrorCode.MANIFEST_HASH_INVALID)
        unsigned = dict(document)
        del unsigned["manifest_sha256"]
        if sha256_bytes(canonical_json_bytes(unsigned)) != manifest_hash:
            raise FrozenPackageError(FrozenPackageErrorCode.MANIFEST_HASH_MISMATCH)
        members = document.get("members")
        if type(members) is not list or not members:
            raise FrozenPackageError(FrozenPackageErrorCode.MEMBER_SET_MISMATCH)
        declared: dict[str, str] = {}
        for item in members:
            if type(item) is not dict:
                raise FrozenPackageError(FrozenPackageErrorCode.MEMBER_SET_MISMATCH)
            path = item.get("path")
            digest = item.get("sha256")
            if type(path) is not str or type(digest) is not str:
                raise FrozenPackageError(FrozenPackageErrorCode.MEMBER_HASH_INVALID)
            require_relative_member(path)
            if path == "manifest.json" or path in declared:
                raise FrozenPackageError(FrozenPackageErrorCode.MEMBER_SET_MISMATCH)
            if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
                raise FrozenPackageError(FrozenPackageErrorCode.MEMBER_HASH_INVALID)
            declared[path] = digest
        missing_required = [path for path in _REQUIRED_MEMBERS if path not in declared]
        if missing_required:
            raise FrozenPackageError(FrozenPackageErrorCode.MEMBER_SET_MISMATCH)
        found = scan_regular_files(root)
        expected = set(declared) | {"manifest.json"}
        if found != expected:
            raise FrozenPackageError(FrozenPackageErrorCode.MEMBER_SET_MISMATCH)
        for path, digest in declared.items():
            member = root / path
            if member.is_symlink():
                raise FrozenPackageError(FrozenPackageErrorCode.SYMLINK_FORBIDDEN)
            if hash_file(member) != digest:
                raise FrozenPackageError(FrozenPackageErrorCode.MEMBER_HASH_MISMATCH)
        try:
            run_id = UUID(str(document["capture_run_id"]))
        except (KeyError, ValueError) as error:
            raise FrozenPackageError(FrozenPackageErrorCode.RECORD_INVALID) from error
        self._root = root
        self._run_id = run_id
        self._document = document
        self._declared = declared

    @property
    def capture_run_id(self) -> UUID:
        return self._run_id

    def optional_member_bytes(self, relative: str) -> bytes | None:
        if relative not in self._declared:
            return None
        return (self._root / relative).read_bytes()

    def _require_run(self, capture_run_id: UUID) -> None:
        if capture_run_id != self._run_id:
            raise FrozenPackageError(FrozenPackageErrorCode.RUN_MISMATCH)

    def read_capture_manifest(self, capture_run_id: UUID) -> CaptureManifest:
        self._require_run(capture_run_id)
        venues = self._document.get("venue_set")
        if type(venues) is not list or not venues or any(type(item) is not str for item in venues):
            raise FrozenPackageError(FrozenPackageErrorCode.RECORD_INVALID)
        started = self._document.get("started_at_ms")
        if type(started) is not int:
            raise FrozenPackageError(FrozenPackageErrorCode.RECORD_INVALID)
        return CaptureManifest(
            capture_run_id=self._run_id,
            started_at_ms=started,
            venue_set=tuple(venues),
            schema_version=PACKAGE_SCHEMA,
        )

    def capture_terminal(self, capture_run_id: UUID) -> CaptureTerminal:
        self._require_run(capture_run_id)
        payload = json.loads((self._root / "terminal.json").read_text(encoding="utf-8"))
        return CaptureTerminal(
            capture_run_id=self._run_id,
            terminated_at_ms=int(payload["terminated_at_ms"]),
            status=str(payload["status"]),
        )

    def iter_control_evidence(self, capture_run_id: UUID) -> Iterator[ControlEvidenceRecord]:
        self._require_run(capture_run_id)
        for row in _read_ndjson(self._root / "control_evidence/records.ndjson"):
            yield ControlEvidenceRecord(
                capture_run_id=self._run_id,
                recorded_at_ms=int(row["recorded_at_ms"]),
                kind=str(row["kind"]),
                payload_sha256=str(row["payload_sha256"]),
            )

    def iter_raw_batches(self, capture_run_id: UUID) -> Iterator[RawBatchRecord]:
        self._require_run(capture_run_id)
        payload = (self._root / "raw_batches/0.bin").read_bytes()
        digest = sha256_bytes(payload)
        yield RawBatchRecord(
            capture_run_id=self._run_id,
            batch_index=0,
            stored_sha256=digest,
            content_sha256=digest,
            payload=payload,
        )

    def iter_raw_envelopes(self, capture_run_id: UUID) -> Iterator[RawPublicEnvelope]:
        self._require_run(capture_run_id)
        for row in _read_ndjson(self._root / "raw_envelopes/records.ndjson"):
            body = bytes.fromhex(str(row["payload_hex"]))
            yield RawPublicEnvelope(
                capture_run_id=self._run_id,
                envelope_index=int(row["envelope_index"]),
                observed_at_ms=int(row["observed_at_ms"]),
                venue=str(row["venue"]),
                payload_sha256=sha256_bytes(body),
                payload=body,
            )

    def iter_quality_minutes(self, capture_run_id: UUID) -> Iterator[QualityMinuteRecord]:
        self._require_run(capture_run_id)
        for row in _read_ndjson(self._root / "quality_minutes/records.ndjson"):
            yield QualityMinuteRecord(
                capture_run_id=self._run_id,
                minute_start_ms=int(row["minute_start_ms"]),
                venue=str(row["venue"]),
                accepted=int(row["accepted"]),
                rejected=int(row["rejected"]),
            )

    def read_mapping_snapshot(self, capture_run_id: UUID) -> MappingSnapshot:
        self._require_run(capture_run_id)
        raw = (self._root / "mapping_snapshot.json").read_bytes()
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise FrozenPackageError(FrozenPackageErrorCode.RECORD_INVALID) from error
        if type(payload) is not dict or set(payload) != {"mappings"}:
            raise FrozenPackageError(FrozenPackageErrorCode.RECORD_INVALID)
        rows = payload["mappings"]
        if type(rows) is not list:
            raise FrozenPackageError(FrozenPackageErrorCode.RECORD_INVALID)
        try:
            mappings = tuple(_mapping_from_document(item) for item in rows)
        except (TypeError, ValueError, KeyError, InvalidOperation) as error:
            raise FrozenPackageError(FrozenPackageErrorCode.RECORD_INVALID) from error
        return MappingSnapshot(
            capture_run_id=self._run_id,
            mappings=mappings,
            snapshot_sha256=sha256_bytes(raw),
        )


_IDENTITY_KEYS = frozenset(
    {
        "base_asset",
        "quote_asset",
        "product_kind",
        "settlement_asset",
        "payoff_kind",
    }
)
_MAPPING_KEYS = frozenset(
    {
        "mapping_id",
        "mapping_version",
        "decision",
        "venue",
        "symbol",
        "identity",
        "evidence_sha256",
        "evidence_reference",
        "valid_from_ms",
        "valid_until_ms",
        "reviewed_contract_multiplier",
        "displayed_size_unit",
        "quantity_step",
        "price_tick",
        "price_decimals",
        "max_price_significant_digits",
        "min_quantity",
        "min_notional",
    }
)
_OPTIONAL_MAPPING_KEYS = frozenset({"lighter_market_index"})


def _require_exact_keys(item: object, keys: frozenset[str]) -> dict[str, object]:
    if type(item) is not dict or set(item) != keys:
        raise FrozenPackageError(FrozenPackageErrorCode.RECORD_INVALID)
    return item


def _decimal_string(value: object) -> Decimal:
    if type(value) is not str:
        raise FrozenPackageError(FrozenPackageErrorCode.RECORD_INVALID)
    return Decimal(value)


def _optional_decimal_string(value: object) -> Decimal | None:
    if value is None:
        return None
    return _decimal_string(value)


def _mapping_from_document(item: object) -> MarketMappingEvidence:
    if type(item) is not dict:
        raise FrozenPackageError(FrozenPackageErrorCode.RECORD_INVALID)
    keys = set(item)
    if not (_MAPPING_KEYS <= keys <= (_MAPPING_KEYS | _OPTIONAL_MAPPING_KEYS)):
        raise FrozenPackageError(FrozenPackageErrorCode.RECORD_INVALID)
    row = item
    identity_raw = _require_exact_keys(row["identity"], _IDENTITY_KEYS)
    identity = InstrumentIdentity(
        base_asset=str(identity_raw["base_asset"]),
        quote_asset=str(identity_raw["quote_asset"]),
        product_kind=str(identity_raw["product_kind"]),
        settlement_asset=str(identity_raw["settlement_asset"]),
        payoff_kind=str(identity_raw["payoff_kind"]),
    )
    until = row["valid_until_ms"]
    if until is not None:
        until = int(until)
    lighter_market_index = None
    if "lighter_market_index" in row:
        index = row["lighter_market_index"]
        if type(index) is not int or index < 0:
            raise FrozenPackageError(FrozenPackageErrorCode.RECORD_INVALID)
        if str(row["venue"]).casefold() != "lighter":
            raise FrozenPackageError(FrozenPackageErrorCode.RECORD_INVALID)
        lighter_market_index = index
    return MarketMappingEvidence(
        mapping_id=str(row["mapping_id"]),
        mapping_version=str(row["mapping_version"]),
        decision=MappingDecision(str(row["decision"])),
        venue=str(row["venue"]),
        symbol=str(row["symbol"]),
        identity=identity,
        evidence_sha256=str(row["evidence_sha256"]),
        evidence_reference=str(row["evidence_reference"]),
        valid_from_ms=int(row["valid_from_ms"]),
        valid_until_ms=until,
        reviewed_contract_multiplier=_decimal_string(row["reviewed_contract_multiplier"]),
        displayed_size_unit=str(row["displayed_size_unit"]),
        quantity_step=_decimal_string(row["quantity_step"]),
        price_tick=_optional_decimal_string(row["price_tick"]),
        price_decimals=row["price_decimals"],
        max_price_significant_digits=row["max_price_significant_digits"],
        min_quantity=_optional_decimal_string(row["min_quantity"]),
        min_notional=_decimal_string(row["min_notional"]),
        lighter_market_index=lighter_market_index,
    )


def _read_ndjson(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    text = path.read_text(encoding="utf-8")
    if not text:
        return rows
    for line in text.splitlines():
        row = json.loads(line)
        if type(row) is not dict:
            raise FrozenPackageError(FrozenPackageErrorCode.RECORD_INVALID)
        rows.append(row)
    return rows


def _assert_reader_protocol() -> None:
    # Keep the class structurally aligned with EvidenceReader without subclassing
    # a runtime-checkable Protocol in a way that implies extra methods.
    _: type[EvidenceReader] = FrozenPackageEvidenceReader


_assert_reader_protocol()
