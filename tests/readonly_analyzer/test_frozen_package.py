"""Frozen package reader behavior on mee_contracts types."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

import pytest
from mee_contracts.provenance import MappingDecision
from mee_readonly_analyzer.frozen_package.reader import FrozenPackageEvidenceReader
from mee_readonly_analyzer.frozen_package.types import FrozenPackageError

from tests.readonly_analyzer.package_factory import (
    SAMPLE_LIGHTER_MAPPING,
    SAMPLE_MAPPING,
    rebind_member,
    write_valid_package,
)

RUN = UUID("00000000-0000-0000-0000-000000000001")


def test_reader_returns_contracts_records(tmp_path: Path) -> None:
    package = write_valid_package(tmp_path / "pkg", RUN, mappings=[])
    reader = FrozenPackageEvidenceReader(package)
    manifest = reader.read_capture_manifest(RUN)
    assert manifest.capture_run_id == RUN
    assert manifest.venue_set == ("hyperliquid", "lighter")
    assert reader.capture_terminal(RUN).status == "sealed"
    assert len(tuple(reader.iter_control_evidence(RUN))) == 1
    assert len(tuple(reader.iter_raw_batches(RUN))) == 1
    assert len(tuple(reader.iter_raw_envelopes(RUN))) == 1
    assert len(tuple(reader.iter_quality_minutes(RUN))) == 1
    assert reader.read_mapping_snapshot(RUN).mappings == ()


def test_reader_decodes_market_mapping_evidence(tmp_path: Path) -> None:
    package = write_valid_package(tmp_path / "pkg", RUN, mappings=[SAMPLE_MAPPING])
    snapshot = FrozenPackageEvidenceReader(package).read_mapping_snapshot(RUN)
    assert len(snapshot.mappings) == 1
    mapping = snapshot.mappings[0]
    assert mapping.mapping_id == "map-1"
    assert mapping.decision is MappingDecision.APPROVED
    assert mapping.identity.base_asset == "BTC"
    assert mapping.symbol == "BTC"


def test_reader_accepts_optional_lighter_market_index(tmp_path: Path) -> None:
    package = write_valid_package(tmp_path / "pkg", RUN, mappings=[SAMPLE_LIGHTER_MAPPING])
    mapping = FrozenPackageEvidenceReader(package).read_mapping_snapshot(RUN).mappings[0]
    assert mapping.mapping_id == "map-lighter-1"
    assert mapping.venue == "lighter"
    assert mapping.symbol == "BTC"
    assert mapping.lighter_market_index == 1


def test_reader_omitted_lighter_market_index_is_none(tmp_path: Path) -> None:
    package = write_valid_package(tmp_path / "pkg", RUN, mappings=[SAMPLE_MAPPING])
    mapping = FrozenPackageEvidenceReader(package).read_mapping_snapshot(RUN).mappings[0]
    assert mapping.lighter_market_index is None


def test_reader_lighter_row_without_index_is_none(tmp_path: Path) -> None:
    row = dict(SAMPLE_LIGHTER_MAPPING)
    del row["lighter_market_index"]
    package = write_valid_package(tmp_path / "pkg", RUN, mappings=[row])
    mapping = FrozenPackageEvidenceReader(package).read_mapping_snapshot(RUN).mappings[0]
    assert mapping.venue == "lighter"
    assert mapping.lighter_market_index is None


def test_reader_rejects_unknown_mapping_key(tmp_path: Path) -> None:
    row = dict(SAMPLE_MAPPING)
    row["extra"] = 1
    package = write_valid_package(tmp_path / "pkg", RUN, mappings=[row])
    reader = FrozenPackageEvidenceReader(package)
    with pytest.raises(FrozenPackageError, match="RECORD_INVALID"):
        reader.read_mapping_snapshot(RUN)


def test_reader_rejects_hyperliquid_lighter_market_index(tmp_path: Path) -> None:
    row = dict(SAMPLE_MAPPING)
    row["lighter_market_index"] = 1
    package = write_valid_package(tmp_path / "pkg", RUN, mappings=[row])
    reader = FrozenPackageEvidenceReader(package)
    with pytest.raises(FrozenPackageError, match="RECORD_INVALID"):
        reader.read_mapping_snapshot(RUN)


def test_reader_rejects_non_int_lighter_market_index(tmp_path: Path) -> None:
    for value in (True, "1", None, -1, 1.0):
        row = dict(SAMPLE_LIGHTER_MAPPING)
        row["lighter_market_index"] = value
        package = write_valid_package(tmp_path / "pkg", RUN, mappings=[row])
        reader = FrozenPackageEvidenceReader(package)
        with pytest.raises(FrozenPackageError, match="RECORD_INVALID"):
            reader.read_mapping_snapshot(RUN)


def test_reader_rejects_malformed_mapping(tmp_path: Path) -> None:
    package = write_valid_package(tmp_path / "pkg", RUN, mappings=[{"mapping_id": "bad"}])
    reader = FrozenPackageEvidenceReader(package)
    with pytest.raises(FrozenPackageError, match="RECORD_INVALID"):
        reader.read_mapping_snapshot(RUN)


def test_reader_rejects_json_number_money_fields(tmp_path: Path) -> None:
    row = dict(SAMPLE_MAPPING)
    row["min_notional"] = 10
    package = write_valid_package(tmp_path / "pkg", RUN, mappings=[row])
    reader = FrozenPackageEvidenceReader(package)
    with pytest.raises(FrozenPackageError, match="RECORD_INVALID"):
        reader.read_mapping_snapshot(RUN)


def test_reader_rejects_undeclared_member_file(tmp_path: Path) -> None:
    package = write_valid_package(tmp_path / "pkg", RUN)
    (package / "stale.bin").write_bytes(b"old")
    with pytest.raises(FrozenPackageError, match="MEMBER_SET_MISMATCH"):
        FrozenPackageEvidenceReader(package)


def test_reader_rejects_extra_envelope_key(tmp_path: Path) -> None:
    package = write_valid_package(tmp_path / "pkg", RUN)
    rebind_member(package, "mapping_snapshot.json", b'{"mappings":[],"extra":true}\n')
    reader = FrozenPackageEvidenceReader(package)
    with pytest.raises(FrozenPackageError, match="RECORD_INVALID"):
        reader.read_mapping_snapshot(RUN)
