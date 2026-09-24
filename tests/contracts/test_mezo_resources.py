"""Contract examples for immutable reports and safe public resources."""

from copy import deepcopy

import mezo_evidence_support as c
import pytest

ID = "123e4567-e89b-42d3-a456-426614174000"
OTHER_ID = "123e4567-e89b-42d3-a456-426614174001"
TIME = "2026-09-24T12:00:00Z"
EXPIRES = "2026-09-24T12:02:00Z"
HASH = "a" * 64
TX_HASH = "0x" + "b" * 64
ADDRESS = "0x" + "a" * 40  # Synthetic fixture bytes, never merchant configuration.
PAYER = "0x" + "b" * 40  # Synthetic fixture bytes, never merchant configuration.
ASSET = "0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503"

PREVIEW = {
    "instrument_id": "hyperliquid:BTC:perpetual",
    "side": "BUY",
    "quantity_base": "0.15",
    "snapshot_at": TIME,
    "snapshot_status": "VALID_FOR_SNAPSHOT_CALCULATION",
    "limitations": ["Calculation over the available snapshot depth."],
    "price_musd": "0.01",
    "expires_at": EXPIRES,
}

REPORT = {
    "schema": "mee-evidence-report/v1",
    "report_id": ID,
    "identity": {
        "venue": "hyperliquid",
        "instrument_id": "hyperliquid:BTC:perpetual",
        "product_kind": "perpetual",
        "payoff_kind": "linear",
        "base_asset": "BTC",
        "quote_asset": "USD",
        "settlement_asset": "USDC",
        "quantity_unit": "BTC",
        "displayed_size_unit": "coin",
        "contract_multiplier": "1",
        "mapping_version": "reviewed/v1",
        "evidence": [{"reference": "https://example.invalid/metadata", "sha256": HASH}],
    },
    "request": {"side": "BUY", "quantity_base": "0.15"},
    "source": {
        "source_mode": "live-public",
        "started_at": TIME,
        "observed_at": TIME,
        "source_at": TIME,
        "created_at": TIME,
        "build_age_ms": 0,
        "payload_sha256": HASH,
        "package_sha256": HASH,
        "available_bid_levels": 2,
        "available_ask_levels": 2,
    },
    "calculation": {
        "requested_quantity": "0.15",
        "filled_quantity": "0.15",
        "notional_quote": {"numerator": "15005", "denominator": "1"},
        "vwap": {"numerator": "300100", "denominator": "3"},
        "worst_price": {"numerator": "100100", "denominator": "1"},
        "price_impact_bps": {"numerator": "10", "denominator": "3"},
        "consumed_levels": 2,
        "display": {
            "notional_quote": "15005",
            "vwap": "100033.3333333333333333333333",
            "worst_price": "100100",
            "price_impact_bps": "3.333333333333333333333333333",
        },
        "display_precision": 28,
        "display_rounding": "ROUND_HALF_EVEN",
    },
    "quality": {
        "snapshot_status": "VALID_FOR_SNAPSHOT_CALCULATION",
        "reason_codes": [],
        "checks": [{"name": "book", "result": "PASS"}],
        "limitations": ["Hypothetical snapshot calculation only."],
    },
    "reproducibility": {
        "engine_commit": "c" * 40,
        "package_versions": [{"name": "mee-readonly-analyzer", "version": "0.1.0"}],
        "lockfile_digests": [{"path": "locks/python.lock", "sha256": HASH}],
        "calculation_version": "snapshot-sweep/v1",
        "policy_version": "snapshot-policy/v1",
        "serialization_version": "canonical-json/v1",
        "input_files": [{"path": "capture/raw.json", "sha256": HASH}],
    },
    "boundaries": {
        "execution_authority": "NONE",
        "fees_calculated": False,
        "funding_calculated": False,
        "net_pnl_calculated": False,
        "execution_promise": False,
        "calculation_label": "hypothetical snapshot sweep",
    },
}

