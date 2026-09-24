"""Deterministic bounded bundles and archive-first, offline recalculation."""

from __future__ import annotations

import fcntl
import os
import shutil
import stat
import struct
import tempfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from uuid import UUID
from zipfile import BadZipFile, ZIP_STORED, ZipFile, ZipInfo

from mee_contracts.exact import ExactDecimal
from mee_readonly_analyzer.vwap import Side

from mee_evidence_report.canonical import canonical_json_bytes
from mee_evidence_report.evidence_io import (
    MAX_BUNDLE_BYTES, MAX_MEMBER_BYTES, MAX_MEMBERS, EvidenceRejected, digest,
    identifier, safe_member, strict_json, timestamp_ms,
)
from mee_evidence_report.report import BuiltReport, ReportRequest, build_inspected_report
from mee_evidence_report.schema_validation import validate
from mee_evidence_report.sealed_input import BASE_MEMBERS, inspect_members

STAMP = (1980, 1, 1, 0, 0, 0)
MODE = (stat.S_IFREG | 0o644) << 16
OUTER_NAMES = {"manifest.json", "report.json", "algorithm.json", "runtime-dependencies.txt"}
ALLOWED_NAMES = OUTER_NAMES | {f"sealed-input/{name}" for name in BASE_MEMBERS} | {
    "sealed-input/source/mapping-evidence.json"}


def _zip(members: dict[str, bytes]) -> bytes:
    if len(members) > MAX_MEMBERS or sum(map(len, members.values())) > MAX_BUNDLE_BYTES:
        raise EvidenceRejected("INVALID_DATASET")
    output = BytesIO()
    with ZipFile(output, "w", compression=ZIP_STORED, allowZip64=False) as archive:
        for name, raw in sorted(members.items()):
            if safe_member(name) not in ALLOWED_NAMES or len(raw) > MAX_MEMBER_BYTES:
                raise EvidenceRejected("INVALID_DATASET")
            entry = ZipInfo(name, date_time=STAMP)
            entry.compress_type = ZIP_STORED
            entry.create_system = 3
            entry.external_attr = MODE
            archive.writestr(entry, raw)
    raw = output.getvalue()
    if len(raw) > MAX_BUNDLE_BYTES:
        raise EvidenceRejected("INVALID_DATASET")
    return raw


def build_bundle(built: BuiltReport) -> bytes:
    if digest(built.report_bytes) != built.report_sha256:
        raise EvidenceRejected("INVALID_DATASET")
    members = {f"sealed-input/{name}": raw for name, raw in built.input_members.items()}
    members.update({"report.json": built.report_bytes, "algorithm.json": built.algorithm_bytes,
                    "runtime-dependencies.txt": built.dependency_bytes})
    manifest = {
        "schema": "mee-evidence-bundle-manifest/v1", "serialization_version": "canonical-json/v1",
        "report_sha256": built.report_sha256,
        "members": [{"path": name, "sha256": digest(raw), "length": len(raw)}
                    for name, raw in sorted(members.items())],
    }
    validate("bundle-manifest.schema.json", manifest)
    members["manifest.json"] = canonical_json_bytes(manifest)
    return _zip(members)


def _read_archive(raw: bytes) -> dict[str, bytes]:
    """Reject hazardous central/local metadata before reading any member body."""
    if type(raw) is not bytes or not 22 <= len(raw) <= MAX_BUNDLE_BYTES:
        raise EvidenceRejected("INVALID_DATASET")
    # Require one single-disk EOCD at the exact end; no ZIP64 or archive comment.
    if raw[-22:-18] != b"PK\x05\x06":
        raise EvidenceRejected("INVALID_DATASET")
    _, disk, cd_disk, disk_count, total_count, cd_size, cd_offset, comment_len = struct.unpack(
        "<4s4H2LH", raw[-22:])
    if (disk or cd_disk or disk_count != total_count or not 4 <= total_count <= MAX_MEMBERS
            or comment_len or cd_offset + cd_size != len(raw) - 22):
        raise EvidenceRejected("INVALID_DATASET")
    result = {}
    with ZipFile(BytesIO(raw), "r", allowZip64=False) as archive:
        infos = archive.infolist()
        if len(infos) != total_count or archive.comment:
            raise EvidenceRejected("INVALID_DATASET")
        total = 0
        cursor = 0
        names = []
        for info in infos:
            name = safe_member(info.filename)
            if (name not in ALLOWED_NAMES or name in names or info.orig_filename != name
                    or info.compress_type != ZIP_STORED or info.file_size != info.compress_size
                    or not 1 <= info.file_size <= MAX_MEMBER_BYTES
                    or info.flag_bits != 0 or info.extra or info.comment
                    or info.create_system != 3 or info.external_attr != MODE or info.date_time != STAMP
                    or info.header_offset != cursor or info.header_offset + 30 > cd_offset):
                raise EvidenceRejected("INVALID_DATASET")
            names.append(name)
            header = struct.unpack("<4s5H3L2H", raw[cursor:cursor + 30])
            signature, version, flags, compression, _, _, crc, size, unpacked, name_size, extra_size = header
            encoded = name.encode("ascii")
            if (signature != b"PK\x03\x04" or version != 20 or flags != 0 or compression != ZIP_STORED
                    or crc != info.CRC or size != info.file_size or unpacked != info.file_size
                    or name_size != len(encoded) or extra_size != 0
                    or raw[cursor + 30:cursor + 30 + name_size] != encoded):
                raise EvidenceRejected("INVALID_DATASET")
            cursor += 30 + name_size + info.file_size
            total += info.file_size
            if cursor > cd_offset or total > MAX_BUNDLE_BYTES:
                raise EvidenceRejected("INVALID_DATASET")
        if names != sorted(names) or cursor != cd_offset or not OUTER_NAMES <= set(names):
            raise EvidenceRejected("INVALID_DATASET")
        for info in infos:
            with archive.open(info) as member:
                content = member.read(info.file_size + 1)
                if len(content) != info.file_size:
                    raise EvidenceRejected("INVALID_DATASET")
                result[info.filename] = content
    # This also rejects central-directory tricks, prepended/trailing bytes,
    # unexpected metadata, overlapping members, and alternative serialization.
    if _zip(result) != raw:
        raise EvidenceRejected("INVALID_DATASET")
    return result


