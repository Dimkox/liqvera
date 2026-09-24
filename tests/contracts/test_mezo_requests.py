"""Liqvera F2 request normalization and safe public error contracts."""

from __future__ import annotations

import mezo_evidence_support as c
import pytest

INSTRUMENT = "hyperliquid:BTC:perpetual"
PAYER = "0x" + "ab" * 20
REQUEST = {
    "instrument_id": INSTRUMENT,
    "side": "BUY",
    "quantity_base": "0.15",
    "expected_payer": PAYER,
}

REASONS_BY_STATUS = {
    422: (
        "INVALID_INPUT", "INVALID_DATASET", "STALE_SOURCE", "CLOCK_SKEW",
        "IDENTITY_UNVERIFIED", "IDENTITY_MISMATCH", "CROSSED_BOOK",
        "DEPTH_INSUFFICIENT", "UNSUPPORTED_INSTRUMENT", "SIMULATED_SOURCE",
    ),
    503: (
        "SOURCE_UNAVAILABLE", "STORAGE_UNAVAILABLE", "PAYMENT_SERVICE_UNAVAILABLE",
        "PAYMENT_NOT_READY", "PAY_TO_MISSING", "FINALITY_RULE_UNVERIFIED",
        "AUTHORIZATION_IDENTITY_UNVERIFIED", "ARTIFACT_INTEGRITY_FAILURE",
    ),
    401: ("UNAUTHORIZED",),
    404: ("NOT_FOUND",),
    409: (
        "IDEMPOTENCY_CONFLICT", "INVALID_STATE", "PAYMENT_REJECTED",
        "AUTHORIZATION_REUSED",
    ),
    410: ("QUOTE_EXPIRED", "RETENTION_EXPIRED"),
    429: ("RATE_LIMITED",),
    402: ("PAYMENT_REQUIRED",),
    202: ("PAYMENT_UNCERTAIN", "MANUAL_REVIEW"),
}


def test_same_body_has_one_canonical_representation() -> None:
    raw = {
        **REQUEST,
        "quantity_base": "0.15000000",
        "expected_payer": "0x" + "AB" * 20,
    }
    try:
        actual = c.canonical_body(raw)
    except c.ContractError as error:
        pytest.fail(f"valid request rejected: {error}")
    assert actual == REQUEST
    assert c.canonical_bytes(raw) == c.canonical_bytes(REQUEST)
    assert c.canonical_bytes(raw) == (
        b'{"expected_payer":"0xabababababababababababababababababababab",'
        b'"instrument_id":"hyperliquid:BTC:perpetual",'
        b'"quantity_base":"0.15","side":"BUY"}'
    )


@pytest.mark.parametrize("quantity", ["+0.15", "00.15000000"])
def test_accepted_lexical_variants_normalize_without_changing_value(quantity: str) -> None:
    assert c.canonical_body({**REQUEST, "quantity_base": quantity}) == REQUEST


@pytest.mark.parametrize("quantity", ["0.00000001", "92233720368.54775807"])
def test_exact_positive_quantity_boundaries_are_accepted(quantity: str) -> None:
    assert c.canonical_body({**REQUEST, "quantity_base": quantity})["quantity_base"] == quantity


def test_sell_is_an_accepted_calculation_side() -> None:
    assert c.canonical_body({**REQUEST, "side": "SELL"})["side"] == "SELL"


@pytest.mark.parametrize(
    "quantity",
    [
        "0", "0.00000000", "-0.15", "-1", 0.15, float("nan"),
        "NaN", "Infinity", "1e-2", " 0.15", "0.15 ", "", "٠.15",
        "0.150000000", "92233720368.54775808", True, None,
    ],
)
def test_invalid_quantities_never_canonicalize(quantity: object) -> None:
    with pytest.raises(c.ContractError):
        c.canonical_body({**REQUEST, "quantity_base": quantity})


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("instrument_id", "Hyperliquid:BTC:perpetual"),
        ("instrument_id", "hyperliquid:BTC:perp"),
        ("side", "buy"),
        ("side", "HOLD"),
        ("expected_payer", "0x" + "00" * 20),
        ("expected_payer", "0x" + "ab" * 19),
        ("expected_payer", "0x" + "gg" * 20),
        ("expected_payer", "0X" + "ab" * 20),
    ],
)
def test_invalid_instrument_side_or_payer_is_rejected(field: str, value: str) -> None:
    with pytest.raises(c.ContractError):
        c.canonical_body({**REQUEST, field: value})


@pytest.mark.parametrize(
    "field",
    ["client_source", "source", "url", "mapping", "filepath", "chain", "price", "payTo", "digest"],
)
def test_client_cannot_control_server_evidence_or_payment_terms(field: str) -> None:
    with pytest.raises(c.ContractError):
        c.canonical_body({**REQUEST, field: "client-supplied"})


@pytest.mark.parametrize("field", tuple(REQUEST))
def test_request_requires_all_four_fields(field: str) -> None:
    with pytest.raises(c.ContractError):
        c.canonical_body({key: value for key, value in REQUEST.items() if key != field})


def test_request_schema_accepts_only_the_four_field_body() -> None:
    c.validate(c.load("quote-request.schema.json"), REQUEST, document="quote-request.schema.json")


@pytest.mark.parametrize("code", [code for codes in REASONS_BY_STATUS.values() for code in codes])
def test_every_public_reason_has_one_versioned_error_envelope(code: str) -> None:
    c.validate(
        c.load("error.schema.json"),
        {
            "schema": "mee-evidence-error/v1",
            "request_id": "123e4567-e89b-42d3-a456-426614174000",
            "code": code,
            "message": "Request could not be completed.",
        },
        document="error.schema.json",
    )


@pytest.mark.parametrize(
    "change",
    [
        {"schema": "mee-evidence-error/v2"},
        {"code": "UNKNOWN"},
        {"message": ""},
        {"message": "x" * 257},
        {"request_id": "not-a-uuid"},
        {"details": {"path": "/private/report"}},
        {"stack": "secret"},
        {"wallet": PAYER},
    ],
)
def test_error_envelope_rejects_unknown_versions_codes_and_leak_fields(change: dict) -> None:
    error = {
        "schema": "mee-evidence-error/v1",
        "request_id": "123e4567-e89b-42d3-a456-426614174000",
        "code": "INVALID_INPUT",
        "message": "Invalid request.",
        **change,
    }
    with pytest.raises(c.ContractError):
        c.validate(c.load("error.schema.json"), error, document="error.schema.json")


@pytest.mark.parametrize("field", ["schema", "request_id", "code", "message"])
def test_error_envelope_requires_every_safe_field(field: str) -> None:
    error = {
        "schema": "mee-evidence-error/v1",
        "request_id": "123e4567-e89b-42d3-a456-426614174000",
        "code": "INVALID_INPUT",
        "message": "Invalid request.",
    }
    del error[field]
    with pytest.raises(c.ContractError):
        c.validate(c.load("error.schema.json"), error, document="error.schema.json")


def test_public_reasons_are_closed_to_exactly_the_defined_codes() -> None:
    reasons = c.load("reasons.schema.json")
    expected = {code for codes in REASONS_BY_STATUS.values() for code in codes}
    assert len(expected) == sum(map(len, REASONS_BY_STATUS.values()))
    for code in expected:
        c.validate(reasons, code, document="reasons.schema.json")
    with pytest.raises(c.ContractError):
        c.validate(reasons, "INTERNAL_ERROR", document="reasons.schema.json")
    assert set(reasons["enum"]) == expected
