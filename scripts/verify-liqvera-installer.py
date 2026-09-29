#!/usr/bin/env python3
"""Verify and safely materialize a Liqvera installer ZIP without executing it."""

from __future__ import annotations

import argparse
import ctypes
import errno
import hashlib
import io
import json
import os
import re
import shutil
import stat
import struct
import sys
import tempfile
import unicodedata
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath

from jsonschema import Draft202012Validator, ValidationError


ROOT = Path(__file__).resolve().parents[1]
RELEASE_SCHEMA = ROOT / "installer" / "schemas" / "release-manifest.schema.json"
ARCHIVE_PREFIX = "liqvera-installer-0.0.2/"
MAX_ARCHIVE_BYTES = 128 * 1024 * 1024
MAX_MEMBER_BYTES = 16 * 1024 * 1024
MAX_TOTAL_BYTES = 64 * 1024 * 1024
MAX_MEMBERS = 128
MAX_METADATA_BYTES = 64 * 1024
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
MIGRATION_NAMES = (
    "001_ledger.sql",
    "002_fix_immutable_ledger_identity.sql",
    "003_live_grant_consumption.sql",
    "004_receipt_confirmation_provenance.sql",
    "005_receipt_confirmation_count.sql",
)
APPROVED_PATHS = frozenset(
    {
        "install.sh",
        "liqvera.sh",
        "compose.yaml",
        "config/liqvera.env.template",
        "config/ports.env.template",
        "manifests/release-manifest.json",
        "manifests/migration-checksums.json",
        "LICENSE-NOTICE.md",
        "SHA256SUMS",
        *(f"migrations/{name}" for name in MIGRATION_NAMES),
    }
)
_EOCD = struct.Struct("<4s4H2LH")
_CENTRAL_HEADER = struct.Struct("<4s6H3L5H2L")
_LIBC = ctypes.CDLL(None, use_errno=True)
_RENAME_NOREPLACE = 1


class VerificationError(ValueError):
    """The archive cannot be trusted or safely materialized."""


@dataclass(frozen=True)
class VerifiedRelease:
    schema_version: str
    archive_sha256: str
    destination: str
    file_count: int
    product_version: str
    git_commit: str
    git_tree: str


@dataclass(frozen=True)
class _Member:
    info: zipfile.ZipInfo
    path: str


def _capture_archive(path: Path) -> bytes:
    try:
        descriptor = os.open(
            path,
            os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK,
        )
    except OSError as exc:
        raise VerificationError("ARCHIVE_INVALID: archive input cannot be opened safely") from exc
    with os.fdopen(descriptor, "rb") as handle:
        archive_stat = os.fstat(descriptor)
        if (
            not stat.S_ISREG(archive_stat.st_mode)
            or archive_stat.st_nlink != 1
            or archive_stat.st_size > MAX_ARCHIVE_BYTES
        ):
            raise VerificationError(
                "ARCHIVE_INVALID: archive input is not a bounded single-link file"
            )
        captured = bytearray()
        while len(captured) <= MAX_ARCHIVE_BYTES:
            chunk = handle.read(min(1024 * 1024, MAX_ARCHIVE_BYTES + 1 - len(captured)))
            if not chunk:
                break
            captured.extend(chunk)
        if len(captured) > MAX_ARCHIVE_BYTES:
            raise VerificationError("ARCHIVE_INVALID: archive grew beyond size bound")
    return bytes(captured)


def _handle_sha256(handle: io.BufferedReader) -> str:
    digest = hashlib.sha256()
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
        digest.update(chunk)
    handle.seek(0)
    return digest.hexdigest()


