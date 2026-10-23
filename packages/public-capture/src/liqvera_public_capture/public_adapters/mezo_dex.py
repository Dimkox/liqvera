"""Strict offline decoding of raw fixed-block Mezo Testnet DEX observations.

No decoded RPC annotations are trusted. Consistency is not chain authentication.
Selectors derive from the pinned Pool/Router/PoolFactory ABIs in mezo-protocol.
"""

from __future__ import annotations

import re

RPC_URL = "https://rpc.test.mezo.org"
POOL = "0xd16A5Df82120ED8D626a1a15232bFcE2366d6AA9"
ROUTER = "0x9a1ff7FE3a0F69959A3fBa1F1e5ee18e1A9CD7E9"
FACTORY = "0x4947243CC818b627A5D06d14C4eCe7398A23Ce1A"
MUSD = "0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503"
BTC = "0x7b7C000000000000000000000000000000000000"


def _require(ok: bool) -> None:
    if not ok:
        raise ValueError("MEZO_DEX_INVALID_EVIDENCE")


def _words(raw: object, size: int) -> list[int]:
    _require(type(raw) is str and re.fullmatch(r"0x[0-9a-fA-F]+", raw) is not None)
    _require(len(raw) == 2 + 64 * size)
    return [int(raw[i:i + 64], 16) for i in range(2, len(raw), 64)]


def _address_word(address: str) -> str:
    return address[2:].lower().zfill(64)


def router_calldata(amount: int, token_in: str, token_out: str) -> str:
    """Encode one verified four-field Route; no transaction submission surface."""
    _require(type(amount) is int and 0 <= amount < 2**256)
    _require((token_in, token_out) in {(BTC, MUSD), (MUSD, BTC)})
    return "0x5509a1ac" + "".join([
        f"{amount:064x}", f"{64:064x}", f"{1:064x}",
        _address_word(token_in), _address_word(token_out), f"{0:064x}",
        _address_word(FACTORY),
    ])


def decode_probe(probe: object, *, amount: int = 10**18, token_in: str = BTC) -> dict:
    """Decode the retained raw probe; discard every convenience decoded field.

    Probe also includes separate Trove discovery calls. All calls must use its
    one block and have unique target/calldata pairs. Only the required DEX calls
    contribute to the returned DEX calculation input.
    """
    try:
        _require(type(probe) is dict and probe["rpc_url"] == RPC_URL)
        _require(probe["chain"]["result"] == "0x7b7b")
        header = probe["block"]["result"]
        block = header["number"]
        _require(type(block) is str and re.fullmatch(r"0x[1-9a-f][0-9a-f]*", block) is not None)
        _require(re.fullmatch(r"0x[0-9a-fA-F]{64}", header["hash"]) is not None)
        timestamp = int(header["timestamp"], 16)
        if "block_after" in probe:
            after = probe["block_after"]["result"]
            _require(after["number"] == block and after["hash"] == header["hash"]
                     and after["timestamp"] == header["timestamp"])
        _require(type(probe["calls"]) is list and 8 <= len(probe["calls"]) <= 64)
        calls = {}
        for call in probe["calls"]:
            _require(call["block"] == block)
            key = (call["to"].lower(), call["data"].lower())
            _require(key not in calls)
            calls[key] = call

        def words(address: str, data: str, size: int) -> list[int]:
            response = calls[(address.lower(), data.lower())]["response"]
            _require("error" not in response and response.get("jsonrpc") == "2.0")
            return _words(response["result"], size)

        _require(words(POOL, "0x0dfe1681", 1) == [int(MUSD, 16)])
        _require(words(POOL, "0xd21220a7", 1) == [int(BTC, 16)])
        _require(words(POOL, "0x22be3de1", 1) == [0])
        musd, btc, last = words(POOL, "0x0902f1ac", 3)
        _require(musd > 0 and btc > 0 and 0 <= last <= timestamp)
        decimals = words(BTC, "0x313ce567", 1)[0]
        _require(decimals == 18)
        fee = words(FACTORY, "0xcc56b2c5" + _address_word(POOL) + "0" * 64, 1)[0]
        _require(0 <= fee < 10_000)
        _require(type(amount) is int and 0 < amount < 2**256 and token_in in {BTC, MUSD})
        token_out = MUSD if token_in == BTC else BTC
        pool_out = words(POOL, "0xf140a35a" + f"{amount:064x}" + _address_word(token_in), 1)[0]
        router = words(ROUTER, router_calldata(amount, token_in, token_out), 4)
        _require(router[:3] == [32, 2, amount])
        _require(amount * fee < 2**256)
        net = amount - amount * fee // 10_000
        reserve_in, reserve_out = (btc, musd) if token_in == BTC else (musd, btc)
        _require(net * reserve_out < 2**256 and reserve_in + net < 2**256)
        expected = net * reserve_out // (reserve_in + net)
        _require(pool_out == router[3] == expected)
        return {"block_number": str(int(block, 16)), "block_hash": header["hash"],
                "block_timestamp": timestamp, "reserve_musd": musd, "reserve_btc": btc,
                "fee_bps": fee, "btc_decimals": decimals, "pool_amount_out": pool_out,
                "router_amount_out": router[3], "amount_in": amount}
    except (KeyError, TypeError, ValueError, AttributeError, OverflowError) as error:
        raise ValueError("MEZO_DEX_INVALID_EVIDENCE") from error


def _buy_input(quantity: int, reserve_musd: int, reserve_btc: int, fee: int) -> int:
    _require(0 < quantity < reserve_btc and reserve_musd > 0 and 0 <= fee < 10_000)
    denominator = reserve_btc - quantity
    net = (quantity * reserve_musd + denominator - 1) // denominator
    return (net - 1) * 10_000 // (10_000 - fee) + 1