TERMS = {
    "version": "mee-evidence-terms/v1",
    "network": "eip155:31611",
    "chain_id": 31611,
    "asset": ASSET,
    "decimals": 18,
    "amount_atomic": "10000000000000000",
    "price_musd": "0.01",
    "pay_to": ADDRESS,
    "expected_payer": PAYER,
    "expires_at": EXPIRES,
}
RECEIPT = {
    "schema": "mee-evidence-receipt/v1",
    "quote_id": OTHER_ID,
    "report_id": ID,
    "payment_attempt_id": ID,
    "report_sha256": HASH,
    "network": "eip155:31611",
    "chain_id": 31611,
    "asset": ASSET,
    "amount_atomic": "10000000000000000",
    "payer": PAYER,
    "pay_to": ADDRESS,
    "tx_hash": TX_HASH,
    "block_hash": TX_HASH,
    "block_number": 1,
    "log_index": 0,
    "confirmed_at": TIME,
    "finality_policy_version": "verified/v1",
}
EXAMPLES = {
    "preview": PREVIEW,
    "terms": TERMS,
    "quote": {
        "schema": "mee-evidence-quote/v1",
        "request_id": ID,
        "report_request_id": ID,
        "quote_id": OTHER_ID,
        "report_id": ID,
        "report_sha256": HASH,
        "bundle_sha256": HASH,
        "state": "READY",
        "preview": PREVIEW,
        "terms": TERMS,
        "retention": {
            "paid_days": 7,
            "unpaid_grace_seconds": 900,
            "ledger_days": 30,
            "authorization_validity_floor": True,
            "deletion_must_not_enable_replay": True,
        },
    },
    "request_status": {
        "schema": "mee-evidence-request-status/v1",
        "request_id": ID,
        "report_request_id": ID,
        "status_location": f"/v1/report-requests/{ID}",
        "state": "PREPARING",
    },
    "receipt": RECEIPT,
    "paid_report": {
        "schema": "mee-evidence-delivery/v1",
        "request_id": ID,
        "report": REPORT,
        "receipt": RECEIPT,
    },
    "capabilities": {
        "schema": "mee-evidence-capabilities/v1",
        "request_id": ID,
        "instrument_id": "hyperliquid:BTC:perpetual",
        "instrument_label": "Hyperliquid BTC linear perpetual",
        "network": "eip155:31611",
        "asset": ASSET,
        "decimals": 18,
        "price_musd": "0.01",
        "amount_atomic": "10000000000000000",
        "source_mode": "live-public",
        "limitations": ["Testnet payment only."],
        "payment_ready": False,
        "blockers": ["PAY_TO_MISSING"],
    },
    "health": {"schema": "mee-evidence-health/v1", "request_id": ID, "status": "alive"},
    "readiness": {
        "schema": "mee-evidence-readiness/v1",
        "request_id": ID,
        "ready": False,
        "storage_ready": True,
        "configuration_ready": False,
        "integration_ready": True,
        "payment_ready": False,
        "blockers": ["PAY_TO_MISSING"],
    },
}


def validate_resource(name, value):
    c.validate({"$ref": f"resources.schema.json#/$defs/{name}"}, value,
               document="resources.schema.json")


def test_preview_rejects_paid_calculation():
    try:
        validate_resource("preview", PREVIEW)
    except c.ContractError as error:
        pytest.fail(f"valid preview rejected: {error}")
    for key in ("vwap", "notional_quote", "report", "input_files", "path", "bundle"):
        with pytest.raises(c.ContractError):
            validate_resource("preview", {**PREVIEW, key: "private"})


@pytest.mark.parametrize("name,value", EXAMPLES.items())
def test_resource_examples_are_closed_and_required(name, value):
    validate_resource(name, value)
    for key in value:
        missing = {field: item for field, item in value.items() if field != key}
        with pytest.raises(c.ContractError):
            validate_resource(name, missing)
    with pytest.raises(c.ContractError):
        validate_resource(name, {**value, "internal_path": "/private"})


