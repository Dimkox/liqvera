"""Private fixed-source capture HTTP adapter; run on an isolated network."""

from __future__ import annotations

import json
import os
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from uuid import UUID

from mee_public_capture.config import load_public_configuration
from mee_public_capture.evidence_capture import CaptureRejected, strict_json
from mee_public_capture.evidence_package import capture_package


def main() -> int:
    # Preserve the inherited credential-name guard and additionally refuse
    # gateway/payment configuration rather than filtering it out silently.
    load_public_configuration()
    if any(any(marker in key.upper() for marker in ("DATABASE", "PAY_TO", "FACILITATOR", "RPC_URL"))
           for key in os.environ):
        raise ValueError("capture must not receive gateway configuration")
    root = Path(os.environ.get("LIQVERA_CAPTURE_ROOT", "/var/lib/liqvera/captures"))
    mode = os.environ.get("LIQVERA_SOURCE_MODE", "fixture")
    if mode not in {"fixture", "live-public"} or not root.is_absolute() or root.is_symlink():
        raise ValueError("invalid capture configuration")
    root.mkdir(parents=True, exist_ok=True)

    class Handler(BaseHTTPRequestHandler):
        server_version = "LiqveraCapture"
        sys_version = ""

        def setup(self) -> None:
            super().setup()
            self.connection.settimeout(3)

        def log_message(self, format: str, *args: object) -> None:
            pass  # Do not log request headers, bodies, or arbitrary caller paths.

        def reply(self, status: int, body: dict) -> None:
            raw = (json.dumps(body, sort_keys=True, separators=(",", ":")) + "\n").encode()
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
                ready = root.is_dir() and os.access(root, os.W_OK)
                self.reply(200 if ready else 503, {"ready": ready, "source_mode": mode,
                            "identity_ready": False, "payment_ready": False})
            else:
                self.reply(404, {"code": "NOT_FOUND", "retryable": False})

        def do_POST(self) -> None:
            if self.path != "/internal/v1/captures":
                self.reply(404, {"code": "NOT_FOUND", "retryable": False})
                return
            try:
                lengths = self.headers.get_all("Content-Length", [])
                if (len(lengths) != 1 or not lengths[0].isascii() or not lengths[0].isdigit()
                        or self.headers.get("Transfer-Encoding") is not None
                        or self.headers.get_content_type() != "application/json"
                        or not 1 <= int(lengths[0]) <= 16384):
                    raise CaptureRejected("INVALID_INPUT")
                raw = self.rfile.read(int(lengths[0]))
                if len(raw) != int(lengths[0]):
                    raise CaptureRejected("INVALID_INPUT")
                body = strict_json(raw)
                if type(body) is not dict or set(body) != {"capture_id"} or type(body["capture_id"]) is not str:
                    raise CaptureRejected("INVALID_INPUT")
                capture_id = UUID(body["capture_id"])
                if str(capture_id) != body["capture_id"]:
                    raise CaptureRejected("INVALID_INPUT")
                capture_package(root, capture_id, source_mode=mode)
                self.reply(201, {"capture_id": str(capture_id), "source_mode": mode,
                                 "identity_status": "SIMULATED" if mode == "fixture" else "UNVERIFIED"})
            except FileExistsError:
                self.reply(409, {"code": "CAPTURE_ALREADY_EXISTS", "retryable": False})
            except CaptureRejected as error:
                self.reply(422 if error.code == "INVALID_INPUT" else 503,
                           {"code": error.code, "retryable": False})
            except (ValueError, TypeError, UnicodeError, KeyError):
                self.reply(400, {"code": "INVALID_INPUT", "retryable": False})
            except (OSError, socket.timeout):
                self.reply(503, {"code": "SOURCE_UNAVAILABLE", "retryable": False})

    # Synchronous by design: the hard capture deadline uses a main-thread timer.
    server = HTTPServer((os.environ.get("LIQVERA_CAPTURE_HOST", "0.0.0.0"),
                         int(os.environ.get("LIQVERA_CAPTURE_PORT", "8081"))), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
