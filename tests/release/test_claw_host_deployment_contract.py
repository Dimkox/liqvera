from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest

from scripts.claw_host_deployment_contract import (
    ApprovalError,
    ContractError,
    canonical_bytes,
    load_closed_bytes,
    verify_approval,
    verify_d0_approval,
    verify_legacy_recovery_approval,
    verify_request,
)


SHA = "a" * 40
TREE = "b" * 40
DIGEST = "c" * 64
NOW = dt.datetime(2026, 8, 13, 9, 30, tzinfo=dt.timezone.utc)


def valid_request(action: str = "begin") -> dict[str, object]:
    begin = action == "begin"
    return {
        "schema_version": "claw-host-deployment-request-v1",
        "action": action,
        "github_token": "ephemeral-test-token" if action in {"begin", "finalize"} else None,
        "repository": "Dimkox/multi-exchange-engine",
        "approval_comment_id": 100 if begin else None,
        "release_id": 200 if begin else None,
        "transaction_id": None if begin else "d" * 32,
    }


def installed_identity() -> dict[str, object]:
    return {
        "schema_version": "claw-host-deployment-installed-v1",
        "repository": "Dimkox/multi-exchange-engine",
        "default_branch": "main",
        "controller_sha": SHA,
        "controller_tree": TREE,
    }


def approval_body() -> dict[str, object]:
    return {
        "schema_version": "claw-host-deployment-approval-v1",
        "decision": "APPROVE_CLAW_HOST_TRANSITION",
        "repository": "Dimkox/multi-exchange-engine",
        "source_sha": SHA,
        "source_tree": TREE,
        "policy_sha256": DIGEST,
        "closure_sha256": "d" * 64,
        "oci_archive_sha256": "e" * 64,
        "oci_archive_size": 25_295_872,
        "oci_archive_format": "docker-archive",
        "image_manifest_digest": "sha256:" + "f" * 64,
        "host_inventory_sha256": "1" * 64,
        "host_inventory_observed_at": "2026-08-13T09:00:00Z",
        "bundle_manifest_sha256": "2" * 64,
        "release_id": 200,
        "release_tag": "claw-host-inputs-2026-08-13",
        "assets": [
            {
                "id": 502,
                "name": "podman_4.9.3_amd64.deb",
                "role": "deb:podman",
                "size": 1024,
                "sha256": "3" * 64,
            },
            {
                "id": 503,
                "name": "claw-host-inventory.json",
                "role": "host_inventory",
                "size": 2048,
                "sha256": "1" * 64,
            },
            {
                "id": 501,
                "name": "actionlint-linux-amd64.tar",
                "role": "oci_archive",
                "size": 25_295_872,
                "sha256": "e" * 64,
            },
        ],
        "rollback_deadline_seconds": 900,
        "expires_at": "2026-08-13T10:00:00Z",
        "nonce": "A" * 43,
    }


def approval_comment(body: dict[str, object] | None = None) -> dict[str, object]:
    body = approval_body() if body is None else body
    return {
        "id": 100,
        "user": {"login": "Dimkox", "id": 42},
        "author_association": "OWNER",
        "created_at": "2026-08-13T09:15:00Z",
        "updated_at": "2026-08-13T09:15:00Z",
        "issue_url": "https://api.github.com/repos/Dimkox/multi-exchange-engine/issues/34",
        "html_url": "https://github.com/Dimkox/multi-exchange-engine/issues/34#issuecomment-100",
        "body": canonical_bytes(body).decode().rstrip("\n"),
    }


def repository_metadata() -> dict[str, object]:
    return {
        "full_name": "Dimkox/multi-exchange-engine",
        "default_branch": "main",
        "owner": {"login": "Dimkox", "id": 42},
    }


def release_projection() -> dict[str, object]:
    return {
        "id": 200,
        "tag_name": "claw-host-inputs-2026-08-13",
        "draft": True,
        "prerelease": False,
        "assets": [
            {"id": item["id"], "name": item["name"], "size": item["size"]}
            for item in approval_body()["assets"]
        ],
    }


def test_request_rejects_duplicate_extra_and_token_projection() -> None:
    with pytest.raises(ContractError, match="DUPLICATE_KEY"):
        load_closed_bytes(b'{"action":"status","action":"rollback"}', max_bytes=32768)

    value = valid_request()
    value["persisted_token"] = "forbidden"
    with pytest.raises(ContractError, match="REQUEST_FIELDS"):
        verify_request(value, expected_action="begin")

    request = verify_request(valid_request(), expected_action="begin")
    assert request.github_token == "ephemeral-test-token"
    assert "ephemeral-test-token" not in json.dumps(request.projection(), sort_keys=True)


