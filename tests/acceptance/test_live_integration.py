from datetime import datetime, timedelta, timezone

import pytest

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
