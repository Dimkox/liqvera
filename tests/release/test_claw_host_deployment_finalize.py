from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path

import pytest

from scripts import claw_host_deployment_contract as contract
from scripts import claw_host_deployment_client as client
from scripts.claw_host_deployment_contract import canonical_bytes, verify_request
from scripts import claw_host_deployment_controller as controller
from scripts.claw_host_deployment_controller import ControllerError, HostDeploymentRuntime, LocalActionDispatcher


def _request(action: str) -> dict[str, object]:
    begin = action == "begin"
    return {
        "schema_version": "claw-host-deployment-request-v1",
        "action": action,
        "github_token": "memory-only-token" if action in {"begin", "finalize"} else None,
        "repository": "Dimkox/multi-exchange-engine",
        "approval_comment_id": 11 if begin else None,
        "release_id": 22 if begin else None,
        "transaction_id": None if begin else "a" * 32,
    }


class FakeRuntime:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def _response(self, action: str, transaction_id: str | None) -> dict[str, object]:
        self.calls.append(action)
        return {
            "schema_version": "claw-host-deployment-response-v1",
            "authority": "NONE",
            "action": action,
            "transaction_id": transaction_id or "b" * 32,
            "state": {
                "begin": "HOST_APPLIED_PENDING_FINALIZE",
                "finalize": "COMMITTED",
                "status": "HOST_APPLIED_PENDING_FINALIZE",
                "rollback": "ROLLED_BACK",
            }[action],
            "receipt_sha256": "c" * 64 if action == "finalize" else None,
        }

    def begin(self, request): return self._response("begin", request.transaction_id)
    def finalize(self, request): return self._response("finalize", request.transaction_id)
    def status(self, request): return self._response("status", request.transaction_id)
    def rollback(self, request): return self._response("rollback", request.transaction_id)


@pytest.mark.parametrize("action", ["begin", "finalize", "status", "rollback"])
def test_local_dispatch_routes_only_fixed_actions(action: str) -> None:
    runtime = FakeRuntime()
    request = verify_request(_request(action), expected_action=action)
    response = LocalActionDispatcher(runtime)(request)
    assert runtime.calls == [action]
    assert response["action"] == action
    assert response["authority"] == "NONE"


def test_local_dispatch_rejects_missing_runtime_method() -> None:
    request = verify_request(_request("status"), expected_action="status")
    with pytest.raises(ControllerError, match="ACTION_NOT_IMPLEMENTED"):
        LocalActionDispatcher(object())(request)


def test_request_and_source_have_no_actions_run_or_job_surface() -> None:
    request_schema = json.loads(Path("schemas/claw-host-deployment-request-v1.schema.json").read_text())
    assert set(request_schema["required"]) == {
        "schema_version", "action", "github_token", "repository",
        "approval_comment_id", "release_id", "transaction_id",
    }
    source = "\n".join(
        Path(path).read_text()
        for path in (
            "scripts/claw_host_deployment_contract.py",
            "scripts/claw_host_deployment_controller.py",
            "scripts/claw_host_deployment_client.py",
        )
    )
    for forbidden in ("repository_dispatch", "workflow_run", "actions/runs", "run_attempt", "job_id"):
        assert forbidden not in source
    assert not Path(".github/workflows/finalize-claw-host-transition.yml").exists()


def test_post_migration_projection_never_contains_token() -> None:
    request = verify_request(_request("finalize"), expected_action="finalize")
    assert request.projection() == {
        "schema_version": "claw-host-deployment-request-v1",
        "action": "finalize",
        "repository": "Dimkox/multi-exchange-engine",
        "approval_comment_id": None,
        "release_id": None,
        "transaction_id": "a" * 32,
    }
    assert b"memory-only-token" not in canonical_bytes(request.projection())


def test_root_client_independently_closes_response_before_printing() -> None:
    request = _request("status")
    response = {
        "schema_version": "claw-host-deployment-response-v1",
        "authority": "NONE",
        "action": "status",
        "transaction_id": "a" * 32,
        "state": "HOST_APPLIED_PENDING_FINALIZE",
        "receipt_sha256": None,
    }
    assert client.verify_response(response, request) == response
    with pytest.raises(RuntimeError, match="RESPONSE_FIELDS"):
        client.verify_response({**response, "raw_output": "forbidden"}, request)


def _runtime(tmp_path: Path) -> HostDeploymentRuntime:
    durable = tmp_path / "host-transaction"
    policy = tmp_path / "policy.json"
    closure = tmp_path / "closure.json"
    policy.write_text(json.dumps({
        "repository": "Dimkox/multi-exchange-engine",
        "runner_name": "claw-engine-runner",
        "required_labels": ["self-hosted", "claw", "claw-engine-runner"],
        "transaction_root": str(durable),
    }))
    closure.write_text('{"packages":[]}')
    root = tmp_path / "controller"
    root.mkdir()
    d0_receipt = root / "D0-VERIFIED.json"
    d0_receipt.write_bytes(canonical_bytes({
        "schema_version": "claw-host-deployment-d0-receipt-v1",
        "authority": "NONE",
        "not_host_receipt": True,
        "repository": "Dimkox/multi-exchange-engine",
        "controller_sha": "a" * 40,
        "controller_tree": "b" * 40,
        "install_manifest_sha256": "c" * 64,
        "artifact_count": 19,
        "status": "D0_VERIFIED",
        "created_at": "2026-08-13T12:00:00Z",
    }))
    d0_receipt.chmod(0o600)
    return HostDeploymentRuntime(root=root, policy=policy, closure=closure)


