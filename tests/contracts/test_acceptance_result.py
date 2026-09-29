import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from tools.mezo_acceptance import runner

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads(
    (ROOT / "schemas/mezo-evidence/v1/acceptance-result.schema.json").read_text(
        encoding="utf-8"
    )
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
    assert row["omissions"] == ["ASSERTION_COMMAND_NOT_CONFIGURED"]


def _result_with_passing_case(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> dict:
    result = _generated_result(tmp_path, monkeypatch)
    result["cases"][0].update({
        "status": "PASS",
        "started_at": "2026-09-29T00:00:00Z",
        "ended_at": "2026-09-29T00:00:01Z",
        "command": ["offline-assertion"],
        "exit_code": 0,
        "stdout_sha256": "a" * 64,
        "stderr_sha256": "b" * 64,
        "command_sha256": "d" * 64,
        "assertion_contract_sha256": runner.canonical_sha256({
            "case_id": "A01", "assertion": "before_after_checks", "execution_class": "local",
            "required_claims": ["before_after_checks"],
        }),
        "evidence": [{"file": "a01.json", "sha256": "c" * 64, "size_bytes": 1}],
        "omissions": [],
    })
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
@pytest.mark.parametrize(
    "bad_oid", ["a" * 39, "a" * 41, "A" * 40, "g" * 40, "a" * 40 + "\n"]
)
def test_acceptance_result_rejects_noncanonical_git_object_ids(
    field: str, bad_oid: str
) -> None:
    validator = Draft202012Validator(SCHEMA)
    repository = {
        "repository": "Dimkox/liqvera",
        "origin": "UNSET",
        "commit": COMMIT,
        "tree": TREE,
        "worktree": "CLEAN",
    }

    repository[field] = bad_oid
    errors = list(validator.iter_errors({
        "schema": "liqvera-acceptance-result/v1",
        "mode": "offline",
        "repository": repository,
        "environment": {"platform": "test", "python": "3.12.0"},
        "started_at": "2026-09-29T00:00:00Z",
        "ended_at": "2026-09-29T00:00:01Z",
        "overall_status": "INCOMPLETE",
        "cases": [],
    }))

    assert any(list(error.path) == ["repository", field] for error in errors)
