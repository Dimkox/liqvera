#!/usr/bin/env python3
"""Execute one checked-in, network-free F7 acceptance assertion."""

import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = os.environ.get("LIQVERA_ACCEPTANCE_PYTHON", sys.executable)
COMMANDS = {
    "A01": [PYTHON, "-m", "pytest", "-vv", "tests/contracts/test_acceptance_result.py"],
    "A08": [PYTHON, "-m", "pytest", "-vv", "tests/evidence_report/test_canonical_f3.py"],
    "A09": [PYTHON, "-m", "pytest", "-vv", "tests/installed/test_canonical_f3_installed.py"],
    "A27": [PYTHON, "-m", "pytest", "-vv", "tests/contracts/test_mezo_vectors.py"],
    "A30": ["npm", "test"],
}
BASELINE_COMMIT = "f07562eee1a33df74768e9fa4a3b074783d8c59e"
ASSERTIONS = {
    "A01": "before_after_checks",
    "A08": "bundle_tamper_rejected",
    "A09": "offline_replay_exact",
    "A27": "stage_a_regression",
    "A30": "wallet_recovery",
}


def _git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", ROOT, *args], text=True).strip()


def _command_result(command: list[str], cwd: Path) -> tuple[subprocess.CompletedProcess[bytes], dict]:
    completed = subprocess.run(command, cwd=cwd, capture_output=True, check=False, timeout=900)
    return completed, {
        "interpreter": {"implementation": platform.python_implementation(),
                        "version": platform.python_version(),
                        "executable_sha256": hashlib.sha256(Path(command[0]).read_bytes()).hexdigest()},
        "argv_tail": command[1:], "exit_code": completed.returncode,
        "stdout_sha256": hashlib.sha256(completed.stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(completed.stderr).hexdigest(),
    }


def _a01_observations(current: subprocess.CompletedProcess[bytes], after: tuple[str, str], checks: list[str]) -> dict:
    baseline_tree = _git("rev-parse", f"{BASELINE_COMMIT}^{{tree}}")
    with tempfile.TemporaryDirectory(prefix="liqvera-a01-") as temporary:
        root = Path(temporary)
        archive = root / "baseline.tar"
        subprocess.run(["git", "-C", ROOT, "archive", "--format=tar", "--output", archive,
                        BASELINE_COMMIT], check=True, timeout=60)
        extracted = root / "tree"
        extracted.mkdir()
        with tarfile.open(archive, "r:") as bundle:
            bundle.extractall(extracted, filter="data")
        baseline_command = [PYTHON, "-m", "pytest", "-vv", "tests/contracts/test_acceptance_result.py"]
        baseline, baseline_result = _command_result(baseline_command, extracted)
    if baseline.returncode == 0:
        raise RuntimeError("frozen baseline unexpectedly contains passing F7 acceptance checks")
    return {
        "baseline": {**baseline_result, "commit": BASELINE_COMMIT, "tree": baseline_tree,
                     "status": "EXPECTED_HISTORICAL_FAILURE"},
        "current": {"interpreter": {"implementation": platform.python_implementation(),
                                     "version": platform.python_version(),
                                     "executable_sha256": hashlib.sha256(Path(PYTHON).read_bytes()).hexdigest()},
                    "argv_tail": COMMANDS["A01"][1:], "exit_code": current.returncode,
                    "stdout_sha256": hashlib.sha256(current.stdout).hexdigest(),
                    "stderr_sha256": hashlib.sha256(current.stderr).hexdigest(),
                    "commit": after[0], "tree": after[1], "status": "PASS", "checks": checks},
        "expected_delta": "BASELINE_LACKS_F7_ACCEPTANCE_CONTRACT_CURRENT_PASSES",
    }


def _a27_observations(after: tuple[str, str], checks: list[str]) -> dict:
    stage_command = [PYTHON, "-m", "pytest", "-vv",
                     "tests/readonly_analyzer/test_cli_decision.py::test_valid_package_emits_insufficient_evidence",
                     "tests/contracts/test_decision.py::test_stage_a_decision_code_is_the_closed_four"]
    stage, stage_result = _command_result(stage_command, ROOT)
    if stage.returncode:
        raise RuntimeError("canonical Stage A verdict checks failed")
    stage_checks = sorted(set(re.findall(r"^(tests/[^ ]+::[^ ]+) PASSED", stage.stdout.decode(), re.MULTILINE)))
    artifact_command = [PYTHON, "-B", "scripts/check-stage-a-artifacts.py", "--forbid-path",
                        "cmd/**", "internal/**", "go.mod", "go.sum", "--forbid-binary", "engine"]
    artifacts, artifact_result = _command_result(artifact_command, ROOT)
    if artifacts.returncode:
        raise RuntimeError("canonical Stage A artifact verifier failed")
    fixture = ROOT / "tests/fixtures/shadow-golden-v1.ndjson"
    terminal = ROOT / "tests/fixtures/shadow-golden-v1.terminal.sha256"
    baseline_fixture = subprocess.check_output(
        ["git", "-C", ROOT, "show", f"{BASELINE_COMMIT}:tests/fixtures/shadow-golden-v1.ndjson"]
    )
    baseline_terminal = subprocess.check_output(
        ["git", "-C", ROOT, "show", f"{BASELINE_COMMIT}:tests/fixtures/shadow-golden-v1.terminal.sha256"]
    ).decode().strip()
    return {
        "subject_commit": after[0], "subject_tree": after[1], "vector_checks": checks,
        "stage_a": {**stage_result, "checks": stage_checks,
                    "verdict": "INSUFFICIENT_EVIDENCE", "go_possible": False},
        "artifact_verifier": {**artifact_result, "status": "PASS"},
        "fixture": {"path": "tests/fixtures/shadow-golden-v1.ndjson",
                    "baseline_commit": BASELINE_COMMIT,
                    "baseline_sha256": hashlib.sha256(baseline_fixture).hexdigest(),
                    "baseline_record_count": len(baseline_fixture.splitlines()),
                    "baseline_terminal_sha256": baseline_terminal,
                    "sha256": hashlib.sha256(fixture.read_bytes()).hexdigest(),
                    "record_count": len(fixture.read_bytes().splitlines()),
                    "terminal_sha256": terminal.read_text().strip()},
    }


def _observations(case_id: str, completed: subprocess.CompletedProcess[bytes], before: tuple[str, str]) -> dict:
    text = completed.stdout.decode("utf-8", "strict")
    after = (_git("rev-parse", "HEAD"), _git("rev-parse", "HEAD^{tree}"))
    if _git("status", "--porcelain", "--untracked-files=all") or after != before:
        raise RuntimeError("assertion changed the repository subject")
    pytest_checks = sorted(set(re.findall(r"^(tests/[^ ]+::[^ ]+) PASSED", text, re.MULTILINE)))
    node_checks = sorted(set(re.findall(r"^[✔✓] (.+?) \([^)]+\)$", text, re.MULTILINE)))
    checks = pytest_checks or node_checks
    common = {"checks": checks, "subject_commit": after[0], "subject_tree": after[1]}
    if case_id == "A01":
        subprocess.run(["git", "-C", ROOT, "merge-base", "--is-ancestor", BASELINE_COMMIT, after[0]], check=True)
        return _a01_observations(completed, after, checks)
    if case_id == "A08":
        return common
    if case_id == "A09":
        return common
    if case_id == "A27":
        return _a27_observations(after, checks)
    if case_id == "A30":
        return common
    raise ValueError("unsupported local assertion")


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in COMMANDS:
        raise SystemExit("usage: run-local-acceptance-assertion.py A01|A08|A09|A27|A30")
    case_id = sys.argv[1]
    evidence_root = Path(os.environ["LIQVERA_ACCEPTANCE_EVIDENCE_DIR"]).resolve()
    command = COMMANDS[case_id]
    cwd = ROOT / "apps/mezo-web" if case_id == "A30" else ROOT
    before = (_git("rev-parse", "HEAD"), _git("rev-parse", "HEAD^{tree}"))
    completed = subprocess.run(command, cwd=cwd, capture_output=True, check=False, timeout=900)
    if completed.returncode:
        return completed.returncode
    commit, tree = before
    evidence = {
        "case_id": case_id,
        "assertion": ASSERTIONS[case_id],
        "execution_class": "local",
        "claims": [ASSERTIONS[case_id]],
        "subject": {"commit": commit, "tree": tree},
        "observations": _observations(case_id, completed, before),
        "transcript": {"stdout_sha256": hashlib.sha256(completed.stdout).hexdigest(),
                       "stderr_sha256": hashlib.sha256(completed.stderr).hexdigest()},
    }
    relative = f"evidence/{case_id.lower()}.json"
    target = evidence_root / relative
    target.parent.mkdir(mode=0o700, exist_ok=True)
    descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        json.dump(evidence, stream, sort_keys=True, separators=(",", ":"))
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps({"case_id": case_id, "assertion": ASSERTIONS[case_id], "evidence_file": relative}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
