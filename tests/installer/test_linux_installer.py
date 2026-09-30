from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import stat
import subprocess
import sys
import threading
from dataclasses import asdict
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


def verified_release(tmp_path: Path) -> tuple[Path, Path]:
    archive_spec = importlib.util.spec_from_file_location(
        "installer_archive_fixture", ROOT / "tests/installer/test_archive_verifier.py"
    )
    assert archive_spec is not None and archive_spec.loader is not None
    archive_module = importlib.util.module_from_spec(archive_spec)
    sys.modules[archive_spec.name] = archive_module
    archive_spec.loader.exec_module(archive_module)
    archive = tmp_path / "installer.zip"
    actual_digest = archive_module.write_archive(archive)
    verifier_spec = importlib.util.spec_from_file_location(
        "installer_archive_verifier", ROOT / "scripts/verify-liqvera-installer.py"
    )
    assert verifier_spec is not None and verifier_spec.loader is not None
    verifier = importlib.util.module_from_spec(verifier_spec)
    sys.modules[verifier_spec.name] = verifier
    verifier_spec.loader.exec_module(verifier)
    release = tmp_path / "verified"
    result = verifier.verify_installer(archive, actual_digest, release)
    receipt = tmp_path / "verified-receipt.json"
    receipt.write_text(json.dumps(asdict(result)), encoding="utf-8")
    receipt.chmod(0o600)
    return release, receipt


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


def test_bash_numeric_version_accepts_real_spelling() -> None:
    assert RUNTIME._version("5.2.21(1)-release") == (5, 2, 21)


def test_json_inputs_reject_duplicate_keys() -> None:
    with pytest.raises(RUNTIME.InstallerError, match="CONFIG_INVALID"):
        RUNTIME.load_json_bytes(b'{"payment_enabled":true,"payment_enabled":false}', "CONFIG_INVALID")


@pytest.mark.parametrize("name", ["line\nfeed", "${INTERPOLATION}", "$NAME", "$(command)", "`command`", "control\x7f"])
def test_secret_reference_rejects_control_or_interpolation(tmp_path: Path, name: str) -> None:
    secret = tmp_path / name
    secret.write_text("x")
    secret.chmod(0o600)
    with pytest.raises(RUNTIME.InstallerError, match="SECRET_REFERENCE_INVALID"):
        RUNTIME.render_config(safe_config(secret), tmp_path / "runtime.env")


def test_verified_release_rejects_wrong_digest_and_mutated_member(tmp_path: Path) -> None:
    release, receipt = verified_release(tmp_path)
    receipt_value = json.loads(receipt.read_text())
    expected = receipt_value["archive_sha256"]
    inventory = receipt_value["inventory_sha256"]
    with pytest.raises(RUNTIME.InstallerError, match="RELEASE_DIGEST_MISMATCH"):
        RUNTIME.validate_verified_release(release, receipt, "b" * 64, inventory)
    (release / "install.sh").write_text("changed")
    with pytest.raises(RUNTIME.InstallerError, match="ARCHIVE_INVALID"):
        RUNTIME.validate_verified_release(release, receipt, expected, inventory)


def test_verified_receipt_rejects_member_plus_checksum_rewrite(tmp_path: Path) -> None:
    release, receipt = verified_release(tmp_path)
    expected = json.loads(receipt.read_text())["archive_sha256"]
    member = release / "LICENSE-NOTICE.md"
    member.write_bytes(b"coordinated replacement\n")
    lines = (release / "SHA256SUMS").read_text().splitlines()
    replacement = hashlib.sha256(member.read_bytes()).hexdigest()
    (release / "SHA256SUMS").write_text("\n".join(
        f"{replacement}  LICENSE-NOTICE.md" if line.endswith("  LICENSE-NOTICE.md") else line
        for line in lines
    ) + "\n")
    with pytest.raises(RUNTIME.InstallerError, match="ARCHIVE_INVALID"):
        RUNTIME.validate_verified_release(release, receipt, expected, json.loads(receipt.read_text())["inventory_sha256"])


