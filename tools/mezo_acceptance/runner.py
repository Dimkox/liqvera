"""Fail-closed acceptance orchestration; assertion programs own their evidence."""

import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from .cases import CASES

ROOT = Path(__file__).resolve().parents[2]
ENV_NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")
SAFE_ARG = re.compile(r"^[^\x00-\x1f\x7f]+$")
SENSITIVE_ARG = re.compile(r"^--(?:password|secret|private-key|bearer|signature|capability|token)(?:=|$)", re.I)
SENSITIVE_FIELD = re.compile(r"(password|secret|private|bearer|signature|cookie|authorization|capability|seed|mnemonic|token)", re.I)
SENSITIVE_VALUE = re.compile(r"Bearer\s+\S+|-----BEGIN [^-]*PRIVATE KEY-----|0x[0-9a-fA-F]{130,}", re.I)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()


def repo_identity() -> dict[str, str]:
    if Path(git("rev-parse", "--show-toplevel")).resolve() != ROOT:
        raise ValueError("acceptance script is not in the expected repository")
    if git("status", "--porcelain", "--untracked-files=all"):
        raise ValueError("commit or remove worktree changes before acceptance")
    try:
        remote = git("config", "--get", "remote.origin.url")
    except subprocess.CalledProcessError:
        remote = ""
    if remote:
        if remote.startswith("git@github.com:"):
            remote_path = remote.removeprefix("git@github.com:")
        else:
            parsed = urlsplit(remote)
            if parsed.scheme != "https" or parsed.hostname != "github.com" or parsed.username or parsed.password or parsed.query or parsed.fragment:
                raise ValueError("origin is not a credential-free canonical GitHub URL")
            remote_path = parsed.path.lstrip("/")
        if remote_path.removesuffix(".git") != "Dimkox/liqvera":
            raise ValueError("origin does not identify Dimkox/liqvera")
    return {
        "repository": "Dimkox/liqvera",
        "origin": "github.com/Dimkox/liqvera" if remote else "UNSET",
        "commit": git("rev-parse", "HEAD"),
        "tree": git("rev-parse", "HEAD^{tree}"),
        "worktree": "CLEAN",
    }


def read_plan(path: Path | None) -> dict[str, dict]:
    if path is None:
        return {}
    doc = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        raise ValueError("acceptance plan must be an object")
    if set(doc) != {"schema", "commands"} or doc["schema"] != "liqvera-acceptance-plan/v1":
        raise ValueError("invalid acceptance plan envelope")
    if not isinstance(doc["commands"], list):
        raise ValueError("acceptance commands must be a list")
    commands = {}
    for item in doc["commands"]:
        if not isinstance(item, dict):
            raise ValueError("acceptance command must be an object")
        if set(item) != {"case_id", "argv", "timeout_seconds", "environment"}:
            raise ValueError("command has unknown or missing fields")
        case_id = item["case_id"]
        if not isinstance(case_id, str) or case_id not in CASES or case_id in commands:
            raise ValueError(f"unknown or duplicate acceptance case: {case_id}")
        argv = item["argv"]
        if not isinstance(argv, list) or not argv or any(
            not isinstance(arg, str) or not SAFE_ARG.fullmatch(arg) or SENSITIVE_ARG.search(arg)
            or "://" in arg
            for arg in argv
        ):
            raise ValueError(f"unsafe command arguments for {case_id}; pass credentials by environment")
        if type(item["timeout_seconds"]) is not int or not 1 <= item["timeout_seconds"] <= 3600:
            raise ValueError(f"invalid timeout for {case_id}")
        names = item["environment"]
        if not isinstance(names, list) or any(not isinstance(n, str) or not ENV_NAME.fullmatch(n) for n in names):
            raise ValueError(f"invalid environment names for {case_id}")
        if len(set(names)) != len(names):
            raise ValueError(f"duplicate environment name for {case_id}")
        commands[case_id] = item
    return commands


