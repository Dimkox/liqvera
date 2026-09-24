"""Tamper and salvage-manifest fail-closed checks."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

import pytest
import yaml
from mee_readonly_analyzer.frozen_package.reader import FrozenPackageEvidenceReader
from mee_readonly_analyzer.frozen_package.types import FrozenPackageError

from tests.readonly_analyzer.package_factory import write_valid_package

RUN = UUID("00000000-0000-0000-0000-000000000001")
SOURCE_HEAD = "7fe6918690f8bc1da5826c67e3619de4126e4f54"


def test_reader_rejects_changed_member(tmp_path: Path) -> None:
    package = write_valid_package(tmp_path / "pkg", RUN)
    member = package / "quality_minutes/records.ndjson"
    member.write_bytes(member.read_bytes() + b"\n")
    with pytest.raises(FrozenPackageError, match="MEMBER_HASH_MISMATCH"):
        FrozenPackageEvidenceReader(package)


def test_every_salvaged_blob_has_exact_source_and_rewrite_rule() -> None:
    rows = yaml.safe_load(
        Path("architecture/salvage/pr21.yaml").read_text(encoding="utf-8")
    )
    items = rows["items"]
    assert items
    assert rows["source_head"] == SOURCE_HEAD
    assert all(row["source_blob_sha"] and len(row["source_blob_sha"]) == 40 for row in items)
    assert all(row["target"].startswith("packages/readonly-analyzer/") for row in items)
    assert all(row["rule"].strip() for row in items)
    assert all(Path(row["target"]).is_file() for row in items)
