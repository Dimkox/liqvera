"""Raw-call risk/queue replay; owner-array ordering is deliberately different."""

import copy
import importlib

import pytest

UNIT = 10**18
TM = "0xE47c80e8c23f6B4A1aE41c34837a0599D5D16bb0"
ST = "0x722E4D24FD6Ff8b0AC679450F3D91294607268fA"
PF = "0x86bCF0841622a5dAC14A313a15f96A95421b9366"
ZERO = "0x" + "0" * 40
NODES = ["0x" + "1" * 40, "0x" + "2" * 40, "0x" + "3" * 40]


def word(v):
    return f"{int(v, 16) if isinstance(v, str) else v:064x}"


def fixture_capture(borrower=NODES[1]):
    calls = []

    def call(to, data, *result):
        calls.append(
            {
                "to": to,
                "data": data,
                "block": "0x123",
                "response": {
                    "jsonrpc": "2.0",
                    "id": len(calls) + 1,
                    "result": "0x" + "".join(word(v) for v in result),
                },
            }
        )

    call(PF, "0x0fdb11cf", 80_000 * UNIT)
    for selector, value in [
        ("0x794e5724", 11 * UNIT // 10),
        ("0x5733d58f", 15 * UNIT // 10),
        ("0x49eefeee", 3),
        ("0xa20baee6", UNIT),
        ("0x7af110ba", 200 * UNIT),
        ("0x795d26c3", 200_000 * UNIT),
        ("0x887105d3", 4 * UNIT),
    ]:
        call(TM, selector, value)
    call(TM, "0xb82f263d" + word(80_000 * UNIT), 16 * UNIT // 10)
    call(ST, "0xde8fa431", 3)
    call(ST, "0x4d622831", NODES[0])
    call(ST, "0x1e223143", NODES[2])
    for i, address in enumerate([NODES[2], NODES[0], NODES[1]]):
        call(TM, "0xd9a72444" + word(i), address)
    for i, address in enumerate(NODES):
        debt = (100_000 if i == 0 else 50_000) * UNIT
        coll = (2 if i == 2 else 1) * UNIT
        call(ST, "0xb72703ac" + word(address), NODES[i + 1] if i < 2 else ZERO)
        call(ST, "0x765e0159" + word(address), NODES[i - 1] if i > 0 else ZERO)
        call(TM, "0xb91af97c" + word(address), coll, debt - UNIT, UNIT, 0, 0, 0)
        call(TM, "0x21e37801" + word(address), 1)
        call(TM, "0xd293c710" + word(address) + word(80_000 * UNIT), coll * 80_000 * UNIT // debt)
    if borrower not in NODES:
        call(TM, "0xb91af97c" + word(borrower), 0, 0, 0, 0, 0, 0)
        call(TM, "0x21e37801" + word(borrower), 0)
        call(TM, "0xd293c710" + word(borrower) + word(80_000 * UNIT), 2**256 - 1)
    header = {"number": "0x123", "hash": "0x" + "a" * 64, "timestamp": "0x1000"}
    return {
        "schema": "liqvera-mezo-trove-capture/v1",
        "source": "mezo-troves:MUSD:testnet",
        "borrower": borrower,
        "rpc_url": "https://rpc.test.mezo.org",
        "chain": {"jsonrpc": "2.0", "id": 0, "result": "0x7b7b"},
        "block": {"jsonrpc": "2.0", "id": 0, "result": header},
        "block_after": {"jsonrpc": "2.0", "id": 0, "result": copy.deepcopy(header)},
        "calls": calls,
    }


def module():
    return importlib.import_module("liqvera_public_capture.public_adapters.mezo_troves")


def test_verified_tuple_and_actual_links_determine_rank_skipping_liquidatable():
    result = module().verify_trove_capture(fixture_capture())
    assert result["collateral"] == UNIT
    assert result["principal"] + result["interest"] == 50_000 * UNIT
    assert result["redemption_position"] == 1
    assert result["debt_ahead"] == 0
    result = module().verify_trove_capture(fixture_capture(NODES[2]))
    assert result["redemption_position"] == 2
    assert result["debt_ahead"] == 50_000 * UNIT
    assert result["redeemable_debt_ahead"] == 49_800 * UNIT


def test_no_trove_has_no_fabricated_queue_position():
    result = module().verify_trove_capture(fixture_capture("0x" + "4" * 40))
    assert result["status"] == 0 and result["redemption_position"] is None


@pytest.mark.parametrize(
    "mutation", ["neighbor", "chain", "block", "price", "tuple", "icr", "duplicate", "cycle"]
)
def test_tampered_risk_or_queue_is_rejected(mutation):
    capture = fixture_capture()

    def selected(selector):
        return next(c for c in capture["calls"] if c["data"].startswith(selector))

    if mutation == "neighbor":
        selected("0xb72703ac")["response"]["result"] = "0x" + word(NODES[2])
    elif mutation == "chain":
        capture["chain"]["result"] = "0x7b7c"
    elif mutation == "block":
        capture["block_after"]["result"]["hash"] = "0x" + "b" * 64
    elif mutation == "price":
        selected("0x0fdb11cf")["response"]["result"] = "0x" + word(70_000 * UNIT)
    elif mutation == "tuple":
        selected("0xb91af97c")["response"]["result"] = "0x" + "".join(
            word(v) for v in [100_000 * UNIT, UNIT, 0, 0, 0, 0]
        )
    elif mutation == "icr":
        selected("0xd293c710")["response"]["result"] = "0x" + word(2 * UNIT)
    elif mutation == "duplicate":
        capture["calls"].append(copy.deepcopy(capture["calls"][0]))
    else:
        selected("0xb72703ac")["response"]["result"] = "0x" + word(NODES[0])
    with pytest.raises(ValueError, match="MEZO_TROVE_INVALID_EVIDENCE"):
        module().verify_trove_capture(capture)


@pytest.mark.asyncio
async def test_capture_batches_only_fixed_block_calls_and_replays():
    fixture = fixture_capture()
    lookup = {(c["to"].lower(), c["data"]): c["response"] for c in fixture["calls"]}
    seen = []

    async def rpc(method, params):
        seen.append((method, params))
        if method == "eth_blockNumber":
            return {"jsonrpc": "2.0", "id": 1, "result": "0x123"}
        if method == "eth_chainId":
            return fixture["chain"]
        assert method == "eth_getBlockByNumber" and params == ["0x123", False]
        return fixture["block"]

    async def many(queries, block):
        assert block == "0x123"
        seen.append(("eth_call", queries))
        return [lookup[(to.lower(), data.lower())] for to, data in queries]

    captured = await module().capture_trove(NODES[1], rpc=rpc, rpc_many=many)
    assert module().verify_trove_capture(captured)["redemption_position"] == 1
    assert seen[0][0] == "eth_blockNumber"
    assert set(m for m, _ in seen) == {
        "eth_blockNumber",
        "eth_chainId",
        "eth_getBlockByNumber",
        "eth_call",
    }


@pytest.mark.asyncio
async def test_capture_failure_does_not_load_retained_data():
    async def unavailable(*args):
        raise OSError("offline")

    with pytest.raises(ValueError, match="MEZO_TROVE_SOURCE_UNAVAILABLE"):
        await module().capture_trove(NODES[1], rpc=unavailable, rpc_many=unavailable)


@pytest.mark.asyncio
async def test_capture_preserves_borrower_request_spelling(monkeypatch):
    nodes = ["0x" + "a1" * 20, "0x" + "b2" * 20, "0x" + "c3" * 20]
    monkeypatch.setitem(globals(), "NODES", nodes)
    fixture = fixture_capture(nodes[1])
    lookup = {(c["to"].lower(), c["data"]): c["response"] for c in fixture["calls"]}

    async def rpc(method, params):
        if method == "eth_blockNumber":
            return {"jsonrpc": "2.0", "id": 1, "result": "0x123"}
        return fixture["chain"] if method == "eth_chainId" else fixture["block"]

    async def many(queries, block):
        return [lookup[(to.lower(), data)] for to, data in queries]

    requested = "0x" + nodes[1][2:].upper()
    captured = await module().capture_trove(requested, rpc=rpc, rpc_many=many)
    assert captured["borrower"] == requested


def test_native_transport_retries_one_transient_connection_without_changing_block(monkeypatch):
    import json

    import httpx

    fixture = fixture_capture()
    lookup = {(c["to"].lower(), c["data"]): c["response"]["result"] for c in fixture["calls"]}
    attempts = []

    def response(item):
        method, params = item["method"], item["params"]
        if method == "eth_blockNumber":
            result = "0x123"
        elif method == "eth_chainId":
            result = "0x7b7b"
        elif method == "eth_getBlockByNumber":
            result = fixture["block"]["result"]
        else:
            assert method == "eth_call" and params[1] == "0x123"
            result = lookup[(params[0]["to"].lower(), params[0]["data"])]
        return {"jsonrpc": "2.0", "id": item["id"], "result": result}

    async def handler(request):
        payload = json.loads(request.content)
        attempts.append(payload)
        if len(attempts) == 1:
            raise httpx.ConnectTimeout("transient", request=request)
        body = [response(i) for i in payload] if isinstance(payload, list) else response(payload)
        return httpx.Response(
            200,
            stream=httpx.ByteStream(json.dumps(body).encode()),
            headers={"Content-Type": "application/json"},
        )

    client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: client(transport=httpx.MockTransport(handler), **kwargs),
    )
    captured = module().capture_live_trove(NODES[1])
    assert module().verify_trove_capture(captured)["redemption_position"] == 1
    assert attempts[0] == attempts[1]


def test_unused_call_cannot_hide_unverified_bytes():
    capture = fixture_capture()
    extra = copy.deepcopy(capture["calls"][0])
    extra.update(to=ST, data="0x5dbe47e8" + word(NODES[0]))
    extra["response"]["result"] = "not-an-abi-result"
    capture["calls"].append(extra)
    with pytest.raises(ValueError, match="MEZO_TROVE_INVALID_EVIDENCE"):
        module().verify_trove_capture(capture)


def test_queue_above_limit_has_no_invented_position_and_requires_endpoints():
    capture = fixture_capture()
    for c in capture["calls"]:
        if c["data"] in ["0xde8fa431", "0x49eefeee"]:
            c["response"]["result"] = "0x" + word(501)
    # Retain only metadata and the requested Trove for the bounded result.
    capture["calls"] = [
        c
        for c in capture["calls"]
        if len(c["data"]) == 10
        or c["data"].startswith("0xb82f263d")
        or c["data"]
        in [
            "0xb91af97c" + word(NODES[1]),
            "0x21e37801" + word(NODES[1]),
            "0xd293c710" + word(NODES[1]) + word(80_000 * UNIT),
        ]
    ]
    result = module().verify_trove_capture(capture)
    assert result["queue_status"] == "TRAVERSAL_LIMIT" and result["redemption_position"] is None
    next(c for c in capture["calls"] if c["data"] == "0x4d622831")["response"]["result"] = (
        "0x" + word(ZERO)
    )
    with pytest.raises(ValueError, match="MEZO_TROVE_INVALID_EVIDENCE"):
        module().verify_trove_capture(capture)
