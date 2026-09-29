"""Closed live acceptance authority and injectable execution boundary."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta

from .public_read import PublicReadPlan


class LiveAuthorityError(ValueError):
    pass


OID = re.compile(r"[0-9a-f]{40}\Z")
DIGEST = re.compile(r"[0-9a-f]{64}\Z")


@dataclass(frozen=True)
class LivePlan:
    cases: dict[str, dict]
    digest: str

    @classmethod
    def canonical(cls):
        body = b'{"type":"l2Book","coin":"BTC"}'
        cases = {
            "A07": {
                "action": "public_read",
                "method": "POST",
                "url": "https://api.hyperliquid.xyz/info",
                "body_sha256": hashlib.sha256(body).hexdigest(),
                "timeout_seconds": 15,
                "max_response_bytes": 2097152,
                "maximum_attempts": 1,
            },
            "A29": {
                "action": "public_read",
                "method": "GET",
                "url": "https://github.com/Dimkox/liqvera.git/info/refs?service=git-upload-pack",
                "body_sha256": hashlib.sha256(b"").hexdigest(),
                "timeout_seconds": 15,
                "max_response_bytes": 2097152,
                "maximum_attempts": 1,
            },
            "A13": {
                "action": "testnet_payment",
                "cases": ["A13", "A14"],
                "network": "eip155:31611",
                "asset": "0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503",
                "amount_atomic": "10000000000000000",
                "maximum_settlement_submissions": 1,
                "max_gas_wei": "100000000000000",
            },
            "A14": {
                "action": "testnet_payment",
                "cases": ["A13", "A14"],
                "network": "eip155:31611",
                "asset": "0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503",
                "amount_atomic": "10000000000000000",
                "maximum_settlement_submissions": 1,
                "max_gas_wei": "100000000000000",
            },
        }
        digest = hashlib.sha256(
            json.dumps(cases, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        return cls(cases, digest)

    def grant(self, case):
        value = {
            **self.cases[case],
            "grant_id": "00000000-0000-4000-8000-000000000013"
            if case in {"A13", "A14"}
            else f"00000000-0000-4000-8000-0000000000{case[1:]}",
        }
        return value


@dataclass(frozen=True)
class CaseGrant:
    value: dict
    digest: str


@dataclass(frozen=True)
class LiveAuthority:
    plan: LivePlan
    expires_at: datetime
    cases: dict[str, CaseGrant]


def validate_live_bundle(raw, *, subject_commit, subject_tree, now):
    plan = LivePlan.canonical()
    if (
        not isinstance(raw, dict)
        or set(raw)
        != {"schema", "subject_commit", "subject_tree", "plan_sha256", "expires_at", "cases"}
        or raw.get("schema") != "liqvera-live-acceptance-grants/v1"
    ):
        raise LiveAuthorityError("LIVE_GRANT_INVALID")
    if (
        raw["subject_commit"] != subject_commit
        or raw["subject_tree"] != subject_tree
        or not OID.fullmatch(subject_commit)
        or not OID.fullmatch(subject_tree)
    ):
        raise LiveAuthorityError("LIVE_SUBJECT_MISMATCH")
    if raw["plan_sha256"] != plan.digest:
        raise LiveAuthorityError("LIVE_PLAN_MISMATCH")
    try:
        expiry = datetime.fromisoformat(raw["expires_at"].replace("Z", "+00:00"))
    except Exception:
        raise LiveAuthorityError("LIVE_GRANT_INVALID") from None
    if expiry <= now or expiry > now + timedelta(minutes=15):
        raise LiveAuthorityError("LIVE_GRANT_EXPIRED")
    if not isinstance(raw["cases"], dict) or set(raw["cases"]) != set(plan.cases):
        raise LiveAuthorityError("LIVE_GRANT_INVALID")
    grants = {}
    for case, expected in plan.cases.items():
        value = raw["cases"][case]
        if (
            not isinstance(value, dict)
            or {k: v for k, v in value.items() if k != "grant_id"} != expected
            or not re.fullmatch(r"[0-9a-f-]{36}", str(value.get("grant_id")))
        ):
            raise LiveAuthorityError("LIVE_CASE_GRANT_MISMATCH")
        grants[case] = CaseGrant(
            value,
            hashlib.sha256(
                json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest(),
        )
    if grants["A13"].value != grants["A14"].value:
        raise LiveAuthorityError("LIVE_PAYMENT_LINK_MISMATCH")
    return LiveAuthority(plan, expiry, grants)


def execute_live_cases(authority, public_executor, payment_executor, *, now):
    if now() >= authority.expires_at:
        raise LiveAuthorityError("LIVE_GRANT_EXPIRED")
    rows = {}
    for case in ("A07", "A29"):
        spec = authority.plan.cases[case]
        body = b'{"type":"l2Book","coin":"BTC"}' if case == "A07" else b""
        plan = PublicReadPlan(
            case,
            spec["method"],
            spec["url"],
            body,
            spec["timeout_seconds"],
            spec["max_response_bytes"],
            1,
        )
        rows[case] = public_executor.execute(case, authority.cases[case], plan)
    payment = payment_executor.execute(authority.cases["A13"])
    rows["A13"] = payment
    if payment.get("status") != "CONFIRMED":
        rows["A14"] = {"status": "BLOCKED_CONFIRM_ONLY", "settlement_count": 1}
    else:
        replay = payment_executor.replay(payment)
        if replay != {
            "tx_hash": payment["tx_hash"],
            "settlement_count": 1,
            "entitlement_reused": True,
        }:
            raise LiveAuthorityError("LIVE_PAYMENT_REPLAY_MISMATCH")
        rows["A14"] = replay
    return rows
