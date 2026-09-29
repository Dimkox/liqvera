from datetime import datetime, timedelta, timezone

import pytest

from tools.mezo_acceptance import runner
from tools.mezo_acceptance.live import LiveAuthorityError, LivePlan, validate_live_bundle
from tools.mezo_acceptance.runner import execute_authorized_live_cases

NOW = datetime(2026, 9, 29, 15, 0, tzinfo=timezone.utc)
COMMIT = "a" * 40
TREE = "b" * 40


def bundle(**change):
    plan = LivePlan.canonical()
    value = {
        "schema": "liqvera-live-acceptance-grants/v1",
        "subject_commit": COMMIT,
        "subject_tree": TREE,
        "plan_sha256": plan.digest,
        "expires_at": (NOW + timedelta(minutes=5)).isoformat().replace("+00:00", "Z"),
        "cases": {case: plan.grant(case) for case in ("A07", "A29", "A13", "A14")},
    }
    for case in ("A07", "A29"):
        spec = plan.cases[case]
        body = b'{"scenario":"source-unavailable","fallback":"forbidden"}' if case == "A07" else b""
        from tools.mezo_acceptance.public_read import PublicReadPlan
        value["cases"][case].update({
            "subject_commit": COMMIT,
            "subject_tree": TREE,
            "plan_sha256": PublicReadPlan(case, spec["method"], spec["url"], body,
                                             spec["timeout_seconds"], spec["max_response_bytes"], 1).digest,
            "expires_at": value["expires_at"],
        })
    for case in ("A13", "A14"):
        value["cases"][case].update({
            "schema": "liqvera-live-payment-grant/v1",
            "subject_commit": COMMIT,
            "subject_tree": TREE,
            "plan_sha256": plan.digest,
            "expires_at": value["expires_at"],
            "buyer": "0x1111111111111111111111111111111111111111",
            "pay_to": "0x2222222222222222222222222222222222222222",
        })
    value.update(change)
    return value


class Reads:
    def __init__(self):
        self.calls = []

    def execute(self, case, grant, plan):
        self.calls.append(case)
        return {
            "status": 200,
            "response_sha256": case.lower().ljust(64, "0"),
            "response_bytes": 10,
            "attempts": 1,
            "plan_sha256": plan.digest,
        }


class Payment:
    def __init__(self, unknown=False):
        self.settles = 0
        self.unknown = unknown

    def execute(self, grant):
        self.settles += 1
        if self.unknown:
            return {
                "status": "UNKNOWN",
                "grant_digest": grant.digest,
                "attempt_id": "1",
                "settlement_count": 1,
            }
        return {
            "status": "CONFIRMED",
            "grant_digest": grant.digest,
            "attempt_id": "1",
            "authorization_identity": "d" * 64,
            "tx_hash": "0x" + "1" * 64,
            "block_hash": "0x" + "2" * 64,
            "log_index": 0,
            "finality_policy_version": "mezo-testnet-canonical-12/v1",
            "settlement_count": 1,
        }

    def replay(self, receipt):
        return {
            "tx_hash": receipt["tx_hash"],
            "settlement_count": self.settles,
            "entitlement_reused": True,
        }


def test_live_bundle_executes_reads_and_one_shared_payment():
    authority = validate_live_bundle(bundle(), subject_commit=COMMIT, subject_tree=TREE, now=NOW)
    reads = Reads()
    payment = Payment()
    rows = execute_authorized_live_cases(authority, reads, payment, now=lambda: NOW)
    assert reads.calls == ["A07", "A29"]
    assert payment.settles == 1
    assert rows["A14"]["tx_hash"] == rows["A13"]["tx_hash"] and rows["A14"]["settlement_count"] == 1


@pytest.mark.parametrize(
    "change,reason",
    [
        ({"subject_tree": "c" * 40}, "LIVE_SUBJECT_MISMATCH"),
        ({"plan_sha256": "c" * 64}, "LIVE_PLAN_MISMATCH"),
        ({"expires_at": NOW.isoformat().replace("+00:00", "Z")}, "LIVE_GRANT_EXPIRED"),
    ],
)
def test_live_bundle_rejects_stale_or_mismatched_authority(change, reason):
    with pytest.raises(LiveAuthorityError, match=f"^{reason}$"):
        validate_live_bundle(bundle(**change), subject_commit=COMMIT, subject_tree=TREE, now=NOW)


def test_body_target_and_shared_grant_mutants_fail_closed():
    value = bundle()
    value["cases"]["A07"]["body_sha256"] = "e" * 64
    with pytest.raises(LiveAuthorityError, match="^LIVE_CASE_GRANT_MISMATCH$"):
        validate_live_bundle(value, subject_commit=COMMIT, subject_tree=TREE, now=NOW)
    value = bundle()
    value["cases"]["A29"]["url"] = "https://example.com/"
    with pytest.raises(LiveAuthorityError, match="^LIVE_CASE_GRANT_MISMATCH$"):
        validate_live_bundle(value, subject_commit=COMMIT, subject_tree=TREE, now=NOW)
    value = bundle()
    value["cases"]["A14"]["grant_id"] = "00000000-0000-4000-8000-000000000014"
    with pytest.raises(LiveAuthorityError, match="^LIVE_PAYMENT_LINK_MISMATCH$"):
        validate_live_bundle(value, subject_commit=COMMIT, subject_tree=TREE, now=NOW)


