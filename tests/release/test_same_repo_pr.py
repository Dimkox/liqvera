import json
import subprocess
import sys
from pathlib import Path

import pytest
import datetime as dt

from scripts.verify_same_repo_pr import ControllerError, verify_pull_request
from scripts.verify_github_bootstrap_approval import ApprovalError, verify_approval_comment


SHA = "a" * 40
BASE = "b" * 40
TREE = "c" * 40


def pr(**updates):
    value = {
        "number": 7, "state": "open",
        "base": {"ref": "main", "sha": BASE, "repo": {"full_name": "Dimkox/multi-exchange-engine"}},
        "head": {"sha": SHA, "repo": {"full_name": "Dimkox/multi-exchange-engine"}},
    }
    value.update(updates)
    return value


def test_accepts_exact_open_same_repo_identity():
    got = verify_pull_request(pr(), repository="Dimkox/multi-exchange-engine", pr_number=7,
                              expected_head=SHA, controller_sha=BASE, head_tree=TREE,
                              expected_tree=TREE, ancestry_proven=True)
    assert got["head_sha"] == SHA


@pytest.mark.parametrize("mutation,code", [
    ({"state": "closed"}, "PR_NOT_OPEN"),
    ({"number": 8}, "PR_NUMBER_MISMATCH"),
    ({"head": {"sha": SHA, "repo": {"full_name": "evil/fork"}}}, "PR_HEAD_REPOSITORY_MISMATCH"),
])
def test_rejects_bad_pr_identity(mutation, code):
    with pytest.raises(ControllerError, match=code):
        verify_pull_request(pr(**mutation), repository="Dimkox/multi-exchange-engine", pr_number=7,
                            expected_head=SHA, controller_sha=BASE, head_tree=TREE,
                            expected_tree=TREE, ancestry_proven=True)


@pytest.mark.parametrize("kwargs,code", [
    ({"expected_head":"d"*40},"PR_HEAD_SHA_MISMATCH"),
    ({"controller_sha":"d"*40},"PR_BASE_CONTROLLER_MISMATCH"),
    ({"expected_tree":"d"*40},"PR_TREE_MISMATCH"),
    ({"ancestry_proven":False},"PR_ANCESTRY_UNPROVEN"),
])
def test_rejects_stale_head_base_tree_and_ancestry(kwargs,code):
    args={"repository":"Dimkox/multi-exchange-engine","pr_number":7,"expected_head":SHA,"controller_sha":BASE,"head_tree":TREE,"expected_tree":TREE,"ancestry_proven":True}; args.update(kwargs)
    with pytest.raises(ControllerError,match=code): verify_pull_request(pr(),**args)


def test_compare_projection_binds_base_merge_base_and_head():
    compare={"status":"ahead","base_commit":{"sha":BASE},"merge_base_commit":{"sha":BASE},"commits":[{"sha":SHA}]}
    verify_pull_request(pr(),repository="Dimkox/multi-exchange-engine",pr_number=7,expected_head=SHA,controller_sha=BASE,head_tree=TREE,expected_tree=TREE,ancestry_proven=True,compare=compare)
    compare["commits"]=[{"sha":"d"*40}]
    with pytest.raises(ControllerError,match="COMPARE_HEAD_MISMATCH"): verify_pull_request(pr(),repository="Dimkox/multi-exchange-engine",pr_number=7,expected_head=SHA,controller_sha=BASE,head_tree=TREE,expected_tree=TREE,ancestry_proven=True,compare=compare)


def test_cli_rejects_extra_payload_field(tmp_path):
    payload = tmp_path / "payload.json"
    payload.write_text(json.dumps({"pr_number": 7, "expected_head_sha": SHA, "approval_comment_id":9, "command": "id"}))
    run = subprocess.run([sys.executable, "scripts/verify_same_repo_pr.py", "payload", str(payload)], text=True, capture_output=True)
    assert run.returncode == 2 and "PAYLOAD_UNKNOWN_FIELD" in run.stderr


def approval_comment(body_updates=None, api_updates=None):
    body={"decision":"APPROVE_TRANSITIONAL_BOOTSTRAP","repository":"Dimkox/multi-exchange-engine","pr_number":7,"commit_id":SHA,"head_tree":TREE,"base_sha":BASE,"controller_sha":BASE,"controller_tree":TREE,"workflow_path":".github/workflows/validate-pr-on-claw.yml","workflow_blob_sha":TREE,"allowed_paths":["scripts/verify_same_repo_pr.py"],"checks":["independent-source-trust-review"],"expires_at":"2026-08-12T00:30:00Z","nonce":"N"*43}
    body.update(body_updates or {})
    value={"id":9,"node_id":"ignored-api-field","issue_url":"https://api.github.com/repos/Dimkox/multi-exchange-engine/issues/7","html_url":"https://github.com/Dimkox/multi-exchange-engine/pull/7#issuecomment-9","user":{"id":42,"login":"Dimkox","extra":True},"author_association":"OWNER","created_at":"2026-08-12T00:00:00Z","updated_at":"2026-08-12T00:00:00Z","body":json.dumps(body,sort_keys=True,separators=(",",":"))}
    value.update(api_updates or {})
    return value


