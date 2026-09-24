import json
from pathlib import Path


def test_policy_is_immutable_rootless_and_default_network_none():
    p=json.loads(Path("ci/claw/sandbox-policy.json").read_text())
    assert p["authority"] == "NONE"
    assert p["image"].startswith("docker.io/") and "@sha256:" in p["image"]
    assert p["network"] == "none"
    assert p["cap_drop"] == ["ALL"]
    assert p["no_new_privileges"] is True
    assert p["read_only_rootfs"] is True
    assert p["runner_name"] == "claw-engine-runner"
    assert "/home/pall/app-stack" in p["forbidden_roots"]


def test_runner_has_closed_argv_and_no_dangerous_host_access():
    text=Path("ci/claw/run-disposable-validation.sh").read_text()
    for required in ("podman info", "--network=none", "--cap-drop=ALL", "no-new-privileges", "--read-only", "RUNNER_NAME", "timeout 900s", "--pull=never", "podman container exists"):
        assert required in text
    for forbidden in ("eval ", "source $", "/var/run/docker.sock", "/run/podman/podman.sock", "--privileged", "--network=host", "/home/pall/app-stack"):
        assert forbidden not in text
    assert "paths overlap" in text
    assert 'argv=(' in text and '"${argv[@]}"' in text and "MEE_COMMAND_MANIFEST" in text
