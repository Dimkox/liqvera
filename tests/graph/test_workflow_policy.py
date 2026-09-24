"""Static policy checks for active Claw architecture gates."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from collections import Counter
import re
import os
import subprocess

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class WorkflowJob:
    path: str
    runs_on: list[str] | None


@dataclass(frozen=True)
class ActiveWorkflows:
    jobs: tuple[WorkflowJob, ...]


@dataclass(frozen=True)
class Workflow:
    permissions: dict[str, str]
    has_docker_socket: bool
    has_deploy_or_registry_step: bool


def _load_yaml(path: Path) -> dict[str, object]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict), f"workflow is not a mapping: {path}"
    return loaded


def _runs_on(value: object) -> list[str] | None:
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    return None


def load_active_workflows(workflows_root: Path) -> ActiveWorkflows:
    jobs: list[WorkflowJob] = []
    for path in sorted(
        path
        for path in workflows_root.iterdir()
        if path.is_file() and path.suffix in {".yaml", ".yml"}
    ):
        workflow = _load_yaml(path)
        declared_jobs = workflow.get("jobs")
        assert isinstance(declared_jobs, dict), f"workflow has no jobs: {path}"
        for name, job in declared_jobs.items():
            assert isinstance(name, str) and isinstance(job, dict)
            jobs.append(
                WorkflowJob(
                    path=f"{path.as_posix()}:{name}",
                    runs_on=_runs_on(job.get("runs-on")),
                )
            )
    return ActiveWorkflows(tuple(jobs))


def load_workflow(path: Path) -> Workflow:
    workflow = _load_yaml(path)
    permissions = workflow.get("permissions")
    assert isinstance(permissions, dict)
    normalized_permissions = {
        key: value
        for key, value in permissions.items()
        if isinstance(key, str) and isinstance(value, str)
    }
    source = path.read_text(encoding="utf-8").casefold()
    return Workflow(
        permissions=normalized_permissions,
        has_docker_socket=bool(re.search(r"/var/run/docker\.sock|docker\.sock", source)),
        has_deploy_or_registry_step=bool(
            re.search(r"\b(?:deploy|promotion|promote|registry|docker\s+(?:push|login))\b", source)
        ),
    )


def test_all_active_gate_jobs_are_claw_only() -> None:
    workflows = load_active_workflows(ROOT / ".github" / "workflows")
    offenders = [job.path for job in workflows.jobs if job.runs_on not in (["self-hosted", "claw"], ["self-hosted", "claw", "claw-engine-runner"])]
    assert offenders == []


def test_pr_gate_has_no_mutation_authority() -> None:
    gate = load_workflow(ROOT / ".github" / "workflows" / "verify-a2-pr-on-claw.yml")
    assert gate.permissions == {"contents": "read"}
    assert gate.has_docker_socket is False
    assert gate.has_deploy_or_registry_step is False


def test_active_workflow_scan_rejects_hosted_yaml_extension(tmp_path: Path) -> None:
    malicious = tmp_path / "malicious.yaml"
    malicious.write_text(
        "jobs:\n  hosted:\n    runs-on: [ubuntu-24.04]\n",
        encoding="utf-8",
    )

    workflows = load_active_workflows(tmp_path)

    assert [(job.path, job.runs_on) for job in workflows.jobs] == [
        (f"{malicious.as_posix()}:hosted", ["ubuntu-24.04"]),
    ]


def test_matrix_workspaces_are_shard_qualified_in_both_workflows() -> None:
    expected = (
        'workspace_root="${RUNNER_TEMP}/${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}'
        '-${job_name}-${workspace_shard}"'
    )
    for filename in ("verify-a2-pr-on-claw.yml", "build-a2-on-claw.yml"):
        workflow = (ROOT / ".github" / "workflows" / filename).read_text(encoding="utf-8")
        assert "CLAW_WORKSPACE_SHARD: ${{ matrix.postgres_shard }}" in workflow
        assert expected in workflow
        assert "scripts/cleanup-claw-workspace.sh" in workflow


def test_postgres_runtime_uses_random_secret_loopback_ephemeral_port_and_cleanup() -> None:
    identity = (
        "a2_${{ github.run_id }}_${{ github.run_attempt }}_"
        "${{ github.job }}_${{ matrix.postgres_shard }}"
    )
    for filename in ("verify-a2-pr-on-claw.yml", "build-a2-on-claw.yml"):
        workflow = (ROOT / ".github" / "workflows" / filename).read_text(encoding="utf-8")
        assert "postgres_shard: postgres_16_11" in workflow
        assert "postgres_shard: postgres_17_7" in workflow
        assert "services:" not in workflow
        assert "5432:5432" not in workflow
        assert not re.search(r"(?m)^\s*POSTGRES_PASSWORD:",workflow)
        assert "openssl rand -hex 32" in workflow
        assert "::add-mask::%s" in workflow
        assert "--publish 127.0.0.1::5432" in workflow
        assert "--network host" not in workflow and "--privileged" not in workflow
        assert "docker port \"${postgres_container}\" 5432/tcp" in workflow
        assert "docker rm --force \"${postgres_container}\"" in workflow
        assert "test -z \"$(docker ps -aq --filter \"name=^/${postgres_container}$\")\"" in workflow
        assert "postgres-runtime.env" in workflow
        assert 'postgres_identity="a2_${GITHUB_RUN_ID}_${GITHUB_RUN_ATTEMPT}_${job_name}_${workspace_shard}"' in workflow


def test_pr_execution_has_no_artifact_and_database_cleanup_precedes_non_authoritative_status():
    workflow=(ROOT/".github/workflows/verify-a2-pr-on-claw.yml").read_text(encoding="utf-8")
    assert "id: postgres_runtime" in workflow
    assert "printf 'postgres_password=%s\\n' \"${postgres_password}\" >>\"${GITHUB_OUTPUT}\"" in workflow
    assert "TRUSTED_POSTGRES_PASSWORD: ${{ steps.postgres_runtime.outputs.postgres_password }}" in workflow
    assert '[[ "${TRUSTED_POSTGRES_PASSWORD}" =~ ^[0-9a-f]{64}$ ]]' in workflow
    assert "verification.log" not in workflow
    assert "evidence_dir" not in workflow
    assert "summary.txt" not in workflow
    assert "upload-artifact" not in workflow
    cleanup=workflow.index("Validate trusted runtime and cleanup PostgreSQL")
    summary=workflow.index("Write non-authoritative verification status")
    fallback=workflow.index("Final PostgreSQL cleanup fallback")
    assert cleanup < summary < fallback
    assert "steps.cleanup_postgres.outputs.cleanup_proven == 'true'" in workflow
    assert "authority: NONE" in workflow
    assert "GITHUB_STEP_SUMMARY" in workflow
    assert 'rm -f -- "${workspace_root}/postgres-container.env" "${workspace_root}/postgres-runtime.env"' in workflow
    assert workflow.count("if: always()") >= 4

    build=(ROOT/".github/workflows/build-a2-on-claw.yml").read_text(encoding="utf-8")
    assert "actions/upload-artifact@" in build


def test_docker_commands_are_closed_to_approved_lifecycle_and_build_verbs():
    verify=(ROOT/".github/workflows/verify-a2-pr-on-claw.yml").read_text(encoding="utf-8")
    build=(ROOT/".github/workflows/build-a2-on-claw.yml").read_text(encoding="utf-8")
    verify_verbs=set(re.findall(r"\bdocker\s+([a-z]+)",verify))
    build_verbs=set(re.findall(r"\bdocker\s+([a-z]+)",build))
    assert verify_verbs == {"run","port","inspect","rm","ps"}
    assert build_verbs <= {"run","port","inspect","rm","ps","build","create","cp","image"}
    for workflow in (verify,build):
        assert not re.search(r"(?m)^\s*docker\s+(?:exec|mount|volume)\b",workflow)
        assert "/var/run/docker.sock" not in workflow
        docker_lines="\n".join(line for line in workflow.splitlines() if "docker " in line)
        assert not re.search(r"(?:--mount|(?:^|\s)-v(?:\s|=)|--volume|--device|--cap-add|--network|--privileged)",docker_lines)
    expected_run = ('docker run --detach --name "${postgres_container}" --env-file "${env_file}" '
                    '--publish 127.0.0.1::5432 --health-cmd "pg_isready -U ${postgres_identity} '
                    '-d ${postgres_identity}" --health-interval 5s --health-timeout 3s '
                    '--health-retries 12 "${POSTGRES_IMAGE}"')
    common_lifecycle = [
        expected_run,
        'port_projection="$(docker port "${postgres_container}" 5432/tcp)"',
        '[[ "$(docker inspect --format \'{{.State.Health.Status}}\' "${postgres_container}")" == healthy ]] && exit 0',
    ]
    expected_verify_lifecycle = common_lifecycle + [
        'docker rm --force "${postgres_container}" >/dev/null 2>&1 || cleanup_failed=1',
        'test -z "$(docker ps -aq --filter "name=^/${postgres_container}$")" || cleanup_failed=1',
        'docker rm --force "${postgres_container}" >/dev/null 2>&1 || true',
        'test -z "$(docker ps -aq --filter "name=^/${postgres_container}$")"',
    ]
    expected_build_lifecycle = common_lifecycle + [
        'docker rm --force "${postgres_container}" >/dev/null 2>&1 || true',
        'test -z "$(docker ps -aq --filter "name=^/${postgres_container}$")"',
    ]
    for workflow, expected in ((verify, expected_verify_lifecycle), (build, expected_build_lifecycle)):
        normalized_lines = [" ".join(line.strip().split()) for line in workflow.splitlines()]
        run_lines = [line for line in normalized_lines if line.startswith("docker run ")]
        assert run_lines == [expected_run]
        postgres_docker_lines = [line for line in normalized_lines if "docker " in line and "postgres_container" in line]
        assert postgres_docker_lines == expected
    assert Counter(re.findall(r"\bdocker\s+([a-z]+)",verify)) == Counter({"rm":2,"ps":2,"run":1,"port":1,"inspect":1})
    assert Counter(re.findall(r"\bdocker\s+([a-z]+)",build)) == Counter({"build":2,"create":2,"cp":2,"image":2,"rm":2,"run":1,"port":1,"inspect":1,"ps":1})


def _postgres_url_is_fully_identity_bound(workflow: str) -> bool:
    expected = 'A2_TEST_DATABASE_URL="postgresql://${postgres_identity}:${postgres_password}@127.0.0.1:${postgres_port}/${postgres_identity}"'
    return expected in workflow


@pytest.mark.parametrize(
    "replacement",
    (
        "postgresql://a2_fixed:",
        ":pg-fixed@localhost:",
        "@localhost:5432/",
        "/a2_fixed",
    ),
)
def test_postgres_url_rejects_any_unbound_identity_or_port_segment(replacement: str) -> None:
    path = ROOT / ".github" / "workflows" / "verify-a2-pr-on-claw.yml"
    workflow = path.read_text(encoding="utf-8")
    assert _postgres_url_is_fully_identity_bound(workflow)

    expected='A2_TEST_DATABASE_URL="postgresql://${postgres_identity}:${postgres_password}@127.0.0.1:${postgres_port}/${postgres_identity}"'
    assert not _postgres_url_is_fully_identity_bound(workflow.replace(expected,replacement))


def test_cleanup_rejects_nonexistent_wrong_path_before_existence_check(tmp_path: Path) -> None:
    runner_temp = tmp_path / "runner-temp"
    runner_temp.mkdir()
    shard = "postgres:16.11"
    expected = runner_temp / "17-2-verify-a2-pr-postgres_16.11"
    environment = {
        **os.environ,
        "RUNNER_TEMP": str(runner_temp),
        "GITHUB_RUN_ID": "17",
        "GITHUB_RUN_ATTEMPT": "2",
        "GITHUB_JOB": "verify-a2-pr",
        "CLAW_WORKSPACE_SHARD": shard,
    }
    script = ROOT / "scripts" / "cleanup-claw-workspace.sh"

    wrong = subprocess.run(
        ["bash", str(script), str(runner_temp / "not-the-expected-root")],
        capture_output=True,
        env=environment,
        text=True,
    )
    absent_exact = subprocess.run(
        ["bash", str(script), str(expected)],
        capture_output=True,
        env=environment,
        text=True,
    )

    assert wrong.returncode == 64
    assert absent_exact.returncode == 0
    assert not expected.exists()
