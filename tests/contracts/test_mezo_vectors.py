"""F2 vector consistency; these checks do not execute future F3–F5 runtimes."""

import copy
import hashlib
import json
from datetime import datetime
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from fractions import Fraction
from pathlib import Path
from uuid import UUID

import pytest
from mee_contracts.evidence import RawPublicEnvelope
from mee_contracts.exact import ExactDecimal
from mee_contracts.market import InstrumentIdentity
from mee_contracts.provenance import MappingDecision, MarketMappingEvidence
from mee_readonly_analyzer.identity import bind_reconstructed_books
from mee_readonly_analyzer.reconstruction import reconstruct_books
from mee_readonly_analyzer.vwap import DepthRejected, Side, sweep_depth

ROOT = Path(__file__).resolve().parents[2] / "schemas/mezo-evidence/v1"
ASSERTIONS = {
    "F3": {
        "report_builder_matches_exact_sweep",
        "fixture_is_not_live_sale",
        "insufficient_depth_never_sells_partial",
        "dataset_policy_rejects_invalid_evidence",
        "live_outage_never_uses_fixture",
        "report_provenance_required",
        "canonical_report_bytes_reproduce",
    },
    "F4": {
        "invalid_request_never_creates_quote",
        "canonical_retries_one_quote",
        "twenty_concurrent_retries_one_quote",
        "idempotency_body_conflict",
        "idempotency_scope_isolation",
        "sibling_scope_never_reads_body",
        "capability_required_for_access",
        "unpaid_read_returns_sdk_402",
        "missing_artifact_prevents_payment",
        "paid_artifact_loss_requires_recovery_without_charge",
    },
    "F5": {
        "atomic_amount_matches_all_layers",
        "invalid_authorization_never_entitles",
        "sdk_identity_deduplicates_reencoding",
        "receipt_log_bound_to_authorization",
        "verify_alone_never_delivers",
        "unknown_never_resubmits",
        "crash_recovery_never_double_charges",
        "lost_response_reuses_entitlement",
        "expiry_blocks_new_payment_only",
        "late_confirmation_delivers_original",
        "paid_repeat_read_never_settles",
        "current_confirmation_required_for_delivery",
        "retention_covers_authorization_validity",
        "deletion_cannot_enable_replay",
    },
}


def support():
    assert (ROOT / "vectors.schema.json").is_file(), "vector schema is missing"
    import mezo_evidence_support

    return mezo_evidence_support


def strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate key")
            result[key] = value
        return result

    def nonfinite(value):
        raise ValueError(f"nonfinite JSON: {value}")

    return json.loads(text, parse_float=Decimal, parse_constant=nonfinite, object_pairs_hook=pairs)


def vector_document():
    assert (ROOT / "vectors.json").is_file(), "exact vectors are missing"
    document = strict_json((ROOT / "vectors.json").read_text(encoding="utf-8"))
    c = support()
    c.validate(c.load("vectors.schema.json"), document, document="vectors.schema.json")
    return document


def records():
    return vector_document()["vectors"]


@pytest.fixture(scope="module")
def review_vectors():
    return {vector["id"]: vector for vector in records()}


def test_final_review_vector_http_statuses_are_declared_by_their_endpoints(review_vectors):
    paths = support().load("openapi.json")["paths"]
    endpoints = {"quote": "/v1/report-quotes/{quote_id}",
                 "report": "/v1/reports/{report_id}",
                 "evidence": "/v1/reports/{report_id}/evidence"}
    for vector in review_vectors.values():
        if vector["kind"] == "access":
            path = endpoints[vector["input"]["resource"]]
            assert str(vector["expected"]["http_status"]) in paths[path]["get"]["responses"], vector["id"]
        elif vector["kind"] == "idempotency":
            for status in vector["expected"]["http_statuses"]:
                assert str(status) in paths["/v1/report-quotes"]["post"]["responses"], vector["id"]
        elif vector["kind"] in {"payment", "recovery"}:
            assert str(vector["expected"]["http_status"]) in paths[endpoints["report"]]["get"]["responses"], vector["id"]


@pytest.mark.parametrize("authorization,status,code", [
    ("same_scope", 410, "QUOTE_EXPIRED"), ("missing", 401, "UNAUTHORIZED"),
    ("other_scope", 404, "NOT_FOUND")])
def test_final_review_expired_quote_preserves_scope_boundary(review_vectors, authorization, status, code):
    vector = copy.deepcopy(review_vectors["missing-quote"])
    vector["input"].update(authorization=authorization, quote_state="EXPIRED",
                           attempt_state="REJECTED", entitlement_present=False)
    vector["expected"].update(http_status=status, code=code)
    check_access(vector)


@pytest.mark.parametrize("vector_id,reason", [
    ("source-age-boundary", "SIMULATED_SOURCE"), ("source-age-outside", "STALE_SOURCE"),
    ("crossed-book", "CROSSED_BOOK"), ("live-upstream-outage", "SOURCE_UNAVAILABLE")])
def test_final_review_fixture_reason_preserves_specific_rejections(review_vectors, vector_id, reason):
    source = strict_json(review_vectors[vector_id]["input"]["dataset_json"])
    assert dataset_reason(source) == reason


