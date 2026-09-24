#!/usr/bin/python3.14
"""Offline independent verifier for a captured Claw host deployment approval."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

try:
    from scripts.claw_host_deployment_contract import (
        ApprovalError, ContractError, canonical_bytes, load_closed_bytes,
        verify_approval, verify_request,
    )
except ModuleNotFoundError:
    sys.path.insert(0, "/usr/local/libexec/mee-claw-host-deploy-lib")
    from claw_host_deployment_contract import (  # type: ignore[no-redef]
        ApprovalError, ContractError, canonical_bytes, load_closed_bytes,
        verify_approval, verify_request,
    )


def _read(path: Path, limit: int = 1_048_576) -> dict[str, object]:
    return load_closed_bytes(path.read_bytes(), max_bytes=limit)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--approval-comment", type=Path, required=True)
    parser.add_argument("--repository-metadata", type=Path, required=True)
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--installed-identity", type=Path, required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--approval-comment-id", type=int, required=True)
    parser.add_argument("--release-id", type=int, required=True)
    parser.add_argument("--policy-sha256", required=True)
    parser.add_argument("--closure-sha256", required=True)
    parser.add_argument("--now")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        now = dt.datetime.now(dt.timezone.utc) if args.now is None else dt.datetime.fromisoformat(args.now.replace("Z", "+00:00"))
        request = verify_request(
            {
                "schema_version": "claw-host-deployment-request-v1",
                "action": "begin",
                "github_token": "offline-verifier-placeholder",
                "repository": args.repository,
                "approval_comment_id": args.approval_comment_id,
                "release_id": args.release_id,
                "transaction_id": None,
            },
            expected_action="begin",
        )
        result = verify_approval(
            _read(args.approval_comment),
            _read(args.repository_metadata),
            _read(args.release),
            request=request,
            installed_identity=_read(args.installed_identity),
            expected_policy_sha256=args.policy_sha256,
            expected_closure_sha256=args.closure_sha256,
            now=now,
        )
        if args.output:
            args.output.write_bytes(canonical_bytes(result))
        return 0
    except (OSError, ValueError, ContractError, ApprovalError) as exc:
        print(f"CLAW_HOST_DEPLOYMENT_APPROVAL_ERROR:{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