def _fake_staged_acquisition(transaction_root: Path) -> dict[str, object]:
    inputs = transaction_root / "inputs"
    inputs.mkdir(parents=True)
    assets = []
    for role, name in (
        ("oci_archive", "image.tar"),
        ("oci_layout", "layout.tar"),
        ("oci_receipt", "evidence.json"),
        ("oci_sidecar", "evidence.sha256"),
    ):
        (inputs / name).write_bytes(role.encode())
        assets.append({"role": role, "staged_name": name})
    persisted = {
        "schema_version": "claw-host-staged-inputs-v1",
        "authority": "NONE",
        "transaction_id": transaction_root.name,
        "assets": assets,
        "bundle_manifest_sha256": "1" * 64,
        "controller_sha": "a" * 40,
        "controller_tree": "b" * 40,
        "policy_sha256": "2" * 64,
        "closure_sha256": "3" * 64,
        "approval_body_sha256": "e" * 64,
        "host_inventory_sha256": "4" * 64,
        "rollback_deadline_seconds": 900,
        "approval_comment_id": 11,
        "release_id": 22,
    }
    (inputs / "manifest.json").write_bytes(canonical_bytes(persisted))
    return {**persisted, "approval_nonce": "A" * 43}


@pytest.mark.parametrize("case", [
    "valid", "wrong-journal-approval", "nonce-record-drift",
    "binding-policy-drift", "linked-d0-receipt", "invalid-compatibility-timestamp",
    "valid-compatibility-timestamp-drift", "noncanonical-compatibility-receipt",
])
@pytest.mark.skipif(os.name == "posix" and os.geteuid() != 0, reason="root-private recovery evidence")
def test_legacy_terminal_recovery_is_distinct_owner_bound_and_idempotent(tmp_path, monkeypatch, case):
    from scripts import claw_host_bootstrap_transaction as host

    runtime = _runtime(tmp_path)
    transaction_id = "e" * 32
    transaction_root = runtime.root / "transactions" / transaction_id
    staged = _fake_staged_acquisition(transaction_root)
    begin = runtime._create_begin_intent(staged, transaction_id)
    runtime._consume_nonce(staged, transaction_id)
    for path in (runtime.root / "transactions", transaction_root, transaction_root / "inputs"):
        path.chmod(0o700)
    (transaction_root / "inputs" / "manifest.json").chmod(0o600)
    journal, host_receipt, _ = runtime._paths(transaction_id)
    wal = host.Journal(journal)
    journal.parent.chmod(0o700)
    wal.record("ROLLING_BACK", [])
    wal.record("ROLLED_BACK", [], status="ROLLED_BACK")
    binding = journal.parent / "credential-binding.json"
    host.create_credential_binding(binding, {
        "transaction_id": transaction_id, "controller_sha": "a" * 40,
        "policy_sha256": hashlib.sha256(runtime.policy_path.read_bytes()).hexdigest(),
    })
    nonce_path = runtime.root / "nonces" / f"{begin['nonce_sha256']}.json"
    facts = {
        "repository": "Dimkox/multi-exchange-engine", "transaction_id": transaction_id,
        "begin_intent_sha256": hashlib.sha256((transaction_root / "begin-intent.json").read_bytes()).hexdigest(),
        "staged_manifest_sha256": hashlib.sha256((transaction_root / "inputs" / "manifest.json").read_bytes()).hexdigest(),
        "nonce_record_sha256": hashlib.sha256(nonce_path.read_bytes()).hexdigest(),
        "terminal_journal_sha256": hashlib.sha256(journal.read_bytes()).hexdigest(),
        "credential_binding_sha256": hashlib.sha256(binding.read_bytes()).hexdigest(),
        "old_controller_sha": "a" * 40, "old_controller_tree": "b" * 40,
        "reason": "PRE_MARKER_TERMINAL_ROLLBACK_COMPATIBILITY",
    }
    if case == "nonce-record-drift":
        nonce_value = json.loads(nonce_path.read_text())
        nonce_value["approval_comment_id"] += 1
        nonce_path.write_bytes(canonical_bytes(nonce_value))
        nonce_path.chmod(0o600)
        facts["nonce_record_sha256"] = hashlib.sha256(nonce_path.read_bytes()).hexdigest()
    if case == "binding-policy-drift":
        binding_value = json.loads(binding.read_text())
        binding_value["policy_sha256"] = "f" * 64
        binding.write_bytes(canonical_bytes(binding_value))
        binding.chmod(0o600)
        facts["credential_binding_sha256"] = hashlib.sha256(binding.read_bytes()).hexdigest()
    if case == "linked-d0-receipt":
        d0_receipt = runtime.root / "D0-VERIFIED.json"
        outside = tmp_path / "outside-d0.json"
        outside.write_bytes(d0_receipt.read_bytes())
        d0_receipt.unlink()
        os.link(outside, d0_receipt)
    runtime.LEGACY_RECOVERY_FACTS = facts
    class CompatibilityHost:
        Journal = host.Journal
        is_terminal_rolled_back_journal = staticmethod(host.is_terminal_rolled_back_journal)
        durable_unlink = staticmethod(host.durable_unlink)
        @staticmethod
        def main(*_args, **_kwargs): pytest.fail("compatibility recovery must not call host.main")
    monkeypatch.setattr(runtime, "_host_module", lambda: CompatibilityHost)
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    expected = {
        **facts, "recovery_controller_sha": "a" * 40,
        "recovery_controller_tree": "b" * 40,
        "recovery_install_manifest_sha256": "c" * 64,
    }
    body = {
        "schema_version": "claw-host-deployment-legacy-recovery-approval-v1",
        "decision": "APPROVE_LEGACY_D1_TERMINAL_RECOVERY", **expected,
        "expires_at": (now + dt.timedelta(minutes=30)).isoformat().replace("+00:00", "Z"),
        "nonce": "L" * 43,
    }
    if case == "wrong-journal-approval":
        body["terminal_journal_sha256"] = "0" * 64
    comment = tmp_path / "comment.json"
    repository = tmp_path / "repository.json"
    comment.write_bytes(canonical_bytes({
        "id": 77, "body": canonical_bytes(body).decode().rstrip("\n"),
        "author_association": "OWNER", "created_at": now.isoformat().replace("+00:00", "Z"),
        "updated_at": now.isoformat().replace("+00:00", "Z"),
        "html_url": "https://github.com/Dimkox/multi-exchange-engine/issues/44#issuecomment-77",
        "user": {"login": "Dimkox", "id": 1},
    }))
    repository.write_bytes(canonical_bytes({
        "full_name": "Dimkox/multi-exchange-engine", "default_branch": "main",
        "owner": {"login": "Dimkox", "id": 1},
    }))
    comment.chmod(0o600); repository.chmod(0o600)
    journal_before = journal.read_bytes(); binding_before = binding.read_bytes()
    if case == "wrong-journal-approval":
        with pytest.raises(contract.ApprovalError, match="LEGACY_RECOVERY_TUPLE"):
            runtime.recover_legacy_terminal(comment, repository)
        assert journal.read_bytes() == journal_before and binding.read_bytes() == binding_before
        assert not any(path.exists() for path in (*runtime._legacy_recovery_paths(), *runtime._rollback_paths(transaction_id)))
        return
    if case in {"nonce-record-drift", "binding-policy-drift", "linked-d0-receipt"}:
        with pytest.raises(ControllerError, match="LEGACY_RECOVERY_STATE|D0_IDENTITY"):
            runtime.recover_legacy_terminal(comment, repository)
        assert journal.read_bytes() == journal_before and binding.read_bytes() == binding_before
        assert not any(path.exists() for path in (*runtime._legacy_recovery_paths(), *runtime._rollback_paths(transaction_id)))
        return
    response = runtime.recover_legacy_terminal(comment, repository)
    authorization, compatibility_receipt = runtime._legacy_recovery_paths()
    rollback_intent, rollback_receipt = runtime._rollback_paths(transaction_id)
    assert response["state"] == "ROLLED_BACK"
    assert json.loads(authorization.read_text())["status"] == "RETROSPECTIVE_COMPATIBILITY_RECOVERY_APPROVED"
    assert json.loads(compatibility_receipt.read_text())["status"] == "RETROSPECTIVE_COMPATIBILITY_RECOVERY_COMPLETE"
    assert json.loads(rollback_intent.read_text())["prior_host_receipt_sha256"] is None
    assert rollback_receipt.is_file() and not host_receipt.exists()
    assert journal.read_bytes() == journal_before and binding.read_bytes() == binding_before
    assert not (transaction_root / "host-apply-intent.json").exists()
    if case in {"invalid-compatibility-timestamp", "valid-compatibility-timestamp-drift", "noncanonical-compatibility-receipt"}:
        receipt_value = json.loads(compatibility_receipt.read_text())
        if case == "invalid-compatibility-timestamp":
            receipt_value["created_at"] = "not-a-timestamp"
        elif case == "valid-compatibility-timestamp-drift":
            receipt_value["created_at"] = "2026-08-13T23:59:59Z"
        if case == "noncanonical-compatibility-receipt":
            compatibility_receipt.write_text(json.dumps(receipt_value, indent=2) + "\n")
        else:
            compatibility_receipt.write_bytes(canonical_bytes(receipt_value))
        compatibility_receipt.chmod(0o600)
        with pytest.raises(ControllerError, match="LEGACY_RECOVERY_RECEIPT"):
            runtime.recover_legacy_terminal()
    else:
        assert runtime.recover_legacy_terminal() == response