@pytest.mark.parametrize("vector_id,now,expiry", [
    ("crash-after-durable-attempt-before-submit", "2026-09-24T12:02:00Z", "2026-09-24T12:02:00.000000001Z"),
    ("expired-before-submitting", "2026-09-24T12:02:00.000Z", "2026-09-24T12:02:00Z"),
    ("expired-before-submitting", "2026-09-24T12:02:00.000000001Z", "2026-09-24T12:02:00Z"),
    ("submitted-before-confirmed-after-expiry", "2026-09-24T12:02:00.1Z", "2026-09-24T12:02:00Z"),
    ("unknown-retained-after-expiry", "2026-09-24T12:02:00.1Z", "2026-09-24T12:02:00Z")])
def test_final_review_expiry_compares_exact_instants(review_vectors, vector_id, now, expiry):
    vector = copy.deepcopy(review_vectors[vector_id])
    vector["input"].update(now=now, quote_expires_at=expiry)
    check_recovery(vector)


@pytest.mark.parametrize("mutation", ["assertion", "reused", "attempts", "settlements", "entitlement"])
def test_final_review_reencoded_identity_cannot_claim_resolution(review_vectors, mutation):
    vector = copy.deepcopy(review_vectors["reencoded-authorization"])
    if mutation == "assertion":
        vector["future_assertions"] = ["invalid_authorization_never_entitles"]
    elif mutation == "reused":
        claims = strict_json(vector["input"]["candidate_claims_json"])
        claims["authorization_reused"] = True
        vector["input"]["candidate_claims_json"] = json.dumps(claims)
        vector["expected"].update(http_status=409, code="AUTHORIZATION_REUSED")
    else:
        field = {"attempts": "distinct_attempts", "settlements": "settlement_calls",
                 "entitlement": "entitlement_count"}[mutation]
        vector["expected"][field] = 1
    with pytest.raises(AssertionError):
        check_payment(vector)


@pytest.mark.parametrize("mutation", ["flag", "scenario"])
def test_followup_reencoding_scenario_and_claim_are_equivalent(review_vectors, mutation):
    vector = copy.deepcopy(review_vectors["reencoded-authorization"])
    if mutation == "flag":
        claims = strict_json(vector["input"]["candidate_claims_json"])
        claims["same_authorization_different_encoding"] = False
        vector["input"]["candidate_claims_json"] = json.dumps(claims)
    else:
        vector["input"]["scenario"] = "exact_units"
    with pytest.raises(AssertionError):
        check_payment(vector)


@pytest.mark.parametrize("relation,delta", [("before", -1), ("equal", 0), ("after", 1)])
def test_followup_long_fraction_preserves_exact_order(relation, delta):
    # A schema-valid fraction exceeds Python's decimal-string-to-int limit.
    digits = "1" * 4300 + str(1 + delta)
    actual = utc_instant("2026-09-24T12:02:00." + digits + "Z")
    whole = utc_instant("2026-09-24T12:02:00Z")
    numerator = (10 ** 4301 - 1) // 9
    boundary = whole + Fraction(numerator, 10 ** 4301)
    assert actual - boundary == Fraction(delta, 10 ** 4301), relation
    assert (actual < boundary, actual == boundary, actual > boundary) == (
        delta < 0, delta == 0, delta > 0)


@pytest.mark.parametrize("mutation", ["wrong_version", "missing_version", "extra_field"])
def test_records_rejects_invalid_on_disk_envelope(tmp_path, monkeypatch, mutation):
    c = support()
    document = strict_json((ROOT / "vectors.json").read_text())
    if mutation == "wrong_version":
        document["schema"] = "mee-evidence-vectors/v2"
    elif mutation == "missing_version":
        del document["schema"]
    else:
        document["unreviewed_override"] = True
    (tmp_path / "vectors.json").write_text(json.dumps(document), encoding="utf-8")
    # Data loads from the temporary directory; references use the real schema registry.
    (tmp_path / "vectors.schema.json").write_bytes((ROOT / "vectors.schema.json").read_bytes())
    monkeypatch.setitem(globals(), "ROOT", tmp_path)
    with pytest.raises(c.ContractError):
        records()


def test_sell_nonterminating_vector_is_exact():
    values = {v["id"]: v for v in records()}
    value = values["sell-two-levels"]["expected"]
    assert value["notional_quote"] == {"numerator": "14995", "denominator": "1"}
    assert value["vwap"] == {"numerator": "299900", "denominator": "3"}
    assert value["price_impact_bps"] == {"numerator": "10", "denominator": "3"}
    assert value["worst_price"] == {"numerator": "99900", "denominator": "1"}
    assert value["consumed_levels"] == 2
    assert values["sell-two-levels"]["runtime_status"] == "NOT_RUN"


@pytest.mark.parametrize(
    "kind",
    [
        "sweep",
        "invalid_request",
        "dataset_rejection",
        "idempotency",
        "payment",
        "access",
        "recovery",
        "artifact",
    ],
)
def test_each_future_family_has_literal_obligations(kind):
    family = [v for v in records() if v["kind"] == kind]
    assert family, f"missing {kind} obligations"
    assert all(v["runtime_status"] == "NOT_RUN" for v in family)
    assert all(v["input"] and v["expected"] and v["future_assertions"] for v in family)


