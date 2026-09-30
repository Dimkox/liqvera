#!/usr/bin/env python3
"""Closed Linux preflight/configuration helper for the Liqvera installer."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import platform
import re
import secrets
import socket
import stat
import subprocess  # nosec B404: every executable and argv is closed below.
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable

from jsonschema import Draft202012Validator, ValidationError

INSTALLER_ROOT = Path(__file__).resolve().parents[1]
CONFIG_SCHEMA = INSTALLER_ROOT / "schemas" / "config.schema.json"
STATE_SCHEMA = INSTALLER_ROOT / "schemas" / "install-state.schema.json"
MIN_BASH = (5, 2, 0)
MIN_DOCKER = (27, 0, 0)
MIN_COMPOSE = (2, 30, 0)
MIN_DISK_BYTES = 4 * 1024**3
MIN_MEMORY_BYTES = 2 * 1024**3
SUPPORTED_LINUX = {
    "ubuntu": {"22.04", "24.04"},
    "debian": {"12"},
    "fedora": {"40", "41"},
    "rhel": {"9"},
}
ARCHITECTURES = {"x86_64": "amd64", "aarch64": "arm64"}
NETWORK_FILESYSTEMS = {"nfs", "nfs4", "cifs", "smb3", "sshfs", "9p", "fuse.sshfs"}
SAFE_ENV = {"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C"}
FORBIDDEN_AMBIENT_ENV = {
    "DOCKER_HOST", "DOCKER_CONTEXT", "COMPOSE_FILE", "COMPOSE_PROFILES",
    "COMPOSE_PROJECT_NAME", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
    "NO_PROXY", "http_proxy", "https_proxy", "all_proxy", "no_proxy",
    "BASH_ENV", "ENV",
}
READ_ONLY_COMMANDS = {
    ("/usr/bin/docker", "--host", "unix:///var/run/docker.sock", "version", "--format", "{{.Server.Version}}"),
    ("/usr/bin/docker", "--host", "unix:///var/run/docker.sock", "compose", "version", "--short"),
    ("/usr/bin/docker", "--host", "unix:///var/run/docker.sock", "info", "--format", "{{.ServerVersion}}"),
}
DEPENDENCY_COMMANDS = {
    "ubuntu": ("/usr/bin/sudo", "--", "/usr/bin/apt-get", "install", "docker-ce", "docker-compose-plugin"),
    "debian": ("/usr/bin/sudo", "--", "/usr/bin/apt-get", "install", "docker-ce", "docker-compose-plugin"),
    "fedora": ("/usr/bin/sudo", "--", "/usr/bin/dnf", "install", "docker-ce", "docker-compose-plugin"),
    "rhel": ("/usr/bin/sudo", "--", "/usr/bin/dnf", "install", "docker-ce", "docker-compose-plugin"),
}
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class InstallerError(RuntimeError):
    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        super().__init__(f"{code}: {detail}")


def _load_schema(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _reject_duplicate_key(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise InstallerError("CONFIG_INVALID", "duplicate JSON key")
        result[key] = value
    return result


def load_json_bytes(data: bytes, code: str, *, maximum: int = 1024 * 1024) -> object:
    if len(data) > maximum:
        raise InstallerError(code, "input exceeds bounded size")
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=_reject_duplicate_key)
    except InstallerError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InstallerError(code, "JSON is malformed") from exc


def _validate(schema_path: Path, value: dict[str, object], code: str) -> None:
    try:
        Draft202012Validator(_load_schema(schema_path)).validate(value)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        raise InstallerError(code, "closed schema validation failed") from exc


def _version(value: object) -> tuple[int, int, int]:
    match = re.fullmatch(
        r"([0-9]+)\.([0-9]+)(?:\.([0-9]+))?(?:\([0-9]+\))?(?:[-+][A-Za-z0-9_.-]+)?",
        str(value),
    )
    if match is None:
        raise InstallerError("DEPENDENCY_MISSING", "dependency version is malformed")
    return tuple(int(part or "0") for part in match.groups())  # type: ignore[return-value]


def _validate_install_root(path_value: object, filesystem_type: object) -> Path:
    path = Path(str(path_value))
    if not path.is_absolute() or path == Path("/") or "\x00" in str(path):
        raise InstallerError("UNSAFE_INSTALL_ROOT", "install root must be a narrow absolute path")
    if str(filesystem_type) in NETWORK_FILESYSTEMS:
        raise InstallerError("UNSAFE_INSTALL_ROOT", "network filesystems are forbidden")
    candidate = Path("/")
    for part in path.parts[1:]:
        candidate /= part
        try:
            item = candidate.lstat()
        except FileNotFoundError:
            break
        if stat.S_ISLNK(item.st_mode):
            raise InstallerError("UNSAFE_INSTALL_ROOT", "link path component")
        writable = stat.S_IMODE(item.st_mode) & 0o022
        trusted_sticky_root = item.st_uid == 0 and bool(item.st_mode & stat.S_ISVTX)
        if writable and not trusted_sticky_root:
            raise InstallerError("UNSAFE_INSTALL_ROOT", "writable path ancestry")
    existing = path
    while not existing.exists():
        existing = existing.parent
    parent = existing if existing.is_dir() else existing.parent
    parent_stat = parent.stat()
    if parent_stat.st_uid != os.getuid() or parent_stat.st_mode & stat.S_IWOTH:
        raise InstallerError("UNSAFE_INSTALL_ROOT", "unsafe existing ancestor")
    if path.exists() and any(path.iterdir()):
        state_path = path / "state" / "install-state.json"
        config_path = path / "config" / "runtime.env"
        if not state_path.is_file() or not config_path.is_file():
            raise InstallerError("UNSAFE_INSTALL_ROOT", "existing directory is not a complete Liqvera install")
        state_value = load_json_bytes(_safe_regular_bytes(state_path, "CONFIG_INVALID"), "CONFIG_INVALID")
        if not isinstance(state_value, dict):
            raise InstallerError("CONFIG_INVALID", "existing state is invalid")
        _validate(STATE_SCHEMA, state_value, "CONFIG_INVALID")
        if state_value.get("install_root") != str(path.resolve(strict=False)):
            raise InstallerError("UNSAFE_INSTALL_ROOT", "existing state belongs to another root")
    return path.resolve(strict=False)


def preflight(request: dict[str, object], facts: dict[str, object]) -> dict[str, object]:
    if set(request) != {"schema_version", "install_root", "config"} or request.get("schema_version") != "liqvera-preflight-request/v1":
        raise InstallerError("CONFIG_INVALID", "preflight request is not closed")
    if facts.get("kernel") != "Linux":
        raise InstallerError("UNSUPPORTED_LINUX", "Linux is required")
    distribution = str(facts.get("distribution", ""))
    distro_version = str(facts.get("distribution_version", ""))
    machine = str(facts.get("architecture", ""))
    if distro_version not in SUPPORTED_LINUX.get(distribution, set()) or machine not in ARCHITECTURES:
        raise InstallerError("UNSUPPORTED_LINUX", "distribution/version/architecture is unsupported")
    dependency_checks = (
        (_version(facts.get("bash_version")), MIN_BASH),
        (_version(facts.get("docker_version")), MIN_DOCKER),
        (_version(facts.get("compose_version")), MIN_COMPOSE),
    )
    if any(observed < minimum for observed, minimum in dependency_checks):
        raise InstallerError("DEPENDENCY_MISSING", "dependency below reviewed floor")
    if facts.get("daemon_reachable") is not True:
        raise InstallerError("DEPENDENCY_MISSING", "local Docker daemon is unavailable")
    if facts.get("docker_endpoint") != "unix:///var/run/docker.sock":
        raise InstallerError("DEPENDENCY_MISSING", "only the reviewed local Docker socket is allowed")
    if int(facts.get("disk_bytes", 0)) < MIN_DISK_BYTES or int(facts.get("memory_bytes", 0)) < MIN_MEMORY_BYTES:
        raise InstallerError("DEPENDENCY_MISSING", "host resource floor is not met")
    config = request["config"]
    if not isinstance(config, dict):
        raise InstallerError("CONFIG_INVALID", "config must be an object")
    _validate(CONFIG_SCHEMA, config, "CONFIG_INVALID")
    root = _validate_install_root(request["install_root"], facts.get("filesystem_type"))
    ports = facts.get("ports_available")
    if not isinstance(ports, dict):
        raise InstallerError("PORT_OCCUPIED", "port observations are missing")
    for name in ("web", "gateway", "metrics"):
        if ports.get(name) is not True:
            raise InstallerError("PORT_OCCUPIED", name)
    return {
        "schema_version": "liqvera-preflight-result/v1",
        "status": "PASS",
        "distribution": distribution,
        "distribution_version": distro_version,
        "architecture": ARCHITECTURES[machine],
        "install_root": str(root),
        "source_mode": "shadow",
        "payment_enabled": False,
    }


def _validate_secret_reference(path_value: object) -> Path:
    path = Path(str(path_value))
    if any(character in str(path) for character in ("\n", "\r", "\x00", "\x7f", "$", "`", "\\")):
        raise InstallerError("SECRET_REFERENCE_INVALID", "secret reference contains unsafe characters")
    current = Path("/")
    for part in path.parts[1:]:
        current /= part
        try:
            component = current.lstat()
        except OSError as exc:
            raise InstallerError("SECRET_REFERENCE_INVALID", "secret reference is unavailable") from exc
        if stat.S_ISLNK(component.st_mode):
            raise InstallerError("SECRET_REFERENCE_INVALID", "secret reference ancestry contains a link")
    try:
        item = path.lstat()
    except OSError as exc:
        raise InstallerError("SECRET_REFERENCE_INVALID", "secret reference is unavailable") from exc
    if (
        not path.is_absolute()
        or not stat.S_ISREG(item.st_mode)
        or stat.S_ISLNK(item.st_mode)
        or item.st_nlink != 1
        or item.st_uid != os.getuid()
        or stat.S_IMODE(item.st_mode) & 0o077
        or item.st_size < 1
        or item.st_size > 65536
    ):
        raise InstallerError("SECRET_REFERENCE_INVALID", "secret reference is unsafe")
    return path


class InstallRoot:
    """Descriptor-bound private installation root."""

    def __init__(
        self, path: Path, root_fd: int, parent_fd: int,
        identity: tuple[int, int], ancestry: tuple[tuple[int, int], ...], created: bool,
    ) -> None:
        self.path = path
        self.fd = root_fd
        self.identity = identity
        self.parent_fd = parent_fd
        self.ancestry = ancestry
        self.created = created

    @classmethod
    def create(cls, path: Path) -> "InstallRoot":
        path = Path(path)
        if not path.is_absolute() or path == Path("/"):
            raise InstallerError("UNSAFE_INSTALL_ROOT", "install root must be a narrow absolute path")
        fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW)
        ancestry: list[tuple[int, int]] = []
        parent_fd = -1
        root_created = False
        try:
            root_item = os.fstat(fd)
            ancestry.append((root_item.st_dev, root_item.st_ino))
            for index, name in enumerate(path.parts[1:]):
                try:
                    child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW, dir_fd=fd)
                except FileNotFoundError:
                    os.mkdir(name, 0o700, dir_fd=fd)
                    child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW, dir_fd=fd)
                    if index == len(path.parts[1:]) - 1:
                        root_created = True
                item = os.fstat(child)
                writable = stat.S_IMODE(item.st_mode) & 0o022
                trusted_sticky_root = item.st_uid == 0 and bool(item.st_mode & stat.S_ISVTX)
                if writable and not trusted_sticky_root:
                    os.close(child)
                    raise InstallerError("UNSAFE_INSTALL_ROOT", "writable path ancestry")
                ancestry.append((item.st_dev, item.st_ino))
                if index == len(path.parts[1:]) - 1:
                    parent_fd = fd
                    fd = child
                    break
                os.close(fd)
                fd = child
            item = os.fstat(fd)
            return cls(path, fd, parent_fd, (item.st_dev, item.st_ino), tuple(ancestry), root_created)
        except Exception:
            os.close(fd)
            if parent_fd >= 0:
                os.close(parent_fd)
            raise

    def ensure_directory(self, name: str) -> int:
        try:
            os.mkdir(name, 0o700, dir_fd=self.fd)
        except FileExistsError:
            pass
        child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW, dir_fd=self.fd)
        item = os.fstat(child)
        if item.st_uid != os.getuid() or stat.S_IMODE(item.st_mode) & 0o077:
            os.close(child)
            raise InstallerError("UNSAFE_INSTALL_ROOT", "installation child is not private")
        return child

    def write(self, relative: str, data: bytes) -> None:
        directory, name = relative.split("/", 1)
        parent_fd = self.ensure_directory(directory)
        try:
            _atomic_write_fd(parent_fd, name, data)
        finally:
            os.close(parent_fd)

    def read(self, relative: str, maximum: int = 1024 * 1024) -> bytes:
        directory, name = relative.split("/", 1)
        try:
            parent_fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW, dir_fd=self.fd)
        except OSError as exc:
            raise InstallerError("CONFIG_INVALID", "installed directory is unavailable") from exc
        try:
            file_fd = os.open(name, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW, dir_fd=parent_fd)
            try:
                item = os.fstat(file_fd)
                if not stat.S_ISREG(item.st_mode) or item.st_nlink != 1 or item.st_size > maximum:
                    raise InstallerError("CONFIG_INVALID", "installed file is unsafe")
                data = os.read(file_fd, maximum + 1)
            finally:
                os.close(file_fd)
        finally:
            os.close(parent_fd)
        if len(data) > maximum:
            raise InstallerError("CONFIG_INVALID", "installed file exceeds bound")
        return data

    def assert_selected_path(self) -> None:
        fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW)
        try:
            observed = [(os.fstat(fd).st_dev, os.fstat(fd).st_ino)]
            for name in self.path.parts[1:]:
                child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd)
                fd = child
                item = os.fstat(fd)
                observed.append((item.st_dev, item.st_ino))
        except OSError as exc:
            raise InstallerError("UNSAFE_INSTALL_ROOT", "selected root disappeared") from exc
        finally:
            os.close(fd)
        if tuple(observed) != self.ancestry:
            raise InstallerError("UNSAFE_INSTALL_ROOT", "selected root identity changed")

    def close(self) -> None:
        os.close(self.fd)
        os.close(self.parent_fd)

    def cleanup_created(self) -> None:
        if not self.created:
            return
        for directory, filename in (("config", "runtime.env"), ("state", "install-state.json")):
            try:
                child = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW, dir_fd=self.fd)
            except FileNotFoundError:
                continue
            try:
                try:
                    os.unlink(filename, dir_fd=child)
                except FileNotFoundError:
                    pass
            finally:
                os.close(child)
            try:
                os.rmdir(directory, dir_fd=self.fd)
            except FileNotFoundError:
                pass
        try:
            os.unlink(".install.lock", dir_fd=self.fd)
        except FileNotFoundError:
            pass
        os.rmdir(self.path.name, dir_fd=self.parent_fd)


class LifecycleLock:
    """Serializes one canonical install path from a descriptor-bound anchor."""

    def __init__(self, directory_fd: int, lock_fd: int) -> None:
        self.directory_fd = directory_fd
        self.lock_fd = lock_fd

    @classmethod
    def acquire(cls, path: Path) -> "LifecycleLock":
        fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW)
        try:
            for name in path.parts[1:-1]:
                try:
                    child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW, dir_fd=fd)
                except FileNotFoundError:
                    break
                item = os.fstat(child)
                os.close(fd)
                fd = child
                if item.st_uid == os.getuid():
                    break
            if os.fstat(fd).st_uid != os.getuid():
                raise InstallerError("UNSAFE_INSTALL_ROOT", "no owned lifecycle-lock anchor")
            lock_name = f".liqvera-install-{hashlib.sha256(str(path).encode()).hexdigest()[:24]}.lock"
            lock_fd = os.open(lock_name, os.O_WRONLY | os.O_CREAT | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600, dir_fd=fd)
            lock_item = os.fstat(lock_fd)
            if (not stat.S_ISREG(lock_item.st_mode) or lock_item.st_uid != os.getuid()
                    or lock_item.st_nlink != 1 or stat.S_IMODE(lock_item.st_mode) & 0o077):
                os.close(lock_fd)
                raise InstallerError("UNSAFE_INSTALL_ROOT", "lifecycle lock is unsafe")
            fcntl.flock(lock_fd, fcntl.LOCK_EX)
            return cls(fd, lock_fd)
        except Exception:
            os.close(fd)
            raise

    def close(self) -> None:
        os.close(self.lock_fd)
        os.close(self.directory_fd)


def _atomic_write_fd(parent_fd: int, name: str, data: bytes) -> None:
    temporary = f".{name}.{secrets.token_hex(12)}"
    file_fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600, dir_fd=parent_fd)
    try:
        with os.fdopen(file_fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, name, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
        os.fsync(parent_fd)
    except Exception:
        try:
            os.unlink(temporary, dir_fd=parent_fd)
        except FileNotFoundError:
            pass
        raise


def _atomic_write(path: Path, data: bytes) -> None:
    parent = path.parent
    try:
        parent_fd = os.open(parent, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW)
    except OSError as exc:
        raise InstallerError("CONFIG_INVALID", "output parent is unavailable") from exc
    try:
        _atomic_write_fd(parent_fd, path.name, data)
    finally:
        os.close(parent_fd)


def render_config_bytes(config: dict[str, object]) -> bytes:
    preliminary_secrets = config.get("secret_files")
    if isinstance(preliminary_secrets, dict):
        for value in preliminary_secrets.values():
            raw = str(value)
            if any(character in raw for character in ("\n", "\r", "\x00", "\x7f", "$", "`", "\\")):
                raise InstallerError("SECRET_REFERENCE_INVALID", "secret reference contains unsafe characters")
    _validate(CONFIG_SCHEMA, config, "CONFIG_INVALID")
    secret_files = config["secret_files"]
    if not isinstance(secret_files, dict):
        raise InstallerError("CONFIG_INVALID", "secret_files must be an object")
    validated_secrets = {name: _validate_secret_reference(value) for name, value in secret_files.items()}
    ports = config["ports"]
    if not isinstance(ports, dict):
        raise InstallerError("CONFIG_INVALID", "ports must be an object")
    lines = [
        "LIQVERA_CHAIN_ID=31611",
        "LIQVERA_PAYMENT_ENABLED=false",
        "LIQVERA_SOURCE_MODE=shadow",
    ]
    for name in ("web", "gateway", "metrics"):
        endpoint = ports[name]
        if not isinstance(endpoint, dict):
            raise InstallerError("CONFIG_INVALID", "port endpoint must be an object")
        prefix = f"LIQVERA_{name.upper()}"
        lines.extend((f"{prefix}_HOST={endpoint['host']}", f"{prefix}_PORT={endpoint['port']}"))
    for name, path in sorted(validated_secrets.items()):
        lines.append(f"{name}={path}")
    return ("\n".join(lines) + "\n").encode()


def render_config(config: dict[str, object], destination: Path) -> None:
    _atomic_write(destination, render_config_bytes(config))


def write_state_atomic(path: Path, state: dict[str, object]) -> None:
    _validate(STATE_SCHEMA, state, "CONFIG_INVALID")
    _atomic_write(path, (json.dumps(state, sort_keys=True, separators=(",", ":")) + "\n").encode())


def load_state(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InstallerError("CONFIG_INVALID", "install state is corrupt") from exc
    if not isinstance(state, dict):
        raise InstallerError("CONFIG_INVALID", "install state must be an object")
    _validate(STATE_SCHEMA, state, "CONFIG_INVALID")
    return state


def reconcile_existing(root: Path, expected: dict[str, object], config_bytes: bytes) -> dict[str, object] | None:
    if not root.exists():
        return None
    state_path = root / "state/install-state.json"
    config_path = root / "config/runtime.env"
    if not state_path.is_file() or not config_path.is_file():
        raise InstallerError("UNSAFE_INSTALL_ROOT", "existing root is not a complete Liqvera install")
    observed = load_state(state_path)
    if observed is None:
        raise InstallerError("CONFIG_INVALID", "existing state is missing")
    for key in ("product_version", "release_sha256", "git_commit", "git_tree", "install_root", "compose_project", "ports"):
        if observed.get(key) != expected.get(key):
            code = "RELEASE_DIGEST_MISMATCH" if key in {"release_sha256", "git_commit", "git_tree", "product_version"} else "CONFIG_INVALID"
            raise InstallerError(code, "existing installation identity conflicts")
    try:
        existing_config = config_path.read_bytes()
    except OSError as exc:
        raise InstallerError("CONFIG_INVALID", "existing config is unavailable") from exc
    if existing_config != config_bytes:
        raise InstallerError("CONFIG_INVALID", "existing configuration conflicts")
    return observed


def reconcile_handle(handle: InstallRoot, expected: dict[str, object], config_bytes: bytes) -> dict[str, object]:
    state_value = load_json_bytes(handle.read("state/install-state.json"), "CONFIG_INVALID")
    if not isinstance(state_value, dict):
        raise InstallerError("CONFIG_INVALID", "existing state is invalid")
    _validate(STATE_SCHEMA, state_value, "CONFIG_INVALID")
    for key in ("product_version", "release_sha256", "git_commit", "git_tree", "install_root", "compose_project", "ports"):
        if state_value.get(key) != expected.get(key):
            code = "RELEASE_DIGEST_MISMATCH" if key in {"release_sha256", "git_commit", "git_tree", "product_version"} else "CONFIG_INVALID"
            raise InstallerError(code, "existing installation identity conflicts")
    if handle.read("config/runtime.env") != config_bytes:
        raise InstallerError("CONFIG_INVALID", "existing configuration conflicts")
    handle.assert_selected_path()
    return state_value


def _safe_regular_bytes(path: Path, code: str, maximum: int = 1024 * 1024) -> bytes:
    try:
        item = path.lstat()
        if not stat.S_ISREG(item.st_mode) or item.st_nlink != 1 or item.st_size > maximum:
            raise InstallerError(code, "input is not a bounded single-link regular file")
        fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
        try:
            data = os.read(fd, maximum + 1)
            after = os.fstat(fd)
        finally:
            os.close(fd)
    except OSError as exc:
        raise InstallerError(code, "input is unavailable") from exc
    if len(data) > maximum or (after.st_dev, after.st_ino, after.st_size) != (item.st_dev, item.st_ino, item.st_size):
        raise InstallerError(code, "input identity changed")
    return data


def validate_verified_release(release: Path, receipt_path: Path, expected_sha256: str) -> dict[str, object]:
    receipt = load_json_bytes(_safe_regular_bytes(receipt_path, "ARCHIVE_INVALID"), "ARCHIVE_INVALID")
    required = {"schema_version", "archive_sha256", "inventory_sha256", "destination", "file_count", "product_version", "git_commit", "git_tree"}
    if not isinstance(receipt, dict) or set(receipt) != required or receipt.get("schema_version") != "verified-release-v1":
        raise InstallerError("ARCHIVE_INVALID", "verified release receipt is not closed")
    if receipt.get("archive_sha256") != expected_sha256:
        raise InstallerError("RELEASE_DIGEST_MISMATCH", "receipt does not bind the supplied archive digest")
    if receipt.get("destination") != str(release.resolve(strict=True)):
        raise InstallerError("ARCHIVE_INVALID", "receipt destination mismatch")
    manifest = load_json_bytes(_safe_regular_bytes(release / "manifests/release-manifest.json", "ARCHIVE_INVALID"), "ARCHIVE_INVALID")
    if not isinstance(manifest, dict):
        raise InstallerError("ARCHIVE_INVALID", "release manifest is not an object")
    _validate(INSTALLER_ROOT / "schemas/release-manifest.schema.json", manifest, "ARCHIVE_INVALID")
    sums_bytes = _safe_regular_bytes(release / "SHA256SUMS", "ARCHIVE_INVALID")
    if hashlib.sha256(sums_bytes).hexdigest() != receipt.get("inventory_sha256"):
        raise InstallerError("ARCHIVE_INVALID", "verified inventory digest mismatch")
    sums_data = sums_bytes.decode("utf-8")
    expected: dict[str, str] = {}
    for line in sums_data.splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  ([^\x00-\x1f\x7f]+)", line)
        if match is None or match.group(2) in expected:
            raise InstallerError("ARCHIVE_INVALID", "checksum inventory is malformed")
        expected[match.group(2)] = match.group(1)
    observed = {str(path.relative_to(release)): path for path in release.rglob("*") if path.is_file() and path.name != "SHA256SUMS"}
    if set(observed) != set(expected) or receipt.get("file_count") != len(expected) + 1:
        raise InstallerError("ARCHIVE_INVALID", "release inventory mismatch")
    for name, path in observed.items():
        if hashlib.sha256(_safe_regular_bytes(path, "ARCHIVE_INVALID", 16 * 1024 * 1024)).hexdigest() != expected[name]:
            raise InstallerError("ARCHIVE_INVALID", "release member digest mismatch")
    for key in ("product_version", "git_commit", "git_tree"):
        if receipt.get(key) != manifest.get(key):
            raise InstallerError("ARCHIVE_INVALID", "receipt and manifest identity mismatch")
    return manifest


def dependency_command(distribution: str) -> tuple[str, ...]:
    try:
        return DEPENDENCY_COMMANDS[distribution]
    except KeyError as exc:
        raise InstallerError("UNSUPPORTED_LINUX", "no dependency command for distribution") from exc


def install_dependencies(
    distribution: str,
    approval_digest: str | None,
    runner: Callable[[tuple[str, ...]], int],
) -> None:
    command = dependency_command(distribution)
    expected = hashlib.sha256("\0".join(command).encode()).hexdigest()
    if approval_digest != expected:
        raise InstallerError("DEPENDENCY_MISSING", f"dependency command requires approval {expected}")
    if runner(command) != 0:
        raise InstallerError("DEPENDENCY_MISSING", "approved dependency command failed")


def run_process(argv: tuple[str, ...], runner: Callable[[tuple[str, ...]], int]) -> int:
    if argv not in READ_ONLY_COMMANDS:
        raise InstallerError("DEPENDENCY_MISSING", "process argv is outside the read-only allowlist")
    return runner(argv)


def reject_ambient_authority(environment: dict[str, str] | os._Environ[str]) -> None:
    if FORBIDDEN_AMBIENT_ENV.intersection(environment):
        raise InstallerError("DEPENDENCY_MISSING", "ambient process authority is forbidden")


def _system_runner(argv: tuple[str, ...]) -> int:
    # argv is either a fixed read-only command or an exact reviewed dependency tuple.
    try:
        return subprocess.run(  # nosec B603
            argv, env=SAFE_ENV, check=False, timeout=30,
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        ).returncode
    except (OSError, subprocess.SubprocessError):
        return 127


def _cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Configure a verified Liqvera Linux release")
    parser.add_argument("--verified-release", type=Path, required=True)
    parser.add_argument("--verified-receipt", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--install-dir", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--bash-version", required=True, help=argparse.SUPPRESS)
    parser.add_argument("--non-interactive", action="store_true")
    parser.add_argument("--install-deps", action="store_true")
    parser.add_argument("--approve-dependency-command")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _cli_parser().parse_args(argv)
    if not HEX64.fullmatch(args.sha256):
        print("RELEASE_DIGEST_MISMATCH: malformed outer digest", file=sys.stderr)
        return 2
    lifecycle: LifecycleLock | None = None
    try:
        reject_ambient_authority(os.environ)
        config = load_json_bytes(_safe_regular_bytes(args.config, "CONFIG_INVALID"), "CONFIG_INVALID")
        manifest = validate_verified_release(args.verified_release, args.verified_receipt, args.sha256)
        if not isinstance(config, dict) or not isinstance(manifest, dict):
            raise InstallerError("CONFIG_INVALID", "config or manifest is not an object")
        _validate(CONFIG_SCHEMA, config, "CONFIG_INVALID")
        config_bytes = render_config_bytes(config)
        root = _validate_install_root(args.install_dir, "unknown")
        identity = {
            "product_version": manifest["product_version"], "release_sha256": args.sha256,
            "git_commit": manifest["git_commit"], "git_tree": manifest["git_tree"],
            "install_root": str(root), "compose_project": f"liqvera-{args.sha256[:12]}",
            "ports": {name: config["ports"][name]["port"] for name in ("web", "gateway", "metrics")},
        }
        lifecycle = LifecycleLock.acquire(root)
        if root.exists():
            existing_handle = InstallRoot.create(root)
            try:
                existing = reconcile_handle(existing_handle, identity, config_bytes)
            finally:
                existing_handle.close()
            print(json.dumps({"schema_version": "liqvera-preflight-result/v1", "status": existing["last_completed_phase"], "install_root": str(root)}, sort_keys=True, separators=(",", ":")))
            return 0
        # Host collection remains read-only; Task 4 owns Docker/Compose mutation.
        facts = _collect_system_facts(args.install_dir, config, args.bash_version)
        independent_facts = {
            **facts, "docker_version": ".".join(map(str, MIN_DOCKER)),
            "compose_version": ".".join(map(str, MIN_COMPOSE)),
            "daemon_reachable": True, "installable_dependency_missing": False,
        }
        preflight({"schema_version": "liqvera-preflight-request/v1", "install_root": str(args.install_dir), "config": config}, independent_facts)
        try:
            outcome = preflight(request={
                "schema_version": "liqvera-preflight-request/v1",
                "install_root": str(args.install_dir),
                "config": config,
            }, facts=facts)
        except InstallerError:
            if facts.get("installable_dependency_missing") is not True or not args.install_deps:
                raise
            approval = args.approve_dependency_command
            command = dependency_command(str(facts["distribution"]))
            command_digest = hashlib.sha256("\0".join(command).encode()).hexdigest()
            print(f"DEPENDENCY_PREVIEW: {' '.join(command)}", file=sys.stderr)
            print(f"DEPENDENCY_APPROVAL_SHA256: {command_digest}", file=sys.stderr)
            if approval is None and not args.non_interactive:
                try:
                    print("Enter the exact dependency approval SHA-256: ", end="", file=sys.stderr, flush=True)
                    approval = input().strip()
                except EOFError as input_error:
                    raise InstallerError("DEPENDENCY_MISSING", "dependency approval was not provided") from input_error
            install_dependencies(str(facts["distribution"]), approval, _system_runner)
            facts = _collect_system_facts(args.install_dir, config, args.bash_version)
            outcome = preflight({"schema_version": "liqvera-preflight-request/v1", "install_root": str(args.install_dir), "config": config}, facts)
        now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        state = {
            "schema_version": "liqvera-install-state/v1",
            "product_version": manifest["product_version"],
            "release_sha256": args.sha256,
            "git_commit": manifest["git_commit"],
            "git_tree": manifest["git_tree"],
            "install_root": outcome["install_root"],
            "compose_project": f"liqvera-{args.sha256[:12]}",
            "linux": {"distribution": outcome["distribution"], "architecture": outcome["architecture"]},
            "docker": {
                "engine_version": ".".join(str(part) for part in _version(facts["docker_version"])),
                "compose_version": ".".join(str(part) for part in _version(facts["compose_version"])),
            },
            "ports": {name: config["ports"][name]["port"] for name in ("web", "gateway", "metrics")},
            "last_completed_phase": "CONFIGURED",
            "last_error": None,
            "created_at": now,
            "updated_at": now,
        }
        _validate(STATE_SCHEMA, state, "CONFIG_INVALID")
        root_handle = InstallRoot.create(args.install_dir)
        try:
            if not root_handle.created:
                existing = reconcile_handle(root_handle, identity, config_bytes)
                print(json.dumps({"schema_version": "liqvera-preflight-result/v1", "status": existing["last_completed_phase"], "install_root": str(root)}, sort_keys=True, separators=(",", ":")))
                return 0
            root_handle.write("config/runtime.env", config_bytes)
            root_handle.write("state/install-state.json", (json.dumps(state, sort_keys=True, separators=(",", ":")) + "\n").encode())
            root_handle.assert_selected_path()
        except Exception:
            root_handle.cleanup_created()
            raise
        finally:
            root_handle.close()
        print(json.dumps({**outcome, "status": "CONFIGURED"}, sort_keys=True, separators=(",", ":")))
        return 0
    except (InstallerError, OSError, json.JSONDecodeError, KeyError, TypeError, ValueError, subprocess.SubprocessError) as exc:
        message = str(exc) if isinstance(exc, InstallerError) else "CONFIG_INVALID: bounded input failure"
        print(message, file=sys.stderr)
        return 2
    finally:
        if lifecycle is not None:
            lifecycle.close()


def _read_os_release() -> tuple[str, str]:
    values: dict[str, str] = {}
    for line in Path("/etc/os-release").read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value.strip().strip('"')
    return values.get("ID", ""), values.get("VERSION_ID", "")


def _command_output(argv: tuple[str, ...]) -> str | None:
    # Callers supply only literal entries from READ_ONLY_COMMANDS.
    try:
        completed = subprocess.run(  # nosec B603
            argv, env=SAFE_ENV, check=False, capture_output=True, timeout=10,
            stdin=subprocess.DEVNULL,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    if len(completed.stdout) > 256 or len(completed.stderr) > 256:
        return None
    try:
        return completed.stdout.decode("ascii").strip().removeprefix("Docker version ").split(",", 1)[0].removeprefix("v")
    except UnicodeDecodeError:
        return None


def _filesystem_type(path: Path) -> str:
    resolved = path.resolve(strict=False)
    best = (0, "unknown")
    for line in Path("/proc/self/mountinfo").read_text(encoding="utf-8").splitlines():
        before, separator, after = line.partition(" - ")
        if not separator:
            continue
        fields = before.split()
        mounted = Path(fields[4].replace("\\040", " "))
        try:
            resolved.relative_to(mounted)
        except ValueError:
            continue
        if len(mounted.parts) > best[0]:
            best = (len(mounted.parts), after.split()[0])
    return best[1]


def _port_available(host: str, port: int) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind((host, port))
        return True
    except OSError:
        return False


def _collect_system_facts(install_root: Path, config: dict[str, object], bash_version: str) -> dict[str, object]:
    distribution, distribution_version = _read_os_release()
    existing = install_root.parent
    while not existing.exists():
        existing = existing.parent
    usage = os.statvfs(existing.resolve(strict=True))
    ports = config["ports"]
    if not isinstance(ports, dict):
        raise InstallerError("CONFIG_INVALID", "ports must be an object")
    docker_version = _command_output(("/usr/bin/docker", "--host", "unix:///var/run/docker.sock", "version", "--format", "{{.Server.Version}}"))
    compose_version = _command_output(("/usr/bin/docker", "--host", "unix:///var/run/docker.sock", "compose", "version", "--short"))
    missing = docker_version is None or compose_version is None
    return {
        "kernel": platform.system(),
        "distribution": distribution,
        "distribution_version": distribution_version,
        "architecture": platform.machine(),
        "bash_version": bash_version,
        "docker_version": docker_version or "0.0.0",
        "compose_version": compose_version or "0.0.0",
        "installable_dependency_missing": missing,
        "docker_endpoint": "unix:///var/run/docker.sock",
        "daemon_reachable": not missing and _system_runner(("/usr/bin/docker", "--host", "unix:///var/run/docker.sock", "info", "--format", "{{.ServerVersion}}")) == 0,
        "disk_bytes": usage.f_bavail * usage.f_frsize,
        "memory_bytes": os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_AVPHYS_PAGES"),
        "filesystem_type": _filesystem_type(install_root),
        "ports_available": {
            name: _port_available(str(endpoint["host"]), int(endpoint["port"]))
            for name, endpoint in ports.items()
        },
    }


if __name__ == "__main__":
    raise SystemExit(main())