def test_legacy_terminal_recovery_cli_has_exact_initial_and_replay_arities(tmp_path, monkeypatch):
    calls = []

    class FakeRuntime:
        def recover_legacy_terminal(self, comment=None, repository=None):
            calls.append((comment, repository))

    monkeypatch.setattr(controller, "HostDeploymentRuntime", FakeRuntime)
    monkeypatch.setattr(controller.os, "geteuid", lambda: 0)
    comment = tmp_path / "comment.json"
    repository = tmp_path / "repository.json"
    assert controller.main(["--recover-legacy-e872", str(comment), str(repository)]) == 0
    assert controller.main(["--recover-legacy-e872"]) == 0
    assert calls == [(comment, repository), (None, None)]
    for invalid in (
        ["--recover-legacy-e872", str(comment)],
        ["--recover-legacy-e872", str(comment), str(repository), "extra"],
        ["--recover-legacy-other"],
    ):
        assert controller.main(invalid) == 2
    assert len(calls) == 2


def test_exclusive_short_write_cleanup_is_retryable(tmp_path, monkeypatch):
    target = tmp_path / "exclusive" / "state.json"
    real_write = controller.os.write
    calls = 0

    def short_once(fd, value):
        nonlocal calls
        calls += 1
        if calls == 1:
            return 0
        return real_write(fd, value)

    monkeypatch.setattr(controller.os, "write", short_once)
    with pytest.raises(ControllerError, match="EXCLUSIVE_WRITE"):
        controller._exclusive(target, b"first\n")
    assert not target.exists()
    controller._exclusive(target, b"second\n")
    assert target.read_bytes() == b"second\n"


def test_controller_lock_serializes_distinct_approvals(tmp_path):
    runtime = _runtime(tmp_path)
    with runtime._controller_lock():
        with pytest.raises(ControllerError, match="ACTIVE_TRANSACTION"):
            with runtime._controller_lock():
                pytest.fail("second begin unexpectedly acquired the root lock")


def test_nonce_consumption_is_hash_only_and_replay_fails_closed(tmp_path):
    runtime = _runtime(tmp_path)
    nonce = "A" * 43
    staged = {
        "approval_nonce": nonce,
        "approval_comment_id": 11,
        "release_id": 22,
        "approval_body_sha256": "e" * 64,
    }
    runtime._consume_nonce(staged, "d" * 32)
    nonce_files = list((runtime.root / "nonces").glob("*.json"))
    assert len(nonce_files) == 1
    assert nonce.encode() not in nonce_files[0].read_bytes()
    with pytest.raises(ControllerError, match="APPROVAL_NONCE_REPLAY"):
        runtime._consume_nonce(staged, "f" * 32)


@pytest.mark.parametrize("action", ["finalize", "rollback"])
def test_post_migration_mutations_share_controller_lock(tmp_path, action):
    runtime = _runtime(tmp_path)
    request = verify_request(_request(action), expected_action=action)
    with runtime._controller_lock():
        with pytest.raises(ControllerError, match="ACTIVE_TRANSACTION"):
            getattr(runtime, action)(request)


def test_reconciler_shares_controller_lock(tmp_path):
    runtime = _runtime(tmp_path)
    with runtime._controller_lock():
        with pytest.raises(ControllerError, match="ACTIVE_TRANSACTION"):
            runtime.reconcile()


