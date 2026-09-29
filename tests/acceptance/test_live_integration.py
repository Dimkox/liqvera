import json
from datetime import datetime, timedelta, timezone

import pytest

from tools.mezo_acceptance import runner
from tools.mezo_acceptance.live import (
    LiveAuthorityError,
    P2Plan,
    P3Plan,
    _digest,
    validate_p2_bundle,
    validate_p3_bundle,
)
from tools.mezo_acceptance.public_read import (
    PublicReadPlan,
    consume_public_read_grant,
    initialize_public_read_journal,
)

NOW = datetime(2026, 9, 29, 15, 0, tzinfo=timezone.utc)
COMMIT = "a" * 40
TREE = "b" * 40
JOURNAL = "00000000-0000-4000-8000-000000000099"


def p2_bundle(journal_sha="e" * 64, **change):
    plan = P2Plan.canonical()
    expiry = (NOW + timedelta(minutes=5)).isoformat().replace("+00:00", "Z")
    cases = {}
    for case, spec in plan.cases.items():
        digest = (
            _digest(spec)
            if case == "A29"
            else PublicReadPlan(
                "A07",
                spec["method"],
                spec["url"],
                b'{"scenario":"source-unavailable","fallback":"forbidden"}',
                15,
                2097152,
                1,
            ).digest
        )
        cases[case] = {
            **spec,
            "grant_id": f"00000000-0000-4000-8000-0000000000{case[1:]}",
            "journal_id": JOURNAL,
            "journal_sha256": journal_sha,
            "subject_commit": COMMIT,
            "subject_tree": TREE,
            "plan_sha256": digest,
            "expires_at": expiry,
        }
    value = {
        "schema": "liqvera-p2-acceptance-grants/v1",
        "subject_commit": COMMIT,
        "subject_tree": TREE,
        "plan_sha256": plan.digest,
        "expires_at": expiry,
        "journal_id": JOURNAL,
        "journal_sha256": journal_sha,
        "cases": cases,
    }
    value.update(change)
    return value


def p3_bundle(**change):
    plan = P3Plan.canonical()
    expiry = (NOW + timedelta(minutes=5)).isoformat().replace("+00:00", "Z")
    grant = {
        "schema": "liqvera-mezo-payment-grant/v1",
        "grant_id": "00000000-0000-4000-8000-000000000013",
        "subject_commit": COMMIT,
        "subject_tree": TREE,
        "plan_sha256": plan.digest,
        "expires_at": expiry,
        "buyer": "0x" + "1" * 40,
        "pay_to": "0x" + "2" * 40,
        "database_identity": "9" * 64,
        **plan.cases["A13"],
    }
    value = {
        "schema": "liqvera-p3-payment-grants/v1",
        "subject_commit": COMMIT,
        "subject_tree": TREE,
        "plan_sha256": plan.digest,
        "expires_at": expiry,
        "cases": {"A13": grant, "A14": dict(grant)},
    }
    value.update(change)
    return value


def test_p2_and_p3_are_disjoint_least_authority():
    assert set(
        validate_p2_bundle(p2_bundle(), subject_commit=COMMIT, subject_tree=TREE, now=NOW).cases
    ) == {"A07", "A29"}
    assert set(
        validate_p3_bundle(p3_bundle(), subject_commit=COMMIT, subject_tree=TREE, now=NOW).cases
    ) == {"A13", "A14"}
    mixed = p2_bundle()
    mixed["cases"]["A13"] = p3_bundle()["cases"]["A13"]
    with pytest.raises(LiveAuthorityError, match="LIVE_GRANT_INVALID"):
        validate_p2_bundle(mixed, subject_commit=COMMIT, subject_tree=TREE, now=NOW)
    with pytest.raises(LiveAuthorityError, match="LIVE_GRANT_INVALID"):
        validate_p3_bundle(p2_bundle(), subject_commit=COMMIT, subject_tree=TREE, now=NOW)


def test_p3_requires_one_byte_identical_linked_grant():
    value = p3_bundle()
    value["cases"]["A14"]["grant_id"] = "00000000-0000-4000-8000-000000000014"
    with pytest.raises(LiveAuthorityError, match="LIVE_PAYMENT_LINK_MISMATCH"):
        validate_p3_bundle(value, subject_commit=COMMIT, subject_tree=TREE, now=NOW)


