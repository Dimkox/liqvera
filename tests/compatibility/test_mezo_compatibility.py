"""Fixed public compatibility checks must never imply payment readiness."""

import io
import json
import runpy
import threading
from http.client import HTTPResponse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPSHandler, Request

import pytest

from tools import mezo_compatibility as compatibility
from tools.mezo_compatibility import CompatibilityError, verify_observations

ROOT = Path(__file__).resolve().parents[2]


def wire_response(body, headers=None):
    """Exercise the real HTTPResponse reader with synthetic wire bytes."""

    class Socket:
        def makefile(self, mode):
            return io.BytesIO(b"HTTP/1.1 200 OK\r\n" + (headers or b"") + b"\r\n" + body)

    response = HTTPResponse(Socket())
    response.begin()
    return response


@pytest.fixture
def lock():
    return json.loads((ROOT / "docs/compatibility/mezo-evidence-v1.json").read_text())


@pytest.fixture
def observations():
    # Synthetic prices/quantities exist only in memory and never enter results.
    return {
        "chain_id": "0x7b7b",
        "token_code": "0x6080604052",
        "token_decimals": "0x12",
        "facilitator": {
            "kinds": [
                {
                    "x402Version": 2,
                    "scheme": "exact",
                    "network": "eip155:31611",
                    "extra": {
                        "assets": [
                            {
                                "address": "0x118917a40faf1cd7a13db0ef56c86de7973ac503",
                                "decimals": 18,
                                "assetTransferMethod": "permit2",
                                "eip712": {"name": "Mezo USD", "version": "1"},
                                "supportsEip2612": True,
                                "symbol": "MUSD",
                            }
                        ],
                    },
                }
            ],
            "extensions": [],
            "signers": {},
        },
        "meta": {"universe": [{"name": "BTC", "szDecimals": 5}]},
        "book": {
            "coin": "BTC",
            "time": 1,
            "levels": [
                [{"px": "100", "sz": "1", "n": 1} for _ in range(20)],
                [{"px": "101", "sz": "2", "n": 1} for _ in range(20)],
            ],
        },
        "npm_versions": {
            "@x402/core": "2.16.0",
            "@x402/evm": "2.16.0",
            "@x402/express": "2.16.0",
            "@x402/paywall": "2.16.0",
        },
    }


def test_technical_compatibility_still_blocks_payment(lock, observations):
    result = verify_observations(lock, observations)
    assert result == {
        "schema": "liqvera-mezo-compatibility-result/v1",
        "status": "COMPATIBILITY_PASS_PAYMENT_BLOCKED",
        "network": "eip155:31611",
        "chain_id": 31611,
        "musd_address": "0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503",
        "musd_decimals": 18,
        "x402_version": 2,
        "scheme": "exact",
        "sdk_version": "2.16.0",
        "coin": "BTC",
        "bid_levels": 20,
        "ask_levels": 20,
        "payment_readiness": "BLOCKED",
        "payment_blockers": ["PAY_TO_MISSING", "FINALITY_RULE_UNVERIFIED"],
    }
    assert result["payment_blockers"] == ["PAY_TO_MISSING", "FINALITY_RULE_UNVERIFIED"]


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        ("wrong_chain", "MEZO_CHAIN_ID_MISMATCH"),
        ("empty_token_code", "MUSD_CODE_MISSING"),
        ("wrong_decimals", "MUSD_DECIMALS_MISMATCH"),
        ("facilitator_mainnet_only", "FACILITATOR_SUPPORT_MISSING"),
        ("missing_btc_meta", "HYPERLIQUID_BTC_MISSING"),
        ("too_many_levels", "HYPERLIQUID_DEPTH_LIMIT_EXCEEDED"),
        ("sdk_version_missing", "X402_SDK_VERSION_MISSING"),
        ("unsafe_pay_to_policy", "PAY_TO_POLICY_UNSAFE"),
        ("invented_finality_policy", "FINALITY_POLICY_UNSUPPORTED"),
    ],
)
def test_incompatible_observations_fail_with_only_reason_code(lock, observations, mutation, reason):
    if mutation == "wrong_chain":
        observations["chain_id"] = "0x7b7c"
    elif mutation == "empty_token_code":
        observations["token_code"] = "0x"
    elif mutation == "wrong_decimals":
        observations["token_decimals"] = "0x6"
    elif mutation == "facilitator_mainnet_only":
        observations["facilitator"]["kinds"][0]["network"] = "eip155:31612"
    elif mutation == "missing_btc_meta":
        observations["meta"] = {"universe": [{"name": "ETH", "szDecimals": 4}]}
    elif mutation == "too_many_levels":
        observations["book"]["levels"][0].append({"px": "100", "sz": "1", "n": 1})
    elif mutation == "sdk_version_missing":
        del observations["npm_versions"]["@x402/paywall"]
    elif mutation == "unsafe_pay_to_policy":
        lock["payment_readiness"]["default_pay_to_forbidden"] = False
    elif mutation == "invented_finality_policy":
        lock["payment_readiness"]["finality_policy_status"] = "ONE_CONFIRMATION"
    with pytest.raises(CompatibilityError) as error:
        verify_observations(lock, observations)
    assert str(error.value) == reason


