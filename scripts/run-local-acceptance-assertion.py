#!/usr/bin/env python3
"""Execute one checked-in, network-free F7 acceptance assertion."""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMANDS = {
    "A01": [sys.executable, "-m", "pytest", "-q", "tests/contracts/test_acceptance_result.py"],
    "A08": [sys.executable, "-m", "pytest", "-q", "tests/evidence_report/test_canonical_f3.py"],
    "A09": [sys.executable, "-m", "pytest", "-q", "tests/installed/test_canonical_f3_installed.py"],
    "A27": [sys.executable, "-m", "pytest", "-q", "tests/contracts/test_mezo_vectors.py"],
    "A30": ["npm", "test"],
}
ASSERTIONS = {
    "A01": "before_after_checks",
    "A08": "bundle_tamper_rejected",
    "A09": "offline_replay_exact",
    "A27": "stage_a_regression",
    "A30": "wallet_recovery",
}


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in COMMANDS:
        raise SystemExit("usage: run-local-acceptance-assertion.py A01|A08|A09|A27|A30")
    case_id = sys.argv[1]
    evidence_root = Path(os.environ["LIQVERA_ACCEPTANCE_EVIDENCE_DIR"]).resolve()
    command = COMMANDS[case_id]
    cwd = ROOT / "apps/mezo-web" if case_id == "A30" else ROOT
    completed = subprocess.run(command, cwd=cwd, capture_output=True, check=False, timeout=900)
    if completed.returncode:
        return completed.returncode
    commit = subprocess.check_output(["git", "-C", ROOT, "rev-parse", "HEAD"], text=True).strip()
    tree = subprocess.check_output(["git", "-C", ROOT, "rev-parse", "HEAD^{tree}"], text=True).strip()
    evidence = {
        "case_id": case_id,
        "assertion": ASSERTIONS[case_id],
        "execution_class": "local",
        "claims": [ASSERTIONS[case_id]],
        "subject": {"commit": commit, "tree": tree},
        "observations": [
            f"checked command exited 0: {' '.join(command)}",
            f"stdout_sha256={hashlib.sha256(completed.stdout).hexdigest()}",
            f"stderr_sha256={hashlib.sha256(completed.stderr).hexdigest()}",
        ],
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
