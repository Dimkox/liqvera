"""Private F3 report service: bounded capture request and immutable artifacts."""

from __future__ import annotations

import http.client
import os
import re
import threading
import time
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

from mee_evidence_report.canonical import canonical_json_bytes
from mee_evidence_report.evidence_bundle import publish_artifact, read_published
from mee_evidence_report.evidence_io import EvidenceRejected, strict_json
from mee_evidence_report.report import build_report, parse_request

PUBLIC_CODES = {"INVALID_INPUT", "INVALID_DATASET", "SOURCE_UNAVAILABLE", "STALE_SOURCE",
                "CLOCK_SKEW", "IDENTITY_UNVERIFIED", "IDENTITY_MISMATCH", "CROSSED_BOOK",
                "DEPTH_INSUFFICIENT", "UNSUPPORTED_INSTRUMENT", "ARTIFACT_INTEGRITY_FAILED",
                "STORAGE_UNAVAILABLE", "REPORT_ALREADY_EXISTS"}


def _capture(origin: str, capture_id: str, timeout: float) -> dict:
    url = urlsplit(origin)
    if (url.scheme != "http" or url.hostname not in {"evidence-capture", "127.0.0.1", "localhost"}
            or url.path not in {"", "/"} or url.query or url.fragment or url.username or url.password
            or url.port not in {None, 8081}):
        raise EvidenceRejected("SOURCE_UNAVAILABLE")
    client = http.client.HTTPConnection(url.hostname, url.port or 8081, timeout=timeout)
    try:
        client.request("POST", "/internal/v1/captures", body=canonical_json_bytes({"capture_id": capture_id}),
                       headers={"Content-Type": "application/json", "Connection": "close"})
        response = client.getresponse()
        raw = response.read(16385)
        if len(raw) > 16384 or response.status != 201:
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
    if any(any(marker in key.upper() for marker in forbidden) for key in os.environ):
        raise ValueError("report service must not receive gateway credentials or payment configuration")
    capture_root = Path(os.environ.get("LIQVERA_CAPTURE_ROOT", "/var/lib/liqvera/captures"))
    artifact_root = Path(os.environ.get("LIQVERA_ARTIFACT_ROOT", "/var/lib/liqvera/artifacts"))
    engine_commit = os.environ.get("LIQVERA_ENGINE_COMMIT", "")
    mode = os.environ.get("LIQVERA_SOURCE_MODE", "fixture")
    capture_url = os.environ.get("LIQVERA_CAPTURE_URL", "http://evidence-capture:8081")
    if (not re.fullmatch(r"[0-9a-f]{40}", engine_commit) or mode not in {"fixture", "live-public"}
            or any(not path.is_absolute() or path.is_symlink() for path in (capture_root, artifact_root))):
        raise ValueError("invalid report service configuration")
    artifact_root.mkdir(parents=True, exist_ok=True)
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
                request = parse_request(strict_json(raw), engine_commit=engine_commit)
                report_id = str(request.report_id)
                with active_lock:
                    if report_id in active:
                        self.reply(409, {"code": "BUILD_IN_PROGRESS", "retryable": True})
                        return
                    active.add(report_id)
                    acquired = True
                deadline = time.monotonic() + 15
                if os.path.lexists(artifact_root / report_id):
                    built, artifact = read_published(artifact_root, report_id)
                    if built.document["request"] != {"side": request.side.value,
                                                      "quantity_base": str(request.quantity_base)}:
                        raise EvidenceRejected("REPORT_ALREADY_EXISTS")
                    if built.document["source"]["source_mode"] != mode:
                        raise EvidenceRejected("INVALID_DATASET")
                else:
                    capture_id = str(uuid4())
                    capture = _capture(capture_url, capture_id, 12.5)
                    if capture["source_mode"] != mode:
                        raise EvidenceRejected("INVALID_DATASET")
                    built = build_report(capture_root / capture_id, request)
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
                status = 503 if code in {"SOURCE_UNAVAILABLE", "STORAGE_UNAVAILABLE", "ARTIFACT_INTEGRITY_FAILED"} else 422
                self.reply(status, {"code": code, "retryable": False})
            except FileExistsError:
                self.reply(409, {"code": "REPORT_ALREADY_EXISTS", "retryable": False})
            except (OSError, ValueError, TypeError, KeyError):
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
