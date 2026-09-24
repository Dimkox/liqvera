#!/usr/bin/env python3
"""Verify an exact GitHub-authenticated owner issue-comment approval."""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, re, sys
from pathlib import Path

SHA=re.compile(r"^[0-9a-f]{40}$"); NONCE=re.compile(r"^[A-Za-z0-9_-]{43}$")
FIELDS={"decision","repository","pr_number","commit_id","head_tree","base_sha","controller_sha","controller_tree","workflow_path","workflow_blob_sha","allowed_paths","checks","expires_at","nonce"}
MAX_FUTURE_CLOCK_SKEW=dt.timedelta(0)
class ApprovalError(ValueError): pass
def _fail(code): raise ApprovalError(code)
def _sha(value): return isinstance(value,str) and SHA.fullmatch(value)
def _time(value, code):
    try: parsed=dt.datetime.fromisoformat(value.replace("Z","+00:00"))
    except (AttributeError,ValueError) as exc: raise ApprovalError(code) from exc
    if parsed.tzinfo is None or parsed.utcoffset() != dt.timedelta(0): _fail(code)
    return parsed
def loads_no_duplicates(source: str):
    def pairs(items):
        result={}
        for key,value in items:
            if key in result: _fail("JSON_DUPLICATE_KEY")
            result[key]=value
        return result
    return json.loads(source,object_pairs_hook=pairs)

