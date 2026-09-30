#!/usr/bin/env python3
"""Build the deterministic, offline Liqvera Linux installer archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess  # nosec B404 - fixed Git argv reads the frozen local repository
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "liqvera-installer-0.0.2/"
ARCHIVE = "liqvera-installer-0.0.2.zip"
IMAGE_NAMES = ("edge", "web", "gateway", "capture", "report", "postgres")
IMAGE = re.compile(r"[^@\s]+@sha256:[0-9a-f]{64}\Z")
MIGRATIONS = (
    "001_ledger.sql", "002_fix_immutable_ledger_identity.sql",
    "003_live_grant_consumption.sql", "004_receipt_confirmation_provenance.sql",
    "005_receipt_confirmation_count.sql",
)
SOURCE_MAP = {
    "install.sh": "installer/install.sh", "Caddyfile": "installer/Caddyfile",
    "lib/common.sh": "installer/lib/common.sh", "lib/runtime.py": "installer/lib/runtime.py",
    "lib/orchestration.py": "installer/lib/orchestration.py",
    "lib/lifecycle.py": "installer/lib/lifecycle.py", "liqvera.sh": "installer/liqvera.sh",
    "compose.yaml": "installer/compose.yaml",
    "config/liqvera.env.template": "installer/config/liqvera.env.template",
    "config/ports.env.template": "installer/config/ports.env.template",
    "schemas/config.schema.json": "installer/schemas/config.schema.json",
    "schemas/install-state.schema.json": "installer/schemas/install-state.schema.json",
    "schemas/release-manifest.schema.json": "installer/schemas/release-manifest.schema.json",
    "manifests/v0.0.2.json": "installer/manifests/v0.0.2.json",
    "manifests/image-lock-v0.0.2.json": "installer/manifests/image-lock-v0.0.2.json",
    "systemd/liqvera.service.in": "installer/systemd/liqvera.service.in",
    **{f"migrations/{name}": f"apps/mezo-gateway/migrations/{name}" for name in MIGRATIONS},
}


class BuildError(ValueError):
    pass


@dataclass(frozen=True)
class BuildResult:
    archive: Path
    checksum: Path
    sha256: str
    inventory_sha256: str


def _git(*args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=ROOT, text=True).strip()  # nosec B603


def _git_status() -> str:
    return _git("status", "--porcelain", "--untracked-files=all")


def _images(path: Path) -> dict[str, str]:
    try:
        value = json.loads(path.read_bytes())
    except (OSError, json.JSONDecodeError) as exc:
        raise BuildError("image lock is unreadable") from exc
    if (not isinstance(value, dict) or set(value) != set(IMAGE_NAMES)
            or any(not isinstance(item, str) or not IMAGE.fullmatch(item) for item in value.values())):
        raise BuildError("image lock must contain exact immutable digest references")
    return value


def _tracked_bytes(commit: str, path: str) -> bytes:
    try:
        return subprocess.check_output(("git", "show", f"{commit}:{path}"), cwd=ROOT)  # nosec B603
    except subprocess.CalledProcessError as exc:
        raise BuildError(f"required tracked source is missing: {path}") from exc


def _manifest(commit: str, tree: str, payloads: dict[str, bytes], images: dict[str, str]) -> bytes:
    migrations = [{"name": name, "sha256": hashlib.sha256(payloads[f"migrations/{name}"]).hexdigest()}
                  for name in MIGRATIONS]
    value = {
        "schema_version": "liqvera-installer-release/v1", "product_version": "0.0.2",
        "git_commit": commit, "git_tree": tree,
        "compose_sha256": hashlib.sha256(payloads["compose.yaml"]).hexdigest(),
        "launchers": {name: hashlib.sha256(payloads[name]).hexdigest()
                      for name in ("install.sh", "liqvera.sh")},
        "images": images, "migrations": migrations,
        "database_compatibility": {"accepted_migrations": migrations, "down_migrations": False},
        "supported_linux": {"architectures": ["amd64", "arm64"],
                            "distributions": ["ubuntu", "debian", "fedora", "rhel"]},
    }
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def build_installer(source_commit: str, output: Path, image_lock: Path) -> BuildResult:
    head = _git("rev-parse", "HEAD")
    if source_commit != head or not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        raise BuildError("source commit must equal exact HEAD")
    if _git_status():
        raise BuildError("worktree must be clean")
    output = Path(output)
    try:
        output.mkdir(mode=0o700)
    except FileExistsError as exc:
        raise BuildError("output directory must not already exist") from exc
    images = _images(Path(image_lock))
    tree = _git("rev-parse", f"{source_commit}^{{tree}}")
    payloads = {target: _tracked_bytes(source_commit, source) for target, source in SOURCE_MAP.items()}
    payloads["LICENSE-NOTICE.md"] = (
        b"Liqvera installer distribution notice\n\nNo license grant is created by this package. "
        b"See the canonical repository for component provenance and terms.\n"
    )
    payloads["manifests/release-manifest.json"] = _manifest(source_commit, tree, payloads, images)
    migrations = json.loads(payloads["manifests/release-manifest.json"])["migrations"]
    payloads["manifests/migration-checksums.json"] = (
        json.dumps({item["name"]: item["sha256"] for item in migrations}, sort_keys=True,
                   separators=(",", ":")) + "\n"
    ).encode()
    sums = "".join(f"{hashlib.sha256(data).hexdigest()}  {name}\n"
                   for name, data in sorted(payloads.items()))
    payloads["SHA256SUMS"] = sums.encode()
    timestamp = int(_git("show", "-s", "--format=%ct", source_commit))
    date = datetime.fromtimestamp(timestamp, UTC)
    date_tuple = (date.year, date.month, date.day, date.hour, date.minute, date.second // 2 * 2)
    archive = output / ARCHIVE
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9,
                         allowZip64=False) as package:
        for name, data in sorted(payloads.items()):
            info = zipfile.ZipInfo(PREFIX + name, date_time=date_tuple)
            info.create_system = 3
            mode = 0o755 if name in {"install.sh", "liqvera.sh"} else 0o644
            info.external_attr = (0o100000 | mode) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            info.extra = b""
            info.comment = b""
            package.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum = output / f"{ARCHIVE}.sha256"
    checksum.write_text(f"{digest}  {ARCHIVE}\n")
    return BuildResult(archive, checksum, digest, hashlib.sha256(payloads["SHA256SUMS"]).hexdigest())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--image-lock", type=Path, required=True)
    args = parser.parse_args()
    result = build_installer(args.source_commit, args.output, args.image_lock)
    print(json.dumps({"archive": str(result.archive), "sha256": result.sha256,
                      "inventory_sha256": result.inventory_sha256}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
