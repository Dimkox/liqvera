"""Capture writes a package the analyzer can read."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from uuid import uuid4

import pytest
from mee_contracts.decision import StageADecisionCode, StageAReasonCode
from mee_public_capture.config import PublicConfigError, load_public_configuration
from mee_public_capture.package import REVIEWED_BTC, REVIEWED_LIGHTER_BTC, write_frozen_package
from mee_public_capture.runtime import FIXTURE_BOOK, FIXTURE_LIGHTER_SNAPSHOT, run_public_capture
from mee_readonly_analyzer.frozen_package.reader import FrozenPackageEvidenceReader
from mee_readonly_analyzer.identity import bind_reconstructed_books
from mee_readonly_analyzer.reconstruction import reconstruct_books
from mee_readonly_analyzer.verdict import evaluate_frozen_package

_RUNTIME = Path("packages/public-capture/src/mee_public_capture/runtime.py")
_INSUFFICIENT_REASONS = (
    StageAReasonCode.INSUFFICIENT_ACQUISITION_WINDOW,
    StageAReasonCode.INSUFFICIENT_COMPLETE_UTC_DAYS,
    StageAReasonCode.INSUFFICIENT_STRICT_HEALTHY_MINUTES,
    StageAReasonCode.INSUFFICIENT_INDEPENDENT_EPISODES,
)
_REVIEWED_BTC_KEYS = frozenset(
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


def _fixture_package(tmp_path: Path, venues: str) -> Path:
    root = tmp_path / "pkg"
    root.mkdir()
    config = load_public_configuration(
        {
            "MEE_CAPTURE_OUT": str(root),
            "MEE_CAPTURE_SOURCE": "fixture",
            "MEE_PUBLIC_VENUES": venues,
        }
    )
    assert run_public_capture(config) == 0
    return root


def test_dry_run_without_output_still_validates() -> None:
    assert run_public_capture(load_public_configuration({})) == 0


def test_fixture_capture_is_readable_by_analyzer(tmp_path: Path) -> None:
    root = _fixture_package(tmp_path, "hyperliquid,lighter")
    reader = FrozenPackageEvidenceReader(root)
    manifest = reader.read_capture_manifest(reader.capture_run_id)
    assert manifest.venue_set == ("hyperliquid", "lighter")
    assert reader.capture_terminal(reader.capture_run_id).status == "sealed"
    mappings = reader.read_mapping_snapshot(reader.capture_run_id).mappings
    assert mappings[0].symbol == "BTC"
    assert mappings[0].venue == "hyperliquid"
    assert mappings[1].venue == "lighter"
    assert mappings[1].lighter_market_index == 1


def test_default_fixture_writes_two_envelopes_without_lighter_symbol(tmp_path: Path) -> None:
    root = _fixture_package(tmp_path, "hyperliquid,lighter")
    reader = FrozenPackageEvidenceReader(root)
    envelopes = tuple(reader.iter_raw_envelopes(reader.capture_run_id))
    assert len(envelopes) == 2
    assert [item.envelope_index for item in envelopes] == [0, 1]
    assert [item.venue for item in envelopes] == ["hyperliquid", "lighter"]
    assert envelopes[0].payload == FIXTURE_BOOK
    assert envelopes[1].payload == FIXTURE_LIGHTER_SNAPSHOT
    assert (root / "raw_batches/0.bin").read_bytes() == FIXTURE_BOOK
    lighter_payload = json.loads(envelopes[1].payload)
    assert "symbol" not in lighter_payload
    assert lighter_payload["type"] == "subscribed/order_book"
    assert lighter_payload["channel"] == "order_book:1"
    minutes = tuple(reader.iter_quality_minutes(reader.capture_run_id))
    assert len(minutes) == 1
    assert minutes[0].venue == "hyperliquid"


def test_default_fixture_seals_reviewed_btc_and_indexed_lighter_mapping(tmp_path: Path) -> None:
    root = _fixture_package(tmp_path, "hyperliquid,lighter")
    document = json.loads((root / "mapping_snapshot.json").read_text(encoding="utf-8"))
    rows = document["mappings"]
    assert rows == [REVIEWED_BTC, REVIEWED_LIGHTER_BTC]
    assert set(rows[0]) == _REVIEWED_BTC_KEYS
    assert "lighter_market_index" not in rows[0]
    assert rows[1]["venue"] == "lighter"
    assert rows[1]["symbol"] == "BTC"
    assert rows[1]["mapping_id"] == "lighter-btc-usd-linear-perpetual"
    assert rows[1]["mapping_id"] != rows[0]["mapping_id"]
    assert rows[1]["lighter_market_index"] == 1
    assert type(rows[1]["lighter_market_index"]) is int


def test_hyperliquid_only_fixture_writes_one_reviewed_btc_envelope(tmp_path: Path) -> None:
    root = _fixture_package(tmp_path, "hyperliquid")
    reader = FrozenPackageEvidenceReader(root)
    envelopes = tuple(reader.iter_raw_envelopes(reader.capture_run_id))
    assert len(envelopes) == 1
    assert envelopes[0].venue == "hyperliquid"
    assert envelopes[0].payload == FIXTURE_BOOK
    rows = json.loads((root / "mapping_snapshot.json").read_text(encoding="utf-8"))["mappings"]
    assert rows == [REVIEWED_BTC]


def test_lighter_only_fixture_writes_official_snap_as_batch_zero(tmp_path: Path) -> None:
    root = _fixture_package(tmp_path, "lighter")
    reader = FrozenPackageEvidenceReader(root)
    envelopes = tuple(reader.iter_raw_envelopes(reader.capture_run_id))
    assert len(envelopes) == 1
    assert envelopes[0].venue == "lighter"
    assert envelopes[0].payload == FIXTURE_LIGHTER_SNAPSHOT
    assert (root / "raw_batches/0.bin").read_bytes() == FIXTURE_LIGHTER_SNAPSHOT
    assert "symbol" not in json.loads(envelopes[0].payload)
    rows = json.loads((root / "mapping_snapshot.json").read_text(encoding="utf-8"))["mappings"]
    assert rows == [REVIEWED_LIGHTER_BTC]


def test_capture_written_fixture_evaluates_insufficient_with_four_reasons(
    tmp_path: Path,
) -> None:
    root = _fixture_package(tmp_path, "hyperliquid,lighter")
    decision = evaluate_frozen_package(root)
    assert decision.decision is StageADecisionCode.INSUFFICIENT_EVIDENCE
    assert decision.reasons == _INSUFFICIENT_REASONS
    assert all(item.value.startswith("INSUFFICIENT_") for item in decision.reasons)
    assert b"GO" not in decision.to_canonical_json()
    assert decision.decision is not StageADecisionCode.STOP
    assert decision.decision is not StageADecisionCode.EXTEND_LONGER_SHADOW


def test_capture_written_fixture_reconstructs_and_binds_both_books(tmp_path: Path) -> None:
    root = _fixture_package(tmp_path, "hyperliquid,lighter")
    reader = FrozenPackageEvidenceReader(root)
    envelopes = tuple(reader.iter_raw_envelopes(reader.capture_run_id))
    mappings = reader.read_mapping_snapshot(reader.capture_run_id).mappings
    books = reconstruct_books(envelopes, mappings)
    assert len(books) == 2
    assert books[0].snapshot.venue == "HYPERLIQUID"
    assert books[1].snapshot.venue == "LIGHTER"
    assert books[0].snapshot.symbol == "BTC"
    assert books[1].snapshot.symbol == "BTC"
    assert books[1].channel == "order_book:1"
    assert books[0].mapping_id is None
    assert books[1].mapping_id is None
    bound = bind_reconstructed_books(books, mappings)
    assert bound[0].mapping_id == "btc-usd-linear-perpetual"
    assert bound[1].mapping_id == "lighter-btc-usd-linear-perpetual"


def test_writer_rejects_empty_envelopes(tmp_path: Path) -> None:
    root = tmp_path / "pkg"
    root.mkdir()
    with pytest.raises(ValueError, match="envelopes"):
        write_frozen_package(
            root,
            run_id=uuid4(),
            started_at_ms=1,
            terminated_at_ms=2,
            venues=("hyperliquid",),
            envelopes=(),
            mappings=[],
        )


def test_writer_clears_leftover_members_before_seal(tmp_path: Path) -> None:
    root = tmp_path / "pkg"
    root.mkdir()
    leftover = root / "stale.bin"
    leftover.write_bytes(b"old")
    (root / "nested").mkdir()
    (root / "nested" / "extra.txt").write_text("x", encoding="utf-8")
    write_frozen_package(
        root,
        run_id=uuid4(),
        started_at_ms=1,
        terminated_at_ms=2,
        venues=("hyperliquid",),
        envelopes=(("hyperliquid", b"{}"),),
        mappings=[],
    )
    assert not leftover.exists()
    assert not (root / "nested").exists()
    FrozenPackageEvidenceReader(root)


def test_fixture_path_does_not_import_httpx() -> None:
    source = _RUNTIME.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(_RUNTIME))
    for node in tree.body:
        if isinstance(node, ast.Import):
            assert all(alias.name.split(".", 1)[0] != "httpx" for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".", 1)[0] != "httpx"
    assert b'"symbol"' not in FIXTURE_LIGHTER_SNAPSHOT
    assert "api.hyperliquid.xyz" in source


def test_capture_rejects_credential_env_names() -> None:
    with pytest.raises(PublicConfigError, match="credential environment is forbidden"):
        load_public_configuration({"VENUE_TOKEN": "1"})
