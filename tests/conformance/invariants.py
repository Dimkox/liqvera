"""Executable Python specifications for retained domain invariants."""

from __future__ import annotations

from dataclasses import dataclass

from mee_contracts.exact import ExactDecimal


@dataclass(frozen=True, slots=True)
class OwnershipKey:
    tenant_id: str
    account_id: str
    venue: str
    client_id: str


def owned_keys_only(
    owned: frozenset[OwnershipKey], candidates: tuple[OwnershipKey, ...]
) -> tuple[OwnershipKey, ...]:
    return tuple(item for item in candidates if item in owned)


def claim_unique(owned: frozenset[OwnershipKey], key: OwnershipKey) -> frozenset[OwnershipKey]:
    if key in owned:
        raise ValueError("ownership conflict")
    return owned | {key}


def unknown_blocks_retry(state: str) -> bool:
    return state == "unknown"


def apply_cumulative(
    current: ExactDecimal, incoming: ExactDecimal, base_quantity: ExactDecimal
) -> ExactDecimal:
    if incoming.scaled < 0:
        raise ValueError("negative fill")
    if incoming < current:
        raise ValueError("fill regression")
    if incoming.scaled > base_quantity.scaled:
        raise ValueError("overfill")
    return incoming


@dataclass(frozen=True, slots=True)
class ReservationRequest:
    notional: ExactDecimal
    gross_after: ExactDecimal
    venue_healthy: bool
    market_data_fresh: bool


@dataclass(frozen=True, slots=True)
class ReservationLimits:
    max_notional: ExactDecimal
    max_gross: ExactDecimal


def evaluate_reservation(
    limits: ReservationLimits, request: ReservationRequest
) -> ExactDecimal:
    if not request.venue_healthy or not request.market_data_fresh:
        raise ValueError("reservation rejected")
    if request.notional.scaled > limits.max_notional.scaled:
        raise ValueError("reservation rejected")
    if request.gross_after.scaled > limits.max_gross.scaled:
        raise ValueError("reservation rejected")
    return request.notional