def test_independent_inventory_authority_rejects_receipt_and_content_rewrite(tmp_path: Path) -> None:
    release, receipt = verified_release(tmp_path)
    original_receipt = json.loads(receipt.read_text())
    member = release / "LICENSE-NOTICE.md"
    member.write_bytes(b"coordinated replacement\n")
    lines = (release / "SHA256SUMS").read_text().splitlines()
    replacement = hashlib.sha256(member.read_bytes()).hexdigest()
    sums = "\n".join(
        f"{replacement}  LICENSE-NOTICE.md" if line.endswith("  LICENSE-NOTICE.md") else line
        for line in lines
    ) + "\n"
    (release / "SHA256SUMS").write_text(sums)
    changed_receipt = {**original_receipt, "inventory_sha256": hashlib.sha256(sums.encode()).hexdigest()}
    receipt.write_text(json.dumps(changed_receipt))
    with pytest.raises(RUNTIME.InstallerError, match="ARCHIVE_INVALID"):
        RUNTIME.validate_verified_release(
            release, receipt, original_receipt["archive_sha256"], original_receipt["inventory_sha256"]
        )


def test_descriptor_bound_root_rejects_path_replacement(tmp_path: Path) -> None:
    root = tmp_path / "install"
    handle = RUNTIME.InstallRoot.create(root)
    outside = tmp_path / "outside"
    outside.mkdir()
    moved = tmp_path / "moved"
    root.rename(moved)
    root.symlink_to(outside, target_is_directory=True)
    try:
        with pytest.raises(RUNTIME.InstallerError, match="UNSAFE_INSTALL_ROOT"):
            handle.assert_selected_path()
        handle.write("config/runtime.env", b"safe\n")
        assert not (outside / "config/runtime.env").exists()
    finally:
        handle.close()


def test_descriptor_traversal_rejects_ancestor_exchange_before_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    selected = tmp_path / "selected"
    (selected / "private").mkdir(parents=True)
    outside = tmp_path / "outside"
    (outside / "private").mkdir(parents=True)
    moved = tmp_path / "moved"
    original_open = RUNTIME.os.open
    exchanged = False

    def raced_open(path: object, *args: object, **kwargs: object) -> int:
        nonlocal exchanged
        if path == "selected" and not exchanged:
            exchanged = True
            selected.rename(moved)
            selected.symlink_to(outside, target_is_directory=True)
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(RUNTIME.os, "open", raced_open)
    with pytest.raises((RUNTIME.InstallerError, OSError)):
        RUNTIME.InstallRoot.create(selected / "private/install")
    assert not (outside / "private/install").exists()


def test_existing_install_is_idempotent_and_conflicts_fail_without_overwrite(tmp_path: Path) -> None:
    root = tmp_path / "install"
    root.mkdir(mode=0o700)
    (root / "config").mkdir()
    (root / "state").mkdir()
    config_bytes = b"stable\n"
    (root / "config/runtime.env").write_bytes(config_bytes)
    state = {
        "schema_version": "liqvera-install-state/v1", "product_version": "0.0.2",
        "release_sha256": "a" * 64, "git_commit": "1" * 40, "git_tree": "2" * 40,
        "install_root": str(root.resolve()), "compose_project": "liqvera-aaaaaaaaaaaa",
        "linux": {"distribution": "ubuntu", "architecture": "amd64"},
        "docker": {"engine_version": "27.5.1", "compose_version": "2.32.4"},
        "ports": {"web": 3000, "gateway": 8080, "metrics": 9090},
        "last_completed_phase": "HEALTHY", "last_error": None,
        "created_at": "2026-09-29T00:00:00Z", "updated_at": "2026-09-29T00:00:00Z",
    }
    (root / "state/install-state.json").write_text(json.dumps(state))
    assert RUNTIME.reconcile_existing(root, state, config_bytes) == state
    assert (root / "config/runtime.env").read_bytes() == config_bytes
    with pytest.raises(RUNTIME.InstallerError, match="RELEASE_DIGEST_MISMATCH"):
        RUNTIME.reconcile_existing(root, {**state, "release_sha256": "b" * 64}, config_bytes)
    assert json.loads((root / "state/install-state.json").read_text())["release_sha256"] == "a" * 64


