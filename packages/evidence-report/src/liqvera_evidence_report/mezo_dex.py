"""Exact Mezo analytics derived exclusively from decoded evidence calls."""

from fractions import Fraction

from liqvera_public_capture.public_adapters.mezo_dex import (
    POOL,
    ROUTER,
    verify_capture,
)

from liqvera_evidence_report.calculation import _display, amm_amount_in, amm_amount_out


def build_dex_report(capture: dict, *, side: str, quantity_btc: str) -> dict:
    decoded = verify_capture(capture)
    quantity = Fraction(quantity_btc) * 10**18
    if (quantity.denominator != 1 or quantity.numerator != decoded["quantity_wei"]
            or side != decoded["side"]):
        raise ValueError("MEZO_DEX_REQUEST_MISMATCH")
    musd, btc, fee = decoded["reserve_musd"], decoded["reserve_btc"], decoded["fee_bps"]
    mid = Fraction(musd, btc)

    def quote(q: int) -> dict:
        if side == "SELL":
            amount_in = q
            out = amm_amount_out(q, btc, musd, fee)
            if out == 0:
                raise ValueError("INSUFFICIENT_LIQUIDITY")
            average = Fraction(out, q)
            impact = (mid - average) * 10_000 / mid
        else:
            amount_in = amm_amount_in(q, musd, btc, fee)
            out = amm_amount_out(amount_in, musd, btc, fee)
            average = Fraction(amount_in, out)
            impact = (average - mid) * 10_000 / mid
        return {"quantity_btc": _display(Fraction(q, 10**18)),
                "amount_in": str(amount_in), "amount_out": str(out),
                "avg_price_musd": _display(average), "price_impact_bps": _display(impact)}

    result = quote(quantity.numerator)
    if (result["amount_in"] != str(decoded["amount_in"])
            or result["amount_out"] != str(decoded["router_amount_out"])):
        raise ValueError("MEZO_DEX_FORMULA_MISMATCH")
    ladder = []
    for q in (10**16, 10**17, 10**18, 5 * 10**18, 10 * 10**18):
        try:
            ladder.append(quote(q))
        except ValueError as error:
            if str(error) != "INSUFFICIENT_LIQUIDITY":
                raise
            ladder.append({"quantity_btc": _display(Fraction(q, 10**18)),
                           "status": "INSUFFICIENT_LIQUIDITY"})
    block = decoded["block_number"]
    explorer = "https://explorer.test.mezo.org"
    return {"side": side, **result, "mid_price_musd": _display(mid), "fee_bps": fee,
            "router_amount_out": str(decoded["router_amount_out"]),
            "formula_amount_out": result["amount_out"], "match": True, "depth_ladder": ladder,
            "block_number": block, "block_hash": decoded["block_hash"],
            "explorer_links": {"pool": f"{explorer}/address/{POOL}",
                               "router": f"{explorer}/address/{ROUTER}",
                               "block": f"{explorer}/block/{block}"},
            "caveats": ["Mezo Testnet liquidity; excludes gas and execution guarantees.",
                        "BUY is a minimum-input exact-input quote reaching at least the requested BTC.",
                        "Depth ladder is calculated from reserves; only the requested size is RPC cross-checked.",
                        "RPC observations are not independently authenticated chain inclusion proofs."]}


def dex_members(capture: dict) -> dict[str, bytes]:
    from importlib.resources import files
    from pathlib import Path

    from liqvera_evidence_report.canonical import canonical_json_bytes

    members = {"mezo-dex/capture.json": canonical_json_bytes(capture),
               "mezo-dex/calls.json": canonical_json_bytes(capture["probe"]["calls"])}
    for name in ("Pool", "Router", "PoolFactory"):
        filename = f"{name}.testnet.json"
        resource = files("liqvera_evidence_report").joinpath("resources", "mezo", filename)
        if resource.is_file():
            raw = resource.read_bytes()
        else:
            raw = (Path(__file__).resolve().parents[4] /
                   "packages/mezo-protocol/vendor" / filename).read_bytes()
        members[f"mezo-dex/{filename}"] = raw
    return members


def venue_comparison(dex: dict, hl_vwap: Fraction, *, side: str) -> dict:
    # Keep fractions through the comparison; display rounding does not decide venue.
    amount_in, amount_out = int(dex["amount_in"]), int(dex["amount_out"])
    average = Fraction(amount_out, amount_in) if side == "SELL" else Fraction(amount_in, amount_out)
    better = "equal" if average == hl_vwap else (
        "mezo" if (average > hl_vwap if side == "SELL" else average < hl_vwap) else "hyperliquid")
    return {"hyperliquid_avg_price": _display(hl_vwap), "mezo_avg_price": _display(average),
            "spread_bps": _display((average - hl_vwap) * 10_000 / hl_vwap),
            "better_venue": better,
            "caveats": ["Hyperliquid BTC perpetual USD quote versus Mezo BTC spot MUSD quote; not equivalent assets.",
                        "Testnet liquidity; excludes gas, Hyperliquid fees and funding.",
                        "Separate source timestamps; comparison is hypothetical, not an execution recommendation."]}