@pytest.mark.parametrize("action", ["begin", "finalize"])
def test_network_actions_require_memory_only_token(action: str) -> None:
    value = valid_request(action)
    value["github_token"] = None
    with pytest.raises(ContractError, match="REQUEST_TOKEN"):
        verify_request(value, expected_action=action)


@pytest.mark.parametrize("action", ["status", "rollback"])
def test_local_recovery_actions_require_null_token(action: str) -> None:
    assert verify_request(valid_request(action), expected_action=action).github_token is None
    value = valid_request(action)
    value["github_token"] = "unneeded-token"
    with pytest.raises(ContractError, match="REQUEST_TOKEN"):
        verify_request(value, expected_action=action)


@pytest.mark.parametrize("action", ["finalize", "status", "rollback"])
def test_post_migration_requests_require_exact_transaction_binding(action: str) -> None:
    request = verify_request(valid_request(action), expected_action=action)
    assert request.transaction_id == "d" * 32
    missing_transaction = valid_request(action)
    missing_transaction["transaction_id"] = None
    with pytest.raises(ContractError, match="REQUEST_RUN_BINDING"):
        verify_request(missing_transaction, expected_action=action)


def test_owner_approval_tuple_is_exact_and_canonical() -> None:
    result = verify_approval(
        approval_comment(),
        repository_metadata(),
        release_projection(),
        request=verify_request(valid_request(), expected_action="begin"),
        installed_identity=installed_identity(),
        expected_policy_sha256=DIGEST,
        expected_closure_sha256="d" * 64,
        now=NOW,
    )
    assert result["source_sha"] == SHA
    assert result["approval_comment_id"] == 100
    assert result["approval_owner_id"] == 42
    assert result["approval_body_sha256"]


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("repository", "other/repo", "APPROVAL_TARGET"),
        ("source_sha", "0" * 40, "APPROVAL_SOURCE"),
        ("policy_sha256", "0" * 64, "APPROVAL_POLICY"),
        ("host_inventory_sha256", "0" * 64, "APPROVAL_HOST_INVENTORY"),
        ("release_id", 201, "APPROVAL_RELEASE"),
    ],
)
def test_owner_approval_rejects_tuple_mutations(field: str, value: object, code: str) -> None:
    body = approval_body()
    body[field] = value
    with pytest.raises(ApprovalError, match=code):
        verify_approval(
            approval_comment(body),
            repository_metadata(),
            release_projection(),
            request=verify_request(valid_request(), expected_action="begin"),
            installed_identity=installed_identity(),
            expected_policy_sha256=DIGEST,
            expected_closure_sha256="d" * 64,
            now=NOW,
        )


def test_owner_approval_rejects_asset_order_modification_and_expiry() -> None:
    reordered = approval_body()
    reordered["assets"] = list(reversed(reordered["assets"]))
    with pytest.raises(ApprovalError, match="APPROVAL_ASSETS_ORDER"):
        verify_approval(
            approval_comment(reordered),
            repository_metadata(),
            release_projection(),
            request=verify_request(valid_request(), expected_action="begin"),
            installed_identity=installed_identity(),
            expected_policy_sha256=DIGEST,
            expected_closure_sha256="d" * 64,
            now=NOW,
        )

    with pytest.raises(ApprovalError, match="APPROVAL_EXPIRED"):
        verify_approval(
            approval_comment(),
            repository_metadata(),
            release_projection(),
            request=verify_request(valid_request(), expected_action="begin"),
            installed_identity=installed_identity(),
            expected_policy_sha256=DIGEST,
            expected_closure_sha256="d" * 64,
            now=dt.datetime(2026, 8, 13, 10, 0, tzinfo=dt.timezone.utc),
        )


def test_owner_approval_rejects_modified_comment_and_long_ttl() -> None:
    modified = approval_comment()
    modified["updated_at"] = "2026-08-13T09:16:00Z"
    with pytest.raises(ApprovalError, match="APPROVAL_OWNER"):
        verify_approval(
            modified,
            repository_metadata(),
            release_projection(),
            request=verify_request(valid_request(), expected_action="begin"),
            installed_identity=installed_identity(),
            expected_policy_sha256=DIGEST,
            expected_closure_sha256="d" * 64,
            now=NOW,
        )

    body = approval_body()
    body["expires_at"] = "2026-08-13T10:15:01Z"
    with pytest.raises(ApprovalError, match="APPROVAL_TTL"):
        verify_approval(
            approval_comment(body),
            repository_metadata(),
            release_projection(),
            request=verify_request(valid_request(), expected_action="begin"),
            installed_identity=installed_identity(),
            expected_policy_sha256=DIGEST,
            expected_closure_sha256="d" * 64,
            now=NOW,
        )