def verify_capture(capture: object) -> dict:
    """Reproduce a request's quote from raw calls without network access."""
    try:
        _require(type(capture) is dict and set(capture) == {
            "schema", "source", "side", "quantity_wei", "probe"})
        _require(capture["schema"] == "liqvera-mezo-dex-capture/v1")
        _require(capture["source"] == "mezo-dex:MUSD-BTC:testnet")
        side = capture["side"]
        text = capture["quantity_wei"]
        _require(side in {"BUY", "SELL"} and type(text) is str
                 and re.fullmatch(r"[1-9][0-9]{0,77}", text) is not None)
        quantity = int(text)
        _require(quantity < 2**256)
        # The planned input is encoded in both quote calls. Decode it from the
        # router calldata, then independently check its exact-out minimality.
        router_calls = [c for c in capture["probe"]["calls"] if c["to"].lower() == ROUTER.lower()]
        _require(len(router_calls) == 1)
        data = router_calls[0]["data"]
        _require(type(data) is str and len(data) >= 74)
        amount = int(data[10:74], 16)
        result = decode_probe(capture["probe"], amount=amount, token_in=BTC if side == "SELL" else MUSD)
        if side == "SELL":
            _require(amount == quantity)
        else:
            _require(amount == _buy_input(quantity, result["reserve_musd"],
                                          result["reserve_btc"], result["fee_bps"]))
            _require(result["router_amount_out"] >= quantity)
        return {**result, "side": side, "quantity_wei": quantity}
    except (KeyError, TypeError, ValueError, AttributeError, OverflowError) as error:
        raise ValueError("MEZO_DEX_INVALID_EVIDENCE") from error


def capture_dex(side: str, quantity_wei: int, *, rpc) -> dict:
    """Capture metadata then calls at one block using a read-only transport.

    The transport accepts (method, params) and returns a JSON-RPC envelope.
    No transport result is substituted with a retained observation on failure.
    """
    if side not in {"BUY", "SELL"} or type(quantity_wei) is not int or not 0 < quantity_wei < 2**256:
        raise ValueError("MEZO_DEX_INVALID_INPUT")
    try:
        block = rpc("eth_blockNumber", [])["result"]
        _require(type(block) is str and re.fullmatch(r"0x[1-9a-f][0-9a-f]*", block) is not None)
        chain = rpc("eth_chainId", [])
        _require(chain.get("result") == "0x7b7b")
        header = rpc("eth_getBlockByNumber", [block, False])
        _require(header["result"]["number"] == block)
        calls = []

        def call(to: str, data: str) -> object:
            response = rpc("eth_call", [{"to": to, "data": data}, block])
            _require(type(response) is dict and "error" not in response and "result" in response)
            calls.append({"to": to, "data": data, "block": block, "response": response})
            return response["result"]

        call(POOL, "0x0dfe1681")
        call(POOL, "0xd21220a7")
        call(POOL, "0x22be3de1")
        reserves = _words(call(POOL, "0x0902f1ac"), 3)
        call(BTC, "0x313ce567")
        fee = _words(call(FACTORY, "0xcc56b2c5" + _address_word(POOL) + "0" * 64), 1)[0]
        amount = quantity_wei if side == "SELL" else _buy_input(quantity_wei, reserves[0], reserves[1], fee)
        token_in, token_out = (BTC, MUSD) if side == "SELL" else (MUSD, BTC)
        call(POOL, "0xf140a35a" + f"{amount:064x}" + _address_word(token_in))
        call(ROUTER, router_calldata(amount, token_in, token_out))
        after = rpc("eth_getBlockByNumber", [block, False])
        _require(after["result"]["hash"] == header["result"]["hash"])
        capture = {"schema": "liqvera-mezo-dex-capture/v1", "source": "mezo-dex:MUSD-BTC:testnet",
                   "side": side, "quantity_wei": str(quantity_wei),
                   "probe": {"rpc_url": RPC_URL, "chain": chain, "block": header, "block_after": after, "calls": calls}}
        verify_capture(capture)
        return capture
    except (OSError, KeyError, TypeError, ValueError) as error:
        raise ValueError("MEZO_SOURCE_UNAVAILABLE") from error


def capture_live_dex(side: str, quantity_wei: int) -> dict:
    """Bounded production transport restricted to the pinned Testnet RPC."""
    import httpx

    from liqvera_public_capture.evidence_capture import _deadline, strict_json

    request_id = 0
    try:
        with _deadline(), httpx.Client(trust_env=False, follow_redirects=False, timeout=3.0,
                                      headers={"Accept-Encoding": "identity"}) as client:
            def rpc(method, params):
                nonlocal request_id
                request_id += 1
                with client.stream("POST", RPC_URL, json={"jsonrpc": "2.0", "id": request_id,
                                                          "method": method, "params": params}) as response:
                    if response.status_code != 200 or response.headers.get("content-encoding", "identity") != "identity":
                        raise ValueError("MEZO_SOURCE_UNAVAILABLE")
                    raw = bytearray()
                    for chunk in response.iter_raw():
                        if len(raw) + len(chunk) > 256 * 1024:
                            raise ValueError("MEZO_SOURCE_UNAVAILABLE")
                        raw.extend(chunk)
                result = strict_json(bytes(raw))
                if (type(result) is not dict or result.get("jsonrpc") != "2.0"
                        or type(result.get("id")) is not int or result["id"] != request_id
                        or "error" in result or "result" not in result):
                    raise ValueError("MEZO_SOURCE_UNAVAILABLE")
                return result
            return capture_dex(side, quantity_wei, rpc=rpc)
    except (httpx.HTTPError, OSError, ValueError) as error:
        raise ValueError("MEZO_SOURCE_UNAVAILABLE") from error