def test_unknown_is_spent_and_never_replayed():
    authority = validate_live_bundle(bundle(), subject_commit=COMMIT, subject_tree=TREE, now=NOW)
    payment = Payment(True)
    rows = execute_authorized_live_cases(authority, Reads(), payment, now=lambda: NOW)
    assert (
        payment.settles == 1
        and rows["A13"]["status"] == "UNKNOWN"
        and rows["A14"]["status"] == "BLOCKED_CONFIRM_ONLY"
    )


def test_operator_cli_seals_public_reads_and_blocks_payment_without_gas_seam(tmp_path, monkeypatch):
    grant_file = tmp_path / "grants.json"
    live_bundle = bundle()
    expiry = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat().replace("+00:00", "Z")
    live_bundle["expires_at"] = expiry
    for case in ("A07", "A29", "A13", "A14"):
        live_bundle["cases"][case]["expires_at"] = expiry
    grant_file.write_text(__import__("json").dumps(live_bundle), encoding="utf-8")
    output = tmp_path / "sealed" / "result.json"
    calls = []

    def fake_a07(plan, grant, **kwargs):
        from tools.mezo_acceptance.public_read import consume_public_read_grant
        state_identity = consume_public_read_grant(kwargs["state_dir"], grant)
        calls.append((plan.case, grant.grant_id))
        return {
            "schema": "liqvera-a07-source-unavailable/v1", "adapter": "HttpReportService.build",
            "request_count": 1, "reason": "SOURCE_UNAVAILABLE", "source_mode": "live-public",
            "fixture_fallback_used": False, "artifact_emitted": False,
            "grant_id": grant.grant_id, "grant_digest": grant.digest,
            "plan_sha256": plan.digest, "subject_commit": COMMIT, "subject_tree": TREE,
            "state_dir_identity": state_identity,
            "stdout_sha256": "d" * 64, "build_stdout_sha256": "e" * 64,
        }
    def fake_a29(plan, grant, **kwargs):
        from tools.mezo_acceptance.public_read import consume_public_read_grant
        state_identity = consume_public_read_grant(kwargs["state_dir"], grant)
        calls.append((plan.case, grant.grant_id))
        return {"schema": "liqvera-a29-anonymous-clone/v1", "commit": COMMIT, "tree": TREE,
                "origin": "https://github.com/Dimkox/liqvera.git", "clone_size_bytes": 10,
                "credential_prompt": False, "redirects_allowed": False,
                "resolved_addresses": ["8.8.8.8"], "connected_address": "8.8.8.8", "grant_id": grant.grant_id,
                "grant_digest": grant.digest, "plan_sha256": plan.digest, "subject_commit": COMMIT,
                "subject_tree": TREE, "state_dir_identity": state_identity}

    monkeypatch.setattr(runner, "repo_identity", lambda: {
        "repository": "Dimkox/liqvera", "origin": "UNSET", "commit": COMMIT,
        "tree": TREE, "worktree": "CLEAN",
    })
    monkeypatch.setattr(runner, "execute_a07", fake_a07)
    monkeypatch.setattr(runner, "execute_a29", fake_a29)
    monkeypatch.setattr(runner.sys, "argv", ["runner", "--mode", "live", "--live-grants",
                                              str(grant_file), "--operator-state-dir", str(tmp_path / "state"),
                                              "--output", str(output)])
    (tmp_path / "state").mkdir(mode=0o700)
    assert runner.main() == 1
    result = __import__("json").loads(output.read_text())
    rows = {row["case_id"]: row for row in result["cases"]}
    assert [case for case, _ in calls] == ["A07", "A29"]
    assert rows["A07"]["status"] == rows["A29"]["status"] == "PASS"
    assert rows["A13"]["omissions"] == rows["A14"]["omissions"] == ["LIVE_GAS_ENFORCEMENT_UNAVAILABLE"]
    output2 = tmp_path / "sealed-again" / "result.json"
    monkeypatch.setattr(runner.sys, "argv", ["runner", "--mode", "live", "--live-grants",
                                              str(grant_file), "--operator-state-dir", str(tmp_path / "state"),
                                              "--output", str(output2)])
    assert runner.main() == 1
    replay = __import__("json").loads(output2.read_text())
    replay_rows = {row["case_id"]: row for row in replay["cases"]}
    assert [case for case, _ in calls] == ["A07", "A29"]
    assert replay_rows["A07"]["status"] == replay_rows["A29"]["status"] == "FAIL"
