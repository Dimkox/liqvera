"""Small canonical JSON boundary for deterministic MVP report bytes."""

from __future__ import annotations

import json


def canonical_json_bytes(document: object) -> bytes:
    """Serialize the supported JSON data model with one final line feed.

    Binary floating point is refused recursively. Exact financial values must
    reach this boundary as integer or decimal/rational strings.
    """

    _require_json_value(document, path="$")
    text = json.dumps(
        document,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return (text + "\n").encode("utf-8")


def _require_json_value(value: object, *, path: str) -> None:
    if type(value) is float:
        raise TypeError(f"float is forbidden in canonical JSON at {path}")
    if value is None or type(value) in {bool, int, str}:
        return
    if type(value) is list:
        for index, child in enumerate(value):
            _require_json_value(child, path=f"{path}[{index}]")
        return
    if type(value) is dict:
        for key, child in value.items():
            if type(key) is not str:
                raise TypeError(f"canonical JSON object key is not str at {path}")
            _require_json_value(child, path=f"{path}.{key}")
        return
    raise TypeError(f"unsupported canonical JSON value {type(value).__name__} at {path}")
