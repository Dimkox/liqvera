from __future__ import annotations

import hashlib
import importlib.util
import json
import os
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


def test_in_place_mutation_after_snapshot_cannot_change_verified_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = tmp_path / "release.zip"
    expected = write_archive(archive)
    replacement = tmp_path / "replacement.zip"
    replacement_files = valid_files()
    replacement_files["LICENSE-NOTICE.md"] = b"unbound in-place replacement\n"
    write_archive(replacement, replacement_files)
    replacement_bytes = replacement.read_bytes()
    original_snapshot = VERIFIER._capture_archive

    def mutate_after_snapshot(path: Path):
        snapshot = original_snapshot(path)
        with path.open("r+b") as handle:
            handle.write(replacement_bytes)
            handle.truncate()
        return snapshot

    monkeypatch.setattr(VERIFIER, "_capture_archive", mutate_after_snapshot)
    destination = tmp_path / "release"

    VERIFIER.verify_installer(archive, expected, destination)

    assert (destination / "LICENSE-NOTICE.md").read_bytes() == b"Liqvera test fixture\n"


def test_raced_empty_destination_is_preserved_and_publication_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = tmp_path / "release.zip"
    expected = write_archive(archive)
    destination = tmp_path / "release"
    original_publish = VERIFIER._rename_noreplace
    raced_inode: int | None = None

    def race(parent_fd: int, temporary_name: str, destination_name: str) -> None:
        nonlocal raced_inode
        destination.mkdir()
        raced_inode = destination.stat().st_ino
        original_publish(parent_fd, temporary_name, destination_name)

    monkeypatch.setattr(VERIFIER, "_rename_noreplace", race)

    with pytest.raises(VERIFIER.VerificationError):
        VERIFIER.verify_installer(archive, expected, destination)
    assert destination.is_dir()
    assert destination.stat().st_ino == raced_inode
    assert list(destination.iterdir()) == []


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


@pytest.mark.parametrize(
    ("removed", "added"),
    [
        ("config/ports.env.template", None),
        ("compose.yaml", None),
        (None, "migrations/006_unapproved.sql"),
        (None, "unauthorized.txt"),
    ],
)
def test_rejects_rechecksummed_missing_or_extra_package_assets(
    tmp_path: Path, removed: str | None, added: str | None
) -> None:
    files = valid_files()
    if removed is not None:
        files.pop(removed)
    if added is not None:
        files[added] = b"SELECT 6;\n"
    archive = tmp_path / "invalid-inventory.zip"
    expected = write_archive(archive, files)
    assert_failed_without_materialization(archive, expected, tmp_path / "release")


def test_rejects_nul_truncated_raw_zip_name(tmp_path: Path) -> None:
    archive = tmp_path / "nul.zip"
    expected = write_archive(
        archive,
        extra_entries=[(PREFIX + "nullXevil", b"bad", stat.S_IFREG | 0o600)],
    )
    raw = archive.read_bytes().replace(b"nullXevil", b"null\x00evil")
    assert raw != archive.read_bytes()
    archive.write_bytes(raw)
    expected = sha(raw)
    with zipfile.ZipFile(archive) as package:
        crafted = package.infolist()[-1]
        assert crafted.filename.endswith("/null")
        assert crafted.orig_filename.endswith("/null\x00evil")
    assert_failed_without_materialization(archive, expected, tmp_path / "release")


@pytest.mark.parametrize("control", ["\x7f", "\x80", "\x9f"])
def test_rejects_del_and_c1_control_names(tmp_path: Path, control: str) -> None:
    archive = tmp_path / "control.zip"
    expected = write_archive(
        archive,
        extra_entries=[(PREFIX + f"bad{control}name", b"bad", stat.S_IFREG | 0o600)],
    )
    assert_failed_without_materialization(archive, expected, tmp_path / "release")


def test_fifo_input_fails_promptly_without_materialization(tmp_path: Path) -> None:
    fifo = tmp_path / "archive.fifo"
    os.mkfifo(fifo)
    destination = tmp_path / "release"
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), str(fifo), "0" * 64, str(destination)],
        check=False,
        capture_output=True,
        text=True,
        timeout=2,
    )
    assert completed.returncode == 2
    assert "ARCHIVE_INVALID" in completed.stderr
    assert not destination.exists()


def test_member_limit_is_rejected_before_zipfile_allocates_inventory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = tmp_path / "many.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_STORED) as package:
        for index in range(VERIFIER.MAX_MEMBERS + 1):
            info = zipfile.ZipInfo(PREFIX + f"tiny-{index:03d}")
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o600) << 16
            package.writestr(info, b"")
    expected = sha(archive.read_bytes())
    called = False
    original_zipfile = VERIFIER.zipfile.ZipFile

    def forbidden_parser(*args, **kwargs):
        nonlocal called
        called = True
        return original_zipfile(*args, **kwargs)

    monkeypatch.setattr(VERIFIER.zipfile, "ZipFile", forbidden_parser)
    assert_failed_without_materialization(archive, expected, tmp_path / "release")
    assert called is False


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