@pytest.mark.parametrize("field,bad", [
    ("facilitator_url", "https://evil.invalid/"),
    ("rpc_url", "https://evil.invalid/"),
    ("database_identity", "0" * 63),
])
def test_p3_binds_exact_external_identities(field, bad):
    value = p3_bundle()
    value["cases"]["A13"][field] = bad
    value["cases"]["A14"][field] = bad
    with pytest.raises(LiveAuthorityError, match="LIVE_CASE_GRANT_MISMATCH"):
        validate_p3_bundle(value, subject_commit=COMMIT, subject_tree=TREE, now=NOW)


def test_p3_private_input_rejects_permissions_links_and_replacement(tmp_path, monkeypatch):
    path = tmp_path / "grant.json"
    path.write_text("{}")
    with pytest.raises(ValueError, match="private single-link"):
        runner.read_private_input(path, 64)
    path.chmod(0o600)
    linked = tmp_path / "linked.json"
    linked.hardlink_to(path)
    with pytest.raises(ValueError, match="private single-link"):
        runner.read_private_input(path, 64)
    linked.unlink()
    symlink = tmp_path / "symlink.json"
    symlink.symlink_to(path)
    with pytest.raises(ValueError, match="private single-link"):
        runner.read_private_input(symlink, 64)


def test_runner_binds_journal_and_keeps_a29_blocked(tmp_path, monkeypatch):
    state = tmp_path / "state"
    state.mkdir(mode=0o700)
    journal_sha = initialize_public_read_journal(state, JOURNAL)
    value = p2_bundle(journal_sha)
    expiry = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat().replace("+00:00", "Z")
    value["expires_at"] = expiry
    for case in value["cases"].values():
        case["expires_at"] = expiry
    grants = tmp_path / "grants.json"
    grants.write_text(json.dumps(value))
    calls = []

    def fake(plan, grant, **kwargs):
        identity = consume_public_read_grant(kwargs["state_dir"], grant)
        calls.append("A07")
        return {
            "schema": "liqvera-a07-source-unavailable/v1",
            "adapter": "HttpReportService.build",
            "request_count": 1,
            "reason": "SOURCE_UNAVAILABLE",
            "source_mode": "live-public",
            "fixture_fallback_used": False,
            "artifact_emitted": False,
            "grant_id": grant.grant_id,
            "grant_digest": grant.digest,
            "plan_sha256": plan.digest,
            "subject_commit": COMMIT,
            "subject_tree": TREE,
            "state_dir_identity": identity,
            "stdout_sha256": "d" * 64,
            "build_stdout_sha256": "e" * 64,
        }

    monkeypatch.setattr(
        runner,
        "repo_identity",
        lambda: {
            "repository": "Dimkox/liqvera",
            "origin": "UNSET",
            "commit": COMMIT,
            "tree": TREE,
            "worktree": "CLEAN",
        },
    )
    monkeypatch.setattr(runner, "execute_a07", fake)
    output = tmp_path / "out" / "result.json"
    monkeypatch.setattr(
        runner.sys,
        "argv",
        [
            "runner",
            "--mode",
            "live",
            "--live-grants",
            str(grants),
            "--operator-state-dir",
            str(state),
            "--output",
            str(output),
        ],
    )
    assert runner.main() == 1
    rows = {x["case_id"]: x for x in json.loads(output.read_text())["cases"]}
    assert calls == ["A07"]
    assert rows["A07"]["status"] == "PASS"
    assert rows["A29"]["omissions"] == ["A29_NETWORK_BYTE_CAP_UNENFORCEABLE"]
    other = tmp_path / "other"
    other.mkdir(mode=0o700)
    initialize_public_read_journal(other, "00000000-0000-4000-8000-000000000098")
    monkeypatch.setattr(
        runner.sys,
        "argv",
        [
            "runner",
            "--mode",
            "live",
            "--live-grants",
            str(grants),
            "--operator-state-dir",
            str(other),
            "--output",
            str(tmp_path / "other-out" / "result.json"),
        ],
    )
    with pytest.raises(SystemExit):
        runner.main()
    assert calls == ["A07"]


