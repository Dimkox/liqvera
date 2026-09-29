from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from tools.mezo_acceptance.public_read import GrantError, PublicReadGrant, PublicReadPlan, validate_public_read_evidence


NOW = datetime(2026, 9, 29, 14, 0, tzinfo=timezone.utc)
COMMIT = "a" * 40
TREE = "b" * 40
PLAN = "c" * 64


def plan() -> PublicReadPlan:
    return PublicReadPlan(
        case="A07",
        method="POST",
        url="https://api.hyperliquid.xyz/info",
        body=b'{"type":"l2Book","coin":"BTC"}',
        timeout_seconds=15,
        max_response_bytes=2_097_152,
        maximum_attempts=2,
    )


def grant(**changes: object) -> dict[str, object]:
    value: dict[str, object] = {
        "schema": "liqvera-public-read-grant/v1",
        "subject_commit": COMMIT,
        "subject_tree": TREE,
        "plan_sha256": PLAN,
        "case": "A07",
        "method": "POST",
        "url": "https://api.hyperliquid.xyz/info",
        "expires_at": (NOW + timedelta(minutes=5)).isoformat().replace("+00:00", "Z"),
        "maximum_attempts": 2,
        "timeout_seconds": 15,
        "max_response_bytes": 2_097_152,
    }
    value.update(changes)
    return value


def test_exact_short_lived_grant_binds_subject_plan_and_request() -> None:
    parsed = PublicReadGrant.parse(grant(), now=NOW)
    parsed.authorize(plan(), subject_commit=COMMIT, subject_tree=TREE, plan_sha256=PLAN)


@pytest.mark.parametrize(
    "changes,reason",
    [
        ({"url": "http://api.hyperliquid.xyz/info"}, "PUBLIC_READ_TLS_REQUIRED"),
        ({"url": "https://127.0.0.1/info"}, "PUBLIC_READ_DESTINATION_FORBIDDEN"),
        ({"url": "https://api.hyperliquid.xyz/other"}, "PUBLIC_READ_DESTINATION_FORBIDDEN"),
        ({"method": "GET"}, "PUBLIC_READ_DESTINATION_FORBIDDEN"),
        ({"expires_at": NOW.isoformat().replace("+00:00", "Z")}, "PUBLIC_READ_GRANT_EXPIRED"),
        ({"extra": True}, "PUBLIC_READ_GRANT_INVALID"),
    ],
)
def test_grant_rejects_broadened_or_expired_authority(changes: dict[str, object], reason: str) -> None:
    with pytest.raises(GrantError, match=f"^{reason}$"):
        PublicReadGrant.parse(grant(**changes), now=NOW)


@pytest.mark.parametrize("field,value", [("subject_commit", "d" * 40), ("subject_tree", "d" * 40), ("plan_sha256", "d" * 64)])
def test_grant_rejects_changed_subject_or_plan(field: str, value: str) -> None:
    parsed = PublicReadGrant.parse(grant(), now=NOW)
    kwargs = {"subject_commit": COMMIT, "subject_tree": TREE, "plan_sha256": PLAN}
    kwargs[field] = value
    with pytest.raises(GrantError, match="^PUBLIC_READ_GRANT_MISMATCH$"):
        parsed.authorize(plan(), **kwargs)


def test_resolution_must_stay_public_and_stable() -> None:
    parsed = PublicReadGrant.parse(grant(), now=NOW)
    parsed.validate_resolution(("8.8.8.8",), ("8.8.8.8",))
    with pytest.raises(GrantError, match="^PUBLIC_READ_PRIVATE_ADDRESS$"):
        parsed.validate_resolution(("127.0.0.1",), ("127.0.0.1",))
    with pytest.raises(GrantError, match="^PUBLIC_READ_DNS_REBINDING$"):
        parsed.validate_resolution(("8.8.8.8",), ("8.8.4.4",))


def test_result_evidence_rejects_redirect_oversize_and_ambient_proxy() -> None:
    parsed = PublicReadGrant.parse(grant(), now=NOW)
    evidence = {"status": 200, "final_url": parsed.url, "response_bytes": 12, "response_sha256": "d" * 64,
                "resolved_addresses": ["8.8.8.8"], "connected_address": "8.8.8.8", "attempts": 1}
    assert validate_public_read_evidence(parsed, evidence, environ={})["response_sha256"] == "d" * 64
    with pytest.raises(GrantError, match="^PUBLIC_READ_REDIRECT_BLOCKED$"):
        validate_public_read_evidence(parsed, {**evidence, "final_url": "https://example.com/"}, environ={})
    with pytest.raises(GrantError, match="^PUBLIC_READ_RESPONSE_TOO_LARGE$"):
        validate_public_read_evidence(parsed, {**evidence, "response_bytes": 3_000_000}, environ={})
    with pytest.raises(GrantError, match="^PUBLIC_READ_AMBIENT_AUTHORITY$"):
        validate_public_read_evidence(parsed, evidence, environ={"HTTPS_PROXY": "http://proxy.invalid"})
