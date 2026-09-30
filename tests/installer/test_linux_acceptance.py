from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
RUNTIME_SPEC = importlib.util.spec_from_file_location(
    "installer_acceptance_runtime", ROOT / "installer/lib/runtime.py"
)
assert RUNTIME_SPEC is not None and RUNTIME_SPEC.loader is not None
RUNTIME = importlib.util.module_from_spec(RUNTIME_SPEC)
RUNTIME_SPEC.loader.exec_module(RUNTIME)


def test_operator_docs_publish_exact_linux_safe_command_contract() -> None:
    readme = (ROOT / "README.md").read_text()
    startup = (ROOT / "docs/runbooks/startup-shutdown.md").read_text()
    observability = (ROOT / "docs/runbooks/observability.md").read_text()
    combined = "\n".join((readme, startup, observability))
    for literal in (
        "Linux-only", "Ubuntu 22.04", "Ubuntu 24.04", "Debian 12",
        "Fedora 40", "Fedora 41", "RHEL 9", "amd64", "arm64",
        "Bash 5.2", "Docker Engine 27", "Compose v2.30", "4 GiB", "2 GiB",
        "install-liqvera-0.0.2.sh", "liqvera-installer-0.0.2.zip",
        "sha256sum --check", "--install-root", "status --json",
        "logs gateway --tail 200 --since 15m", "uninstall --purge-data",
        "EXTERNAL_GRANT_REQUIRED", "payment disabled", "127.0.0.1",
    ):
        assert literal in combined
    assert "curl | bash" in combined
    assert "never" in combined.lower()


def test_installer_workflow_is_nonpublishing_claw_only_and_bounded() -> None:
    workflow = yaml.safe_load((ROOT / ".github/workflows/installer-linux.yml").read_text())
    assert workflow["permissions"] == {"contents": "read"}
    assert workflow["concurrency"]["cancel-in-progress"] is True
    assert set(workflow["jobs"]) == {"linux-contract"}
    job = workflow["jobs"]["linux-contract"]
    assert job["runs-on"] == ["self-hosted", "claw"]
    assert job["timeout-minutes"] <= 20
    rendered = str(workflow)
    assert "tests/installer" in rendered
    for forbidden in ("sudo", "--install-deps", "docker login", "gh release", "curl | bash"):
        assert forbidden not in rendered


@pytest.mark.parametrize(
    ("distribution", "version", "machine"),
    [
        ("ubuntu", "22.04", "x86_64"), ("ubuntu", "24.04", "aarch64"),
        ("debian", "12", "x86_64"), ("fedora", "40", "aarch64"),
        ("fedora", "41", "x86_64"), ("rhel", "9", "aarch64"),
    ],
)
def test_mocked_supported_linux_matrix_is_explicitly_contract_only(
    tmp_path: Path, distribution: str, version: str, machine: str,
) -> None:
    config = {
        "schema_version": "liqvera-install-config/v1", "chain_id": 31611,
        "payment_enabled": False, "source_mode": "shadow",
        "ports": {
            "web": {"host": "127.0.0.1", "port": 3000},
            "gateway": {"host": "127.0.0.1", "port": 8080},
            "metrics": {"host": "127.0.0.1", "port": 9090},
        },
        "secret_files": {},
    }
    facts = {
        "kernel": "Linux", "distribution": distribution,
        "distribution_version": version, "architecture": machine,
        "bash_version": "5.2.0", "docker_version": "27.0.0",
        "compose_version": "2.30.0", "daemon_reachable": True,
        "docker_endpoint": "unix:///var/run/docker.sock",
        "disk_bytes": 4 * 1024**3, "memory_bytes": 2 * 1024**3,
        "filesystem_type": "ext4",
        "ports_available": {"web": True, "gateway": True, "metrics": True},
    }
    result = RUNTIME.preflight(
        {"schema_version": "liqvera-preflight-request/v1",
         "install_root": str(tmp_path / "install"), "config": config},
        facts,
    )
    assert result["status"] == "PASS"
    assert not (tmp_path / "install").exists()


def test_docs_keep_clean_host_and_external_acceptance_truthful() -> None:
    notes = (ROOT / "engineering/changes/20260929-f7-live-acceptance-and-release-0-0-1-337ef5/release-notes-v0.0.2.md").read_text()
    assert "409" in notes or "installer" in notes
    assert "mocked" in notes.lower()
    assert "clean-host" in notes
    assert "NOT_RUN" in notes
    assert "21 NOT_RUN" in notes
    assert "single runner overall PASS" in notes
