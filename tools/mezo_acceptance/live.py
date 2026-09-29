"""Least-authority P2/P3 acceptance grant contracts."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

from .public_read import PublicReadGrant, PublicReadPlan


class LiveAuthorityError(ValueError):
    pass


OID = re.compile(r"[0-9a-f]{40}\Z")
DIGEST = re.compile(r"[0-9a-f]{64}\Z")
ADDRESS = re.compile(r"0x[0-9a-f]{40}\Z")


def _digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _expiry(raw, now):
    try:
        value = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        raise LiveAuthorityError("LIVE_GRANT_INVALID") from None
    if value <= now or value > now + timedelta(minutes=15):
        raise LiveAuthorityError("LIVE_GRANT_EXPIRED")
    return value


@dataclass(frozen=True)
class P2Plan:
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
                "url": "https://github.com/Dimkox/liqvera.git",
                "timeout_seconds": 15,
                "max_aggregate_disk_bytes": 52428800,
                "max_single_file_bytes": 26214400,
                "max_process_memory_bytes": 536870912,
                "max_output_bytes": 65536,
                "maximum_attempts": 1,
                "network_byte_limit_enforced": False,
            },
        }
        return cls(cases, _digest(cases))


@dataclass(frozen=True)
class P3Plan:
    cases: dict[str, dict]
    digest: str

    @classmethod
    def canonical(cls):
        payment = {
            "scheme": "exact",
            "settlement_broadcaster": "facilitator",
            "network": "eip155:31611",
            "chain_id": 31611,
            "asset": "0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503",
            "amount_atomic": "10000000000000000",
            "maximum_settlement_submissions": 1,
            "max_buyer_native_gas_wei": "100000000000000",
            "asset_transfer_method": "permit2",
            "permit2_address": "0x000000000022D473030F116dDEE9F6B43aC78BA3",
            "permit2_proxy": "0x402085c248EeA27D92E8b30b2C58ed07f9E20001",
            "approval_mode": "eip2612-gas-sponsoring",
            "required_extension": "eip2612GasSponsoring",
            "authorization_identity_version": "liqvera-permit2-eip2612-identity/v1",
            "facilitator_url": "https://facilitator.vativ.io/",
            "rpc_url": "https://rpc.test.mezo.org/",
            "database_identity_kind": "sha256-credential-free-postgresql-endpoint/v1",
            "database_host_policy": "loopback-only/v1",
        }
        cases = {"A13": payment, "A14": payment}
        return cls(cases, _digest(cases))


@dataclass(frozen=True)
class CaseGrant:
    value: dict
    digest: str


@dataclass(frozen=True)
class P2Authority:
    plan: P2Plan
    expires_at: datetime
    journal_id: str
    journal_sha256: str
    cases: dict[str, CaseGrant]

    def a07_grant(self, *, now):
        value = self.cases["A07"].value
        return PublicReadGrant.parse(
            {
                "schema": "liqvera-public-read-grant/v1",
                **{
                    key: value[key]
                    for key in (
                        "grant_id",
                        "journal_id",
                        "journal_sha256",
                        "subject_commit",
                        "subject_tree",
                        "plan_sha256",
                        "method",
                        "url",
                        "expires_at",
                        "maximum_attempts",
                        "timeout_seconds",
                        "max_response_bytes",
                        "body_sha256",
                    )
                },
                "case": "A07",
            },
            now=now,
        )


@dataclass(frozen=True)
class P3Authority:
    plan: P3Plan
    expires_at: datetime
    cases: dict[str, CaseGrant]


def _base(raw, schema, cases, digest, subject_commit, subject_tree, now, extra=frozenset()):
    fields = {
        "schema",
        "subject_commit",
        "subject_tree",
        "plan_sha256",
        "expires_at",
        "cases",
    } | set(extra)
    if not isinstance(raw, dict) or set(raw) != fields or raw.get("schema") != schema:
        raise LiveAuthorityError("LIVE_GRANT_INVALID")
    if (
        (raw["subject_commit"], raw["subject_tree"]) != (subject_commit, subject_tree)
        or not OID.fullmatch(subject_commit)
        or not OID.fullmatch(subject_tree)
    ):
        raise LiveAuthorityError("LIVE_SUBJECT_MISMATCH")
    if raw["plan_sha256"] != digest:
        raise LiveAuthorityError("LIVE_PLAN_MISMATCH")
    expiry = _expiry(raw["expires_at"], now)
    if not isinstance(raw["cases"], dict) or set(raw["cases"]) != cases:
        raise LiveAuthorityError("LIVE_GRANT_INVALID")
    return expiry


def validate_p2_bundle(raw, *, subject_commit, subject_tree, now):
    plan = P2Plan.canonical()
    expiry = _base(
        raw,
        "liqvera-p2-acceptance-grants/v1",
        {"A07", "A29"},
        plan.digest,
        subject_commit,
        subject_tree,
        now,
        {"journal_id", "journal_sha256"},
    )
    try:
        if str(uuid.UUID(raw["journal_id"])) != raw["journal_id"]:
            raise ValueError
    except (ValueError, TypeError):
        raise LiveAuthorityError("LIVE_JOURNAL_INVALID") from None
    if not isinstance(raw["journal_sha256"], str) or not DIGEST.fullmatch(raw["journal_sha256"]):
        raise LiveAuthorityError("LIVE_JOURNAL_INVALID")
    grants = {}
    for case, expected in plan.cases.items():
        value = raw["cases"][case]
        common = {
            "grant_id",
            "journal_id",
            "journal_sha256",
            "subject_commit",
            "subject_tree",
            "plan_sha256",
            "expires_at",
        }
        if not isinstance(value, dict) or set(value) != set(expected) | common:
            raise LiveAuthorityError("LIVE_CASE_GRANT_MISMATCH")
        case_digest = (
            _digest(expected)
            if case == "A29"
            else PublicReadPlan(
                "A07",
                expected["method"],
                expected["url"],
                b'{"scenario":"source-unavailable","fallback":"forbidden"}',
                expected["timeout_seconds"],
                expected["max_response_bytes"],
                1,
            ).digest
        )
        binding = {
            "journal_id": raw["journal_id"],
            "journal_sha256": raw["journal_sha256"],
            "subject_commit": subject_commit,
            "subject_tree": subject_tree,
            "plan_sha256": case_digest,
            "expires_at": raw["expires_at"],
        }
        if any(value.get(k) != v for k, v in {**expected, **binding}.items()):
            raise LiveAuthorityError("LIVE_CASE_GRANT_MISMATCH")
        try:
            if str(uuid.UUID(value["grant_id"])) != value["grant_id"]:
                raise ValueError
        except (ValueError, TypeError):
            raise LiveAuthorityError("LIVE_CASE_GRANT_MISMATCH") from None
        grants[case] = CaseGrant(value, _digest(value))
    return P2Authority(plan, expiry, raw["journal_id"], raw["journal_sha256"], grants)


def validate_p3_bundle(raw, *, subject_commit, subject_tree, now):
    plan = P3Plan.canonical()
    expiry = _base(
        raw,
        "liqvera-p3-payment-grants/v1",
        {"A13", "A14"},
        plan.digest,
        subject_commit,
        subject_tree,
        now,
    )
    grants = {}
    for case in ("A13", "A14"):
        value = raw["cases"][case]
        expected = {
            "schema": "liqvera-mezo-payment-grant/v1",
            "subject_commit": subject_commit,
            "subject_tree": subject_tree,
            "plan_sha256": plan.digest,
            "expires_at": raw["expires_at"],
            **plan.cases[case],
        }
        if (
            not isinstance(value, dict)
            or set(value) != set(expected) | {"grant_id", "buyer", "pay_to", "database_identity"}
            or any(value.get(k) != v for k, v in expected.items())
            or not ADDRESS.fullmatch(str(value.get("buyer")))
            or not ADDRESS.fullmatch(str(value.get("pay_to")))
            or value["buyer"].lower() == value["pay_to"].lower()
            or not DIGEST.fullmatch(str(value.get("database_identity")))
        ):
            raise LiveAuthorityError("LIVE_CASE_GRANT_MISMATCH")
        try:
            if str(uuid.UUID(value["grant_id"])) != value["grant_id"]:
                raise ValueError
        except (ValueError, TypeError):
            raise LiveAuthorityError("LIVE_CASE_GRANT_MISMATCH") from None
        grants[case] = CaseGrant(value, _digest(value))
    if grants["A13"].value != grants["A14"].value:
        raise LiveAuthorityError("LIVE_PAYMENT_LINK_MISMATCH")
    return P3Authority(plan, expiry, grants)
