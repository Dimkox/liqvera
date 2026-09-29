import json
from datetime import datetime, timedelta, timezone

import pytest

from tools.mezo_acceptance.live import P3Plan
from tools.mezo_acceptance.p3_operator import (
    REQUIRED_MIGRATIONS,
    P3Operator,
    P3OperatorError,
    load_payment_input,
)


NOW = datetime(2026, 9, 29, 17, 0, tzinfo=timezone.utc)
COMMIT = "a" * 40
TREE = "b" * 40
BUYER = "0x" + "1" * 40
PAYEE = "0x" + "2" * 40
TX = "0x" + "3" * 64


def grant():
    expires = (NOW + timedelta(minutes=5)).isoformat().replace("+00:00", "Z")
    item = {
        "schema": "liqvera-mezo-payment-grant/v1",
        "grant_id": "00000000-0000-4000-8000-000000000013",
        "subject_commit": COMMIT,
        "subject_tree": TREE,
        "plan_sha256": P3Plan.canonical().digest,
        "expires_at": expires,
        "buyer": BUYER,
        "pay_to": PAYEE,
        "database_identity": "9" * 64,
        **P3Plan.canonical().cases["A13"],
    }
    return {
        "schema": "liqvera-p3-payment-grants/v1",
        "subject_commit": COMMIT,
        "subject_tree": TREE,
        "plan_sha256": P3Plan.canonical().digest,
        "expires_at": expires,
        "cases": {"A13": item, "A14": dict(item)},
    }


def payload():
    return {
        "schema": "liqvera-p3-signed-payment/v1",
        "quote_id": "00000000-0000-4000-8000-000000000001",
        "scope_hash": "a" * 64,
        "report_id": "00000000-0000-4000-8000-000000000002",
        "payment_signature": "opaque-human-wallet-produced-x402-header",
        "buyer": BUYER,
        "pay_to": PAYEE,
    }


class FakeStore:
    def __init__(self):
        self.state = None
        self.consumes = 0

    def migrations(self):
        return dict(REQUIRED_MIGRATIONS)

    def existing(self, grant_digest):
        return self.state

    def consume_and_mark_submitting(self, grant_digest, grant_id, payment):
        if self.state is not None:
            return False
        self.consumes += 1
        self.state = {"state": "SUBMITTING", "attempt_id": "attempt-1", "tx_hash": None}
        return True

    def mark_unknown(self, tx_hash):
        self.state.update(state="UNKNOWN", tx_hash=tx_hash)

    def confirm(self, observation):
        self.state = {"state": "CONFIRMED", **observation}


class FakeExternal:
    def __init__(self, pending=False):
        self.pending = pending
        self.calls = []

    def snapshot(self, buyer):
        self.calls.append("snapshot")
        return {"balance": "7", "block_number": 10, "block_hash": "0x" + "4" * 64}

    def verify(self, payment):
        self.calls.append("verify")
        return {"authorization_identity": "auth", "transfer_identity": "transfer"}

    def settle(self, payment):
        self.calls.append("settle")
        return {"status": "pending" if self.pending else "submitted", "tx_hash": TX}

    def confirmation(self, tx_hash, before):
        self.calls.append("confirmation")
        if self.pending:
            return None
        return {
            "tx_hash": TX,
            "transaction_from": "0x" + "5" * 40,
            "buyer_native_balance_before": "7",
            "buyer_native_balance_after": "7",
            "buyer_native_gas_spent": "0",
            "observation_before_block_number": 10,
            "observation_before_block_hash": "0x" + "4" * 64,
            "observation_after_block_number": 22,
            "observation_after_block_hash": "0x" + "6" * 64,
            "block_number": 11,
            "block_hash": "0x" + "7" * 64,
            "log_index": 0,
            "confirmations": 12,
            "authorization_identity": "auth",
            "transfer_identity": "transfer",
            "payer": BUYER,
            "pay_to": PAYEE,
        }


def test_confirmed_operator_and_replay_share_one_settlement():
    store = FakeStore()
    external = FakeExternal()
    operator = P3Operator(store, external, now=lambda: NOW)
    first = operator.execute(grant(), payload(), subject_commit=COMMIT, subject_tree=TREE)
    second = operator.execute(grant(), payload(), subject_commit=COMMIT, subject_tree=TREE)
    assert first["status"] == "CONFIRMED"
    assert second["status"] == "CONFIRMED"
    assert external.calls.count("settle") == 1
    assert store.consumes == 1
    assert first["settlement_count"] == second["settlement_count"] == 1


def test_pending_is_spent_and_replay_is_confirm_only():
    store = FakeStore()
    external = FakeExternal(pending=True)
    operator = P3Operator(store, external, now=lambda: NOW)
    first = operator.execute(grant(), payload(), subject_commit=COMMIT, subject_tree=TREE)
    second = operator.execute(grant(), payload(), subject_commit=COMMIT, subject_tree=TREE)
    assert first["status"] == second["status"] == "UNKNOWN"
    assert external.calls.count("settle") == 1
    assert external.calls[-1] == "confirmation"


def test_preflight_performs_no_store_or_external_io():
    class Exploding:
        def __getattr__(self, name):
            raise AssertionError(name)

    result = P3Operator(Exploding(), Exploding(), now=lambda: NOW).preflight(
        grant(), payload(), subject_commit=COMMIT, subject_tree=TREE
    )
    assert result["external_calls"] == 0
    assert result["database_writes"] == 0
    assert result["migration_checksums"] == dict(REQUIRED_MIGRATIONS)


def test_wrong_migrations_fail_before_external_call():
    store = FakeStore()
    store.migrations = lambda: {**dict(REQUIRED_MIGRATIONS), "004_receipt_confirmation_provenance.sql": "0" * 64}
    external = FakeExternal()
    with pytest.raises(P3OperatorError, match="P3_MIGRATION_MISMATCH"):
        P3Operator(store, external, now=lambda: NOW).execute(
            grant(), payload(), subject_commit=COMMIT, subject_tree=TREE
        )
    assert external.calls == []


def test_payment_input_is_closed_and_never_accepts_private_key(tmp_path):
    path = tmp_path / "payment.json"
    path.write_text(json.dumps(payload()))
    path.chmod(0o600)
    assert load_payment_input(path)["buyer"] == BUYER
    value = payload()
    value["private_key"] = "forbidden"
    path.write_text(json.dumps(value))
    with pytest.raises(P3OperatorError, match="P3_PAYMENT_INPUT_INVALID"):
        load_payment_input(path)
