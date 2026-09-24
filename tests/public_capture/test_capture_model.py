"""Copied A2 capture value types stay pure and fail closed."""

from __future__ import annotations

import pytest
from mee_public_capture.model import (
    CAPTURE_BOUNDARY_PROFILE,
    COMPRESSION_PROFILE,
    ENVELOPE_SCHEMA,
    NDJSON_SCHEMA,
    CaptureProfile,
    Venue,
    WebSocketMessageType,
    application_payload_bytes,
)


def test_application_payload_preserves_text_and_binary() -> None:
    text = "snowman=\u2603\\u2603\x00"
    assert application_payload_bytes(WebSocketMessageType.TEXT, text) == text.encode(
        "utf-8"
    )
    payload = b"\x00\xffbinary"
    assert application_payload_bytes(WebSocketMessageType.BINARY, payload) == payload


def test_application_payload_rejects_mismatched_types() -> None:
    with pytest.raises(ValueError):
        application_payload_bytes(WebSocketMessageType.TEXT, b"bytes")
    with pytest.raises(ValueError):
        application_payload_bytes(WebSocketMessageType.BINARY, "text")


def test_capture_profile_literals_and_venues_are_stable() -> None:
    assert CAPTURE_BOUNDARY_PROFILE == (
        "websocket-application-message-post-decompression/v1"
    )
    assert ENVELOPE_SCHEMA == "mee-a2-envelope/v1"
    assert NDJSON_SCHEMA == "mee-a2-ndjson/v1"
    assert COMPRESSION_PROFILE == "gzip-raw-deflate-6-mtime0-os255/v1"
    assert {item.value for item in Venue} == {"HYPERLIQUID", "LIGHTER"}
    profile = CaptureProfile(
        collector_version="collector/v1",
        python_version="3.14",
        websocket_library="aiohttp",
        websocket_library_version="3.14.3",
        zlib_version="1.2.13",
        capture_boundary_profile=CAPTURE_BOUNDARY_PROFILE,
        envelope_schema=ENVELOPE_SCHEMA,
        ndjson_schema=NDJSON_SCHEMA,
        compression_profile=COMPRESSION_PROFILE,
    )
    assert profile.envelope_schema == ENVELOPE_SCHEMA


def test_package_exports_copied_capture_values() -> None:
    import mee_public_capture as pkg

    assert pkg.Venue.HYPERLIQUID.value == "HYPERLIQUID"
    assert pkg.CAPTURE_BOUNDARY_PROFILE == CAPTURE_BOUNDARY_PROFILE
    assert "ClosedLifecycle" not in pkg.__all__
    assert "GateConfig" not in pkg.__all__
    assert pkg.application_payload_bytes is application_payload_bytes


def test_model_module_has_no_legacy_or_analyzer_imports() -> None:
    import ast
    from pathlib import Path

    source = Path("packages/public-capture/src/mee_public_capture/model.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".", 1)[0])
    assert imported.isdisjoint(
        {"multi_exchange_engine", "mee_readonly_analyzer", "httpx", "psycopg"}
    )
    assert "ClosedLifecycle" not in source
    assert "GateConfig" not in source
