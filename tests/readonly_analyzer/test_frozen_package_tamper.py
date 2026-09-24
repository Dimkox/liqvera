"""Tamper and salvage-manifest fail-closed checks."""

from __future__ import annotations

import hashlib
import runpy
import subprocess
import sys
from pathlib import Path
from uuid import UUID

import pytest
import yaml
from mee_readonly_analyzer.frozen_package.reader import FrozenPackageEvidenceReader
from mee_readonly_analyzer.frozen_package.types import FrozenPackageError

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


def test_salvage_manifest_pins_target_bytes_and_source_metadata() -> None:
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
    assert all(len(row["target_sha256"]) == 64 for row in items)
    assert all(_sha256(Path(row["target"])) == row["target_sha256"] for row in items)


def test_public_salvage_verifies_targets_without_private_git_objects(tmp_path: Path) -> None:
    manifest, _ = _write_public_salvage_fixture(tmp_path)
    completed = _run_salvage(manifest, tmp_path)
    assert completed.returncode == 0
    assert "items=1" in completed.stdout
    assert "targets=verified" in completed.stdout
    assert "source_objects=unavailable" in completed.stdout


def test_public_salvage_rejects_changed_target(tmp_path: Path) -> None:
    manifest, target = _write_public_salvage_fixture(tmp_path)
    target.write_bytes(b"tampered\n")
    completed = _run_salvage(manifest, tmp_path)
    assert completed.returncode != 0
    assert "target sha256 mismatch" in completed.stderr


def test_private_salvage_mode_requires_source_objects(tmp_path: Path) -> None:
    manifest, _ = _write_public_salvage_fixture(tmp_path)
    completed = _run_salvage(manifest, tmp_path, "--require-source-objects")
    assert completed.returncode != 0
    assert "required source objects are unavailable" in completed.stderr


def test_source_verification_reads_actual_blob_payload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    manifest, _ = _write_public_salvage_fixture(tmp_path)
    source = tmp_path / "private/example.py"
    source.parent.mkdir()
    source.write_bytes(b"synthetic source bytes\n")
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "add", "private/example.py")
    _git(
        tmp_path,
        "-c", "user.name=Fixture",
        "-c", "user.email=fixture@example.test",
        "commit", "-qm", "synthetic source fixture",
    )
    head = _git(tmp_path, "rev-parse", "HEAD")
    blob_sha = _git(tmp_path, "rev-parse", "HEAD:private/example.py")
    rows = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    rows["source_head"] = head
    rows["items"][0]["source_blob_sha"] = blob_sha
    manifest.write_text(yaml.safe_dump(rows), encoding="utf-8")
    verifier = runpy.run_path(str(VERIFY_SALVAGE))
    main = verifier["main"]
    main.__globals__["EXPECTED_HEAD"] = head
    monkeypatch.setattr(
        sys,
        "argv",
        [str(VERIFY_SALVAGE), "--manifest", str(manifest), "--repository-root", str(tmp_path),
         "--require-source-objects"],
    )
    assert main() == 0
    assert "source_objects=verified" in capsys.readouterr().out

    # The commit and tree still resolve this object ID after its loose payload is removed.
    object_path = tmp_path / ".git/objects" / blob_sha[:2] / blob_sha[2:]
    assert object_path.is_file()
    object_path.unlink()
    with pytest.raises(SystemExit, match="required source objects are unavailable"):
        main()
    monkeypatch.setattr(
        sys,
        "argv",
        [str(VERIFY_SALVAGE), "--manifest", str(manifest), "--repository-root", str(tmp_path)],
    )
    assert main() == 0
    assert "source_objects=unavailable" in capsys.readouterr().out


@pytest.mark.parametrize("mutation", ["wrong_pr", "wrong_head", "unknown_root", "missing_field", "wrong_type"])
def test_salvage_rejects_manifest_outside_closed_schema(tmp_path: Path, mutation: str) -> None:
    manifest, _ = _write_public_salvage_fixture(tmp_path)
    rows = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    if mutation == "wrong_pr":
        rows["source_pr"] = 210
    elif mutation == "wrong_head":
        rows["source_head"] = "0" * 40
        rows["items"][0]["rule"] += SOURCE_HEAD
    elif mutation == "unknown_root":
        rows["unexpected"] = True
    elif mutation == "missing_field":
        del rows["items"][0]["target_sha256"]
    else:
        rows["items"][0]["source_blob_sha"] = 42
    manifest.write_text(yaml.safe_dump(rows), encoding="utf-8")
    completed = _run_salvage(manifest, tmp_path)
    assert completed.returncode != 0
    assert "invalid salvage manifest" in completed.stderr


def test_salvage_rejects_malformed_yaml(tmp_path: Path) -> None:
    manifest, _ = _write_public_salvage_fixture(tmp_path)
    manifest.write_text("source_pr: [\n", encoding="utf-8")
    completed = _run_salvage(manifest, tmp_path)
    assert completed.returncode != 0
    assert "invalid salvage manifest" in completed.stderr
