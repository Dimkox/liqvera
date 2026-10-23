"""Fixed-block Mezo Testnet Trove evidence and exact raw-call verification."""

from __future__ import annotations

import re

from liqvera_public_capture.public_adapters.mezo_dex import RPC_URL, _address_word, _words

TROVE_MANAGER = "0xE47c80e8c23f6B4A1aE41c34837a0599D5D16bb0"
SORTED_TROVES = "0x722E4D24FD6Ff8b0AC679450F3D91294607268fA"
PRICE_FEED = "0x86bCF0841622a5dAC14A313a15f96A95421b9366"
ZERO = "0x" + "0" * 40
UNIT = 10**18
QUEUE_LIMIT = 500
MAXIMUM = 2**256 - 1
# Selectors are checked against the pinned verified implementation ABI by tests.
MANAGER_SELECTORS = {
    "0x794e5724": 0,
    "0x5733d58f": 0,
    "0xa20baee6": 0,
    "0x7af110ba": 0,
    "0x49eefeee": 0,
    "0xd9a72444": 1,
    "0xb91af97c": 1,
    "0x21e37801": 1,
    "0xd293c710": 2,
    "0xb82f263d": 1,
    "0x795d26c3": 0,
    "0x887105d3": 0,
}
SORTED_SELECTORS = {
    "0xde8fa431": 0,
    "0x4d622831": 0,
    "0x1e223143": 0,
    "0xb72703ac": 1,
    "0x765e0159": 1,
    "0x5dbe47e8": 1,
}


def _require(condition: bool) -> None:
    if not condition:
        raise ValueError("MEZO_TROVE_INVALID_EVIDENCE")


def _address(value: object, *, zero: bool = False) -> str:
    _require(type(value) is str and re.fullmatch(r"0x[0-9a-fA-F]{40}", value) is not None)
    value = value.lower()
    _require(zero or value != ZERO)
    return value


def _icr(collateral: int, debt: int, price: int) -> int:
    _require(debt <= MAXIMUM)
    if debt == 0:
        return MAXIMUM
    _require(collateral * price <= MAXIMUM)
    return collateral * price // debt


def verify_trove_capture(capture: object) -> dict:
    """Prove internal call/risk/list consistency, not canonical chain inclusion."""
    try:
        return _verify(capture)
    except (KeyError, TypeError, ValueError, AttributeError, OverflowError) as error:
        raise ValueError("MEZO_TROVE_INVALID_EVIDENCE") from error


