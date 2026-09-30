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
    assert compose["services"]["report"]["environment"]["LIQVERA_ENGINE_COMMIT"] == "${LIQVERA_ENGINE_COMMIT:?verified release commit required}"
    assert compose["services"]["gateway"]["environment"]["PUBLIC_BASE_URL"] == "http://127.0.0.1:3000"
    assert compose["services"]["gateway"]["networks"]["operations"]["aliases"] == ["gateway-metrics"]
    assert compose["services"]["capture"]["networks"]["capture_report"]["aliases"] == ["evidence-capture"]
    assert compose["services"]["report"]["environment"]["LIQVERA_CAPTURE_URL"] == "http://evidence-capture:8081"
    for name in ("capture", "report", "gateway", "web", "edge"):
        service = compose["services"][name]
        assert service["healthcheck"]["start_period"]
        assert service["user"]
        assert service["mem_limit"]
        assert service["cpus"]
        assert service["tmpfs"]
    assert compose["services"]["migrate"]["tmpfs"] == ["/tmp:rw,noexec,nosuid,size=32m"]
    assert compose["services"]["capture"]["tmpfs"] == ["/tmp:rw,noexec,nosuid,size=32m"]
    assert compose["services"]["report"]["tmpfs"] == ["/tmp:rw,noexec,nosuid,size=64m"]
    assert compose["services"]["gateway"]["tmpfs"] == ["/tmp:rw,noexec,nosuid,size=64m"]
    assert compose["services"]["edge"]["tmpfs"] == ["/tmp:rw,noexec,nosuid,size=16m"]
    assert compose["services"]["migrate"]["volumes"] == [
        "./manifests/release-manifest.json:/run/liqvera/release-manifest.json:ro",
        "./migrations:/run/liqvera/migrations:ro",
    ]
    assert compose["services"]["migrate"]["environment"] == {
        "MIGRATION_MANIFEST_FILE": "/run/liqvera/release-manifest.json",
        "MIGRATION_SQL_ROOT": "/run/liqvera/migrations",
    }
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
    clock_values = iter([0.0, 1.0, 2.0, 3.0, 4.0])
    remaining: list[float] = []
    result = ORCHESTRATION.wait_healthy(lambda budget: remaining.append(budget) or next(observations),
                                        lambda: next(clock_values), lambda _: None, 10.0)
    assert result["containers"] == "healthy"
    assert remaining == [9.0, 7.0]
    with pytest.raises(ORCHESTRATION.OrchestrationError, match="HEALTH_TIMEOUT"):
        ORCHESTRATION.wait_healthy(
            lambda _: {"containers": "healthy", "storage": False, "integration": True, "payment": False,
                     "reasons": ["STORAGE_UNAVAILABLE"]},
            iter([0.0, 11.0]).__next__, lambda _: None, 10.0,
        )


@pytest.mark.parametrize(
    "reasons",
    [
        ["SIMULATED_SOURCE"],
        ["EXTERNAL_GRANT_REQUIRED"],
        ["SIMULATED_SOURCE", "EXTERNAL_GRANT_REQUIRED", 1],
        ["SIMULATED_SOURCE", "EXTERNAL_GRANT_REQUIRED", "UNKNOWN"],
        ["SIMULATED_SOURCE", "EXTERNAL_GRANT_REQUIRED", "EXTERNAL_GRANT_REQUIRED"],
    ],
)
def test_health_requires_both_closed_honest_blockers(reasons: list[object]) -> None:
    clocks = iter([10.0, 10.0, 10.5, 12.0])
    with pytest.raises(ORCHESTRATION.OrchestrationError, match="HEALTH_TIMEOUT"):
        ORCHESTRATION.wait_healthy(
            lambda _: {"containers": "healthy", "storage": True, "integration": True,
                     "payment": False, "reasons": reasons},
            clocks.__next__, lambda _: None, 1.0,
        )


def test_health_deadline_rejects_a_clock_that_moves_backwards() -> None:
    clocks = iter([10.0, 10.0, 9.0])
    with pytest.raises(ORCHESTRATION.OrchestrationError, match="HEALTH_CLOCK_INVALID"):
        ORCHESTRATION.wait_healthy(lambda _: {"containers": "starting"}, clocks.__next__, lambda _: None, 10.0)


def test_health_rejects_success_returned_after_total_deadline() -> None:
    clocks = iter([0.0, 1.0, 11.0])
    with pytest.raises(ORCHESTRATION.OrchestrationError, match="HEALTH_TIMEOUT"):
        ORCHESTRATION.wait_healthy(
            lambda _: {"containers": "healthy", "storage": True, "integration": True,
                     "payment": False, "reasons": ["SIMULATED_SOURCE", "EXTERNAL_GRANT_REQUIRED"]},
            clocks.__next__, lambda _: None, 10.0,
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


def test_partial_compose_up_failure_stops_only_candidate() -> None:
    trace: list[tuple[str, str]] = []

    def partial_up(project: str) -> None:
        trace.append(("up", project))
        raise RuntimeError("partial startup")

    with pytest.raises(RuntimeError, match="partial startup"):
        ORCHESTRATION.start_candidate("candidate", partial_up, lambda: True, lambda: {},
                                      lambda project: trace.append(("down", project)))
    assert trace == [("up", "candidate"), ("down", "candidate")]


def test_candidate_cleanup_failure_does_not_mask_startup_failure() -> None:
    def fail_up(_: str) -> None:
        raise RuntimeError("original startup failure")

    def fail_down(_: str) -> None:
        raise RuntimeError("cleanup failure")

    with pytest.raises(RuntimeError, match="original startup failure"):
        ORCHESTRATION.start_candidate("candidate", fail_up, lambda: True, lambda: {}, fail_down)
