from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "installer/lib/lifecycle.py"
SPEC = importlib.util.spec_from_file_location("installer_lifecycle", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
LIFECYCLE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LIFECYCLE)

LEDGER = [
    {"name": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    for path in sorted((ROOT / "apps/mezo-gateway/migrations").glob("*.sql"))
]
IMAGES = {name: f"registry.invalid/liqvera/{name}@sha256:{hashlib.sha256(name.encode()).hexdigest()}"
          for name in ("edge", "web", "gateway", "capture", "report", "postgres")}


class FakeAdapter:
    def __init__(self) -> None:
        self.trace: list[tuple[object, ...]] = []
        self.healthy = True
        self.migration_committed = False
        self.log_text = ("ok\nAuthorization: Bearer CANARY\npostgres://user:secret@db/x\n"
                         "REPORT_SERVICE_TOKEN=REPORT_CANARY\nPAYMENT_SIGNATURE=SIGNATURE_CANARY\n")

    def start(self, project: str, release: Path) -> None:
        self.trace.append(("start", project, release.name))

    def stop(self, project: str) -> None:
        self.trace.append(("stop", project))

    def health(self, project: str) -> bool:
        self.trace.append(("health", project))
        return self.healthy

    def migration_ledger(self) -> list[dict[str, str]]:
        return LEDGER

    def backup(self, project: str) -> dict[str, object]:
        self.trace.append(("backup", project))
        return {"complete": True, "sha256": "b" * 64}

    def migrate(self, project: str, release: Path) -> bool:
        self.trace.append(("migrate", project, release.name))
        return self.migration_committed

    def remove_runtime(self, project: str) -> None:
        self.trace.append(("remove_runtime", project))

    def purge(self, targets: tuple[str, ...]) -> None:
        self.trace.append(("purge", *targets))

    def logs(self, project: str, service: str, tail: int, since: str) -> str:
        self.trace.append(("logs", project, service, tail, since))
        return self.log_text


def release(root: Path, digest: str, *, compatible: bool = True) -> Path:
    target = root / "releases" / f"0.0.2-{digest[:12]}"
    target.mkdir(parents=True)
    payload = b"fixture\n"
    compose = (ROOT / "installer/compose.yaml").read_bytes()
    (target / "payload.txt").write_bytes(payload)
    (target / "compose.yaml").write_bytes(compose)
    package_manifest = {
        "schema_version": "liqvera-installer-release/v1", "product_version": "0.0.2",
        "git_commit": digest[:40], "git_tree": digest[-40:], "images": IMAGES,
        "database_compatibility": {"accepted_migrations": LEDGER, "down_migrations": False},
    }
    (target / "manifests").mkdir()
    manifest_bytes = json.dumps(package_manifest, sort_keys=True).encode()
    (target / "manifests/release-manifest.json").write_bytes(manifest_bytes)
    sums = (f"{hashlib.sha256(compose).hexdigest()}  compose.yaml\n"
            f"{hashlib.sha256(manifest_bytes).hexdigest()}  manifests/release-manifest.json\n"
            f"{hashlib.sha256(payload).hexdigest()}  payload.txt\n").encode()
    (target / "SHA256SUMS").write_bytes(sums)
    metadata = {
        "schema_version": "liqvera-lifecycle-release/v1",
        "product_version": "0.0.2",
        "release_sha256": digest,
        "inventory_sha256": hashlib.sha256(sums).hexdigest(),
        "git_commit": digest[:40],
        "git_tree": digest[-40:],
        "database_compatibility": LEDGER if compatible else LEDGER[:-1],
        "images": IMAGES,
    }
    (target / "release.json").write_text(json.dumps(metadata))
    return target


def installed(tmp_path: Path) -> tuple[Path, str, Path]:
    root = tmp_path / "install"
    root.mkdir(mode=0o700)
    (root / "state").mkdir(mode=0o700)
    digest = "a" * 64
    current = release(root, digest)
    (root / "current").symlink_to(current.relative_to(root))
    install_state = {
        "product_version": "0.0.2", "release_sha256": digest,
        "git_commit": "a" * 40, "git_tree": "a" * 40,
        "inventory_sha256": json.loads((current / "release.json").read_text())["inventory_sha256"],
        "compose_project": "liqvera-test", "last_completed_phase": "HEALTHY",
    }
    (root / "state/install-state.json").write_text(json.dumps(install_state))
    return root, digest, current


def runtime_files(root: Path, current: Path) -> None:
    (root / "config").mkdir(exist_ok=True)
    (root / "config/runtime.env").write_text(
        "LIQVERA_CHAIN_ID=31611\nLIQVERA_PAYMENT_ENABLED=false\nLIQVERA_SOURCE_MODE=shadow\n"
        "LIQVERA_ENGINE_COMMIT=" + "a" * 40 + "\n"
        "LIQVERA_WEB_HOST=127.0.0.1\nLIQVERA_WEB_PORT=3000\n"
        "LIQVERA_GATEWAY_HOST=127.0.0.1\nLIQVERA_GATEWAY_PORT=8080\n"
        "LIQVERA_METRICS_HOST=127.0.0.1\nLIQVERA_METRICS_PORT=9090\n"
        + "".join(f"LIQVERA_IMAGE_{name.upper()}={value}\n" for name, value in sorted(IMAGES.items()))
    )


def test_start_stop_are_idempotent_and_status_is_closed(tmp_path: Path) -> None:
    root, digest, _ = installed(tmp_path)
    adapter = FakeAdapter()
    assert LIFECYCLE.run_lifecycle(root, "stop", {}, adapter)["status"] == "STOPPED"
    assert LIFECYCLE.run_lifecycle(root, "stop", {}, adapter)["status"] == "STOPPED"
    assert LIFECYCLE.run_lifecycle(root, "start", {}, adapter)["status"] == "HEALTHY"
    status = LIFECYCLE.run_lifecycle(root, "status", {}, adapter)
    assert set(status) == {"schema_version", "status", "version", "release_sha256", "git_commit",
                           "git_tree", "compose_project", "service_manager", "blockers"}
    assert status["release_sha256"] == digest
    assert [item[0] for item in adapter.trace].count("start") == 1
    assert [item[0] for item in adapter.trace].count("stop") == 1


def test_update_stages_and_health_checks_before_atomic_current_switch(tmp_path: Path) -> None:
    root, old_digest, old = installed(tmp_path)
    new_digest = "b" * 64
    candidate = release(root, new_digest)
    adapter = FakeAdapter()
    result = LIFECYCLE.run_lifecycle(
        root, "update", {"version": "0.0.2", "sha256": new_digest}, adapter,
    )
    assert result["status"] == "HEALTHY"
    assert (root / "current").resolve() == candidate.resolve()
    assert json.loads((root / "state/lifecycle.json").read_text())["previous"]["release_sha256"] == old_digest
    assert ("health", "liqvera-test") in adapter.trace
    assert old.exists()


def test_failed_candidate_health_preserves_prior_pointer_and_data(tmp_path: Path) -> None:
    root, _, old = installed(tmp_path)
    release(root, "b" * 64)
    adapter = FakeAdapter()
    adapter.healthy = False
    with pytest.raises(LIFECYCLE.LifecycleError, match="HEALTH_TIMEOUT"):
        LIFECYCLE.run_lifecycle(root, "update", {"version": "0.0.2", "sha256": "b" * 64}, adapter)
    assert (root / "current").resolve() == old.resolve()
    assert ("stop", "liqvera-test") in adapter.trace
    assert not any(item[0] == "purge" for item in adapter.trace)


def test_update_crash_after_migration_never_repeats_migration(tmp_path: Path) -> None:
    root, _, _ = installed(tmp_path)
    release(root, "b" * 64)
    adapter = FakeAdapter()
    adapter.migration_committed = True
    with pytest.raises(LIFECYCLE.InjectedCrash):
        LIFECYCLE.run_lifecycle(
            root, "update", {"version": "0.0.2", "sha256": "b" * 64,
                             "crash_after": "MIGRATION_COMMITTED"}, adapter,
        )
    adapter.trace.clear()
    with pytest.raises(LIFECYCLE.LifecycleError, match="ROLLBACK_RESTORE_REQUIRED"):
        LIFECYCLE.run_lifecycle(root, "start", {}, adapter)
    assert not any(item[0] == "migrate" for item in adapter.trace)


@pytest.mark.parametrize("phase", ["INTENT", "BACKUP_COMPLETE", "CANDIDATE_STARTED", "HEALTHY", "POINTER_SWITCHED"])
def test_update_resumes_each_non_irreversible_crash_boundary(tmp_path: Path, phase: str) -> None:
    root, _, _ = installed(tmp_path)
    candidate = release(root, "b" * 64)
    adapter = FakeAdapter()
    with pytest.raises(LIFECYCLE.InjectedCrash, match=phase):
        LIFECYCLE.run_lifecycle(
            root, "update", {"version": "0.0.2", "sha256": "b" * 64, "crash_after": phase}, adapter,
        )
    result = LIFECYCLE.run_lifecycle(
        root, "update", {"version": "0.0.2", "sha256": "b" * 64}, adapter,
    )
    assert result["status"] == "HEALTHY"
    assert (root / "current").resolve() == candidate.resolve()
    assert LIFECYCLE.load_lifecycle_state(root)["operation"] is None


def test_rollback_after_migration_requires_exact_prior_compatibility(tmp_path: Path) -> None:
    root, _, old = installed(tmp_path)
    state = LIFECYCLE.bootstrap_state(root)
    current = release(root, "b" * 64)
    (root / "current").unlink()
    (root / "current").symlink_to(current.relative_to(root))
    state["previous"] = json.loads((old / "release.json").read_text())
    state["current"] = json.loads((current / "release.json").read_text())
    state["migration_committed"] = True
    LIFECYCLE.write_lifecycle_state(root, state)
    adapter = FakeAdapter()
    assert LIFECYCLE.run_lifecycle(root, "rollback", {}, adapter)["status"] == "HEALTHY"
    state = LIFECYCLE.load_lifecycle_state(root)
    state["previous"]["database_compatibility"] = [*LEDGER[:-1], {**LEDGER[-1], "sha256": "0" * 64}]
    state["migration_committed"] = True
    LIFECYCLE.write_lifecycle_state(root, state)
    with pytest.raises(LIFECYCLE.LifecycleError, match="ROLLBACK_RESTORE_REQUIRED"):
        LIFECYCLE.run_lifecycle(root, "rollback", {}, adapter)


def test_default_uninstall_preserves_data_and_purge_requires_exact_token(tmp_path: Path) -> None:
    root, _, _ = installed(tmp_path)
    for name in ("config", "logs", "backups", "data"):
        (root / name).mkdir(exist_ok=True)
        (root / name / "sentinel").write_text(name)
    adapter = FakeAdapter()
    result = LIFECYCLE.run_lifecycle(root, "uninstall", {}, adapter)
    assert result["status"] == "UNINSTALLED"
    assert all((root / name / "sentinel").exists() for name in ("config", "logs", "backups", "data"))
    preview = LIFECYCLE.purge_preview(root)
    with pytest.raises(LIFECYCLE.LifecycleError, match="PURGE_CONFIRMATION_REQUIRED"):
        LIFECYCLE.run_lifecycle(root, "uninstall", {"purge_data": True, "confirm_purge": "wrong"}, adapter)
    LIFECYCLE.run_lifecycle(root, "uninstall", {"purge_data": True, "confirm_purge": preview["token"]}, adapter)
    assert any(item[0] == "purge" for item in adapter.trace)


def test_purge_refuses_symlink_or_broad_target(tmp_path: Path) -> None:
    root, _, _ = installed(tmp_path)
    (root / "data").symlink_to(tmp_path)
    with pytest.raises(LIFECYCLE.LifecycleError, match="PURGE_CONFIRMATION_REQUIRED"):
        LIFECYCLE.purge_preview(root)


def test_logs_are_bounded_redacted_and_validate_arguments(tmp_path: Path) -> None:
    root, _, _ = installed(tmp_path)
    adapter = FakeAdapter()
    result = LIFECYCLE.run_lifecycle(root, "logs", {"service": "gateway", "tail": 50, "since": "10m"}, adapter)
    assert "CANARY" not in result["logs"] and "secret" not in result["logs"]
    assert "[REDACTED]" in result["logs"]
    with pytest.raises(LIFECYCLE.LifecycleError, match="CONFIG_INVALID"):
        LIFECYCLE.run_lifecycle(root, "logs", {"service": "../../x", "tail": 10_000, "since": "all"}, adapter)


def test_concurrent_lock_fails_closed_without_effect(tmp_path: Path) -> None:
    root, _, _ = installed(tmp_path)
    held = LIFECYCLE.LifecycleLock.acquire(root)
    adapter = FakeAdapter()
    try:
        with pytest.raises(LIFECYCLE.LifecycleError, match="LIFECYCLE_BUSY"):
            LIFECYCLE.run_lifecycle(root, "stop", {}, adapter)
    finally:
        held.close()
    assert adapter.trace == []


def test_compose_adapter_uses_fixed_argv_and_never_removes_volumes(tmp_path: Path) -> None:
    root, _, current = installed(tmp_path)
    runtime_files(root, current)
    calls: list[tuple[tuple[str, ...], dict[str, object]]] = []

    def runner(argv: tuple[str, ...], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        calls.append((argv, kwargs))
        rows = [
            {"Service": service, "State": "running", "Health": "healthy"}
            for service in ("postgres", "capture", "report", "gateway", "web", "edge")
        ] + [{"Service": "migrate", "State": "exited", "Health": "", "ExitCode": 0}]
        if argv[-4:] == ("ps", "--all", "--format", "json"):
            output = json.dumps(rows).encode()
        elif argv[-2:] == ("readiness", "--json"):
            output = json.dumps({"status": "BLOCKED", "blockers": ["SIMULATED_SOURCE", "EXTERNAL_GRANT_REQUIRED"]}).encode()
        else:
            output = b""
        return subprocess.CompletedProcess(argv, 0, output, b"")

    readiness = {"schema": "mee-evidence-readiness/v1", "request_id": "0" * 36,
                 "ready": False, "storage_ready": True, "configuration_ready": False,
                 "integration_ready": True, "payment_ready": False,
                 "blockers": ["SIMULATED_SOURCE", "EXTERNAL_GRANT_REQUIRED", "PAY_TO_MISSING"]}
    adapter = LIFECYCLE.ComposeAdapter(root, runner, lambda: readiness)
    adapter.start("liqvera-test", current)
    assert adapter.health("liqvera-test") is True
    adapter.remove_runtime("liqvera-test")
    assert all(call[0][0] == "/usr/bin/docker" for call in calls)
    assert all("--volumes" not in call[0] and "-v" not in call[0] for call in calls)
    assert all(call[1]["env"] == {"PATH": "/usr/bin:/bin"} for call in calls)


def test_compose_health_requires_exact_unique_service_states(tmp_path: Path) -> None:
    root, _, current = installed(tmp_path)
    runtime_files(root, current)
    rows = [{"Service": name, "State": "running", "Health": "healthy"}
            for name in ("postgres", "capture", "report", "gateway", "web", "edge")]
    rows.append({"Service": "gateway", "State": "exited", "Health": ""})
    def runner(argv: tuple[str, ...], **_: object) -> subprocess.CompletedProcess[bytes]:
        return subprocess.CompletedProcess(argv, 0, json.dumps(rows).encode(), b"")
    assert LIFECYCLE.ComposeAdapter(root, runner).health("liqvera-test") is False


def test_migrate_exception_records_uncertain_outcome(tmp_path: Path) -> None:
    root, _, _ = installed(tmp_path)
    release(root, "b" * 64)
    adapter = FakeAdapter()
    adapter.migrate = lambda project, path: (_ for _ in ()).throw(RuntimeError("lost response"))
    with pytest.raises(LIFECYCLE.LifecycleError, match="ROLLBACK_RESTORE_REQUIRED"):
        LIFECYCLE.run_lifecycle(root, "update", {"version": "0.0.2", "sha256": "b" * 64}, adapter)
    state = LIFECYCLE.load_lifecycle_state(root)
    assert state["migration_committed"] is True
    assert state["operation"]["phase"] == "MIGRATION_COMMITTED"


def test_partial_candidate_start_is_always_stopped(tmp_path: Path) -> None:
    root, _, _ = installed(tmp_path)
    release(root, "b" * 64)
    adapter = FakeAdapter()
    def partial(project: str, path: Path) -> None:
        adapter.trace.append(("start-partial", project))
        raise RuntimeError("partial")
    adapter.start = partial
    with pytest.raises(LIFECYCLE.LifecycleError, match="LIFECYCLE_COMMAND_FAILED"):
        LIFECYCLE.run_lifecycle(root, "update", {"version": "0.0.2", "sha256": "b" * 64}, adapter)
    assert ("stop", "liqvera-test") in adapter.trace


def test_pointer_switch_crash_is_reconciled_from_disk(tmp_path: Path) -> None:
    root, _, _ = installed(tmp_path)
    candidate = release(root, "b" * 64)
    adapter = FakeAdapter()
    with pytest.raises(LIFECYCLE.InjectedCrash):
        LIFECYCLE.run_lifecycle(root, "update", {"version": "0.0.2", "sha256": "b" * 64,
                                                 "crash_after": "POINTER_SWITCHED"}, adapter)
    # Simulate the smaller crash window: pointer persisted, phase marker remained HEALTHY.
    state_path = root / "state/lifecycle.json"
    state = json.loads(state_path.read_text())
    state["operation"]["phase"] = "HEALTHY"
    state["current"] = state["operation"]["prior"]
    state_path.write_text(json.dumps(state))
    result = LIFECYCLE.run_lifecycle(root, "status", {}, adapter)
    assert result["release_sha256"] == "b" * 64
    assert (root / "current").resolve() == candidate.resolve()


def test_runtime_files_are_rehashed_before_compose_use(tmp_path: Path) -> None:
    root, _, current = installed(tmp_path)
    (root / "config").mkdir()
    env = root / "config/runtime.env"
    compose = current / "compose.yaml"
    env.write_text("LIQVERA_PAYMENT_ENABLED=false\nLIQVERA_SOURCE_MODE=shadow\n" +
                   "".join(f"LIQVERA_IMAGE_{name.upper()}={value}\n" for name, value in sorted(IMAGES.items())))
    compose.write_bytes((ROOT / "installer/compose.yaml").read_bytes())
    adapter = LIFECYCLE.ComposeAdapter(root, lambda argv, **kwargs: subprocess.CompletedProcess(argv, 0, b"", b""))
    adapter.bind_runtime(current, compose, env)
    compose.write_text("services: {evil: {}}\n")
    with pytest.raises(LIFECYCLE.LifecycleError, match="ARCHIVE_INVALID"):
        adapter.start("liqvera-test", current)


def test_runtime_image_values_are_exactly_manifest_bound(tmp_path: Path) -> None:
    root, _, current = installed(tmp_path)
    runtime_files(root, current)
    env = root / "config/runtime.env"
    env.write_text(env.read_text().replace(IMAGES["web"], "registry.invalid/liqvera/web:latest"))
    adapter = LIFECYCLE.ComposeAdapter(root, lambda argv, **kwargs: subprocess.CompletedProcess(argv, 0, b"", b""))
    with pytest.raises(LIFECYCLE.LifecycleError, match="CONFIG_INVALID"):
        adapter.start("liqvera-test", current)


def test_coordinated_release_metadata_and_env_image_rewrite_cannot_reuse_inventory_authority(
    tmp_path: Path,
) -> None:
    root, _, current = installed(tmp_path)
    runtime_files(root, current)
    changed = dict(IMAGES)
    changed["web"] = "registry.invalid/attacker/web@sha256:" + "f" * 64
    metadata = json.loads((current / "release.json").read_text())
    metadata["images"] = changed
    (current / "release.json").write_text(json.dumps(metadata))
    env = root / "config/runtime.env"
    env.write_text(env.read_text().replace(IMAGES["web"], changed["web"]))

    adapter = LIFECYCLE.ComposeAdapter(
        root, lambda argv, **kwargs: subprocess.CompletedProcess(argv, 0, b"", b"")
    )
    with pytest.raises(LIFECYCLE.LifecycleError, match="ARCHIVE_INVALID"):
        adapter.start("liqvera-test", current)


def test_locked_root_replacement_cannot_receive_state_write(tmp_path: Path) -> None:
    root, _, _ = installed(tmp_path)
    displaced = tmp_path / "displaced"
    adapter = FakeAdapter()
    original_stop = adapter.stop
    def replace_root(project: str) -> None:
        original_stop(project)
        root.rename(displaced)
        root.mkdir(mode=0o700)
    adapter.stop = replace_root
    with pytest.raises(LIFECYCLE.LifecycleError, match="UNSAFE_INSTALL_ROOT"):
        LIFECYCLE.run_lifecycle(root, "stop", {}, adapter)
    assert not (root / "state/lifecycle.json").exists()


def test_purge_removes_runtime_before_owned_volumes(tmp_path: Path) -> None:
    root, _, _ = installed(tmp_path)
    adapter = FakeAdapter()
    preview = LIFECYCLE.purge_preview(root)
    LIFECYCLE.run_lifecycle(root, "uninstall", {"purge_data": True,
                                                "confirm_purge": preview["token"]}, adapter)
    kinds = [item[0] for item in adapter.trace]
    assert kinds.index("remove_runtime") < kinds.index("purge")


def test_backup_callback_root_swap_cannot_redirect_update_journal(tmp_path: Path) -> None:
    root, _, _ = installed(tmp_path)
    release(root, "b" * 64)
    displaced = tmp_path / "displaced"
    adapter = FakeAdapter()
    def swapped(_: str) -> dict[str, object]:
        root.rename(displaced)
        root.mkdir(mode=0o700)
        return {"complete": True, "sha256": "b" * 64}
    adapter.backup = swapped
    with pytest.raises(LIFECYCLE.LifecycleError, match="UNSAFE_INSTALL_ROOT"):
        LIFECYCLE.run_lifecycle(root, "update", {"version": "0.0.2", "sha256": "b" * 64}, adapter)
    assert not (root / "state/lifecycle.json").exists()


def test_compose_purge_requires_exact_full_project_label(tmp_path: Path) -> None:
    root, _, current = installed(tmp_path)
    runtime_files(root, current)
    calls: list[tuple[str, ...]] = []
    def runner(argv: tuple[str, ...], **_: object) -> subprocess.CompletedProcess[bytes]:
        calls.append(argv)
        body = json.dumps([{"Labels": {"com.docker.compose.project": "liqvera-test"}}]).encode()
        return subprocess.CompletedProcess(argv, 0, body, b"")
    adapter = LIFECYCLE.ComposeAdapter(root, runner)
    targets = tuple(f"liqvera-test_{name}" for name in
                    ("postgres_data", "captures", "artifacts", "caddy_data", "caddy_config"))
    adapter.purge(targets)
    assert calls[-1][-5:] == targets


def test_injected_log_adapter_rejects_oversized_capture(tmp_path: Path) -> None:
    root, _, current = installed(tmp_path)
    runtime_files(root, current)
    def runner(argv: tuple[str, ...], **_: object) -> subprocess.CompletedProcess[bytes]:
        return subprocess.CompletedProcess(argv, 0, b"x" * 65537, b"")
    with pytest.raises(LIFECYCLE.LifecycleError, match="LIFECYCLE_COMMAND_FAILED"):
        LIFECYCLE.ComposeAdapter(root, runner).logs("liqvera-test", "gateway", 100, "10m")


def test_readiness_probe_uses_real_bounded_readyz_http_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    body = json.dumps({"schema": "mee-evidence-readiness/v1", "request_id": "0" * 36,
                       "ready": False, "storage_ready": True, "configuration_ready": False,
                       "integration_ready": True, "payment_ready": False,
                       "blockers": ["SIMULATED_SOURCE", "EXTERNAL_GRANT_REQUIRED"]}).encode()
    class Response:
        status = 503
        def getheader(self, _: str) -> None: return None
        def read(self, size: int) -> bytes:
            nonlocal body
            chunk, body = body[:size], body[size:]
            return chunk
    class Connection:
        def __init__(self, host: str, port: int, timeout: int) -> None:
            assert (host, port, timeout) == ("127.0.0.1", 3000, 5)
        def request(self, method: str, path: str, headers: dict[str, str]) -> None:
            assert method == "GET" and path == "/readyz" and headers["Connection"] == "close"
        def getresponse(self) -> Response: return Response()
        def close(self) -> None: pass
    monkeypatch.setattr(LIFECYCLE.http.client, "HTTPConnection", Connection)
    assert LIFECYCLE._read_readyz()["storage_ready"] is True


def test_readiness_rejects_unknown_or_integrity_blocker(tmp_path: Path) -> None:
    root, _, current = installed(tmp_path)
    runtime_files(root, current)
    rows = [{"Service": service, "State": "running", "Health": "healthy"}
            for service in ("postgres", "capture", "report", "gateway", "web", "edge")]
    rows.append({"Service": "migrate", "State": "exited", "Health": "", "ExitCode": 0})
    def runner(argv: tuple[str, ...], **_: object) -> subprocess.CompletedProcess[bytes]:
        return subprocess.CompletedProcess(argv, 0, json.dumps(rows).encode(), b"")
    base = {"schema": "mee-evidence-readiness/v1", "request_id": "0" * 36,
            "ready": False, "storage_ready": True, "configuration_ready": False,
            "integration_ready": True, "payment_ready": False,
            "blockers": ["SIMULATED_SOURCE", "EXTERNAL_GRANT_REQUIRED", "ARTIFACT_INTEGRITY_FAILURE"]}
    assert LIFECYCLE.ComposeAdapter(root, runner, lambda: base).health("liqvera-test") is False
