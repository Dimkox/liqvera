"""Private F3 report service: bounded capture request and immutable artifacts."""

from __future__ import annotations

import hmac
import http.client
import os
import re
import stat
import threading
import time
from dataclasses import asdict, replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

from liqvera_evidence_report.canonical import canonical_json_bytes
from liqvera_evidence_report.evidence_bundle import (
    delete_published,
    publish_artifact,
    read_published,
)
from liqvera_evidence_report.evidence_io import EvidenceRejected, identifier, strict_json
from liqvera_evidence_report.product_request import parse_product_request, request_identity
from liqvera_evidence_report.report import build_report
from liqvera_evidence_report.trove_capture import read_trove_package
from liqvera_evidence_report.trove_report import TroveReportRequest, build_trove_report

PUBLIC_CODES = {"MEZO_SOURCE_UNAVAILABLE", "MEZO_DEX_INVALID_EVIDENCE", "INVALID_INPUT", "INVALID_DATASET", "SOURCE_UNAVAILABLE", "STALE_SOURCE",
                "CLOCK_SKEW", "IDENTITY_UNVERIFIED", "IDENTITY_MISMATCH", "CROSSED_BOOK",
                "DEPTH_INSUFFICIENT", "UNSUPPORTED_INSTRUMENT", "ARTIFACT_INTEGRITY_FAILED",
                "STORAGE_UNAVAILABLE", "REPORT_ALREADY_EXISTS"}



def require_mezo_source(built) -> None:
    """Fresh enabled builds cannot silently return Hyperliquid-only evidence."""
    if ("source/mezo-dex.json" not in built.input_members
            or "mezo-dex/capture.json" not in built.extra_members
            or "mezo_dex" not in built.document):
        raise EvidenceRejected("MEZO_SOURCE_UNAVAILABLE")

def build_trove_product(path: Path, request: TroveReportRequest, *, created_at_ms: int):
    capture = read_trove_package(path, path.name)
    built = build_trove_report(capture, replace(request, created_at_ms=created_at_ms))
    if built.document["quality"]["snapshot_status"] != "VALID_FOR_SNAPSHOT_CALCULATION":
        raise EvidenceRejected("STALE_SOURCE")
    return built


def _internal_token(path: str) -> str:
    """Load one narrowly scoped internal credential without logging its value."""
    try:
        if not path or not Path(path).is_absolute():
            raise ValueError()
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise ValueError()
            raw = stream.read(258)
        # Secret managers commonly append one LF; other surrounding whitespace
        # and embedded controls are not token normalization rules.
        token = raw.removesuffix(b"\n")
        if not 32 <= len(token) <= 256 or any(byte < 33 or byte > 126 for byte in token):
            raise ValueError()
        return token.decode("ascii")
    except (OSError, ValueError, UnicodeError):
        raise ValueError("invalid internal authentication configuration") from None


def _capture(origin: str, capture_id: str, timeout: float, *, mezo_request: dict | None = None, trove_request: dict | None = None) -> dict:
    url = urlsplit(origin)
    if (url.scheme != "http" or url.hostname not in {"evidence-capture", "127.0.0.1", "localhost"}
            or url.path not in {"", "/"} or url.query or url.fragment or url.username or url.password
            or url.port not in {None, 8081}):
        raise EvidenceRejected("SOURCE_UNAVAILABLE")
    client = http.client.HTTPConnection(url.hostname, url.port or 8081, timeout=timeout)
    try:
        client.request("POST", "/internal/v1/captures", body=canonical_json_bytes({"capture_id": capture_id, **({"mezo_dex": mezo_request} if mezo_request is not None else {}), **({"trove_risk": trove_request} if trove_request is not None else {})}),
                       headers={"Content-Type": "application/json", "Connection": "close"})
        response = client.getresponse()
        raw = response.read(16385)
        if len(raw) > 16384 or response.status != 201:
            if len(raw) <= 16384:
                failure = strict_json(raw)
                if type(failure) is dict and failure.get("code") == "MEZO_SOURCE_UNAVAILABLE":
                    raise EvidenceRejected("MEZO_SOURCE_UNAVAILABLE")
            raise EvidenceRejected("SOURCE_UNAVAILABLE")
        value = strict_json(raw)
        if (type(value) is not dict or set(value) != {"capture_id", "source_mode", "identity_status"}
                or value["capture_id"] != capture_id):
            raise EvidenceRejected("SOURCE_UNAVAILABLE")
        return value
    except (OSError, http.client.HTTPException) as error:
        raise EvidenceRejected("SOURCE_UNAVAILABLE") from error
    finally:
        client.close()