def test_production_begin_passes_owner_deadline_and_memory_token_without_actions_ids(tmp_path, monkeypatch):
    runtime = _runtime(tmp_path)
    transaction_id = "d" * 32
    monkeypatch.setattr(controller.secrets, "token_hex", lambda _: transaction_id)

    class Client:
        def __init__(self, token, repository):
            assert token == "memory-only-token"
            assert repository == "Dimkox/multi-exchange-engine"
            self.closed = False
        def close(self): self.closed = True

    monkeypatch.setattr(controller, "GitHubAcquisitionClient", Client)

    def acquire(_client, **kwargs):
        return _fake_staged_acquisition(kwargs["transaction_root"])

    monkeypatch.setattr(controller, "acquire_begin_inputs", acquire)
    monkeypatch.setattr(controller, "_extract_oci_layout_archive", lambda _source, target: target)
    calls = {}

    class Host:
        @staticmethod
        def main(argv, token_reader=None):
            host_apply_intent = runtime.root / "transactions" / transaction_id / "host-apply-intent.json"
            rollback_intent = runtime._rollback_paths(transaction_id)[0]
            assert host_apply_intent.is_file()
            assert not rollback_intent.exists()
            calls["argv"] = list(argv)
            calls["token"] = token_reader()
            journal = Path(argv[argv.index("--journal") + 1])
            journal.parent.mkdir(parents=True, exist_ok=True)
            journal.write_text('{"phase":"HOST_APPLIED_PENDING_FINALIZE","status":"OPEN"}')
            return 0

    monkeypatch.setattr(runtime, "_host_module", lambda: Host)
    request = verify_request(_request("begin"), expected_action="begin")
    response = runtime.begin(request)
    assert response["transaction_id"] == transaction_id
    assert response["state"] == "HOST_APPLIED_PENDING_FINALIZE"
    assert calls["token"] == "memory-only-token"
    assert calls["argv"][calls["argv"].index("--deadline-seconds") + 1] == "900"
    assert not any(item in calls["argv"] for item in ("--run-id", "--run-attempt", "--job-id"))
    assert (runtime.root / "transactions" / transaction_id / "begin-intent.json").is_file()
    assert b"A" * 43 not in (runtime.root / "transactions" / transaction_id / "inputs" / "manifest.json").read_bytes()

    journal, host_receipt, _ = runtime._paths(transaction_id)
    journal.write_text('{"phase":"COMMITTED","status":"COMMITTED"}')
    host_receipt.write_bytes(b"committed-host-receipt\n")
    prior_sha = controller.hashlib.sha256(host_receipt.read_bytes()).hexdigest()

    class RollbackHost:
        @staticmethod
        def main(argv):
            assert "--rollback" in argv
            journal.write_text('{"phase":"ROLLED_BACK","status":"ROLLED_BACK"}')
            return 0

        @staticmethod
        def durable_unlink(path): Path(path).unlink()

    monkeypatch.setattr(runtime, "_host_module", lambda: RollbackHost)
    rollback_request = {**_request("rollback"), "transaction_id": transaction_id}
    rollback_response = runtime.rollback(verify_request(rollback_request, expected_action="rollback"))
    rollback_intent = runtime._rollback_paths(transaction_id)[0]
    assert json.loads(rollback_intent.read_text())["prior_host_receipt_sha256"] == prior_sha
    assert rollback_response["state"] == "ROLLED_BACK"


def test_begin_host_failure_persists_host_apply_intent_for_token_free_terminal_rollback(tmp_path, monkeypatch):
    runtime = _runtime(tmp_path)
    transaction_id = "d" * 32
    monkeypatch.setattr(controller.secrets, "token_hex", lambda _: transaction_id)

    class Client:
        def __init__(self, *_args): pass
        def close(self): pass

    monkeypatch.setattr(controller, "GitHubAcquisitionClient", Client)
    monkeypatch.setattr(
        controller,
        "acquire_begin_inputs",
        lambda _client, **kwargs: _fake_staged_acquisition(kwargs["transaction_root"]),
    )
    monkeypatch.setattr(controller, "_extract_oci_layout_archive", lambda _source, target: target)

    class Host:
        @staticmethod
        def main(argv, token_reader=None):
            host_apply_intent = runtime.root / "transactions" / transaction_id / "host-apply-intent.json"
            rollback_intent = runtime._rollback_paths(transaction_id)[0]
            assert host_apply_intent.is_file()
            assert not rollback_intent.exists()
            assert token_reader() == "memory-only-token"
            journal = Path(argv[argv.index("--journal") + 1])
            journal.parent.mkdir(parents=True, exist_ok=True)
            journal.write_text('{"phase":"ROLLED_BACK","status":"ROLLED_BACK"}')
            return 2

    monkeypatch.setattr(runtime, "_host_module", lambda: Host)
    with pytest.raises(ControllerError, match="HOST_APPLY"):
        runtime.begin(verify_request(_request("begin"), expected_action="begin"))

    intent, _ = runtime._rollback_paths(transaction_id)
    assert not intent.exists()
    host_apply_intent = runtime.root / "transactions" / transaction_id / "host-apply-intent.json"
    assert json.loads(host_apply_intent.read_text()) == {
        "schema_version": "claw-host-deployment-host-apply-intent-v1",
        "transaction_id": transaction_id,
        "begin_intent_sha256": controller.hashlib.sha256(
            (runtime.root / "transactions" / transaction_id / "begin-intent.json").read_bytes()
        ).hexdigest(),
    }
    request = {**_request("rollback"), "transaction_id": transaction_id}
    response = runtime.rollback(verify_request(request, expected_action="rollback"))
    assert response["state"] == "ROLLED_BACK"
    assert response["receipt_sha256"] is not None
    assert json.loads(intent.read_text())["prior_host_receipt_sha256"] is None


