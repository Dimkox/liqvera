"""Case-specific live acceptance executors with closed observations."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

from .public_read import GrantError, PublicReadGrant, PublicReadPlan, _resolve, consume_public_read_grant


def execute_a07(plan: PublicReadPlan, grant: PublicReadGrant, *, identity: dict[str, str],
                state_dir: Path, root: Path, now) -> dict[str, object]:
    grant.authorize(plan, subject_commit=identity["commit"], subject_tree=identity["tree"], now=now())
    state_identity = consume_public_read_grant(state_dir, grant)
    build = subprocess.run(["npm", "--prefix", str(root / "apps/mezo-gateway"), "run", "build"], cwd=root,
                           capture_output=True, text=True, timeout=30, check=False,
                           env={"PATH": os.environ.get("PATH", "")})
    if build.returncode != 0:
        raise GrantError("A07_HARNESS_BUILD_FAILED")
    command = ["node", str(root / "apps/mezo-gateway/scripts/a07-source-unavailable.mjs")]
    completed = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=5, check=False,
                               env={"PATH": os.environ.get("PATH", "")})
    try:
        raw = json.loads(completed.stdout)
    except json.JSONDecodeError:
        raise GrantError("A07_HARNESS_INVALID") from None
    expected = {"schema": "liqvera-a07-source-unavailable/v1", "adapter": "HttpReportService.build",
                "request_count": 1, "reason": "SOURCE_UNAVAILABLE", "source_mode": "live-public",
                "fixture_fallback_used": False, "artifact_emitted": False}
    if completed.returncode != 0 or raw != expected or completed.stderr:
        raise GrantError("A07_SEMANTICS_FAILED")
    return {**expected, "grant_id": grant.grant_id, "grant_digest": grant.digest,
            "plan_sha256": plan.digest, "subject_commit": identity["commit"],
            "subject_tree": identity["tree"], "state_dir_identity": state_identity,
            "stdout_sha256": hashlib.sha256(completed.stdout.encode()).hexdigest(),
            "build_stdout_sha256": hashlib.sha256(build.stdout.encode()).hexdigest()}


def execute_a29(plan: PublicReadPlan, grant: PublicReadGrant, *, identity: dict[str, str],
                state_dir: Path, now, runner=subprocess.run, resolver=_resolve) -> dict[str, object]:
    grant.authorize(plan, subject_commit=identity["commit"], subject_tree=identity["tree"], now=now())
    before = tuple(resolver("github.com")); connected = tuple(resolver("github.com"))
    grant.validate_resolution(before, connected)
    state_identity = consume_public_read_grant(state_dir, grant)
    with tempfile.TemporaryDirectory(prefix="liqvera-a29-") as temporary:
        destination = Path(temporary) / "clone"
        env = {"PATH": os.environ.get("PATH", ""), "GIT_TERMINAL_PROMPT": "0", "GIT_CONFIG_NOSYSTEM": "1",
               "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_ASKPASS": "/bin/false", "SSH_ASKPASS": "/bin/false"}
        command = ["git", "-c", "credential.helper=", "-c", "http.followRedirects=false", "-c", "protocol.version=2",
                   "-c", f"http.curloptResolve=github.com:443:{connected[0]}",
                   "clone", "--quiet", "--no-tags", "--depth=1", "--filter=blob:none", plan.url, str(destination)]
        completed = runner(command, capture_output=True, text=True, timeout=plan.timeout_seconds, env=env, check=False)
        if completed.returncode != 0:
            raise GrantError("A29_CLONE_FAILED")
        total = sum(item.stat().st_size for item in destination.rglob("*") if item.is_file() and not item.is_symlink())
        if total > plan.max_response_bytes:
            raise GrantError("A29_CLONE_TOO_LARGE")
        def git(*args: str) -> str:
            return subprocess.check_output(["git", "-C", destination, *args], text=True, timeout=3,
                                           env=env).strip()
        commit, tree, origin = git("rev-parse", "HEAD"), git("rev-parse", "HEAD^{tree}"), git("remote", "get-url", "origin")
        if (commit, tree, origin) != (identity["commit"], identity["tree"], plan.url):
            raise GrantError("A29_PROVENANCE_MISMATCH")
        return {"schema": "liqvera-a29-anonymous-clone/v1", "commit": commit, "tree": tree,
                "origin": origin, "clone_size_bytes": total, "credential_prompt": False,
                "redirects_allowed": False, "resolved_addresses": list(before), "connected_address": connected[0],
                "grant_id": grant.grant_id, "grant_digest": grant.digest,
                "plan_sha256": plan.digest, "subject_commit": identity["commit"],
                "subject_tree": identity["tree"], "state_dir_identity": state_identity}
