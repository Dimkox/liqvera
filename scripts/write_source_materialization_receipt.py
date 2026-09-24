#!/usr/bin/env python3
"""Canonical writer for a non-authoritative source materialization observation."""
from __future__ import annotations
import json, os, re, tempfile
from pathlib import Path

SHA1 = re.compile(r"^[0-9a-f]{40}$"); SHA256 = re.compile(r"^[0-9a-f]{64}$")
FIELDS = {"schema_version","authority","repository","pr_number","head_sha","head_tree","base_sha","controller_sha","controller_tree","workflow_path","workflow_blob_sha","action_set_sha256","input_sha256","archive_sha256","member_policy_sha256","approval_comment_id","approval_comment_url","approval_owner_id","approval_owner_login","approval_body_sha256","approval_nonce","approval_created_at","cleanup"}
class ObservationError(ValueError): pass

def validate(value):
    if not isinstance(value, dict): raise ObservationError("OBSERVATION_NOT_OBJECT")
    extra, missing = set(value)-FIELDS, FIELDS-set(value)
    if extra: raise ObservationError("OBSERVATION_UNKNOWN_FIELD")
    if missing: raise ObservationError("OBSERVATION_MISSING_FIELD")
    if value["schema_version"] != "source-materialization-observation-v1" or value["authority"] != "NONE": raise ObservationError("OBSERVATION_AUTHORITY_FORBIDDEN")
    if not isinstance(value["repository"],str) or len(value["repository"]) > 200 or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+",value["repository"]): raise ObservationError("OBSERVATION_REPOSITORY_INVALID")
    if not isinstance(value["pr_number"],int) or isinstance(value["pr_number"],bool) or value["pr_number"] < 1: raise ObservationError("OBSERVATION_PR_INVALID")
    for field in ("head_sha","head_tree","base_sha","controller_sha","controller_tree","workflow_blob_sha"):
        if not isinstance(value[field], str) or not SHA1.fullmatch(value[field]): raise ObservationError("OBSERVATION_SHA_INVALID")
    for field in ("action_set_sha256","input_sha256","archive_sha256","member_policy_sha256"):
        if not isinstance(value[field], str) or not SHA256.fullmatch(value[field]): raise ObservationError("OBSERVATION_DIGEST_INVALID")
    if value["cleanup"] != {"intent":"REMOVE_ALL","outcome":"REMOVED"}: raise ObservationError("OBSERVATION_CLEANUP_UNPROVEN")
    if value["workflow_path"] != ".github/workflows/validate-pr-on-claw.yml": raise ObservationError("OBSERVATION_WORKFLOW_INVALID")
    if not isinstance(value["approval_comment_id"],int) or isinstance(value["approval_comment_id"],bool) or value["approval_comment_id"] < 1: raise ObservationError("OBSERVATION_APPROVAL_INVALID")
    if not isinstance(value["approval_owner_id"],int) or isinstance(value["approval_owner_id"],bool) or value["approval_owner_id"] < 1: raise ObservationError("OBSERVATION_APPROVAL_OWNER_INVALID")
    if not isinstance(value["approval_comment_url"],str) or not re.fullmatch(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/pull/[1-9][0-9]*#issuecomment-[1-9][0-9]*",value["approval_comment_url"]): raise ObservationError("OBSERVATION_APPROVAL_URL_INVALID")
    if not isinstance(value["approval_owner_login"],str) or not value["approval_owner_login"]: raise ObservationError("OBSERVATION_APPROVAL_OWNER_INVALID")
    if not SHA256.fullmatch(str(value["approval_body_sha256"])): raise ObservationError("OBSERVATION_APPROVAL_DIGEST_INVALID")
    if not re.fullmatch(r"[A-Za-z0-9_-]{43}",str(value["approval_nonce"])): raise ObservationError("OBSERVATION_APPROVAL_NONCE_INVALID")
    if not isinstance(value["approval_created_at"],str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z",value["approval_created_at"]): raise ObservationError("OBSERVATION_APPROVAL_CREATED_AT_INVALID")

def write_observation(value, path: Path):
    validate(value); path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    fd, name = tempfile.mkstemp(prefix=".observation-", dir=path.parent)
    try:
        os.fchmod(fd, 0o600); os.write(fd, data); os.fsync(fd); os.close(fd); os.replace(name, path)
    except BaseException:
        try: os.close(fd)
        except OSError: pass
        try: os.unlink(name)
        except OSError: pass
        raise