def verify_approval_comment(comment, *, expected_comment_id:int, repository:str, pr_number:int,
                            expected_head:str, expected_owner_login:str, expected_owner_id:int,
                            expected_allowed_paths:list[str], expected_checks:list[str],
                            now:dt.datetime, max_ttl:dt.timedelta,
                            expected_decision:str="APPROVE_TRANSITIONAL_BOOTSTRAP",
                            expected_workflow_path:str=".github/workflows/validate-pr-on-claw.yml",
                            expected_workflow_blob_sha:str|None=None):
    if not isinstance(expected_comment_id,int) or isinstance(expected_comment_id,bool) or expected_comment_id < 1: _fail("APPROVAL_COMMENT_ID_INVALID")
    if not isinstance(repository,str) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+",repository): _fail("APPROVAL_REPOSITORY_INVALID")
    if not isinstance(pr_number,int) or isinstance(pr_number,bool) or pr_number < 1: _fail("APPROVAL_PR_INVALID")
    if not isinstance(expected_owner_login,str) or not expected_owner_login or not isinstance(expected_owner_id,int) or isinstance(expected_owner_id,bool) or expected_owner_id < 1: _fail("APPROVAL_EXPECTED_OWNER_INVALID")
    if not isinstance(comment,dict): _fail("APPROVAL_RESPONSE_INVALID")
    if comment.get("id") != expected_comment_id: _fail("APPROVAL_COMMENT_ID_MISMATCH")
    user=comment.get("user")
    if not isinstance(user,dict) or user.get("login") != expected_owner_login or user.get("id") != expected_owner_id: _fail("APPROVAL_OWNER_MISMATCH")
    if comment.get("author_association") != "OWNER": _fail("APPROVAL_NOT_OWNER")
    if comment.get("issue_url") != f"https://api.github.com/repos/{repository}/issues/{pr_number}": _fail("APPROVAL_ISSUE_URL_INVALID")
    url=comment.get("html_url")
    if url != f"https://github.com/{repository}/pull/{pr_number}#issuecomment-{expected_comment_id}": _fail("APPROVAL_URL_INVALID")
    if comment.get("created_at") != comment.get("updated_at"): _fail("APPROVAL_COMMENT_MODIFIED")
    if not isinstance(comment.get("body"),str): _fail("APPROVAL_BODY_NOT_STRING")
    if len(comment["body"].encode("utf-8")) > 65536: _fail("APPROVAL_BODY_TOO_LARGE")
    try: body=loads_no_duplicates(comment["body"])
    except json.JSONDecodeError as exc: raise ApprovalError("APPROVAL_BODY_JSON_INVALID") from exc
    if not isinstance(body,dict) or set(body) != FIELDS: _fail("APPROVAL_BODY_NOT_CLOSED")
    canonical=json.dumps(body,sort_keys=True,separators=(",",":"))
    if comment["body"] != canonical: _fail("APPROVAL_BODY_NOT_CANONICAL")
    if body["decision"] != expected_decision: _fail("APPROVAL_DECISION_INVALID")
    if body["repository"] != repository or body["pr_number"] != pr_number: _fail("APPROVAL_TARGET_MISMATCH")
    if body["commit_id"] != expected_head or not _sha(expected_head): _fail("APPROVAL_COMMIT_MISMATCH")
    for key in ("head_tree","base_sha","controller_sha","controller_tree","workflow_blob_sha"):
        if not _sha(body[key]): _fail("APPROVAL_IDENTITY_INVALID")
    if body["base_sha"] != body["controller_sha"]: _fail("APPROVAL_BASE_CONTROLLER_MISMATCH")
    if body["workflow_path"] != expected_workflow_path: _fail("APPROVAL_WORKFLOW_MISMATCH")
    if expected_workflow_blob_sha is not None and body["workflow_blob_sha"] != expected_workflow_blob_sha: _fail("APPROVAL_WORKFLOW_BLOB_MISMATCH")
    if not isinstance(body["allowed_paths"],list) or len(body["allowed_paths"]) > 96 or not all(isinstance(item,str) and 1 <= len(item) <= 300 for item in body["allowed_paths"]): _fail("APPROVAL_ALLOWED_PATHS_INVALID")
    if not isinstance(body["checks"],list) or len(body["checks"]) > 16 or not all(isinstance(item,str) and 1 <= len(item) <= 100 for item in body["checks"]): _fail("APPROVAL_CHECKS_INVALID")
    if body["allowed_paths"] != expected_allowed_paths: _fail("APPROVAL_ALLOWED_PATHS_MISMATCH")
    if body["checks"] != expected_checks: _fail("APPROVAL_CHECKS_MISMATCH")
    if len(set(body["allowed_paths"])) != len(body["allowed_paths"]) or len(set(body["checks"])) != len(body["checks"]): _fail("APPROVAL_LIST_DUPLICATE")
    if not isinstance(body["nonce"],str) or not NONCE.fullmatch(body["nonce"]): _fail("APPROVAL_NONCE_INVALID")
    created_source=comment.get("created_at"); created=_time(created_source,"APPROVAL_CREATED_AT_INVALID"); expiry=_time(body["expires_at"],"APPROVAL_EXPIRY_INVALID")
    if now.tzinfo is None or now.utcoffset() != dt.timedelta(0): _fail("APPROVAL_NOW_INVALID")
    if created > now + MAX_FUTURE_CLOCK_SKEW: _fail("APPROVAL_CREATED_IN_FUTURE")
    if expiry <= created: _fail("APPROVAL_EXPIRY_BEFORE_CREATION")
    if expiry-created > max_ttl: _fail("APPROVAL_TTL_EXCEEDED")
    if expiry <= now: _fail("APPROVAL_EXPIRED")
    return {**body,"approval_comment_id":expected_comment_id,"approval_comment_url":url,"approval_owner_login":expected_owner_login,"approval_owner_id":expected_owner_id,"approval_body_sha256":hashlib.sha256(canonical.encode()).hexdigest(),"approval_created_at":created_source}

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--approval-comment",type=Path,required=True); p.add_argument("--repository-metadata",type=Path,required=True); p.add_argument("--changed-files",type=Path,required=True); p.add_argument("--repository",required=True); p.add_argument("--pr-number",type=int,required=True); p.add_argument("--expected-head",required=True); p.add_argument("--approval-comment-id",type=int,required=True); p.add_argument("--allowed-path",action="append",default=[]); p.add_argument("--check",action="append",default=[]); p.add_argument("--expected-decision",default="APPROVE_TRANSITIONAL_BOOTSTRAP"); p.add_argument("--expected-workflow-path",default=".github/workflows/validate-pr-on-claw.yml"); p.add_argument("--expected-workflow-blob-sha"); p.add_argument("--max-ttl-seconds",type=int,default=3600); p.add_argument("--output",type=Path,required=True); a=p.parse_args(argv)
    try:
        if any(path.stat().st_size > 1_048_576 for path in (a.approval_comment,a.repository_metadata,a.changed_files)): _fail("API_RESPONSE_TOO_LARGE")
        comment=loads_no_duplicates(a.approval_comment.read_text(encoding="utf-8")); repo=loads_no_duplicates(a.repository_metadata.read_text(encoding="utf-8")); files=loads_no_duplicates(a.changed_files.read_text(encoding="utf-8")); owner=repo.get("owner") if isinstance(repo,dict) else None
        if not isinstance(repo,dict) or repo.get("full_name") != a.repository: _fail("REPOSITORY_IDENTITY_MISMATCH")
        if not isinstance(owner,dict) or not isinstance(owner.get("login"),str) or not isinstance(owner.get("id"),int) or isinstance(owner.get("id"),bool) or owner["id"] < 1: _fail("REPOSITORY_OWNER_INVALID")
        if not isinstance(files,list) or not all(isinstance(item,dict) and isinstance(item.get("filename"),str) for item in files): _fail("PR_FILES_INVALID")
        actual_paths=sorted(item["filename"] for item in files)
        if len(actual_paths) != len(set(actual_paths)) or actual_paths != sorted(a.allowed_path): _fail("PR_CHANGED_PATHS_MISMATCH")
        result=verify_approval_comment(comment,expected_comment_id=a.approval_comment_id,repository=a.repository,pr_number=a.pr_number,expected_head=a.expected_head,expected_owner_login=owner["login"],expected_owner_id=owner["id"],expected_allowed_paths=a.allowed_path,expected_checks=a.check,now=dt.datetime.now(dt.timezone.utc),max_ttl=dt.timedelta(seconds=a.max_ttl_seconds),expected_decision=a.expected_decision,expected_workflow_path=a.expected_workflow_path,expected_workflow_blob_sha=a.expected_workflow_blob_sha)
        a.output.write_text(json.dumps(result,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8"); return 0
    except (OSError,json.JSONDecodeError,ApprovalError) as exc: print(f"SOURCE_CONTROLLER_ERROR:{exc}",file=sys.stderr); return 2
if __name__=="__main__": raise SystemExit(main())