def verify_bundle_bytes(raw: bytes, *, expected_report_sha256: str | None = None) -> BuiltReport:
    """Verify relative integrity and reproduce every report field, without egress."""
    try:
        members = _read_archive(raw)
        manifest = strict_json(members["manifest.json"])
        validate("bundle-manifest.schema.json", manifest)
        if canonical_json_bytes(manifest) != members["manifest.json"]:
            raise EvidenceRejected("INVALID_DATASET")
        declared = manifest["members"]
        if [item["path"] for item in declared] != sorted(set(members) - {"manifest.json"}):
            raise EvidenceRejected("INVALID_DATASET")
        for item in declared:
            content = members[item["path"]]
            if len(content) != item["length"] or digest(content) != item["sha256"]:
                raise EvidenceRejected("INVALID_DATASET")
        report = strict_json(members["report.json"])
        validate("report.schema.json", report)
        report_hash = digest(members["report.json"])
        if (manifest["report_sha256"] != report_hash
                or (expected_report_sha256 is not None and expected_report_sha256 != report_hash)
                or canonical_json_bytes(report) != members["report.json"]):
            raise EvidenceRejected("INVALID_DATASET")
        validate("algorithm.schema.json", strict_json(members["algorithm.json"]))
        inputs = {name.removeprefix("sealed-input/"): content for name, content in members.items()
                  if name.startswith("sealed-input/")}
        inspected = inspect_members(inputs)
        request = ReportRequest(
            UUID(identifier(report["report_id"])), Side(report["request"]["side"]),
            ExactDecimal.parse(report["request"]["quantity_base"]),
            report["reproducibility"]["engine_commit"], timestamp_ms(report["source"]["created_at"]),
        )
        rebuilt = build_inspected_report(inspected, request)
        if (rebuilt.report_bytes != members["report.json"]
                or rebuilt.algorithm_bytes != members["algorithm.json"]
                or rebuilt.dependency_bytes != members["runtime-dependencies.txt"]
                or build_bundle(rebuilt) != raw):
            raise EvidenceRejected("INVALID_DATASET")
        return rebuilt
    except EvidenceRejected:
        raise
    except (BadZipFile, OSError, ValueError, TypeError, KeyError, struct.error, RuntimeError) as error:
        raise EvidenceRejected("INVALID_DATASET") from error


def verify_bundle(path: Path, *, expected_report_sha256: str | None = None) -> BuiltReport:
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise EvidenceRejected("INVALID_DATASET")
            raw = stream.read(MAX_BUNDLE_BYTES + 1)
    except OSError as error:
        raise EvidenceRejected("INVALID_DATASET") from error
    return verify_bundle_bytes(raw, expected_report_sha256=expected_report_sha256)


@dataclass(frozen=True)
class PublishedArtifact:
    report_id: str
    report_sha256: str
    bundle_sha256: str
    report_size_bytes: int
    bundle_size_bytes: int


def publish_artifact(root: Path, built: BuiltReport) -> PublishedArtifact:
    """Write, fsync, verify, then atomically publish under the report UUID."""
    report_id = identifier(built.document["report_id"])
    root = Path(root)
    if not root.is_absolute() or root.is_symlink() or not root.is_dir():
        raise EvidenceRejected("STORAGE_UNAVAILABLE")
    target = root / report_id
    lock = root / f".{report_id}.lock"
    lock_fd = _open_report_lock(lock)
    staging = None
    try:
        if os.path.lexists(target):
            raise FileExistsError("immutable report already exists")
        bundle = build_bundle(built)
        staging = Path(tempfile.mkdtemp(prefix=f".{report_id}.", dir=root))
        staging.chmod(0o750)
        for name, payload in (("report.json", built.report_bytes), ("evidence.zip", bundle)):
            with (staging / name).open("xb") as stream:
                os.fchmod(stream.fileno(), 0o640)
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            if digest((staging / name).read_bytes()) != digest(payload):
                raise EvidenceRejected("ARTIFACT_INTEGRITY_FAILED")
        verify_bundle(staging / "evidence.zip", expected_report_sha256=built.report_sha256)
        _fsync_directory(staging)
        if os.path.lexists(target):
            raise FileExistsError("immutable report already exists")
        staging.rename(target)
        _fsync_directory(root)
        return PublishedArtifact(report_id, built.report_sha256, digest(bundle),
                                 len(built.report_bytes), len(bundle))
    finally:
        if staging is not None and staging.exists():
            shutil.rmtree(staging)
        os.close(lock_fd)