def cli_args(release: Path, receipt: Path, config: Path, root: Path, *extra: str) -> list[str]:
    receipt_value = json.loads(receipt.read_text())
    digest = receipt_value["archive_sha256"]
    return [
        "--verified-release", str(release), "--verified-receipt", str(receipt),
        "--sha256", digest, "--inventory-sha256", receipt_value["inventory_sha256"],
        "--install-dir", str(root), "--config", str(config),
        "--bash-version", "5.2.21", *extra,
    ]


def test_direct_runtime_requires_independent_inventory_authority(tmp_path: Path) -> None:
    release, receipt = verified_release(tmp_path)
    config = tmp_path / "config.json"
    config.write_text(json.dumps(safe_config()))
    arguments = cli_args(release, receipt, config, tmp_path / "install")
    index = arguments.index("--inventory-sha256")
    del arguments[index:index + 2]
    completed = subprocess.run(
        [sys.executable, str(RUNTIME_PATH), *arguments], check=False,
        capture_output=True, text=True, env={"PATH": "/usr/bin:/bin"},
    )
    assert completed.returncode == 2
    assert "--inventory-sha256" in completed.stderr
    assert not (tmp_path / "install").exists()


def clear_authority(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in RUNTIME.FORBIDDEN_AMBIENT_ENV:
        monkeypatch.delenv(name, raising=False)


def test_main_validates_everything_before_write_and_preserves_matching_install(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    clear_authority(monkeypatch)
    release, receipt = verified_release(tmp_path)
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(safe_config()))
    root = tmp_path / "install"
    monkeypatch.setattr(RUNTIME, "_collect_system_facts", lambda *_: facts())

    assert RUNTIME.main(cli_args(release, receipt, config_path, root)) == 0
    first_state = (root / "state/install-state.json").read_bytes()
    first_config_stat = (root / "config/runtime.env").stat()
    assert "LIQVERA_ENGINE_COMMIT=" + "1" * 40 in (root / "config/runtime.env").read_text()
    assert json.loads(capsys.readouterr().out)["status"] == "CONFIGURED"

    assert RUNTIME.main(cli_args(release, receipt, config_path, root)) == 0
    assert (root / "state/install-state.json").read_bytes() == first_state
    assert (root / "config/runtime.env").stat().st_ino == first_config_stat.st_ino


def test_main_invalid_secret_or_manifest_leaves_no_install_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clear_authority(monkeypatch)
    release, receipt = verified_release(tmp_path)
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(safe_config(tmp_path / "missing-secret")))
    root = tmp_path / "install"
    monkeypatch.setattr(RUNTIME, "_collect_system_facts", lambda *_: facts())
    assert RUNTIME.main(cli_args(release, receipt, config_path, root)) == 2
    assert not root.exists()

    config_path.write_text(json.dumps(safe_config()))
    (release / "manifests/release-manifest.json").write_text("{}")
    assert RUNTIME.main(cli_args(release, receipt, config_path, root)) == 2
    assert not root.exists()


def test_main_missing_docker_only_runs_exact_explicit_approved_dependency(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clear_authority(monkeypatch)
    release, receipt = verified_release(tmp_path)
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(safe_config()))
    root = tmp_path / "install"
    observations = [facts(docker_version="0.0.0", compose_version="0.0.0", daemon_reachable=False,
                          installable_dependency_missing=True), facts()]
    monkeypatch.setattr(RUNTIME, "_collect_system_facts", lambda *_: observations.pop(0))
    calls: list[tuple[str, ...]] = []
    monkeypatch.setattr(RUNTIME, "_system_runner", lambda argv: calls.append(argv) or 0)
    command = RUNTIME.dependency_command("ubuntu")
    approval = hashlib.sha256("\0".join(command).encode()).hexdigest()
    assert RUNTIME.main(cli_args(release, receipt, config_path, root, "--install-deps", "--non-interactive",
                                 "--approve-dependency-command", approval)) == 0
    assert calls == [command]


