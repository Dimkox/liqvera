from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / "scripts/build-liqvera-installer.py"
SPEC = importlib.util.spec_from_file_location("installer_builder", PATH)
assert SPEC is not None and SPEC.loader is not None
BUILDER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = BUILDER
SPEC.loader.exec_module(BUILDER)


@pytest.fixture(autouse=True)
def clean_subject(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(BUILDER, "_git_status", lambda: "")


def image_lock(tmp_path: Path) -> Path:
    value = {name: f"registry.invalid/liqvera/{name}@sha256:{hashlib.sha256(name.encode()).hexdigest()}"
             for name in ("edge", "web", "gateway", "capture", "report", "postgres")}
    path = tmp_path / "images.json"
    path.write_text(json.dumps(value, sort_keys=True))
    return path


def test_build_is_byte_reproducible_and_independently_verified(tmp_path: Path) -> None:
    commit = subprocess.check_output(("git", "rev-parse", "HEAD"), cwd=ROOT, text=True).strip()
    first = BUILDER.build_installer(commit, tmp_path / "a", image_lock(tmp_path))
    second = BUILDER.build_installer(commit, tmp_path / "b", image_lock(tmp_path))
    assert first.sha256 == second.sha256
    assert first.archive.read_bytes() == second.archive.read_bytes()
    verified = tmp_path / "verified"
    result = subprocess.run(
        (str(ROOT / ".venv/bin/python"), str(ROOT / "scripts/verify-liqvera-installer.py"),
         str(first.archive), first.sha256, str(verified)),
        cwd=ROOT, check=False, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["inventory_sha256"] == first.inventory_sha256
    assert (verified / "migrations/001_ledger.sql").stat().st_mode & 0o777 == 0o644
    assert (verified / "install.sh").stat().st_mode & 0o777 == 0o755
    with zipfile.ZipFile(first.archive) as package:
        infos = package.infolist()
        assert [item.filename for item in infos] == sorted(item.filename for item in infos)
        assert all(item.extra == b"" and item.comment == b"" for item in infos)
        migration = package.getinfo("liqvera-installer-0.0.2/migrations/001_ledger.sql")
        assert (migration.external_attr >> 16) & 0o777 == 0o644


def test_build_rejects_mutable_or_incomplete_images(tmp_path: Path) -> None:
    commit = subprocess.check_output(("git", "rev-parse", "HEAD"), cwd=ROOT, text=True).strip()
    lock = image_lock(tmp_path)
    value = json.loads(lock.read_text())
    value["web"] = "liqvera/web:latest"
    lock.write_text(json.dumps(value))
    with pytest.raises(BUILDER.BuildError, match="image lock"):
        BUILDER.build_installer(commit, tmp_path / "out", lock)


def test_build_rejects_wrong_commit_dirty_tree_and_existing_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    commit = subprocess.check_output(("git", "rev-parse", "HEAD"), cwd=ROOT, text=True).strip()
    lock = image_lock(tmp_path)
    with pytest.raises(BUILDER.BuildError, match="HEAD"):
        BUILDER.build_installer("0" * 40, tmp_path / "wrong", lock)
    monkeypatch.setattr(BUILDER, "_git_status", lambda: " M installer/compose.yaml")
    with pytest.raises(BUILDER.BuildError, match="clean"):
        BUILDER.build_installer(commit, tmp_path / "dirty", lock)
    monkeypatch.setattr(BUILDER, "_git_status", lambda: "")
    output = tmp_path / "existing"
    output.mkdir()
    with pytest.raises(BUILDER.BuildError, match="output"):
        BUILDER.build_installer(commit, output, lock)


def test_bootstrap_passes_verifier_inventory_authority_without_user_input() -> None:
    text = (ROOT / "scripts/install-liqvera-0.0.2.sh").read_text()
    assert "inventory_sha256" in text
    assert "--inventory-sha256" in text
    assert "eval" not in text and "curl" not in text
