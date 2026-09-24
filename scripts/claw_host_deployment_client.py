#!/usr/bin/python3.14
"""Zero-argument bounded-stdin client for the fixed root deployment socket."""
from __future__ import annotations

import json
import os
import re
import socket
import stat
import struct
import sys
from pathlib import Path

try:
    from scripts.claw_host_deployment_contract import canonical_bytes, load_closed_bytes
except ModuleNotFoundError:
    sys.path.insert(0, "/usr/local/libexec/mee-claw-host-deploy-lib")
    from claw_host_deployment_contract import canonical_bytes, load_closed_bytes  # type: ignore[no-redef]


SOCKET_PATH = Path("/run/mee-claw-host-deploy/control.sock")
HEADER = struct.Struct("!I")
MAX_REQUEST = 32768
MAX_RESPONSE = 8192
RESPONSE_FIELDS = {
    "schema_version", "authority", "action", "transaction_id", "state",
    "receipt_sha256",
}
RESPONSE_STATES = {
    "D0_VERIFIED", "BEGIN_ACCEPTED", "HOST_APPLIED_PENDING_FINALIZE",
    "APPLYING", "VERIFYING", "FINALIZING", "COMMITTED", "ROLLING_BACK",
    "ROLLED_BACK", "ROLLBACK_BLOCKED",
}


def encode_frame(payload: bytes) -> bytes:
    if not isinstance(payload, bytes) or len(payload) < 2 or len(payload) > MAX_REQUEST:
        raise RuntimeError("FRAME_SIZE")
    return HEADER.pack(len(payload)) + payload


def read_frame(stream, *, limit: int) -> bytes:
    header = stream.read(HEADER.size)
    if len(header) != HEADER.size:
        raise RuntimeError("FRAME_HEADER")
    size = HEADER.unpack(header)[0]
    if size < 2 or size > limit:
        raise RuntimeError("FRAME_SIZE")
    chunks: list[bytes] = []
    remaining = size
    while remaining:
        chunk = stream.read(remaining)
        if not chunk:
            raise RuntimeError("FRAME_TRUNCATED")
        chunks.append(chunk)
        remaining -= len(chunk)
    if stream.read(1):
        raise RuntimeError("FRAME_TRAILING")
    return b"".join(chunks)


def verify_response(value: object, request: dict[str, object]) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != RESPONSE_FIELDS:
        raise RuntimeError("RESPONSE_FIELDS")
    if value["schema_version"] != "claw-host-deployment-response-v1" or value["authority"] != "NONE":
        raise RuntimeError("RESPONSE_AUTHORITY")
    if value["action"] != request.get("action") or value["state"] not in RESPONSE_STATES:
        raise RuntimeError("RESPONSE_BINDING")
    transaction_id = value["transaction_id"]
    if not isinstance(transaction_id, str) or not re.fullmatch(r"[0-9a-f]{32}", transaction_id):
        raise RuntimeError("RESPONSE_BINDING")
    if request.get("action") != "begin" and transaction_id != request.get("transaction_id"):
        raise RuntimeError("RESPONSE_BINDING")
    receipt = value["receipt_sha256"]
    if receipt is not None and (not isinstance(receipt, str) or not re.fullmatch(r"[0-9a-f]{64}", receipt)):
        raise RuntimeError("RESPONSE_RECEIPT")
    return value


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args:
        return 2
    try:
        if not hasattr(os, "geteuid") or os.geteuid() != 0:
            raise RuntimeError("ROOT_REQUIRED")
        info = SOCKET_PATH.lstat()
        if not stat.S_ISSOCK(info.st_mode) or info.st_uid != 0 or info.st_nlink != 1 or stat.S_IMODE(info.st_mode) != 0o600:
            raise RuntimeError("SOCKET_IDENTITY")
        raw = sys.stdin.buffer.read(MAX_REQUEST + 1)
        if not raw or len(raw) > MAX_REQUEST:
            raise RuntimeError("REQUEST_SIZE")
        request = load_closed_bytes(raw, max_bytes=MAX_REQUEST)
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
            connection.connect(str(SOCKET_PATH))
            connection.sendall(encode_frame(canonical_bytes(request)))
            connection.shutdown(socket.SHUT_WR)
            response_raw = read_frame(connection.makefile("rb"), limit=MAX_RESPONSE)
        response = verify_response(load_closed_bytes(response_raw, max_bytes=MAX_RESPONSE), request)
        print(json.dumps(response, sort_keys=True, separators=(",", ":")))
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"CLAW_HOST_DEPLOYMENT_CLIENT_ERROR:{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
