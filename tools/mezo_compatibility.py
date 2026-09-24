"""Read-only, sanitized evidence for the fixed Liqvera F1 boundary."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import urllib.error
import urllib.request
from http.client import HTTPException
from pathlib import Path

INFO_URL = "https://api.hyperliquid.xyz/info"
RPC_URL = "https://rpc.test.mezo.org"
FACILITATOR_URL = "https://facilitator.vativ.io"
MUSD_ADDRESS = "0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503"
PACKAGES = ("@x402/core", "@x402/evm", "@x402/express", "@x402/paywall")
SDK_VERSION = "2.16.0"
REGISTRY_METADATA = (
    ("@x402/core", "https://registry.npmjs.org/%40x402%2Fcore/2.16.0"),
    ("@x402/evm", "https://registry.npmjs.org/%40x402%2Fevm/2.16.0"),
    ("@x402/express", "https://registry.npmjs.org/%40x402%2Fexpress/2.16.0"),
    ("@x402/paywall", "https://registry.npmjs.org/%40x402%2Fpaywall/2.16.0"),
)
MAX_RESPONSE_BYTES = 2 * 1024 * 1024


class CompatibilityError(ValueError):
    """Carries a stable reason code, never remote data or exception details."""


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise CompatibilityError(reason)


def _validate_boundary(lock: dict) -> None:
    expected = {
        "schema": "liqvera-mezo-compatibility/v1",
        "hyperliquid": {"info_url": INFO_URL, "coin": "BTC", "maximum_levels_per_side": 20},
        "mezo": {
            "network": "eip155:31611",
            "chain_id": 31611,
            "rpc_url": RPC_URL,
            "musd_address": MUSD_ADDRESS,
            "musd_decimals": 18,
            "facilitator_url": FACILITATOR_URL,
        },
        "x402": {
            "version": 2,
            "scheme": "exact",
            "typescript_version": SDK_VERSION,
            "packages": list(PACKAGES),
        },
    }
    _require(isinstance(lock, dict), "COMPATIBILITY_LOCK_INVALID")
    _require(set(lock) == {*expected, "payment_readiness"}, "COMPATIBILITY_LOCK_INVALID")
    # Canonical comparison also rejects bool/float substitutions for integer pins.
    try:
        actual = json.dumps({key: lock[key] for key in expected}, sort_keys=True)
    except (TypeError, ValueError):
        raise CompatibilityError("COMPATIBILITY_LOCK_INVALID") from None
    _require(actual == json.dumps(expected, sort_keys=True), "COMPATIBILITY_LOCK_INVALID")


def _validate_payment_policy(lock: dict) -> None:
    policy = lock.get("payment_readiness")
    _require(isinstance(policy, dict), "PAY_TO_POLICY_UNSAFE")
    _require(
        set(policy)
        == {
            "pay_to_required",
            "pay_to_source",
            "default_pay_to_forbidden",
            "finality_policy_status",
        }
        and policy.get("pay_to_required") is True
        and policy.get("pay_to_source") == "operator_environment"
        and policy.get("default_pay_to_forbidden") is True,
        "PAY_TO_POLICY_UNSAFE",
    )
    _require(policy.get("finality_policy_status") == "UNVERIFIED", "FINALITY_POLICY_UNSUPPORTED")


def validate_lock(lock: dict) -> None:
    """Reject any reconfiguration before the CLI performs external reads."""
    _validate_boundary(lock)
    _validate_payment_policy(lock)


def _hex_equals(value: object, expected: int) -> bool:
    return (
        isinstance(value, str)
        and re.fullmatch(r"0x[0-9a-fA-F]{1,64}", value) is not None
        and int(value, 16) == expected
    )


def _supports_musd(value: object) -> bool:
    if not isinstance(value, dict) or not isinstance(value.get("kinds"), list):
        return False
    for kind in value["kinds"]:
        if not isinstance(kind, dict) or not (
            type(kind.get("x402Version")) is int
            and kind["x402Version"] == 2
            and kind.get("scheme") == "exact"
            and kind.get("network") == "eip155:31611"
        ):
            continue
        extra = kind.get("extra")
        if not isinstance(extra, dict) or not isinstance(extra.get("assets"), list):
            continue
        for asset in extra["assets"]:
            if (
                isinstance(asset, dict)
                and isinstance(asset.get("address"), str)
                and asset["address"].lower() == MUSD_ADDRESS.lower()
                and type(asset.get("decimals")) is int
                and asset["decimals"] == 18
            ):
                return True
    return False


def _valid_level(level: object) -> bool:
    if not isinstance(level, dict) or type(level.get("n")) is not int or level["n"] <= 0:
        return False
    for field in ("px", "sz"):
        value = level.get(field)
        if not isinstance(value, str) or re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", value) is None:
            return False
        if not any(character in "123456789" for character in value):
            return False
    return True


def verify_observations(lock: dict, observations: dict) -> dict[str, object]:
    """Validate untrusted observations and return only the approved summary."""
    _validate_boundary(lock)
    _require(isinstance(observations, dict), "OBSERVATIONS_INVALID")
    _require(_hex_equals(observations.get("chain_id"), 31611), "MEZO_CHAIN_ID_MISMATCH")
    code = observations.get("token_code")
    _require(
        isinstance(code, str)
        and re.fullmatch(r"0x(?:[0-9a-fA-F]{2})+", code) is not None
        and any(character != "0" for character in code[2:]),
        "MUSD_CODE_MISSING",
    )
    _require(_hex_equals(observations.get("token_decimals"), 18), "MUSD_DECIMALS_MISMATCH")
    _require(_supports_musd(observations.get("facilitator")), "FACILITATOR_SUPPORT_MISSING")
    meta = observations.get("meta")
    _require(
        isinstance(meta, dict)
        and isinstance(meta.get("universe"), list)
        and any(isinstance(item, dict) and item.get("name") == "BTC" for item in meta["universe"]),
        "HYPERLIQUID_BTC_MISSING",
    )
    book = observations.get("book")
    _require(isinstance(book, dict) and book.get("coin") == "BTC", "HYPERLIQUID_BOOK_INVALID")
    sides = book.get("levels")
    _require(
        isinstance(sides, list)
        and len(sides) == 2
        and all(isinstance(side, list) and len(side) > 0 for side in sides),
        "HYPERLIQUID_BOOK_INVALID",
    )
    _require(all(len(side) <= 20 for side in sides), "HYPERLIQUID_DEPTH_LIMIT_EXCEEDED")
    _require(
        all(_valid_level(level) for side in sides for level in side), "HYPERLIQUID_BOOK_INVALID"
    )
    versions = observations.get("npm_versions")
    _require(
        isinstance(versions, dict) and all(versions.get(name) == SDK_VERSION for name in PACKAGES),
        "X402_SDK_VERSION_MISSING",
    )
    _validate_payment_policy(lock)
    return {
        "schema": "liqvera-mezo-compatibility-result/v1",
        "status": "COMPATIBILITY_PASS_PAYMENT_BLOCKED",
        "network": "eip155:31611",
        "chain_id": 31611,
        "musd_address": MUSD_ADDRESS,
        "musd_decimals": 18,
        "x402_version": 2,
        "scheme": "exact",
        "sdk_version": SDK_VERSION,
        "coin": "BTC",
        "bid_levels": len(sides[0]),
        "ask_levels": len(sides[1]),
        "payment_readiness": "BLOCKED",
        "payment_blockers": ["PAY_TO_MISSING", "FINALITY_RULE_UNVERIFIED"],
    }


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """No endpoint may move a read to a different host or resource."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise CompatibilityError("HTTP_REDIRECT_BLOCKED")


