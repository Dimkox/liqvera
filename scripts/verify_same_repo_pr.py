#!/usr/bin/env python3
"""Closed, deterministic GitHub same-repository PR identity verifier."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SHA = re.compile(r"^[0-9a-f]{40}$")


class ControllerError(ValueError):
    pass


def fail(code: str) -> None:
    raise ControllerError(code)


def _sha(value: object, code: str) -> str:
    if not isinstance(value, str) or not SHA.fullmatch(value): fail(code)
    return value


def verify_pull_request(pr: object, *, repository: str, pr_number: int, expected_head: str,
                        controller_sha: str, head_tree: str, expected_tree: str,
                        ancestry_proven: bool, compare: object | None = None) -> dict[str, object]:
    if not isinstance(pr, dict): fail("PR_RESPONSE_NOT_OBJECT")
    if pr.get("number") != pr_number: fail("PR_NUMBER_MISMATCH")
    if pr.get("state") != "open": fail("PR_NOT_OPEN")
    base, head = pr.get("base"), pr.get("head")
    if not isinstance(base, dict) or not isinstance(head, dict): fail("PR_SHAPE_INVALID")
    if base.get("ref") != "main": fail("PR_BASE_BRANCH_MISMATCH")
    for side, value in (("BASE", base), ("HEAD", head)):
        repo = value.get("repo")
        if not isinstance(repo, dict) or repo.get("full_name") != repository:
            fail(f"PR_{side}_REPOSITORY_MISMATCH")
    if _sha(head.get("sha"), "PR_HEAD_SHA_INVALID") != _sha(expected_head, "EXPECTED_HEAD_SHA_INVALID"):
        fail("PR_HEAD_SHA_MISMATCH")
    if _sha(base.get("sha"), "PR_BASE_SHA_INVALID") != _sha(controller_sha, "CONTROLLER_SHA_INVALID"):
        fail("PR_BASE_CONTROLLER_MISMATCH")
    if not ancestry_proven: fail("PR_ANCESTRY_UNPROVEN")
    if compare is not None:
        if not isinstance(compare,dict): fail("COMPARE_RESPONSE_INVALID")
        base_commit, head_commit = compare.get("base_commit"), compare.get("merge_base_commit")
        commits = compare.get("commits")
        if not isinstance(base_commit,dict) or base_commit.get("sha") != controller_sha: fail("COMPARE_BASE_MISMATCH")
        if compare.get("status") not in {"ahead","identical"}: fail("COMPARE_STATUS_INVALID")
        if expected_head != controller_sha:
            if not isinstance(commits,list) or not commits or not isinstance(commits[-1],dict) or commits[-1].get("sha") != expected_head: fail("COMPARE_HEAD_MISMATCH")
        if not isinstance(head_commit,dict) or head_commit.get("sha") != controller_sha: fail("COMPARE_MERGE_BASE_MISMATCH")
    if _sha(head_tree, "HEAD_TREE_INVALID") != _sha(expected_tree, "EXPECTED_TREE_INVALID"):
        fail("PR_TREE_MISMATCH")
    return {"repository": repository, "pr_number": pr_number, "head_sha": expected_head,
            "head_tree": head_tree, "base_sha": controller_sha, "controller_sha": controller_sha}


def load_closed(path: Path, fields: set[str], prefix: str) -> dict[str, object]:
    if path.stat().st_size > 1_048_576: fail(f"{prefix}_TOO_LARGE")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict): fail(f"{prefix}_NOT_OBJECT")
    extra = set(value) - fields
    if extra: fail(f"{prefix}_UNKNOWN_FIELD:{sorted(extra)[0]}")
    return value


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="mode", required=True)
    p = sub.add_parser("payload"); p.add_argument("path", type=Path)
    f = sub.add_parser("full")
    for name in ("pr","commit","compare"):
        f.add_argument(f"--{name}",type=Path,required=True)
    f.add_argument("--repository",required=True); f.add_argument("--pr-number",type=int,required=True)
    f.add_argument("--expected-head",required=True); f.add_argument("--controller-sha",required=True); f.add_argument("--output",type=Path,required=True)
    args = parser.parse_args(argv)
    try:
        if args.mode == "full":
            pr=json.loads(args.pr.read_text()); commit=json.loads(args.commit.read_text()); compare=json.loads(args.compare.read_text())
            tree=commit.get("commit",{}).get("tree",{}).get("sha") if isinstance(commit,dict) else None
            result=verify_pull_request(pr,repository=args.repository,pr_number=args.pr_number,expected_head=args.expected_head,controller_sha=args.controller_sha,head_tree=tree,expected_tree=tree,ancestry_proven=True,compare=compare)
            args.output.write_text(json.dumps(result,sort_keys=True,separators=(",",":"))+"\n"); return 0
        value = load_closed(args.path, {"pr_number", "expected_head_sha", "approval_comment_id"}, "PAYLOAD")
        if not isinstance(value.get("pr_number"), int) or value["pr_number"] < 1: fail("PAYLOAD_PR_NUMBER_INVALID")
        _sha(value.get("expected_head_sha"), "PAYLOAD_HEAD_SHA_INVALID")
        if not isinstance(value.get("approval_comment_id"), int) or isinstance(value["approval_comment_id"], bool) or value["approval_comment_id"] < 1: fail("PAYLOAD_APPROVAL_COMMENT_ID_INVALID")
        print(json.dumps(value, sort_keys=True, separators=(",", ":")))
        return 0
    except (ControllerError, OSError, json.JSONDecodeError) as exc:
        print(f"SOURCE_CONTROLLER_ERROR:{exc}", file=sys.stderr); return 2


if __name__ == "__main__": raise SystemExit(main())
