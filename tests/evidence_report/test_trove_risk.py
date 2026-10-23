"""Trove arithmetic uses the verified collateral/principal/interest ABI order."""

import pytest
from liqvera_evidence_report import calculation

UNIT = 10**18


def risk(**changes):
    values = dict(
        collateral=2 * UNIT,
        principal=79_000 * UNIT,
        interest=1_000 * UNIT,
        price=80_000 * UNIT,
        mcr=11 * UNIT // 10,
        ccr=15 * UNIT // 10,
        tcr=2 * UNIT,
        status=1,
    )
    return calculation.trove_risk(**(values | changes))


def test_active_trove_exact_threshold_buffer_and_scenarios():
    result = risk()
    assert result["debt_musd"] == "80000"
    assert result["collateral_btc"] == "2"
    assert result["icr_atomic"] == str(2 * UNIT)
    assert result["icr"] == "2"
    assert result["liquidation_price_musd"] == "44000"
    assert result["buffer_pct"] == "81.81818181818181818181818182"
    assert [s["icr"] for s in result["scenarios"]] == ["1.8", "1.6", "1.4"]
    assert result["flags"] == []


def test_liquidatable_and_recovery_flags_are_independent():
    result = risk(price=40_000 * UNIT, tcr=14 * UNIT // 10)
    assert result["flags"] == ["LIQUIDATABLE", "RECOVERY_MODE"]
    assert result["icr"] == "1"
    assert result["buffer_pct"].startswith("-9.0909")


@pytest.mark.parametrize("status", [0, 2, 3, 4])
def test_inactive_zero_debt_has_no_division_or_healthy_claim(status):
    result = risk(collateral=0, principal=0, interest=0, status=status)
    assert result["status"] == "NOT_ACTIVE"
    assert result["icr"] is None
    assert result["liquidation_price_musd"] is None
    assert result["buffer_pct"] is None
    assert result["icr_atomic"] == str(2**256 - 1)


def test_zero_collateral_nonzero_debt_has_no_division():
    result = risk(collateral=0)
    assert result["icr_atomic"] == "0"
    assert result["liquidation_price_musd"] is None
    assert "LIQUIDATABLE" in result["flags"]


@pytest.mark.parametrize(
    "changes",
    [
        {"principal": 2**256},
        {"interest": True},
        {"price": 0},
        {"status": 5},
        {"collateral": 2**256 - 1},
        {"principal": 0, "interest": 0},
    ],
)
def test_invalid_or_solidity_overflowing_inputs_reject(changes):
    with pytest.raises(ValueError, match="MEZO_TROVE_INVALID_INPUT"):
        risk(**changes)


def test_retained_native_capture_reproduces_contract_icr_and_queue_offline():
    import json
    from pathlib import Path

    from liqvera_public_capture.public_adapters.mezo_troves import verify_trove_capture

    path = (
        Path(__file__).resolve().parents[2]
        / "evidence/mezo-testnet/2026-10-23-trove-active-native.json"
    )
    decoded = verify_trove_capture(json.loads(path.read_bytes()))
    report = calculation.trove_risk(
        **{
            name: decoded[name]
            for name in (
                "collateral",
                "principal",
                "interest",
                "price",
                "mcr",
                "ccr",
                "tcr",
                "status",
            )
        }
    )
    assert report["icr_atomic"] == str(decoded["icr"])
    assert decoded["redemption_position"] == 1
    assert decoded["block_number"] == "16320987"
