from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess

import pytest

from scripts.claw_host_deployment_install import (
    D0Error,
    D0Journal,
    FakeD0Backend,
    RealD0Backend,
    execute,
    recover,
)


SOURCE_IDENTITY = {"controller_sha": "a" * 40, "controller_tree": "b" * 40}


def test_every_d0_failure_restores_exact_fake_baseline(tmp_path: Path) -> None:
    for fail_after in range(1, len(FakeD0Backend.OPERATIONS) + 1):
        journal = D0Journal(tmp_path / f"journal-{fail_after}.json")
        backend = FakeD0Backend(fail_after=fail_after)
        with pytest.raises(D0Error, match="INJECTED"):
            execute(backend, journal)
        assert backend.state == {}
        assert journal.value["phase"] == "ROLLED_BACK"
        assert journal.value["status"] == "ROLLED_BACK"


def test_inverse_failure_is_aggregated_and_recovery_evidence_is_retained(tmp_path: Path) -> None:
    journal = D0Journal(tmp_path / "journal.json")
    backend = FakeD0Backend(fail_after=3, inverse_failures={"install_verifier", "create_state"})
    with pytest.raises(D0Error, match="INJECTED"):
        execute(backend, journal)
    assert journal.value["phase"] == "ROLLBACK_BLOCKED"
    assert journal.value["status"] == "OPEN"
    assert {item["operation"] for item in journal.value["failures"]} == {
        "install_verifier", "create_state",
    }


def test_open_journal_recovers_in_reverse_order_with_durable_snapshots(tmp_path: Path) -> None:
    path = tmp_path / "journal.json"
    journal = D0Journal(path)
    backend = FakeD0Backend()
    for operation in FakeD0Backend.OPERATIONS[:4]:
        snapshot = backend.snapshot(operation)
        journal.applying(operation, snapshot)
        backend.apply(operation)
        journal.applied(operation)

    resumed = D0Journal.resume(path)
    fresh = FakeD0Backend()
    fresh.state = dict(backend.state)
    recover(fresh, resumed)
    assert fresh.state == {}
    assert resumed.value["status"] == "ROLLED_BACK"


def _source_fixture(tmp_path: Path) -> tuple[Path, Path]:
    source = tmp_path / "source"
    source.mkdir()
    artifacts = []
    for index, (operation, target, mode) in enumerate(RealD0Backend.FILE_TARGETS):
        relative = f"payload/{index}-{operation}"
        item = source / relative
        item.parent.mkdir(parents=True, exist_ok=True)
        item.write_bytes(f"payload:{operation}\n".encode())
        artifacts.append({
            "operation": operation,
            "source": relative,
            "target": target,
            "mode": mode,
            "sha256": hashlib.sha256(item.read_bytes()).hexdigest(),
        })
    manifest = {
        "schema_version": "claw-host-deployment-install-manifest-v1",
        "authority": "NONE",
        "artifacts": artifacts,
    }
    manifest_path = source / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n")
    return source, manifest_path


def _fake_host_root(tmp_path: Path) -> Path:
    root = tmp_path / "root"
    for base in RealD0Backend.BASE_DIRS:
        root.joinpath(*Path(base).parts[1:]).mkdir(parents=True, exist_ok=True)
    return root


def test_real_backend_installs_exact_bytes_modes_and_rolls_back(tmp_path: Path) -> None:
    source, manifest = _source_fixture(tmp_path)
    root = _fake_host_root(tmp_path)
    backend = RealD0Backend(source=source, manifest=manifest, root=root, **SOURCE_IDENTITY)
    journal = D0Journal(tmp_path / "journal.json")

    execute(backend, journal)
    assert journal.value["phase"] == "COMMITTED"
    receipt = json.loads((root / "var/lib/mee-claw-host-deploy/D0-VERIFIED.json").read_text())
    schema = json.loads(Path("schemas/claw-host-deployment-d0-receipt-v1.schema.json").read_text())
    assert set(receipt) == set(schema["required"]) == set(schema["properties"])
    assert receipt["authority"] == "NONE" and receipt["not_host_receipt"] is True
    assert receipt["controller_sha"] == SOURCE_IDENTITY["controller_sha"]
    for _, target, mode in RealD0Backend.FILE_TARGETS:
        installed = root.joinpath(*Path(target).parts[1:])
        assert installed.is_file()
        if os.name == "posix":
            assert installed.stat().st_mode & 0o777 == mode

    rollback_journal = D0Journal.resume_terminal(tmp_path / "journal.json")
    recover(RealD0Backend(source=source, manifest=manifest, root=root, **SOURCE_IDENTITY), rollback_journal)
    for _, target, _ in RealD0Backend.FILE_TARGETS:
        assert not root.joinpath(*Path(target).parts[1:]).exists()