def rational(value):
    result = Fraction(int(value["numerator"]), int(value["denominator"]))
    assert value == {"numerator": str(result.numerator), "denominator": str(result.denominator)}
    return result


def display(value):
    with localcontext() as context:
        context.prec = 28
        context.rounding = ROUND_HALF_EVEN
        rendered = format(Decimal(value.numerator) / Decimal(value.denominator), "f")
    return rendered.rstrip("0").rstrip(".") if "." in rendered else rendered


def bound_book(source):
    """Real reconstruction/identity/kernel, with retained SIMULATED metadata bytes."""
    metadata = b"SIMULATED retained metadata v1\n"
    payload = json.dumps(
        {
            "coin": "BTC",
            "time": 1,
            "levels": [[{"px": p, "sz": q} for p, q in source[side]] for side in ("bids", "asks")],
        },
        separators=(",", ":"),
    ).encode()
    envelope = RawPublicEnvelope(
        capture_run_id=UUID("00000000-0000-0000-0000-000000000001"),
        envelope_index=0,
        observed_at_ms=1,
        venue="hyperliquid",
        payload_sha256=hashlib.sha256(payload).hexdigest(),
        payload=payload,
    )
    mapping = MarketMappingEvidence(
        mapping_id="simulated-vector",
        mapping_version="fixture/v1",
        decision=MappingDecision.APPROVED,
        venue="hyperliquid",
        symbol="BTC",
        identity=InstrumentIdentity(
            base_asset="BTC",
            quote_asset="USD",
            product_kind="perp",
            settlement_asset="USD",
            payoff_kind="linear",
        ),
        evidence_sha256=hashlib.sha256(metadata).hexdigest(),
        evidence_reference="fixture/retained-metadata.txt",
        valid_from_ms=0,
        valid_until_ms=None,
        reviewed_contract_multiplier=Decimal("1"),
        displayed_size_unit="coin",
        quantity_step=Decimal("0.00000001"),
        price_tick=Decimal("0.1"),
        price_decimals=None,
        max_price_significant_digits=None,
        min_quantity=None,
        min_notional=Decimal("10"),
    )
    return bind_reconstructed_books(reconstruct_books((envelope,)), (mapping,))[0]


def check_sweep(vector):
    source, expected = vector["input"], vector["expected"]
    result = sweep_depth(
        bound_book(source), Side(source["side"]), ExactDecimal.parse(source["quantity_base"])
    )
    for key in ("notional_quote", "vwap", "worst_price"):
        assert getattr(result, key) == rational(expected[key])
    assert result.consumed_levels == expected["consumed_levels"]
    assert result.filled_quantity == Fraction(expected["filled_quantity"])
    assert result.filled_quantity == result.requested_quantity == Fraction(source["quantity_base"])
    best = Fraction(source["asks" if source["side"] == "BUY" else "bids"][0][0])
    impact = (result.vwap / best - 1) * 10000
    if source["side"] == "SELL":
        impact = -impact
    assert impact == rational(expected["price_impact_bps"])
    assert expected["snapshot_status"] == "SIMULATED"
    assert expected["chargeable_quote"] is False
    for key, rendered in expected["display"].items():
        assert rendered == display(rational(expected[key]))
    for example in expected["display_rounding_examples"]:
        assert display(rational(example["exact"])) == example["display"]


@pytest.mark.parametrize(
    "vector_id", ["buy-two-levels", "sell-two-levels", "sell-one-level", "sell-exact-depth"]
)
def test_exact_kernel_matches_hand_derived_literals(vector_id):
    check_sweep(next(v for v in records() if v["id"] == vector_id))


def dataset_reason(source):
    """F2 policy oracle only; F3 must reproduce these cases on retained artifacts."""
    if not source["upstream_available"]:
        return "SOURCE_UNAVAILABLE"
    if source["requested_instrument"] != "hyperliquid:BTC:perpetual":
        return "UNSUPPORTED_INSTRUMENT"
    if source["returned_instrument"] != "hyperliquid:BTC:perpetual":
        return "IDENTITY_MISMATCH"
    if source["age_ms"] > 5000:
        return "STALE_SOURCE"
    if source["age_ms"] < -1000:
        return "CLOCK_SKEW"
    if (
        source["metadata_age_ms"] > 86400000
        or not source["metadata_valid_from_ms"]
        <= source["metadata_now_ms"]
        <= source["metadata_valid_until_ms"]
        or source["quantity_unit"] != "coin"
        or source["multiplier"] != "1"
        or source["evidence_sha256"] != hashlib.sha256(source["evidence_text"].encode()).hexdigest()
    ):
        return "IDENTITY_UNVERIFIED"
    try:
        bids = [(Decimal(p), Decimal(q)) for p, q in source["bids"]]
        asks = [(Decimal(p), Decimal(q)) for p, q in source["asks"]]
        if not bids or not asks:
            return "INVALID_DATASET"
        if any(not p.is_finite() or not q.is_finite() or p <= 0 or q < 0 for p, q in bids + asks):
            return "INVALID_DATASET"
        if any(a[0] <= b[0] for a, b in zip(bids, bids[1:])):
            return "INVALID_DATASET"
        if any(a[0] >= b[0] for a, b in zip(asks, asks[1:])):
            return "INVALID_DATASET"
        if bids[0][0] >= asks[0][0]:
            return "CROSSED_BOOK"
        if Fraction(source["quantity_base"]) > sum(
            Fraction(q) for _, q in source["asks" if source["side"] == "BUY" else "bids"]
        ):
            return "DEPTH_INSUFFICIENT"
    except (ValueError, ArithmeticError):
        return "INVALID_DATASET"
    return "SIMULATED_SOURCE" if source["source_mode"] == "fixture" else None


