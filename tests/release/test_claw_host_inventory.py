import base64
import hashlib
import json
from pathlib import Path
import sys

import pytest

import scripts.collect_claw_host_inventory as collector
import scripts.verify_claw_host_inventory as verifier
from scripts.collect_claw_host_inventory import build_observation, canonical_bytes
from scripts.verify_claw_host_inventory import emit_log_envelope, load_closed_json, verify_observation


ROOT = Path(__file__).resolve().parents[2]
HEAD = "5a8f85d344e066f85d54413ee0e7521713e3845d"
TREE = "18b70a5c474ce23f1721b2ae904564411cd08c80"


def _policy() -> dict:
    return json.loads((ROOT / "ci/claw/host-bootstrap-policy.json").read_text())


def _facts() -> dict:
    policy = _policy()
    engine = {
        "unit": policy["engine_service"],
        "load_state": "loaded",
        "active_state": "active",
        "sub_state": "running",
        "fragment_path": "/etc/systemd/system/" + policy["engine_service"],
        "user": "pall",
        "group": "pall",
        "main_pid": 1234,
        "exec_start_path_sha256": hashlib.sha256(
            f'{policy["runner_tree"]}/runsvc.sh'.encode()
        ).hexdigest(),
        "working_directory": policy["runner_tree"],
    }
    app = {
        "unit": policy["app_service"],
        "load_state": "loaded",
        "active_state": "active",
        "sub_state": "running",
        "fragment_path": "/etc/systemd/system/" + policy["app_service"],
        "user": "pall",
        "group": "pall",
        "main_pid": 5678,
        "exec_start_path_sha256": hashlib.sha256(
            f'{policy["app_working_directory"]}/runsvc.sh'.encode()
        ).hexdigest(),
        "working_directory": policy["app_working_directory"],
    }
    path = lambda value, inode: {
        "path": value,
        "realpath": value,
        "kind": "directory",
        "uid": 1000,
        "gid": 1000,
        "mode": "0750",
        "device": 8,
        "inode": inode,
        "link_count": 2,
    }
    return {
        "os": {"id": "ubuntu", "version_id": "24.04", "architecture": "x86_64", "kernel": "6.8.0"},
        "cgroup_v2": True,
        "engine": engine,
        "app": app,
        "paths": [path(policy["runner_tree"], 11), {"path": policy["runner_home"], "realpath": "", "kind": "missing", "uid": None, "gid": None, "mode": None, "device": None, "inode": None, "link_count": None}, path(policy["app_working_directory"], 13)],
        "target_identity": {"user_present": False, "group_present": False, "uid": None, "gid": None, "uid_occupant": None, "gid_occupant": None},
        "subids": {"subuid_target": [], "subgid_target": [], "subuid_overlaps": [], "subgid_overlaps": []},
        "packages": [{"name": item["name"], "status": "absent", "version": None, "architecture": None, "selection": None} for item in json.loads((ROOT / policy["package_closure"]).read_text())["packages"]],
        "podman": {"present": False, "version": None},
    }


def _identity() -> dict:
    return {
        "repository": "Dimkox/multi-exchange-engine",
        "controller_sha": HEAD,
        "controller_tree": TREE,
        "collection_mode": "DIRECT_CLAW",
        "collector_path": "scripts/collect_claw_host_inventory.py",
        "collector_sha256": "a" * 64,
        "collection_id": "1" * 32,
        "runner_name": "claw-engine-runner",
        "observed_at": "2026-08-12T19:00:00Z",
    }


def test_closed_observation_binds_policy_closure_host_and_run() -> None:
    policy_path = ROOT / "ci/claw/host-bootstrap-policy.json"
    closure_path = ROOT / "ci/claw/host-package-closure.json"
    value = build_observation(policy_path, closure_path, _facts(), _identity())

    assert verify_observation(value, policy_path, closure_path, _identity()) is value
    assert value["authority"] == "NONE"
    assert value["status"] == "HOST_INVENTORY_OBSERVED"
    assert value["not_host_receipt"] is True
    assert value["preflight_blockers"] == []
    assert value["policy_sha256"] == hashlib.sha256(policy_path.read_bytes()).hexdigest()
    assert value["package_closure_sha256"] == hashlib.sha256(closure_path.read_bytes()).hexdigest()
    unsigned = {key: item for key, item in value.items() if key != "inventory_payload_sha256"}
    assert value["inventory_payload_sha256"] == hashlib.sha256(canonical_bytes(unsigned)).hexdigest()


