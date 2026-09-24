from __future__ import annotations

import json

import pytest

from scripts.claw_host_bootstrap_transaction import (
    Deadline,
    FakeBackend,
    Journal,
    OPERATIONS,
    TxError,
    execute,
    finalize,
    receipt,
    reconcile_deadline,
)


RUNNER = {
    "repository": "Dimkox/multi-exchange-engine",
    "runner_id": 17,
    "runner_name": "claw-engine-runner",
    "status": "online",
    "labels": ["claw", "claw-engine-runner", "self-hosted"],
    "matching_count": 1,
    "total_count": 2,
}


def _deadline(*, cutoff: int = 2_000, boot: str = "boot-a") -> Deadline:
    return Deadline(
        boot_id=boot,
        monotonic_deadline_ns=cutoff,
        deadline_utc="2026-08-13T12:15:00Z",
    )


def test_apply_stops_at_pending_finalize_and_receipt_is_forbidden(tmp_path):
    journal = Journal(tmp_path / "transaction.json")
    pending = execute(FakeBackend(), journal, deadline=_deadline())
    value = json.loads(journal.path.read_text())
    assert pending.transaction_id == "transaction"
    assert value["phase"] == "HOST_APPLIED_PENDING_FINALIZE"
    assert value["status"] == "OPEN"
    assert value["deadline"] == _deadline().as_dict()
    assert "COMMITTED" not in value["history"]
    with pytest.raises(TxError, match="HOST_JOURNAL_NOT_COMMITTED"):
        receipt(tmp_path / "p", tmp_path / "c", tmp_path / "o", journal.path, "a" * 40)


def test_finalize_commits_only_after_fresh_closed_runner_projection(tmp_path):
    journal = Journal(tmp_path / "transaction.json")
    backend = FakeBackend()
    execute(backend, journal, deadline=_deadline())
    finalize(
        backend,
        Journal.resume(journal.path),
        authenticated_projection=RUNNER,
        now_boot_id="boot-a",
        now_monotonic_ns=1_999,
    )
    value = json.loads(journal.path.read_text())
    assert value["phase"] == "COMMITTED"
    assert value["status"] == "COMMITTED"
    assert value["finalize_projection"] == RUNNER
    assert value["history"][-3:] == ["FINALIZING", "VERIFIED", "COMMITTED"]
    assert backend.events[-1] == ("final_verify", "all")


def test_finalize_allows_unrelated_global_runner_count_drift(tmp_path):
    journal = Journal(tmp_path / "transaction.json")
    backend = FakeBackend()
    execute(backend, journal, deadline=_deadline())
    projection = dict(RUNNER)
    projection["total_count"] = RUNNER["total_count"] + 7
    finalize(
        backend,
        Journal.resume(journal.path),
        authenticated_projection=projection,
        now_boot_id="boot-a",
        now_monotonic_ns=1_999,
    )
    value = json.loads(journal.path.read_text())
    assert value["phase"] == "COMMITTED"
    assert value["finalize_projection"] == projection


@pytest.mark.parametrize(
    "mutation",
    [
        {"status": "offline"},
        {"matching_count": 0},
        {"runner_id": 18},
        {"labels": ["claw-engine-runner", "claw", "self-hosted"]},
        {"extra": True},
    ],
)
def test_finalize_projection_is_closed_and_canonical(tmp_path, mutation):
    journal = Journal(tmp_path / "transaction.json")
    execute(FakeBackend(), journal, deadline=_deadline())
    projection = dict(RUNNER)
    projection.update(mutation)
    with pytest.raises(TxError, match="FINALIZE_PROJECTION"):
        finalize(
            FakeBackend(),
            Journal.resume(journal.path),
            authenticated_projection=projection,
            now_boot_id="boot-a",
            now_monotonic_ns=1_000,
        )
    assert json.loads(journal.path.read_text())["phase"] == "HOST_APPLIED_PENDING_FINALIZE"


