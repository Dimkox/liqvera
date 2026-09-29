"""Fail-closed acceptance orchestration; assertion programs own their evidence."""

import argparse
import hashlib
import json
import os
import platform
import re
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator

from .cases import CASES

ROOT = Path(__file__).resolve().parents[2]
ENV_NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")
SAFE_ARG = re.compile(r"^[^\x00-\x1f\x7f]+$")
SENSITIVE_ARG = re.compile(r"^--(?:password|secret|private-key|bearer|signature|capability|token)(?:=|$)", re.I)
SENSITIVE_FIELD = re.compile(r"(password|secret|private|bearer|signature|cookie|authorization|capability|seed|mnemonic|token)", re.I)
SENSITIVE_VALUE = re.compile(r"Bearer\s+\S+|-----BEGIN [^-]*PRIVATE KEY-----|0x[0-9a-fA-F]{130,}", re.I)
RESULT_SCHEMA = ROOT / "schemas/mezo-evidence/v1/acceptance-result.schema.json"
DISPATCHER = ROOT / "scripts/run-local-acceptance-assertion.py"
BLOCKED_REASON = "EXACT_EXTERNAL_GRANT_ABSENT"
FAIL_REASONS = {"ASSERTION_EXIT_NONZERO", "ASSERTION_TIMEOUT", "ASSERTION_VALIDATION_ERROR", "ASSERTION_EXECUTION_ERROR"}
OBSERVATION_FIELDS = {
    "A01": {"baseline", "current", "expected_delta"},
    "A08": {"checks", "subject_commit", "subject_tree"},
    "A09": {"checks", "subject_commit", "subject_tree"},
    "A27": {"subject_commit", "subject_tree", "vector_checks", "stage_a", "artifact_verifier", "fixture"},
    "A30": {"checks", "subject_commit", "subject_tree"},
}
REQUIRED_CHECKS = {
    "A01": {
        "tests/contracts/test_acceptance_result.py::test_runner_result_accepts_exact_git_object_ids",
        "tests/contracts/test_acceptance_result.py::test_plan_snapshot_detects_replacement",
        "tests/contracts/test_acceptance_result.py::test_post_seal_verifier_rejects_result_mutation",
    },
    "A08": {
        "tests/evidence_report/test_canonical_f3.py::test_tampered_bundle_and_trusted_digest_are_rejected",
        "tests/evidence_report/test_canonical_f3.py::test_standalone_report_tamper_cannot_split_from_verified_bundle",
    },
    "A09": {
        "tests/installed/test_canonical_f3_installed.py::test_installed_canonical_f3_builds_and_verifies_outside_checkout",
    },
    "A27": {
        "tests/contracts/test_mezo_vectors.py::test_required_adversarial_cases_cannot_disappear",
        "tests/contracts/test_mezo_vectors.py::test_all_vector_shapes_semantics_and_assertion_registry",
    },
    "A30": {
        "wrong network is explicit and switching never submits payment",
        "typed pre-submit cancellation clears only with a fresh READY quote",
        "reload recovery uses only the saved identity and exact create replay",
        "one guarded invocation is the maximum across ambiguous outcome and reload",
    },
}


@dataclass(frozen=True)
class PlanSnapshot:
    path: Path
    raw: bytes
    digest: str
    device: int
    inode: int
    size: int

    def verify_unchanged(self) -> None:
        info = os.lstat(self.path)
        if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                or (info.st_dev, info.st_ino, info.st_size) != (self.device, self.inode, self.size)
                or hashlib.sha256(self.path.read_bytes()).hexdigest() != self.digest):
            raise ValueError("acceptance plan changed after validation")


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