def _verify(capture: dict) -> dict:
    _require(
        type(capture) is dict
        and set(capture)
        == {"schema", "source", "borrower", "rpc_url", "chain", "block", "block_after", "calls"}
    )
    _require(
        capture["schema"] == "liqvera-mezo-trove-capture/v1"
        and capture["source"] == "mezo-troves:MUSD:testnet"
        and capture["rpc_url"] == RPC_URL
        and capture["chain"]["result"] == "0x7b7b"
    )
    borrower = _address(capture["borrower"])
    header = capture["block"]["result"]
    block = header["number"]
    _require(type(block) is str and re.fullmatch(r"0x[1-9a-f][0-9a-f]*", block) is not None)
    _require(
        type(header["hash"]) is str
        and re.fullmatch(r"0x[0-9a-fA-F]{64}", header["hash"]) is not None
    )
    _require(
        all(
            capture["block_after"]["result"][key] == header[key]
            for key in ("number", "hash", "timestamp")
        )
    )
    _require(int(header["timestamp"], 16) >= 0)
    _require(type(capture["calls"]) is list and 15 <= len(capture["calls"]) <= 6 * QUEUE_LIMIT + 32)
    calls = {}
    allowed = {
        TROVE_MANAGER.lower(): MANAGER_SELECTORS,
        SORTED_TROVES.lower(): SORTED_SELECTORS,
        PRICE_FEED.lower(): {"0x0fdb11cf": 0},
    }
    for call in capture["calls"]:
        _require(type(call) is dict and set(call) == {"to", "data", "block", "response"})
        target, data = _address(call["to"]), call["data"].lower()
        _require(call["block"] == block and target in allowed and data[:10] in allowed[target])
        _require(
            len(data) == 10 + 64 * allowed[target][data[:10]]
            and re.fullmatch(r"0x[0-9a-f]+", data) is not None
        )
        key = (target, data)
        _require(key not in calls)
        response = call["response"]
        _require(
            type(response) is dict
            and response.get("jsonrpc") == "2.0"
            and "error" not in response
            and "result" in response
        )
        calls[key] = response["result"]

    used = set()

    def words(to: str, selector: str, count: int = 1, args: str = "") -> list[int]:
        key = (to.lower(), selector + args)
        used.add(key)
        return _words(calls[key], count)

    def uint(to: str, selector: str, args: str = "") -> int:
        return words(to, selector, args=args)[0]

    def address(to: str, selector: str, args: str = "") -> str:
        value = uint(to, selector, args)
        _require(value < 2**160)
        return "0x" + f"{value:040x}"

    price = uint(PRICE_FEED, "0x0fdb11cf")
    precision = uint(TROVE_MANAGER, "0xa20baee6")
    mcr, ccr = uint(TROVE_MANAGER, "0x794e5724"), uint(TROVE_MANAGER, "0x5733d58f")
    gas = uint(TROVE_MANAGER, "0x7af110ba")
    _require(price > 0 and precision == UNIT and 0 < mcr <= ccr and gas > 0)
    price_arg = f"{price:064x}"
    system_debt = uint(TROVE_MANAGER, "0x795d26c3")
    system_coll = uint(TROVE_MANAGER, "0x887105d3")
    tcr = uint(TROVE_MANAGER, "0xb82f263d", price_arg)
    _require(tcr == _icr(system_coll, system_debt, price))
    size = uint(SORTED_TROVES, "0xde8fa431")
    owners_count = uint(TROVE_MANAGER, "0x49eefeee")
    _require(size == owners_count)
    first = address(SORTED_TROVES, "0x1e223143")
    last = address(SORTED_TROVES, "0x4d622831")
    _require((first == ZERO and last == ZERO) if size == 0 else (first != ZERO and last != ZERO))

    def trove(owner: str) -> dict:
        arg = _address_word(owner)
        coll, principal, interest, pending_coll, pending_principal, pending_interest = words(
            TROVE_MANAGER, "0xb91af97c", 6, arg
        )
        status = uint(TROVE_MANAGER, "0x21e37801", arg)
        ratio = uint(TROVE_MANAGER, "0xd293c710", arg + price_arg)
        _require(
            0 <= status <= 4
            and pending_coll <= coll
            and pending_principal <= principal
            and pending_interest <= interest
        )
        debt = principal + interest
        _require(ratio == _icr(coll, debt, price))
        _require(status != 1 or debt >= gas)
        return {
            "collateral": coll,
            "principal": principal,
            "interest": interest,
            "status": status,
            "icr": ratio,
            "debt": debt,
        }

    target = trove(borrower)
    result = {
        **target,
        "borrower": capture["borrower"],
        "price": price,
        "mcr": mcr,
        "ccr": ccr,
        "tcr": tcr,
        "gas_compensation": gas,
        "sorted_troves_size": size,
        "block_number": str(int(block, 16)),
        "block_hash": header["hash"],
        "block_timestamp": int(header["timestamp"], 16),
        "redemption_position": None,
        "debt_ahead": None,
        "redeemable_debt_ahead": None,
        "queue_status": "NOT_ACTIVE" if target["status"] != 1 else "TRAVERSAL_LIMIT",
    }
    if size > QUEUE_LIMIT:
        _require(set(calls) == used)
        return result
    owners = [address(TROVE_MANAGER, "0xd9a72444", f"{i:064x}") for i in range(size)]
    _require(len(set(owners)) == size and ZERO not in owners)
    _require((borrower in owners) == (target["status"] == 1))
    seen = set()
    previous, current = ZERO, last
    rank, debt_ahead, net_ahead = 0, 0, 0
    while current != ZERO:
        _require(current in owners and current not in seen)
        seen.add(current)
        arg = _address_word(current)
        _require(address(SORTED_TROVES, "0x765e0159", arg) == previous)
        node = trove(current)
        _require(node["status"] == 1)
        if node["icr"] >= mcr:
            rank += 1
            if current == borrower:
                result.update(
                    redemption_position=rank,
                    debt_ahead=debt_ahead,
                    redeemable_debt_ahead=net_ahead,
                    queue_status="PROVEN",
                )
            debt_ahead += node["debt"]
            net_ahead += node["debt"] - gas
        previous, current = current, address(SORTED_TROVES, "0xb72703ac", arg)
    _require(seen == set(owners) and previous == first)
    if target["status"] == 1 and target["icr"] < mcr:
        result["queue_status"] = "BELOW_MCR"
    if tcr < mcr:
        result.update(
            redemption_position=None,
            debt_ahead=None,
            redeemable_debt_ahead=None,
            queue_status="SYSTEM_PAUSED",
        )
    _require(set(calls) == used)
    return result


