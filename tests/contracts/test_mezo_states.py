"""Offline obligations for the F2 report, quote, payment, and delivery graphs."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2] / "schemas" / "mezo-evidence" / "v1"


def _load(name: str) -> dict:
    with (ROOT / name).open(encoding="utf-8") as source:
        return json.load(source)


def _machine(graph: dict, name: str) -> dict:
    return next(machine for machine in graph["machines"] if machine["name"] == name)


def _transition(machine: dict, source: str, event: str) -> dict:
    matches = [
        item for item in machine["transitions"] if item["from"] == source and item["event"] == event
    ]
    assert len(matches) == 1
    return matches[0]


def _take(machine: dict, source: str, event: str, satisfied: set[str]) -> str:
    transition = _transition(machine, source, event)
    assert set(transition["guards"]) <= satisfied, "transition guard is unsatisfied"
    return transition["to"]


def _reachable(machine: dict, start: str) -> set[str]:
    reached = {start}
    frontier = [start]
    while frontier:
        current = frontier.pop()
        for transition in machine["transitions"]:
            target = transition["to"]
            if transition["from"] == current and target not in reached:
                reached.add(target)
                frontier.append(target)
    return reached


def _assert_graph_consistent(graph: dict) -> None:
    assert graph["schema"] == "mee-evidence-states/v1"
    assert {machine["name"] for machine in graph["machines"]} == {
        "report_request",
        "quote",
        "payment_attempt",
        "delivery",
    }
    for machine in graph["machines"]:
        states = set(machine["states"])
        assert len(states) == len(machine["states"])
        assert machine["initial"] in states
        assert _reachable(machine, machine["initial"]) == states
        event_sources = set()
        for transition in machine["transitions"]:
            assert {transition["from"], transition["to"]} <= states
            key = transition["from"], transition["event"]
            assert key not in event_sources
            event_sources.add(key)
            assert transition["guards"] and transition["effects"]
            assert len(set(transition["guards"])) == len(transition["guards"])
            assert len(set(transition["effects"])) == len(transition["effects"])
    expected_edges = {
        "report_request": {
            ("PREPARING", "artifact_verified", "READY"),
            ("PREPARING", "data_rejected", "REJECTED"),
            ("PREPARING", "build_failed", "BUILD_FAILED"),
        },
        "quote": {
            ("READY", "authorization_accepted", "PAYMENT_PENDING"),
            ("READY", "deadline_passed", "EXPIRED"),
            ("PAYMENT_PENDING", "outcome_unknown", "PAYMENT_UNCERTAIN"),
            ("PAYMENT_PENDING", "payment_confirmed", "PAID"),
            ("PAYMENT_UNCERTAIN", "reconciled_confirmation", "PAID"),
            ("PAYMENT_PENDING", "definitive_pre_submit_rejection", "READY"),
            ("PAYMENT_PENDING", "definitive_pre_submit_rejection_after_expiry", "EXPIRED"),
            ("PAYMENT_PENDING", "inconsistent_receipt", "MANUAL_REVIEW"),
            ("PAYMENT_UNCERTAIN", "reconciliation_exhausted", "MANUAL_REVIEW"),
            ("PAID", "chain_inconsistency", "MANUAL_REVIEW"),
            ("MANUAL_REVIEW", "authoritative_confirmation", "PAID"),
        },
        "payment_attempt": {
            ("RECEIVED", "verification_succeeded", "VERIFIED"),
            ("RECEIVED", "verification_rejected", "REJECTED"),
            ("VERIFIED", "submit_committed", "SUBMITTING"),
            ("VERIFIED", "expired_before_submit", "REJECTED"),
            ("SUBMITTING", "receipt_confirmed", "CONFIRMED"),
            ("SUBMITTING", "timeout_or_crash", "UNKNOWN"),
            ("SUBMITTING", "definitely_not_submitted", "REJECTED"),
            ("UNKNOWN", "reconciled_confirmation", "CONFIRMED"),
            ("UNKNOWN", "unresolved", "MANUAL_REVIEW"),
            ("CONFIRMED", "chain_inconsistency", "MANUAL_REVIEW"),
            ("MANUAL_REVIEW", "authoritative_confirmation", "CONFIRMED"),
        },
        "delivery": {
            ("NOT_ATTEMPTED", "delivery_started", "ATTEMPTED"),
            ("ATTEMPTED", "read_retried", "ATTEMPTED"),
        },
    }
    for name, expected in expected_edges.items():
        assert {
            (transition["from"], transition["event"], transition["to"])
            for transition in _machine(graph, name)["transitions"]
        } == expected
    attempt = _machine(graph, "payment_attempt")
    assert "SUBMITTING" not in _reachable(attempt, "UNKNOWN")
    assert "SUBMITTING" not in _reachable(attempt, "MANUAL_REVIEW")
    quote = _machine(graph, "quote")
    assert "EXPIRED" not in _reachable(quote, "PAYMENT_UNCERTAIN")
    assert "EXPIRED" not in _reachable(quote, "PAID")
    assert "EXPIRED" not in _reachable(quote, "MANUAL_REVIEW")


def _delivery_allowed(
    graph: dict, *, quote: str, attempt: str, finality: bool, chain_inconsistency: bool
) -> bool:
    delivery = _machine(graph, "delivery")
    transition = _transition(delivery, "ATTEMPTED", "read_retried")
    facts = {"entitlement_matches_digest", "storage_integrity_verified"}
    if quote == "PAID":
        facts.add("quote_is_paid")
    if attempt == "CONFIRMED":
        facts.add("attempt_is_confirmed")
    if finality:
        facts.add("current_finality_verified")
    if not chain_inconsistency:
        facts.add("no_chain_inconsistency")
    return set(transition["guards"]) <= facts


def test_unknown_cannot_restart_settlement():
    assert (ROOT / "states.json").is_file(), "payment state contract is missing"
    graph = _load("states.json")
    machine = next(m for m in graph["machines"] if m["name"] == "payment_attempt")
    outgoing = {t["to"] for t in machine["transitions"] if t["from"] == "UNKNOWN"}
    assert outgoing == {"CONFIRMED", "MANUAL_REVIEW"}
    assert all(
        t["to"] not in {"RECEIVED", "VERIFIED", "SUBMITTING"}
        for t in machine["transitions"]
        if t["from"] == "MANUAL_REVIEW"
    )


def test_machines_are_closed_reachable_and_do_not_reenter_submission():
    graph = _load("states.json")
    _assert_graph_consistent(graph)
    mutated = json.loads(json.dumps(graph))
    _machine(mutated, "payment_attempt")["transitions"].append(
        {
            "from": "UNKNOWN",
            "event": "retry",
            "to": "SUBMITTING",
            "guards": ["not_expired"],
            "effects": ["one_settle_call_after_commit"],
        }
    )
    with pytest.raises(AssertionError):
        _assert_graph_consistent(mutated)


def test_state_schema_closes_every_record_and_fixes_unresolved_bindings():
    schema = _load("states.schema.json")
    assert schema["$id"] == "https://schemas.liqvera.invalid/mezo-evidence/v1/states.schema.json"
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    for name, record in {"root": schema, **schema["$defs"]}.items():
        if record.get("type") == "object":
            assert record["additionalProperties"] is False, name
            assert set(record["required"]) == set(record["properties"]), name
    bindings = schema["$defs"]["bindings"]["properties"]
    assert bindings["payment_ready"] == {"const": False}
    assert schema["$defs"]["finality_binding"]["properties"]["status"] == {"const": "UNRESOLVED"}
    assert schema["$defs"]["authorization_binding"]["properties"]["status"] == {
        "const": "UNRESOLVED"
    }


def test_report_readback_is_the_only_chargeable_quote_origin():
    graph = _load("states.json")
    request = _machine(graph, "report_request")
    quote = _machine(graph, "quote")
    assert request["initial"] == "PREPARING"
    assert quote["initial"] == "READY"
    assert {transition["event"] for transition in request["transitions"]} == {
        "artifact_verified",
        "data_rejected",
        "build_failed",
    }
    verified = _transition(request, "PREPARING", "artifact_verified")
    assert verified["to"] == "READY"
    assert set(verified["guards"]) == {
        "semantic_report_valid",
        "live_source",
        "immutable_publish_complete",
        "report_and_bundle_readback_verified",
    }
    assert set(verified["effects"]) == {"issue_one_quote", "bind_scope_and_digest"}
    for event, target in (("data_rejected", "REJECTED"), ("build_failed", "BUILD_FAILED")):
        rejection = _transition(request, "PREPARING", event)
        assert rejection["to"] == target
        assert rejection["effects"] == ["no_quote"]
    with pytest.raises(AssertionError):
        _take(
            request,
            "PREPARING",
            "artifact_verified",
            {"semantic_report_valid", "live_source", "immutable_publish_complete"},
        )


def test_expiry_blocks_only_new_or_proven_unbroadcast_payment():
    graph = _load("states.json")
    quote = _machine(graph, "quote")
    attempt = _machine(graph, "payment_attempt")
    assert _take(quote, "READY", "deadline_passed", {"no_active_attempt"}) == "EXPIRED"
    assert _transition(quote, "PAYMENT_PENDING", "outcome_unknown")["to"] == "PAYMENT_UNCERTAIN"
    exception = _transition(
        quote, "PAYMENT_PENDING", "definitive_pre_submit_rejection_after_expiry"
    )
    assert exception["to"] == "EXPIRED"
    assert set(exception["guards"]) == {"authoritative_no_broadcast_proof", "quote_expired"}
    for missing in exception["guards"]:
        with pytest.raises(AssertionError):
            _take(
                quote, "PAYMENT_PENDING", exception["event"], set(exception["guards"]) - {missing}
            )
    assert all(
        t["to"] != "EXPIRED" for t in quote["transitions"] if t["from"] == "PAYMENT_UNCERTAIN"
    )
    assert (
        "not_expired"
        not in _transition(quote, "PAYMENT_UNCERTAIN", "reconciled_confirmation")["guards"]
    )
    assert (
        "quote_not_expired"
        not in _transition(attempt, "UNKNOWN", "reconciled_confirmation")["guards"]
    )
    assert (
        _take(
            attempt, "UNKNOWN", "reconciled_confirmation", {"final_receipt_bound_to_authorization"}
        )
        == "CONFIRMED"
    )
    assert (
        _take(
            quote,
            "PAYMENT_UNCERTAIN",
            "reconciled_confirmation",
            {"final_receipt_bound_to_authorization", "atomic_entitlement_commit"},
        )
        == "PAID"
    )
    assert graph["bindings"]["expiry_policy"] == {
        "not_expired": "now < expires_at",
        "quote_not_expired": "now < expires_at",
        "quote_expired": "now >= expires_at",
        "submitted_confirmation_after_expiry": True,
    }


def test_new_payment_requires_all_bindings_and_durable_attempt():
    graph = _load("states.json")
    quote = _machine(graph, "quote")
    attempt = _machine(graph, "payment_attempt")
    accepted = _transition(quote, "READY", "authorization_accepted")
    assert set(accepted["guards"]) == {
        "not_expired",
        "scope_matches",
        "payer_matches",
        "terms_match",
        "artifact_readback_verified",
        "payment_bindings_verified",
        "no_active_attempt",
        "authorization_unique",
    }
    assert accepted["effects"] == ["persist_attempt_before_submit"]
    submitted = _transition(attempt, "VERIFIED", "submit_committed")
    assert set(submitted["guards"]) == {
        "attempt_durable",
        "quote_not_expired",
        "no_other_active_attempt",
    }
    assert submitted["effects"] == ["one_settle_call_after_commit"]
    assert graph["bindings"]["payment_ready"] is False
    for key in ("finality", "authorization_identity"):
        assert graph["bindings"][key]["status"] == "UNRESOLVED"
        assert graph["bindings"][key]["owner"] == "F5"
        assert graph["bindings"][key]["required_before"] == "payment_bindings_verified"


@pytest.mark.parametrize(
    ("quote", "attempt", "finality", "inconsistency", "allowed"),
    [
        ("PAID", "CONFIRMED", True, False, True),
        ("PAID", "CONFIRMED", False, False, False),
        ("PAID", "MANUAL_REVIEW", True, False, False),
        ("MANUAL_REVIEW", "CONFIRMED", True, False, False),
        ("PAID", "CONFIRMED", True, True, False),
        ("PAYMENT_UNCERTAIN", "UNKNOWN", True, False, False),
    ],
)
def test_each_repeat_report_or_bundle_read_rechecks_joint_state(
    quote, attempt, finality, inconsistency, allowed
):
    graph = _load("states.json")
    assert (
        _delivery_allowed(
            graph,
            quote=quote,
            attempt=attempt,
            finality=finality,
            chain_inconsistency=inconsistency,
        )
        is allowed
    )
    delivery = _machine(graph, "delivery")
    assert (
        _transition(delivery, "NOT_ATTEMPTED", "delivery_started")["guards"]
        == _transition(delivery, "ATTEMPTED", "read_retried")["guards"]
    )
    assert _transition(delivery, "ATTEMPTED", "read_retried")["effects"] == ["no_settlement"]


def test_chain_inconsistency_withholds_paid_repeat_until_reconfirmed():
    graph = _load("states.json")
    quote = _machine(graph, "quote")
    attempt = _machine(graph, "payment_attempt")
    assert _delivery_allowed(
        graph, quote="PAID", attempt="CONFIRMED", finality=True, chain_inconsistency=False
    )
    assert _take(quote, "PAID", "chain_inconsistency", {"reorg_or_rpc_conflict"}) == "MANUAL_REVIEW"
    assert not _delivery_allowed(
        graph, quote="MANUAL_REVIEW", attempt="CONFIRMED", finality=False, chain_inconsistency=True
    )
    assert (
        _take(attempt, "CONFIRMED", "chain_inconsistency", {"reorg_or_rpc_conflict"})
        == "MANUAL_REVIEW"
    )
    assert not _delivery_allowed(
        graph, quote="PAID", attempt="MANUAL_REVIEW", finality=True, chain_inconsistency=False
    )
    assert (
        _take(
            attempt,
            "MANUAL_REVIEW",
            "authoritative_confirmation",
            {"final_receipt_bound_to_authorization"},
        )
        == "CONFIRMED"
    )
    assert (
        _take(
            quote,
            "MANUAL_REVIEW",
            "authoritative_confirmation",
            {"final_receipt_bound_to_authorization", "atomic_entitlement_commit"},
        )
        == "PAID"
    )
    assert _delivery_allowed(
        graph, quote="PAID", attempt="CONFIRMED", finality=True, chain_inconsistency=False
    )
    assert all(
        "one_settle_call_after_commit" not in t["effects"]
        for machine in graph["machines"]
        for t in machine["transitions"]
        if t["from"] == "MANUAL_REVIEW"
    )


def test_authorization_validity_and_replay_outlive_artifact_retention():
    graph = _load("states.json")
    names = {item["name"]: item for item in graph["invariants"]}
    assert set(names) == {
        "delivery_requires_current_confirmation",
        "retention_covers_authorization_validity",
        "deletion_cannot_enable_replay",
    }
    assert all(item["owner"] == "F5" and item["expression"] for item in names.values())
    created = datetime(2026, 9, 24, tzinfo=timezone.utc)
    ledger_floor = created + timedelta(days=30)
    now = created + timedelta(days=31)
    authorization_valid_until = created + timedelta(days=61)
    # The review obligation survives the ordinary 30-day ledger floor.
    assert ledger_floor < now < authorization_valid_until
    retention_expression = names["retention_covers_authorization_validity"]["expression"]
    assert "authorization's validity horizon" in retention_expression
    assert "if that horizon is unknown" in retention_expression
    replay_expression = names["deletion_cannot_enable_replay"]["expression"]
    assert "until reviewed evidence proves reuse impossible" in replay_expression
    assert graph["bindings"]["authorization_identity"]["requirements"] == [
        "canonical scheme-specific identity",
        "nonce semantics",
        "replay domain",
        "quote association",
        "chain correlation",
    ]
    assert {item["entity"]: item["fields"] for item in graph["uniqueness"]} == {
        "report_request": ["access_scope", "idempotency_key"],
        "payment_attempt": ["authorization_identity"],
        "chain_event": ["chain_id", "tx_hash", "log_index"],
        "entitlement": ["quote_id", "report_id", "report_sha256"],
        "active_attempt": ["quote_id"],
    }