def check_invalid_request(vector):
    c = support()
    expected = vector["expected"]
    try:
        body = strict_json(vector["input"]["request_json"])
    except ValueError:
        assert expected["code"] == "INVALID_INPUT"
    else:
        with pytest.raises(c.ContractError):
            c.canonical_body(body)
        code = (
            "UNSUPPORTED_INSTRUMENT"
            if isinstance(body, dict)
            and body.get("instrument_id", "hyperliquid:BTC:perpetual")
            != "hyperliquid:BTC:perpetual"
            else "INVALID_INPUT"
        )
        assert expected["code"] == code
    assert expected == {
        "http_status": 422,
        "code": expected["code"],
        "chargeable_quote": False,
        "settlement_calls": 0,
    }


def check_dataset(vector):
    c = support()
    try:
        source = strict_json(vector["input"]["dataset_json"])
    except ValueError:
        code = "INVALID_DATASET"
    else:
        c.validate({"$ref": "#/$defs/dataset_input"}, source, document="vectors.schema.json")
        code = dataset_reason(source)
        if code == "DEPTH_INSUFFICIENT":
            with pytest.raises(DepthRejected):
                sweep_depth(
                    bound_book(source),
                    Side(source["side"]),
                    ExactDecimal.parse(source["quantity_base"]),
                )
    assert vector["expected"] == {
        "http_status": 200 if code is None else 503 if code == "SOURCE_UNAVAILABLE" else 422,
        "code": code,
        "chargeable_quote": False,
        "settlement_calls": 0,
    }


def check_idempotency(vector):
    c = support()
    source, expected = vector["input"], vector["expected"]
    objects, statuses = {}, []
    for call in source["calls"]:
        key = (call["scope"], call["key"])
        body = strict_json(call["request_json"])
        # Conflict comparison precedes an unsupported changed instrument's fresh validation.
        # All previously unseen requests still pass the real canonical request oracle.
        if key in objects and body["instrument_id"] != "hyperliquid:BTC:perpetual":
            statuses.append(409)
            continue
        canonical = c.canonical_bytes(body)
        if key in objects and objects[key] != canonical:
            statuses.append(409)
        else:
            objects[key] = canonical
            statuses.append(202 if source["phase"] == "PREPARING" else 201)
    assert expected == {
        "http_statuses": statuses,
        "logical_requests": len(objects),
        "builds": len(objects),
        "quotes": 0 if source["phase"] == "PREPARING" else len(objects),
        "same_object": len(objects) == 1,
        "cross_scope_access": False,
        "settlement_calls": 0,
    }
    assert 1 <= source["parallelism"] <= len(source["calls"]) <= 20


def check_payment(vector):
    c = support()
    source, expected = vector["input"], vector["expected"]
    terms = source["terms"]
    atomic = Fraction(source["price_musd"]) * 10 ** source["decimals"]
    assert atomic.denominator == 1
    assert (
        str(atomic.numerator)
        == terms["amount_atomic"]
        == expected["amount_atomic"]
        == "10000000000000000"
    )
    claims = strict_json(source["candidate_claims_json"])
    c.validate({"$ref": "#/$defs/candidate_claims"}, claims, document="vectors.schema.json")
    assert (source["scenario"] == "reencoded_authorization") is claims[
        "same_authorization_different_encoding"]
    if claims["same_authorization_different_encoding"]:
        assert vector["future_assertions"] == ["sdk_identity_deduplicates_reencoding"]
        assert expected["code"] == "AUTHORIZATION_IDENTITY_UNVERIFIED"
        assert expected["http_status"] == 503
    invalid = (
        any(
            claims[a] != terms[b]
            for a, b in (
                ("network", "network"),
                ("asset", "asset"),
                ("amount_atomic", "amount_atomic"),
                ("pay_to", "pay_to"),
                ("payer", "expected_payer"),
            )
        )
        or not claims["signature_valid"]
        or claims["authorization_expired"]
    )
    code = (
        "PAYMENT_REJECTED"
        if invalid
        else "AUTHORIZATION_REUSED"
        if claims["authorization_reused"]
        else "AUTHORIZATION_IDENTITY_UNVERIFIED"
    )
    assert expected == {
        "http_status": 503 if code == "AUTHORIZATION_IDENTITY_UNVERIFIED" else 409,
        "code": code,
        "amount_atomic": "10000000000000000",
        "entitlement_count": 0,
        "paid_body": False,
        "settlement_calls": 0,
        "distinct_attempts": 0,
    }
    assert source["identity_binding_status"] == "UNRESOLVED_F5"