@pytest.mark.parametrize(
    "mutation,error",
    [
        (lambda value: value.update(authority="HOST"), "INVENTORY_AUTHORITY"),
        (lambda value: value["engine"].update(main_pid=0), "ENGINE_PROJECTION"),
        (lambda value: value["engine"].update(exec_start="--registration-token hidden"), "SECRET_FIELD|ENGINE_PROJECTION"),
        (lambda value: value["engine"].update(exec_start_path_sha256="0" * 64), "ENGINE_PROJECTION"),
        (lambda value: value["app"].update(active_state="inactive"), "APP_CANARY"),
        (lambda value: value["paths"][0].update(realpath="/home/pall/app-stack"), "PATH_PROJECTION"),
        (lambda value: value["packages"][0].update(status="installed"), "PACKAGE_BASELINE|PREFLIGHT_BLOCKERS"),
        (lambda value: value["subids"]["subuid_overlaps"].append({"name": "pall", "start": 165536, "count": 65536}), "PREFLIGHT_BLOCKERS"),
        (lambda value: value["target_identity"].update(uid_occupant="other-user"), "TARGET_IDENTITY"),
        (lambda value: value.update(extra=True), "INVENTORY_FIELDS"),
    ],
)
def test_inventory_mutations_fail_closed(mutation, error) -> None:
    policy_path = ROOT / "ci/claw/host-bootstrap-policy.json"
    closure_path = ROOT / "ci/claw/host-package-closure.json"
    value = build_observation(policy_path, closure_path, _facts(), _identity())
    mutation(value)
    with pytest.raises(ValueError, match=error):
        verify_observation(value, policy_path, closure_path, _identity())


def test_runner_home_must_be_absent_before_identity_creation() -> None:
    policy_path = ROOT / "ci/claw/host-bootstrap-policy.json"
    closure_path = ROOT / "ci/claw/host-package-closure.json"
    value = build_observation(policy_path, closure_path, _facts(), _identity())
    assert verify_observation(value, policy_path, closure_path, _identity()) is value
    value["paths"][1] = {**value["paths"][0], "path": _policy()["runner_home"], "realpath": _policy()["runner_home"]}
    with pytest.raises(ValueError, match="PATH_PROJECTION"):
        verify_observation(value, policy_path, closure_path, _identity())


def test_observation_reports_policy_blockers_instead_of_hiding_host_facts() -> None:
    policy_path = ROOT / "ci/claw/host-bootstrap-policy.json"
    closure_path = ROOT / "ci/claw/host-package-closure.json"
    facts = _facts()
    facts["subids"]["subuid_overlaps"] = [
        {"name": "pall", "start": 165536, "count": 65536}
    ]
    facts["packages"][0] = {
        "name": facts["packages"][0]["name"],
        "status": "installed",
        "version": "1.0",
        "architecture": "amd64",
        "selection": "ii ",
    }
    facts["podman"] = {"present": True, "version": None}

    value = build_observation(policy_path, closure_path, facts, _identity())

    assert verify_observation(value, policy_path, closure_path, _identity()) is value
    assert value["preflight_blockers"] == [
        "PACKAGE_BASELINE_PRESENT",
        "PODMAN_ALREADY_PRESENT",
        "SUBID_RANGE_OVERLAP",
    ]


def test_verifier_derives_blockers_independently_from_collector(monkeypatch) -> None:
    policy_path = ROOT / "ci/claw/host-bootstrap-policy.json"
    closure_path = ROOT / "ci/claw/host-package-closure.json"
    monkeypatch.setattr(
        collector,
        "preflight_blockers",
        lambda _facts: ["PODMAN_ALREADY_PRESENT"],
    )
    value = build_observation(policy_path, closure_path, _facts(), _identity())
    assert value["preflight_blockers"] == ["PODMAN_ALREADY_PRESENT"]
    assert verifier._derive_preflight_blockers is not collector.preflight_blockers
    with pytest.raises(ValueError, match="PREFLIGHT_BLOCKERS"):
        verify_observation(value, policy_path, closure_path, _identity())


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value["packages"][0].update(version="x" * 129),
        lambda value: value["packages"][0].update(architecture="x" * 33),
        lambda value: value["packages"][0].update(selection="ii secret"),
        lambda value: value["preflight_blockers"].append("SUBID_RANGE_OVERLAP"),
        lambda value: value.update(preflight_blockers=[]),
    ],
)
def test_blocker_fact_strings_and_codes_are_closed(mutation) -> None:
    policy_path = ROOT / "ci/claw/host-bootstrap-policy.json"
    closure_path = ROOT / "ci/claw/host-package-closure.json"
    facts = _facts()
    facts["packages"][0] = {
        "name": facts["packages"][0]["name"],
        "status": "installed",
        "version": "1.0",
        "architecture": "amd64",
        "selection": "ii ",
    }
    value = build_observation(policy_path, closure_path, facts, _identity())
    mutation(value)
    unsigned = {key: item for key, item in value.items() if key != "inventory_payload_sha256"}
    value["inventory_payload_sha256"] = hashlib.sha256(canonical_bytes(unsigned)).hexdigest()
    with pytest.raises(ValueError, match="PACKAGE_BASELINE|PREFLIGHT_BLOCKERS"):
        verify_observation(value, policy_path, closure_path, _identity())