def evidence_reference(root: Path, relative: str, case_id: str, assertion: str) -> dict[str, str | int]:
    if not isinstance(relative, str) or not relative.endswith(".json") or Path(relative).is_absolute():
        raise ValueError("evidence_file must be a relative JSON path")
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file() or path.is_symlink():
        raise ValueError("evidence_file must be a regular file under the evidence directory")
    if path.stat().st_size > 10_000_000:
        raise ValueError("evidence_file exceeds 10 MB")
    raw = path.read_bytes()
    document = json.loads(raw)
    if not isinstance(document, dict) or document.get("case_id") != case_id or document.get("assertion") != assertion:
        raise ValueError("evidence document does not bind to this assertion")
    if not isinstance(document.get("observations"), list) or not document["observations"] or any(
        not isinstance(item, str) or not item.strip() for item in document["observations"]
    ):
        raise ValueError("evidence document needs concrete observations")

    def inspect(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if not isinstance(key, str) or SENSITIVE_FIELD.search(key):
                    raise ValueError("evidence contains a sensitive field name")
                inspect(child)
        elif isinstance(value, list):
            for child in value:
                inspect(child)
        elif isinstance(value, str) and SENSITIVE_VALUE.search(value):
            raise ValueError("evidence contains a sensitive value pattern")

    inspect(document)
    digest = hashlib.sha256(raw).hexdigest()
    return {"file": relative, "sha256": digest, "size_bytes": path.stat().st_size}


def payment_reference(case_id: str, result: dict, prior: dict | None) -> dict | None:
    if case_id == "A13":
        payment = result.get("payment")
        if not isinstance(payment, dict) or set(payment) != {
            "tx_hash", "block_hash", "log_index", "buyer", "merchant", "network", "asset", "amount_atomic"
        }:
            raise ValueError("A13 requires exact sanitized transaction evidence")
        if not all(isinstance(payment[k], str) and re.fullmatch(r"0x[0-9a-fA-F]{64}", payment[k]) for k in ("tx_hash", "block_hash")):
            raise ValueError("A13 transaction/block hash is invalid")
        if type(payment["log_index"]) is not int or payment["log_index"] < 0:
            raise ValueError("A13 log index is invalid")
        if not all(isinstance(payment[k], str) and re.fullmatch(r"0x[0-9a-fA-F]{40}", payment[k]) for k in ("buyer", "merchant")):
            raise ValueError("A13 buyer/merchant address is invalid")
        if payment["buyer"].lower() == payment["merchant"].lower():
            raise ValueError("A13 buyer must differ from merchant")
        if not all(isinstance(payment[k], str) for k in ("network", "asset", "amount_atomic")):
            raise ValueError("A13 transfer terms have invalid types")
        if (payment["network"], payment["asset"].lower(), payment["amount_atomic"]) != (
            "eip155:31611", "0x118917a40faf1cd7a13db0ef56c86de7973ac503", "10000000000000000"
        ):
            raise ValueError("A13 transfer terms do not match the Mezo Testnet lock")
        return payment
    if case_id == "A14":
        payment = result.get("payment")
        if not isinstance(payment, dict) or set(payment) != {"tx_hash", "settlement_count"}:
            raise ValueError("A14 requires repeat-access settlement evidence")
        if (prior is None or not isinstance(payment["tx_hash"], str)
                or payment["tx_hash"] != prior["tx_hash"]
                or type(payment["settlement_count"]) is not int or payment["settlement_count"] != 1):
            raise ValueError("A14 must bind to passing A13 and exactly one settlement")
        return payment
    if "payment" in result:
        raise ValueError("unexpected payment evidence")
    return None


def run_case(case_id: str, spec: dict, evidence_root: Path, prior_payment: dict | None) -> dict:
    case = CASES[case_id]
    started = utc_now()
    env = {name: os.environ[name] for name in spec["environment"] if name in os.environ}
    env["LIQVERA_ACCEPTANCE_EVIDENCE_DIR"] = str(evidence_root)
    row = {
        "case_id": case_id, "title": case.title, "status": "FAIL", "started_at": started,
        "command": spec["argv"], "environment_names": sorted(env),
        "exit_code": None, "evidence": [], "omissions": [],
    }
    try:
        completed = subprocess.run(
            spec["argv"], cwd=ROOT, env=env, capture_output=True,
            timeout=spec["timeout_seconds"], check=False,
        )
        row["exit_code"] = completed.returncode
        row["stdout_sha256"] = hashlib.sha256(completed.stdout).hexdigest()
        row["stderr_sha256"] = hashlib.sha256(completed.stderr).hexdigest()
        if completed.returncode != 0:
            raise ValueError("assertion command exited nonzero")
        if len(completed.stdout) > 65536:
            raise ValueError("assertion protocol exceeds 64 KiB")
        answer = json.loads(completed.stdout)
        if not isinstance(answer, dict):
            raise ValueError("assertion protocol must be an object")
        allowed = {"case_id", "assertion", "evidence_file"}
        if case_id in {"A13", "A14"}:
            allowed.add("payment")
        if set(answer) != allowed or answer["case_id"] != case_id or answer["assertion"] != case.assertion:
            raise ValueError("assertion protocol does not match the case contract")
        row["evidence"] = [evidence_reference(evidence_root, answer["evidence_file"], case_id, case.assertion)]
        payment = payment_reference(case_id, answer, prior_payment)
        if payment is not None:
            row["payment_evidence"] = payment
        row["status"] = "PASS"
    except subprocess.TimeoutExpired:
        row["omissions"] = ["ASSERTION_TIMEOUT"]
    except Exception as exc:
        row["omissions"] = [f"ASSERTION_INCOMPLETE:{type(exc).__name__}"]
    row["ended_at"] = utc_now()
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("offline", "live"), required=True)
    parser.add_argument("--plan", type=Path, help="explicit JSON command plan")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--authorize-live", action="store_true", help="explicitly permit planned live commands")
    args = parser.parse_args()
    if args.authorize_live and args.mode != "live":
        parser.error("--authorize-live requires --mode live")
    try:
        identity = repo_identity()
        commands = read_plan(args.plan)
        output = args.output.resolve()
        if output.exists():
            raise ValueError("output already exists; use a new result path")
        evidence_root = output.parent
        evidence_root.mkdir(parents=True, exist_ok=True)
        rows = []
        prior_payment = None
        started = utc_now()
        for case_id, case in CASES.items():
            if case.live and (args.mode != "live" or not args.authorize_live):
                row = {"case_id": case_id, "title": case.title, "status": "BLOCKED_EXTERNAL",
                       "omissions": ["LIVE_AUTHORIZATION_ABSENT"], "command": None,
                       "environment_names": [], "exit_code": None, "evidence": []}
            elif case_id not in commands:
                row = {"case_id": case_id, "title": case.title, "status": "NOT_RUN",
                       "omissions": ["ASSERTION_COMMAND_NOT_CONFIGURED"], "command": None,
                       "environment_names": [], "exit_code": None, "evidence": []}
            else:
                row = run_case(case_id, commands[case_id], evidence_root, prior_payment)
            rows.append(row)
            if case_id == "A13" and row["status"] == "PASS":
                prior_payment = row["payment_evidence"]
        statuses = {row["status"] for row in rows}
        overall = "FAIL" if "FAIL" in statuses else "PASS" if statuses == {"PASS"} else "INCOMPLETE"
        result = {"schema": "liqvera-acceptance-result/v1", "mode": args.mode,
                  "repository": identity, "environment": {"platform": platform.platform(),
                  "python": platform.python_version()}, "started_at": started,
                  "ended_at": utc_now(), "overall_status": overall, "cases": rows}
        encoded = (json.dumps(result, sort_keys=True, indent=2) + "\n").encode()
        with tempfile.NamedTemporaryFile(dir=evidence_root, prefix=".acceptance-", delete=False) as tmp:
            tmp.write(encoded)
            temp_path = Path(tmp.name)
        os.replace(temp_path, output)
        print(f"{overall}: {output}")
        return 0 if overall == "PASS" else 1
    except (OSError, ValueError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        parser.exit(2, f"acceptance setup failed: {exc}\n")


if __name__ == "__main__":
    sys.exit(main())