@pytest.mark.parametrize("link_kind", ["symlink", "hardlink"])
def test_host_apply_intent_rejects_link_state(tmp_path, link_kind):
    runtime = _runtime(tmp_path)
    transaction_id = "d" * 32
    staged = _fake_staged_acquisition(runtime.root / "transactions" / transaction_id)
    runtime._create_begin_intent(staged, transaction_id)
    runtime._host_apply_intent(transaction_id, create=True)
    marker = runtime.root / "transactions" / transaction_id / "host-apply-intent.json"
    outside = tmp_path / "outside-host-apply-intent.json"
    outside.write_bytes(marker.read_bytes())
    marker.unlink()
    if link_kind == "symlink":
        marker.symlink_to(outside)
    else:
        controller.os.link(outside, marker)
    with pytest.raises(ControllerError, match="HOST_APPLY_INTENT"):
        runtime._host_apply_intent(transaction_id, create=False)


@pytest.mark.parametrize("link_kind", ["symlink", "hardlink"])
def test_terminal_rollback_rejects_linked_intent_without_host_apply_marker(tmp_path, monkeypatch, link_kind):
    runtime = _runtime(tmp_path)
    transaction_id = "d" * 32
    journal, _, _ = runtime._paths(transaction_id)
    journal.parent.mkdir(parents=True, exist_ok=True)
    journal.write_text('{"phase":"ROLLED_BACK","status":"ROLLED_BACK"}')
    intent, _ = runtime._rollback_paths(transaction_id)
    outside = tmp_path / "outside-rollback-intent.json"
    outside.write_bytes(canonical_bytes({
        "schema_version": "claw-host-deployment-rollback-intent-v1",
        "transaction_id": transaction_id,
        "prior_host_receipt_sha256": None,
    }))
    if link_kind == "symlink":
        intent.symlink_to(outside)
    else:
        controller.os.link(outside, intent)
    monkeypatch.setattr(runtime, "_host_module", lambda: pytest.fail("host recovery must not run"))
    request = {**_request("rollback"), "transaction_id": transaction_id}
    with pytest.raises(ControllerError, match="ROLLBACK_INTENT"):
        runtime.rollback(verify_request(request, expected_action="rollback"))
    assert controller.os.path.lexists(intent)
    assert not runtime._rollback_paths(transaction_id)[1].exists()


def test_begin_recovers_crash_after_nonce_before_host_journal(tmp_path, monkeypatch):
    runtime = _runtime(tmp_path)
    transaction_id = "d" * 32
    monkeypatch.setattr(controller.secrets, "token_hex", lambda _: transaction_id)
    acquisitions = 0

    class Client:
        def __init__(self, *_args): pass
        def close(self): pass

    monkeypatch.setattr(controller, "GitHubAcquisitionClient", Client)

    def acquire(_client, **kwargs):
        nonlocal acquisitions
        acquisitions += 1
        return _fake_staged_acquisition(kwargs["transaction_root"])

    monkeypatch.setattr(controller, "acquire_begin_inputs", acquire)
    monkeypatch.setattr(controller, "_extract_oci_layout_archive", lambda _source, target: target)
    calls = 0

    class Host:
        @staticmethod
        def main(argv, token_reader=None):
            nonlocal calls
            calls += 1
            assert token_reader() == "memory-only-token"
            if calls == 1:
                raise RuntimeError("simulated crash before WAL")
            journal = Path(argv[argv.index("--journal") + 1])
            journal.parent.mkdir(parents=True, exist_ok=True)
            journal.write_text('{"phase":"HOST_APPLIED_PENDING_FINALIZE","status":"OPEN"}')
            return 0

    monkeypatch.setattr(runtime, "_host_module", lambda: Host)
    request = verify_request(_request("begin"), expected_action="begin")
    with pytest.raises(RuntimeError, match="simulated crash"):
        runtime.begin(request)
    assert not runtime._paths(transaction_id)[0].exists()
    assert len(list((runtime.root / "nonces").glob("*.json"))) == 1
    assert (runtime.root / "transactions" / transaction_id / "begin-intent.json").is_file()
    assert b"A" * 43 not in b"".join(path.read_bytes() for path in runtime.root.rglob("*") if path.is_file())

    response = runtime.begin(verify_request(_request("begin"), expected_action="begin"))
    assert response == runtime._response("begin", transaction_id, "HOST_APPLIED_PENDING_FINALIZE")
    assert acquisitions == 1
    assert calls == 2


def test_begin_replay_recovers_transaction_after_pending_journal_before_response(tmp_path, monkeypatch):
    runtime = _runtime(tmp_path)
    transaction_id = "d" * 32
    journal_path, _, _ = runtime._paths(transaction_id)
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    journal_path.write_text('{"phase":"HOST_APPLIED_PENDING_FINALIZE","status":"OPEN"}')
    nonce_root = runtime.root / "nonces"
    nonce_root.mkdir()
    (nonce_root / f"{'c' * 64}.json").write_bytes(canonical_bytes({
        "schema_version": "claw-host-deployment-nonce-consumption-v1",
        "transaction_id": transaction_id,
        "approval_comment_id": 11,
        "release_id": 22,
        "approval_body_sha256": "e" * 64,
        "nonce_sha256": "c" * 64,
    }))
    monkeypatch.setattr(controller, "GitHubAcquisitionClient", lambda *_args: pytest.fail("replay must not reacquire"))
    response = runtime.begin(verify_request(_request("begin"), expected_action="begin"))
    assert response == runtime._response("begin", transaction_id, "HOST_APPLIED_PENDING_FINALIZE")


