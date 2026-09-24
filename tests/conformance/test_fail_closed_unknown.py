"""Hypothesis: unknown outcomes freeze retry until authoritative reconciliation."""

from __future__ import annotations

from tests.conformance.invariants import unknown_blocks_retry


def test_unknown_blocks_retry() -> None:
    assert unknown_blocks_retry("unknown") is True
    assert unknown_blocks_retry("open") is False
    assert unknown_blocks_retry("reconciled") is False
