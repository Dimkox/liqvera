"""Hypothesis: reservation fails closed on stale data or degraded venue."""

from __future__ import annotations

from dataclasses import replace

import pytest
from mee_contracts.exact import ExactDecimal

from tests.conformance.invariants import (
    ReservationLimits,
    ReservationRequest,
    evaluate_reservation,
)


def _limits() -> ReservationLimits:
    return ReservationLimits(
        max_notional=ExactDecimal.parse("100"),
        max_gross=ExactDecimal.parse("1000"),
    )


def test_healthy_fresh_request_reserves_notional() -> None:
    reserved = evaluate_reservation(
        _limits(),
        ReservationRequest(
            notional=ExactDecimal.parse("50"),
            gross_after=ExactDecimal.parse("500"),
            venue_healthy=True,
            market_data_fresh=True,
        ),
    )
    assert str(reserved) == "50"


def test_degraded_or_stale_request_fails_closed() -> None:
    healthy = ReservationRequest(
        notional=ExactDecimal.parse("50"),
        gross_after=ExactDecimal.parse("500"),
        venue_healthy=True,
        market_data_fresh=True,
    )
    with pytest.raises(ValueError, match="reservation rejected"):
        evaluate_reservation(_limits(), replace(healthy, venue_healthy=False))
    with pytest.raises(ValueError, match="reservation rejected"):
        evaluate_reservation(_limits(), replace(healthy, market_data_fresh=False))
