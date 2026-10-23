"""Integer AMM behavior follows the sourced volatile pool, including fee dust."""

import pytest
from liqvera_evidence_report import calculation


def test_fee_is_truncated_before_subtraction():
    # One wei is fee-free: floor(1 * 30 / 10000) == 0.
    assert calculation.amm_amount_out(1, 100, 1000, 30) == 9
    assert calculation.amm_amount_out(10_000, 100_000, 1_000_000, 30) == 90_661


@pytest.mark.parametrize("quantity", [1, 2, 9, 99, 999])
def test_exact_out_is_the_minimum_sufficient_integer_input(quantity):
    amount = calculation.amm_amount_in(quantity, 100, 1000, 30)
    assert calculation.amm_amount_out(amount, 100, 1000, 30) >= quantity
    assert amount == 0 or calculation.amm_amount_out(amount - 1, 100, 1000, 30) < quantity


@pytest.mark.parametrize("values", [(1, 0, 100, 30), (1, 100, 0, 30),
                                   (-1, 100, 100, 30), (1, 100, 100, 10000),
                                   (True, 100, 100, 30), (1.0, 100, 100, 30)])
def test_invalid_pool_inputs_are_rejected(values):
    with pytest.raises(ValueError, match="MEZO_DEX_INVALID_INPUT"):
        calculation.amm_amount_out(*values)


def test_exact_out_cannot_drain_pool():
    with pytest.raises(ValueError, match="INSUFFICIENT_LIQUIDITY"):
        calculation.amm_amount_in(1000, 100, 1000, 30)


def test_large_integer_precision_and_zero_fee():
    reserve = 10**30
    assert calculation.amm_amount_out(10**18, reserve, reserve, 0) == (10**18 * reserve) // (reserve + 10**18)
    assert calculation.amm_amount_in(0, reserve, reserve, 0) == 0


def test_mezo_report_uses_raw_calls_and_exact_rationals():
    import json
    from pathlib import Path

    from liqvera_evidence_report.mezo_dex import build_dex_report

    probe = json.loads((Path(__file__).resolve().parents[2] /
                        "evidence/mezo-testnet/2026-10-23-protocol-probe.json").read_bytes())
    captured = {"schema": "liqvera-mezo-dex-capture/v1", "source": "mezo-dex:MUSD-BTC:testnet",
                "side": "SELL", "quantity_wei": str(10**18), "probe": probe}
    report = build_dex_report(captured, side="SELL", quantity_btc="1")
    assert report["amount_out"] == "78597122786115561193110"
    assert report["fee_bps"] == 4
    assert report["match"] is True
    assert report["block_number"] == "16319875"
    assert len(report["depth_ladder"]) == 5
    assert report["avg_price_musd"] == "78597.12278611556119311"
    with pytest.raises(ValueError, match="MEZO_DEX_REQUEST_MISMATCH"):
        build_dex_report(captured, side="BUY", quantity_btc="1")


@pytest.mark.parametrize("amount,reserve_in,reserve_out,fee", [
    (10**18, 2**256 - 1, 2**256 - 1, 0),
    (2**256 - 1, 100, 100, 30),
])
def test_solidity_intermediate_overflow_is_rejected(amount, reserve_in, reserve_out, fee):
    with pytest.raises(ValueError, match="MEZO_DEX_ARITHMETIC_OVERFLOW"):
        calculation.amm_amount_out(amount, reserve_in, reserve_out, fee)


@pytest.mark.parametrize("side", ["buy", "sell"])
def test_retained_native_rpc_capture_matches_formula(side):
    import json
    from pathlib import Path

    from liqvera_evidence_report.mezo_dex import build_dex_report

    path = Path(__file__).resolve().parents[2] / f"evidence/mezo-testnet/2026-10-23-dex-{side}-native.json"
    captured = json.loads(path.read_bytes())
    result = build_dex_report(captured, side=side.upper(), quantity_btc="1")
    assert result["router_amount_out"] == result["formula_amount_out"]
    assert result["match"]