def test_main_interactive_dependency_requires_exact_typed_digest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    clear_authority(monkeypatch)
    release, receipt = verified_release(tmp_path)
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(safe_config()))
    observations = [facts(docker_version="0.0.0", compose_version="0.0.0", daemon_reachable=False,
                          installable_dependency_missing=True), facts()]
    monkeypatch.setattr(RUNTIME, "_collect_system_facts", lambda *_: observations.pop(0))
    calls: list[tuple[str, ...]] = []
    monkeypatch.setattr(RUNTIME, "_system_runner", lambda argv: calls.append(argv) or 0)
    command = RUNTIME.dependency_command("ubuntu")
    approval = hashlib.sha256("\0".join(command).encode()).hexdigest()
    monkeypatch.setattr(sys, "stdin", io.StringIO(approval + "\n"))

    assert RUNTIME.main(cli_args(release, receipt, config_path, tmp_path / "install", "--install-deps")) == 0
    assert calls == [command]
    captured = capsys.readouterr()
    assert json.loads(captured.out)["status"] == "CONFIGURED"
    diagnostic = captured.err
    assert "DEPENDENCY_PREVIEW: /usr/bin/sudo -- /usr/bin/apt-get install" in diagnostic
    assert approval in diagnostic


def test_main_resource_failure_never_runs_dependency_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clear_authority(monkeypatch)
    release, receipt = verified_release(tmp_path)
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(safe_config()))
    monkeypatch.setattr(RUNTIME, "_collect_system_facts", lambda *_: facts(disk_bytes=1))
    calls: list[tuple[str, ...]] = []
    monkeypatch.setattr(RUNTIME, "_system_runner", lambda argv: calls.append(argv) or 0)
    assert RUNTIME.main(cli_args(release, receipt, config_path, tmp_path / "install", "--install-deps")) == 2
    assert calls == []


@pytest.mark.parametrize(
    "mutation",
    [
        {"distribution_version": "20.04"},
        {"architecture": "i686"},
        {"bash_version": "5.1.99"},
        {"disk_bytes": 1},
        {"memory_bytes": 1},
    ],
)
def test_missing_docker_never_crosses_an_independent_preflight_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: dict[str, object]
) -> None:
    clear_authority(monkeypatch)
    release, receipt = verified_release(tmp_path)
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(safe_config()))
    combined = facts(
        docker_version="0.0.0", compose_version="0.0.0", daemon_reachable=False,
        installable_dependency_missing=True, **mutation,
    )
    monkeypatch.setattr(RUNTIME, "_collect_system_facts", lambda *_: combined)
    calls: list[tuple[str, ...]] = []
    monkeypatch.setattr(RUNTIME, "_system_runner", lambda argv: calls.append(argv) or 0)
    command = RUNTIME.dependency_command("ubuntu")
    approval = hashlib.sha256("\0".join(command).encode()).hexdigest()
    result = RUNTIME.main(cli_args(
        release, receipt, config_path, tmp_path / "install", "--install-deps",
        "--non-interactive", "--approve-dependency-command", approval,
    ))
    assert result == 2
    assert calls == []


def test_main_publication_failure_removes_invocation_owned_partial_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clear_authority(monkeypatch)
    release, receipt = verified_release(tmp_path)
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(safe_config()))
    root = tmp_path / "install"
    monkeypatch.setattr(RUNTIME, "_collect_system_facts", lambda *_: facts())
    original_write = RUNTIME.InstallRoot.write
    calls = 0

    def fail_second_write(handle: object, relative: str, data: bytes) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("CANARY-WRITE-FAILURE")
        original_write(handle, relative, data)

    monkeypatch.setattr(RUNTIME.InstallRoot, "write", fail_second_write)
    assert RUNTIME.main(cli_args(release, receipt, config_path, root)) == 2
    assert not root.exists()