def test_production_finalize_writes_verified_receipt_last(tmp_path, monkeypatch):
    runtime = _runtime(tmp_path)
    transaction_id = "a" * 32
    journal_path, _, _ = runtime._paths(transaction_id)
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    journal_path.write_text('{"phase":"HOST_APPLIED_PENDING_FINALIZE","status":"OPEN"}')
    projection = {
        "repository": "Dimkox/multi-exchange-engine",
        "runner_id": 17,
        "runner_name": "claw-engine-runner",
        "status": "online",
        "labels": ["claw", "claw-engine-runner", "self-hosted"],
        "matching_count": 1,
        "total_count": 2,
    }
    monkeypatch.setattr(runtime, "_runner_projection", lambda token: projection)
    monkeypatch.setattr(runtime, "_recovery_backend", lambda *_args, **_kwargs: object())
    receipt = {
        "schema_version": "claw-host-bootstrap-receipt-v1",
        "transaction_id": transaction_id,
        "controller_sha": "a" * 40,
        "policy_sha256": "b" * 64,
        "closure_sha256": "c" * 64,
        "oci_archive_sha256": "d" * 64,
        "journal_sha256": "e" * 64,
        "host_inventory_sha256": "f" * 64,
        "runner_api": projection,
        "operation_set_sha256": "1" * 64,
        "projections": {"final": "2" * 64},
        "rollback_capability": "ROOT_JOURNAL_AND_CREDENTIAL_HMAC_RETAINED",
        "status": "VERIFIED",
    }
    events = []

    class FakeJournal:
        @staticmethod
        def resume(path): return path

    class Host:
        Journal = FakeJournal
        @staticmethod
        def finalize(_backend, _journal, value): events.append(("finalize", value))
        @staticmethod
        def receipt(*_args): events.append(("receipt", None)); return receipt

    monkeypatch.setattr(runtime, "_host_module", lambda: Host)
    response = runtime.finalize(verify_request(_request("finalize"), expected_action="finalize"))
    receipt_path = Path(json.loads(runtime.policy_path.read_text())["transaction_root"]) / f"{transaction_id}.receipt.json"
    assert events == [("finalize", projection), ("receipt", None)]
    assert receipt_path.is_file()
    assert response["state"] == "COMMITTED"
    assert response["receipt_sha256"] == controller.hashlib.sha256(receipt_path.read_bytes()).hexdigest()


def test_finalize_retry_reconstructs_receipt_from_committed_journal_without_api(tmp_path, monkeypatch):
    runtime = _runtime(tmp_path)
    transaction_id = "a" * 32
    journal_path, receipt_path, _ = runtime._paths(transaction_id)
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    journal_path.write_text('{"phase":"COMMITTED","status":"COMMITTED"}')
    expected = {
        "schema_version": "claw-host-bootstrap-receipt-v1",
        "transaction_id": transaction_id,
        "controller_sha": "a" * 40,
        "policy_sha256": "b" * 64,
        "closure_sha256": "c" * 64,
        "oci_archive_sha256": "d" * 64,
        "journal_sha256": "e" * 64,
        "host_inventory_sha256": "f" * 64,
        "runner_api": {
            "repository": "Dimkox/multi-exchange-engine", "runner_id": 17,
            "runner_name": "claw-engine-runner", "status": "online",
            "labels": ["claw", "claw-engine-runner", "self-hosted"],
            "matching_count": 1, "total_count": 2,
        },
        "operation_set_sha256": "1" * 64,
        "projections": {"final": "2" * 64},
        "rollback_capability": "ROOT_JOURNAL_AND_CREDENTIAL_HMAC_RETAINED",
        "status": "VERIFIED",
    }

    class Host:
        @staticmethod
        def receipt(*_args): return expected

    monkeypatch.setattr(runtime, "_host_module", lambda: Host)
    monkeypatch.setattr(runtime, "_runner_projection", lambda *_args: pytest.fail("committed retry must not call API"))
    response = runtime.finalize(verify_request(_request("finalize"), expected_action="finalize"))
    assert json.loads(receipt_path.read_text()) == expected
    assert response["state"] == "COMMITTED"
    assert response["receipt_sha256"] == controller.hashlib.sha256(receipt_path.read_bytes()).hexdigest()


def test_successful_rollback_writes_distinct_closed_receipt_last(tmp_path, monkeypatch):
    runtime = _runtime(tmp_path)
    transaction_id = "a" * 32
    journal_path, host_receipt_path, _ = runtime._paths(transaction_id)
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    journal_path.write_text('{"phase":"COMMITTED","status":"COMMITTED"}')
    host_receipt_path.write_bytes(b"committed-host-receipt\n")
    prior_sha = controller.hashlib.sha256(host_receipt_path.read_bytes()).hexdigest()

    class Host:
        @staticmethod
        def main(argv):
            assert "--approval" not in argv
            assert "--approval-policy-path" not in argv
            assert "oci-evidence-approval.json" not in argv
            journal_path.write_text('{"phase":"ROLLED_BACK","status":"ROLLED_BACK"}')
            return 0

        @staticmethod
        def durable_unlink(path):
            Path(path).unlink()

    monkeypatch.setattr(runtime, "_host_module", lambda: Host)
    response = runtime.rollback(verify_request(_request("rollback"), expected_action="rollback"))
    rollback_path = journal_path.parent / f"{transaction_id}.rollback-receipt.json"
    value = json.loads(rollback_path.read_text())
    assert not host_receipt_path.exists()
    assert value == contract.verify_rollback_receipt(value)
    assert value["schema_version"] == "claw-host-deployment-rollback-receipt-v1"
    assert value["authority"] == "NONE"
    assert value["not_host_receipt"] is True
    assert value["receipt_kind"] == "ROLLBACK"
    assert value["status"] == "ROLLED_BACK"
    assert value["prior_host_receipt_sha256"] == prior_sha
    assert response["state"] == "ROLLED_BACK"
    assert response["receipt_sha256"] == controller.hashlib.sha256(rollback_path.read_bytes()).hexdigest()
    repeated = runtime.rollback(verify_request(_request("rollback"), expected_action="rollback"))
    assert repeated == response

    monkeypatch.setattr(runtime, "_runner_projection", lambda *_args: pytest.fail("late finalize must not call API"))
    late = runtime.finalize(verify_request(_request("finalize"), expected_action="finalize"))
    assert late == {
        "schema_version": "claw-host-deployment-response-v1",
        "authority": "NONE",
        "action": "finalize",
        "transaction_id": transaction_id,
        "state": "ROLLED_BACK",
        "receipt_sha256": response["receipt_sha256"],
    }

    schema = json.loads(Path("schemas/claw-host-deployment-rollback-receipt-v1.schema.json").read_text())
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(schema["properties"])


