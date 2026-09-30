#!/usr/bin/env python3
"""Recoverable Linux lifecycle policy with injected, fixed-authority effects."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import secrets
import stat
import subprocess  # nosec B404
import sys
from pathlib import Path
from typing import Protocol

HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
SINCE = re.compile(r"[1-9][0-9]{0,5}[smhd]\Z")
SERVICES = frozenset({"postgres", "migrate", "capture", "report", "gateway", "web", "edge"})
PHASES = frozenset({"HEALTHY", "STOPPED", "UNINSTALLED"})
OPERATION_PHASES = frozenset({
    "INTENT", "BACKUP_COMPLETE", "MIGRATION_COMMITTED", "CANDIDATE_STARTED",
    "HEALTHY", "POINTER_SWITCHED",
})
RELEASE_KEYS = frozenset({
    "schema_version", "product_version", "release_sha256", "git_commit", "git_tree",
    "database_compatibility",
})
STATE_KEYS = frozenset({
    "schema_version", "generation", "status", "service_manager", "compose_project",
    "current", "previous", "migration_ledger", "migration_committed", "operation",
})


class LifecycleError(RuntimeError):
    pass


class InjectedCrash(RuntimeError):
    pass


class Adapter(Protocol):
    def start(self, project: str, release: Path) -> None: ...
    def stop(self, project: str) -> None: ...
    def health(self, project: str) -> bool: ...
    def migration_ledger(self) -> list[dict[str, str]]: ...
    def backup(self, project: str) -> dict[str, object]: ...
    def migrate(self, project: str, release: Path) -> bool: ...
    def remove_runtime(self, project: str) -> None: ...
    def purge(self, targets: tuple[str, ...]) -> None: ...
    def logs(self, project: str, service: str, tail: int, since: str) -> str: ...


class ComposeAdapter:
    """Fixed-argv local Compose adapter; update remains fail-closed without backup proof."""

    def __init__(self, root: Path, runner: object = subprocess.run) -> None:
        self.root = _safe_root(root)
        self.runner = runner
        self.releases: dict[str, Path] = {}

    def _base(self, project: str, release: Path) -> tuple[str, ...]:
        compose = release / "compose.yaml"
        env_file = self.root / "config/runtime.env"
        if compose.is_symlink() or env_file.is_symlink() or not compose.is_file() or not env_file.is_file():
            raise LifecycleError("CONFIG_INVALID")
        return (
            "/usr/bin/docker", "compose", "--project-name", project,
            "--file", str(compose), "--env-file", str(env_file),
        )

    def _run(self, argv: tuple[str, ...], *, capture: bool = False, timeout: int = 130) -> subprocess.CompletedProcess[bytes]:
        try:
            result = self.runner(
                argv, stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE if capture else subprocess.DEVNULL,
                stderr=subprocess.PIPE if capture else subprocess.DEVNULL,
                timeout=timeout, check=False, env={"PATH": "/usr/bin:/bin"},
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise LifecycleError("LIFECYCLE_COMMAND_FAILED") from exc
        if not isinstance(result, subprocess.CompletedProcess) or result.returncode != 0:
            raise LifecycleError("LIFECYCLE_COMMAND_FAILED")
        return result

    def start(self, project: str, release: Path) -> None:
        self._run((*self._base(project, release), "up", "-d", "--wait", "--wait-timeout", "120"))
        self.releases[project] = release

    def stop(self, project: str) -> None:
        release = self.releases.get(project) or _current_release(self.root)[0]
        self._run((*self._base(project, release), "stop", "--timeout", "30"), timeout=40)

    def health(self, project: str) -> bool:
        release = self.releases.get(project) or _current_release(self.root)[0]
        result = self._run((*self._base(project, release), "ps", "--format", "json"), capture=True, timeout=10)
        try:
            rows = json.loads(result.stdout)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return False
        if not isinstance(rows, list) or len(rows) < 6:
            return False
        return all(isinstance(row, dict) and row.get("State") in {"running", "exited"}
                   and row.get("Health") in {"healthy", ""} for row in rows)

    def migration_ledger(self) -> list[dict[str, str]]:
        raise LifecycleError("ROLLBACK_RESTORE_REQUIRED: database ledger adapter unavailable")

    def backup(self, project: str) -> dict[str, object]:
        return {"complete": False, "sha256": ""}

    def migrate(self, project: str, release: Path) -> bool:
        raise LifecycleError("ROLLBACK_RESTORE_REQUIRED: update migration is unavailable")

    def remove_runtime(self, project: str) -> None:
        release = self.releases.get(project) or _current_release(self.root)[0]
        self._run((*self._base(project, release), "down", "--remove-orphans", "--timeout", "30"), timeout=40)

    def purge(self, targets: tuple[str, ...]) -> None:
        self._run(("/usr/bin/docker", "volume", "rm", *targets), timeout=30)

    def logs(self, project: str, service: str, tail: int, since: str) -> str:
        release = self.releases.get(project) or _current_release(self.root)[0]
        result = self._run(
            (*self._base(project, release), "logs", "--no-color", "--tail", str(tail), "--since", since, service),
            capture=True, timeout=15,
        )
        return result.stdout[:65536].decode("utf-8", "replace")


def _safe_root(root: Path) -> Path:
    root = Path(root)
    if not root.is_absolute() or root == Path("/") or root.is_symlink():
        raise LifecycleError("UNSAFE_INSTALL_ROOT")
    item = root.stat()
    if not stat.S_ISDIR(item.st_mode) or item.st_uid != os.getuid() or item.st_mode & 0o077:
        raise LifecycleError("UNSAFE_INSTALL_ROOT")
    return root


class LifecycleLock:
    def __init__(self, directory_fd: int, lock_fd: int) -> None:
        self.directory_fd = directory_fd
        self.lock_fd = lock_fd

    @classmethod
    def acquire(cls, root: Path) -> "LifecycleLock":
        root = _safe_root(root)
        directory_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW)
        try:
            lock_fd = os.open(
                ".lifecycle.lock", os.O_WRONLY | os.O_CREAT | os.O_CLOEXEC | os.O_NOFOLLOW,
                0o600, dir_fd=directory_fd,
            )
            item = os.fstat(lock_fd)
            if not stat.S_ISREG(item.st_mode) or item.st_nlink != 1 or item.st_uid != os.getuid():
                raise LifecycleError("LIFECYCLE_BUSY")
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise LifecycleError("LIFECYCLE_BUSY") from exc
            return cls(directory_fd, lock_fd)
        except Exception:
            os.close(directory_fd)
            raise

    def close(self) -> None:
        os.close(self.lock_fd)
        os.close(self.directory_fd)


def _atomic_write(root: Path, relative: str, payload: bytes) -> None:
    directory_name, filename = relative.split("/", 1)
    root_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW)
    try:
        try:
            os.mkdir(directory_name, 0o700, dir_fd=root_fd)
        except FileExistsError:
            pass
        directory_fd = os.open(
            directory_name, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW,
            dir_fd=root_fd,
        )
        try:
            name = f".{filename}.{secrets.token_hex(12)}"
            fd = os.open(
                name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
                0o600, dir_fd=directory_fd,
            )
            try:
                with os.fdopen(fd, "wb") as handle:
                    handle.write(payload)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(name, filename, src_dir_fd=directory_fd, dst_dir_fd=directory_fd)
                os.fsync(directory_fd)
            except Exception:
                try:
                    os.unlink(name, dir_fd=directory_fd)
                except FileNotFoundError:
                    pass
                raise
        finally:
            os.close(directory_fd)
    finally:
        os.close(root_fd)


def _read_json(path: Path, error: str) -> dict[str, object]:
    try:
        fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
        with os.fdopen(fd, "rb") as handle:
            item = os.fstat(handle.fileno())
            if not stat.S_ISREG(item.st_mode) or item.st_nlink != 1 or item.st_size > 1024 * 1024:
                raise LifecycleError(error)
            value = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise LifecycleError(error) from exc
    if not isinstance(value, dict):
        raise LifecycleError(error)
    return value


def _validate_ledger(value: object) -> list[dict[str, str]]:
    if not isinstance(value, list) or len(value) != 5:
        raise LifecycleError("MIGRATION_MISMATCH")
    result: list[dict[str, str]] = []
    for index, row in enumerate(value, 1):
        if (not isinstance(row, dict) or set(row) != {"name", "sha256"}
                or not re.fullmatch(rf"00{index}_[a-z_]+\.sql", str(row.get("name")))
                or not HEX64.fullmatch(str(row.get("sha256")))):
            raise LifecycleError("MIGRATION_MISMATCH")
        result.append({"name": str(row["name"]), "sha256": str(row["sha256"])})
    return result


def _validate_release_value(value: object) -> dict[str, object]:
    if (not isinstance(value, dict) or set(value) != RELEASE_KEYS
            or value.get("schema_version") != "liqvera-lifecycle-release/v1"
            or value.get("product_version") != "0.0.2"
            or not HEX64.fullmatch(str(value.get("release_sha256")))
            or not HEX40.fullmatch(str(value.get("git_commit")))
            or not HEX40.fullmatch(str(value.get("git_tree")))):
        raise LifecycleError("CONFIG_INVALID")
    value["database_compatibility"] = _validate_ledger(value.get("database_compatibility"))
    return value


def _release(root: Path, digest: str) -> tuple[Path, dict[str, object]]:
    if not HEX64.fullmatch(digest):
        raise LifecycleError("RELEASE_DIGEST_MISMATCH")
    target = root / "releases" / f"0.0.2-{digest[:12]}"
    if target.is_symlink() or not target.is_dir():
        raise LifecycleError("ARCHIVE_INVALID")
    value = _read_json(target / "release.json", "ARCHIVE_INVALID")
    if (set(value) != RELEASE_KEYS or value.get("schema_version") != "liqvera-lifecycle-release/v1"
            or value.get("product_version") != "0.0.2" or value.get("release_sha256") != digest
            or not HEX40.fullmatch(str(value.get("git_commit")))
            or not HEX40.fullmatch(str(value.get("git_tree")))):
        raise LifecycleError("ARCHIVE_INVALID")
    value["database_compatibility"] = _validate_ledger(value.get("database_compatibility"))
    return target, value


def _current_release(root: Path) -> tuple[Path, dict[str, object]]:
    link = root / "current"
    if not link.is_symlink():
        raise LifecycleError("CONFIG_INVALID")
    target = link.resolve(strict=True)
    releases = (root / "releases").resolve(strict=True)
    if target.parent != releases:
        raise LifecycleError("UNSAFE_INSTALL_ROOT")
    value = _read_json(target / "release.json", "ARCHIVE_INVALID")
    digest = str(value.get("release_sha256", ""))
    checked_target, checked = _release(root, digest)
    if checked_target.resolve() != target:
        raise LifecycleError("ARCHIVE_INVALID")
    return target, checked


def _validate_state(value: dict[str, object]) -> dict[str, object]:
    if (set(value) != STATE_KEYS or value.get("schema_version") != "liqvera-lifecycle/v1"
            or value.get("status") not in PHASES or value.get("service_manager") not in {"compose", "systemd-user"}
            or not isinstance(value.get("generation"), int) or int(value["generation"]) < 0
            or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,62}", str(value.get("compose_project")))):
        raise LifecycleError("CONFIG_INVALID")
    value["migration_ledger"] = _validate_ledger(value.get("migration_ledger"))
    if type(value.get("migration_committed")) is not bool:
        raise LifecycleError("CONFIG_INVALID")
    value["current"] = _validate_release_value(value.get("current"))
    if value.get("previous") is not None:
        value["previous"] = _validate_release_value(value.get("previous"))
    operation = value.get("operation")
    if operation is not None:
        if (not isinstance(operation, dict)
                or set(operation) != {"id", "type", "phase", "candidate", "prior", "backup_sha256"}
                or not re.fullmatch(r"[0-9a-f]{32}", str(operation.get("id")))
                or operation.get("type") != "UPDATE" or operation.get("phase") not in OPERATION_PHASES
                or operation.get("backup_sha256") is not None
                and not HEX64.fullmatch(str(operation.get("backup_sha256")))):
            raise LifecycleError("CONFIG_INVALID")
        operation["candidate"] = _validate_release_value(operation.get("candidate"))
        operation["prior"] = _validate_release_value(operation.get("prior"))
    return value


def _crash_if(options: dict[str, object], phase: str) -> None:
    if options.get("crash_after") == phase:
        raise InjectedCrash(phase)


def bootstrap_state(root: Path) -> dict[str, object]:
    root = _safe_root(root)
    _, current = _current_release(root)
    installed = _read_json(root / "state/install-state.json", "CONFIG_INVALID")
    if installed.get("release_sha256") != current["release_sha256"]:
        raise LifecycleError("CONFIG_INVALID")
    return {
        "schema_version": "liqvera-lifecycle/v1", "generation": 0,
        "status": installed.get("last_completed_phase", "HEALTHY"),
        "service_manager": "compose", "compose_project": installed.get("compose_project"),
        "current": current, "previous": None,
        "migration_ledger": current["database_compatibility"],
        "migration_committed": False, "operation": None,
    }


def load_lifecycle_state(root: Path) -> dict[str, object]:
    path = root / "state/lifecycle.json"
    return _validate_state(_read_json(path, "CONFIG_INVALID")) if path.exists() else bootstrap_state(root)


def write_lifecycle_state(root: Path, state: dict[str, object]) -> None:
    _validate_state(state)
    state["generation"] = int(state["generation"]) + 1
    _atomic_write(root, "state/lifecycle.json", (json.dumps(state, sort_keys=True, separators=(",", ":")) + "\n").encode())


def _switch_current(root: Path, release: Path) -> None:
    root_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW)
    temporary = f".current.{secrets.token_hex(12)}"
    try:
        os.symlink(str(release.relative_to(root)), temporary, dir_fd=root_fd)
        os.replace(temporary, "current", src_dir_fd=root_fd, dst_dir_fd=root_fd)
        os.fsync(root_fd)
    finally:
        try:
            os.unlink(temporary, dir_fd=root_fd)
        except FileNotFoundError:
            pass
        os.close(root_fd)


def _status(state: dict[str, object]) -> dict[str, object]:
    current = state["current"]
    if not isinstance(current, dict):
        raise LifecycleError("CONFIG_INVALID")
    return {
        "schema_version": "liqvera-lifecycle-result/v1", "status": state["status"],
        "version": current["product_version"], "release_sha256": current["release_sha256"],
        "git_commit": current["git_commit"], "git_tree": current["git_tree"],
        "compose_project": state["compose_project"], "service_manager": state["service_manager"],
        "blockers": ["SIMULATED_SOURCE", "EXTERNAL_GRANT_REQUIRED"],
    }


def _redact(value: str) -> str:
    value = re.sub(r"(?i)(authorization\s*:\s*)([^\r\n]+)", r"\1[REDACTED]", value)
    value = re.sub(r"([a-z][a-z0-9+.-]*://)[^/@\s]+@", r"\1[REDACTED]@", value)
    return value[:65536]


def purge_preview(root: Path) -> dict[str, object]:
    root = _safe_root(root)
    state = load_lifecycle_state(root)
    data = root / "data"
    if data.is_symlink() or (data.exists() and not data.is_dir()):
        raise LifecycleError("PURGE_CONFIRMATION_REQUIRED")
    project = str(state["compose_project"])
    targets = tuple(f"{project}_{name}" for name in ("postgres_data", "captures", "artifacts", "caddy_data", "caddy_config"))
    current = state["current"]
    if not isinstance(current, dict):
        raise LifecycleError("PURGE_CONFIRMATION_REQUIRED")
    material = json.dumps({"root": str(root), "release": current["release_sha256"], "targets": targets},
                          sort_keys=True, separators=(",", ":")).encode()
    return {"targets": targets, "token": hashlib.sha256(material).hexdigest()}


def run_lifecycle(root: Path, command: str, options: dict[str, object], adapter: Adapter) -> dict[str, object]:
    root = _safe_root(root)
    lock = LifecycleLock.acquire(root)
    try:
        state = load_lifecycle_state(root)
        operation = state.get("operation")
        if isinstance(operation, dict) and operation.get("phase") == "POINTER_SWITCHED":
            state["operation"] = None
            state["status"] = "HEALTHY"
            write_lifecycle_state(root, state)
        if (command not in {"status", "rollback"} and isinstance(state.get("operation"), dict)
                and state.get("migration_committed") is True):
            raise LifecycleError("ROLLBACK_RESTORE_REQUIRED: migration outcome requires explicit recovery")
        project = str(state["compose_project"])
        current_path, _ = _current_release(root)
        if command == "status":
            return _status(state)
        if command == "stop":
            if state["status"] != "STOPPED":
                adapter.stop(project)
                state["status"] = "STOPPED"
                write_lifecycle_state(root, state)
            return _status(state)
        if command == "start":
            if state["status"] != "HEALTHY":
                adapter.start(project, current_path)
                if not adapter.health(project):
                    adapter.stop(project)
                    raise LifecycleError("HEALTH_TIMEOUT")
                state["status"] = "HEALTHY"
                write_lifecycle_state(root, state)
            return _status(state)
        if command == "logs":
            service, tail, since = options.get("service", "gateway"), options.get("tail", 100), options.get("since", "10m")
            if service not in SERVICES or type(tail) is not int or not 1 <= tail <= 1000 or not SINCE.fullmatch(str(since)):
                raise LifecycleError("CONFIG_INVALID")
            return {"schema_version": "liqvera-lifecycle-result/v1", "status": "LOGS",
                    "logs": _redact(adapter.logs(project, str(service), tail, str(since)))}
        if command == "update":
            digest = str(options.get("sha256", ""))
            if options.get("version") != "0.0.2":
                raise LifecycleError("CONFIG_INVALID")
            candidate_path, candidate = _release(root, digest)
            if candidate == state["current"]:
                return _status(state)
            ledger = _validate_ledger(adapter.migration_ledger())
            if ledger != candidate["database_compatibility"]:
                raise LifecycleError("ROLLBACK_RESTORE_REQUIRED: candidate database compatibility mismatch")
            operation = {"id": secrets.token_hex(16), "type": "UPDATE", "phase": "INTENT",
                         "candidate": candidate, "prior": state["current"], "backup_sha256": None}
            state["operation"] = operation
            write_lifecycle_state(root, state)
            _crash_if(options, "INTENT")
            backup = adapter.backup(project)
            if set(backup) != {"complete", "sha256"} or backup.get("complete") is not True or not HEX64.fullmatch(str(backup.get("sha256"))):
                raise LifecycleError("ROLLBACK_RESTORE_REQUIRED: coherent backup unavailable")
            operation["backup_sha256"] = backup["sha256"]
            operation["phase"] = "BACKUP_COMPLETE"
            write_lifecycle_state(root, state)
            _crash_if(options, "BACKUP_COMPLETE")
            candidate_project = f"{project}-candidate"
            committed = adapter.migrate(candidate_project, candidate_path)
            if committed:
                state["migration_committed"] = True
                operation["phase"] = "MIGRATION_COMMITTED"
                write_lifecycle_state(root, state)
                _crash_if(options, "MIGRATION_COMMITTED")
            adapter.start(candidate_project, candidate_path)
            operation["phase"] = "CANDIDATE_STARTED"
            write_lifecycle_state(root, state)
            _crash_if(options, "CANDIDATE_STARTED")
            if not adapter.health(candidate_project):
                adapter.stop(candidate_project)
                raise LifecycleError("HEALTH_TIMEOUT")
            operation["phase"] = "HEALTHY"
            write_lifecycle_state(root, state)
            _crash_if(options, "HEALTHY")
            state["previous"] = state["current"]
            state["current"] = candidate
            state["migration_ledger"] = ledger
            state["status"] = "HEALTHY"
            _switch_current(root, candidate_path)
            operation["phase"] = "POINTER_SWITCHED"
            write_lifecycle_state(root, state)
            _crash_if(options, "POINTER_SWITCHED")
            state["operation"] = None
            write_lifecycle_state(root, state)
            return _status(state)
        if command == "rollback":
            previous = state.get("previous")
            operation = state.get("operation")
            if previous is None and isinstance(operation, dict):
                previous = operation.get("prior")
            if not isinstance(previous, dict):
                raise LifecycleError("ROLLBACK_RESTORE_REQUIRED: prior release unavailable")
            ledger = _validate_ledger(adapter.migration_ledger())
            if state["migration_committed"] is True and previous.get("database_compatibility") != ledger:
                raise LifecycleError("ROLLBACK_RESTORE_REQUIRED: prior image is incompatible")
            prior_path, checked = _release(root, str(previous.get("release_sha256", "")))
            if checked != previous:
                raise LifecycleError("ROLLBACK_RESTORE_REQUIRED: prior identity mismatch")
            adapter.stop(project)
            adapter.start(project, prior_path)
            if not adapter.health(project):
                adapter.stop(project)
                raise LifecycleError("HEALTH_TIMEOUT")
            state["current"], state["previous"] = previous, state["current"]
            state["migration_committed"] = False
            state["operation"] = None
            state["status"] = "HEALTHY"
            _switch_current(root, prior_path)
            write_lifecycle_state(root, state)
            return _status(state)
        if command == "uninstall":
            if options.get("purge_data") is True:
                preview = purge_preview(root)
                if options.get("confirm_purge") != preview["token"]:
                    raise LifecycleError("PURGE_CONFIRMATION_REQUIRED")
                adapter.purge(tuple(preview["targets"]))
            adapter.remove_runtime(project)
            state["status"] = "UNINSTALLED"
            write_lifecycle_state(root, state)
            return _status(state)
        raise LifecycleError("CONFIG_INVALID")
    finally:
        lock.close()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Liqvera Linux lifecycle")
    parser.add_argument("--install-root", type=Path, required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status").add_argument("--json", action="store_true")
    sub.add_parser("start")
    sub.add_parser("stop")
    sub.add_parser("rollback")
    logs = sub.add_parser("logs")
    logs.add_argument("service", nargs="?", default="gateway")
    logs.add_argument("--tail", type=int, default=100)
    logs.add_argument("--since", default="10m")
    update = sub.add_parser("update")
    update.add_argument("--version", required=True)
    update.add_argument("--sha256", required=True)
    uninstall = sub.add_parser("uninstall")
    uninstall.add_argument("--purge-data", action="store_true")
    uninstall.add_argument("--confirm-purge")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "status":
            state = load_lifecycle_state(_safe_root(args.install_root))
            print(json.dumps(_status(state), sort_keys=True, separators=(",", ":")))
            return 0
        options = vars(args).copy()
        options.pop("install_root", None)
        options.pop("command", None)
        result = run_lifecycle(args.install_root, args.command, options, ComposeAdapter(args.install_root))
        if args.command == "logs":
            print(result["logs"], end="")
        else:
            print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except LifecycleError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