def deliverable(source):
    return (
        source["quote_state"] == "PAID"
        and source["attempt_state"] == "CONFIRMED"
        and source["finality_verified"]
        and not source["chain_inconsistency"]
    )


def check_access(vector):
    source, expected = vector["input"], vector["expected"]
    authorization = source["authorization"]
    if authorization == "missing":
        status, code, paid = 401, "UNAUTHORIZED", False
    elif authorization != "same_scope":
        status, code, paid = 404, "NOT_FOUND", False
    elif (
        source["quote_state"] == "MANUAL_REVIEW"
        or source["attempt_state"] == "MANUAL_REVIEW"
        or source["chain_inconsistency"]
    ):
        status, code, paid = 202, "MANUAL_REVIEW", False
    elif source["quote_state"] == "EXPIRED":
        status, code, paid = 410, "QUOTE_EXPIRED", False
    elif source["resource"] == "quote":
        status, code, paid = 200, None, False
    elif source["entitlement_present"] and deliverable(source):
        status, code, paid = 200, None, True
    elif source["quote_state"] in {"PAYMENT_PENDING", "PAYMENT_UNCERTAIN", "PAID"}:
        status, code, paid = 202, "PAYMENT_UNCERTAIN", False
    else:
        status, code, paid = 402, "PAYMENT_REQUIRED", False
    assert expected == {
        "http_status": status,
        "code": code,
        "paid_body": paid,
        "settlement_calls": 0,
    }


def utc_instant(timestamp):
    """Exact UTC seconds, retaining every schema-permitted fractional digit."""
    support().validate({"$ref": "primitives.schema.json#/$defs/timestamp"}, timestamp,
                       document="vectors.schema.json")
    whole, dot, fraction = timestamp[:-1].partition(".")
    instant = datetime.fromisoformat(whole)
    seconds = (instant.toordinal() * 86400 + instant.hour * 3600
               + instant.minute * 60 + instant.second)
    return Fraction(seconds) + (Fraction(Decimal("0." + fraction)) if dot else 0)


def check_recovery(vector):
    source, expected = vector["input"], vector["expected"]
    event = source["event"]
    states = {
        "verify_only": ("PAYMENT_PENDING", "VERIFIED", 202, False),
        "timeout_without_hash": ("PAYMENT_UNCERTAIN", "UNKNOWN", 202, False),
        "ambiguous_transfers": ("PAYMENT_UNCERTAIN", "UNKNOWN", 202, False),
        "crash_before_submit": ("READY", "REJECTED", 409, False),
        "crash_after_broadcast": ("PAYMENT_UNCERTAIN", "UNKNOWN", 202, False),
        "crash_after_chain_success": ("PAID", "CONFIRMED", 200, True),
        "lost_response": ("PAID", "CONFIRMED", 200, True),
        "expiry_before_submit": ("EXPIRED", "REJECTED", 410, False),
        "confirmation_after_expiry": ("PAID", "CONFIRMED", 200, True),
        "unknown_after_expiry": ("PAYMENT_UNCERTAIN", "UNKNOWN", 202, False),
        "repeat_paid_read": ("PAID", "CONFIRMED", 200, True),
        "chain_inconsistency": ("MANUAL_REVIEW", "MANUAL_REVIEW", 202, False),
        "retention_check": ("EXPIRED", "REJECTED", 410, False),
    }
    quote, attempt, status, paid = states[event]
    assert (
        expected["quote_state"],
        expected["attempt_state"],
        expected["http_status"],
        expected["paid_body"],
    ) == states[event]
    if paid:
        assert source["finality_verified"] and not source["chain_inconsistency"]
    if event == "crash_before_submit":
        assert source["authoritative_no_broadcast_proof"]
        assert utc_instant(source["now"]) < utc_instant(source["quote_expires_at"])
    if event in {"expiry_before_submit", "confirmation_after_expiry", "unknown_after_expiry"}:
        assert utc_instant(source["now"]) >= utc_instant(source["quote_expires_at"])
    if event == "ambiguous_transfers":
        assert source["matching_transfer_count"] > 1 and not source["finality_verified"]
    if event == "timeout_without_hash":
        assert source["tx_hash"] is None
    assert expected["additional_settlement_calls"] == 0
    assert expected["original_digest_preserved"] is True
    assert expected["retain_artifacts"] is (event != "retention_check")
    now = utc_instant(source["now"])
    minimum = utc_instant(source["ledger_created_at"]) + source["ledger_days"] * 86400
    validity = source["authorization_valid_until"]
    must_retain = (
        now < minimum
        or validity is None
        or now < utc_instant(validity)
        or not source["replay_impossible_proven"]
        or attempt in {"SUBMITTING", "UNKNOWN", "MANUAL_REVIEW"}
    )
    if must_retain:
        assert all(
            expected[key]
            for key in ("retain_ledger", "retain_scope_binding", "retain_dedup_association")
        )


