"""Hypothesis: only exact owned identity keys are actionable."""

from __future__ import annotations

import pytest

from tests.conformance.invariants import OwnershipKey, claim_unique, owned_keys_only


def test_only_exact_owned_keys_are_returned() -> None:
    owned = frozenset(
        {
            OwnershipKey("t", "a", "hyperliquid", "engine-1"),
        }
    )
    candidates = (
        OwnershipKey("t", "a", "hyperliquid", "engine-1"),
        OwnershipKey("t", "a", "hyperliquid", "manual-1"),
        OwnershipKey("other", "a", "hyperliquid", "engine-1"),
    )
    assert owned_keys_only(owned, candidates) == (candidates[0],)


def test_conflicting_claim_fails_closed() -> None:
    key = OwnershipKey("t", "a", "lighter", "same")
    owned = claim_unique(frozenset(), key)
    with pytest.raises(ValueError, match="ownership conflict"):
        claim_unique(owned, key)
