"""Fixed, bounded public Hyperliquid evidence capture; no trading capability."""

from __future__ import annotations

import hashlib
import json
import signal
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from decimal import Decimal

ORIGIN = "https://api.hyperliquid.xyz/info"
MAX_PAYLOAD_BYTES = 2 * 1024 * 1024
CAPTURE_DEADLINE_SECONDS = 12
REQUESTS = {"metadata": b'{"type":"meta"}', "book": b'{"type":"l2Book","coin":"BTC"}'}
FIXTURE_TIME_MS = 1_790_208_000_000
FIXTURE_METADATA = b'{"universe":[{"name":"BTC","szDecimals":5,"maxLeverage":40}]}'
FIXTURE_BOOK = (
    b'{"coin":"BTC","time":1790208000000,"levels":'
    b'[[{"px":"99900","sz":"0.1"},{"px":"99800","sz":"0.1"}],'
    b'[{"px":"100000","sz":"0.1"},{"px":"100100","sz":"0.1"}]]}'
)


class CaptureRejected(ValueError):
    def __init__(self, code: str = "SOURCE_UNAVAILABLE") -> None:
        self.code = code
        super().__init__(code)


def strict_json(raw: bytes) -> object:
    """Reject ambiguous JSON without rounding upstream decimal tokens."""
    def pairs(items: list[tuple[str, object]]) -> dict[str, object]:
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    def invalid(value: str) -> object:
        raise ValueError("non-finite JSON")

    return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                      parse_float=Decimal, parse_constant=invalid)


@dataclass(frozen=True)
class CapturedResponse:
    kind: str
    payload: bytes
    started_at_ms: int
    received_at_ms: int
    elapsed_ns: int
    http_status: int = 200

    def evidence(self, source_mode: str) -> dict[str, object]:
        return {
            "kind": self.kind,
            "origin": ORIGIN,
            "method": "POST",
            "request_body": REQUESTS[self.kind].decode("ascii"),
            "source_mode": source_mode,
            "started_at_ms": self.started_at_ms,
            "received_at_ms": self.received_at_ms,
            "elapsed_ns": self.elapsed_ns,
            "http_status": self.http_status,
            "payload_path": f"source/{self.kind}.bin",
            "payload_sha256": hashlib.sha256(self.payload).hexdigest(),
            "payload_length": len(self.payload),
        }


@contextmanager
def _deadline():
    # The service deliberately runs capture on its main thread. No background
    # network operation is left running after a timeout or disconnect.
    if (threading.current_thread() is not threading.main_thread()
            or not hasattr(signal, "setitimer")
            or signal.getitimer(signal.ITIMER_REAL) != (0.0, 0.0)):
        raise CaptureRejected()
    previous = signal.getsignal(signal.SIGALRM)

    def expired(signum: int, frame: object) -> None:
        raise CaptureRejected()

    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, CAPTURE_DEADLINE_SECONDS)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def capture_responses(source_mode: str) -> tuple[CapturedResponse, CapturedResponse]:
    """Exactly two fixed requests under one deadline; never fixture fallback."""
    if source_mode == "fixture":
        return tuple(CapturedResponse(kind, payload, FIXTURE_TIME_MS, FIXTURE_TIME_MS, 0)
                     for kind, payload in (("metadata", FIXTURE_METADATA), ("book", FIXTURE_BOOK)))
    if source_mode != "live-public":
        raise CaptureRejected("INVALID_INPUT")
    import httpx

    try:
        with _deadline(), httpx.Client(
            trust_env=False, follow_redirects=False, timeout=5.0,
            headers={"Accept-Encoding": "identity", "Content-Type": "application/json"},
        ) as client:
            responses = []
            for kind, request in REQUESTS.items():
                started = time.time_ns() // 1_000_000
                monotonic = time.monotonic_ns()
                with client.stream("POST", ORIGIN, content=request) as response:
                    if response.status_code != 200 or response.headers.get(
                        "content-encoding", "identity"
                    ).lower() != "identity":
                        raise CaptureRejected()
                    content_type = response.headers.get("content-type", "").split(";", 1)[0]
                    if content_type.strip().lower() != "application/json":
                        raise CaptureRejected()
                    declared = response.headers.get("content-length")
                    if declared is not None and (not declared.isascii() or not declared.isdigit()
                                                  or int(declared) > MAX_PAYLOAD_BYTES):
                        raise CaptureRejected()
                    payload = bytearray()
                    for chunk in response.iter_raw():
                        if len(payload) + len(chunk) > MAX_PAYLOAD_BYTES:
                            raise CaptureRejected()
                        payload.extend(chunk)
                received = time.time_ns() // 1_000_000
                elapsed = time.monotonic_ns() - monotonic
                if declared is not None and len(payload) != int(declared):
                    raise CaptureRejected()
                if not payload or received < started:
                    raise CaptureRejected("CLOCK_SKEW")
                strict_json(bytes(payload))
                responses.append(CapturedResponse(kind, bytes(payload), started, received, elapsed))
            return tuple(responses)
    except CaptureRejected:
        raise
    except (httpx.HTTPError, OSError, ValueError, UnicodeError, RecursionError) as error:
        raise CaptureRejected() from error
