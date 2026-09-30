from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
RUNTIME_PATH = ROOT / "installer" / "lib" / "runtime.py"
INSTALLER = ROOT / "installer" / "install.sh"
PROCESS_FIXTURES = ROOT / "tests/installer/fixtures/process-fixtures.json"
SPEC = importlib.util.spec_from_file_location("liqvera_installer_runtime", RUNTIME_PATH)
assert SPEC is not None and SPEC.loader is not None
RUNTIME = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RUNTIME
SPEC.loader.exec_module(RUNTIME)


def safe_config(secret_file: Path | None = None) -> dict[str, object]:
    secret_files = {}
    if secret_file is not None:
        secret_files["DATABASE_PASSWORD_FILE"] = str(secret_file)
    return {
        "schema_version": "liqvera-install-config/v1",
        "chain_id": 31611,
        "payment_enabled": False,
        "source_mode": "shadow",
        "ports": {
            "web": {"host": "127.0.0.1", "port": 3000},
            "gateway": {"host": "127.0.0.1", "port": 8080},
            "metrics": {"host": "127.0.0.1", "port": 9090},
        },
        "secret_files": secret_files,
    }


def facts(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "kernel": "Linux",
        "distribution": "ubuntu",
        "distribution_version": "24.04",
        "architecture": "x86_64",
        "bash_version": "5.2.21",
        "docker_version": "27.5.1",
        "compose_version": "2.32.4",
        "docker_endpoint": "unix:///var/run/docker.sock",
        "daemon_reachable": True,
        "disk_bytes": 4 * 1024**3,
        "memory_bytes": 2 * 1024**3,
        "filesystem_type": "ext4",
        "ports_available": {"web": True, "gateway": True, "metrics": True},
    }
    value.update(overrides)
    return value


def request(install_root: Path, config: dict[str, object] | None = None) -> dict[str, object]:
    return {
        "schema_version": "liqvera-preflight-request/v1",
        "install_root": str(install_root),
        "config": safe_config() if config is None else config,
    }


@pytest.mark.parametrize(
    ("distribution", "version", "machine", "normalized"),
    [
        ("ubuntu", "22.04", "x86_64", "amd64"),
        ("ubuntu", "24.04", "aarch64", "arm64"),
        ("debian", "12", "x86_64", "amd64"),
        ("fedora", "40", "aarch64", "arm64"),
        ("rhel", "9", "x86_64", "amd64"),
    ],
)
def test_preflight_accepts_only_frozen_linux_matrix(
    tmp_path: Path, distribution: str, version: str, machine: str, normalized: str
) -> None:
    root = tmp_path / "install root"
    result = RUNTIME.preflight(
        request(root),
        facts(distribution=distribution, distribution_version=version, architecture=machine),
    )
    assert result["schema_version"] == "liqvera-preflight-result/v1"
    assert result["status"] == "PASS"
    assert result["architecture"] == normalized
    assert result["install_root"] == str(root.resolve(strict=False))
    assert not root.exists()


@pytest.mark.parametrize(
    "mutation",
    [
        {"kernel": "Darwin"},
        {"distribution": "mint"},
        {"distribution": "ubuntu", "distribution_version": "20.04"},
        {"architecture": "i686"},
    ],
)
def test_preflight_rejects_unsupported_linux_before_mutation(
    tmp_path: Path, mutation: dict[str, object]
) -> None:
    root = tmp_path / "install"
    with pytest.raises(RUNTIME.InstallerError, match="UNSUPPORTED_LINUX"):
        RUNTIME.preflight(request(root), facts(**mutation))
    assert not root.exists()


@pytest.mark.parametrize(
    "mutation",
    [
        {"bash_version": "5.1.99"},
        {"docker_version": "26.9.9"},
        {"compose_version": "2.29.9"},
        {"daemon_reachable": False},
        {"docker_endpoint": "tcp://127.0.0.1:2375"},
        {"disk_bytes": 4 * 1024**3 - 1},
        {"memory_bytes": 2 * 1024**3 - 1},
    ],
)
def test_preflight_enforces_dependency_resource_and_local_daemon_floors(
    tmp_path: Path, mutation: dict[str, object]
) -> None:
    code = "DEPENDENCY_MISSING"
    with pytest.raises(RUNTIME.InstallerError, match=code):
        RUNTIME.preflight(request(tmp_path / "install"), facts(**mutation))