def _preflight_zip(data: bytes) -> None:
    search_start = max(0, len(data) - (65535 + _EOCD.size))
    offset = data.rfind(b"PK\x05\x06", search_start)
    if offset < 0 or offset + _EOCD.size > len(data):
        raise VerificationError("ARCHIVE_INVALID: missing bounded ZIP end record")
    (
        signature,
        disk_number,
        central_disk,
        disk_entries,
        total_entries,
        central_size,
        central_offset,
        comment_size,
    ) = _EOCD.unpack_from(data, offset)
    if signature != b"PK\x05\x06" or offset + _EOCD.size + comment_size != len(data):
        raise VerificationError("ARCHIVE_INVALID: inconsistent ZIP end record")
    if disk_number != 0 or central_disk != 0 or disk_entries != total_entries:
        raise VerificationError("ARCHIVE_INVALID: multidisk ZIP is forbidden")
    if total_entries in {0xFFFF} or central_size == 0xFFFFFFFF or central_offset == 0xFFFFFFFF:
        raise VerificationError("ARCHIVE_INVALID: ZIP64 is forbidden")
    if total_entries == 0 or total_entries > MAX_MEMBERS:
        raise VerificationError("ARCHIVE_INVALID: member count outside bounds")
    if central_size > MAX_METADATA_BYTES or central_offset + central_size != offset:
        raise VerificationError("ARCHIVE_INVALID: central directory outside bounds")

    cursor = central_offset
    central_end = central_offset + central_size
    parsed = 0
    while cursor < central_end:
        if cursor + _CENTRAL_HEADER.size > central_end:
            raise VerificationError("ARCHIVE_INVALID: truncated central directory")
        fields = _CENTRAL_HEADER.unpack_from(data, cursor)
        if fields[0] != b"PK\x01\x02" or fields[13] != 0:
            raise VerificationError("ARCHIVE_INVALID: invalid central directory entry")
        record_size = _CENTRAL_HEADER.size + fields[10] + fields[11] + fields[12]
        cursor += record_size
        parsed += 1
        if cursor > central_end or parsed > MAX_MEMBERS:
            raise VerificationError("ARCHIVE_INVALID: central directory exceeds bounds")
    if cursor != central_end or parsed != total_entries:
        raise VerificationError("ARCHIVE_INVALID: central directory count mismatch")


def _normalized_member(raw_name: str) -> str:
    if "\\" in raw_name or "\x00" in raw_name:
        raise VerificationError("ARCHIVE_INVALID: unsafe member separator")
    if not raw_name.startswith(ARCHIVE_PREFIX):
        raise VerificationError("ARCHIVE_INVALID: member outside release root")
    relative = raw_name[len(ARCHIVE_PREFIX) :]
    if not relative or relative.startswith("/"):
        raise VerificationError("ARCHIVE_INVALID: empty or absolute member")
    raw_parts = relative.split("/")
    if any(part in {"", ".", ".."} for part in raw_parts):
        raise VerificationError("ARCHIVE_INVALID: non-canonical member path")
    normalized = unicodedata.normalize("NFC", relative)
    path = PurePosixPath(normalized)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise VerificationError("ARCHIVE_INVALID: path traversal")
    if any(
        ord(character) < 32
        or 0x7F <= ord(character) <= 0x9F
        or unicodedata.category(character) in {"Cf", "Cs"}
        for character in normalized
    ):
        raise VerificationError("ARCHIVE_INVALID: control character in path")
    return path.as_posix()


def _regular_mode(info: zipfile.ZipInfo) -> int:
    if info.create_system != 3:
        raise VerificationError("ARCHIVE_INVALID: missing Unix regular-file identity")
    mode = (info.external_attr >> 16) & 0xFFFF
    if not stat.S_ISREG(mode):
        raise VerificationError("ARCHIVE_INVALID: links and special files are forbidden")
    return mode


def _inspect_archive(archive: zipfile.ZipFile) -> dict[str, _Member]:
    infos = archive.infolist()
    if not infos or len(infos) > MAX_MEMBERS:
        raise VerificationError("ARCHIVE_INVALID: member count outside bounds")
    metadata_bytes = len(archive.comment)
    total_bytes = 0
    members: dict[str, _Member] = {}
    collision_keys: set[str] = set()
    for info in infos:
        raw_name = info.orig_filename
        if raw_name != info.filename or "\x00" in raw_name:
            raise VerificationError("ARCHIVE_INVALID: parser-altered member name")
        try:
            metadata_bytes += len(raw_name.encode("utf-8")) + len(info.extra) + len(info.comment)
        except UnicodeEncodeError as exc:
            raise VerificationError("ARCHIVE_INVALID: invalid member name encoding") from exc
        if metadata_bytes > MAX_METADATA_BYTES:
            raise VerificationError("ARCHIVE_INVALID: metadata exceeds bound")
        path = _normalized_member(raw_name)
        collision_key = unicodedata.normalize("NFC", path).casefold()
        if collision_key in collision_keys:
            raise VerificationError("ARCHIVE_INVALID: normalized member collision")
        collision_keys.add(collision_key)
        _regular_mode(info)
        if info.file_size < 0 or info.file_size > MAX_MEMBER_BYTES:
            raise VerificationError("ARCHIVE_INVALID: member exceeds size bound")
        total_bytes += info.file_size
        if total_bytes > MAX_TOTAL_BYTES:
            raise VerificationError("ARCHIVE_INVALID: archive exceeds aggregate bound")
        members[path] = _Member(info=info, path=path)
    if set(members) != APPROVED_PATHS:
        raise VerificationError("ARCHIVE_INVALID: package inventory mismatch")
    return members


