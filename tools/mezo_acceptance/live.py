"""Closed live acceptance authority and injectable execution boundary."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta

from .public_read import PublicReadGrant, PublicReadPlan


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
        body = b'{"scenario":"source-unavailable","fallback":"forbidden"}'
        cases = {
            "A07": {
                "action": "gateway_source_unavailable_harness",
                "method": "LOCAL_POST",
                "url": "https://source.invalid/internal/v1/reports",
                "body_sha256": hashlib.sha256(body).hexdigest(),
                "timeout_seconds": 15,
                "max_response_bytes": 2097152,
                "maximum_attempts": 1,
            },
            "A29": {
                "action": "anonymous_clone",
                "method": "GIT_CLONE",
                "url": "https://github.com/Dimkox/liqvera.git",
                "body_sha256": hashlib.sha256(b"").hexdigest(),
                "timeout_seconds": 15,
                "max_response_bytes": 52428800,
                "maximum_attempts": 1,
            },
            "A13": {
                "network": "eip155:31611",
                "chain_id": 31611,
                "asset": "0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503",
                "amount_atomic": "10000000000000000",
                "maximum_settlement_submissions": 1,
                "max_gas_wei": "100000000000000",
            },
            "A14": {
                "network": "eip155:31611",
                "chain_id": 31611,
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

    def public_grant(self, case: str, *, now: datetime) -> PublicReadGrant:
        value = self.cases[case].value
        return PublicReadGrant.parse(
            {
                "schema": "liqvera-public-read-grant/v1",
                "grant_id": value["grant_id"],
                "subject_commit": value["subject_commit"],
                "subject_tree": value["subject_tree"],
                "plan_sha256": value["plan_sha256"],
                "case": case,
                "method": value["method"],
                "url": value["url"],
                "expires_at": value["expires_at"],
                "maximum_attempts": value["maximum_attempts"],
                "timeout_seconds": value["timeout_seconds"],
                "max_response_bytes": value["max_response_bytes"],
                "body_sha256": value["body_sha256"],
            },
            now=now,
        )


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
        binding = {
            "subject_commit": raw["subject_commit"],
            "subject_tree": raw["subject_tree"],
            "plan_sha256": PublicReadPlan(
                case,
                expected["method"],
                expected["url"],
                b'{"scenario":"source-unavailable","fallback":"forbidden"}' if case == "A07" else b"",
                expected["timeout_seconds"],
                expected["max_response_bytes"],
                expected["maximum_attempts"],
            ).digest,
            "expires_at": raw["expires_at"],
        } if case in {"A07", "A29"} else {
            "schema": "liqvera-live-payment-grant/v1",
            "subject_commit": raw["subject_commit"],
            "subject_tree": raw["subject_tree"],
            "plan_sha256": raw["plan_sha256"],
            "expires_at": raw["expires_at"],
        }
        permitted = {"grant_id", *binding, *expected}
        if case in {"A13", "A14"}:
            permitted |= {"buyer", "pay_to"}
        if (
            not isinstance(value, dict)
            or set(value) != permitted
            or {k: v for k, v in value.items() if k in expected} != expected
            or any(value.get(k) != v for k, v in binding.items())
            or not re.fullmatch(r"[0-9a-f-]{36}", str(value.get("grant_id")))
            or (case in {"A13", "A14"} and (
                not re.fullmatch(r"0x[0-9a-fA-F]{40}", str(value.get("buyer")))
                or not re.fullmatch(r"0x[0-9a-fA-F]{40}", str(value.get("pay_to")))
                or value["buyer"].lower() == value["pay_to"].lower()
            ))
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
        body = b'{"scenario":"source-unavailable","fallback":"forbidden"}' if case == "A07" else b""
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
