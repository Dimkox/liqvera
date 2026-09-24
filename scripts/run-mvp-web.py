#!/usr/bin/env python3
"""Serve the local, fixture-only Liqvera browser demonstration."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import tempfile
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from uuid import UUID

from mee_evidence_report.local_flow import LocalDemoError, LocalDemoFlow
from mee_evidence_report.local_store import LocalDemoStore
from mee_public_capture.config import load_public_configuration
from mee_public_capture.runtime import run_public_capture
from mee_readonly_analyzer.frozen_package.reader import FrozenPackageEvidenceReader

_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
_CAPABILITY = re.compile(r"[0-9a-f]{64}\Z")
_ACTION_KEY = re.compile(r"[0-9a-f]{64}\Z")
_RUN_PATH = re.compile(
    r"/demo/runs/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-"
    r"[0-9a-f]{4}-[0-9a-f]{12})(?:/(confirm-simulated|report|evidence))?\Z"
)
_BODY_LIMIT = 8192
_RUN_FIELDS = frozenset({"instrument_id", "side", "quantity_base", "expected_payer"})
_STATIC = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
}
_CAPABILITIES = {
    "schema": "liqvera-local-demo/v1",
    "mode": "SIMULATED",
    "instrument_id": "hyperliquid:BTC:perpetual",
    "instrument_label": "Hyperliquid BTC perpetual (fixture)",
    "price_display": "0 MUSD — simulated access, NO TRANSFER",
    "source_mode": "fixture",
    "limitations": [
        "SIMULATED and UNVERIFIED historical fixture data; not a live market snapshot.",
        "Read-only analytics; no trading or execution authority.",
        "Local unlock only: NO TRANSFER, wallet signature, receipt, or settlement.",
    ],
}


class DemoHttpError(Exception):
    def __init__(self, status: HTTPStatus, code: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.code = code


def _real_directory(path: Path) -> Path:
    """Create one repository-owned directory without following a symlink."""
    if path.is_symlink():
        raise RuntimeError(f"Refusing a symlinked local demo directory: {path}")
    path.mkdir(mode=0o700, exist_ok=True)
    if not path.is_dir() or path.is_symlink():
        raise RuntimeError(f"Local demo path is not a real directory: {path}")
    return path


def _fixture_package(store_root: Path) -> Path:
    """Capture once into a private temporary directory, then publish atomically."""
    package_root = store_root / "package"
    if package_root.is_symlink():
        raise RuntimeError("Refusing a symlinked fixture package")
    if package_root.exists():
        FrozenPackageEvidenceReader(package_root)
        return package_root

    temporary = Path(tempfile.mkdtemp(prefix=".package-", dir=store_root))
    try:
        config = load_public_configuration(
            {
                "MEE_PUBLIC_VENUES": "hyperliquid",
                "MEE_PUBLIC_MODE": "public",
                "MEE_CAPTURE_SOURCE": "fixture",
                "MEE_CAPTURE_OUT": str(temporary),
            }
        )
        if run_public_capture(config) != 0:
            raise RuntimeError("Local fixture capture failed")
        FrozenPackageEvidenceReader(temporary)
        try:
            temporary.rename(package_root)
        except OSError:
            if not package_root.exists():
                raise
            FrozenPackageEvidenceReader(package_root)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return package_root


def _reject_constant(value: str) -> object:
    raise ValueError(f"Non-JSON number is forbidden: {value}")


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON field")
        result[key] = value
    return result


class DemoServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True
    request_queue_size = 16

    def __init__(self, address: tuple[str, int], flow: LocalDemoFlow) -> None:
        self.flow = flow
        self.web_root = _REPOSITORY_ROOT / "web"
        super().__init__(address, DemoHandler)


class DemoHandler(BaseHTTPRequestHandler):
    server: DemoServer
    timeout = 15

    def setup(self) -> None:
        super().setup()
        self.connection.settimeout(self.timeout)

    def log_message(self, _format: str, *_args: object) -> None:
        # Request URLs and headers can contain user-supplied identifiers.
        pass

    def send_error(self, code: int, message: str | None = None, explain: str | None = None) -> None:
        del message, explain
        status = HTTPStatus.METHOD_NOT_ALLOWED if code == 501 else HTTPStatus(code)
        self._json(status, {"error": "HTTP_ERROR", "message": status.phrase})

    def _send(
        self,
        status: HTTPStatus,
        payload: bytes,
        content_type: str,
        *,
        disposition: str | None = None,
    ) -> None:
        self.close_connection = True
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; base-uri 'none'; object-src 'none'; frame-ancestors 'none'",
        )
        self.send_header("Connection", "close")
        if disposition is not None:
            self.send_header("Content-Disposition", disposition)
        self.end_headers()
        self.wfile.write(payload)

    def _json(self, status: HTTPStatus, document: object) -> None:
        payload = json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self._send(status, payload, "application/json; charset=utf-8")

    def _single_header(self, name: str) -> str | None:
        values = self.headers.get_all(name, [])
        if len(values) > 1:
            raise DemoHttpError(
                HTTPStatus.BAD_REQUEST, "DUPLICATE_HEADER", f"Duplicate {name} header"
            )
        return values[0] if values else None

    def _capability(self) -> str:
        authorization = self._single_header("Authorization")
        if authorization is None or not authorization.startswith("Bearer "):
            raise DemoHttpError(
                HTTPStatus.UNAUTHORIZED, "CAPABILITY_REQUIRED", "A browser capability is required"
            )
        capability = authorization[len("Bearer ") :]
        if _CAPABILITY.fullmatch(capability) is None:
            raise DemoHttpError(
                HTTPStatus.UNAUTHORIZED, "CAPABILITY_INVALID", "Invalid browser capability"
            )
        return capability

    def _key(self, name: str) -> str:
        value = self._single_header(name)
        if value is None or _ACTION_KEY.fullmatch(value) is None:
            raise DemoHttpError(
                HTTPStatus.BAD_REQUEST,
                "ACTION_KEY_INVALID",
                f"{name} must be 64 lowercase hex characters",
            )
        return value

    def _body(self, *, optional: bool = False) -> dict[str, object]:
        if self._single_header("Transfer-Encoding") is not None:
            raise DemoHttpError(
                HTTPStatus.BAD_REQUEST,
                "TRANSFER_ENCODING_FORBIDDEN",
                "Transfer encoding is unsupported",
            )
        raw_length = self._single_header("Content-Length")
        if raw_length is None:
            if optional:
                return {}
            raise DemoHttpError(
                HTTPStatus.LENGTH_REQUIRED, "CONTENT_LENGTH_REQUIRED", "Content-Length is required"
            )
        if re.fullmatch(r"[0-9]+", raw_length) is None:
            raise DemoHttpError(
                HTTPStatus.BAD_REQUEST, "CONTENT_LENGTH_INVALID", "Invalid Content-Length"
            )
        length = int(raw_length)
        if length > _BODY_LIMIT:
            raise DemoHttpError(
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                "BODY_TOO_LARGE",
                "JSON body exceeds 8192 bytes",
            )
        if length == 0 and optional:
            return {}
        if length == 0:
            raise DemoHttpError(HTTPStatus.BAD_REQUEST, "BODY_REQUIRED", "JSON body is required")
        content_type = self._single_header("Content-Type")
        if content_type not in ("application/json", "application/json; charset=utf-8"):
            raise DemoHttpError(
                HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
                "CONTENT_TYPE_INVALID",
                "Content-Type must be application/json",
            )
        payload = self.rfile.read(length)
        if len(payload) != length:
            raise DemoHttpError(HTTPStatus.BAD_REQUEST, "BODY_TRUNCATED", "Incomplete JSON body")
        try:
            document = json.loads(
                payload.decode("utf-8"),
                parse_constant=_reject_constant,
                object_pairs_hook=_unique_object,
            )
        except (UnicodeDecodeError, ValueError) as error:
            raise DemoHttpError(
                HTTPStatus.BAD_REQUEST, "JSON_INVALID", "Invalid JSON body"
            ) from error
        if type(document) is not dict:
            raise DemoHttpError(
                HTTPStatus.BAD_REQUEST, "JSON_OBJECT_REQUIRED", "JSON body must be an object"
            )
        return document

    def _path(self) -> str:
        parsed = urlsplit(self.path)
        if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
            raise DemoHttpError(HTTPStatus.NOT_FOUND, "NOT_FOUND", "Route not found")
        return parsed.path

    def _run_match(self, path: str) -> tuple[UUID, str | None] | None:
        match = _RUN_PATH.fullmatch(path)
        if match is None:
            return None
        run_id = UUID(match.group(1))
        if str(run_id) != match.group(1):
            return None
        return run_id, match.group(2)

    def _static(self, path: str) -> None:
        asset = _STATIC.get(path)
        if asset is None:
            raise DemoHttpError(HTTPStatus.NOT_FOUND, "NOT_FOUND", "Route not found")
        root = self.server.web_root
        if root.is_symlink() or not root.is_dir():
            raise DemoHttpError(
                HTTPStatus.SERVICE_UNAVAILABLE,
                "WEB_ASSETS_UNAVAILABLE",
                "Web assets are unavailable",
            )
        filename, content_type = asset
        target = root / filename
        if target.is_symlink() or not target.is_file() or target.resolve().parent != root.resolve():
            raise DemoHttpError(
                HTTPStatus.SERVICE_UNAVAILABLE,
                "WEB_ASSETS_UNAVAILABLE",
                "Web assets are unavailable",
            )
        self._send(HTTPStatus.OK, target.read_bytes(), content_type)

    def _handle_get(self) -> None:
        path = self._path()
        if path == "/demo/capabilities":
            self._json(HTTPStatus.OK, _CAPABILITIES)
            return
        if path in _STATIC:
            self._static(path)
            return
        matched = self._run_match(path)
        if matched is None:
            raise DemoHttpError(HTTPStatus.NOT_FOUND, "NOT_FOUND", "Route not found")
        run_id, suffix = matched
        capability = self._capability()
        if suffix is None:
            self._json(HTTPStatus.OK, self.server.flow.get_run(capability, run_id))
        elif suffix == "report":
            self._send(
                HTTPStatus.OK,
                self.server.flow.get_report(capability, run_id),
                "application/json; charset=utf-8",
                disposition=f'attachment; filename="liqvera-report-{run_id}.json"',
            )
        elif suffix == "evidence":
            self._send(
                HTTPStatus.OK,
                self.server.flow.get_evidence(capability, run_id),
                "application/zip",
                disposition=f'attachment; filename="liqvera-evidence-{run_id}.zip"',
            )
        else:
            raise DemoHttpError(HTTPStatus.NOT_FOUND, "NOT_FOUND", "Route not found")

    def _handle_post(self) -> None:
        path = self._path()
        if path == "/demo/runs":
            capability = self._capability()
            key = self._key("Idempotency-Key")
            body = self._body()
            if set(body) != _RUN_FIELDS or any(type(value) is not str for value in body.values()):
                raise DemoHttpError(
                    HTTPStatus.BAD_REQUEST,
                    "REQUEST_FIELDS_INVALID",
                    "Run body must contain exactly four string fields",
                )
            self._json(HTTPStatus.CREATED, self.server.flow.create_run(capability, key, body))
            return
        matched = self._run_match(path)
        if matched is None or matched[1] != "confirm-simulated":
            raise DemoHttpError(HTTPStatus.NOT_FOUND, "NOT_FOUND", "Route not found")
        run_id, _ = matched
        capability = self._capability()
        action_key = self._key("X-Demo-Action-Key")
        if self._body(optional=True):
            raise DemoHttpError(
                HTTPStatus.BAD_REQUEST, "REQUEST_FIELDS_INVALID", "Confirmation body must be empty"
            )
        result = self.server.flow.confirm_simulated(capability, run_id, action_key)
        if "grant" not in result:
            result = {
                **result,
                "grant": {"mode": "SIMULATED", "transferred": False, "message": "NO TRANSFER"},
            }
        self._json(HTTPStatus.OK, result)

    def _dispatch(self, method: str) -> None:
        try:
            if method == "GET":
                self._handle_get()
            else:
                self._handle_post()
        except DemoHttpError as error:
            self._json(error.status, {"error": error.code, "message": str(error)})
        except LocalDemoError as error:
            status = (
                HTTPStatus(error.status)
                if 400 <= error.status <= 599
                else HTTPStatus.INTERNAL_SERVER_ERROR
            )
            self._json(status, {"error": error.code, "message": str(error)})
        except Exception:
            self._json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"error": "INTERNAL_ERROR", "message": "Local demo request failed"},
            )

    def do_GET(self) -> None:
        self._dispatch("GET")

    def do_POST(self) -> None:
        self._dispatch("POST")


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve the fixture-only Liqvera local MVP")
    parser.add_argument("--host", default=os.environ.get("MVP_WEB_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=os.environ.get("MVP_WEB_PORT", "8765"))
    args = parser.parse_args()
    if args.host != "127.0.0.1" or not 1 <= args.port <= 65535:
        parser.error("the local demo binds only 127.0.0.1 on a port from 1 to 65535")

    mvp_root = _real_directory(_REPOSITORY_ROOT / ".mvp")
    store_root = _real_directory(mvp_root / "store")
    artifact_root = _real_directory(store_root / "artifacts")
    package_root = _fixture_package(store_root)
    flow = LocalDemoFlow(LocalDemoStore(store_root / "ledger.sqlite3", artifact_root), package_root)
    with DemoServer((args.host, args.port), flow) as server:
        print(f"Liqvera local demo: http://{args.host}:{args.port}/", flush=True)
        print("SIMULATED / UNVERIFIED fixture analytics; NO TRANSFER", flush=True)
        try:
            server.serve_forever(poll_interval=0.5)
        except KeyboardInterrupt:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