@pytest.mark.parametrize("unsafe", ["symlink", "hardlink", "digest"])
def test_real_backend_rejects_unstable_or_mismatched_source(tmp_path: Path, unsafe: str) -> None:
    source, manifest = _source_fixture(tmp_path)
    first = source / json.loads(manifest.read_text())["artifacts"][0]["source"]
    if unsafe == "symlink":
        target = source / "replacement"
        target.write_bytes(first.read_bytes())
        first.unlink()
        first.symlink_to(target)
    elif unsafe == "hardlink":
        (source / "second-link").hardlink_to(first)
    else:
        first.write_bytes(b"changed")
    with pytest.raises(D0Error):
        RealD0Backend(source=source, manifest=manifest, root=_fake_host_root(tmp_path), **SOURCE_IDENTITY)


def test_repository_install_manifest_binds_every_installed_byte(tmp_path: Path) -> None:
    backend = RealD0Backend(
        source=Path.cwd(),
        manifest=Path("ci/claw/host-deployment-controller-manifest.json"),
        root=_fake_host_root(tmp_path),
        **SOURCE_IDENTITY,
    )
    assert set(backend.artifacts) == {item[0] for item in RealD0Backend.FILE_TARGETS}
    required = {
        "install_inventory_collector", "install_inventory_verifier",
        "install_oci_library", "install_oci_verifier", "install_oci_builder_source",
        "install_oci_independent_verifier_source", "install_oci_schema", "install_policy",
        "install_closure", "install_oci_approval",
    }
    assert required <= set(backend.artifacts)
    for name in required:
        assert backend.artifacts[name]["bytes"]


def test_preexisting_created_directory_file_collision_is_rejected_before_wal(tmp_path: Path) -> None:
    root = _fake_host_root(tmp_path)
    collision = root / "usr/local/libexec/schemas"
    collision.write_bytes(b"foreign\n")
    with pytest.raises(D0Error, match="CREATED_DIRECTORY_REQUIRED"):
        RealD0Backend(
            source=Path.cwd(),
            manifest=Path("ci/claw/host-deployment-controller-manifest.json"),
            root=root,
            **SOURCE_IDENTITY,
        )
    assert collision.read_bytes() == b"foreign\n"


def test_preexisting_target_bytes_are_restored_after_committed_rollback(tmp_path: Path) -> None:
    source, manifest = _source_fixture(tmp_path)
    root = _fake_host_root(tmp_path)
    target = root.joinpath(*Path(RealD0Backend.FILE_TARGETS[0][1]).parts[1:])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"baseline\n")
    journal_path = tmp_path / "journal.json"
    execute(RealD0Backend(source=source, manifest=manifest, root=root, **SOURCE_IDENTITY), D0Journal(journal_path))
    recover(
        RealD0Backend(source=source, manifest=manifest, root=root, **SOURCE_IDENTITY),
        D0Journal.resume_terminal(journal_path),
    )
    assert target.read_bytes() == b"baseline\n"


def test_manifest_duplicate_keys_fail_closed(tmp_path: Path) -> None:
    source, manifest = _source_fixture(tmp_path)
    manifest.write_text('{"schema_version":"x","schema_version":"y"}')
    with pytest.raises(D0Error, match="DUPLICATE_KEY"):
        RealD0Backend(source=source, manifest=manifest, root=_fake_host_root(tmp_path), **SOURCE_IDENTITY)