def test_preflight_rejects_unsafe_roots_and_occupied_ports(tmp_path: Path) -> None:
    world_writable = tmp_path / "shared"
    world_writable.mkdir(mode=0o777)
    world_writable.chmod(0o777)
    with pytest.raises(RUNTIME.InstallerError, match="UNSAFE_INSTALL_ROOT"):
        RUNTIME.preflight(request(world_writable / "liqvera"), facts())

    link = tmp_path / "link"
    link.symlink_to(tmp_path / "elsewhere")
    with pytest.raises(RUNTIME.InstallerError, match="UNSAFE_INSTALL_ROOT"):
        RUNTIME.preflight(request(link / "liqvera"), facts())

    root = tmp_path / "install"
    with pytest.raises(RUNTIME.InstallerError, match="PORT_OCCUPIED.*gateway"):
        RUNTIME.preflight(
            request(root),
            facts(ports_available={"web": True, "gateway": False, "metrics": True}),
        )
    assert not root.exists()


def test_config_rejects_live_payment_unknown_and_control_values(tmp_path: Path) -> None:
    base = safe_config()
    mutations = [
        {**base, "source_mode": "live-public"},
        {**base, "payment_enabled": True},
        {**base, "chain_id": 1},
        {**base, "unknown": "value"},
        {**base, "secret_files": {"P3_LIVE_GRANTS_FILE": "/tmp/grants"}},
    ]
    for index, config in enumerate(mutations):
        destination = tmp_path / f"runtime-{index}.env"
        with pytest.raises(RUNTIME.InstallerError, match="CONFIG_INVALID"):
            RUNTIME.render_config(config, destination)
        assert not destination.exists()


def test_config_is_atomic_private_and_contains_references_not_secret_values(tmp_path: Path) -> None:
    secret = tmp_path / "database-password"
    secret.write_text("CANARY-DO-NOT-LEAK", encoding="utf-8")
    secret.chmod(0o600)
    destination = tmp_path / "config" / "runtime.env"
    destination.parent.mkdir(mode=0o700)

    RUNTIME.render_config(safe_config(secret), destination)

    rendered = destination.read_text(encoding="utf-8")
    assert "CANARY-DO-NOT-LEAK" not in rendered
    assert f"DATABASE_PASSWORD_FILE={secret}" in rendered
    assert "LIQVERA_SOURCE_MODE=shadow" in rendered
    assert stat.S_IMODE(destination.stat().st_mode) == 0o600


@pytest.mark.parametrize("kind", ["missing", "symlink", "multilink", "public", "empty"])
def test_secret_references_fail_closed_without_leaking(
    tmp_path: Path, kind: str
) -> None:
    target = tmp_path / "secret"
    if kind != "missing":
        target.write_text("CANARY-SECRET" if kind != "empty" else "", encoding="utf-8")
        target.chmod(0o600)
    if kind == "symlink":
        link = tmp_path / "secret-link"
        link.symlink_to(target)
        target = link
    elif kind == "multilink":
        os.link(target, tmp_path / "secret-second-link")
    elif kind == "public":
        target.chmod(0o644)
    destination = tmp_path / "runtime.env"

    with pytest.raises(RUNTIME.InstallerError) as error:
        RUNTIME.render_config(safe_config(target), destination)
    assert error.value.code == "SECRET_REFERENCE_INVALID"
    assert "CANARY-SECRET" not in str(error.value)
    assert not destination.exists()


def test_state_write_is_atomic_closed_and_contains_no_secret(tmp_path: Path) -> None:
    state_path = tmp_path / "state" / "install-state.json"
    state_path.parent.mkdir(mode=0o700)
    value = {
        "schema_version": "liqvera-install-state/v1",
        "product_version": "0.0.2",
        "release_sha256": "a" * 64,
        "git_commit": "1" * 40,
        "git_tree": "2" * 40,
        "install_root": str((tmp_path / "install").resolve()),
        "compose_project": "liqvera-local",
        "linux": {"distribution": "ubuntu", "architecture": "amd64"},
        "docker": {"engine_version": "27.5.1", "compose_version": "2.32.4"},
        "ports": {"web": 3000, "gateway": 8080, "metrics": 9090},
        "last_completed_phase": "CONFIGURED",
        "last_error": None,
        "created_at": "2026-09-30T00:00:00Z",
        "updated_at": "2026-09-30T00:00:00Z",
    }
    RUNTIME.write_state_atomic(state_path, value)
    assert RUNTIME.load_state(state_path) == value
    assert stat.S_IMODE(state_path.stat().st_mode) == 0o600
    with pytest.raises(RUNTIME.InstallerError, match="CONFIG_INVALID"):
        RUNTIME.write_state_atomic(state_path, {**value, "secret": "CANARY"})
    assert "CANARY" not in state_path.read_text(encoding="utf-8")


class FakeRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []

    def __call__(self, argv: tuple[str, ...]) -> int:
        self.calls.append(argv)
        return 0


def test_process_contract_matches_reviewed_fixture() -> None:
    fixture = json.loads(PROCESS_FIXTURES.read_text(encoding="utf-8"))
    assert fixture["schema_version"] == "liqvera-installer-process-fixtures/v1"
    assert {tuple(item) for item in fixture["allowed_read_only"]} == RUNTIME.READ_ONLY_COMMANDS
    assert {
        name: tuple(command) for name, command in fixture["dependency_commands"].items()
    } == RUNTIME.DEPENDENCY_COMMANDS


def test_dependency_install_requires_exact_digest_and_never_implicit_sudo() -> None:
    runner = FakeRunner()
    command = RUNTIME.dependency_command("ubuntu")
    approval = hashlib.sha256("\0".join(command).encode()).hexdigest()

    with pytest.raises(RUNTIME.InstallerError, match="DEPENDENCY_MISSING"):
        RUNTIME.install_dependencies("ubuntu", None, runner)
    assert runner.calls == []
    with pytest.raises(RUNTIME.InstallerError, match="DEPENDENCY_MISSING"):
        RUNTIME.install_dependencies("ubuntu", "0" * 64, runner)
    assert runner.calls == []

    RUNTIME.install_dependencies("ubuntu", approval, runner)
    assert runner.calls == [command]
    assert command[:2] == ("/usr/bin/sudo", "--")
    assert all("CANARY" not in argument for argument in command)


@pytest.mark.parametrize(
    "name",
    [
        "DOCKER_HOST",
        "DOCKER_CONTEXT",
        "COMPOSE_FILE",
        "COMPOSE_PROFILES",
        "COMPOSE_PROJECT_NAME",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "NO_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
        "no_proxy",
        "BASH_ENV",
        "ENV",
    ],
)
def test_ambient_runtime_authority_is_rejected_before_process_execution(name: str) -> None:
    with pytest.raises(RUNTIME.InstallerError, match="DEPENDENCY_MISSING"):
        RUNTIME.reject_ambient_authority({name: "CANARY"})


def test_process_adapter_rejects_shell_live_and_daemon_authority() -> None:
    runner = FakeRunner()
    assert RUNTIME.run_process(("/usr/bin/docker", "version", "--format", "{{.Server.Version}}"), runner) == 0
    for argv in (
        ("/bin/sh", "-c", "true"),
        ("/usr/bin/docker", "compose", "-f", "/tmp/evil", "up"),
        ("/usr/bin/docker", "--host", "tcp://remote", "info"),
        ("/usr/bin/docker", "compose", "--profile", "live", "config"),
    ):
        with pytest.raises(RUNTIME.InstallerError, match="DEPENDENCY_MISSING"):
            RUNTIME.run_process(argv, runner)
    assert runner.calls == [
        ("/usr/bin/docker", "version", "--format", "{{.Server.Version}}")
    ]


def test_bash_entrypoint_has_closed_help_and_rejects_unknown_flags(tmp_path: Path) -> None:
    help_result = subprocess.run(
        ["bash", str(INSTALLER), "--help"],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert help_result.returncode == 0
    assert "--install-deps" in help_result.stdout
    assert "--approve-dependency-command" in help_result.stdout
    assert "--verified-release" in help_result.stdout
    unknown = subprocess.run(
        ["bash", str(INSTALLER), "--eval", "touch pwned"],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert unknown.returncode == 2
    assert not (tmp_path / "pwned").exists()