def _read_member(archive: zipfile.ZipFile, member: _Member) -> bytes:
    with archive.open(member.info, "r") as handle:
        data = handle.read(MAX_MEMBER_BYTES + 1)
        if len(data) > MAX_MEMBER_BYTES or len(data) != member.info.file_size:
            raise VerificationError("ARCHIVE_INVALID: expanded member size mismatch")
        if handle.read(1):
            raise VerificationError("ARCHIVE_INVALID: expanded member exceeds bound")
        return data


def _parse_checksums(data: bytes) -> dict[str, str]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise VerificationError("ARCHIVE_INVALID: SHA256SUMS is not UTF-8") from exc
    checksums: dict[str, str] = {}
    collision_keys: set[str] = set()
    for line in text.splitlines():
        if not line or len(line) < 67 or line[64:66] != "  ":
            raise VerificationError("ARCHIVE_INVALID: malformed SHA256SUMS")
        digest, raw_path = line[:64], line[66:]
        if not SHA256.fullmatch(digest):
            raise VerificationError("ARCHIVE_INVALID: malformed inner digest")
        path = _normalized_member(ARCHIVE_PREFIX + raw_path)
        key = path.casefold()
        if key in collision_keys:
            raise VerificationError("ARCHIVE_INVALID: duplicate checksum path")
        collision_keys.add(key)
        checksums[path] = digest
    if not checksums:
        raise VerificationError("ARCHIVE_INVALID: empty SHA256SUMS")
    return checksums