def check_artifact(vector):
    source, expected = vector["input"], vector["expected"]
    defect = source["defect"]
    assert expected == {
        "http_status": 422 if defect == "fictitious_provenance" else 503,
        "code": {
            "missing_bytes": "STORAGE_UNAVAILABLE",
            "corrupt_bytes": "ARTIFACT_INTEGRITY_FAILURE",
            "fictitious_provenance": "IDENTITY_UNVERIFIED",
        }[defect],
        "chargeable_quote": False,
        "paid_body": False,
        "additional_settlement_calls": 0,
        "recovery_required": defect == "corrupt_bytes",
    }
    if defect == "missing_bytes":
        assert source["readback_digest"] is None
    if defect == "corrupt_bytes":
        assert source["readback_digest"] != source["expected_digest"]


CHECKS = {
    "sweep": check_sweep,
    "invalid_request": check_invalid_request,
    "dataset_rejection": check_dataset,
    "idempotency": check_idempotency,
    "payment": check_payment,
    "access": check_access,
    "recovery": check_recovery,
    "artifact": check_artifact,
}


@pytest.mark.parametrize("kind", list(CHECKS))
def test_each_family_semantics(kind):
    for vector in records():
        if vector["kind"] == kind:
            CHECKS[kind](vector)


def test_required_adversarial_cases_cannot_disappear():
    by_id = {vector["id"]: vector for vector in records()}
    required = {
        "same-scope-expired-quote",
        "valid-fixture-no-sale",
        "valid-live-policy-boundary",
        "buy-two-levels",
        "sell-two-levels",
        "sell-one-level",
        "sell-exact-depth",
        "buy-insufficient-depth",
        "sell-insufficient-depth",
        "quantity-zero",
        "quantity-negative",
        "quantity-json-number",
        "quantity-json-nan",
        "quantity-json-infinity",
        "quantity-nan-string",
        "quantity-infinity-string",
        "quantity-exponent",
        "quantity-whitespace",
        "quantity-empty",
        "quantity-unicode-digits",
        "quantity-overprecision",
        "quantity-overflow",
        "quantity-bool",
        "quantity-null",
        "malformed-json",
        "duplicate-body-key",
        "body-array",
        "body-null",
        "source-age-boundary",
        "source-age-outside",
        "future-boundary",
        "future-outside",
        "metadata-age-boundary",
        "metadata-age-outside",
        "validity-start-inside",
        "validity-start-equal",
        "validity-start-outside",
        "validity-end-inside",
        "validity-end-equal",
        "validity-end-outside",
        "crossed-book",
        "locked-book",
        "unsorted-bids",
        "unsorted-asks",
        "duplicate-bids",
        "duplicate-asks",
        "negative-size",
        "zero-price",
        "nonfinite-price-string",
        "nonfinite-size-string",
        "nonfinite-price-json",
        "wrong-requested-instrument",
        "wrong-returned-instrument",
        "wrong-unit",
        "wrong-multiplier",
        "missing-source-hash",
        "fictitious-source-hash",
        "live-upstream-outage",
        "canonical-retry",
        "twenty-parallel-retries",
        "preparing-retries",
        "isolated-scope-same-key",
        "changed-side",
        "changed-quantity_base",
        "changed-expected_payer",
        "changed-instrument_id",
        "musd-exact-atomic-units",
        "wrong-mainnet",
        "wrong-network",
        "wrong-token",
        "amount-minus-one",
        "amount-plus-one",
        "six-decimal-amount",
        "numeric-amount",
        "wrong-receiver",
        "payer-changed-after-quote",
        "wrong-signature",
        "expired-authorization",
        "reused-authorization",
        "reencoded-authorization",
        "verify-without-confirmation",
        "timeout-without-hash",
        "ambiguous-identical-transfers",
        "crash-after-durable-attempt-before-submit",
        "crash-after-broadcast",
        "crash-after-chain-before-commit",
        "lost-http-response-after-commit",
        "expired-before-submitting",
        "submitted-before-confirmed-after-expiry",
        "unknown-retained-after-expiry",
        "historical-paid-repeat-read",
        "review-withholds-repeat-read",
        "authorization-outlives-retention",
        "authorization-validity-unresolved",
        "post-validity-replay-not-proven",
        "artifact-missing-before-payment",
        "paid-artifact-corruption",
        "fictitious-report-provenance",
    }
    required.update(
        "missing-" + key for key in ("instrument_id", "side", "quantity_base", "expected_payer")
    )
    required.update(
        "forbidden-" + key
        for key in (
            "source",
            "source_mode",
            "url",
            "mapping",
            "filepath",
            "chain",
            "chain_id",
            "price",
            "price_musd",
            "payTo",
            "pay_to",
            "digest",
            "report_sha256",
            "scope",
        )
    )
    required.update(
        {
            "quantity-zero-scale",
            "quantity-negative-integer",
            "quantity-trailing-space",
            "quantity-arabic-digits",
            "quantity-trailing-newline",
            "invalid-side-hold",
            "invalid-instrument-venue-case",
            "invalid-instrument-product",
            "invalid-payer-19-bytes",
            "invalid-payer-nonhex",
            "invalid-payer-prefix",
            "forbidden-client_source",
        }
    )
    for resource in ("quote", "report", "evidence"):
        for authorization in ("missing", "other_scope", "guessed_id", "public_tx_hash"):
            required.add(
                "sibling-scope-report"
                if (authorization, resource) == ("other_scope", "report")
                else f"{authorization}-{resource}"
            )
    for resource in ("report", "evidence"):
        required.update(
            f"{case}-{resource}"
            for case in (
                "unpaid",
                "paid",
                "quote-review",
                "attempt-review",
                "finality-unverified",
                "chain-conflict",
            )
        )
    assert required <= by_id.keys()
    for key, amount in (
        ("amount-minus-one", "9999999999999999"),
        ("amount-plus-one", "10000000000000001"),
        ("six-decimal-amount", "10000"),
    ):
        assert strict_json(by_id[key]["input"]["candidate_claims_json"])["amount_atomic"] == amount
    assert len(by_id["twenty-parallel-retries"]["input"]["calls"]) == 20