@pytest.mark.parametrize(
    ("section", "key", "value"),
    [
        (None, "schema", "wrong"),
        ("mezo", "network", "eip155:31612"),
        ("mezo", "rpc_url", "https://untrusted.invalid"),
        ("mezo", "musd_address", "0x0000000000000000000000000000000000000000"),
        ("hyperliquid", "coin", "ETH"),
        ("hyperliquid", "maximum_levels_per_side", 21),
        ("x402", "typescript_version", "latest"),
        ("x402", "packages", ["untrusted-package"]),
    ],
)
def test_lock_cannot_reconfigure_probe(lock, observations, section, key, value):
    (lock if section is None else lock[section])[key] = value
    with pytest.raises(CompatibilityError, match="^COMPATIBILITY_LOCK_INVALID$"):
        verify_observations(lock, observations)


@pytest.mark.parametrize("code", [None, "", "0x", "0x0", "0x00", "0xzz", "0x123"])
def test_missing_or_malformed_bytecode_fails_closed(lock, observations, code):
    observations["token_code"] = code
    with pytest.raises(CompatibilityError, match="^MUSD_CODE_MISSING$"):
        verify_observations(lock, observations)


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("chain_id", 31611, "MEZO_CHAIN_ID_MISMATCH"),
        ("chain_id", "31611", "MEZO_CHAIN_ID_MISMATCH"),
        ("token_decimals", 18, "MUSD_DECIMALS_MISMATCH"),
        ("facilitator", {"kinds": None}, "FACILITATOR_SUPPORT_MISSING"),
        ("meta", {"universe": None}, "HYPERLIQUID_BTC_MISSING"),
        ("book", {"coin": "BTC", "levels": [[]]}, "HYPERLIQUID_BOOK_INVALID"),
        ("book", {"coin": "ETH", "levels": [[], []]}, "HYPERLIQUID_BOOK_INVALID"),
        ("book", {"coin": "BTC", "levels": [[], []]}, "HYPERLIQUID_BOOK_INVALID"),
        ("book", {"coin": "BTC", "levels": [[None], [None]]}, "HYPERLIQUID_BOOK_INVALID"),
        ("npm_versions", None, "X402_SDK_VERSION_MISSING"),
    ],
)
def test_malformed_observations_are_sanitized(lock, observations, field, value, reason):
    observations[field] = value
    with pytest.raises(CompatibilityError) as error:
        verify_observations(lock, observations)
    assert str(error.value) == reason


@pytest.mark.parametrize(
    "extra",
    [
        {"assets": [{"address": "0x0000000000000000000000000000000000000000", "decimals": 18}]},
        {"assets": [{"address": "0x118917a40faf1cd7a13db0ef56c86de7973ac503", "decimals": 6}]},
        {},
    ],
)
def test_facilitator_must_advertise_locked_asset_and_decimals(lock, observations, extra):
    observations["facilitator"]["kinds"][0]["extra"] = extra
    with pytest.raises(CompatibilityError, match="^FACILITATOR_SUPPORT_MISSING$"):
        verify_observations(lock, observations)


def test_lock_cannot_include_receiver(lock, observations):
    lock["payment_readiness"]["pay_to"] = "forbidden-receiver"
    with pytest.raises(CompatibilityError, match="^PAY_TO_POLICY_UNSAFE$"):
        verify_observations(lock, observations)


