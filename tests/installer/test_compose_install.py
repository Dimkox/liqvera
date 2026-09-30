from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "installer/lib/orchestration.py"
SPEC = importlib.util.spec_from_file_location("installer_orchestration", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
ORCHESTRATION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ORCHESTRATION)

MIGRATIONS = [
    (path.name, hashlib.sha256(path.read_bytes()).hexdigest())
    for path in sorted((ROOT / "apps/mezo-gateway/migrations").glob("*.sql"))
]


def test_compose_is_shadow_only_digest_bound_and_publishes_only_edge() -> None:
    compose = yaml.safe_load((ROOT / "installer/compose.yaml").read_text())
    assert set(compose["services"]) == {"postgres", "migrate", "capture", "report", "gateway", "web", "edge"}
    for service in compose["services"].values():
        assert "build" not in service
        assert service["image"].startswith("${LIQVERA_IMAGE_")
        assert "ports" not in service or service is compose["services"]["edge"]
        assert "/var/run/docker.sock" not in repr(service)
        assert "P3_" not in repr(service)
    assert compose["services"]["edge"]["ports"] == ["127.0.0.1:3000:8080"]
    assert compose["services"]["capture"]["environment"]["LIQVERA_SOURCE_MODE"] == "fixture"
    assert compose["services"]["gateway"]["environment"]["SOURCE_MODE"] == "fixture"
    assert compose["networks"]["operations"]["internal"] is True
    assert compose["services"]["migrate"]["restart"] == "no"
    source_manifest = json.loads((ROOT / "installer/manifests/v0.0.2.json").read_text())
    assert source_manifest["runnable"] is False
    assert set(source_manifest["images"].values()) == {None}
    assert source_manifest["compose_sha256"] == hashlib.sha256(
        (ROOT / "installer/compose.yaml").read_bytes()
    ).hexdigest()
    assert [(item["name"], item["sha256"]) for item in source_manifest["migrations"]] == MIGRATIONS


@pytest.mark.parametrize("applied", [[], MIGRATIONS[:1], MIGRATIONS[:4], MIGRATIONS])
def test_migration_plan_accepts_only_exact_prefix(applied: list[tuple[str, str]]) -> None:
    assert ORCHESTRATION.check_migration_plan(MIGRATIONS, applied) == MIGRATIONS[len(applied):]


@pytest.mark.parametrize(
    "applied",
    [
        [("000_unknown.sql", "0" * 64)],
        [MIGRATIONS[1]],
        [(MIGRATIONS[0][0], "0" * 64)],
        [*MIGRATIONS, ("006_unknown.sql", "0" * 64)],
        [MIGRATIONS[0], MIGRATIONS[0]],
    ],
)
def test_migration_plan_rejects_unknown_gap_checksum_or_duplicate(applied: list[tuple[str, str]]) -> None:
    with pytest.raises(ORCHESTRATION.OrchestrationError, match="MIGRATION_MISMATCH"):
        ORCHESTRATION.check_migration_plan(MIGRATIONS, applied)


def test_bounded_health_accepts_only_safe_shadow_blockers() -> None:
    observations = iter([
        {"containers": "starting"},
        {"containers": "healthy", "storage": True, "integration": True, "payment": False,
         "reasons": ["SIMULATED_SOURCE", "EXTERNAL_GRANT_REQUIRED", "PAYMENT_SERVICE_UNAVAILABLE", "PAY_TO_MISSING"]},
    ])
    clock_values = iter([0.0, 1.0, 2.0, 3.0])
    result = ORCHESTRATION.wait_healthy(lambda: next(observations), lambda: next(clock_values), lambda _: None, 10.0)
    assert result["containers"] == "healthy"
    with pytest.raises(ORCHESTRATION.OrchestrationError, match="HEALTH_TIMEOUT"):
        ORCHESTRATION.wait_healthy(
            lambda: {"containers": "healthy", "storage": False, "integration": True, "payment": False,
                     "reasons": ["STORAGE_UNAVAILABLE"]},
            iter([0.0, 11.0]).__next__, lambda _: None, 10.0,
        )


def test_port_race_or_health_failure_stops_only_candidate() -> None:
    trace: list[tuple[str, str]] = []
    with pytest.raises(ORCHESTRATION.OrchestrationError, match="PORT_OCCUPIED"):
        ORCHESTRATION.start_candidate("candidate", lambda p: trace.append(("up", p)), lambda: False,
                                      lambda: {}, lambda p: trace.append(("down", p)))
    assert trace == [("down", "candidate")]
    trace.clear()
    with pytest.raises(ORCHESTRATION.OrchestrationError, match="HEALTH_TIMEOUT"):
        ORCHESTRATION.start_candidate("candidate", lambda p: trace.append(("up", p)), lambda: True,
                                      lambda: (_ for _ in ()).throw(ORCHESTRATION.OrchestrationError("HEALTH_TIMEOUT")),
                                      lambda p: trace.append(("down", p)))
    assert trace == [("up", "candidate"), ("down", "candidate")]