def test_embedded_json_rejects_unbounded_claims_and_dataset_keys():
    c = support()
    for kind, field, definition in (
        ("payment", "candidate_claims_json", "candidate_claims"),
        ("dataset_rejection", "dataset_json", "dataset_input"),
    ):
        vector = next(v for v in records() if v["kind"] == kind)
        value = strict_json(vector["input"][field])
        value["unreviewed_override"] = "forbidden"
        with pytest.raises(c.ContractError):
            c.validate({"$ref": f"#/$defs/{definition}"}, value, document="vectors.schema.json")


def test_every_payment_terms_projection_agrees_with_f1_lock():
    lock = strict_json((ROOT.parents[2] / "docs/compatibility/mezo-evidence-v1.json").read_text())
    for vector in records():
        if vector["kind"] != "payment":
            continue
        terms = vector["input"]["terms"]
        assert terms["network"] == lock["mezo"]["network"]
        assert terms["chain_id"] == lock["mezo"]["chain_id"]
        assert terms["decimals"] == lock["mezo"]["musd_decimals"]
        assert bytes.fromhex(terms["asset"][2:]) == bytes.fromhex(lock["mezo"]["musd_address"][2:])
        assert terms["pay_to"] != terms["expected_payer"]
        assert int(terms["pay_to"][2:], 16) != 0


def test_vector_states_and_reasons_are_declared_by_their_contracts():
    c = support()
    machines = {
        machine["name"]: set(machine["states"]) for machine in c.load("states.json")["machines"]
    }
    reasons = set(c.load("reasons.schema.json")["enum"])
    for vector in records():
        for fields in (vector["input"], vector["expected"]):
            if "quote_state" in fields:
                assert fields["quote_state"] in machines["quote"]
            if "attempt_state" in fields:
                assert fields["attempt_state"] in machines["payment_attempt"]
            if fields.get("code") is not None:
                assert fields["code"] in reasons


def test_recovery_vectors_follow_actual_graph_edges_without_new_submission():
    c = support()
    machines = {machine["name"]: machine for machine in c.load("states.json")["machines"]}
    for vector in records():
        if vector["kind"] != "recovery":
            continue
        source, expected = vector["input"], vector["expected"]
        for field, name in (("quote_state", "quote"), ("attempt_state", "payment_attempt")):
            if source[field] == expected[field]:
                continue
            transitions = [
                transition
                for transition in machines[name]["transitions"]
                if (transition["from"], transition["to"]) == (source[field], expected[field])
            ]
            assert transitions, vector["id"]
            assert all(transition["to"] != "SUBMITTING" for transition in transitions)
        if source["attempt_state"] in {"UNKNOWN", "MANUAL_REVIEW"}:
            assert expected["attempt_state"] in {"UNKNOWN", "MANUAL_REVIEW", "CONFIRMED"}
            assert expected["retain_artifacts"]


def test_access_vectors_evaluate_joint_graph_delivery_guards():
    c = support()
    delivery = next(
        machine for machine in c.load("states.json")["machines"] if machine["name"] == "delivery"
    )
    guards = set(
        next(
            transition
            for transition in delivery["transitions"]
            if transition["event"] == "read_retried"
        )["guards"]
    )
    for vector in records():
        if vector["kind"] != "access" or vector["input"]["resource"] == "quote":
            continue
        source = vector["input"]
        facts = {"storage_integrity_verified"}
        if source["entitlement_present"]:
            facts.add("entitlement_matches_digest")
        if source["quote_state"] == "PAID":
            facts.add("quote_is_paid")
        if source["attempt_state"] == "CONFIRMED":
            facts.add("attempt_is_confirmed")
        if source["finality_verified"]:
            facts.add("current_finality_verified")
        if not source["chain_inconsistency"]:
            facts.add("no_chain_inconsistency")
        assert vector["expected"]["paid_body"] is (
            source["authorization"] == "same_scope" and guards <= facts
        )