def test_cli_stdout_is_canonical_sanitized_json(lock, observations, monkeypatch, capsys):
    monkeypatch.setattr(compatibility, "collect_observations", lambda: observations, raising=False)
    entrypoint = runpy.run_path(str(ROOT / "scripts/check-mezo-compatibility.py"))
    assert (
        entrypoint["main"](["--lock", str(ROOT / "docs/compatibility/mezo-evidence-v1.json")]) == 0
    )
    captured = capsys.readouterr()
    expected = verify_observations(lock, observations)
    assert captured.out == json.dumps(expected, sort_keys=True, separators=(",", ":")) + "\n"
    assert captured.err == ""


def test_cli_atomically_publishes_only_sanitized_result(lock, observations, monkeypatch, tmp_path):
    monkeypatch.setattr(compatibility, "collect_observations", lambda: observations, raising=False)
    target = tmp_path / "evidence" / "result.json"
    args = [
        "--lock",
        str(ROOT / "docs/compatibility/mezo-evidence-v1.json"),
        "--output",
        str(target),
    ]
    assert compatibility.main(args) == 0
    assert (
        target.read_text()
        == json.dumps(
            verify_observations(lock, observations), sort_keys=True, separators=(",", ":")
        )
        + "\n"
    )
    assert list(target.parent.iterdir()) == [target]


def test_cli_rejects_modified_lock_before_network(lock, monkeypatch, tmp_path, capsys):
    def forbidden():
        pytest.fail("invalid lock reached external reads")

    monkeypatch.setattr(compatibility, "collect_observations", forbidden, raising=False)
    lock["mezo"]["rpc_url"] = "https://untrusted.invalid/PRIVATE-MARKER"
    source = tmp_path / "lock.json"
    source.write_text(json.dumps(lock))
    target = tmp_path / "result.json"
    assert compatibility.main(["--lock", str(source), "--output", str(target)]) == 1
    assert capsys.readouterr().err == "COMPATIBILITY_LOCK_INVALID\n"
    assert not target.exists()


@pytest.mark.parametrize(
    "args",
    [
        [],
        ["--lock", "absent", "--url", "PRIVATE-MARKER"],
        ["--lock", "absent", "--network", "eip155:31612"],
        ["--lock", "absent", "--body", "PRIVATE-MARKER"],
        ["--lock", "absent", "--coin", "ETH"],
        ["--lock", "absent", "--asset", "PRIVATE-MARKER"],
        ["--lock", "absent", "--npm-version", "latest"],
        ["--lo", "absent"],
    ],
)
def test_cli_argument_errors_never_echo_input(args, capsys):
    assert compatibility.main(args) == 1
    captured = capsys.readouterr()
    assert captured.err == "CLI_ARGUMENTS_INVALID\n"
    assert captured.out == ""


def test_cli_external_failure_creates_no_result(monkeypatch, tmp_path, capsys):
    def unavailable():
        raise CompatibilityError("MEZO_RPC_UNAVAILABLE")

    monkeypatch.setattr(compatibility, "collect_observations", unavailable, raising=False)
    target = tmp_path / "result.json"
    assert (
        compatibility.main(
            [
                "--lock",
                str(ROOT / "docs/compatibility/mezo-evidence-v1.json"),
                "--output",
                str(target),
            ]
        )
        == 1
    )
    captured = capsys.readouterr()
    assert captured.err == "MEZO_RPC_UNAVAILABLE\n"
    assert captured.out == ""
    assert not target.exists()


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
def test_all_redirects_fail_without_exposing_location(status):
    handler = compatibility.NoRedirect()
    with pytest.raises(CompatibilityError, match="^HTTP_REDIRECT_BLOCKED$"):
        handler.redirect_request(
            Request("https://rpc.test.mezo.org"),
            None,
            status,
            "PRIVATE-MARKER",
            {},
            "https://untrusted.invalid/PRIVATE-MARKER",
        )