def test_report_is_closed_and_does_not_hash_itself():
    c.validate(c.load("report.schema.json"), REPORT, document="report.schema.json")
    for key in REPORT:
        with pytest.raises(c.ContractError):
            c.validate(c.load("report.schema.json"),
                       {field: item for field, item in REPORT.items() if field != key},
                       document="report.schema.json")
    for key in ("report_sha256", "payer", "capability", "payment_signature"):
        with pytest.raises(c.ContractError):
            c.validate(c.load("report.schema.json"), {**REPORT, key: "private"},
                       document="report.schema.json")


def test_evidence_reference_requires_https_even_when_format_is_annotation():
    reference = c.load("report.schema.json")["$defs"]["evidence"]["properties"]["reference"]
    without_format = {key: value for key, value in reference.items() if key != "format"}
    c.validate(without_format, "https://example.invalid/metadata",
               document="report.schema.json")
    with pytest.raises(c.ContractError):
        c.validate(without_format, "http://example.invalid/metadata",
                   document="report.schema.json")


@pytest.mark.parametrize("path", ["/absolute", "../escape", "a/../b", "a/./b",
                                   "a//b", "a\\b", "C:foo", ".", "..", "a/é"])
def test_report_rejects_unsafe_artifact_paths(path):
    changed = deepcopy(REPORT)
    changed["reproducibility"]["input_files"][0]["path"] = path
    with pytest.raises(c.ContractError):
        c.validate(c.load("report.schema.json"), changed, document="report.schema.json")


def test_stage_a_verdict_remains_independent_and_exact():
    changed = deepcopy(REPORT)
    changed["quality"]["stage_a"] = {
        "schema": "mee-stage-a-decision/v1",
        "package_schema": "mee-readonly-frozen-package/v1",
        "capture_run_id": None,
        "decision": "INSUFFICIENT_EVIDENCE",
        "reasons": ["INSUFFICIENT_ACQUISITION_WINDOW"],
    }
    c.validate(c.load("report.schema.json"), changed, document="report.schema.json")
    changed["quality"]["stage_a"]["decision"] = "GO"
    with pytest.raises(c.ContractError):
        c.validate(c.load("report.schema.json"), changed, document="report.schema.json")


def test_simulated_report_has_valid_shape_without_implying_sale_eligibility():
    changed = deepcopy(REPORT)
    changed["source"]["source_mode"] = "fixture"
    changed["quality"]["snapshot_status"] = "SIMULATED"
    changed["quality"]["reason_codes"] = ["SIMULATED_SOURCE"]
    c.validate(c.load("report.schema.json"), changed, document="report.schema.json")


@pytest.mark.parametrize("status", ["REJECTED", "SIMULATED"])
def test_final_review_chargeable_quote_rejects_unchargeable_preview(status):
    changed = deepcopy(EXAMPLES["quote"])
    changed["preview"]["snapshot_status"] = status
    with pytest.raises(c.ContractError):
        validate_resource("quote", changed)


def test_final_review_payment_ready_forbids_every_blocker():
    for resource in ("capabilities", "readiness"):
        changed = deepcopy(EXAMPLES[resource])
        changed["payment_ready"] = True
        changed["blockers"] = []
        validate_resource(resource, changed)
        for reason in c.load("reasons.schema.json")["enum"]:
            changed["blockers"] = [reason]
            with pytest.raises(c.ContractError):
                validate_resource(resource, changed)


@pytest.mark.parametrize("gate", ["storage_ready", "configuration_ready", "integration_ready",
                                  "payment_ready"])
def test_final_review_overall_readiness_requires_every_gate(gate):
    changed = deepcopy(EXAMPLES["readiness"])
    changed.update(ready=True, storage_ready=True, configuration_ready=True,
                   integration_ready=True, payment_ready=True, blockers=[])
    validate_resource("readiness", changed)
    changed[gate] = False
    with pytest.raises(c.ContractError):
        validate_resource("readiness", changed)


