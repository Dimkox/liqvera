from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from scripts import claw_host_deployment_client as client
from scripts import claw_host_deployment_controller as controller
from scripts.claw_host_deployment_contract import canonical_bytes
from scripts.claw_host_deployment_controller import (
    ControllerError,
    RequestRegistry,
    encode_frame,
    read_frame,
)


def request(token: str | None = None, action: str = "status") -> dict[str, object]:
    return {
        "schema_version": "claw-host-deployment-request-v1",
        "action": action,
        "github_token": token,
        "repository": "Dimkox/multi-exchange-engine",
        "approval_comment_id": None,
        "release_id": None,
        "transaction_id": "d" * 32,
    }


def test_frame_rejects_trailing_short_and_oversized_input() -> None:
    payload = canonical_bytes(request())
    assert read_frame(io.BytesIO(encode_frame(payload)), reject_trailing=True) == payload
    with pytest.raises(ControllerError, match="FRAME_TRAILING"):
        read_frame(io.BytesIO(encode_frame(payload) + b"x"), reject_trailing=True)
    with pytest.raises(ControllerError, match="FRAME_HEADER"):
        read_frame(io.BytesIO(b"\x00\x01"), reject_trailing=True)
    with pytest.raises(ControllerError, match="FRAME_SIZE"):
        read_frame(io.BytesIO((32769).to_bytes(4, "big")), reject_trailing=True)


def test_live_controller_enforces_trailing_rejection() -> None:
    source = Path("scripts/claw_host_deployment_controller.py").read_text()
    assert 'read_frame(inherited.makefile("rb"), reject_trailing=True)' in source
    assert 'read_frame(inherited.makefile("rb"), reject_trailing=False)' not in source


def test_client_rejects_every_argument_before_socket_access(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(client.os, "geteuid", lambda: 0, raising=False)
    assert client.main(["unexpected"]) == 2


def test_registry_never_persists_or_returns_token(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    token = "sentinel-token-never-persist"
    calls: list[str] = []

    def dispatch(value):
        calls.append(value.action)
        return {
            "schema_version": "claw-host-deployment-response-v1",
            "authority": "NONE",
            "action": value.action,
            "transaction_id": value.transaction_id,
            "state": "COMMITTED",
            "receipt_sha256": None,
        }

    registry = RequestRegistry(tmp_path)
    first = registry.handle(canonical_bytes(request(token, "finalize")), dispatch)
    second = registry.handle(canonical_bytes(request(token, "finalize")), dispatch)
    assert first == second
    assert calls == ["finalize", "finalize"]
    assert not list((tmp_path / "requests").glob("*.json"))
    assert token not in json.dumps(first)
    assert token not in capsys.readouterr().out + capsys.readouterr().err
    for path in tmp_path.rglob("*"):
        if path.is_file():
            assert token.encode() not in path.read_bytes()


def test_registry_rejects_wrong_repository_before_replay(tmp_path: Path) -> None:
    registry = RequestRegistry(tmp_path)
    dispatch = lambda value: {
        "schema_version": "claw-host-deployment-response-v1",
        "authority": "NONE",
        "action": value.action,
        "transaction_id": value.transaction_id,
        "state": "COMMITTED",
        "receipt_sha256": None,
    }
    registry.handle(canonical_bytes(request()), dispatch)
    changed = request()
    changed["repository"] = "other/repository"
    with pytest.raises(ControllerError, match="REQUEST_REPOSITORY"):
        registry.handle(canonical_bytes(changed), dispatch)


def test_response_contract_is_recursively_closed(tmp_path: Path) -> None:
    registry = RequestRegistry(tmp_path)
    with pytest.raises(ControllerError, match="RESPONSE_FIELDS"):
        registry.handle(canonical_bytes(request()), lambda _: {"state": "OBSERVED", "extra": True})


def test_response_schema_matches_runtime_contract() -> None:
    schema = json.loads(Path("schemas/claw-host-deployment-response-v1.schema.json").read_text())
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(schema["properties"])
    assert schema["properties"]["authority"] == {"const": "NONE"}
    assert set(schema["properties"]["state"]["enum"]) == controller.RESPONSE_STATES


def test_rollback_blocked_response_is_not_cached_and_can_retry(tmp_path: Path) -> None:
    value = request()
    value["action"] = "rollback"
    calls = 0

    def dispatch(request_value):
        nonlocal calls
        calls += 1
        return {
            "schema_version": "claw-host-deployment-response-v1",
            "authority": "NONE",
            "action": request_value.action,
            "transaction_id": request_value.transaction_id,
            "state": "ROLLBACK_BLOCKED" if calls == 1 else "ROLLED_BACK",
            "receipt_sha256": None if calls == 1 else "c" * 64,
        }

    registry = RequestRegistry(tmp_path)
    first = registry.handle(canonical_bytes(value), dispatch)
    second = registry.handle(canonical_bytes(value), dispatch)
    assert first["state"] == "ROLLBACK_BLOCKED"
    assert second["state"] == "ROLLED_BACK"
    assert calls == 2


def test_registry_never_returns_stale_committed_response_after_rollback(tmp_path: Path) -> None:
    value = request()
    value["action"] = "finalize"
    value["github_token"] = "memory-only-token"
    states = iter(("COMMITTED", "ROLLED_BACK"))

    def dispatch(request_value):
        state = next(states)
        return {
            "schema_version": "claw-host-deployment-response-v1",
            "authority": "NONE",
            "action": request_value.action,
            "transaction_id": request_value.transaction_id,
            "state": state,
            "receipt_sha256": "c" * 64,
        }

    registry = RequestRegistry(tmp_path)
    assert registry.handle(canonical_bytes(value), dispatch)["state"] == "COMMITTED"
    assert registry.handle(canonical_bytes(value), dispatch)["state"] == "ROLLED_BACK"
    assert not list((tmp_path / "requests").glob("*.json"))