async def capture_trove(borrower: str, *, rpc, rpc_many) -> dict:
    """Collect one block using bounded batched owner discovery, never list sorting."""
    requested_borrower = borrower
    borrower = _address(borrower)
    try:
        block = (await rpc("eth_blockNumber", []))["result"]
        _require(type(block) is str and re.fullmatch(r"0x[1-9a-f][0-9a-f]*", block) is not None)
        chain = await rpc("eth_chainId", [])
        _require(chain.get("result") == "0x7b7b")
        header = await rpc("eth_getBlockByNumber", [block, False])
        _require(header["result"]["number"] == block)
        calls = []
        results = {}

        async def collect(queries):
            missing = []
            for to, data in queries:
                key = (to.lower(), data.lower())
                if key not in results and (to, data) not in missing:
                    missing.append((to, data))
            if not missing:
                return
            responses = await rpc_many(missing, block)
            _require(type(responses) is list and len(responses) == len(missing))
            for (to, data), response in zip(missing, responses, strict=True):
                _require(
                    type(response) is dict
                    and response.get("jsonrpc") == "2.0"
                    and "error" not in response
                    and "result" in response
                )
                results[(to.lower(), data.lower())] = response["result"]
                calls.append({"to": to, "data": data, "block": block, "response": response})

        def uint(to, data):
            return _words(results[(to.lower(), data.lower())], 1)[0]

        await collect(
            [(PRICE_FEED, "0x0fdb11cf")]
            + [
                (TROVE_MANAGER, selector)
                for selector in (
                    "0x794e5724",
                    "0x5733d58f",
                    "0xa20baee6",
                    "0x7af110ba",
                    "0x49eefeee",
                    "0x795d26c3",
                    "0x887105d3",
                )
            ]
            + [(SORTED_TROVES, selector) for selector in ("0xde8fa431", "0x4d622831", "0x1e223143")]
        )
        price = uint(PRICE_FEED, "0x0fdb11cf")
        size = uint(SORTED_TROVES, "0xde8fa431")
        _require(price > 0 and size == uint(TROVE_MANAGER, "0x49eefeee"))
        price_arg = f"{price:064x}"
        owners_queries = (
            [(TROVE_MANAGER, "0xd9a72444" + f"{i:064x}") for i in range(size)]
            if size <= QUEUE_LIMIT
            else []
        )
        borrower_arg = _address_word(borrower)
        await collect(
            owners_queries
            + [
                (TROVE_MANAGER, "0xb82f263d" + price_arg),
                (TROVE_MANAGER, "0xb91af97c" + borrower_arg),
                (TROVE_MANAGER, "0x21e37801" + borrower_arg),
                (TROVE_MANAGER, "0xd293c710" + borrower_arg + price_arg),
            ]
        )
        owners = []
        for to, data in owners_queries:
            value = uint(to, data)
            _require(0 < value < 2**160)
            owners.append("0x" + f"{value:040x}")
        queries = []
        for owner in owners:
            arg = _address_word(owner)
            queries.extend(
                [
                    (SORTED_TROVES, "0xb72703ac" + arg),
                    (SORTED_TROVES, "0x765e0159" + arg),
                    (TROVE_MANAGER, "0xb91af97c" + arg),
                    (TROVE_MANAGER, "0x21e37801" + arg),
                    (TROVE_MANAGER, "0xd293c710" + arg + price_arg),
                ]
            )
        await collect(queries)
        after = await rpc("eth_getBlockByNumber", [block, False])
        capture = {
            "schema": "liqvera-mezo-trove-capture/v1",
            "source": "mezo-troves:MUSD:testnet",
            "borrower": requested_borrower,
            "rpc_url": RPC_URL,
            "chain": chain,
            "block": header,
            "block_after": after,
            "calls": calls,
        }
        verify_trove_capture(capture)
        return capture
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise ValueError("MEZO_TROVE_SOURCE_UNAVAILABLE") from error