@pytest.mark.parametrize("section,key,value", [
    ("identity", "evidence", []),
    ("source", "build_age_ms", 5001),
    ("source", "available_ask_levels", 21),
    ("calculation", "vwap", 100033.3),
    ("calculation", "display_precision", 27),
    ("quality", "snapshot_status", "GO"),
    ("boundaries", "execution_authority", "TRADE"),
])
def test_report_rejects_unsupported_identity_arithmetic_or_authority(section, key, value):
    changed = deepcopy(REPORT)
    changed[section][key] = value
    with pytest.raises(c.ContractError):
        c.validate(c.load("report.schema.json"), changed, document="report.schema.json")


@pytest.mark.parametrize("section,field", [
    ("identity", "internal_mapping_path"),
    ("source", "authorization_signature"),
    ("calculation", "executed_fill"),
    ("quality", "chargeable"),
    ("reproducibility", "private_key"),
    ("boundaries", "trading_permission"),
])
def test_report_nested_objects_are_closed(section, field):
    changed = deepcopy(REPORT)
    changed[section][field] = "private"
    with pytest.raises(c.ContractError):
        c.validate(c.load("report.schema.json"), changed, document="report.schema.json")


@pytest.mark.parametrize("section,field", [
    ("identity", "evidence"),
    ("quality", "checks"),
    ("reproducibility", "package_versions"),
    ("reproducibility", "lockfile_digests"),
    ("reproducibility", "input_files"),
])
def test_report_nested_array_records_reject_extra_fields(section, field):
    changed = deepcopy(REPORT)
    changed[section][field][0]["internal_path"] = "/private"
    with pytest.raises(c.ContractError):
        c.validate(c.load("report.schema.json"), changed, document="report.schema.json")


@pytest.mark.parametrize("state,reason", [("PREPARING", None), ("READY", None),
                                          ("REJECTED", "STALE_SOURCE"),
                                          ("BUILD_FAILED", "SOURCE_UNAVAILABLE")])
def test_request_status_variants_keep_unready_quote_private(state, reason):
    status = {**EXAMPLES["request_status"], "state": state}
    if state == "READY":
        status["quote_id"] = OTHER_ID
    if reason:
        status["reason"] = reason
    validate_resource("request_status", status)
    for key in ("quote_id", "reason"):
        mutated = dict(status)
        if key in mutated:
            del mutated[key]
        else:
            mutated[key] = OTHER_ID if key == "quote_id" else "STALE_SOURCE"
        with pytest.raises(c.ContractError):
            validate_resource("request_status", mutated)


@pytest.mark.parametrize("state,reason", [("REJECTED", "SOURCE_UNAVAILABLE"),
                                          ("BUILD_FAILED", "STALE_SOURCE")])
def test_request_status_rejects_reason_from_other_branch(state, reason):
    status = {**EXAMPLES["request_status"], "state": state, "reason": reason}
    with pytest.raises(c.ContractError):
        validate_resource("request_status", status)


def test_terms_reject_zero_recipient_and_wrong_atomic_price():
    for change in ({"pay_to": "0x" + "0" * 40},
                   {"expected_payer": "0x" + "0" * 40},
                   {"amount_atomic": "1000000000000000"},
                   {"network": "eip155:31612"}):
        with pytest.raises(c.ContractError):
            validate_resource("terms", {**TERMS, **change})


def test_public_resources_reject_credentials_and_internal_artifacts():
    for name in ("quote", "request_status", "receipt", "capabilities", "readiness"):
        for field in ("access_scope_hash", "capability", "authorization_signature",
                      "internal_path", "raw_proof"):
            with pytest.raises(c.ContractError):
                validate_resource(name, {**EXAMPLES[name], field: "private"})