def test_rollback_blocked_retains_host_evidence_and_emits_no_receipt(tmp_path, monkeypatch):
    runtime = _runtime(tmp_path)
    transaction_id = "a" * 32
    journal_path, host_receipt_path, _ = runtime._paths(transaction_id)
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    journal_path.write_text('{"phase":"COMMITTED","status":"COMMITTED"}')
    host_receipt_path.write_bytes(b"committed-host-receipt\n")

    class Host:
        @staticmethod
        def main(_argv):
            journal_path.write_text('{"phase":"ROLLBACK_BLOCKED","status":"OPEN"}')
            return 2

    monkeypatch.setattr(runtime, "_host_module", lambda: Host)
    response = runtime.rollback(verify_request(_request("rollback"), expected_action="rollback"))
    assert response["state"] == "ROLLBACK_BLOCKED"
    assert response["receipt_sha256"] is None
    assert host_receipt_path.is_file()
    assert not (journal_path.parent / f"{transaction_id}.rollback-receipt.json").exists()


def test_rollback_intent_rejects_replaced_host_receipt(tmp_path, monkeypatch):
    runtime = _runtime(tmp_path)
    transaction_id = "a" * 32
    journal_path, host_receipt_path, _ = runtime._paths(transaction_id)
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    journal_path.write_text('{"phase":"COMMITTED","status":"COMMITTED"}')
    host_receipt_path.write_bytes(b"original\n")
    intent = {
        "schema_version": "claw-host-deployment-rollback-intent-v1",
        "transaction_id": transaction_id,
        "prior_host_receipt_sha256": controller.hashlib.sha256(host_receipt_path.read_bytes()).hexdigest(),
    }
    (journal_path.parent / f"{transaction_id}.rollback-intent.json").write_bytes(canonical_bytes(intent))
    (journal_path.parent / f"{transaction_id}.rollback-intent.json").chmod(0o600)
    host_receipt_path.write_bytes(b"replaced\n")
    monkeypatch.setattr(runtime, "_host_module", lambda: pytest.fail("host rollback must not run"))
    with pytest.raises(ControllerError, match="ROLLBACK_PRIOR_RECEIPT"):
        runtime.rollback(verify_request(_request("rollback"), expected_action="rollback"))
    assert host_receipt_path.read_bytes() == b"replaced\n"


def test_rollback_intent_rejects_missing_prior_receipt_before_host_rollback(tmp_path, monkeypatch):
    runtime = _runtime(tmp_path)
    transaction_id = "a" * 32
    journal_path, _, _ = runtime._paths(transaction_id)
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    journal_path.write_text('{"phase":"COMMITTED","status":"COMMITTED"}')
    intent = {
        "schema_version": "claw-host-deployment-rollback-intent-v1",
        "transaction_id": transaction_id,
        "prior_host_receipt_sha256": "c" * 64,
    }
    (journal_path.parent / f"{transaction_id}.rollback-intent.json").write_bytes(canonical_bytes(intent))
    (journal_path.parent / f"{transaction_id}.rollback-intent.json").chmod(0o600)
    monkeypatch.setattr(runtime, "_host_module", lambda: pytest.fail("host rollback must not run"))
    with pytest.raises(ControllerError, match="ROLLBACK_PRIOR_RECEIPT"):
        runtime.rollback(verify_request(_request("rollback"), expected_action="rollback"))


def test_committed_rollback_without_prior_receipt_or_intent_fails_before_mutation(tmp_path, monkeypatch):
    runtime = _runtime(tmp_path)
    transaction_id = "a" * 32
    journal_path, _, _ = runtime._paths(transaction_id)
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    journal_path.write_text('{"phase":"COMMITTED","status":"COMMITTED"}')
    monkeypatch.setattr(runtime, "_host_module", lambda: pytest.fail("host rollback must not run"))
    with pytest.raises(ControllerError, match="ROLLBACK_PRIOR_RECEIPT"):
        runtime.rollback(verify_request(_request("rollback"), expected_action="rollback"))


def test_existing_rollback_receipt_is_bound_to_installed_controller(tmp_path, monkeypatch):
    runtime = _runtime(tmp_path)
    transaction_id = "a" * 32
    journal_path, _, _ = runtime._paths(transaction_id)
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    journal_path.write_text('{"phase":"ROLLED_BACK","status":"ROLLED_BACK"}')
    (journal_path.parent / f"{transaction_id}.rollback-intent.json").write_bytes(canonical_bytes({
        "schema_version": "claw-host-deployment-rollback-intent-v1",
        "transaction_id": transaction_id,
        "prior_host_receipt_sha256": None,
    }))
    (journal_path.parent / f"{transaction_id}.rollback-intent.json").chmod(0o600)
    rollback_path = journal_path.parent / f"{transaction_id}.rollback-receipt.json"
    rollback_path.write_bytes(canonical_bytes({
        "schema_version": "claw-host-deployment-rollback-receipt-v1",
        "authority": "NONE",
        "not_host_receipt": True,
        "receipt_kind": "ROLLBACK",
        "transaction_id": transaction_id,
        "controller_sha": "f" * 40,
        "controller_tree": "b" * 40,
        "policy_sha256": controller.hashlib.sha256(runtime.policy_path.read_bytes()).hexdigest(),
        "closure_sha256": controller.hashlib.sha256(runtime.closure_path.read_bytes()).hexdigest(),
        "journal_sha256": controller.hashlib.sha256(journal_path.read_bytes()).hexdigest(),
        "prior_host_receipt_sha256": None,
        "status": "ROLLED_BACK",
        "created_at": controller.dt.datetime.now(controller.dt.timezone.utc).isoformat().replace("+00:00", "Z"),
    }))
    monkeypatch.setattr(runtime, "_host_module", lambda: pytest.fail("existing receipt must be verified first"))
    with pytest.raises(contract.ContractError, match="ROLLBACK_RECEIPT_BINDING"):
        runtime.rollback(verify_request(_request("rollback"), expected_action="rollback"))


@pytest.mark.parametrize(
    ("phase", "expected"),
    [
        ("PREPARED", "BEGIN_ACCEPTED"),
        ("APPLYING(stop_engine)", "APPLYING"),
        ("APPLIED(stop_engine)", "APPLYING"),
        ("VERIFYING", "VERIFYING"),
        ("VERIFIED", "FINALIZING"),
        ("ROLLING_BACK", "ROLLING_BACK"),
    ],
)
def test_status_maps_internal_journal_phases_to_closed_public_states(tmp_path, phase, expected):
    runtime = _runtime(tmp_path)
    transaction_id = "a" * 32
    journal_path, _, _ = runtime._paths(transaction_id)
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    journal_path.write_text(json.dumps({"phase": phase, "status": "OPEN"}))
    response = runtime.status(verify_request(_request("status"), expected_action="status"))
    assert response["state"] == expected
    assert response["state"] in controller.RESPONSE_STATES