def _build_opener():
    return urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())


def _request_json(opener, url: str, payload: dict | None, reason: str) -> object:
    request = urllib.request.Request(
        url,
        data=None if payload is None else json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Liqvera-Compatibility-Probe/1",
            "Accept-Encoding": "identity",
        },
        method="GET" if payload is None else "POST",
    )
    try:
        with opener.open(request, timeout=12) as response:
            lengths = response.headers.get_all("Content-Length", [])
            encodings = response.headers.get_all("Content-Encoding", [])
            transfers = response.headers.get_all("Transfer-Encoding", [])
            _require(
                not encodings or [value.lower() for value in encodings] == ["identity"], reason
            )
            _require(not transfers or [value.lower() for value in transfers] == ["chunked"], reason)
            _require(not (lengths and transfers), reason)
            expected_length = None
            if lengths:
                _require(
                    len(lengths) == 1 and re.fullmatch(r"[0-9]{1,10}", lengths[0]) is not None,
                    reason,
                )
                expected_length = int(lengths[0])
                _require(expected_length <= MAX_RESPONSE_BYTES, reason)
            body = response.read(MAX_RESPONSE_BYTES + 1)
            _require(expected_length is None or len(body) == expected_length, reason)
        _require(len(body) <= MAX_RESPONSE_BYTES, reason)
        return json.loads(body)
    except (OSError, urllib.error.URLError, HTTPException, ValueError, RecursionError) as error:
        if isinstance(error, CompatibilityError):
            raise
        raise CompatibilityError(reason) from None