def test_expired_deadline_rolls_back_every_operation(tmp_path):
    journal = Journal(tmp_path / "transaction.json")
    execute(FakeBackend(), journal, deadline=_deadline())
    recovered = FakeBackend()
    assert reconcile_deadline(
        recovered,
        Journal.resume(journal.path),
        now_boot_id="boot-a",
        now_monotonic_ns=2_000,
    ) is True
    value = json.loads(journal.path.read_text())
    assert value["phase"] == "ROLLED_BACK"
    assert [event[1] for event in recovered.events if event[0] == "rollback"] == [
        operation.name for operation in reversed(OPERATIONS)
    ]


def test_boot_change_fails_safe_to_rollback(tmp_path):
    journal = Journal(tmp_path / "transaction.json")
    execute(FakeBackend(), journal, deadline=_deadline())
    assert reconcile_deadline(
        FakeBackend(),
        Journal.resume(journal.path),
        now_boot_id="boot-b",
        now_monotonic_ns=1,
    ) is True
    assert json.loads(journal.path.read_text())["status"] == "ROLLED_BACK"


def test_not_yet_expired_deadline_does_not_mutate_journal(tmp_path):
    journal = Journal(tmp_path / "transaction.json")
    execute(FakeBackend(), journal, deadline=_deadline())
    before = journal.path.read_bytes()
    assert reconcile_deadline(
        FakeBackend(),
        Journal.resume(journal.path),
        now_boot_id="boot-a",
        now_monotonic_ns=1_999,
    ) is False
    assert journal.path.read_bytes() == before


def test_late_finalize_cannot_overwrite_rollback(tmp_path):
    journal = Journal(tmp_path / "transaction.json")
    execute(FakeBackend(), journal, deadline=_deadline())
    reconcile_deadline(
        FakeBackend(),
        Journal.resume(journal.path),
        now_boot_id="boot-a",
        now_monotonic_ns=2_000,
    )
    with pytest.raises(TxError, match="FINALIZE_STATE"):
        finalize(
            FakeBackend(),
            Journal.load(journal.path, ("ROLLED_BACK",)),
            authenticated_projection=RUNNER,
            now_boot_id="boot-a",
            now_monotonic_ns=1_000,
        )


@pytest.mark.parametrize("crash_phase", ["FINALIZING", "VERIFIED"])
def test_finalize_retry_converges_from_durable_incomplete_phase(tmp_path, crash_phase):
    journal = Journal(tmp_path / "transaction.json")
    backend = FakeBackend()
    execute(backend, journal, deadline=_deadline())
    resumed = Journal.resume(journal.path)
    resumed.record("FINALIZING", list(resumed.value["applied"]), finalize_projection=RUNNER)
    if crash_phase == "VERIFIED":
        resumed.record("VERIFIED", list(resumed.value["applied"]))
    retry_backend = FakeBackend()
    finalize(
        retry_backend,
        Journal.resume(journal.path),
        authenticated_projection={**RUNNER, "total_count": 9},
        now_boot_id="boot-a",
        now_monotonic_ns=1_999,
    )
    value = json.loads(journal.path.read_text())
    assert value["phase"] == "COMMITTED"
    assert value["status"] == "COMMITTED"
    if crash_phase == "FINALIZING":
        assert retry_backend.events[-1] == ("final_verify", "all")
    else:
        assert ("final_verify", "all") not in retry_backend.events


def test_verified_without_commit_remains_deadline_rollback_eligible(tmp_path):
    journal = Journal(tmp_path / "transaction.json")
    execute(FakeBackend(), journal, deadline=_deadline())
    resumed = Journal.resume(journal.path)
    resumed.record("FINALIZING", list(resumed.value["applied"]), finalize_projection=RUNNER)
    resumed.record("VERIFIED", list(resumed.value["applied"]))
    recovered = FakeBackend()
    assert reconcile_deadline(
        recovered,
        Journal.resume(journal.path),
        now_boot_id="boot-a",
        now_monotonic_ns=2_000,
    ) is True
    assert json.loads(journal.path.read_text())["status"] == "ROLLED_BACK"
