"""Tamper and salvage-manifest fail-closed checks."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from uuid import UUID

import pytest
import yaml
from liqvera_readonly_analyzer.frozen_package.reader import FrozenPackageEvidenceReader
from liqvera_readonly_analyzer.frozen_package.types import FrozenPackageError

from tests.readonly_analyzer.package_factory import write_valid_package

RUN = UUID("00000000-0000-0000-0000-000000000001")
SOURCE_HEAD = "7fe6918690f8bc1da5826c67e3619de4126e4f54"
ROOT = Path(__file__).resolve().parents[2]
VERIFY_SALVAGE = ROOT / "scripts/verify-pr21-salvage.py"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_public_salvage_fixture(tmp_path: Path) -> tuple[Path, Path]:
    target = tmp_path / "packages/readonly-analyzer/src/example.py"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"verified target\n")
    manifest = tmp_path / "salvage.yaml"
    manifest.write_text(
        yaml.safe_dump(
            {
                "source_pr": 21,
                "source_head": SOURCE_HEAD,
                "items": [
                    {
                        "source_path": "private/example.py",
                        "source_blob_sha": "a" * 40,
                        "target": "packages/readonly-analyzer/src/example.py",
                        "target_sha256": _sha256(target),
                        "rule": "rewrite for the public analyzer",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return manifest, target


def _run_salvage(manifest: Path, repository_root: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "python3",
            str(VERIFY_SALVAGE),
            "--manifest",
            str(manifest),
            "--repository-root",
            str(repository_root),
            *extra,
        ],
        check=False,
        capture_output=True,
        text=True,
    )


def _git(repository_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository_root), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def test_reader_rejects_changed_member(tmp_path: Path) -> None:
    package = write_valid_package(tmp_path / "pkg", RUN)
    member = package / "quality_minutes/records.ndjson"
    member.write_bytes(member.read_bytes() + b"\n")
    with pytest.raises(FrozenPackageError, match="MEMBER_HASH_MISMATCH"):
        FrozenPackageEvidenceReader(package)