def main() -> int:
    forbidden = ("SECRET", "TOKEN", "PASSWORD", "PRIVATE", "WALLET", "SIGNER", "API_KEY",
                 "APIKEY", "DATABASE", "PAY_TO", "FACILITATOR", "RPC_URL")
    if any(any(marker in key.upper() for marker in forbidden)
           for key in os.environ if key != "LIQVERA_INTERNAL_TOKEN_FILE"):
        raise ValueError("report service must not receive gateway credentials or payment configuration")
    internal_token = _internal_token(os.environ.get("LIQVERA_INTERNAL_TOKEN_FILE", ""))
    capture_root = Path(os.environ.get("LIQVERA_CAPTURE_ROOT", "/var/lib/liqvera/captures"))
    artifact_root = Path(os.environ.get("LIQVERA_ARTIFACT_ROOT", "/var/lib/liqvera/artifacts"))
    engine_commit = os.environ.get("LIQVERA_ENGINE_COMMIT", "")
    mode = os.environ.get("LIQVERA_SOURCE_MODE", "fixture")
    capture_url = os.environ.get("LIQVERA_CAPTURE_URL", "http://evidence-capture:8081")
    if (not re.fullmatch(r"[0-9a-f]{40}", engine_commit) or mode not in {"fixture", "live-public"}
            or any(not path.is_absolute() or path.is_symlink() for path in (capture_root, artifact_root))):
        raise ValueError("invalid report service configuration")
    artifact_root.mkdir(parents=True, exist_ok=True)
    dex_enabled = os.environ.get("LIQVERA_MEZO_DEX_ENABLED", "false")
    if dex_enabled not in {"true", "false"} or (dex_enabled == "true" and mode != "live-public"):
        raise ValueError("invalid Mezo DEX source configuration")
    troves_enabled = os.environ.get("LIQVERA_MEZO_TROVES_ENABLED", "false")
    if troves_enabled not in {"true", "false"} or (troves_enabled == "true" and mode != "live-public"):
        raise ValueError("invalid Mezo Trove source configuration")
    active: set[str] = set()
    active_lock = threading.Lock()

    class Server(ThreadingHTTPServer):
        daemon_threads = True
        request_queue_size = 16
        slots = threading.BoundedSemaphore(4)

        def process_request(self, request, client_address) -> None:
            if not self.slots.acquire(blocking=False):
                try:
                    request.sendall(b"HTTP/1.1 503 Service Unavailable\r\nConnection: close\r\nContent-Length: 0\r\n\r\n")
                finally:
                    self.shutdown_request(request)
                return
            try:
                super().process_request(request, client_address)
            except BaseException:
                self.slots.release()
                raise

        def process_request_thread(self, request, client_address) -> None:
            try:
                super().process_request_thread(request, client_address)
            finally:
                self.slots.release()

    class Handler(BaseHTTPRequestHandler):
        server_version = "LiqveraReport"
        sys_version = ""

        def setup(self) -> None:
            super().setup()
            self.connection.settimeout(3)

        def log_message(self, format: str, *args: object) -> None:
            pass

        def authorized(self) -> bool:
            values = self.headers.get_all("Authorization", [])
            if (len(values) != 1 or not values[0].isascii()
                    or not hmac.compare_digest(values[0], "Bearer " + internal_token)):
                self.reply(401, {"code": "UNAUTHORIZED", "retryable": False})
                return False
            return True

        def reply(self, status: int, document: dict) -> None:
            raw = canonical_json_bytes(document)
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "private, no-store")
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(raw)
            self.close_connection = True

        def do_GET(self) -> None:
            if self.path == "/healthz":
                self.reply(200, {"status": "ok"})
            elif self.path == "/readyz":
                ready = capture_root.is_dir() and artifact_root.is_dir() and os.access(artifact_root, os.W_OK)
                self.reply(200 if ready else 503, {"ready": ready, "source_mode": mode,
                    "payment_ready": False, "live_identity_approved": False,
                    "blockers": ["IDENTITY_UNVERIFIED"] if mode == "live-public" else ["SIMULATED_SOURCE"]})
            else:
                self.reply(404, {"code": "NOT_FOUND", "retryable": False})

        def do_POST(self) -> None:
            if self.path != "/internal/v1/reports":
                self.reply(404, {"code": "NOT_FOUND", "retryable": False})
                return
            if not self.authorized():
                return
            report_id = None
            acquired = False
            try:
                lengths = self.headers.get_all("Content-Length", [])
                if (len(lengths) != 1 or not lengths[0].isascii() or not lengths[0].isdigit()
                        or self.headers.get("Transfer-Encoding") is not None
                        or self.headers.get_content_type() != "application/json"
                        or not 1 <= int(lengths[0]) <= 16384):
                    raise EvidenceRejected("INVALID_INPUT")
                raw = self.rfile.read(int(lengths[0]))
                if len(raw) != int(lengths[0]):
                    raise EvidenceRejected("INVALID_INPUT")
                request = parse_product_request(strict_json(raw), engine_commit=engine_commit,
                                                created_at_ms=time.time_ns() // 1_000_000)
                report_id = str(request.report_id)
                with active_lock:
                    if report_id in active:
                        self.reply(409, {"code": "BUILD_IN_PROGRESS", "retryable": True})
                        return
                    active.add(report_id)
                    acquired = True
                deadline = time.monotonic() + 15
                # Existing report IDs retain immutable historical bytes, including
                # pre-extension reports. The requirement applies to fresh builds.
                if os.path.lexists(artifact_root / report_id):
                    built, artifact = read_published(artifact_root, report_id)
                    if built.document["request"] != request_identity(request):
                        raise EvidenceRejected("REPORT_ALREADY_EXISTS")
                    if built.document["source"]["source_mode"] != mode:
                        raise EvidenceRejected("INVALID_DATASET")
                else:
                    capture_id = str(uuid4())
                    trove = type(request) is TroveReportRequest
                    if trove:
                        if troves_enabled != "true":
                            raise EvidenceRejected("UNSUPPORTED_INSTRUMENT")
                        capture = _capture(capture_url, capture_id, 12.5,
                                           trove_request={"borrower": request.borrower})
                    elif dex_enabled == "true":
                        from fractions import Fraction
                        quantity = Fraction(str(request.quantity_base)) * 10**18
                        capture = _capture(capture_url, capture_id, 12.5, mezo_request={
                            "side": request.side.value, "quantity_wei": str(quantity.numerator)})
                    else:
                        capture = _capture(capture_url, capture_id, 12.5)
                    if capture["source_mode"] != mode:
                        raise EvidenceRejected("INVALID_DATASET")
                    built = (build_trove_product(capture_root / capture_id, request,
                                                 created_at_ms=time.time_ns() // 1_000_000)
                             if trove else build_report(capture_root / capture_id, request))
                    if not trove and dex_enabled == "true":
                        require_mezo_source(built)
                    if built.document["source"]["source_mode"] != mode:
                        raise EvidenceRejected("INVALID_DATASET")
                    if time.monotonic() >= deadline:
                        raise EvidenceRejected("SOURCE_UNAVAILABLE")
                    artifact = publish_artifact(artifact_root, built)
                if time.monotonic() >= deadline:
                    raise EvidenceRejected("SOURCE_UNAVAILABLE")
                self.reply(200, {**asdict(artifact),
                    "snapshot_at": built.document["source"]["source_at"],
                    "created_at": built.document["source"]["created_at"],
                    "source_mode": built.document["source"]["source_mode"],
                    "snapshot_status": built.document["quality"]["snapshot_status"],
                    "limitations": built.document["quality"]["limitations"]})
            except EvidenceRejected as error:
                code = error.code if error.code in PUBLIC_CODES else "INVALID_DATASET"
                status = 503 if code in {"MEZO_SOURCE_UNAVAILABLE", "SOURCE_UNAVAILABLE", "STORAGE_UNAVAILABLE", "ARTIFACT_INTEGRITY_FAILED"} else 422
                self.reply(status, {"code": code, "retryable": False})
            except FileExistsError:
                self.reply(409, {"code": "REPORT_ALREADY_EXISTS", "retryable": False})
            except (OSError, ValueError, TypeError, KeyError):
                self.reply(503, {"code": "STORAGE_UNAVAILABLE", "retryable": False})
            finally:
                if acquired:
                    with active_lock:
                        active.discard(report_id)

        def do_DELETE(self) -> None:
            if not self.authorized():
                return
            prefix = "/internal/v1/reports/"
            report_id = None
            acquired = False
            try:
                if not self.path.startswith(prefix):
                    self.reply(404, {"code": "NOT_FOUND", "retryable": False})
                    return
                # Do not percent-decode, normalize traversal, accept query
                # parameters, or consume a caller-supplied filesystem path.
                report_id = identifier(self.path[len(prefix):])
                lengths = self.headers.get_all("Content-Length", [])
                if (self.headers.get("Transfer-Encoding") is not None
                        or lengths not in ([], ["0"])):
                    raise EvidenceRejected("INVALID_INPUT")
                with active_lock:
                    if report_id in active:
                        self.reply(409, {"code": "BUILD_IN_PROGRESS", "retryable": True})
                        return
                    active.add(report_id)
                    acquired = True
                deleted = delete_published(artifact_root, report_id)
                self.reply(200, {"report_id": report_id, "deleted": deleted})
            except EvidenceRejected as error:
                status = 400 if error.code == "INVALID_INPUT" else 409
                self.reply(status, {"code": error.code, "retryable": False})
            except FileExistsError:
                self.reply(409, {"code": "BUILD_IN_PROGRESS", "retryable": True})
            except OSError:
                self.reply(503, {"code": "STORAGE_UNAVAILABLE", "retryable": False})
            finally:
                if acquired:
                    with active_lock:
                        active.discard(report_id)

    server = Server((os.environ.get("LIQVERA_REPORT_HOST", "0.0.0.0"),
                     int(os.environ.get("LIQVERA_REPORT_PORT", "8082"))), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
