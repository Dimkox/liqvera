from __future__ import annotations

import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

from tools.mezo_acceptance.live import LivePlan
from tools.mezo_acceptance.live_cases import execute_a07, execute_a29
from tools.mezo_acceptance.public_read import PublicReadGrant, PublicReadPlan

ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 9, 29, 15, 0, tzinfo=timezone.utc)


def identity() -> dict[str, str]:
    return {
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "tree": subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=ROOT, text=True).strip(),
    }


def authority(case: str) -> tuple[PublicReadPlan, PublicReadGrant]:
    spec = LivePlan.canonical().cases[case]
    body = b'{"scenario":"source-unavailable","fallback":"forbidden"}' if case == "A07" else b""
    plan = PublicReadPlan(case, spec["method"], spec["url"], body, spec["timeout_seconds"],
                          spec["max_response_bytes"], 1)
    subject = identity()
    grant = PublicReadGrant.parse({
        "schema": "liqvera-public-read-grant/v1",
        "grant_id": f"00000000-0000-4000-8000-0000000000{case[1:]}",
        "subject_commit": subject["commit"], "subject_tree": subject["tree"],
        "plan_sha256": plan.digest, "case": case, "method": plan.method, "url": plan.url,
        "expires_at": (NOW + timedelta(minutes=5)).isoformat().replace("+00:00", "Z"),
        "maximum_attempts": 1, "timeout_seconds": plan.timeout_seconds,
        "max_response_bytes": plan.max_response_bytes, "body_sha256": plan.body_sha256,
    }, now=NOW)
    return plan, grant


def test_a07_real_gateway_adapter_reports_unavailable_without_fixture_or_artifact(tmp_path: Path) -> None:
    state = tmp_path / "state"
    state.mkdir(mode=0o700)
    plan, grant = authority("A07")
    result = execute_a07(plan, grant, identity=identity(), state_dir=state, root=ROOT, now=lambda: NOW)
    assert result["reason"] == "SOURCE_UNAVAILABLE"
    assert result["fixture_fallback_used"] is result["artifact_emitted"] is False
    assert result["adapter"] == "HttpReportService.build"


def test_a29_anonymous_clone_proves_exact_commit_tree_and_origin_without_network(tmp_path: Path) -> None:
    state = tmp_path / "state"
    state.mkdir(mode=0o700)
    plan, grant = authority("A29")
    def local_clone(command, **kwargs):
        local = [*command]
        local[-2] = f"file://{ROOT}"
        result = subprocess.run(local, **kwargs)
        if result.returncode == 0:
            subprocess.run(["git", "-C", local[-1], "remote", "set-url", "origin", plan.url], check=True)
        return result
    result = execute_a29(plan, grant, identity=identity(), state_dir=state, now=lambda: NOW, runner=local_clone,
                         resolver=lambda _host: ("8.8.8.8",))
    assert (result["commit"], result["tree"], result["origin"]) == (
        identity()["commit"], identity()["tree"], "https://github.com/Dimkox/liqvera.git")