def capture_live_trove(borrower: str) -> dict:
    """Native read-only transport: 64-call batches, four in flight, 12s total."""
    import asyncio

    import httpx

    from liqvera_public_capture.evidence_capture import strict_json

    async def run():
        request_id = 0
        semaphore = asyncio.Semaphore(4)
        async with (
            asyncio.timeout(12),
            httpx.AsyncClient(
                trust_env=False,
                follow_redirects=False,
                timeout=3.0,
                headers={"Accept-Encoding": "identity"},
            ) as client,
        ):

            def request(method, params):
                nonlocal request_id
                request_id += 1
                return {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}

            async def send(payload):
                for attempt in range(2):
                    try:
                        async with (
                            semaphore,
                            client.stream("POST", RPC_URL, json=payload) as response,
                        ):
                            if (
                                response.status_code != 200
                                or response.headers.get("content-encoding", "identity")
                                != "identity"
                            ):
                                raise ValueError("MEZO_TROVE_SOURCE_UNAVAILABLE")
                            raw = bytearray()
                            async for chunk in response.aiter_raw():
                                if len(raw) + len(chunk) > 256 * 1024:
                                    raise ValueError("MEZO_TROVE_SOURCE_UNAVAILABLE")
                                raw.extend(chunk)
                            return strict_json(bytes(raw))
                    except (httpx.ConnectTimeout, httpx.ConnectError, httpx.ReadTimeout):
                        if attempt:
                            raise
                raise ValueError("MEZO_TROVE_SOURCE_UNAVAILABLE")

            def validate(response, expected_id):
                _require(
                    type(response) is dict
                    and response.get("jsonrpc") == "2.0"
                    and type(response.get("id")) is int
                    and response["id"] == expected_id
                    and "error" not in response
                    and "result" in response
                )
                return response

            async def rpc(method, params):
                payload = request(method, params)
                return validate(await send(payload), payload["id"])

            async def many(queries, block):
                async def chunk(part):
                    payload = [
                        request("eth_call", [{"to": to, "data": data}, block]) for to, data in part
                    ]
                    response = await send(payload)
                    _require(type(response) is list and len(response) == len(payload))
                    _require(
                        all(type(item) is dict and type(item.get("id")) is int for item in response)
                    )
                    by_id = {item["id"]: item for item in response}
                    _require(len(by_id) == len(payload))
                    return [validate(by_id[item["id"]], item["id"]) for item in payload]

                chunks = [queries[i : i + 64] for i in range(0, len(queries), 64)]
                groups = await asyncio.gather(*(chunk(part) for part in chunks))
                return [response for group in groups for response in group]

            return await capture_trove(borrower, rpc=rpc, rpc_many=many)

    try:
        return asyncio.run(run())
    except (OSError, ValueError, httpx.HTTPError) as error:
        raise ValueError("MEZO_TROVE_SOURCE_UNAVAILABLE") from error
