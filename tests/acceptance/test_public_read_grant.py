from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from tools.mezo_acceptance.public_read import GrantError, PublicReadGrant, PublicReadPlan, execute_public_read, validate_public_read_evidence


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
        maximum_attempts=1,
    )


def grant(**changes: object) -> dict[str, object]:
    value: dict[str, object] = {
        "schema": "liqvera-public-read-grant/v1",
        "grant_id": "00000000-0000-4000-8000-000000000007",
        "subject_commit": COMMIT,
        "subject_tree": TREE,
        "plan_sha256": plan().digest,
        "case": "A07",
        "method": "POST",
        "url": "https://api.hyperliquid.xyz/info",
        "expires_at": (NOW + timedelta(minutes=5)).isoformat().replace("+00:00", "Z"),
        "maximum_attempts": 1,
        "timeout_seconds": 15,
        "max_response_bytes": 2_097_152,
        "body_sha256": "74e1560af7031d150e32c06ab991dd688096266396d5f0cf9d1ad8e02238e2a5",
    }
    value.update(changes)
    return value


def test_exact_short_lived_grant_binds_subject_plan_and_request() -> None:
    parsed = PublicReadGrant.parse(grant(), now=NOW)
    parsed.authorize(plan(), subject_commit=COMMIT, subject_tree=TREE, now=NOW)


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
    kwargs = {"subject_commit": COMMIT, "subject_tree": TREE}
    if field == "plan_sha256":
        object.__setattr__(parsed, "plan_sha256", value)
    else:
        kwargs[field] = value
    with pytest.raises(GrantError, match="^PUBLIC_READ_GRANT_MISMATCH$"):
        parsed.authorize(plan(), now=NOW, **kwargs)


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
    assert validate_public_read_evidence(parsed, evidence, environ={}, now=NOW)["response_sha256"] == "d" * 64
    with pytest.raises(GrantError, match="^PUBLIC_READ_REDIRECT_BLOCKED$"):
        validate_public_read_evidence(parsed, {**evidence, "final_url": "https://example.com/"}, environ={}, now=NOW)
    with pytest.raises(GrantError, match="^PUBLIC_READ_RESPONSE_TOO_LARGE$"):
        validate_public_read_evidence(parsed, {**evidence, "response_bytes": 3_000_000}, environ={}, now=NOW)
    with pytest.raises(GrantError, match="^PUBLIC_READ_AMBIENT_AUTHORITY$"):
        validate_public_read_evidence(parsed, evidence, environ={"HTTPS_PROXY": "http://proxy.invalid"}, now=NOW)


def test_executor_sends_exact_body_once_streams_with_cap_and_consumes(tmp_path) -> None:
    parsed = PublicReadGrant.parse(grant(), now=NOW)
    seen: list[tuple[str, str, bytes, dict[str, str]]] = []
    class Response:
        status=200
        reads=0
        def getheader(self, name: str): return None
        def read(self, amount: int):
            self.reads+=1
            return b'{"ok":true}' if self.reads==1 else b""
    class Connection:
        def request(self, method: str, path: str, body: bytes, headers: dict[str,str]):
            seen.append((method,path,body,{**headers,"read":""}))
        def getresponse(self): return Response()
        def close(self): pass
    evidence=execute_public_read(plan(),parsed,subject_commit=COMMIT,subject_tree=TREE,now=lambda:NOW,
        environ={},resolver=lambda host:("8.8.8.8",),connection=lambda host,ip,timeout:Connection(),state_dir=tmp_path)
    assert evidence["attempts"]==1 and seen[0][:3]==("POST","/info",plan().body)
    with pytest.raises(GrantError,match="^PUBLIC_READ_GRANT_ALREADY_CONSUMED$"):
        execute_public_read(plan(),parsed,subject_commit=COMMIT,subject_tree=TREE,now=lambda:NOW,
            environ={},resolver=lambda host:("8.8.8.8",),connection=lambda host,ip,timeout:Connection(),state_dir=tmp_path)


def test_executor_derives_replay_marker_and_rejects_caller_selected_path(tmp_path) -> None:
    parsed = PublicReadGrant.parse(grant(), now=NOW)
    assert parsed.digest == PublicReadGrant.parse(grant(), now=NOW).digest
    with pytest.raises(TypeError, match="consumption_path"):
        execute_public_read(plan(), parsed, subject_commit=COMMIT, subject_tree=TREE, now=lambda: NOW,
            environ={}, resolver=lambda host: ("8.8.8.8",), connection=lambda *args: None,
            state_dir=tmp_path, consumption_path=tmp_path / "alternate")


def test_executor_rechecks_expiry_and_dns_before_send(tmp_path) -> None:
    parsed=PublicReadGrant.parse(grant(),now=NOW)
    later=NOW+timedelta(minutes=6)
    with pytest.raises(GrantError,match="^PUBLIC_READ_GRANT_EXPIRED$"):
        execute_public_read(plan(),parsed,subject_commit=COMMIT,subject_tree=TREE,now=lambda:later,
            environ={},resolver=lambda host:("8.8.8.8",),connection=lambda *args:None,state_dir=tmp_path)