def test_deadline_reconcile_writes_separate_rollback_receipt(tmp_path, monkeypatch):
    runtime = _runtime(tmp_path)
    transaction_id = "a" * 32
    journal_path, _, _ = runtime._paths(transaction_id)
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    journal_path.write_text('{"phase":"HOST_APPLIED_PENDING_FINALIZE","status":"OPEN"}')
    monkeypatch.setattr(runtime, "_recovery_backend", lambda *_args, **_kwargs: object())

    class FakeJournal:
        def __init__(self, path):
            self.path = path
            self.value = json.loads(Path(path).read_text())
        @staticmethod
        def resume(path): return FakeJournal(path)

    class Host:
        TxError = RuntimeError
        Journal = FakeJournal
        @staticmethod
        def deadline_due(_journal): return True
        @staticmethod
        def reconcile_deadline(_backend, journal):
            assert (journal_path.parent / f"{transaction_id}.rollback-intent.json").is_file()
            Path(journal.path).write_text('{"phase":"ROLLED_BACK","status":"ROLLED_BACK"}')
            return True
        @staticmethod
        def durable_unlink(path): Path(path).unlink()

    monkeypatch.setattr(runtime, "_host_module", lambda: Host)
    runtime.reconcile()
    receipt_path = journal_path.parent / f"{transaction_id}.rollback-receipt.json"
    value = contract.verify_rollback_receipt(json.loads(receipt_path.read_text()))
    assert value["prior_host_receipt_sha256"] is None
    assert value["status"] == "ROLLED_BACK"


def test_reconcile_resume_never_requires_external_approval(tmp_path, monkeypatch):
    runtime = _runtime(tmp_path)
    transaction_id = "a" * 32
    journal_path, _, _ = runtime._paths(transaction_id)
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    journal_path.write_text('{"phase":"HOST_APPLIED_PENDING_FINALIZE","status":"OPEN"}')
    resumed: list[Path] = []
    installed_approval = Path("/usr/local/libexec/mee-claw-host-deploy-lib/oci-evidence-approval.json")
    original_is_file = Path.is_file

    class FakeJournal:
        def __init__(self, path):
            self.value = json.loads(Path(path).read_text())

        @staticmethod
        def resume(*args):
            assert "--approval" not in args
            assert "--approval-policy-path" not in args
            assert installed_approval not in args
            assert args == (journal_path,)
            resumed.append(Path(args[0]))
            return FakeJournal(args[0])

    class Host:
        TxError = RuntimeError
        Journal = FakeJournal

        @staticmethod
        def deadline_due(_journal):
            return False

    def is_file(path):
        if path == installed_approval:
            pytest.fail("resume must not inspect installed approval")
        return original_is_file(path)

    monkeypatch.setattr(Path, "is_file", is_file)
    monkeypatch.setattr(runtime, "_host_module", lambda: Host)
    monkeypatch.setattr(runtime, "_recovery_backend", lambda *_args, **_kwargs: pytest.fail("resume must not start external recovery"))

    runtime.reconcile()

    assert resumed == [journal_path]


@pytest.mark.parametrize("phase", ["PREPARED", "APPLYING(stop_engine)", "APPLIED(stop_engine)", "VERIFYING", "ROLLING_BACK", "ROLLBACK_BLOCKED"])
def test_reconcile_rolls_back_every_interrupted_open_apply(tmp_path, monkeypatch, phase):
    runtime = _runtime(tmp_path)
    transaction_id = "a" * 32
    journal_path, _, _ = runtime._paths(transaction_id)
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    journal_path.write_text(json.dumps({"phase": phase, "status": "OPEN"}))

    class Host:
        TxError = RuntimeError

        @staticmethod
        def main(argv):
            assert "--rollback" in argv
            assert (journal_path.parent / f"{transaction_id}.rollback-intent.json").is_file()
            journal_path.write_text('{"phase":"ROLLED_BACK","status":"ROLLED_BACK"}')
            return 0

        @staticmethod
        def durable_unlink(path): Path(path).unlink()

    monkeypatch.setattr(runtime, "_host_module", lambda: Host)
    runtime.reconcile()
    receipt_path = journal_path.parent / f"{transaction_id}.rollback-receipt.json"
    assert contract.verify_rollback_receipt(json.loads(receipt_path.read_text()))["status"] == "ROLLED_BACK"


def test_reconcile_accepts_durable_pre_mutation_initialization_cleanup(tmp_path, monkeypatch):
    runtime = _runtime(tmp_path)
    transaction_id = "a" * 32
    journal_path, _, _ = runtime._paths(transaction_id)
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    journal_path.write_text(json.dumps({
        "phase": "PREPARED", "status": "OPEN", "applied": [], "current": None,
    }))

    class Host:
        TxError = RuntimeError

        @staticmethod
        def main(argv):
            assert "--rollback" in argv
            journal_path.unlink()
            return 0

        @staticmethod
        def durable_unlink(path): Path(path).unlink()

    monkeypatch.setattr(runtime, "_host_module", lambda: Host)
    runtime.reconcile()
    assert not journal_path.exists()
    assert not (journal_path.parent / f"{transaction_id}.rollback-intent.json").exists()
    assert not (journal_path.parent / f"{transaction_id}.rollback-receipt.json").exists()


def test_reconcile_rejects_terminal_rollback_without_prior_intent(tmp_path, monkeypatch):
    runtime = _runtime(tmp_path)
    transaction_id = "a" * 32
    journal_path, _, _ = runtime._paths(transaction_id)
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    journal_path.write_text('{"phase":"ROLLED_BACK","status":"ROLLED_BACK"}')

    class Host:
        TxError = RuntimeError

    monkeypatch.setattr(runtime, "_host_module", lambda: Host)
    with pytest.raises(ControllerError, match="RECONCILE_FAILED"):
        runtime.reconcile()
