"""Closed sealed Stage A economics document: exact strings, no floats."""

from __future__ import annotations

import json
from decimal import Decimal

import pytest
from mee_contracts.economics import (
    STAGE_A_SEALED_ECONOMICS_SCHEMA,
    SealedStageAEconomics,
)
from mee_contracts.exact import ExactDecimal, ExactError


def _document(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema": STAGE_A_SEALED_ECONOMICS_SCHEMA,
        "independent_episode_count": 20,
        "total_net": "1",
        "median_net": "1",
        "usd_1000_net": "1",
        "usd_5000_net": "0",
        "largest_episode_concentration": "0.24",
        "survived_delay_300ms": True,
        "survived_delay_500ms": True,
        "survived_both_fee_cases": True,
    }
    payload.update(overrides)
    return payload


def _valid(**overrides: object) -> SealedStageAEconomics:
    values: dict[str, object] = {
        "schema": STAGE_A_SEALED_ECONOMICS_SCHEMA,
        "independent_episode_count": 20,
        "total_net": ExactDecimal.parse("1"),
        "median_net": ExactDecimal.parse("1"),
        "usd_1000_net": ExactDecimal.parse("1"),
        "usd_5000_net": ExactDecimal.parse("0"),
        "largest_episode_concentration": ExactDecimal.parse("0.24"),
        "survived_delay_300ms": True,
        "survived_delay_500ms": True,
        "survived_both_fee_cases": True,
    }
    values.update(overrides)
    return SealedStageAEconomics(**values)  # type: ignore[arg-type]


def test_from_document_accepts_closed_object() -> None:
    economics = SealedStageAEconomics.from_document(_document())
    assert economics.schema == STAGE_A_SEALED_ECONOMICS_SCHEMA
    assert economics.independent_episode_count == 20
    assert economics.total_net == ExactDecimal.parse("1")
    assert economics.usd_5000_net == ExactDecimal.parse("0")
    assert economics.largest_episode_concentration == ExactDecimal.parse("0.24")
    assert economics.survived_delay_300ms is True
    assert economics.survived_both_fee_cases is True


def test_to_canonical_json_is_sorted_compact_ascii() -> None:
    payload = SealedStageAEconomics.from_document(_document()).to_canonical_json()
    assert payload.endswith(b"\n")
    document = json.loads(payload)
    assert tuple(document) == (
        "independent_episode_count",
        "largest_episode_concentration",
        "median_net",
        "schema",
        "survived_both_fee_cases",
        "survived_delay_300ms",
        "survived_delay_500ms",
        "total_net",
        "usd_1000_net",
        "usd_5000_net",
    )
    assert document["schema"] == STAGE_A_SEALED_ECONOMICS_SCHEMA
    assert document["usd_5000_net"] == "0"
    assert document["largest_episode_concentration"] == "0.24"
    assert payload == (
        json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("ascii")


@pytest.mark.parametrize(
    "document",
    (
        _document(extra=True),
        {key: value for key, value in _document().items() if key != "total_net"},
        _document(schema="mee-stage-a-sealed-economics/v0"),
        [],
    ),
)
def test_from_document_rejects_key_set_and_schema(document: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        SealedStageAEconomics.from_document(document)


@pytest.mark.parametrize(
    "overrides",
    (
        {"total_net": 1},
        {"median_net": 1.25},
        {"usd_1000_net": None},
        {"usd_5000_net": "1e-2"},
        {"largest_episode_concentration": 0.24},
        {"independent_episode_count": True},
        {"independent_episode_count": 20.0},
        {"independent_episode_count": -1},
        {"survived_delay_300ms": 1},
        {"survived_delay_500ms": 0},
        {"survived_both_fee_cases": "true"},
    ),
)
def test_from_document_rejects_non_string_money_and_bad_scalars(
    overrides: dict[str, object],
) -> None:
    with pytest.raises((TypeError, ValueError, ExactError)):
        SealedStageAEconomics.from_document(_document(**overrides))


def test_constructor_rejects_non_exact_nets_and_non_bool_survivals() -> None:
    with pytest.raises(TypeError):
        _valid(total_net="1")
    with pytest.raises(TypeError):
        _valid(median_net=Decimal("1"))
    with pytest.raises(TypeError):
        _valid(usd_1000_net=1.25)
    with pytest.raises(TypeError):
        _valid(survived_delay_300ms=1)
    with pytest.raises(TypeError):
        _valid(independent_episode_count=True)
    with pytest.raises(ValueError):
        _valid(independent_episode_count=-1)
    with pytest.raises(TypeError):
        ExactDecimal(0.25)  # type: ignore[arg-type]
    assert ExactDecimal.parse("0.25") == ExactDecimal.parse("0.25")
