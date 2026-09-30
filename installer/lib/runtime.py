#!/usr/bin/env python3
"""Closed Linux preflight/configuration helper for the Liqvera installer."""

from __future__ import annotations

import argparse
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
    ("/usr/bin/docker", "version", "--format", "{{.Server.Version}}"),
    ("/usr/bin/docker", "compose", "version", "--short"),
    ("/usr/bin/docker", "info", "--format", "{{json .}}"),
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


def _validate(schema_path: Path, value: dict[str, object], code: str) -> None:
    try:
        Draft202012Validator(_load_schema(schema_path)).validate(value)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        raise InstallerError(code, "closed schema validation failed") from exc


def _version(value: object) -> tuple[int, int, int]:
    match = re.fullmatch(r"([0-9]+)\.([0-9]+)(?:\.([0-9]+))?(?:[-+][A-Za-z0-9_.-]+)?", str(value))
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
    existing = path
    while not existing.exists():
        existing = existing.parent
    parent = existing if existing.is_dir() else existing.parent
    parent_stat = parent.stat()
    if parent_stat.st_uid != os.getuid() or parent_stat.st_mode & stat.S_IWOTH:
        raise InstallerError("UNSAFE_INSTALL_ROOT", "unsafe existing ancestor")
    if path.exists() and any(path.iterdir()) and not (path / "state" / "install-state.json").is_file():
        raise InstallerError("UNSAFE_INSTALL_ROOT", "existing directory is not a Liqvera install")
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


def _atomic_write(path: Path, data: bytes) -> None:
    parent = path.parent
    try:
        parent_fd = os.open(parent, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW)
    except OSError as exc:
        raise InstallerError("CONFIG_INVALID", "output parent is unavailable") from exc
    temporary = f".{path.name}.{secrets.token_hex(12)}"
    try:
        file_fd = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
            0o600,
            dir_fd=parent_fd,
        )
        try:
            with os.fdopen(file_fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path.name, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
            os.fsync(parent_fd)
        except Exception:
            try:
                os.unlink(temporary, dir_fd=parent_fd)
            except FileNotFoundError:
                pass
            raise
    finally:
        os.close(parent_fd)


def render_config(config: dict[str, object], destination: Path) -> None:
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
    _atomic_write(destination, ("\n".join(lines) + "\n").encode())


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
    return subprocess.run(argv, env=SAFE_ENV, check=False, timeout=30).returncode  # nosec B603


def _cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Configure a verified Liqvera Linux release")
    parser.add_argument("--verified-release", type=Path, required=True)
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
    try:
        reject_ambient_authority(os.environ)
        config = json.loads(args.config.read_text(encoding="utf-8"))
        manifest = json.loads((args.verified_release / "manifests/release-manifest.json").read_text(encoding="utf-8"))
        if not isinstance(config, dict) or not isinstance(manifest, dict):
            raise InstallerError("CONFIG_INVALID", "config or manifest is not an object")
        # Host collection remains read-only; Task 4 owns all Docker/Compose mutation.
        facts = _collect_system_facts(args.install_dir, config, args.bash_version)
        try:
            outcome = preflight(request={
                "schema_version": "liqvera-preflight-request/v1",
                "install_root": str(args.install_dir),
                "config": config,
            }, facts=facts)
        except InstallerError as exc:
            if exc.code != "DEPENDENCY_MISSING" or not args.install_deps:
                raise
            install_dependencies(str(facts["distribution"]), args.approve_dependency_command, _system_runner)
            facts = _collect_system_facts(args.install_dir, config, args.bash_version)
            outcome = preflight({"schema_version": "liqvera-preflight-request/v1", "install_root": str(args.install_dir), "config": config}, facts)
        args.install_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        (args.install_dir / "config").mkdir(mode=0o700, exist_ok=True)
        (args.install_dir / "state").mkdir(mode=0o700, exist_ok=True)
        render_config(config, args.install_dir / "config" / "runtime.env")
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
            "docker": {"engine_version": str(facts["docker_version"]), "compose_version": str(facts["compose_version"])},
            "ports": {name: config["ports"][name]["port"] for name in ("web", "gateway", "metrics")},
            "last_completed_phase": "CONFIGURED",
            "last_error": None,
            "created_at": now,
            "updated_at": now,
        }
        write_state_atomic(args.install_dir / "state" / "install-state.json", state)
        print(json.dumps({**outcome, "status": "CONFIGURED"}, sort_keys=True, separators=(",", ":")))
        return 0
    except (InstallerError, OSError, json.JSONDecodeError, KeyError) as exc:
        message = str(exc) if isinstance(exc, InstallerError) else "CONFIG_INVALID: bounded input failure"
        print(message, file=sys.stderr)
        return 2


def _read_os_release() -> tuple[str, str]:
    values: dict[str, str] = {}
    for line in Path("/etc/os-release").read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value.strip().strip('"')
    return values.get("ID", ""), values.get("VERSION_ID", "")


def _command_output(argv: tuple[str, ...]) -> str:
    # Callers supply only literal entries from READ_ONLY_COMMANDS.
    completed = subprocess.run(  # nosec B603
        argv, env=SAFE_ENV, check=False, capture_output=True, text=True, timeout=10
    )
    if completed.returncode != 0:
        return "0.0.0"
    return completed.stdout.strip().removeprefix("Docker version ").split(",", 1)[0].removeprefix("v")


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
    return {
        "kernel": platform.system(),
        "distribution": distribution,
        "distribution_version": distribution_version,
        "architecture": platform.machine(),
        "bash_version": bash_version,
        "docker_version": _command_output(("/usr/bin/docker", "version", "--format", "{{.Server.Version}}")),
        "compose_version": _command_output(("/usr/bin/docker", "compose", "version", "--short")),
        "docker_endpoint": "unix:///var/run/docker.sock" if not os.environ.get("DOCKER_HOST") else "ambient-override",
        "daemon_reachable": _system_runner(("/usr/bin/docker", "info", "--format", "{{json .}}")) == 0,
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