def test_installed_units_keep_root_only_owner_boundary_closed() -> None:
    socket = Path("ci/claw/systemd/mee-claw-host-deploy.socket").read_text()
    service = Path("ci/claw/systemd/mee-claw-host-deploy@.service").read_text()
    reconciler = Path("ci/claw/systemd/mee-claw-host-deploy-reconcile.service").read_text()
    timer = Path("ci/claw/systemd/mee-claw-host-deploy-reconcile.timer").read_text()

    assert not Path("ci/claw/sudoers/mee-claw-host-deploy").exists()
    assert "install_sudoers" not in FakeD0Backend.OPERATIONS
    assert all(target != "/etc/sudoers.d/mee-claw-host-deploy" for _, target, _ in RealD0Backend.FILE_TARGETS)
    assert "ListenStream=/run/mee-claw-host-deploy/control.sock" in socket
    assert "SocketUser=root" in socket and "SocketGroup=root" in socket
    assert "SocketMode=0600" in socket and "claw-engine-runner" not in socket
    client = Path("scripts/claw_host_deployment_client.py").read_text()
    assert "stat.S_IMODE(info.st_mode) != 0o600" in client
    assert 'sys.path.insert(0, "/usr/local/libexec/mee-claw-host-deploy-lib")' in client
    assert "from scripts.claw_host_deployment_controller" not in client
    assert "StandardInput=socket" in service
    assert "NoNewPrivileges=true" in service
    for unit in (service, reconciler):
        assert "ProtectSystem=false" in unit
        assert "ProtectHome=tmpfs" in unit
        assert "BindPaths=/home/pall/actions-runner-engine" in unit
        assert "/home/pall/app-stack" not in unit
    assert "TimeoutStartSec=30min" in service
    assert "TimeoutStartSec=15min" in reconciler
    assert "Persistent=true" in timer


def test_installer_shell_is_root_only_and_never_grants_begin_to_pall() -> None:
    source = Path("ci/claw/install-host-deployment-controller.sh").read_text()
    assert 'test "$(id -u)" -eq 0' in source
    assert "sudo" not in source
    assert "github-token" in source
    assert "apply)" in source and "resume|rollback)" in source


def _installer_shell_harness(tmp_path: Path) -> tuple[Path, dict[str, str]]:
    """Run the checked-in argument gate without allowing an installer mutation."""
    source = Path("ci/claw/install-host-deployment-controller.sh").read_text()
    harness = tmp_path / "install-host-deployment-controller.sh"
    assert source.count("/usr/bin/python3.14") == 2
    harness.write_text(source.replace("/usr/bin/python3.14", '"$D0_TEST_PYTHON"'))
    harness.chmod(0o755)

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_id = fake_bin / "id"
    fake_id.write_text("#!/bin/sh\n[ \"$1\" = -u ] && echo 0\n")
    fake_id.chmod(0o755)
    fake_python = tmp_path / "python3.14"
    fake_python.write_text("#!/bin/sh\nprintf '%s\\n' \"$*\" >> \"$D0_TEST_LOG\"\n")
    fake_python.chmod(0o755)
    log = tmp_path / "python.log"
    env = {
        **os.environ,
        "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
        "D0_TEST_PYTHON": str(fake_python),
        "D0_TEST_LOG": str(log),
    }
    return harness, env


@pytest.mark.parametrize("mode", ["resume", "rollback"])
def test_installer_shell_recovery_needs_no_expiring_github_approval(
    tmp_path: Path, mode: str
) -> None:
    harness, env = _installer_shell_harness(tmp_path)
    source = Path.cwd()
    identity = [
        str(source),
        subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], text=True).strip(),
    ]

    result = subprocess.run(["bash", str(harness), *identity, mode], env=env, text=True, capture_output=True)

    assert result.returncode == 0, result.stderr
    assert f"--mode {mode}" in (tmp_path / "python.log").read_text()


def test_installer_shell_apply_rejects_missing_approval_and_extra_recovery_args(tmp_path: Path) -> None:
    harness, env = _installer_shell_harness(tmp_path)
    source = Path.cwd()
    identity = [
        str(source),
        subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], text=True).strip(),
    ]

    missing_apply = subprocess.run(
        ["bash", str(harness), *identity, "apply"], env=env, text=True, capture_output=True
    )
    extra_recovery = subprocess.run(
        ["bash", str(harness), *identity, "resume", "unexpected"], env=env, text=True, capture_output=True
    )
    unknown_mode = subprocess.run(
        ["bash", str(harness), *identity, "replay"], env=env, text=True, capture_output=True
    )
    wrong_identity = subprocess.run(
        ["bash", str(harness), str(source), "0" * 40, identity[2], "resume"],
        env=env,
        text=True,
        capture_output=True,
    )

    assert missing_apply.returncode != 0
    assert "approval" in missing_apply.stderr
    assert extra_recovery.returncode != 0
    assert "unexpected-argument-count" in extra_recovery.stderr
    assert unknown_mode.returncode != 0
    assert "unknown-mode" in unknown_mode.stderr
    assert wrong_identity.returncode != 0
    assert not (tmp_path / "python.log").exists()