def _validated_payloads(
    archive: zipfile.ZipFile, members: dict[str, _Member]
) -> tuple[dict[str, bytes], dict[str, object]]:
    sums_member = members.get("SHA256SUMS")
    if sums_member is None:
        raise VerificationError("ARCHIVE_INVALID: missing SHA256SUMS")
    checksums = _parse_checksums(_read_member(archive, sums_member))
    if set(checksums) != APPROVED_PATHS - {"SHA256SUMS"}:
        raise VerificationError("ARCHIVE_INVALID: checksum inventory mismatch")

    payloads: dict[str, bytes] = {}
    for path, member in members.items():
        data = _read_member(archive, member)
        if path != "SHA256SUMS" and hashlib.sha256(data).hexdigest() != checksums[path]:
            raise VerificationError("ARCHIVE_INVALID: inner checksum mismatch")
        payloads[path] = data

    manifest_path = "manifests/release-manifest.json"
    try:
        manifest = json.loads(payloads[manifest_path])
        schema = json.loads(RELEASE_SCHEMA.read_bytes())
        Draft202012Validator(schema).validate(manifest)
    except (KeyError, json.JSONDecodeError, UnicodeDecodeError, ValidationError) as exc:
        raise VerificationError("ARCHIVE_INVALID: release manifest is invalid") from exc

    if manifest["compose_sha256"] != hashlib.sha256(payloads["compose.yaml"]).hexdigest():
        raise VerificationError("ARCHIVE_INVALID: Compose digest mismatch")
    for launcher, digest in manifest["launchers"].items():
        if digest != hashlib.sha256(payloads[launcher]).hexdigest():
            raise VerificationError("ARCHIVE_INVALID: launcher digest mismatch")
    migration_sums = {
        item["name"]: item["sha256"] for item in manifest["migrations"]
    }
    for name, digest in migration_sums.items():
        if digest != hashlib.sha256(payloads[f"migrations/{name}"]).hexdigest():
            raise VerificationError("ARCHIVE_INVALID: migration digest mismatch")
    try:
        declared_migrations = json.loads(payloads["manifests/migration-checksums.json"])
    except (KeyError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise VerificationError("ARCHIVE_INVALID: migration checksum manifest is invalid") from exc
    if declared_migrations != migration_sums:
        raise VerificationError("ARCHIVE_INVALID: migration manifests disagree")
    return payloads, manifest


def _rename_noreplace(parent_fd: int, temporary_name: str, destination_name: str) -> None:
    renameat2 = getattr(_LIBC, "renameat2", None)
    if renameat2 is None:
        raise VerificationError("ARCHIVE_INVALID: atomic no-replace publication unavailable")
    result = renameat2(
        parent_fd,
        os.fsencode(temporary_name),
        parent_fd,
        os.fsencode(destination_name),
        _RENAME_NOREPLACE,
    )
    if result != 0:
        error = ctypes.get_errno()
        if error == errno.EEXIST:
            raise VerificationError("ARCHIVE_INVALID: destination appeared during publication")
        raise VerificationError(
            f"ARCHIVE_INVALID: atomic publication failed with errno {error}"
        )


def _materialize(payloads: dict[str, bytes], destination: Path) -> None:
    parent = destination.parent
    if not destination.name or not parent.is_dir():
        raise VerificationError("ARCHIVE_INVALID: destination must be new")
    try:
        parent_fd = os.open(parent, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW)
    except OSError as exc:
        raise VerificationError("ARCHIVE_INVALID: destination parent is unsafe") from exc
    parent_identity = os.fstat(parent_fd)
    temporary: Path | None = None
    try:
        try:
            os.stat(destination.name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise VerificationError("ARCHIVE_INVALID: destination already exists")
        temporary = Path(tempfile.mkdtemp(prefix=f".{destination.name}.", dir=parent))
        current_parent = parent.stat(follow_symlinks=False)
        if (current_parent.st_dev, current_parent.st_ino) != (
            parent_identity.st_dev,
            parent_identity.st_ino,
        ):
            raise VerificationError("ARCHIVE_INVALID: destination parent changed")
        os.chmod(temporary, 0o700)
        for relative, data in sorted(payloads.items()):
            target = temporary.joinpath(*PurePosixPath(relative).parts)
            target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            with target.open("xb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(target, 0o600)
        _rename_noreplace(parent_fd, temporary.name, destination.name)
        os.fsync(parent_fd)
        temporary = None
    except Exception:
        if temporary is not None:
            shutil.rmtree(temporary, ignore_errors=True)
        raise
    finally:
        os.close(parent_fd)


def verify_installer(
    archive: Path, expected_sha256: str, destination: Path
) -> VerifiedRelease:
    archive = Path(archive)
    destination = Path(destination)
    if not SHA256.fullmatch(expected_sha256):
        raise VerificationError("RELEASE_DIGEST_MISMATCH: expected digest is malformed")
    try:
        captured = _capture_archive(archive)
        archive_handle = io.BytesIO(captured)
        actual_sha256 = _handle_sha256(archive_handle)
        if actual_sha256 != expected_sha256:
            raise VerificationError("RELEASE_DIGEST_MISMATCH: outer digest mismatch")
        _preflight_zip(captured)
        with zipfile.ZipFile(archive_handle, "r") as package:
            members = _inspect_archive(package)
            payloads, manifest = _validated_payloads(package, members)
    except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
        raise VerificationError("ARCHIVE_INVALID: unreadable ZIP") from exc
    try:
        _materialize(payloads, destination)
    except VerificationError:
        raise
    except OSError as exc:
        raise VerificationError("ARCHIVE_INVALID: materialization failed") from exc
    return VerifiedRelease(
        schema_version="verified-release-v1",
        archive_sha256=actual_sha256,
        destination=str(destination.resolve()),
        file_count=len(payloads),
        product_version=str(manifest["product_version"]),
        git_commit=str(manifest["git_commit"]),
        git_tree=str(manifest["git_tree"]),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("expected_sha256")
    parser.add_argument("destination", type=Path)
    args = parser.parse_args(argv)
    try:
        result = verify_installer(args.archive, args.expected_sha256, args.destination)
    except (OSError, VerificationError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(asdict(result), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