def test_request_and_receipt_schemas_are_closed_and_semantically_aligned() -> None:
    request_schema = json.loads(Path("schemas/claw-host-deployment-request-v1.schema.json").read_text())
    receipt_schema = json.loads(Path("schemas/claw-host-deployment-receipt-v1.schema.json").read_text())

    assert request_schema["additionalProperties"] is False
    assert set(request_schema["required"]) == REQUEST_SCHEMA_FIELDS
    assert set(request_schema["properties"]) == REQUEST_SCHEMA_FIELDS
    assert request_schema["properties"]["action"]["enum"] == ["begin", "finalize", "status", "rollback"]
    assert request_schema["properties"]["github_token"] == {
        "type": ["string", "null"], "minLength": 1, "maxLength": 4096,
    }

    assert receipt_schema["additionalProperties"] is False
    assert set(receipt_schema["required"]) == set(receipt_schema["properties"])
    assert receipt_schema["properties"]["authority"] == {"const": "NONE"}
    assert receipt_schema["properties"]["status"]["enum"] == [
        "D0_VERIFIED", "BEGIN_ACCEPTED", "HOST_APPLIED_PENDING_FINALIZE",
        "COMMITTED", "ROLLED_BACK", "ROLLBACK_BLOCKED",
    ]


REQUEST_SCHEMA_FIELDS = {
    "schema_version", "action", "github_token", "repository",
    "approval_comment_id", "release_id", "transaction_id",
}


def test_d0_approval_is_separate_exact_owner_tuple() -> None:
    manifest_sha = "9" * 64
    body = {
        "schema_version": "claw-host-deployment-d0-approval-v1",
        "decision": "APPROVE_D0_CONTROLLER_INSTALL",
        "repository": "Dimkox/multi-exchange-engine",
        "source_sha": SHA,
        "source_tree": TREE,
        "install_manifest_sha256": manifest_sha,
        "expires_at": "2026-08-13T10:00:00Z",
        "nonce": "B" * 43,
    }
    comment = approval_comment(body)
    result = verify_d0_approval(
        comment, repository_metadata(), repository="Dimkox/multi-exchange-engine",
        source_sha=SHA, source_tree=TREE, install_manifest_sha256=manifest_sha, now=NOW,
    )
    assert result["decision"] == "APPROVE_D0_CONTROLLER_INSTALL"

    body["source_sha"] = "0" * 40
    with pytest.raises(ApprovalError, match="D0_TUPLE"):
        verify_d0_approval(
            approval_comment(body), repository_metadata(), repository="Dimkox/multi-exchange-engine",
            source_sha=SHA, source_tree=TREE, install_manifest_sha256=manifest_sha, now=NOW,
        )


def test_legacy_recovery_approval_is_closed_owner_exception() -> None:
    expected = {
        "repository": "Dimkox/multi-exchange-engine", "transaction_id": "1" * 32,
        "begin_intent_sha256": "2" * 64, "staged_manifest_sha256": "3" * 64,
        "nonce_record_sha256": "4" * 64, "terminal_journal_sha256": "5" * 64,
        "credential_binding_sha256": "6" * 64, "old_controller_sha": "7" * 40,
        "old_controller_tree": "8" * 40, "recovery_controller_sha": SHA,
        "recovery_controller_tree": TREE, "recovery_install_manifest_sha256": "9" * 64,
        "reason": "PRE_MARKER_TERMINAL_ROLLBACK_COMPATIBILITY",
    }
    body = {
        "schema_version": "claw-host-deployment-legacy-recovery-approval-v1",
        "decision": "APPROVE_LEGACY_D1_TERMINAL_RECOVERY", **expected,
        "expires_at": "2026-08-13T10:00:00Z", "nonce": "L" * 43,
    }
    result = verify_legacy_recovery_approval(approval_comment(body), repository_metadata(), expected=expected, now=NOW)
    assert result["approval_body_sha256"]
    body["terminal_journal_sha256"] = "0" * 64
    with pytest.raises(ApprovalError, match="LEGACY_RECOVERY_TUPLE"):
        verify_legacy_recovery_approval(approval_comment(body), repository_metadata(), expected=expected, now=NOW)