def required_assertions(vector):
    kind, source = vector["kind"], vector["input"]
    if kind == "sweep":
        return {
            "report_builder_matches_exact_sweep",
            "fixture_is_not_live_sale",
            "canonical_report_bytes_reproduce",
        }
    if kind == "invalid_request":
        return {"invalid_request_never_creates_quote"}
    if kind == "dataset_rejection":
        code = vector["expected"]["code"]
        return {
            {
                "DEPTH_INSUFFICIENT": "insufficient_depth_never_sells_partial",
                "SOURCE_UNAVAILABLE": "live_outage_never_uses_fixture",
            }.get(code, "dataset_policy_rejects_invalid_evidence")
        }
    if kind == "idempotency":
        if source["parallelism"] == 20:
            return {"twenty_concurrent_retries_one_quote"}
        if not vector["expected"]["same_object"]:
            return {"idempotency_scope_isolation"}
        if 409 in vector["expected"]["http_statuses"]:
            return {"idempotency_body_conflict"}
        return {"canonical_retries_one_quote"}
    if kind == "payment":
        return {
            {
                "exact_units": "atomic_amount_matches_all_layers",
                "reencoded_authorization": "sdk_identity_deduplicates_reencoding",
            }.get(source["scenario"], "invalid_authorization_never_entitles")
        }
    if kind == "access":
        return {
            "capability_required_for_access"
            if source["authorization"] == "missing"
            else "sibling_scope_never_reads_body"
            if source["authorization"] != "same_scope"
            else "unpaid_read_returns_sdk_402"
            if vector["expected"]["http_status"] == 402
            else "capability_required_for_access"
        }
    if kind == "artifact":
        return {
            {
                "missing_bytes": "missing_artifact_prevents_payment",
                "corrupt_bytes": "paid_artifact_loss_requires_recovery_without_charge",
                "fictitious_provenance": "report_provenance_required",
            }[source["defect"]]
        }
    event = source["event"]
    return {
        "verify_only": {"verify_alone_never_delivers"},
        "timeout_without_hash": {"unknown_never_resubmits"},
        "ambiguous_transfers": {"receipt_log_bound_to_authorization", "unknown_never_resubmits"},
        "crash_before_submit": {"crash_recovery_never_double_charges"},
        "crash_after_broadcast": {"crash_recovery_never_double_charges", "unknown_never_resubmits"},
        "crash_after_chain_success": {
            "crash_recovery_never_double_charges",
            "receipt_log_bound_to_authorization",
        },
        "lost_response": {"lost_response_reuses_entitlement"},
        "expiry_before_submit": {"expiry_blocks_new_payment_only"},
        "confirmation_after_expiry": {"late_confirmation_delivers_original"},
        "unknown_after_expiry": {"unknown_never_resubmits", "expiry_blocks_new_payment_only"},
        "repeat_paid_read": {
            "paid_repeat_read_never_settles",
            "current_confirmation_required_for_delivery",
        },
        "chain_inconsistency": {
            "current_confirmation_required_for_delivery",
            "unknown_never_resubmits",
        },
        "retention_check": {
            "retention_covers_authorization_validity",
            "deletion_cannot_enable_replay",
        },
    }[event]


def check_document(document):
    c = support()
    c.validate(c.load("vectors.schema.json"), document, document="vectors.schema.json")
    ids, covered = set(), {owner: set() for owner in ASSERTIONS}
    for vector in document["vectors"]:
        assert vector["id"] not in ids
        ids.add(vector["id"])
        assert required_assertions(vector) <= set(vector["future_assertions"])
        covered[vector["owner"]].update(vector["future_assertions"])
        CHECKS[vector["kind"]](vector)
    assert covered == ASSERTIONS


def test_all_vector_shapes_semantics_and_assertion_registry():
    check_document(vector_document())
    c = support()
    for owner, assertions in ASSERTIONS.items():
        assert (
            set(c.load("vectors.schema.json")["$defs"][f"assertions_{owner}"]["enum"]) == assertions
        )


@pytest.mark.parametrize(
    "mutation",
    [
        "side",
        "fraction",
        "assertion",
        "amount",
        "runtime",
        "owner",
        "duplicate_id",
        "duplicate_assertion",
        "unknown_assertion",
        "extra_input",
        "extra_expected",
        "version",
    ],
)
def test_mutation_self_checks_reject_weakened_vectors(mutation):
    document = copy.deepcopy(vector_document())
    sweep = next(v for v in document["vectors"] if v["id"] == "sell-two-levels")
    if mutation == "side":
        sweep["input"]["side"] = "BUY"
    elif mutation == "fraction":
        sweep["expected"]["vwap"]["numerator"] = "299901"
    elif mutation == "assertion":
        sweep["future_assertions"].remove("canonical_report_bytes_reproduce")
    elif mutation == "amount":
        next(v for v in document["vectors"] if v["kind"] == "payment")["expected"][
            "amount_atomic"
        ] = "10000"
    elif mutation == "runtime":
        sweep["runtime_status"] = "PASS"
    elif mutation == "owner":
        sweep["owner"] = "F5"
    elif mutation == "duplicate_id":
        document["vectors"].append(copy.deepcopy(sweep))
    elif mutation == "duplicate_assertion":
        sweep["future_assertions"].append(sweep["future_assertions"][0])
    elif mutation == "unknown_assertion":
        sweep["future_assertions"].append("made_up_runtime_proof")
    elif mutation == "extra_input":
        sweep["input"]["arbitrary"] = {}
    elif mutation == "extra_expected":
        sweep["expected"]["arbitrary"] = {}
    else:
        document["schema"] = "mee-evidence-vectors/v2"
    with pytest.raises((AssertionError, ValueError)):
        check_document(document)