def read_plan(path: Path | None) -> tuple[dict[str, dict], PlanSnapshot | None]:
    if path is None:
        return {}, None
    resolved = path.resolve(strict=True)
    if resolved != ROOT / "acceptance/offline-plan.json":
        raise ValueError("only the tracked reviewed offline plan is accepted")
    info = os.lstat(path)
    if resolved != path.absolute() or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise ValueError("acceptance plan must be one regular non-linked file")
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        opened = os.fstat(descriptor)
        raw = os.read(descriptor, 1_000_001)
    finally:
        os.close(descriptor)
    if len(raw) > 1_000_000 or (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
        raise ValueError("acceptance plan is unsafe or too large")
    doc = json.loads(raw)
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
        if argv != ["scripts/run-local-acceptance-assertion.py", case_id]:
            raise ValueError(f"command is not the exact allowlisted dispatcher for {case_id}")
        if type(item["timeout_seconds"]) is not int or not 1 <= item["timeout_seconds"] <= 3600:
            raise ValueError(f"invalid timeout for {case_id}")
        names = item["environment"]
        if names != []:
            raise ValueError(f"environment inputs are not approved for {case_id}")
        commands[case_id] = item
    snapshot = PlanSnapshot(resolved, raw, hashlib.sha256(raw).hexdigest(), info.st_dev, info.st_ino, info.st_size)
    return commands, snapshot


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _publish_exclusive(output: Path, encoded: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".acceptance-", dir=output.parent)
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary_path, 0o400)
        os.link(temporary_path, output, follow_symlinks=False)
        temporary_path.unlink()
        directory = os.open(output.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        temporary_path.unlink(missing_ok=True)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _seal_evidence_tree(root: Path) -> None:
    evidence = root / "evidence"
    if not evidence.is_dir() or evidence.is_symlink():
        raise ValueError("evidence directory is missing or linked")
    for directory, child_dirs, files in os.walk(evidence, topdown=False, followlinks=False):
        current = Path(directory)
        if child_dirs:
            raise ValueError("nested evidence directories are not part of the closed layout")
        for name in files:
            path = current / name
            info = os.lstat(path)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_mode & 0o222:
                raise ValueError("evidence tree contains an unsafe file")
        _fsync_directory(current)
        os.chmod(current, 0o500)
        _fsync_directory(current)


def _invalidate_published(output: Path) -> None:
    root = output.parent
    os.chmod(root, 0o700)
    invalid = output.with_name(f"{output.name}.invalid")
    os.replace(output, invalid)
    os.chmod(invalid, 0o400)
    os.chmod(root, 0o500)
    _fsync_directory(root)


def verify_sealed_result(output: Path, expected_result_sha256: str | None = None,
                         *, require_current_repository: bool = False) -> dict:
    info = os.lstat(output)
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_mode & 0o222:
        raise ValueError("sealed result must be one read-only regular file")
    raw = output.read_bytes()
    if expected_result_sha256 and hashlib.sha256(raw).hexdigest() != expected_result_sha256:
        raise ValueError("sealed result digest mismatch")
    result = json.loads(raw)
    validate_result_semantics(result)
    if result["bindings"]["runner_sha256"] != file_sha256(Path(__file__)):
        raise ValueError("sealed runner binding mismatch")
    plan = ROOT / "acceptance/offline-plan.json"
    empty_digest = hashlib.sha256(b"").hexdigest()
    if result["bindings"]["plan_sha256"] not in {empty_digest, file_sha256(plan)}:
        raise ValueError("sealed plan binding mismatch")
    root = output.parent
    if os.lstat(root).st_mode & 0o222:
        raise ValueError("sealed result directory must be non-writable")
    for row in result["cases"]:
        for reference in row["evidence"]:
            path = root / reference["file"]
            item = os.lstat(path)
            if (not stat.S_ISREG(item.st_mode) or item.st_nlink != 1 or item.st_mode & 0o222
                    or item.st_size != reference["size_bytes"] or file_sha256(path) != reference["sha256"]):
                raise ValueError("sealed evidence integrity mismatch")
            if os.lstat(path.parent).st_mode & 0o222:
                raise ValueError("sealed evidence directory must be non-writable")
            evidence_reference(root, reference["file"], row["case_id"],
                               CASES[row["case_id"]].assertion, row["execution_class"],
                               result["repository"])
    if require_current_repository and repo_identity() != result["repository"]:
        raise ValueError("sealed subject no longer matches the current clean repository")
    return result


def validate_result_semantics(result: dict) -> None:
    expected = list(CASES)
    rows = result.get("cases")
    if not isinstance(rows, list) or [row.get("case_id") for row in rows if isinstance(row, dict)] != expected:
        raise ValueError("acceptance cases must use canonical A01-A30 order exactly once")
    statuses = {row["status"] for row in rows}
    derived = "FAIL" if "FAIL" in statuses else "PASS" if statuses == {"PASS"} else "INCOMPLETE"
    if result.get("overall_status") != derived:
        raise ValueError("overall_status does not match derived case status")
    prior_payment = None
    for case_id, row in zip(expected, rows, strict=True):
        case = CASES[case_id]
        if row["title"] != case.title or row.get("execution_class") != case.execution_class:
            raise ValueError(f"{case_id} does not match the frozen case contract")
        status = row["status"]
        if status == "PASS":
            if row.get("assertion_contract_sha256") != canonical_sha256({
                "case_id": case_id, "assertion": case.assertion,
                "execution_class": case.execution_class,
                "required_claims": list(case.required_claims),
            }):
                raise ValueError(f"{case_id} assertion contract digest mismatch")
            if row.get("command") != ["scripts/run-local-acceptance-assertion.py", case_id] or row.get("environment_names") != []:
                raise ValueError(f"{case_id} command capability is not closed")
        elif status == "BLOCKED_EXTERNAL":
            if case.execution_class == "local" or row.get("omissions") != [BLOCKED_REASON]:
                raise ValueError(f"{case_id} has invalid external blocker algebra")
        elif status == "NOT_RUN":
            expected_reason = case.local_omission
            if case.execution_class != "local" or expected_reason is None or row.get("omissions") != [expected_reason]:
                raise ValueError(f"{case_id} has invalid local omission algebra")
        elif status == "FAIL":
            reasons = row.get("omissions", [])
            exit_code = row.get("exit_code")
            if (not row.get("started_at") or not row.get("ended_at") or row.get("command") is None
                    or len(reasons) != 1 or reasons[0] not in FAIL_REASONS
                    or (reasons[0] == "ASSERTION_EXIT_NONZERO" and (type(exit_code) is not int or exit_code == 0))
                    or (reasons[0] == "ASSERTION_TIMEOUT" and exit_code is not None)
                    or (reasons[0] == "ASSERTION_VALIDATION_ERROR" and exit_code != 0)
                    or (reasons[0] == "ASSERTION_EXECUTION_ERROR" and exit_code is not None)):
                raise ValueError(f"{case_id} has contradictory failure algebra")
        if status == "PASS" or "payment_evidence" in row:
            payment = payment_reference(
                case_id,
                {"payment": row["payment_evidence"]} if "payment_evidence" in row else {},
                prior_payment,
            )
            if case_id == "A13":
                prior_payment = payment
    schema = json.loads(RESULT_SCHEMA.read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(schema).iter_errors(result))
    if errors:
        raise ValueError(f"acceptance result schema invalid at {list(errors[0].path)}")


def evidence_reference(root: Path, relative: str, case_id: str, assertion: str,
                       execution_class: str, identity: dict[str, str]) -> dict[str, str | int]:
    if not isinstance(relative, str) or not relative.endswith(".json") or Path(relative).is_absolute():
        raise ValueError("evidence_file must be a relative JSON path")
    candidate = root / relative
    link_info = os.lstat(candidate)
    path = candidate.resolve()
    info = path.stat()
    if (not path.is_relative_to(root.resolve()) or not stat.S_ISREG(link_info.st_mode)
            or not path.is_file() or info.st_nlink != 1):
        raise ValueError("evidence_file must be a regular file under the evidence directory")
    if path.stat().st_size > 10_000_000:
        raise ValueError("evidence_file exceeds 10 MB")
    raw = path.read_bytes()
    document = json.loads(raw)
    if not isinstance(document, dict) or document.get("case_id") != case_id or document.get("assertion") != assertion:
        raise ValueError("evidence document does not bind to this assertion")
    if document.get("execution_class") != execution_class or document.get("claims") != list(CASES[case_id].required_claims):
        raise ValueError("evidence claims do not match the closed case contract")
    if document.get("subject") != {"commit": identity["commit"], "tree": identity["tree"]}:
        raise ValueError("evidence does not bind to the acceptance subject")
    observations = document.get("observations")
    expected_fields = OBSERVATION_FIELDS.get(case_id)
    if expected_fields is None or not isinstance(observations, dict) or set(observations) != expected_fields:
        raise ValueError("evidence observations do not match the case-specific schema")
    if case_id == "A01":
        baseline, current = observations["baseline"], observations["current"]
        execution_keys = {"argv", "exit_code", "stdout_sha256", "stderr_sha256", "commit", "tree", "status"}
        if (not isinstance(baseline, dict) or set(baseline) != execution_keys
                or baseline["argv"] != [sys.executable, "-m", "pytest", "-vv", "tests/contracts/test_acceptance_result.py"]
                or baseline["commit"] != "f07562eee1a33df74768e9fa4a3b074783d8c59e"
                or baseline["tree"] != "a1df248d000718c28c565d1d5b11bd425f83a055"
                or baseline["status"] != "EXPECTED_HISTORICAL_FAILURE"
                or baseline["exit_code"] != 4
                or not isinstance(current, dict) or set(current) != execution_keys | {"checks"}
                or current["argv"] != [sys.executable, "-m", "pytest", "-vv", "tests/contracts/test_acceptance_result.py"]
                or current["commit"] != identity["commit"] or current["tree"] != identity["tree"]
                or current["status"] != "PASS" or current["exit_code"] != 0
                or observations["expected_delta"] != "BASELINE_LACKS_F7_ACCEPTANCE_CONTRACT_CURRENT_PASSES"):
            raise ValueError("A01 must retain distinct frozen baseline and current checks")
        checks = current["checks"]
    elif case_id == "A27":
        if (observations["subject_commit"], observations["subject_tree"]) != (identity["commit"], identity["tree"]):
            raise ValueError("A27 observations do not bind to the subject")
        stage = observations["stage_a"]
        fixture = observations["fixture"]
        artifact = observations["artifact_verifier"]
        expected_stage_checks = {
            "tests/readonly_analyzer/test_cli_decision.py::test_valid_package_emits_insufficient_evidence",
            "tests/contracts/test_decision.py::test_stage_a_decision_code_is_the_closed_four",
        }
        canonical_fixture = ROOT / "tests/fixtures/shadow-golden-v1.ndjson"
        if (not isinstance(stage, dict) or stage.get("exit_code") != 0
                or stage.get("argv") != [sys.executable, "-m", "pytest", "-vv",
                    "tests/readonly_analyzer/test_cli_decision.py::test_valid_package_emits_insufficient_evidence",
                    "tests/contracts/test_decision.py::test_stage_a_decision_code_is_the_closed_four"]
                or stage.get("verdict") != "INSUFFICIENT_EVIDENCE" or stage.get("go_possible") is not False
                or set(stage.get("checks", [])) != expected_stage_checks
                or artifact.get("exit_code") != 0 or artifact.get("status") != "PASS"
                or artifact.get("argv") != [sys.executable, "-B", "scripts/check-stage-a-artifacts.py",
                    "--forbid-path", "cmd/**", "internal/**", "go.mod", "go.sum",
                    "--forbid-binary", "engine"]
                or fixture != {"path": "tests/fixtures/shadow-golden-v1.ndjson",
                               "sha256": file_sha256(canonical_fixture),
                               "record_count": len(canonical_fixture.read_bytes().splitlines()),
                               "terminal_sha256": (ROOT / "tests/fixtures/shadow-golden-v1.terminal.sha256").read_text().strip()}):
            raise ValueError("A27 must retain the canonical non-GO verdict and stable fixture")
        checks = observations["vector_checks"]
    else:
        if (observations.get("subject_commit"), observations.get("subject_tree")) != (
            identity["commit"], identity["tree"]
        ):
            raise ValueError("semantic observations do not bind to the subject")
        checks = observations.get("checks")
    if (not isinstance(checks, list) or any(not isinstance(item, str) for item in checks)
            or not REQUIRED_CHECKS[case_id].issubset(checks)):
        raise ValueError("evidence lacks required semantic test identities")
    for execution in ([observations["baseline"], observations["current"]] if case_id == "A01"
                      else [observations["stage_a"], observations["artifact_verifier"]] if case_id == "A27" else []):
        if any(not isinstance(execution.get(name), str) or not re.fullmatch(r"[0-9a-f]{64}", execution[name])
               for name in ("stdout_sha256", "stderr_sha256")):
            raise ValueError("semantic execution transcript digest is invalid")
    transcript = document.get("transcript")
    if (not isinstance(transcript, dict) or set(transcript) != {"stdout_sha256", "stderr_sha256"}
            or any(not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value)
                   for value in transcript.values())):
        raise ValueError("evidence transcript binding is invalid")

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


