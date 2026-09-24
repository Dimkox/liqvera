"""Closed, non-persisting contracts for the Claw host deployment controller."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any


SHA1 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
NONCE = re.compile(r"^[A-Za-z0-9_-]{43}$")
TRANSACTION = re.compile(r"^[0-9a-f]{32}$")
RELEASE_TAG = re.compile(r"^[A-Za-z0-9_.-]{1,100}$")
ASSET_NAME = re.compile(r"^[A-Za-z0-9_.:+-]{1,180}$")
ROLE = re.compile(r"^(bundle_manifest|host_inventory|oci_archive|oci_layout|oci_receipt|oci_sidecar|deb:[a-z0-9][a-z0-9+.-]{0,127})$")
REQUEST_FIELDS = {
    "schema_version", "action", "github_token", "repository",
    "approval_comment_id", "release_id", "transaction_id",
}
APPROVAL_FIELDS = {
    "schema_version", "decision", "repository", "source_sha", "source_tree",
    "policy_sha256", "closure_sha256", "oci_archive_sha256",
    "oci_archive_size", "oci_archive_format", "image_manifest_digest",
    "host_inventory_sha256", "host_inventory_observed_at",
    "bundle_manifest_sha256", "release_id", "release_tag", "assets",
    "rollback_deadline_seconds", "expires_at", "nonce",
}
ASSET_FIELDS = {"id", "name", "role", "size", "sha256"}
INSTALLED_FIELDS = {
    "schema_version", "repository", "default_branch", "controller_sha",
    "controller_tree",
}
ACTIONS = {"begin", "finalize", "status", "rollback"}
ROLLBACK_RECEIPT_FIELDS = {
    "schema_version", "authority", "not_host_receipt", "receipt_kind",
    "transaction_id", "controller_sha", "controller_tree", "policy_sha256",
    "closure_sha256", "journal_sha256", "prior_host_receipt_sha256",
    "status", "created_at",
}
D0_APPROVAL_FIELDS = {
    "schema_version", "decision", "repository", "source_sha", "source_tree",
    "install_manifest_sha256", "expires_at", "nonce",
}
LEGACY_RECOVERY_APPROVAL_FIELDS = {
    "schema_version", "decision", "repository", "transaction_id",
    "begin_intent_sha256", "staged_manifest_sha256", "nonce_record_sha256",
    "terminal_journal_sha256", "credential_binding_sha256",
    "old_controller_sha", "old_controller_tree", "recovery_controller_sha",
    "recovery_controller_tree", "recovery_install_manifest_sha256",
    "reason", "expires_at", "nonce",
}


class ContractError(ValueError):
    pass


class ApprovalError(ContractError):
    pass


def _fail(error_type: type[ContractError], code: str) -> None:
    raise error_type(code)


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in items:
        if key in value:
            raise ContractError("DUPLICATE_KEY")
        value[key] = item
    return value


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def load_closed_bytes(raw: bytes, *, max_bytes: int) -> dict[str, Any]:
    if not isinstance(raw, bytes) or not raw or len(raw) > max_bytes or b"\x00" in raw:
        raise ContractError("INPUT_SIZE")
    try:
        value = json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=_pairs)
    except UnicodeDecodeError as exc:
        raise ContractError("INPUT_ENCODING") from exc
    except json.JSONDecodeError as exc:
        raise ContractError("INPUT_JSON") from exc
    if not isinstance(value, dict):
        raise ContractError("INPUT_NOT_OBJECT")
    return value


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _utc_time(value: object, code: str) -> dt.datetime:
    try:
        parsed = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ApprovalError(code) from exc
    if parsed.tzinfo is None or parsed.utcoffset() != dt.timedelta(0):
        raise ApprovalError(code)
    return parsed


@dataclass(frozen=True)
class DeploymentRequest:
    action: str
    github_token: str | None = field(repr=False)
    repository: str = ""
    approval_comment_id: int | None = None
    release_id: int | None = None
    transaction_id: str | None = None

    def projection(self) -> dict[str, object]:
        return {
            "schema_version": "claw-host-deployment-request-v1",
            "action": self.action,
            "repository": self.repository,
            "approval_comment_id": self.approval_comment_id,
            "release_id": self.release_id,
            "transaction_id": self.transaction_id,
        }


def verify_request(value: dict[str, object], *, expected_action: str) -> DeploymentRequest:
    if not isinstance(value, dict) or set(value) != REQUEST_FIELDS:
        raise ContractError("REQUEST_FIELDS")
    if value["schema_version"] != "claw-host-deployment-request-v1":
        raise ContractError("REQUEST_SCHEMA")
    action = value["action"]
    if action not in ACTIONS or action != expected_action:
        raise ContractError("REQUEST_ACTION")
    token = value["github_token"]
    if action in {"begin", "finalize"}:
        if not isinstance(token, str) or not 1 <= len(token) <= 4096 or any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in token):
            raise ContractError("REQUEST_TOKEN")
    elif token is not None:
        raise ContractError("REQUEST_TOKEN")
    repository = value["repository"]
    if repository != "Dimkox/multi-exchange-engine":
        raise ContractError("REQUEST_REPOSITORY")
    if action == "begin":
        if not _positive_int(value["approval_comment_id"]) or not _positive_int(value["release_id"]):
            raise ContractError("REQUEST_APPROVAL_BINDING")
        if value["transaction_id"] is not None:
            raise ContractError("REQUEST_BEGIN_SCOPE")
    else:
        if value["approval_comment_id"] is not None or value["release_id"] is not None:
            raise ContractError("REQUEST_POST_MIGRATION_SCOPE")
        if not isinstance(value["transaction_id"], str) or not TRANSACTION.fullmatch(value["transaction_id"]):
            raise ContractError("REQUEST_RUN_BINDING")
    return DeploymentRequest(
        action=str(action), github_token=token, repository=repository,
        approval_comment_id=value["approval_comment_id"], release_id=value["release_id"],
        transaction_id=value["transaction_id"],
    )


def verify_rollback_receipt(
    value: dict[str, object], *, expected_transaction_id: str | None = None,
    expected_policy_sha256: str | None = None,
    expected_closure_sha256: str | None = None,
    expected_journal_sha256: str | None = None,
    expected_controller_sha: str | None = None,
    expected_controller_tree: str | None = None,
    expected_prior_host_receipt_sha256: str | None | object = ...,
) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != ROLLBACK_RECEIPT_FIELDS:
        raise ContractError("ROLLBACK_RECEIPT_FIELDS")
    constants = {
        "schema_version": "claw-host-deployment-rollback-receipt-v1",
        "authority": "NONE",
        "not_host_receipt": True,
        "receipt_kind": "ROLLBACK",
        "status": "ROLLED_BACK",
    }
    if any(value.get(key) != expected for key, expected in constants.items()):
        raise ContractError("ROLLBACK_RECEIPT_CONTRACT")
    if not isinstance(value.get("transaction_id"), str) or not TRANSACTION.fullmatch(value["transaction_id"]):
        raise ContractError("ROLLBACK_RECEIPT_TRANSACTION")
    for key in ("controller_sha", "controller_tree"):
        if not isinstance(value.get(key), str) or not SHA1.fullmatch(value[key]):
            raise ContractError("ROLLBACK_RECEIPT_SOURCE")
    for key in ("policy_sha256", "closure_sha256", "journal_sha256"):
        if not isinstance(value.get(key), str) or not SHA256.fullmatch(value[key]):
            raise ContractError("ROLLBACK_RECEIPT_DIGEST")
    prior = value.get("prior_host_receipt_sha256")
    if prior is not None and (not isinstance(prior, str) or not SHA256.fullmatch(prior)):
        raise ContractError("ROLLBACK_RECEIPT_PRIOR")
    created = _utc_time(value.get("created_at"), "ROLLBACK_RECEIPT_TIME")
    if created > dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=5):
        raise ContractError("ROLLBACK_RECEIPT_TIME")
    expected = {
        "transaction_id": expected_transaction_id,
        "policy_sha256": expected_policy_sha256,
        "closure_sha256": expected_closure_sha256,
        "journal_sha256": expected_journal_sha256,
        "controller_sha": expected_controller_sha,
        "controller_tree": expected_controller_tree,
    }
    if any(item is not None and value[key] != item for key, item in expected.items()):
        raise ContractError("ROLLBACK_RECEIPT_BINDING")
    if expected_prior_host_receipt_sha256 is not ... and prior != expected_prior_host_receipt_sha256:
        raise ContractError("ROLLBACK_RECEIPT_BINDING")
    return dict(value)


def _verify_asset(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != ASSET_FIELDS:
        raise ApprovalError("APPROVAL_ASSET_FIELDS")
    if not _positive_int(value["id"]) or not _positive_int(value["size"]):
        raise ApprovalError("APPROVAL_ASSET_IDENTITY")
    if not isinstance(value["name"], str) or not ASSET_NAME.fullmatch(value["name"]):
        raise ApprovalError("APPROVAL_ASSET_IDENTITY")
    if not isinstance(value["role"], str) or not ROLE.fullmatch(value["role"]):
        raise ApprovalError("APPROVAL_ASSET_ROLE")
    if not isinstance(value["sha256"], str) or not SHA256.fullmatch(value["sha256"]):
        raise ApprovalError("APPROVAL_ASSET_DIGEST")
    return value


def verify_d0_approval(
    comment: dict[str, object], repository_metadata: dict[str, object], *,
    repository: str, source_sha: str, source_tree: str,
    install_manifest_sha256: str, now: dt.datetime,
) -> dict[str, object]:
    if repository_metadata.get("full_name") != repository or repository_metadata.get("default_branch") != "main":
        raise ApprovalError("D0_REPOSITORY")
    owner = repository_metadata.get("owner")
    user = comment.get("user") if isinstance(comment, dict) else None
    if not isinstance(owner, dict) or not isinstance(user, dict):
        raise ApprovalError("D0_OWNER")
    if user.get("login") != owner.get("login") or user.get("id") != owner.get("id") or not _positive_int(owner.get("id")):
        raise ApprovalError("D0_OWNER")
    if comment.get("author_association") != "OWNER" or comment.get("created_at") != comment.get("updated_at"):
        raise ApprovalError("D0_OWNER")
    comment_id = comment.get("id")
    html_url = comment.get("html_url")
    if not _positive_int(comment_id) or not isinstance(html_url, str) or not html_url.startswith(f"https://github.com/{repository}/") or not html_url.endswith(f"#issuecomment-{comment_id}"):
        raise ApprovalError("D0_URL")
    body_source = comment.get("body")
    if not isinstance(body_source, str):
        raise ApprovalError("D0_BODY")
    try:
        body = load_closed_bytes(body_source.encode("utf-8"), max_bytes=16384)
    except ContractError as exc:
        raise ApprovalError(f"D0_{exc}") from exc
    if set(body) != D0_APPROVAL_FIELDS or body_source != canonical_bytes(body).decode().rstrip("\n"):
        raise ApprovalError("D0_BODY_NOT_CLOSED")
    if body["schema_version"] != "claw-host-deployment-d0-approval-v1" or body["decision"] != "APPROVE_D0_CONTROLLER_INSTALL":
        raise ApprovalError("D0_DECISION")
    expected = {
        "repository": repository, "source_sha": source_sha,
        "source_tree": source_tree, "install_manifest_sha256": install_manifest_sha256,
    }
    if any(body[key] != value for key, value in expected.items()):
        raise ApprovalError("D0_TUPLE")
    if not SHA1.fullmatch(source_sha) or not SHA1.fullmatch(source_tree) or not SHA256.fullmatch(install_manifest_sha256):
        raise ApprovalError("D0_TUPLE")
    if not isinstance(body["nonce"], str) or not NONCE.fullmatch(body["nonce"]):
        raise ApprovalError("D0_NONCE")
    created = _utc_time(comment.get("created_at"), "D0_CREATED_AT")
    expires = _utc_time(body["expires_at"], "D0_EXPIRY")
    if created > now or expires <= now or expires <= created or expires - created > dt.timedelta(hours=1):
        raise ApprovalError("D0_EXPIRY")
    return {
        **body,
        "approval_comment_id": comment_id,
        "approval_owner_login": owner["login"],
        "approval_owner_id": owner["id"],
        "approval_body_sha256": hashlib.sha256(body_source.encode()).hexdigest(),
    }


def verify_legacy_recovery_approval(
    comment: dict[str, object], repository_metadata: dict[str, object], *,
    expected: dict[str, object], now: dt.datetime,
) -> dict[str, object]:
    repository = str(expected.get("repository"))
    if repository_metadata.get("full_name") != repository or repository_metadata.get("default_branch") != "main":
        raise ApprovalError("LEGACY_RECOVERY_REPOSITORY")
    owner = repository_metadata.get("owner")
    user = comment.get("user") if isinstance(comment, dict) else None
    if not isinstance(owner, dict) or not isinstance(user, dict) or user.get("login") != owner.get("login") or user.get("id") != owner.get("id") or not _positive_int(owner.get("id")):
        raise ApprovalError("LEGACY_RECOVERY_OWNER")
    if comment.get("author_association") != "OWNER" or comment.get("created_at") != comment.get("updated_at"):
        raise ApprovalError("LEGACY_RECOVERY_OWNER")
    body_source = comment.get("body")
    if not isinstance(body_source, str):
        raise ApprovalError("LEGACY_RECOVERY_BODY")
    try:
        body = load_closed_bytes(body_source.encode(), max_bytes=16_384)
    except ContractError as exc:
        raise ApprovalError(f"LEGACY_RECOVERY_{exc}") from exc
    if set(body) != LEGACY_RECOVERY_APPROVAL_FIELDS or body_source != canonical_bytes(body).decode().rstrip("\n"):
        raise ApprovalError("LEGACY_RECOVERY_BODY_NOT_CLOSED")
    if body.get("schema_version") != "claw-host-deployment-legacy-recovery-approval-v1" or body.get("decision") != "APPROVE_LEGACY_D1_TERMINAL_RECOVERY":
        raise ApprovalError("LEGACY_RECOVERY_DECISION")
    if any(body.get(key) != value for key, value in expected.items()):
        raise ApprovalError("LEGACY_RECOVERY_TUPLE")
    for field in ("begin_intent_sha256", "staged_manifest_sha256", "nonce_record_sha256", "terminal_journal_sha256", "credential_binding_sha256", "recovery_install_manifest_sha256"):
        if not isinstance(body.get(field), str) or not SHA256.fullmatch(body[field]):
            raise ApprovalError("LEGACY_RECOVERY_TUPLE")
    for field in ("old_controller_sha", "old_controller_tree", "recovery_controller_sha", "recovery_controller_tree"):
        if not isinstance(body.get(field), str) or not SHA1.fullmatch(body[field]):
            raise ApprovalError("LEGACY_RECOVERY_TUPLE")
    if not isinstance(body.get("transaction_id"), str) or not TRANSACTION.fullmatch(body["transaction_id"]):
        raise ApprovalError("LEGACY_RECOVERY_TUPLE")
    if body.get("reason") != "PRE_MARKER_TERMINAL_ROLLBACK_COMPATIBILITY" or not isinstance(body.get("nonce"), str) or not NONCE.fullmatch(body["nonce"]):
        raise ApprovalError("LEGACY_RECOVERY_TUPLE")
    created = _utc_time(comment.get("created_at"), "LEGACY_RECOVERY_CREATED_AT")
    expires = _utc_time(body["expires_at"], "LEGACY_RECOVERY_EXPIRY")
    if created > now or expires <= now or expires <= created or expires - created > dt.timedelta(hours=1):
        raise ApprovalError("LEGACY_RECOVERY_EXPIRY")
    comment_id = comment.get("id")
    html_url = comment.get("html_url")
    if not _positive_int(comment_id) or not isinstance(html_url, str) or not html_url.startswith(f"https://github.com/{repository}/") or not html_url.endswith(f"#issuecomment-{comment_id}"):
        raise ApprovalError("LEGACY_RECOVERY_OWNER")
    return {**body, "approval_comment_id": comment_id, "approval_owner_login": owner["login"], "approval_owner_id": owner["id"], "approval_body_sha256": hashlib.sha256(body_source.encode()).hexdigest()}


def verify_approval(
    comment: dict[str, object],
    repository_metadata: dict[str, object],
    release: dict[str, object],
    *,
    request: DeploymentRequest,
    installed_identity: dict[str, object],
    expected_policy_sha256: str,
    expected_closure_sha256: str,
    now: dt.datetime,
) -> dict[str, object]:
    if request.action != "begin" or request.approval_comment_id is None or request.release_id is None:
        raise ApprovalError("APPROVAL_REQUEST_SCOPE")
    if set(installed_identity) != INSTALLED_FIELDS or installed_identity.get("schema_version") != "claw-host-deployment-installed-v1":
        raise ApprovalError("APPROVAL_INSTALLED_IDENTITY")
    if installed_identity.get("repository") != request.repository or installed_identity.get("default_branch") != "main":
        raise ApprovalError("APPROVAL_INSTALLED_IDENTITY")
    for key in ("controller_sha", "controller_tree"):
        if not isinstance(installed_identity.get(key), str) or not SHA1.fullmatch(installed_identity[key]):
            raise ApprovalError("APPROVAL_INSTALLED_IDENTITY")
    if not isinstance(comment, dict) or comment.get("id") != request.approval_comment_id:
        raise ApprovalError("APPROVAL_COMMENT")
    owner = repository_metadata.get("owner") if isinstance(repository_metadata, dict) else None
    user = comment.get("user") if isinstance(comment, dict) else None
    if repository_metadata.get("full_name") != request.repository or repository_metadata.get("default_branch") != "main":
        raise ApprovalError("APPROVAL_REPOSITORY")
    if not isinstance(owner, dict) or not isinstance(user, dict) or user.get("login") != owner.get("login") or user.get("id") != owner.get("id") or not _positive_int(owner.get("id")):
        raise ApprovalError("APPROVAL_OWNER")
    if comment.get("author_association") != "OWNER" or comment.get("created_at") != comment.get("updated_at"):
        raise ApprovalError("APPROVAL_OWNER")
    issue_url = comment.get("issue_url")
    html_url = comment.get("html_url")
    api_prefix = f"https://api.github.com/repos/{request.repository}/issues/"
    web_prefix = f"https://github.com/{request.repository}/"
    if not isinstance(issue_url, str) or not issue_url.startswith(api_prefix):
        raise ApprovalError("APPROVAL_URL")
    if not isinstance(html_url, str) or not html_url.startswith(web_prefix) or not html_url.endswith(f"#issuecomment-{request.approval_comment_id}"):
        raise ApprovalError("APPROVAL_URL")
    body_source = comment.get("body")
    if not isinstance(body_source, str) or len(body_source.encode("utf-8")) > 65536:
        raise ApprovalError("APPROVAL_BODY")
    try:
        body = load_closed_bytes(body_source.encode("utf-8"), max_bytes=65536)
    except ContractError as exc:
        raise ApprovalError(f"APPROVAL_{exc}") from exc
    if set(body) != APPROVAL_FIELDS or body_source != canonical_bytes(body).decode("utf-8").rstrip("\n"):
        raise ApprovalError("APPROVAL_BODY_NOT_CLOSED")
    if body["schema_version"] != "claw-host-deployment-approval-v1" or body["decision"] != "APPROVE_CLAW_HOST_TRANSITION":
        raise ApprovalError("APPROVAL_DECISION")
    if body["repository"] != request.repository:
        raise ApprovalError("APPROVAL_TARGET")
    if body["source_sha"] != installed_identity["controller_sha"] or body["source_tree"] != installed_identity["controller_tree"]:
        raise ApprovalError("APPROVAL_SOURCE")
    if body["policy_sha256"] != expected_policy_sha256 or not SHA256.fullmatch(str(expected_policy_sha256)):
        raise ApprovalError("APPROVAL_POLICY")
    if body["closure_sha256"] != expected_closure_sha256 or not SHA256.fullmatch(str(expected_closure_sha256)):
        raise ApprovalError("APPROVAL_CLOSURE")
    for key in ("oci_archive_sha256", "host_inventory_sha256", "bundle_manifest_sha256"):
        if not isinstance(body[key], str) or not SHA256.fullmatch(body[key]) or body[key] == "0" * 64:
            raise ApprovalError("APPROVAL_HOST_INVENTORY" if key == "host_inventory_sha256" else "APPROVAL_DIGEST")
    if not _positive_int(body["oci_archive_size"]) or body["oci_archive_format"] != "docker-archive" or not re.fullmatch(r"sha256:[0-9a-f]{64}", str(body["image_manifest_digest"])):
        raise ApprovalError("APPROVAL_OCI")
    if body["release_id"] != request.release_id or release.get("id") != request.release_id or body["release_tag"] != release.get("tag_name"):
        raise ApprovalError("APPROVAL_RELEASE")
    if not isinstance(body["release_tag"], str) or not RELEASE_TAG.fullmatch(body["release_tag"]) or release.get("draft") is not True or release.get("prerelease") is not False:
        raise ApprovalError("APPROVAL_RELEASE")
    assets_source = body["assets"]
    if not isinstance(assets_source, list) or not 1 <= len(assets_source) <= 32:
        raise ApprovalError("APPROVAL_ASSETS")
    assets = [_verify_asset(item) for item in assets_source]
    order = [(item["role"], item["name"], item["id"]) for item in assets]
    if order != sorted(order) or len({item["id"] for item in assets}) != len(assets) or len({item["name"] for item in assets}) != len(assets) or len({item["role"] for item in assets}) != len(assets):
        raise ApprovalError("APPROVAL_ASSETS_ORDER")
    release_assets = release.get("assets")
    if not isinstance(release_assets, list):
        raise ApprovalError("APPROVAL_RELEASE_ASSETS")
    actual = sorted((item.get("id"), item.get("name"), item.get("size")) for item in release_assets if isinstance(item, dict))
    expected = sorted((item["id"], item["name"], item["size"]) for item in assets)
    if actual != expected:
        raise ApprovalError("APPROVAL_RELEASE_ASSETS")
    archive_assets = [item for item in assets if item["role"] == "oci_archive"]
    if len(archive_assets) != 1 or archive_assets[0]["sha256"] != body["oci_archive_sha256"] or archive_assets[0]["size"] != body["oci_archive_size"]:
        raise ApprovalError("APPROVAL_OCI")
    inventory_assets = [item for item in assets if item["role"] == "host_inventory"]
    if len(inventory_assets) != 1 or inventory_assets[0]["sha256"] != body["host_inventory_sha256"]:
        raise ApprovalError("APPROVAL_HOST_INVENTORY")
    deadline = body["rollback_deadline_seconds"]
    if not isinstance(deadline, int) or isinstance(deadline, bool) or not 300 <= deadline <= 3600:
        raise ApprovalError("APPROVAL_ROLLBACK_DEADLINE")
    if not isinstance(body["nonce"], str) or not NONCE.fullmatch(body["nonce"]):
        raise ApprovalError("APPROVAL_NONCE")
    created = _utc_time(comment.get("created_at"), "APPROVAL_CREATED_AT")
    observed = _utc_time(body["host_inventory_observed_at"], "APPROVAL_HOST_INVENTORY")
    expires = _utc_time(body["expires_at"], "APPROVAL_EXPIRY")
    if now.tzinfo is None or now.utcoffset() != dt.timedelta(0):
        raise ApprovalError("APPROVAL_NOW")
    if created > now or expires <= created or expires - created > dt.timedelta(hours=1):
        raise ApprovalError("APPROVAL_TTL")
    if expires <= now:
        raise ApprovalError("APPROVAL_EXPIRED")
    if observed > created or created - observed > dt.timedelta(hours=1):
        raise ApprovalError("APPROVAL_HOST_INVENTORY")
    canonical = canonical_bytes(body).rstrip(b"\n")
    return {
        **body,
        "approval_comment_id": request.approval_comment_id,
        "approval_comment_url": html_url,
        "approval_owner_login": owner["login"],
        "approval_owner_id": owner["id"],
        "approval_created_at": comment["created_at"],
        "approval_body_sha256": hashlib.sha256(canonical).hexdigest(),
    }