def read_published(root: Path, report_id: str) -> tuple[BuiltReport, PublishedArtifact]:
    identifier(report_id)
    # The artifact reader has a larger per-file limit than sealed inputs.
    path = root / report_id
    if path.is_symlink() or not path.is_dir() or set(os.listdir(path)) != {"report.json", "evidence.zip"}:
        raise EvidenceRejected("ARTIFACT_INTEGRITY_FAILED")
    built = verify_bundle(path / "evidence.zip")
    fd = os.open(path / "report.json", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise EvidenceRejected("ARTIFACT_INTEGRITY_FAILED")
        report_bytes = stream.read(MAX_MEMBER_BYTES + 1)
    if built.document["report_id"] != report_id or report_bytes != built.report_bytes:
        raise EvidenceRejected("ARTIFACT_INTEGRITY_FAILED")
    # The deterministic regenerated ZIP is byte-identical to the verified input.
    bundle = build_bundle(built)
    return built, PublishedArtifact(report_id, built.report_sha256, digest(bundle), len(report_bytes), len(bundle))


def delete_published(root: Path, report_id: str) -> bool:
    """Remove one guarded report directory, without recursive traversal.

    The caller owns ledger retention authorization. The filesystem boundary
    accepts only the two known regular artifact files, including a subset left
    by interrupted deletion. Neither a link nor an unexpected member is removed.
    """
    identifier(report_id)
    root = Path(root)
    if not root.is_absolute():
        raise EvidenceRejected("STORAGE_UNAVAILABLE")
    root_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    lock_name = f".{report_id}.lock"
    lock_fd = None
    directory_fd = None
    try:
        # Use the publication lock across processes, and descriptor-relative
        # operations so no supplied path can escape the configured root.
        lock_fd = _open_report_lock(lock_name, root_fd=root_fd)
        try:
            before = os.stat(report_id, dir_fd=root_fd, follow_symlinks=False)
        except FileNotFoundError:
            return False
        if not stat.S_ISDIR(before.st_mode):
            raise EvidenceRejected("ARTIFACT_INTEGRITY_FAILED")
        directory_fd = os.open(report_id, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                               dir_fd=root_fd)
        opened = os.fstat(directory_fd)
        if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
            raise EvidenceRejected("ARTIFACT_INTEGRITY_FAILED")
        names = set(os.listdir(directory_fd))
        if not names <= {"report.json", "evidence.zip"}:
            raise EvidenceRejected("ARTIFACT_INTEGRITY_FAILED")
        entries = {}
        # Preflight the entire directory before the first unlink; never descend
        # into any member and never invoke a recursive cleanup utility.
        for name in names:
            entry = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            if not stat.S_ISREG(entry.st_mode):
                raise EvidenceRejected("ARTIFACT_INTEGRITY_FAILED")
            entries[name] = (entry.st_dev, entry.st_ino)
        for name in sorted(names):
            current = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            if (not stat.S_ISREG(current.st_mode)
                    or (current.st_dev, current.st_ino) != entries[name]):
                raise EvidenceRejected("ARTIFACT_INTEGRITY_FAILED")
            os.unlink(name, dir_fd=directory_fd)
        os.fsync(directory_fd)
        current_directory = os.stat(report_id, dir_fd=root_fd, follow_symlinks=False)
        if (not stat.S_ISDIR(current_directory.st_mode)
                or (current_directory.st_dev, current_directory.st_ino)
                != (opened.st_dev, opened.st_ino)):
            raise EvidenceRejected("ARTIFACT_INTEGRITY_FAILED")
        os.rmdir(report_id, dir_fd=root_fd)
        os.fsync(root_fd)
        return True
    finally:
        try:
            if directory_fd is not None:
                os.close(directory_fd)
            if lock_fd is not None:
                os.close(lock_fd)
        finally:
            os.close(root_fd)


def _open_report_lock(path: str | Path, *, root_fd: int | None = None) -> int:
    """Use a stable lock inode; process exit automatically releases ownership."""
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK,
                 0o600, dir_fd=root_fd)
    try:
        metadata = os.fstat(fd)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise EvidenceRejected("ARTIFACT_INTEGRITY_FAILED")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise FileExistsError("report operation already in progress") from None
    except BaseException:
        os.close(fd)
        raise
    # Never unlink the lock inode: another process may already have it open.
    # Reusing it prevents independent locks after crash recovery or contention.
    return fd


def _fsync_directory(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