def test_p3_operator_cli_is_separate_and_requires_human_wallet_before_io(tmp_path, monkeypatch):
    value = p3_bundle()
    expiry = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat().replace("+00:00", "Z")
    value["expires_at"] = expiry
    for case in value["cases"].values():
        case["expires_at"] = expiry
    grants = tmp_path / "p3.json"
    grants.write_text(json.dumps(value))
    grants.chmod(0o600)
    monkeypatch.setattr(
        runner,
        "repo_identity",
        lambda: {
            "repository": "Dimkox/liqvera",
            "origin": "UNSET",
            "commit": COMMIT,
            "tree": TREE,
            "worktree": "CLEAN",
        },
    )
    output = tmp_path / "p3-out" / "result.json"
    monkeypatch.setattr(
        runner.sys,
        "argv",
        [
            "runner",
            "--mode",
            "live",
            "--p3-live-grants",
            str(grants),
            "--output",
            str(output),
        ],
    )
    assert runner.main() == 1
    rows = {row["case_id"]: row for row in json.loads(output.read_text())["cases"]}
    assert rows["A13"]["omissions"] == ["HUMAN_WALLET_SIGNATURE_REQUIRED"]
    assert rows["A14"]["omissions"] == ["HUMAN_WALLET_SIGNATURE_REQUIRED"]


def test_p3_operator_cli_seals_confirmed_linked_a13_a14_once(tmp_path, monkeypatch):
    value = p3_bundle()
    expiry = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat().replace("+00:00", "Z")
    value["expires_at"] = expiry
    for case in value["cases"].values():
        case["expires_at"] = expiry
    grants = tmp_path / "p3.json"
    grants.write_text(json.dumps(value))
    grants.chmod(0o600)
    payment = tmp_path / "payment.json"
    payment.write_text("{}")
    payment.chmod(0o600)
    identity = {"repository": "Dimkox/liqvera", "origin": "UNSET", "commit": COMMIT, "tree": TREE, "worktree": "CLEAN"}
    monkeypatch.setattr(runner, "repo_identity", lambda: identity)
    calls = []
    observation = {
        "schema": "liqvera-p3-payment-observation/v1", "status": "CONFIRMED",
        "grant_id": "00000000-0000-4000-8000-000000000013", "grant_digest": "d" * 64,
        "settlement_count": 1, "retry_allowed": False, "tx_hash": "0x" + "3" * 64,
        "transaction_from": "0x" + "4" * 40, "buyer_native_balance_before": "7",
        "buyer_native_balance_after": "7", "buyer_native_gas_spent": "0",
        "observation_before_block_number": 10, "observation_before_block_hash": "0x" + "5" * 64,
        "observation_after_block_number": 22, "observation_after_block_hash": "0x" + "6" * 64,
        "block_number": 11, "block_hash": "0x" + "7" * 64, "log_index": 0,
        "confirmations": 12, "authorization_identity": "auth", "transfer_identity": "transfer",
        "payer": "0x" + "1" * 40, "pay_to": "0x" + "2" * 40,
        "quote_id": "00000000-0000-4000-8000-000000000001",
        "report_id": "00000000-0000-4000-8000-000000000002",
        "payment_attempt_id": "00000000-0000-4000-8000-000000000003",
        "report_sha256": "a" * 64, "network": "eip155:31611", "chain_id": 31611,
        "asset": "0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503",
        "amount_atomic": "10000000000000000", "confirmed_at": NOW.isoformat(),
        "finality_policy_version": "mezo-testnet-canonical-12/v1",
    }
    monkeypatch.setattr(runner, "execute_p3_operator", lambda *a, **k: calls.append(1) or observation)
    output = tmp_path / "p3-confirmed" / "result.json"
    monkeypatch.setattr(runner.sys, "argv", ["runner", "--mode", "live", "--p3-live-grants", str(grants), "--p3-payment", str(payment), "--facilitator-url", "https://facilitator.invalid", "--rpc-url", "https://rpc.invalid", "--output", str(output)])
    assert runner.main() == 1
    rows = {row["case_id"]: row for row in json.loads(output.read_text())["cases"]}
    assert rows["A13"]["status"] == rows["A14"]["status"] == "PASS"
    assert rows["A13"]["payment_evidence"]["tx_hash"] == rows["A14"]["payment_evidence"]["tx_hash"]
    assert rows["A14"]["payment_evidence"]["settlement_count"] == 1
    assert calls == [1]