def test_collect_uses_only_fixed_readonly_requests(observations, monkeypatch):
    replies = [
        {"jsonrpc": "2.0", "id": 1, "result": observations["chain_id"]},
        {"jsonrpc": "2.0", "id": 1, "result": observations["token_code"]},
        {"jsonrpc": "2.0", "id": 1, "result": observations["token_decimals"]},
        observations["facilitator"],
        observations["meta"],
        observations["book"],
        {"name": "@x402/core", "version": "2.16.0"},
        {"name": "@x402/evm", "version": "2.16.0"},
        {"name": "@x402/express", "version": "2.16.0"},
        {"name": "@x402/paywall", "version": "2.16.0"},
    ]
    requests = []

    class Opener:
        def open(self, request, timeout):
            assert timeout == 12
            requests.append(
                (request.full_url, request.method, request.data, dict(request.header_items()))
            )
            return wire_response(json.dumps(replies[len(requests) - 1]).encode())

    def build_opener(*handlers):
        assert any(isinstance(handler, compatibility.NoRedirect) for handler in handlers)
        return Opener()

    monkeypatch.setattr(compatibility.urllib.request, "build_opener", build_opener)
    assert compatibility.collect_observations() == observations
    assert [
        (url, method, json.loads(body) if body else None) for url, method, body, _ in requests
    ] == [
        (
            "https://rpc.test.mezo.org",
            "POST",
            {"jsonrpc": "2.0", "id": 1, "method": "eth_chainId", "params": []},
        ),
        (
            "https://rpc.test.mezo.org",
            "POST",
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "eth_getCode",
                "params": ["0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503", "latest"],
            },
        ),
        (
            "https://rpc.test.mezo.org",
            "POST",
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "eth_call",
                "params": [
                    {"to": "0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503", "data": "0x313ce567"},
                    "latest",
                ],
            },
        ),
        ("https://facilitator.vativ.io/supported", "GET", None),
        ("https://api.hyperliquid.xyz/info", "POST", {"type": "meta"}),
        ("https://api.hyperliquid.xyz/info", "POST", {"type": "l2Book", "coin": "BTC"}),
        ("https://registry.npmjs.org/%40x402%2Fcore/2.16.0", "GET", None),
        ("https://registry.npmjs.org/%40x402%2Fevm/2.16.0", "GET", None),
        ("https://registry.npmjs.org/%40x402%2Fexpress/2.16.0", "GET", None),
        ("https://registry.npmjs.org/%40x402%2Fpaywall/2.16.0", "GET", None),
    ]
    assert all(headers["User-agent"] == "Liqvera-Compatibility-Probe/1" for *_, headers in requests)
    assert all(headers["Accept-encoding"] == "identity" for *_, headers in requests)


@pytest.mark.parametrize(
    "error",
    [
        URLError("PRIVATE-MARKER"),
        TimeoutError("PRIVATE-MARKER"),
        HTTPError("https://private.invalid", 403, "PRIVATE-MARKER", {}, None),
    ],
)
def test_transport_errors_are_sanitized(error):
    class Opener:
        def open(self, request, timeout):
            raise error

    with pytest.raises(CompatibilityError, match="^MEZO_RPC_UNAVAILABLE$"):
        compatibility._request_json(
            Opener(), "https://rpc.test.mezo.org", {}, "MEZO_RPC_UNAVAILABLE"
        )


@pytest.mark.parametrize(
    "body", [b"PRIVATE-MARKER", b"x" * (2 * 1024 * 1024 + 1)], ids=["invalid-json", "oversized"]
)
def test_invalid_or_oversized_remote_json_is_sanitized(body):
    class Opener:
        def open(self, request, timeout):
            return wire_response(body)

    with pytest.raises(CompatibilityError, match="^MEZO_RPC_UNAVAILABLE$"):
        compatibility._request_json(
            Opener(), "https://rpc.test.mezo.org", {}, "MEZO_RPC_UNAVAILABLE"
        )


@pytest.mark.parametrize(
    "metadata",
    [
        None,
        [],
        {},
        {"version": "2.16.0"},
        {"name": "@x402/core", "version": "latest"},
        {"name": "@x402/evm", "version": "2.16.0"},
        {"name": "@x402/core", "version": ["2.16.0"]},
    ],
)
def test_registry_metadata_must_identify_exact_package_and_version(metadata):
    class Opener:
        def open(self, request, timeout):
            return wire_response(json.dumps(metadata).encode())

    with pytest.raises(CompatibilityError, match="^X402_SDK_VERSION_MISSING$"):
        compatibility._registry_versions(Opener())


def test_registry_failure_is_sanitized():
    class Opener:
        def open(self, request, timeout):
            raise URLError("PRIVATE-MARKER")

    with pytest.raises(CompatibilityError, match="^X402_REGISTRY_UNAVAILABLE$"):
        compatibility._registry_versions(Opener())