def _rpc(opener, method: str, params: list) -> object:
    response = _request_json(
        opener,
        RPC_URL,
        {"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
        "MEZO_RPC_UNAVAILABLE",
    )
    _require(
        isinstance(response, dict)
        and response.get("jsonrpc") == "2.0"
        and type(response.get("id")) is int
        and response["id"] == 1
        and "result" in response
        and "error" not in response,
        "MEZO_RPC_RESPONSE_INVALID",
    )
    return response["result"]


def _registry_versions(opener) -> dict[str, str]:
    """Read literal registry URLs and project only validated package identities."""
    versions = {}
    for package, url in REGISTRY_METADATA:
        response = _request_json(opener, url, None, "X402_REGISTRY_UNAVAILABLE")
        _require(isinstance(response, dict), "X402_SDK_VERSION_MISSING")
        # Registry metadata has other fields; none are retained or interpreted.
        identity = {"name": response.get("name"), "version": response.get("version")}
        _require(identity == {"name": package, "version": SDK_VERSION}, "X402_SDK_VERSION_MISSING")
        versions[package] = SDK_VERSION
    return versions


def collect_observations() -> dict:
    """Fixed read-only requests; callers must publish only the validated summary."""
    opener = _build_opener()
    return {
        "chain_id": _rpc(opener, "eth_chainId", []),
        "token_code": _rpc(opener, "eth_getCode", [MUSD_ADDRESS, "latest"]),
        "token_decimals": _rpc(
            opener,
            "eth_call",
            [{"to": MUSD_ADDRESS, "data": "0x313ce567"}, "latest"],
        ),
        "facilitator": _request_json(
            opener,
            FACILITATOR_URL + "/supported",
            None,
            "FACILITATOR_UNAVAILABLE",
        ),
        "meta": _request_json(opener, INFO_URL, {"type": "meta"}, "HYPERLIQUID_UNAVAILABLE"),
        "book": _request_json(
            opener,
            INFO_URL,
            {"type": "l2Book", "coin": "BTC"},
            "HYPERLIQUID_UNAVAILABLE",
        ),
        "npm_versions": _registry_versions(opener),
    }


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise CompatibilityError("CLI_ARGUMENTS_INVALID")


def _write_result(path: Path, content: str) -> None:
    temporary = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=".compatibility-",
            delete=False,
        ) as output:
            temporary = Path(output.name)
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    except OSError:
        raise CompatibilityError("COMPATIBILITY_OUTPUT_UNAVAILABLE") from None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = _Parser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--lock", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    try:
        args = parser.parse_args(argv)
        try:
            lock = json.loads(args.lock.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raise CompatibilityError("COMPATIBILITY_LOCK_INVALID") from None
        validate_lock(lock)
        result = verify_observations(lock, collect_observations())
        content = json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n"
        if args.output is None:
            sys.stdout.write(content)
        else:
            _write_result(args.output, content)
    except CompatibilityError as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0
