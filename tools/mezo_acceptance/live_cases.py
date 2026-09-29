"""Case-specific live acceptance executors with closed observations."""

from __future__ import annotations

import hashlib
import json
import os
import resource
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from .public_read import GrantError, PublicReadGrant, PublicReadPlan, consume_public_read_grant


@dataclass(frozen=True)
class ResourceEnvelope:
    timeout_seconds: int
    max_aggregate_disk_bytes: int
    max_single_file_bytes: int
    max_process_memory_bytes: int
    max_output_bytes: int


def run_resource_bounded(
    command: list[str],
    root: Path,
    envelope: ResourceEnvelope,
    *,
    environment: dict[str, str] | None = None,
    poll_seconds: float = 0.01,
) -> subprocess.CompletedProcess[bytes]:
    stdout = root / "stdout.bin"
    stderr = root / "stderr.bin"

    def limits():
        resource.setrlimit(
            resource.RLIMIT_FSIZE,
            (envelope.max_single_file_bytes, envelope.max_single_file_bytes),
        )
        resource.setrlimit(
            resource.RLIMIT_AS,
            (envelope.max_process_memory_bytes, envelope.max_process_memory_bytes),
        )

    with stdout.open("xb") as out, stderr.open("xb") as err:
        process = subprocess.Popen(
            command,
            cwd=root,
            stdout=out,
            stderr=err,
            preexec_fn=limits,
            env=environment or {"PATH": os.environ.get("PATH", "")},
        )
        deadline = time.monotonic() + envelope.timeout_seconds
        reason = None
        while process.poll() is None:
            files = [item for item in root.rglob("*") if item.is_file() and not item.is_symlink()]
            sizes = [item.stat().st_size for item in files]
            if sum(sizes) > envelope.max_aggregate_disk_bytes:
                reason = "A29_AGGREGATE_DISK_CAP"
            elif stdout.stat().st_size + stderr.stat().st_size > envelope.max_output_bytes:
                reason = "A29_OUTPUT_CAP"
            elif time.monotonic() >= deadline:
                reason = "A29_TIMEOUT"
            if reason:
                process.terminate()
                try:
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                raise GrantError(reason)
            time.sleep(poll_seconds)
    completed = subprocess.CompletedProcess(
        command, process.returncode, stdout.read_bytes(), stderr.read_bytes()
    )
    if completed.returncode != 0:
        raise GrantError("A29_PROCESS_FAILED")
    return completed


def run_bounded_git_clone(
    url: str,
    destination: Path,
    address: str,
    envelope: ResourceEnvelope,
) -> subprocess.CompletedProcess[bytes]:
    """Run the reviewed clone command inside a hard local resource envelope.

    This bounds disk, output, memory, and elapsed time. It deliberately does not
    claim a network-byte limit; callers must keep A29 blocked while that stronger
    property is unavailable.
    """
    if url != "https://github.com/Dimkox/liqvera.git":
        raise GrantError("A29_TARGET_MISMATCH")
    if destination.exists() or not destination.parent.is_dir():
        raise GrantError("A29_DESTINATION_UNSAFE")
    command = [
        "git",
        "-c",
        "credential.helper=",
        "-c",
        "http.followRedirects=false",
        "-c",
        "protocol.version=2",
        "-c",
        f"http.curloptResolve=github.com:443:{address}",
        "clone",
        "--quiet",
        "--no-tags",
        "--depth=1",
        "--filter=blob:none",
        url,
        str(destination),
    ]
    environment = {
        "PATH": os.environ.get("PATH", ""),
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_ASKPASS": "/bin/false",
        "SSH_ASKPASS": "/bin/false",
    }
    return run_resource_bounded(
        command,
        destination.parent,
        envelope,
        environment=environment,
    )


def execute_a07(
    plan: PublicReadPlan,
    grant: PublicReadGrant,
    *,
    identity: dict[str, str],
    state_dir: Path,
    root: Path,
    now,
) -> dict[str, object]:
    grant.authorize(
        plan, subject_commit=identity["commit"], subject_tree=identity["tree"], now=now()
    )
    state_identity = consume_public_read_grant(state_dir, grant)
    build = subprocess.run(
        ["npm", "--prefix", str(root / "apps/mezo-gateway"), "run", "build"],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
        env={"PATH": os.environ.get("PATH", "")},
    )
    if build.returncode != 0:
        raise GrantError("A07_HARNESS_BUILD_FAILED")
    command = ["node", str(root / "apps/mezo-gateway/scripts/a07-source-unavailable.mjs")]
    completed = subprocess.run(
        command,
        cwd=root,
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
        env={"PATH": os.environ.get("PATH", "")},
    )
    try:
        raw = json.loads(completed.stdout)
    except json.JSONDecodeError:
        raise GrantError("A07_HARNESS_INVALID") from None
    expected = {
        "schema": "liqvera-a07-source-unavailable/v1",
        "adapter": "HttpReportService.build",
        "request_count": 1,
        "reason": "SOURCE_UNAVAILABLE",
        "source_mode": "live-public",
        "fixture_fallback_used": False,
        "artifact_emitted": False,
    }
    if completed.returncode != 0 or raw != expected or completed.stderr:
        raise GrantError("A07_SEMANTICS_FAILED")
    return {
        **expected,
        "grant_id": grant.grant_id,
        "grant_digest": grant.digest,
        "plan_sha256": plan.digest,
        "subject_commit": identity["commit"],
        "subject_tree": identity["tree"],
        "state_dir_identity": state_identity,
        "stdout_sha256": hashlib.sha256(completed.stdout.encode()).hexdigest(),
        "build_stdout_sha256": hashlib.sha256(build.stdout.encode()).hexdigest(),
    }