def verify_comment(value):
    return verify_approval_comment(value,expected_comment_id=9,repository="Dimkox/multi-exchange-engine",pr_number=7,expected_head=SHA,expected_owner_login="Dimkox",expected_owner_id=42,expected_allowed_paths=["scripts/verify_same_repo_pr.py"],expected_checks=["independent-source-trust-review"],now=dt.datetime(2026,8,12,tzinfo=dt.timezone.utc),max_ttl=dt.timedelta(hours=1))


def test_bootstrap_comment_is_exact_owner_commit_bound_unmodified_and_expiring():
    got=verify_comment(approval_comment())
    assert got["commit_id"] == SHA and got["approval_comment_id"] == 9
    assert got["approval_created_at"] == "2026-08-12T00:00:00Z"
    with pytest.raises(ApprovalError,match="APPROVAL_COMMENT_MODIFIED"): verify_comment(approval_comment(api_updates={"updated_at":"2026-08-12T00:01:00Z"}))


@pytest.mark.parametrize("mutation,code", [
    ({"expires_at":"2026-08-12T02:00:00Z"},"APPROVAL_TTL_EXCEEDED"),
    ({"nonce":"short"},"APPROVAL_NONCE_INVALID"),
    ({"allowed_paths":["other"]},"APPROVAL_ALLOWED_PATHS_MISMATCH"),
    ({"extra":True},"APPROVAL_BODY_NOT_CLOSED"),
    ({"decision":"APPROVE"},"APPROVAL_DECISION_INVALID"),
])
def test_approval_body_failures(mutation,code):
    with pytest.raises(ApprovalError,match=code): verify_comment(approval_comment(body_updates=mutation))


def test_approval_cli_binds_actual_changed_file_projection(tmp_path):
    now=dt.datetime.now(dt.timezone.utc).replace(microsecond=0); created=now.isoformat().replace("+00:00","Z"); expiry=(now+dt.timedelta(minutes=30)).isoformat().replace("+00:00","Z")
    comment=approval_comment({"expires_at":expiry},{"created_at":created,"updated_at":created})
    paths={"comment.json":comment,"repo.json":{"full_name":"Dimkox/multi-exchange-engine","owner":{"id":42,"login":"Dimkox"}},"files.json":[{"filename":"scripts/verify_same_repo_pr.py"}]}
    for name,value in paths.items(): (tmp_path/name).write_text(json.dumps(value))
    output=tmp_path/"verified.json"
    command=[sys.executable,"scripts/verify_github_bootstrap_approval.py","--approval-comment",str(tmp_path/"comment.json"),"--repository-metadata",str(tmp_path/"repo.json"),"--changed-files",str(tmp_path/"files.json"),"--repository","Dimkox/multi-exchange-engine","--pr-number","7","--expected-head",SHA,"--approval-comment-id","9","--allowed-path","scripts/verify_same_repo_pr.py","--check","independent-source-trust-review","--output",str(output)]
    run=subprocess.run(command,text=True,capture_output=True)
    assert run.returncode==0 and json.loads(output.read_text())["approval_comment_id"]==9
    (tmp_path/"files.json").write_text(json.dumps([{"filename":"evil.py"}]))
    run=subprocess.run(command,text=True,capture_output=True)
    assert run.returncode==2 and "PR_CHANGED_PATHS_MISMATCH" in run.stderr


def test_approval_body_rejects_duplicate_json_keys():
    with pytest.raises(ApprovalError,match="JSON_DUPLICATE_KEY"): verify_comment(approval_comment(api_updates={"body":'{"repository":"Dimkox/multi-exchange-engine","repository":"evil/x"}'}))


@pytest.mark.parametrize("api_updates,code", [
    ({"author_association":"COLLABORATOR"},"APPROVAL_NOT_OWNER"),
    ({"issue_url":"https://api.github.com/repos/Dimkox/multi-exchange-engine/issues/8"},"APPROVAL_ISSUE_URL_INVALID"),
    ({"html_url":"https://github.com/Dimkox/multi-exchange-engine/pull/7#issuecomment-8"},"APPROVAL_URL_INVALID"),
    ({"user":{"id":99,"login":"Dimkox"}},"APPROVAL_OWNER_MISMATCH"),
])
def test_approval_comment_api_identity_failures(api_updates,code):
    with pytest.raises(ApprovalError,match=code): verify_comment(approval_comment(api_updates=api_updates))


@pytest.mark.parametrize("api_updates,body_updates,code", [
    ({"created_at":"invalid","updated_at":"invalid"},{},"APPROVAL_CREATED_AT_INVALID"),
    ({"created_at":"2026-08-12T00:00:00","updated_at":"2026-08-12T00:00:00"},{},"APPROVAL_CREATED_AT_INVALID"),
    ({"created_at":"2026-08-12T00:01:00Z","updated_at":"2026-08-12T00:01:00Z"},{},"APPROVAL_CREATED_IN_FUTURE"),
    ({"created_at":"2026-08-11T23:00:00Z","updated_at":"2026-08-11T23:00:00Z"},{"expires_at":"2026-08-12T00:30:00Z"},"APPROVAL_TTL_EXCEEDED"),
    ({},{"expires_at":"2026-08-11T23:59:59Z"},"APPROVAL_EXPIRY_BEFORE_CREATION"),
])
def test_approval_api_time_and_expiry_bounds(api_updates,body_updates,code):
    with pytest.raises(ApprovalError,match=code): verify_comment(approval_comment(body_updates,api_updates))
