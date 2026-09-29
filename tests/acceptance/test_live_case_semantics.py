from __future__ import annotations

import hashlib
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from tools.mezo_acceptance.live import P2Plan
from tools.mezo_acceptance.live_cases import (
    ResourceEnvelope,
    execute_a07,
    run_bounded_git_clone,
    run_resource_bounded,
)
from tools.mezo_acceptance.public_read import (
    GrantError,
    PublicReadGrant,
    PublicReadPlan,
    initialize_public_read_journal,
    journal_document,
)

ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 9, 29, 15, 0, tzinfo=timezone.utc)
JOURNAL = "00000000-0000-4000-8000-000000000099"
JOURNAL_SHA = hashlib.sha256(journal_document(JOURNAL)).hexdigest()


def identity():
    return {
        "commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "tree": subprocess.check_output(
            ["git", "rev-parse", "HEAD^{tree}"], cwd=ROOT, text=True
        ).strip(),
    }


def authority():
    spec = P2Plan.canonical().cases["A07"]
    plan = PublicReadPlan(
        "A07",
        spec["method"],
        spec["url"],
        b'{"scenario":"source-unavailable","fallback":"forbidden"}',
        15,
        2097152,
        1,
    )
    subject = identity()
    grant = PublicReadGrant.parse(
        {
            "schema": "liqvera-public-read-grant/v1",
            "grant_id": "00000000-0000-4000-8000-000000000007",
            "journal_id": JOURNAL,
            "journal_sha256": JOURNAL_SHA,
            "subject_commit": subject["commit"],
            "subject_tree": subject["tree"],
            "plan_sha256": plan.digest,
            "case": "A07",
            "method": plan.method,
            "url": plan.url,
            "expires_at": (NOW + timedelta(minutes=5)).isoformat().replace("+00:00", "Z"),
            "maximum_attempts": 1,
            "timeout_seconds": 15,
            "max_response_bytes": 2097152,
            "body_sha256": plan.body_sha256,
        },
        now=NOW,
    )
    return plan, grant


def test_a07_real_gateway_adapter_reports_unavailable_without_fixture_or_artifact(tmp_path):
    state = tmp_path / "state"
    state.mkdir(mode=0o700)
    initialize_public_read_journal(state, JOURNAL)
    plan, grant = authority()
    result = execute_a07(
        plan, grant, identity=identity(), state_dir=state, root=ROOT, now=lambda: NOW
    )
    assert result["reason"] == "SOURCE_UNAVAILABLE"
    assert result["fixture_fallback_used"] is result["artifact_emitted"] is False


@pytest.mark.parametrize(
    "script,reason",
    [
        (
            "import sys,time;[(sys.stdout.write('x'*4096),sys.stdout.flush(),time.sleep(.01)) for _ in range(20)]",
            "A29_OUTPUT_CAP",
        ),
        (
            "import pathlib,time; p=pathlib.Path('payload');[(p.write_bytes(b'x'*(i*4096)),time.sleep(.01)) for i in range(1,30)]",
            "A29_AGGREGATE_DISK_CAP",
        ),
    ],
)
def test_resource_envelope_terminates_before_unbounded_completion(tmp_path, script, reason):
    envelope = ResourceEnvelope(5, 32768, 131072, 268435456, 8192)
    with pytest.raises(GrantError, match=f"^{reason}$"):
        run_resource_bounded([sys.executable, "-c", script], tmp_path, envelope)


def test_clone_seam_uses_exact_target_pinned_address_and_no_ambient_credentials(
    monkeypatch, tmp_path
):
    observed = {}

    def bounded(command, root, envelope, *, environment):
        observed.update(command=command, root=root, environment=environment)
        return subprocess.CompletedProcess(command, 0, b"", b"")

    monkeypatch.setattr("tools.mezo_acceptance.live_cases.run_resource_bounded", bounded)
    destination = tmp_path / "clone"
    envelope = ResourceEnvelope(5, 32768, 16384, 268435456, 8192)
    run_bounded_git_clone(
        "https://github.com/Dimkox/liqvera.git", destination, "192.0.2.1", envelope
    )

    assert observed["root"] == tmp_path
    assert observed["command"][-2:] == [
        "https://github.com/Dimkox/liqvera.git",
        str(destination),
    ]
    assert "http.curloptResolve=github.com:443:192.0.2.1" in observed["command"]
    assert observed["environment"] == {
        "PATH": observed["environment"]["PATH"],
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_ASKPASS": "/bin/false",
        "SSH_ASKPASS": "/bin/false",
    }


def test_clone_seam_rejects_non_allowlisted_target_before_process(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "tools.mezo_acceptance.live_cases.run_resource_bounded",
        lambda *args, **kwargs: pytest.fail("process must not start"),
    )
    with pytest.raises(GrantError, match="^A29_TARGET_MISMATCH$"):
        run_bounded_git_clone(
            "https://example.com/repo.git",
            tmp_path / "clone",
            "192.0.2.1",
            ResourceEnvelope(5, 32768, 16384, 268435456, 8192),
        )