def run_case(case_id: str, spec: dict, evidence_root: Path, prior_payment: dict | None,
             identity: dict[str, str]) -> dict:
    case = CASES[case_id]
    started = utc_now()
    env = {
        "LIQVERA_ACCEPTANCE_EVIDENCE_DIR": str(evidence_root),
        "LIQVERA_ACCEPTANCE_PYTHON": sys.executable,
        "PATH": f"{Path(sys.executable).parent}:/usr/bin:/bin",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PIP_NO_INDEX": "1",
    }
    actual_argv = [sys.executable, "-B", str(DISPATCHER), case_id]
    row = {
        "case_id": case_id, "title": case.title, "status": "FAIL", "started_at": started,
        "command": spec["argv"], "environment_names": [],
        "execution_class": case.execution_class,
        "exit_code": None, "evidence": [], "omissions": [],
    }
    completed = None
    try:
        completed = subprocess.run(
            actual_argv, cwd=ROOT, env=env, capture_output=True,
            timeout=spec["timeout_seconds"], check=False,
        )
        row["exit_code"] = completed.returncode
        row["stdout_sha256"] = hashlib.sha256(completed.stdout).hexdigest()
        row["stderr_sha256"] = hashlib.sha256(completed.stderr).hexdigest()
        if completed.returncode != 0:
            row["omissions"] = ["ASSERTION_EXIT_NONZERO"]
            row["ended_at"] = utc_now()
            return row
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
        row["command_sha256"] = canonical_sha256(spec["argv"])
        row["assertion_contract_sha256"] = canonical_sha256({"case_id": case_id, "assertion": case.assertion,
            "execution_class": case.execution_class, "required_claims": list(case.required_claims)})
        row["evidence"] = [evidence_reference(evidence_root, answer["evidence_file"], case_id,
            case.assertion, case.execution_class, identity)]
        payment = payment_reference(case_id, answer, prior_payment)
        if payment is not None:
            row["payment_evidence"] = payment
        row["status"] = "PASS"
    except subprocess.TimeoutExpired:
        row["omissions"] = ["ASSERTION_TIMEOUT"]
    except OSError:
        row["omissions"] = ["ASSERTION_EXECUTION_ERROR" if completed is None else "ASSERTION_VALIDATION_ERROR"]
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        row["omissions"] = ["ASSERTION_VALIDATION_ERROR"]
    row["ended_at"] = utc_now()
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("offline", "live"), required=True)
    parser.add_argument("--plan", type=Path, help="explicit JSON command plan")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--authorize-live", action="store_true", help="explicitly permit planned live commands")
    args = parser.parse_args()
    if args.mode == "live" or args.authorize_live:
        parser.error("live execution requires an exact grant contract that is not implemented")
    try:
        identity = repo_identity()
        commands, plan_snapshot = read_plan(args.plan)
        output = args.output.resolve()
        if output.exists() or output.is_relative_to(ROOT):
            raise ValueError("output must be a new path outside the repository")
        evidence_root = output.parent
        evidence_root.mkdir(parents=True, mode=0o700, exist_ok=False)
        rows = []
        prior_payment = None
        started = utc_now()
        for case_id, case in CASES.items():
            if case.execution_class != "local":
                row = {"case_id": case_id, "title": case.title, "status": "BLOCKED_EXTERNAL",
                       "omissions": [BLOCKED_REASON], "command": None,
                       "environment_names": [], "exit_code": None, "evidence": [],
                       "execution_class": case.execution_class}
            elif case_id not in commands:
                row = {"case_id": case_id, "title": case.title, "status": "NOT_RUN",
                       "omissions": [case.local_omission], "command": None,
                       "environment_names": [], "exit_code": None, "evidence": [],
                       "execution_class": case.execution_class}
            else:
                row = run_case(case_id, commands[case_id], evidence_root, prior_payment, identity)
            rows.append(row)
            if case_id == "A13" and row["status"] == "PASS":
                prior_payment = row["payment_evidence"]
        statuses = {row["status"] for row in rows}
        overall = "FAIL" if "FAIL" in statuses else "PASS" if statuses == {"PASS"} else "INCOMPLETE"
        seen_evidence: set[str] = set()
        for row in rows:
            for reference in row["evidence"]:
                if reference["file"] in seen_evidence:
                    raise ValueError("evidence path is reused by multiple cases")
                seen_evidence.add(reference["file"])
                path = evidence_root / reference["file"]
                if file_sha256(path) != reference["sha256"] or path.stat().st_size != reference["size_bytes"]:
                    raise ValueError("evidence changed before result sealing")
                os.chmod(path, 0o400)
        if plan_snapshot is not None:
            plan_snapshot.verify_unchanged()
        (evidence_root / "evidence").mkdir(mode=0o700, exist_ok=True)
        _seal_evidence_tree(evidence_root)
        final_identity = repo_identity()
        if final_identity != identity:
            raise ValueError("repository identity changed during acceptance")
        plan_digest = plan_snapshot.digest if plan_snapshot else hashlib.sha256(b"").hexdigest()
        result = {"schema": "liqvera-acceptance-result/v1", "mode": args.mode,
                  "repository": identity, "environment": {"platform": platform.platform(),
                  "python": platform.python_version()}, "started_at": started,
                  "ended_at": utc_now(), "overall_status": overall,
                  "bindings": {"runner_sha256": file_sha256(Path(__file__)), "plan_sha256": plan_digest},
                  "cases": rows}
        validate_result_semantics(result)
        encoded = (json.dumps(result, sort_keys=True, indent=2) + "\n").encode()
        _publish_exclusive(output, encoded)
        os.chmod(evidence_root, 0o500)
        _fsync_directory(evidence_root)
        try:
            verify_sealed_result(output, hashlib.sha256(encoded).hexdigest(),
                                 require_current_repository=True)
        except Exception:
            _invalidate_published(output)
            raise
        print(f"{overall}: {output}")
        return 0 if overall == "PASS" else 1
    except (OSError, ValueError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        parser.exit(2, f"acceptance setup failed: {exc}\n")


if __name__ == "__main__":
    sys.exit(main())
