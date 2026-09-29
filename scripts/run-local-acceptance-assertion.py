#!/usr/bin/env python3
"""Execute one checked-in, network-free F7 acceptance assertion."""

import hashlib
import json
import os
import re
import subprocess
import sys
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


def _observations(case_id: str, stdout: bytes, before: tuple[str, str]) -> dict:
    text = stdout.decode("utf-8", "strict")
    after = (_git("rev-parse", "HEAD"), _git("rev-parse", "HEAD^{tree}"))
    if _git("status", "--porcelain", "--untracked-files=all") or after != before:
        raise RuntimeError("assertion changed the repository subject")
    pytest_checks = sorted(set(re.findall(r"^(tests/[^ ]+::[^ ]+) PASSED", text, re.MULTILINE)))
    node_checks = sorted(set(re.findall(r"^[✔✓] (.+?) \([^)]+\)$", text, re.MULTILINE)))
    checks = pytest_checks or node_checks
    common = {"checks": checks, "subject_commit": after[0], "subject_tree": after[1]}
    if case_id == "A01":
        subprocess.run(["git", "-C", ROOT, "merge-base", "--is-ancestor", BASELINE_COMMIT, after[0]], check=True)
        return {**common, "baseline_commit": BASELINE_COMMIT}
    if case_id == "A08":
        return common
    if case_id == "A09":
        return common
    if case_id == "A27":
        vectors = json.loads((ROOT / "schemas/mezo-evidence/v1/vectors.json").read_text())
        go_paths = subprocess.check_output(
            ["git", "-C", ROOT, "ls-files", "*.go"], text=True
        ).splitlines()
        return {**common, "vector_count": len(vectors["vectors"]),
                "vector_sha256": hashlib.sha256((ROOT / "schemas/mezo-evidence/v1/vectors.json").read_bytes()).hexdigest(),
                "go_runtime_paths": len(go_paths)}
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
        "observations": _observations(case_id, completed.stdout, before),
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
