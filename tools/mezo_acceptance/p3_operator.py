"""One-shot P3 payment orchestration shared by the operator CLI and fake E2E tests."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path

from .live import ADDRESS, DIGEST, validate_p3_bundle


class P3OperatorError(ValueError):
    pass


REQUIRED_MIGRATIONS = (
    ("001_ledger.sql", "bc127e55c876961112f33ca2abdfac01827769d6156ddba2f42856d070c75b3b"),
    ("002_fix_immutable_ledger_identity.sql", "981f48215e64fdd0fb72be5a6df78238cf8050de722adb454b4e28b1940ccbcb"),
    ("003_live_grant_consumption.sql", "bbedff6137a648166b77233c56a466e46247480b404b8829b64f29123109bcf0"),
    ("004_receipt_confirmation_provenance.sql", "96bba00d344d81670a4c0f8741186004910e959f374ecd77ce78268d52fd465a"),
    ("005_receipt_confirmation_count.sql", "e99e5cffab60c08dfb1cd73d13caf2915f31aec542c26c87b016d0e125a23b11"),
)
PAYMENT_FIELDS = {
    "schema",
    "quote_id",
    "scope_hash",
    "report_id",
    "payment_signature",
    "buyer",
    "pay_to",
}


def _safe_json(path: Path, maximum: int = 65536):
    info = os.lstat(path)
    if (
        not stat.S_ISREG(info.st_mode)
        or info.st_nlink != 1
        or stat.S_IMODE(info.st_mode) & 0o077
        or not 0 < info.st_size <= maximum
    ):
        raise P3OperatorError("P3_INPUT_UNSAFE")
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        opened = os.fstat(descriptor)
        raw = os.read(descriptor, maximum + 1)
    finally:
        os.close(descriptor)
    if (opened.st_dev, opened.st_ino, opened.st_size) != (info.st_dev, info.st_ino, info.st_size):
        raise P3OperatorError("P3_INPUT_UNSAFE")
    return json.loads(raw)


def load_payment_input(path: Path):
    raw = _safe_json(path)
    if (
        not isinstance(raw, dict)
        or set(raw) != PAYMENT_FIELDS
        or raw.get("schema") != "liqvera-p3-signed-payment/v1"
        or not DIGEST.fullmatch(str(raw.get("scope_hash")))
        or not ADDRESS.fullmatch(str(raw.get("buyer")))
        or not ADDRESS.fullmatch(str(raw.get("pay_to")))
        or raw["buyer"] == raw["pay_to"]
        or not isinstance(raw.get("payment_signature"), str)
        or not 1 <= len(raw["payment_signature"]) <= 16384
    ):
        raise P3OperatorError("P3_PAYMENT_INPUT_INVALID")
    return raw


def grant_digest(authority):
    raw = authority.cases["A13"].value
    return hashlib.sha256(
        json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


class P3Operator:
    """Coordinates exact authorization, durable consumption and confirm-only replay.

    Store implementations own the transaction which consumes a grant and moves
    its immutable payment attempt to SUBMITTING. External implementations are
    bounded facilitator/RPC adapters. No method retries settlement.
    """

    def __init__(self, store, external, *, now):
        self.store = store
        self.external = external
        self.now = now

    def _validate(self, bundle, payment, subject_commit, subject_tree):
        authority = validate_p3_bundle(
            bundle,
            subject_commit=subject_commit,
            subject_tree=subject_tree,
            now=self.now(),
        )
        grant = authority.cases["A13"].value
        if (
            not isinstance(payment, dict)
            or set(payment) != PAYMENT_FIELDS
            or payment.get("schema") != "liqvera-p3-signed-payment/v1"
            or payment.get("buyer") != grant["buyer"]
            or payment.get("pay_to") != grant["pay_to"]
            or not DIGEST.fullmatch(str(payment.get("scope_hash")))
            or not isinstance(payment.get("payment_signature"), str)
            or not 1 <= len(payment["payment_signature"]) <= 16384
        ):
            raise P3OperatorError("P3_PAYMENT_INPUT_INVALID")
        return authority, grant

    def preflight(self, bundle, payment, *, subject_commit, subject_tree):
        authority, grant = self._validate(bundle, payment, subject_commit, subject_tree)
        return {
            "schema": "liqvera-p3-preflight/v1",
            "subject_commit": subject_commit,
            "subject_tree": subject_tree,
            "plan_sha256": authority.plan.digest,
            "grant_id": grant["grant_id"],
            "grant_digest": grant_digest(authority),
            "buyer": grant["buyer"],
            "pay_to": grant["pay_to"],
            "network": grant["network"],
            "asset": grant["asset"],
            "amount_atomic": grant["amount_atomic"],
            "maximum_settlement_submissions": 1,
            "max_buyer_native_gas_wei": grant["max_buyer_native_gas_wei"],
            "facilitator_url": grant["facilitator_url"],
            "rpc_url": grant["rpc_url"],
            "database_identity_kind": grant["database_identity_kind"],
            "database_host_policy": grant["database_host_policy"],
            "database_identity": grant["database_identity"],
            "migration_checksums": dict(REQUIRED_MIGRATIONS),
            "external_calls": 0,
            "database_writes": 0,
        }

    def _check_migrations(self):
        if self.store.migrations() != dict(REQUIRED_MIGRATIONS):
            raise P3OperatorError("P3_MIGRATION_MISMATCH")

    def execute(self, bundle, payment, *, subject_commit, subject_tree):
        authority, grant = self._validate(bundle, payment, subject_commit, subject_tree)
        self._check_migrations()  # Must precede every external call.
        digest = grant_digest(authority)
        existing = self.store.existing(digest)
        if existing is not None:
            return self._reconcile(existing, digest, grant, payment)
        before = self.external.snapshot(grant["buyer"])
        verified = self.external.verify(payment)
        durable_payment = {**payment, **verified, "before": before}
        if not self.store.consume_and_mark_submitting(
            digest, grant["grant_id"], durable_payment
        ):
            existing = self.store.existing(digest)
            if existing is None:
                raise P3OperatorError("P3_CONSUMPTION_CONFLICT")
            return self._reconcile(existing, digest, grant, payment)
        settled = self.external.settle(payment)
        tx_hash = settled.get("tx_hash")
        self.store.mark_unknown(tx_hash)
        state = self.store.existing(digest)
        return self._reconcile(state, digest, grant, payment)

    def _reconcile(self, state, digest, grant, payment):
        if state["state"] == "CONFIRMED":
            return {**state, "grant_digest": digest, "settlement_count": 1}
        tx_hash = state.get("tx_hash")
        confirmation = self.external.confirmation(tx_hash, state)
        if confirmation is None:
            return {
                "schema": "liqvera-p3-payment-observation/v1",
                "status": "UNKNOWN",
                "grant_id": grant["grant_id"],
                "grant_digest": digest,
                "tx_hash": tx_hash,
                "settlement_count": 1,
                "retry_allowed": False,
            }
        required = {
            "tx_hash",
            "transaction_from",
            "buyer_native_balance_before",
            "buyer_native_balance_after",
            "buyer_native_gas_spent",
            "observation_before_block_number",
            "observation_before_block_hash",
            "observation_after_block_number",
            "observation_after_block_hash",
            "block_number",
            "block_hash",
            "log_index",
            "confirmations",
            "authorization_identity",
            "transfer_identity",
            "payer",
            "pay_to",
        }
        if (
            set(confirmation) != required
            or confirmation["tx_hash"] != tx_hash
            or confirmation["payer"] != grant["buyer"]
            or confirmation["pay_to"] != grant["pay_to"]
            or confirmation["transaction_from"].lower() == grant["buyer"].lower()
            or confirmation["buyer_native_balance_before"]
            != confirmation["buyer_native_balance_after"]
            or confirmation["buyer_native_gas_spent"] != "0"
            or confirmation["confirmations"] < 12
        ):
            raise P3OperatorError("P3_CONFIRMATION_MISMATCH")
        observation = {
            "schema": "liqvera-p3-payment-observation/v1",
            "status": "CONFIRMED",
            "grant_id": grant["grant_id"],
            "grant_digest": digest,
            "settlement_count": 1,
            "retry_allowed": False,
            **confirmation,
        }
        self.store.confirm(observation)
        return observation
