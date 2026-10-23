"""Capture/replay use identical fixed-block calls and never synthetic fallback."""

import copy
import importlib
import json
from pathlib import Path

import pytest

PROBE = json.loads((Path(__file__).resolve().parents[2] /
                    "evidence/mezo-testnet/2026-10-23-protocol-probe.json").read_bytes())


def adapter():
    return importlib.import_module("liqvera_public_capture.public_adapters.mezo_dex")


def test_real_probe_can_be_decoded_without_network():
    result = adapter().decode_probe(PROBE)
    assert result["fee_bps"] == 4
    assert result["btc_decimals"] == 18
    assert result["reserve_btc"] == 1303382989603728612099
    assert result["reserve_musd"] == 102561743252456623466280588
    assert result["router_amount_out"] == result["pool_amount_out"] == 78597122786115561193110
    assert result["block_number"] == "16319875"


@pytest.mark.parametrize("mutation", ["block", "chain", "destination", "duplicate", "fee", "router"])
def test_tampered_probe_is_rejected(mutation):
    probe = copy.deepcopy(PROBE)
    if mutation == "block":
        probe["calls"][0]["block"] = "0x1"
    elif mutation == "chain":
        probe["chain"]["result"] = "0x7b7c"
    elif mutation == "destination":
        probe["calls"][0]["to"] = "0x" + "00" * 20
    elif mutation == "duplicate":
        probe["calls"].append(probe["calls"][0])
    elif mutation == "fee":
        probe["calls"][5]["response"]["result"] = "0x" + format(30, "064x")
    else:
        probe["calls"][7]["response"]["result"] = "0x00"
    with pytest.raises(ValueError, match="MEZO_DEX_INVALID_EVIDENCE"):
        adapter().decode_probe(probe)


def test_capture_uses_only_fixed_block_read_calls_and_reproduces_sell():
    module = adapter()
    recorded = []
    responses = {(c["to"].lower(), c["data"].lower()): c["response"]
                 for c in PROBE["calls"]}

    def rpc(method, params):
        recorded.append((method, params))
        if method == "eth_blockNumber":
            return {"jsonrpc": "2.0", "id": 1, "result": PROBE["block"]["result"]["number"]}
        if method == "eth_chainId":
            return PROBE["chain"]
        if method == "eth_getBlockByNumber":
            return PROBE["block"]
        assert method == "eth_call"
        assert params[1] == PROBE["block"]["result"]["number"]
        return responses[(params[0]["to"].lower(), params[0]["data"].lower())]

    captured = module.capture_dex("SELL", 10**18, rpc=rpc)
    decoded = module.verify_capture(captured)
    assert decoded["router_amount_out"] == 78597122786115561193110
    assert decoded["fee_bps"] == 4
    assert recorded[0][0] == "eth_blockNumber"


def test_rpc_failure_never_uses_retained_probe():
    def rpc(method, params):
        raise OSError("unavailable")

    with pytest.raises(ValueError, match="MEZO_SOURCE_UNAVAILABLE"):
        adapter().capture_dex("SELL", 10**18, rpc=rpc)


def test_forged_mathematically_consistent_but_overflowing_pool_is_rejected():
    probe = copy.deepcopy(PROBE)
    reserve = 2**256 - 1
    block_timestamp = int(probe['block']['result']['timestamp'], 16)
    probe['calls'][3]['response']['result'] = '0x' + ''.join(f'{v:064x}' for v in [reserve,reserve,block_timestamp])
    probe['calls'][5]['response']['result'] = '0x' + '0'*64
    amount = 10**18
    expected = amount * reserve // (reserve + amount)
    probe['calls'][6]['response']['result'] = '0x' + f'{expected:064x}'
    probe['calls'][7]['response']['result'] = '0x' + ''.join(f'{v:064x}' for v in [32,2,amount,expected])
    with pytest.raises(ValueError,match='MEZO_DEX_INVALID_EVIDENCE'):
        adapter().decode_probe(probe)


def test_block_header_recheck_rejects_reorg():
    probe = copy.deepcopy(PROBE)
    probe['block_after'] = copy.deepcopy(probe['block'])
    probe['block_after']['result']['hash'] = '0x'+'0'*64
    with pytest.raises(ValueError,match='MEZO_DEX_INVALID_EVIDENCE'):
        adapter().decode_probe(probe)


@pytest.mark.live
@pytest.mark.parametrize('side', ['BUY', 'SELL'])
def test_native_fixed_block_quote_matches_formula(side):
    captured = adapter().capture_live_dex(side,10**18)
    decoded = adapter().verify_capture(captured)
    assert decoded['router_amount_out'] == decoded['pool_amount_out']
    assert decoded['block_number']