def test_ambient_proxy_credentials_never_reach_transport(monkeypatch):
    proxy_user = "synthetic-user"
    proxy_marker = "synthetic-marker"
    proxy_url = "http://" + proxy_user + ":" + proxy_marker + "@proxy.invalid:8080"
    for name in ("https_proxy", "HTTPS_PROXY"):
        monkeypatch.setenv(name, proxy_url)
    monkeypatch.setenv("no_proxy", "")
    monkeypatch.setenv("NO_PROXY", "")
    requests = []
    original = compatibility.urllib.request.build_opener

    class CaptureHTTPS(HTTPSHandler):
        def https_open(self, request):
            requests.append((request.host, request.get_header("Proxy-authorization")))
            raise CompatibilityError("TEST_TRANSPORT_STOP")

    def build_opener(*handlers):
        return original(*handlers, CaptureHTTPS())

    monkeypatch.setattr(compatibility.urllib.request, "build_opener", build_opener)
    with pytest.raises(CompatibilityError, match="^TEST_TRANSPORT_STOP$"):
        compatibility.collect_observations()
    assert requests == [("rpc.test.mezo.org", None)]


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
def test_real_redirect_never_contacts_target(status):
    visits = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            visits.append(self.path)
            self.send_response(status if self.path == "/registry" else 200)
            self.send_header("Location", "/target")
            self.send_header("Content-Length", "0")
            self.end_headers()

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with pytest.raises(CompatibilityError, match="^HTTP_REDIRECT_BLOCKED$"):
                compatibility._request_json(
                    compatibility._build_opener(),
                    f"http://127.0.0.1:{server.server_port}/registry",
                    None,
                    "X402_REGISTRY_UNAVAILABLE",
                )
            assert visits == ["/registry"]
        finally:
            server.shutdown()
            thread.join(timeout=2)


@pytest.mark.parametrize(
    "headers",
    [
        b"Content-Length: 20\r\n",
        b"Content-Length: -1\r\n",
        b"Content-Length: invalid\r\n",
        b"Content-Length: 2097153\r\n",
        b"Content-Length: 2\r\nContent-Length: 20\r\n",
        b"Content-Encoding: gzip\r\n",
        b"Transfer-Encoding: gzip\r\n",
        b"Content-Length: 2\r\nTransfer-Encoding: chunked\r\n",
    ],
)
def test_real_http_response_rejects_incomplete_or_ambiguous_framing(headers):
    class Opener:
        def open(self, request, timeout):
            return wire_response(b"{}", headers)

    with pytest.raises(CompatibilityError, match="^MEZO_RPC_UNAVAILABLE$"):
        compatibility._request_json(
            Opener(), "https://rpc.test.mezo.org", {}, "MEZO_RPC_UNAVAILABLE"
        )


@pytest.mark.parametrize(
    "body,headers",
    [
        (b"{}", b"Content-Length: 2\r\n"),
        (b"{}", b"Content-Encoding: identity\r\n"),
        (b"2\r\n{}\r\n0\r\n\r\n", b"Transfer-Encoding: chunked\r\n"),
    ],
)
def test_real_http_response_accepts_complete_identity_payload(body, headers):
    class Opener:
        def open(self, request, timeout):
            return wire_response(body, headers)

    assert (
        compatibility._request_json(
            Opener(),
            "https://rpc.test.mezo.org",
            {},
            "MEZO_RPC_UNAVAILABLE",
        )
        == {}
    )


def test_truncated_http_response_is_sanitized():
    from http.client import IncompleteRead

    class Opener:
        def open(self, request, timeout):
            raise IncompleteRead(b"PRIVATE-MARKER")

    with pytest.raises(CompatibilityError, match="^MEZO_RPC_UNAVAILABLE$"):
        compatibility._request_json(
            Opener(), "https://rpc.test.mezo.org", {}, "MEZO_RPC_UNAVAILABLE"
        )


def test_failed_atomic_output_preserves_existing_file_and_cleans_temp(
    monkeypatch, tmp_path, capsys
):
    target = tmp_path / "result.json"
    target.write_text("previous-sanitized-evidence\n")

    def unavailable(*args):
        raise OSError("PRIVATE-MARKER")

    monkeypatch.setattr(compatibility.os, "replace", unavailable)
    with pytest.raises(CompatibilityError, match="^COMPATIBILITY_OUTPUT_UNAVAILABLE$"):
        compatibility._write_result(target, "new-sanitized-evidence\n")
    assert target.read_text() == "previous-sanitized-evidence\n"
    assert list(tmp_path.iterdir()) == [target]
    assert capsys.readouterr().err == ""