def test_command_stdout_is_bounded_and_podman_is_never_executed(monkeypatch) -> None:
    with pytest.raises(RuntimeError, match="COMMAND_OUTPUT_TOO_LARGE"):
        collector._run(
            [sys.executable, "-c", "print('x' * 5000)"],
            max_stdout_bytes=128,
        )

    monkeypatch.setattr(
        collector,
        "_run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("podman probe must not execute a binary")
        ),
    )
    source = Path(collector.__file__).read_text(encoding="utf-8")
    assert '"podman", "--version"' not in source
    assert "shutil.which" not in source


def test_package_projection_uses_closed_dpkg_database_not_exit_codes(tmp_path: Path) -> None:
    closure = {"packages": [{"name": "present-pkg"}, {"name": "missing-pkg"}]}
    status = tmp_path / "status"
    status.write_text(
        "Package: present-pkg\n"
        "Status: install ok installed\n"
        "Architecture: amd64\n"
        "Version: 1.2.3-1\n"
        "Conffiles:\n"
        " /etc/present.conf abcdef\n\n",
        encoding="utf-8",
    )

    projection = collector._package_projection(closure, status, require_root=False)

    assert projection == [
        {
            "name": "present-pkg",
            "status": "installed",
            "version": "1.2.3-1",
            "architecture": "amd64",
            "selection": "ii ",
        },
        {
            "name": "missing-pkg",
            "status": "absent",
            "version": None,
            "architecture": None,
            "selection": None,
        },
    ]
    source = Path(collector.__file__).read_text(encoding="utf-8")
    assert "dpkg-query" not in source


def test_package_database_accepts_repeated_empty_paragraph_separators() -> None:
    database = collector._parse_dpkg_status(
        "Package: first-pkg\n"
        "Status: install ok installed\n"
        "Architecture: amd64\n"
        "Version: 1\n\n\n"
        "Package: second-pkg\n"
        "Status: install ok installed\n"
        "Architecture: amd64\n"
        "Version: 2\n".encode()
    )

    assert list(database) == ["first-pkg", "second-pkg"]


@pytest.mark.parametrize("content", ["", "\n", "\n\n\n"])
def test_empty_package_database_never_becomes_absent(content: str) -> None:
    with pytest.raises(RuntimeError, match="DPKG_STATUS_EMPTY"):
        collector._parse_dpkg_status(content.encode())


def test_long_unprojected_package_field_is_bounded_by_paragraph_not_target_limit() -> None:
    database = collector._parse_dpkg_status(
        (
            "Package: present-pkg\n"
            "Status: install ok installed\n"
            "Architecture: amd64\n"
            "Version: 1\n"
            f"Description: {'x' * 5000}\n"
        ).encode()
    )

    assert database["present-pkg"]["Version"] == "1"


@pytest.mark.parametrize(
    "content",
    [
        "Package: present-pkg\nStatus: install ok installed\nArchitecture: amd64\n",
        "Package: present-pkg\nStatus: install ok installed\nArchitecture: amd64\nVersion: 1\nVersion: 2\n",
        "Package present-pkg\nStatus: install ok installed\nArchitecture: amd64\nVersion: 1\n",
        "Status: install ok installed\nArchitecture: amd64\nVersion: 1\n",
    ],
)
def test_package_database_errors_never_become_absent(tmp_path: Path, content: str) -> None:
    status = tmp_path / "status"
    status.write_text(content, encoding="utf-8")
    with pytest.raises(RuntimeError, match="DPKG_STATUS"):
        collector._package_projection(
            {"packages": [{"name": "present-pkg"}]},
            status,
            require_root=False,
        )