def test_full_reconciliation_and_publication_are_serialized(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clear_authority(monkeypatch)
    release, receipt = verified_release(tmp_path)
    secret = tmp_path / "database-password"
    secret.write_text("CANARY")
    secret.chmod(0o600)
    configs = [tmp_path / "config-a.json", tmp_path / "config-b.json"]
    configs[0].write_text(json.dumps(safe_config()))
    configs[1].write_text(json.dumps(safe_config(secret)))
    root = tmp_path / "install"
    monkeypatch.setattr(RUNTIME, "_collect_system_facts", lambda *_: facts())
    barrier = threading.Barrier(2)
    results: list[int] = []

    def invoke(config_path: Path) -> None:
        barrier.wait()
        results.append(RUNTIME.main(cli_args(release, receipt, config_path, root)))

    threads = [threading.Thread(target=invoke, args=(path,)) for path in configs]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)
        assert not thread.is_alive()
    assert sorted(results) == [0, 2]
    rendered = (root / "config/runtime.env").read_bytes()
    assert rendered in {
        RUNTIME.render_config_bytes(safe_config(), "1" * 40),
        RUNTIME.render_config_bytes(safe_config(secret), "1" * 40),
    }
    assert json.loads((root / "state/install-state.json").read_text())["last_completed_phase"] == "CONFIGURED"


def test_process_adapters_suppress_children_and_close_timeout(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[dict[str, object]] = []

    def quiet(*_args: object, **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        calls.append(kwargs)
        return subprocess.CompletedProcess([], 1, b"CANARY", b"CANARY")

    monkeypatch.setattr(RUNTIME.subprocess, "run", quiet)
    assert RUNTIME._system_runner(next(iter(RUNTIME.READ_ONLY_COMMANDS))) == 1
    assert calls[0]["stdout"] is subprocess.DEVNULL
    assert calls[0]["stderr"] is subprocess.DEVNULL

    def timeout(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[bytes]:
        raise subprocess.TimeoutExpired("docker", 10, output=b"CANARY", stderr=b"CANARY")

    monkeypatch.setattr(RUNTIME.subprocess, "run", timeout)
    assert RUNTIME._command_output(next(iter(RUNTIME.READ_ONLY_COMMANDS))) is None
    assert RUNTIME._system_runner(next(iter(RUNTIME.READ_ONLY_COMMANDS))) == 127


def test_process_adapter_rejects_shell_live_and_daemon_authority() -> None:
    runner = FakeRunner()
    allowed = ("/usr/bin/docker", "--host", "unix:///var/run/docker.sock", "version", "--format", "{{.Server.Version}}")
    assert RUNTIME.run_process(allowed, runner) == 0
    for argv in (
        ("/bin/sh", "-c", "true"),
        ("/usr/bin/docker", "compose", "-f", "/tmp/evil", "up"),
        ("/usr/bin/docker", "--host", "tcp://remote", "info"),
        ("/usr/bin/docker", "compose", "--profile", "live", "config"),
    ):
        with pytest.raises(RUNTIME.InstallerError, match="DEPENDENCY_MISSING"):
            RUNTIME.run_process(argv, runner)
    assert runner.calls == [
        allowed
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

    startup = tmp_path / "startup.sh"
    startup.write_text("printf 'CANARY-STARTUP\\n'\n")
    version = subprocess.run(
        [str(INSTALLER), "--version"], cwd=tmp_path, check=False,
        capture_output=True, text=True, env={**os.environ, "BASH_ENV": str(startup)},
    )
    assert version.returncode == 0
    assert version.stdout == "0.0.2\n"
    assert "CANARY" not in version.stderr
