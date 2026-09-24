"""Small deterministic artifact writer for the unverified Liqvera MVP."""

from __future__ import annotations

import hashlib
import os
import shutil
import stat
import tempfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING
from zipfile import ZIP_STORED, ZipFile, ZipInfo

if TYPE_CHECKING:
    from mee_evidence_report.model import BuiltMvpReport

_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
_ZIP_MODE = stat.S_IFREG | 0o644


@dataclass(frozen=True, slots=True)
class MvpArtifact:
    """Paths and external digests for a written prototype artifact."""

    report_path: Path
    bundle_path: Path
    report_sha256: str
    bundle_sha256: str


def _validate_relative_path(relative: Path) -> str:
    member = relative.as_posix()
    pure = PurePosixPath(member)
    if (
        not member
        or member.startswith("/")
        or "\\" in member
        or "\x00" in member
        or any(part in {"", ".", ".."} for part in pure.parts)
        or (pure.parts and pure.parts[0].endswith(":"))
    ):
        raise ValueError(f"unsafe package path: {member!r}")
    return member


def _package_members(package_root: Path) -> list[tuple[str, bytes]]:
    if package_root.is_symlink():
        raise ValueError("package root must not be a symlink")
    if not package_root.is_dir():
        raise ValueError("package root must be a directory")

    members: list[tuple[str, bytes]] = []
    for current, directories, files in os.walk(package_root, followlinks=False):
        current_path = Path(current)
        for name in directories:
            path = current_path / name
            relative = path.relative_to(package_root)
            _validate_relative_path(relative)
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise ValueError(f"package symlink is forbidden: {relative.as_posix()}")
            if not stat.S_ISDIR(mode):
                raise ValueError(f"package entry is not a directory: {relative.as_posix()}")
        for name in files:
            path = current_path / name
            relative = path.relative_to(package_root)
            member = _validate_relative_path(relative)
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise ValueError(f"package symlink is forbidden: {member}")
            if not stat.S_ISREG(mode):
                raise ValueError(f"package entry is not a regular file: {member}")
            members.append((f"sealed-input/{member}", path.read_bytes()))
    return sorted(members, key=lambda item: item[0])


def _zip_info(member: str) -> ZipInfo:
    info = ZipInfo(member, date_time=_ZIP_TIMESTAMP)
    info.compress_type = ZIP_STORED
    info.create_system = 3
    info.external_attr = _ZIP_MODE << 16
    return info


def _bundle_bytes(report_bytes: bytes, package_root: Path) -> bytes:
    members = [("report.json", report_bytes), *_package_members(package_root)]
    target = BytesIO()
    with ZipFile(target, mode="w", compression=ZIP_STORED, allowZip64=False) as archive:
        for member, payload in sorted(members, key=lambda item: item[0]):
            archive.writestr(_zip_info(member), payload)
    return target.getvalue()


def _path_exists(path: Path) -> bool:
    return os.path.lexists(path)


def write_mvp_artifact(
    output_dir: Path,
    built: BuiltMvpReport,
    package_root: Path,
) -> MvpArtifact:
    """Write one no-clobber directory with canonical report and deterministic ZIP bytes."""

    output_dir = Path(output_dir)
    package_root = Path(package_root)
    if _path_exists(output_dir):
        raise FileExistsError(f"output already exists: {output_dir}")

    report_bytes = built.report_bytes
    report_sha256 = hashlib.sha256(report_bytes).hexdigest()
    if report_sha256 != built.report_sha256:
        raise ValueError("built report digest does not match report bytes")
    bundle_bytes = _bundle_bytes(report_bytes, package_root)
    bundle_sha256 = hashlib.sha256(bundle_bytes).hexdigest()

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.", dir=output_dir.parent))
    try:
        (staging / "report.json").write_bytes(report_bytes)
        (staging / "evidence.zip").write_bytes(bundle_bytes)
        if _path_exists(output_dir):
            raise FileExistsError(f"output already exists: {output_dir}")
        staging.rename(output_dir)
    except BaseException:
        if staging.exists():
            shutil.rmtree(staging)
        raise

    return MvpArtifact(
        report_path=output_dir / "report.json",
        bundle_path=output_dir / "evidence.zip",
        report_sha256=report_sha256,
        bundle_sha256=bundle_sha256,
    )
