import hashlib
import json
import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from tools.mezo_acceptance import runner

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads(
    (ROOT / "schemas/mezo-evidence/v1/acceptance-result.schema.json").read_text(encoding="utf-8")
)
COMMIT = "bed18457b084f9c9f15dd8bee24c31a74323e639"
TREE = "2caf0e76a1abc52c1952503fecd0ae6436d6e448"


def _generated_result(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict:
    output = tmp_path / "run" / "acceptance.json"
    monkeypatch.setattr(
        runner,
        "repo_identity",
        lambda: {
            "repository": "Dimkox/liqvera",
            "origin": "github.com/Dimkox/liqvera",
            "commit": COMMIT,
            "tree": TREE,
            "worktree": "CLEAN",
        },
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["mezo-acceptance", "--mode", "offline", "--output", str(output)],
    )

    assert runner.main() == 1
    return json.loads(output.read_text(encoding="utf-8"))


def test_runner_result_accepts_exact_git_object_ids(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    result = _generated_result(tmp_path, monkeypatch)

    Draft202012Validator(SCHEMA).validate(result)
    assert result["repository"]["commit"] == COMMIT
    assert result["repository"]["tree"] == TREE


def test_semantic_validator_rejects_duplicate_inventory_and_dishonest_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    result = _generated_result(tmp_path, monkeypatch)
    duplicate = deepcopy(result)
    duplicate["cases"][1]["case_id"] = "A01"
    with pytest.raises(ValueError, match="canonical A01-A30 order"):
        runner.validate_result_semantics(duplicate)

    result["overall_status"] = "PASS"
    with pytest.raises(ValueError, match="overall_status"):
        runner.validate_result_semantics(result)


def test_local_a30_is_not_blocked_as_external(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    result = _generated_result(tmp_path, monkeypatch)
    row = next(item for item in result["cases"] if item["case_id"] == "A30")
    assert row["status"] == "NOT_RUN"
    assert row["omissions"] == ["WALLET_ASSERTION_PLAN_NOT_PROVIDED"]


def test_runner_propagates_internal_python_and_path_without_claiming_them(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict = {}

    def fake_run(*args, **kwargs):
        captured["argv"] = args[0]
        captured.update(kwargs["env"])
        return subprocess.CompletedProcess(args[0], 1, b"", b"")

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    row = runner.run_case(
        "A09",
        {"argv": ["offline"], "environment": [], "timeout_seconds": 1},
        tmp_path,
        None,
        {"commit": COMMIT, "tree": TREE},
    )

    verified_python = str(runner.ROOT / ".venv/bin/python")
    assert captured["argv"][0] == verified_python
    assert captured["LIQVERA_ACCEPTANCE_PYTHON"] == verified_python
    assert captured["PATH"] == f"{Path(verified_python).parent}:/usr/bin:/bin"
    assert row["environment_names"] == []


def test_runner_fails_closed_when_verified_python_is_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(runner.os, "access", lambda _path, _mode: False)

    with pytest.raises(ValueError, match="verified Python runtime is unavailable"):
        runner.run_case(
            "A08",
            {"argv": ["offline"], "environment": [], "timeout_seconds": 1},
            tmp_path,
            None,
            {"commit": COMMIT, "tree": TREE},
        )


def _result_with_passing_case(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict:
    result = _generated_result(tmp_path, monkeypatch)
    result["cases"][0].update(
        {
            "status": "PASS",
            "started_at": "2026-09-29T00:00:00Z",
            "ended_at": "2026-09-29T00:00:01Z",
            "command": ["offline-assertion"],
            "exit_code": 0,
            "stdout_sha256": "a" * 64,
            "stderr_sha256": "b" * 64,
            "command_sha256": "d" * 64,
            "assertion_contract_sha256": runner.canonical_sha256(
                {
                    "case_id": "A01",
                    "assertion": "before_after_checks",
                    "execution_class": "local",
                    "required_claims": ["before_after_checks"],
                }
            ),
            "evidence": [{"file": "a01.json", "sha256": "c" * 64, "size_bytes": 1}],
            "omissions": [],
        }
    )
    return result


@pytest.mark.parametrize(
    ("field", "path"),
    [
        ("stdout_sha256", ["cases", 0, "stdout_sha256"]),
        ("stderr_sha256", ["cases", 0, "stderr_sha256"]),
        ("evidence_sha256", ["cases", 0, "evidence", 0, "sha256"]),
    ],
)
def test_acceptance_content_digest_rejects_trailing_newline(
    field: str,
    path: list[object],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _result_with_passing_case(tmp_path, monkeypatch)
    if field == "evidence_sha256":
        result["cases"][0]["evidence"][0]["sha256"] += "\n"
    else:
        result["cases"][0][field] += "\n"

    errors = list(Draft202012Validator(SCHEMA).iter_errors(result))

    assert any(list(error.path) == path for error in errors)


@pytest.mark.parametrize("field", ["commit", "tree"])
@pytest.mark.parametrize("bad_oid", ["a" * 39, "a" * 41, "A" * 40, "g" * 40, "a" * 40 + "\n"])
def test_acceptance_result_rejects_noncanonical_git_object_ids(field: str, bad_oid: str) -> None:
    validator = Draft202012Validator(SCHEMA)
    repository = {
        "repository": "Dimkox/liqvera",
        "origin": "UNSET",
        "commit": COMMIT,
        "tree": TREE,
        "worktree": "CLEAN",
    }

    repository[field] = bad_oid
    errors = list(
        validator.iter_errors(
            {
                "schema": "liqvera-acceptance-result/v1",
                "mode": "offline",
                "repository": repository,
                "environment": {"platform": "test", "python": "3.12.0"},
                "started_at": "2026-09-29T00:00:00Z",
                "ended_at": "2026-09-29T00:00:01Z",
                "overall_status": "INCOMPLETE",
                "cases": [],
            }
        )
    )

    assert any(list(error.path) == ["repository", field] for error in errors)


@pytest.mark.parametrize(
    ("case_id", "status", "omissions", "message"),
    [
        ("A02", "NOT_RUN", ["ASSERTION_COMMAND_NOT_CONFIGURED"], "local omission"),
        ("A07", "BLOCKED_EXTERNAL", ["LIVE_AUTHORIZATION_ABSENT"], "external blocker"),
    ],
)
def test_status_reason_algebra_rejects_generic_or_unknown_reasons(
    case_id: str,
    status: str,
    omissions: list[str],
    message: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _generated_result(tmp_path, monkeypatch)
    row = next(item for item in result["cases"] if item["case_id"] == case_id)
    row.update(status=status, omissions=omissions)
    with pytest.raises(ValueError, match=message):
        runner.validate_result_semantics(result)


def test_semantic_validation_error_is_a_real_fail_even_after_exit_zero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    result = _generated_result(tmp_path, monkeypatch)
    row = result["cases"][0]
    row.update(
        {
            "status": "FAIL",
            "started_at": "2026-09-29T00:00:00Z",
            "ended_at": "2026-09-29T00:00:01Z",
            "command": ["offline"],
            "exit_code": 0,
            "omissions": ["ASSERTION_VALIDATION_ERROR"],
        }
    )
    result["overall_status"] = "FAIL"
    runner.validate_result_semantics(result)
    row["omissions"] = ["ASSERTION_TIMEOUT"]
    with pytest.raises(ValueError, match="contradictory failure"):
        runner.validate_result_semantics(result)


@pytest.mark.parametrize(
    ("reason", "exit_code"),
    [
        ("BOGUS", 1),
        ("ASSERTION_EXIT_NONZERO", None),
        ("ASSERTION_TIMEOUT", 1),
        ("ASSERTION_VALIDATION_ERROR", 1),
        ("ASSERTION_EXECUTION_ERROR", 0),
    ],
)
def test_fail_reason_algebra_rejects_unknown_and_contradictory_forms(
    reason: str, exit_code: int | None, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    result = _generated_result(tmp_path, monkeypatch)
    result["cases"][0].update(
        {
            "status": "FAIL",
            "started_at": "2026-09-29T00:00:00Z",
            "ended_at": "2026-09-29T00:00:01Z",
            "command": ["offline"],
            "exit_code": exit_code,
            "omissions": [reason],
        }
    )
    result["overall_status"] = "FAIL"
    with pytest.raises(ValueError, match="contradictory failure"):
        runner.validate_result_semantics(result)


def test_payment_replay_must_bind_to_exact_a13_receipt() -> None:
    a13 = {
        "payment": {
            "tx_hash": "0x" + "1" * 64,
            "block_hash": "0x" + "2" * 64,
            "log_index": 0,
            "buyer": "0x" + "3" * 40,
            "merchant": "0x" + "4" * 40,
            "network": "eip155:31611",
            "asset": "0x118917a40faf1cd7a13db0ef56c86de7973ac503",
            "amount_atomic": "10000000000000000",
            "scheme": "exact",
            "settlement_broadcaster": "facilitator",
            "transaction_from": "0x" + "5" * 40,
            "buyer_native_balance_before": "1000",
            "buyer_native_balance_after": "1000",
            "buyer_native_gas_spend_wei": "0",
        }
    }
    receipt = runner.payment_reference("A13", a13, None)
    with pytest.raises(ValueError, match="bind to passing A13"):
        runner.payment_reference(
            "A14", {"payment": {"tx_hash": "0x" + "9" * 64, "settlement_count": 1}}, receipt
        )

    a13["payment"]["transaction_from"] = a13["payment"]["buyer"]
    a13["payment"]["buyer_native_balance_after"] = "0"
    a13["payment"]["buyer_native_gas_spend_wei"] = "100000000000001"
    with pytest.raises(ValueError, match="facilitator-sponsored zero buyer gas"):
        runner.payment_reference("A13", a13, None)


def test_atomic_publish_leaves_no_result_after_interrupted_link(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "result.json"
    monkeypatch.setattr(
        runner.os, "link", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("stop"))
    )
    with pytest.raises(OSError, match="stop"):
        runner._publish_exclusive(output, b"payload")
    assert not output.exists()
    assert list(tmp_path.iterdir()) == []


def test_plan_symlink_is_rejected(tmp_path: Path) -> None:
    link = tmp_path / "plan.json"
    link.symlink_to(ROOT / "acceptance/offline-plan.json")
    with pytest.raises(ValueError, match="regular non-linked"):
        runner.read_plan(link)


def test_plan_snapshot_detects_replacement(tmp_path: Path) -> None:
    path = tmp_path / "plan.json"
    path.write_bytes(b"one")
    info = path.stat()
    snapshot = runner.PlanSnapshot(
        path,
        b"one",
        hashlib.sha256(b"one").hexdigest(),
        info.st_dev,
        info.st_ino,
        info.st_size,
    )
    path.write_bytes(b"two")
    with pytest.raises(ValueError, match="changed after validation"):
        snapshot.verify_unchanged()


@pytest.mark.parametrize("link_kind", ["symlink", "hardlink"])
def test_evidence_links_are_rejected(tmp_path: Path, link_kind: str) -> None:
    source = tmp_path / "source.json"
    source.write_text("{}", encoding="utf-8")
    linked = tmp_path / "linked.json"
    if link_kind == "symlink":
        linked.symlink_to(source)
    else:
        os.link(source, linked)
    with pytest.raises(ValueError, match="regular file"):
        runner.evidence_reference(
            tmp_path,
            linked.name,
            "A01",
            "before_after_checks",
            "local",
            {"commit": COMMIT, "tree": TREE},
        )


@pytest.mark.parametrize("case_id", ["A01", "A08", "A09", "A27", "A30"])
def test_unrelated_passing_check_cannot_certify_configured_case(
    tmp_path: Path, case_id: str
) -> None:
    case = runner.CASES[case_id]
    observations = {
        "checks": ["tests/unrelated.py::test_always_passes"],
        "subject_commit": COMMIT,
        "subject_tree": TREE,
    }
    if case_id == "A01":
        observations["baseline_commit"] = "f07562eee1a33df74768e9fa4a3b074783d8c59e"
    if case_id == "A27":
        observations.update(vector_count=156, vector_sha256="a" * 64, go_runtime_paths=0)
    document = {
        "case_id": case_id,
        "assertion": case.assertion,
        "execution_class": "local",
        "claims": [case.assertion],
        "subject": {"commit": COMMIT, "tree": TREE},
        "observations": observations,
        "transcript": {"stdout_sha256": "a" * 64, "stderr_sha256": "b" * 64},
    }
    path = tmp_path / f"{case_id}.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError):
        runner.evidence_reference(
            tmp_path, path.name, case_id, case.assertion, "local", {"commit": COMMIT, "tree": TREE}
        )


@pytest.mark.parametrize("retained", ["baseline", "current"])
def test_a01_rejects_one_sided_baseline_or_current_evidence(tmp_path: Path, retained: str) -> None:
    execution = {
        "argv": ["pytest"],
        "exit_code": 0,
        "stdout_sha256": "a" * 64,
        "stderr_sha256": "b" * 64,
        "commit": COMMIT,
        "tree": TREE,
        "status": "PASS",
        "checks": list(runner.REQUIRED_CHECKS["A01"]),
    }
    observations = {
        retained: execution,
        "expected_delta": "BASELINE_LACKS_F7_ACCEPTANCE_CONTRACT_CURRENT_PASSES",
    }
    document = {
        "case_id": "A01",
        "assertion": "before_after_checks",
        "execution_class": "local",
        "claims": ["before_after_checks"],
        "subject": {"commit": COMMIT, "tree": TREE},
        "observations": observations,
        "transcript": {"stdout_sha256": "a" * 64, "stderr_sha256": "b" * 64},
    }
    path = tmp_path / "a01.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError, match="case-specific schema"):
        runner.evidence_reference(
            tmp_path,
            path.name,
            "A01",
            "before_after_checks",
            "local",
            {"commit": COMMIT, "tree": TREE},
        )


def test_a27_rejects_vectors_only_without_stage_a_verdict_and_fixture(tmp_path: Path) -> None:
    document = {
        "case_id": "A27",
        "assertion": "stage_a_regression",
        "execution_class": "local",
        "claims": ["stage_a_regression"],
        "subject": {"commit": COMMIT, "tree": TREE},
        "observations": {
            "subject_commit": COMMIT,
            "subject_tree": TREE,
            "vector_checks": list(runner.REQUIRED_CHECKS["A27"]),
        },
        "transcript": {"stdout_sha256": "a" * 64, "stderr_sha256": "b" * 64},
    }
    path = tmp_path / "a27.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError, match="case-specific schema"):
        runner.evidence_reference(
            tmp_path,
            path.name,
            "A27",
            "stage_a_regression",
            "local",
            {"commit": COMMIT, "tree": TREE},
        )


def test_a27_rejects_fixture_and_terminal_mutated_together() -> None:
    baseline = b'{"record":"frozen"}\n'
    baseline_terminal = hashlib.sha256(baseline).hexdigest()
    mutated = b'{"record":"mutated"}\n'
    mutated_terminal = hashlib.sha256(mutated).hexdigest()
    forged = {
        "path": "tests/fixtures/shadow-golden-v1.ndjson",
        "baseline_commit": "f07562eee1a33df74768e9fa4a3b074783d8c59e",
        "baseline_sha256": hashlib.sha256(baseline).hexdigest(),
        "baseline_record_count": 1,
        "baseline_terminal_sha256": baseline_terminal,
        "sha256": hashlib.sha256(mutated).hexdigest(),
        "record_count": 1,
        "terminal_sha256": mutated_terminal,
    }
    with pytest.raises(ValueError, match="byte-identical to the frozen baseline"):
        runner.validate_fixture_stability(
            forged, mutated, mutated_terminal, baseline, baseline_terminal
        )


def test_system_python_can_verify_venv_produced_seal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _generated_result(tmp_path, monkeypatch)
    output = tmp_path / "run" / "acceptance.json"
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    completed = subprocess.run(
        [
            "/usr/bin/python3",
            "-B",
            "scripts/verify-mezo-acceptance.py",
            str(output),
            "--sha256",
            digest,
            "--allow-detached-subject",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    os.chmod(output.parent, 0o700)
    os.chmod(output.parent / "evidence", 0o700)


def test_portable_interpreter_identity_ignores_compatible_executable_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    alias = tmp_path / "python-alias"
    alias.symlink_to(Path(sys.executable).resolve())
    identity = {
        "implementation": runner.platform.python_implementation(),
        "version": runner.platform.python_version(),
        "executable_sha256": hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest(),
    }
    monkeypatch.setattr(runner.sys, "executable", str(alias))
    assert runner._portable_interpreter_valid(identity)


def test_post_seal_verifier_rejects_result_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    result = _generated_result(tmp_path, monkeypatch)
    output = tmp_path / "run" / "acceptance.json"
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    runner.verify_sealed_result(output, digest)
    os.chmod(output.parent, 0o700)
    os.chmod(output, 0o600)
    output.write_text(json.dumps(result) + "\n", encoding="utf-8")
    os.chmod(output, 0o400)
    with pytest.raises(ValueError, match="digest mismatch"):
        runner.verify_sealed_result(output, digest)


def test_sealed_tree_blocks_unlink_and_has_nonwritable_directories(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _generated_result(tmp_path, monkeypatch)
    root = tmp_path / "run"
    assert root.stat().st_mode & 0o222 == 0
    assert (root / "evidence").stat().st_mode & 0o222 == 0
    with pytest.raises(PermissionError):
        (root / "acceptance.json").unlink()
    os.chmod(root, 0o700)
    os.chmod(root / "evidence", 0o700)


def test_late_repository_drift_invalidates_published_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "late" / "acceptance.json"
    stable = {
        "repository": "Dimkox/liqvera",
        "origin": "UNSET",
        "commit": COMMIT,
        "tree": TREE,
        "worktree": "CLEAN",
    }
    drifted = {**stable, "commit": "a" * 40}
    identities = iter((stable, stable, drifted))
    monkeypatch.setattr(runner, "repo_identity", lambda: next(identities))
    monkeypatch.setattr(
        sys, "argv", ["mezo-acceptance", "--mode", "offline", "--output", str(output)]
    )
    with pytest.raises(SystemExit) as exc:
        runner.main()
    assert exc.value.code == 2
    assert not output.exists()
    assert output.with_name("acceptance.json.invalid").is_file()
    os.chmod(output.parent, 0o700)
    os.chmod(output.parent / "evidence", 0o700)
