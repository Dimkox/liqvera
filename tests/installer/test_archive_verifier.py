from __future__ import annotations

import hashlib
import importlib.util
import json
import stat
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "verify-liqvera-installer.py"
SPEC = importlib.util.spec_from_file_location("verify_liqvera_installer", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
VERIFIER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = VERIFIER
SPEC.loader.exec_module(VERIFIER)

PREFIX = "liqvera-installer-0.0.2/"
MIGRATIONS = {
    path.name: path.read_bytes()
    for path in sorted((ROOT / "apps" / "mezo-gateway" / "migrations").glob("*.sql"))
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def manifest(files: dict[str, bytes]) -> bytes:
    migrations = [
        {"name": name, "sha256": sha(data)} for name, data in MIGRATIONS.items()
    ]
    value = {
        "schema_version": "liqvera-installer-release/v1",
        "product_version": "0.0.2",
        "git_commit": "1" * 40,
        "git_tree": "2" * 40,
        "compose_sha256": sha(files["compose.yaml"]),
        "launchers": {
            "install.sh": sha(files["install.sh"]),
            "liqvera.sh": sha(files["liqvera.sh"]),
        },
        "images": {
            name: f"registry.invalid/liqvera-{name}@sha256:{digit * 64}"
            for name, digit in zip(
                ("edge", "web", "gateway", "capture", "report", "postgres"),
                "123456",
                strict=True,
            )
        },
        "migrations": migrations,
        "supported_linux": {
            "architectures": ["amd64", "arm64"],
            "distributions": ["ubuntu", "debian", "fedora", "rhel"],
        },
    }
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def valid_files() -> dict[str, bytes]:
    files = {
        "install.sh": b"#!/usr/bin/env bash\nexit 0\n",
        "liqvera.sh": b"#!/usr/bin/env bash\nexit 0\n",
        "compose.yaml": b"services: {}\n",
        "config/liqvera.env.template": b"LIQVERA_PAYMENT_ENABLED=false\n",
        "config/ports.env.template": b"LIQVERA_WEB_HOST=127.0.0.1\n",
        "manifests/migration-checksums.json": json.dumps(
            {name: sha(data) for name, data in MIGRATIONS.items()},
            sort_keys=True,
            separators=(",", ":"),
        ).encode(),
        "LICENSE-NOTICE.md": b"Liqvera test fixture\n",
    }
    files.update({f"migrations/{name}": data for name, data in MIGRATIONS.items()})
    files["manifests/release-manifest.json"] = manifest(files)
    return files


def write_archive(
    path: Path,
    files: dict[str, bytes] | None = None,
    *,
    extra_entries: list[tuple[str, bytes, int]] | None = None,
    checksums: dict[str, str] | None = None,
) -> str:
    members = dict(valid_files() if files is None else files)
    sums = checksums or {name: sha(data) for name, data in members.items()}
    members["SHA256SUMS"] = "".join(
        f"{digest}  {name}\n" for name, digest in sorted(sums.items())
    ).encode()
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, data in members.items():
            info = zipfile.ZipInfo(PREFIX + name)
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o600) << 16
            archive.writestr(info, data)
        for name, data, mode in extra_entries or []:
            info = zipfile.ZipInfo(name)
            info.create_system = 3
            info.external_attr = mode << 16
            archive.writestr(info, data)
    return sha(path.read_bytes())


def assert_failed_without_materialization(
    archive: Path, expected: str, destination: Path
) -> None:
    with pytest.raises(VERIFIER.VerificationError):
        VERIFIER.verify_installer(archive, expected, destination)
    assert not destination.exists()
    assert not (destination / "install.sh").exists()


def test_valid_archive_materializes_only_after_complete_verification(tmp_path: Path) -> None:
    archive = tmp_path / "release.zip"
    expected = write_archive(archive)
    destination = tmp_path / "release"

    result = VERIFIER.verify_installer(archive, expected, destination)

    assert result.schema_version == "verified-release-v1"
    assert result.archive_sha256 == expected
    assert result.product_version == "0.0.2"
    assert result.git_commit == "1" * 40
    assert result.git_tree == "2" * 40
    assert result.destination == str(destination.resolve())
    assert result.file_count == len(valid_files()) + 1
    assert (destination / "install.sh").read_bytes().startswith(b"#!/usr/bin/env bash")
    assert stat.S_IMODE(destination.stat().st_mode) == 0o700
    assert stat.S_IMODE((destination / "install.sh").stat().st_mode) == 0o600

    completed = subprocess.run(
        [sys.executable, str(SCRIPT), str(archive), expected, str(tmp_path / "cli-release")],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "archive_sha256": expected,
        "destination": str((tmp_path / "cli-release").resolve()),
        "file_count": len(valid_files()) + 1,
        "git_commit": "1" * 40,
        "git_tree": "2" * 40,
        "product_version": "0.0.2",
        "schema_version": "verified-release-v1",
    }


def test_rejects_wrong_outer_digest_and_existing_destination(tmp_path: Path) -> None:
    archive = tmp_path / "release.zip"
    expected = write_archive(archive)
    assert_failed_without_materialization(archive, "0" * 64, tmp_path / "wrong")

    destination = tmp_path / "existing"
    destination.mkdir()
    marker = destination / "marker"
    marker.write_text("preserve", encoding="utf-8")
    with pytest.raises(VERIFIER.VerificationError):
        VERIFIER.verify_installer(archive, expected, destination)
    assert marker.read_text(encoding="utf-8") == "preserve"


def test_outer_digest_and_zip_validation_use_the_same_open_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = tmp_path / "release.zip"
    expected = write_archive(archive)
    replacement = tmp_path / "replacement.zip"
    replacement_files = valid_files()
    replacement_files["LICENSE-NOTICE.md"] = b"unbound replacement\n"
    write_archive(replacement, replacement_files)
    original_hash = VERIFIER._handle_sha256

    def swap_after_hash(handle) -> str:
        digest = original_hash(handle)
        replacement.replace(path)
        return digest

    path = archive
    monkeypatch.setattr(VERIFIER, "_handle_sha256", swap_after_hash)
    destination = tmp_path / "release"

    VERIFIER.verify_installer(archive, expected, destination)

    assert (destination / "LICENSE-NOTICE.md").read_bytes() == b"Liqvera test fixture\n"


@pytest.mark.parametrize(
    "bad_name",
    [
        f"{PREFIX}../escape",
        "/absolute",
        f"{PREFIX}config\\escape",
        f"{PREFIX}config/../../escape",
    ],
)
def test_rejects_traversal_and_absolute_names(tmp_path: Path, bad_name: str) -> None:
    archive = tmp_path / "release.zip"
    expected = write_archive(
        archive,
        extra_entries=[(bad_name, b"bad", stat.S_IFREG | 0o600)],
    )
    assert_failed_without_materialization(archive, expected, tmp_path / "release")


@pytest.mark.parametrize(
    "first,second",
    [
        ("README", "readme"),
        ("caf\u00e9", "cafe\u0301"),
        ("config/a", "config/./a"),
    ],
)
def test_rejects_casefold_unicode_and_normalized_duplicates(
    tmp_path: Path, first: str, second: str
) -> None:
    archive = tmp_path / "release.zip"
    expected = write_archive(
        archive,
        extra_entries=[
            (PREFIX + first, b"one", stat.S_IFREG | 0o600),
            (PREFIX + second, b"two", stat.S_IFREG | 0o600),
        ],
    )
    assert_failed_without_materialization(archive, expected, tmp_path / "release")


@pytest.mark.parametrize(
    "label,mode",
    [
        ("symlink", stat.S_IFLNK | 0o777),
        ("hardlink", 0),
        ("fifo", stat.S_IFIFO | 0o600),
        ("device", stat.S_IFCHR | 0o600),
    ],
)
def test_rejects_non_regular_entries(tmp_path: Path, label: str, mode: int) -> None:
    archive = tmp_path / f"{label}.zip"
    expected = write_archive(
        archive,
        extra_entries=[(PREFIX + label, b"target", mode)],
    )
    assert_failed_without_materialization(archive, expected, tmp_path / "release")


def test_rejects_missing_extra_and_changed_inner_checksum(tmp_path: Path) -> None:
    cases: list[tuple[dict[str, bytes], dict[str, str] | None]] = []
    missing = valid_files()
    missing.pop("liqvera.sh")
    cases.append((missing, {name: sha(data) for name, data in valid_files().items()}))

    extra = valid_files()
    extra["undeclared.txt"] = b"extra"
    cases.append((extra, {name: sha(data) for name, data in valid_files().items()}))

    changed = valid_files()
    changed["install.sh"] = b"changed"
    cases.append((changed, {name: sha(data) for name, data in valid_files().items()}))

    for index, (files, checksums) in enumerate(cases):
        archive = tmp_path / f"case-{index}.zip"
        expected = write_archive(archive, files, checksums=checksums)
        assert_failed_without_materialization(archive, expected, tmp_path / f"release-{index}")


def test_rejects_oversized_member_and_aggregate_before_materialization(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(VERIFIER, "MAX_MEMBER_BYTES", 128)
    oversized = valid_files()
    oversized["LICENSE-NOTICE.md"] = b"x" * 129
    archive = tmp_path / "oversized.zip"
    expected = write_archive(archive, oversized)
    assert_failed_without_materialization(archive, expected, tmp_path / "oversized-release")

    monkeypatch.setattr(VERIFIER, "MAX_MEMBER_BYTES", 1_000_000)
    monkeypatch.setattr(VERIFIER, "MAX_TOTAL_BYTES", 256)
    archive = tmp_path / "aggregate.zip"
    expected = write_archive(archive)
    assert_failed_without_materialization(archive, expected, tmp_path / "aggregate-release")