def test_duplicate_json_and_secret_like_fields_are_rejected(tmp_path: Path) -> None:
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text('{"schema_version":"x","schema_version":"y"}\n')
    with pytest.raises(ValueError, match="DUPLICATE_KEY"):
        load_closed_json(duplicate)

    policy_path = ROOT / "ci/claw/host-bootstrap-policy.json"
    closure_path = ROOT / "ci/claw/host-package-closure.json"
    value = build_observation(policy_path, closure_path, _facts(), _identity())
    value["runner_token"] = "forbidden"
    with pytest.raises(ValueError, match="INVENTORY_FIELDS|SECRET_FIELD"):
        verify_observation(value, policy_path, closure_path, _identity())


def test_schema_is_recursively_closed_and_collector_has_no_mutation_commands() -> None:
    schema = json.loads((ROOT / "schemas/claw-host-inventory-observation-v2.schema.json").read_text())
    assert schema["additionalProperties"] is False
    for name in ("os", "target_identity", "subids", "podman"):
        assert schema["properties"][name]["additionalProperties"] is False
    assert schema["$defs"]["unit"]["additionalProperties"] is False
    assert schema["$defs"]["path"]["additionalProperties"] is False
    assert schema["$defs"]["package"]["additionalProperties"] is False
    assert "exec_start" not in schema["$defs"]["unit"]["properties"]
    assert schema["$defs"]["unit"]["properties"]["exec_start_path_sha256"]["pattern"] == "^[0-9a-f]{64}$"

    source = (ROOT / "scripts/collect_claw_host_inventory.py").read_text().casefold()
    forbidden = ("sudo", "apt-get", "apt ", "dpkg --install", "systemctl start", "systemctl stop", "systemctl restart", "podman pull", "podman load", "podman run", "docker ", "chown", "chmod", '".credentials"', '".runner"')
    assert not [token for token in forbidden if token in source]


def test_verified_log_envelope_binds_exact_observation_bytes(tmp_path: Path) -> None:
    policy_path = ROOT / "ci/claw/host-bootstrap-policy.json"
    closure_path = ROOT / "ci/claw/host-package-closure.json"
    value = build_observation(policy_path, closure_path, _facts(), _identity())
    observation = tmp_path / "inventory.json"
    raw = canonical_bytes(value)
    observation.write_bytes(raw)

    lines = emit_log_envelope(observation, policy_path, closure_path, _identity())

    assert lines == (
        "HOST_INVENTORY_OBSERVATION_SHA256=" + hashlib.sha256(raw).hexdigest(),
        "HOST_INVENTORY_OBSERVATION_B64=" + base64.b64encode(raw).decode("ascii"),
    )
    decoded = base64.b64decode(lines[1].split("=", 1)[1], validate=True)
    assert decoded == raw


def test_unit_projection_never_persists_raw_exec_argv(monkeypatch) -> None:
    working = "/home/pall/actions-runner-engine"
    raw_exec = (
        "{ path=/home/pall/actions-runner-engine/runsvc.sh ; "
        "argv[]=/home/pall/actions-runner-engine/runsvc.sh --opaque-value ; "
        "ignore_errors=no ; }"
    )
    stdout = "\n".join(
        (
            "LoadState=loaded",
            "ActiveState=active",
            "SubState=running",
            "FragmentPath=/etc/systemd/system/engine.service",
            "User=pall",
            "Group=pall",
            "MainPID=123",
            "ExecStart=" + raw_exec,
            "WorkingDirectory=" + working,
        )
    )
    completed = collector.subprocess.CompletedProcess([], 0, stdout=stdout, stderr="")
    monkeypatch.setattr(collector, "_run", lambda _argv: completed)

    projection = collector._unit_projection("engine.service", working)

    assert "exec_start" not in projection
    assert "opaque-value" not in json.dumps(projection)
    assert projection["exec_start_path_sha256"] == hashlib.sha256(
        (working + "/runsvc.sh").encode()
    ).hexdigest()

    wrong = stdout.replace(
        "path=/home/pall/actions-runner-engine/runsvc.sh",
        "path=/tmp/alternate-runner",
    )
    monkeypatch.setattr(
        collector,
        "_run",
        lambda _argv: collector.subprocess.CompletedProcess([], 0, stdout=wrong, stderr=""),
    )
    with pytest.raises(RuntimeError, match="UNIT_EXEC_START_PATH"):
        collector._unit_projection("engine.service", working)
