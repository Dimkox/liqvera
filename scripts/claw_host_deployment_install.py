#!/usr/bin/env python3
"""WAL-backed D0 installer for the Claw host deployment controller."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import stat
import subprocess
import tempfile
import re
from pathlib import Path
from typing import Any


class D0Error(RuntimeError):
    pass


def _reject_duplicates(items: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in items:
        if key in value:
            raise D0Error("DUPLICATE_KEY")
        value[key] = item
    return value


def _read_regular(path: Path, *, limit: int) -> tuple[bytes, os.stat_result]:
    try:
        initial = path.lstat()
    except OSError as exc:
        raise D0Error("SOURCE_MISSING") from exc
    if not stat.S_ISREG(initial.st_mode) or initial.st_nlink != 1 or initial.st_size > limit:
        raise D0Error("SOURCE_IDENTITY")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size > limit:
            raise D0Error("SOURCE_IDENTITY")
        chunks: list[bytes] = []
        size = 0
        while True:
            chunk = os.read(fd, min(65536, limit + 1 - size))
            if not chunk:
                break
            size += len(chunk)
            if size > limit:
                raise D0Error("SOURCE_SIZE")
            chunks.append(chunk)
        after = os.fstat(fd)
    finally:
        os.close(fd)
    stable = ("st_dev", "st_ino", "st_size", "st_mtime_ns")
    if os.name == "posix":
        stable += ("st_ctime_ns",)
    if any(getattr(initial, key) != getattr(before, key) or getattr(before, key) != getattr(after, key) for key in stable):
        raise D0Error("SOURCE_CHANGED")
    return b"".join(chunks), after


def _atomic(path: Path, data: bytes, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        os.fchmod(fd, mode)
        view = memoryview(data)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise OSError("SHORT_WRITE")
            view = view[written:]
        os.fsync(fd)
        os.close(fd)
        fd = -1
        os.replace(temporary, path)
        if os.name == "posix":
            parent_fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(parent_fd)
            finally:
                os.close(parent_fd)
    except BaseException:
        if fd >= 0:
            os.close(fd)
        Path(temporary).unlink(missing_ok=True)
        raise


class D0Journal:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        if self.path.exists() or self.path.is_symlink():
            raise D0Error("JOURNAL_EXISTS")
        self.value: dict[str, Any] = {
            "schema_version": "claw-host-deployment-install-journal-v1",
            "phase": "PREPARED",
            "status": "OPEN",
            "history": ["PREPARED"],
            "applied": [],
            "current": None,
            "snapshots": {},
            "failures": [],
        }
        self._save()

    def _save(self) -> None:
        _atomic(
            self.path,
            (json.dumps(self.value, sort_keys=True, separators=(",", ":")) + "\n").encode(),
        )

    @classmethod
    def _load(cls, path: Path, *, terminal: bool) -> "D0Journal":
        self = object.__new__(cls)
        self.path = Path(path)
        try:
            self.value = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise D0Error("JOURNAL_INVALID") from exc
        required = {
            "schema_version", "phase", "status", "history", "applied",
            "current", "snapshots", "failures",
        }
        if set(self.value) != required or self.value["schema_version"] != "claw-host-deployment-install-journal-v1":
            raise D0Error("JOURNAL_INVALID")
        if terminal:
            if self.value["status"] != "COMMITTED":
                raise D0Error("JOURNAL_NOT_COMMITTED")
        elif self.value["status"] != "OPEN":
            raise D0Error("JOURNAL_NOT_OPEN")
        return self

    @classmethod
    def resume(cls, path: Path) -> "D0Journal":
        return cls._load(path, terminal=False)

    @classmethod
    def resume_terminal(cls, path: Path) -> "D0Journal":
        return cls._load(path, terminal=True)

    def applying(self, operation: str, snapshot: dict[str, object]) -> None:
        self.value["phase"] = f"APPLYING({operation})"
        self.value["history"].append(self.value["phase"])
        self.value["current"] = operation
        self.value["snapshots"][operation] = snapshot
        self._save()

    def applied(self, operation: str) -> None:
        self.value["applied"].append(operation)
        self.value["phase"] = f"APPLIED({operation})"
        self.value["history"].append(self.value["phase"])
        self.value["current"] = None
        self._save()

    def record(self, phase: str, *, status: str | None = None, failures: list[dict[str, str]] | None = None) -> None:
        self.value["phase"] = phase
        self.value["history"].append(phase)
        if status is not None:
            self.value["status"] = status
        if failures is not None:
            self.value["failures"] = failures
        self._save()


OPERATIONS = (
    "create_state", "install_library", "install_verifier",
    "install_inventory_collector", "install_inventory_verifier",
    "install_oci_library", "install_oci_verifier", "install_oci_builder_source",
    "install_oci_independent_verifier_source", "install_oci_schema", "install_policy",
    "install_closure", "install_oci_approval", "install_controller",
    "install_host_transaction", "install_receipt_writer", "install_receipt_verifier",
    "install_runner_verifier", "install_client", "install_socket", "install_service",
    "install_reconcile_service", "install_reconcile_timer", "daemon_reload",
    "enable_socket", "enable_reconciler", "verify_installed", "write_receipt",
)


class FakeD0Backend:
    OPERATIONS = OPERATIONS

    def __init__(self, *, fail_after: int | None = None, inverse_failures: set[str] | None = None) -> None:
        self.fail_after = fail_after
        self.inverse_failures = inverse_failures or set()
        self.state: dict[str, bool] = {}
        self.applies = 0
        self.snapshots: dict[str, dict[str, object]] = {}

    def snapshot(self, operation: str) -> dict[str, object]:
        value = {"existed": operation in self.state}
        self.snapshots[operation] = value
        return value

    def apply(self, operation: str) -> None:
        self.state[operation] = True
        self.applies += 1
        if self.fail_after == self.applies:
            raise D0Error("INJECTED")

    def rollback(self, operation: str) -> None:
        if operation in self.inverse_failures:
            raise D0Error(f"INVERSE:{operation}")
        snapshot = self.snapshots[operation]
        if snapshot["existed"]:
            self.state[operation] = True
        else:
            self.state.pop(operation, None)


class RealD0Backend:
    BASE_DIRS = ("/usr/local/libexec", "/etc/systemd/system", "/var/lib")
    CREATED_DIRS = (
        ("/var/lib/mee-claw-host-deploy", 0o700),
        ("/usr/local/libexec/mee-claw-host-deploy-lib", 0o755),
        ("/usr/local/libexec/schemas", 0o755),
    )
    FILE_TARGETS = (
        ("install_library", "/usr/local/libexec/mee-claw-host-deploy-lib/claw_host_deployment_contract.py", 0o644),
        ("install_verifier", "/usr/local/libexec/mee-claw-host-deploy-lib/verify_claw_host_deployment_approval.py", 0o644),
        ("install_inventory_collector", "/usr/local/libexec/mee-claw-host-deploy-lib/collect_claw_host_inventory.py", 0o644),
        ("install_inventory_verifier", "/usr/local/libexec/mee-claw-host-deploy-lib/verify_claw_host_inventory.py", 0o644),
        ("install_oci_library", "/usr/local/libexec/mee-claw-host-deploy-lib/oci_evidence_v2.py", 0o644),
        ("install_oci_verifier", "/usr/local/libexec/mee-claw-host-deploy-lib/verify_oci_evidence_approval.py", 0o644),
        ("install_oci_builder_source", "/usr/local/libexec/mee-claw-host-deploy-lib/build_oci_evidence_v2.py", 0o644),
        ("install_oci_independent_verifier_source", "/usr/local/libexec/mee-claw-host-deploy-lib/verify_oci_evidence_v2.py", 0o644),
        ("install_oci_schema", "/usr/local/libexec/schemas/oci-evidence-v2.schema.json", 0o644),
        ("install_policy", "/usr/local/libexec/mee-claw-host-deploy-lib/host-bootstrap-policy.json", 0o644),
        ("install_closure", "/usr/local/libexec/mee-claw-host-deploy-lib/host-package-closure.json", 0o644),
        ("install_oci_approval", "/usr/local/libexec/mee-claw-host-deploy-lib/oci-evidence-approval.json", 0o644),
        ("install_controller", "/usr/local/libexec/mee-claw-host-deploy", 0o755),
        ("install_host_transaction", "/usr/local/libexec/mee-claw-host-deploy-lib/claw_host_bootstrap_transaction.py", 0o644),
        ("install_receipt_writer", "/usr/local/libexec/mee-claw-host-deploy-lib/write_claw_host_bootstrap_receipt.py", 0o644),
        ("install_receipt_verifier", "/usr/local/libexec/mee-claw-host-deploy-lib/verify_claw_host_bootstrap_receipt.py", 0o644),
        ("install_runner_verifier", "/usr/local/libexec/mee-claw-host-deploy-lib/verify_claw_runner_api_canary.py", 0o644),
        ("install_client", "/usr/local/libexec/mee-claw-host-deploy-client", 0o755),
        ("install_socket", "/etc/systemd/system/mee-claw-host-deploy.socket", 0o644),
        ("install_service", "/etc/systemd/system/mee-claw-host-deploy@.service", 0o644),
        ("install_reconcile_service", "/etc/systemd/system/mee-claw-host-deploy-reconcile.service", 0o644),
        ("install_reconcile_timer", "/etc/systemd/system/mee-claw-host-deploy-reconcile.timer", 0o644),
    )
    OPERATIONS = OPERATIONS

    def __init__(
        self, *, source: Path, manifest: Path, controller_sha: str,
        controller_tree: str, root: Path = Path("/"), runner: object | None = None,
    ) -> None:
        if not re.fullmatch(r"[0-9a-f]{40}", controller_sha) or not re.fullmatch(r"[0-9a-f]{40}", controller_tree):
            raise D0Error("SOURCE_IDENTITY")
        self.controller_sha = controller_sha
        self.controller_tree = controller_tree
        self.source = Path(source).resolve()
        self.root = Path(root)
        self.runner = runner or subprocess
        self.snapshots: dict[str, dict[str, object]] = {}
        self.unit_state: dict[str, bool] = {"socket": False, "reconciler": False}
        self.artifacts = self._load_manifest(Path(manifest))
        for base in self.BASE_DIRS:
            projection = self._projection(self._path(base))
            if not projection.get("exists") or projection.get("kind") != "directory":
                raise D0Error("BASE_DIRECTORY_REQUIRED")
        for path, _mode in self.CREATED_DIRS:
            projection = self._projection(self._path(path))
            if projection.get("exists") and projection.get("kind") != "directory":
                raise D0Error("CREATED_DIRECTORY_REQUIRED")
        if self._path("/etc/mee-controller/github-token").exists():
            raise D0Error("LEGACY_TOKEN_PRESENT")

    def _path(self, absolute: str) -> Path:
        path = Path(absolute)
        if self.root == Path("/"):
            return path
        return self.root.joinpath(*path.parts[1:])

    def _load_manifest(self, path: Path) -> dict[str, dict[str, object]]:
        try:
            manifest_bytes, _ = _read_regular(path, limit=1_048_576)
            self.manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
            value = json.loads(manifest_bytes.decode("utf-8", "strict"), object_pairs_hook=_reject_duplicates)
        except (OSError, UnicodeError, ValueError) as exc:
            raise D0Error("MANIFEST_INVALID") from exc
        if set(value) != {"schema_version", "authority", "artifacts"} or value["schema_version"] != "claw-host-deployment-install-manifest-v1" or value["authority"] != "NONE":
            raise D0Error("MANIFEST_INVALID")
        expected = {(operation, target, mode) for operation, target, mode in self.FILE_TARGETS}
        records: dict[str, dict[str, object]] = {}
        for item in value["artifacts"] if isinstance(value["artifacts"], list) else []:
            if not isinstance(item, dict) or set(item) != {"operation", "source", "target", "mode", "sha256"}:
                raise D0Error("MANIFEST_ARTIFACT")
            identity = (item["operation"], item["target"], item["mode"])
            if identity not in expected or item["operation"] in records:
                raise D0Error("MANIFEST_SCOPE")
            relative = Path(str(item["source"]))
            if relative.is_absolute() or ".." in relative.parts:
                raise D0Error("MANIFEST_SOURCE")
            candidate = self.source / relative
            try:
                resolved = candidate.resolve(strict=True)
            except OSError as exc:
                raise D0Error("MANIFEST_SOURCE") from exc
            if self.source not in resolved.parents:
                raise D0Error("MANIFEST_SOURCE")
            data, _ = _read_regular(candidate, limit=4_194_304)
            if not isinstance(item["sha256"], str) or hashlib.sha256(data).hexdigest() != item["sha256"]:
                raise D0Error("MANIFEST_DIGEST")
            records[str(item["operation"])] = {**item, "bytes": data}
        if {(name, item["target"], item["mode"]) for name, item in records.items()} != expected:
            raise D0Error("MANIFEST_SCOPE")
        return records

    def _projection(self, path: Path, *, content: bool = False) -> dict[str, object]:
        if not path.exists() and not path.is_symlink():
            return {"exists": False}
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode) or not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)):
            raise D0Error("UNSAFE_TARGET")
        if stat.S_ISREG(info.st_mode) and info.st_nlink != 1:
            raise D0Error("UNSAFE_TARGET")
        value: dict[str, object] = {
            "exists": True,
            "kind": "directory" if stat.S_ISDIR(info.st_mode) else "file",
            "mode": stat.S_IMODE(info.st_mode),
            "uid": info.st_uid,
            "gid": info.st_gid,
            "dev": info.st_dev,
            "ino": info.st_ino,
            "nlink": info.st_nlink,
            "xattrs": {},
        }
        if hasattr(os, "listxattr"):
            value["xattrs"] = {
                name: os.getxattr(path, name, follow_symlinks=False).hex()
                for name in sorted(os.listxattr(path, follow_symlinks=False))
            }
        if content and value["kind"] == "file":
            value["bytes"] = path.read_bytes().hex()
        return value

    def snapshot(self, operation: str) -> dict[str, object]:
        targets = {name: target for name, target, _ in self.FILE_TARGETS}
        if operation in targets:
            value = self._projection(self._path(targets[operation]), content=True)
        elif operation == "create_state":
            value = {
                "paths": {
                    target: self._projection(self._path(target))
                    for target, _ in self.CREATED_DIRS
                }
            }
        elif operation == "write_receipt":
            value = self._projection(self._path("/var/lib/mee-claw-host-deploy/D0-VERIFIED.json"), content=True)
        elif operation == "enable_socket":
            value = self._unit_projection("mee-claw-host-deploy.socket", "socket")
        elif operation == "enable_reconciler":
            value = self._unit_projection("mee-claw-host-deploy-reconcile.timer", "reconciler")
        else:
            value = {"observed": True}
        self.snapshots[operation] = value
        return value

    def _run(self, argv: list[str]) -> None:
        if self.root == Path("/"):
            self.runner.run(argv, check=True)

    def _unit_projection(self, unit: str, key: str) -> dict[str, bool]:
        if self.root != Path("/"):
            return {"enabled": self.unit_state[key], "active": self.unit_state[key]}
        enabled = self.runner.run(
            ["/usr/bin/systemctl", "is-enabled", unit], check=False,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        ).returncode == 0
        active = self.runner.run(
            ["/usr/bin/systemctl", "is-active", unit], check=False,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        ).returncode == 0
        return {"enabled": enabled, "active": active}

    def apply(self, operation: str) -> None:
        targets = {name: (target, mode) for name, target, mode in self.FILE_TARGETS}
        if operation == "create_state":
            for target, mode in self.CREATED_DIRS:
                path = self._path(target)
                if not path.exists():
                    path.mkdir()
                    os.chmod(path, mode)
        elif operation in targets:
            target, mode = targets[operation]
            _atomic(self._path(target), self.artifacts[operation]["bytes"], mode)
        elif operation == "daemon_reload":
            self._run(["/usr/bin/systemctl", "daemon-reload"])
        elif operation == "enable_socket":
            self._run(["/usr/bin/systemctl", "enable", "--now", "mee-claw-host-deploy.socket"])
            self.unit_state["socket"] = True
        elif operation == "enable_reconciler":
            self._run(["/usr/bin/systemctl", "enable", "--now", "mee-claw-host-deploy-reconcile.timer"])
            self.unit_state["reconciler"] = True
        elif operation == "verify_installed":
            for name, target, mode in self.FILE_TARGETS:
                path = self._path(target)
                if path.read_bytes() != self.artifacts[name]["bytes"]:
                    raise D0Error("INSTALLED_MISMATCH")
                if os.name == "posix" and stat.S_IMODE(path.stat().st_mode) != mode:
                    raise D0Error("INSTALLED_MISMATCH")
            self._run([
                "/usr/bin/systemd-analyze", "verify",
                "/etc/systemd/system/mee-claw-host-deploy.socket",
                "/etc/systemd/system/mee-claw-host-deploy@.service",
                "/etc/systemd/system/mee-claw-host-deploy-reconcile.service",
                "/etc/systemd/system/mee-claw-host-deploy-reconcile.timer",
            ])
        elif operation == "write_receipt":
            receipt = {
                "schema_version": "claw-host-deployment-d0-receipt-v1",
                "authority": "NONE",
                "not_host_receipt": True,
                "repository": "Dimkox/multi-exchange-engine",
                "controller_sha": self.controller_sha,
                "controller_tree": self.controller_tree,
                "install_manifest_sha256": self.manifest_sha256,
                "artifact_count": len(self.artifacts),
                "status": "D0_VERIFIED",
                "created_at": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
            }
            _atomic(
                self._path("/var/lib/mee-claw-host-deploy/D0-VERIFIED.json"),
                (json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n").encode(),
            )

    def _restore(self, path: Path, snapshot: dict[str, object]) -> None:
        if not snapshot["exists"]:
            if path.is_file() or path.is_symlink():
                if os.name == "nt" and not path.is_symlink():
                    os.chmod(path, 0o600)
                path.unlink()
            elif path.is_dir():
                path.rmdir()
            return
        if snapshot["kind"] == "directory":
            path.mkdir(parents=True, exist_ok=True)
        else:
            _atomic(path, bytes.fromhex(str(snapshot["bytes"])), int(snapshot["mode"]))
        os.chmod(path, int(snapshot["mode"]))
        if os.name == "posix":
            os.chown(path, int(snapshot["uid"]), int(snapshot["gid"]))
        if hasattr(os, "listxattr"):
            for name in os.listxattr(path, follow_symlinks=False):
                os.removexattr(path, name, follow_symlinks=False)
            for name, value in dict(snapshot["xattrs"]).items():
                os.setxattr(path, name, bytes.fromhex(str(value)), follow_symlinks=False)

    def rollback(self, operation: str) -> None:
        targets = {name: target for name, target, _ in self.FILE_TARGETS}
        snapshot = self.snapshots[operation]
        if operation in targets:
            self._restore(self._path(targets[operation]), snapshot)
        elif operation == "create_state":
            for target, _ in reversed(self.CREATED_DIRS):
                self._restore(self._path(target), dict(snapshot["paths"])[target])
        elif operation == "write_receipt":
            self._restore(self._path("/var/lib/mee-claw-host-deploy/D0-VERIFIED.json"), snapshot)
        elif operation == "enable_socket":
            self._restore_unit("mee-claw-host-deploy.socket", "socket", snapshot)
        elif operation == "enable_reconciler":
            self._restore_unit("mee-claw-host-deploy-reconcile.timer", "reconciler", snapshot)
        elif operation == "daemon_reload":
            self._run(["/usr/bin/systemctl", "daemon-reload"])

    def _restore_unit(self, unit: str, key: str, snapshot: dict[str, object]) -> None:
        self._run(["/usr/bin/systemctl", "enable" if snapshot["enabled"] else "disable", unit])
        self._run(["/usr/bin/systemctl", "start" if snapshot["active"] else "stop", unit])
        self.unit_state[key] = bool(snapshot["enabled"] and snapshot["active"])


def _rollback_all(backend: object, journal: D0Journal) -> list[dict[str, str]]:
    current = journal.value["current"]
    operations = ([current] if current else []) + list(reversed(journal.value["applied"]))
    failures: list[dict[str, str]] = []
    for operation in operations:
        try:
            backend.rollback(operation)
        except BaseException as exc:
            failures.append({"operation": operation, "code": type(exc).__name__})
    if failures:
        journal.record("ROLLBACK_BLOCKED", status="OPEN", failures=failures)
    else:
        journal.value["applied"] = []
        journal.value["current"] = None
        journal.record("ROLLED_BACK", status="ROLLED_BACK", failures=[])
    return failures


def execute(backend: object, journal: D0Journal) -> None:
    try:
        for operation in OPERATIONS:
            snapshot = backend.snapshot(operation)
            journal.applying(operation, snapshot)
            backend.apply(operation)
            journal.applied(operation)
        journal.record("COMMITTED", status="COMMITTED")
    except BaseException:
        journal.record("ROLLING_BACK")
        _rollback_all(backend, journal)
        raise


def recover(backend: object, journal: D0Journal) -> None:
    backend.snapshots.update(journal.value["snapshots"])
    journal.record("ROLLING_BACK", status="OPEN")
    if _rollback_all(backend, journal):
        raise D0Error("ROLLBACK_BLOCKED")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--journal", type=Path, required=True)
    parser.add_argument("--controller-sha", required=True)
    parser.add_argument("--controller-tree", required=True)
    parser.add_argument("--mode", choices=("apply", "resume", "rollback"), required=True)
    args = parser.parse_args(argv)
    try:
        backend = RealD0Backend(
            source=args.source, manifest=args.manifest,
            controller_sha=args.controller_sha, controller_tree=args.controller_tree,
        )
        if args.mode == "apply":
            execute(backend, D0Journal(args.journal))
        elif args.mode == "resume":
            recover(backend, D0Journal.resume(args.journal))
        else:
            recover(backend, D0Journal.resume_terminal(args.journal))
        return 0
    except (D0Error, OSError, subprocess.SubprocessError) as exc:
        print(f"CLAW_HOST_DEPLOYMENT_INSTALL_ERROR:{exc}", file=__import__("sys").stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
