"""A deliberately bounded, offline checker for Liqvera F2 contract tests.

This module is test infrastructure, not a general JSON Schema engine or a
product runtime input validator.
"""

import json
import math
import re
import uuid
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[2] / "schemas" / "mezo-evidence" / "v1"
BASE = "https://schemas.liqvera.invalid/mezo-evidence/v1/"
KEYWORDS = frozenset({
    "$schema", "$id", "$defs", "$ref", "title", "description", "type",
    "const", "enum", "properties", "required", "additionalProperties",
    "items", "minItems", "maxItems", "uniqueItems", "minLength",
    "maxLength", "pattern", "format", "minimum", "maximum", "oneOf",
})
TYPES = frozenset({"object", "array", "string", "integer", "boolean", "null"})
FORMATS = frozenset({"uuid", "date-time", "uri"})
ABSOLUTE_END = r"(?![\s\S])"


class ContractError(ValueError):
    """The contract or instance is invalid."""


def _reject_duplicate(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ContractError(f"nonfinite JSON constant: {value}")


def _safe_name(name: str) -> str:
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*[.]json", name):
        raise ContractError("document must be a local JSON filename")
    if ".." in name or "%" in name or "\\" in name:
        raise ContractError("unsafe document name")
    return name


def load(name: str) -> dict:
    """Read one regular local JSON file, rejecting ambiguous JSON syntax."""
    name = _safe_name(name)
    path = ROOT / name
    if not path.is_file() or path.is_symlink() or path.resolve().parent != ROOT.resolve():
        raise ContractError(f"unavailable schema document: {name}")
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"),
                            object_pairs_hook=_reject_duplicate,
                            parse_constant=_reject_constant)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ContractError(f"invalid JSON document: {name}") from error
    if not isinstance(parsed, dict):
        raise ContractError("document root must be an object")
    return parsed


def _registry() -> dict[str, str]:
    """Map canonical identifiers to local schema filenames only."""
    result = {}
    for path in ROOT.glob("*.schema.json"):
        name = _safe_name(path.name)
        document = load(name)
        canonical = BASE + name
        if document.get("$id") != canonical:
            raise ContractError(f"mismatched root $id: {name}")
        _reject_nested_ids(document)
        if canonical in result:
            raise ContractError(f"duplicate root $id: {canonical}")
        result[canonical] = name
    # OpenAPI has no JSON Schema $id, but its canonical base resolves refs.
    if (ROOT / "openapi.json").exists():
        load("openapi.json")
        result[BASE + "openapi.json"] = "openapi.json"
    return result


def _reject_nested_ids(value: object) -> None:
    if isinstance(value, dict):
        for child in value.values():
            if isinstance(child, dict) and "$id" in child:
                raise ContractError("nested $id rebasing")
            _reject_nested_ids(child)
    elif isinstance(value, list):
        for child in value:
            _reject_nested_ids(child)


def _pointer(document: object, fragment: str) -> dict:
    if not fragment:
        target = document
    else:
        if not fragment.startswith("/"):
            raise ContractError("invalid JSON Pointer")
        target = document
        for encoded in fragment[1:].split("/"):
            if re.search(r"~(?![01])", encoded):
                raise ContractError("invalid JSON Pointer escape")
            token = encoded.replace("~1", "/").replace("~0", "~")
            if isinstance(target, dict) and token in target:
                target = target[token]
            elif isinstance(target, list) and re.fullmatch(r"0|[1-9][0-9]*", token) and int(token) < len(target):
                target = target[int(token)]
            else:
                raise ContractError("dangling JSON Pointer")
    if not isinstance(target, dict):
        raise ContractError("reference target is not a schema object")
    return target


def _resolve_with_uri(ref: str, document: str) -> tuple[dict, str, str]:
    document = _safe_name(document)
    if not isinstance(ref, str) or not ref or "%" in ref or "\\" in ref:
        raise ContractError("unsafe reference")
    if ref.startswith("/") or any(part in {".", ".."} for part in urlsplit(ref).path.split("/")):
        raise ContractError("path traversal reference")
    raw = urlsplit(ref)
    if raw.query or raw.username or raw.password or raw.scheme not in {"", "https"}:
        raise ContractError("unsupported reference URI")
    uri = urljoin(BASE + document, ref)
    parsed = urlsplit(uri)
    if parsed.query or not uri.startswith(BASE):
        raise ContractError("unregistered reference URI")
    name = parsed.path.removeprefix(urlsplit(BASE).path)
    if _safe_name(name) != name or BASE + name not in _registry():
        raise ContractError("unregistered reference URI")
    return _pointer(load(name), parsed.fragment), name, uri


def resolve(ref: str, *, document: str) -> tuple[dict, str]:
    """Resolve a registered URI or relative JSON Pointer without network I/O."""
    target, name, _ = _resolve_with_uri(ref, document)
    return target, name


def _nonnegative_int(value: object, keyword: str) -> None:
    if type(value) is not int or value < 0:
        raise ContractError(f"{keyword} must be a nonnegative integer")


def _pattern(pattern: object) -> None:
    if not isinstance(pattern, str):
        raise ContractError("pattern must be a string")
    body = pattern.replace(ABSOLUTE_END, "")
    if "$" in body or "\\" in body or "(?" in body or (pattern.startswith("^") and not pattern.endswith(ABSOLUTE_END)):
        raise ContractError("pattern uses a nonportable or weak anchor")
    try:
        re.compile(pattern)
    except re.error as error:
        raise ContractError("invalid pattern") from error


def _assert_node(schema: dict, document: str, *, root: bool, stack: frozenset[str]) -> None:
    if not isinstance(schema, dict):
        raise ContractError("schema must be an object")
    unknown = schema.keys() - KEYWORDS
    if unknown:
        raise ContractError(f"unsupported schema keyword: {sorted(unknown)[0]}")
    if "$id" in schema:
        if not root or schema["$id"] != BASE + document:
            raise ContractError("nested or mismatched $id")
    if "$schema" in schema and schema["$schema"] != "https://json-schema.org/draft/2020-12/schema":
        raise ContractError("unsupported schema dialect")
    for label in ("title", "description"):
        if label in schema and not isinstance(schema[label], str):
            raise ContractError(f"{label} must be a string")
    if "$ref" in schema:
        if schema.keys() - {"$ref", "title", "description"}:
            raise ContractError("$ref has assertion siblings")
        target, target_doc, uri = _resolve_with_uri(schema["$ref"], document)
        if uri in stack:
            raise ContractError("reference cycle")
        _assert_node(target, target_doc, root=not urlsplit(uri).fragment,
                     stack=stack | {uri})
        return
    if "type" in schema and (not isinstance(schema["type"], str) or schema["type"] not in TYPES):
        raise ContractError("unsupported schema type")
    if "format" in schema and (not isinstance(schema["format"], str) or schema["format"] not in FORMATS):
        raise ContractError("unsupported format")
    if "pattern" in schema:
        _pattern(schema["pattern"])
    for label in ("minItems", "maxItems", "minLength", "maxLength"):
        if label in schema:
            _nonnegative_int(schema[label], label)
    for label in ("minimum", "maximum"):
        if label in schema and (type(schema[label]) not in {int, float} or not math.isfinite(schema[label])):
            raise ContractError(f"{label} must be finite numeric")
    for short, long in (("minItems", "maxItems"), ("minLength", "maxLength"), ("minimum", "maximum")):
        if short in schema and long in schema and schema[short] > schema[long]:
            raise ContractError(f"{short} exceeds {long}")
    if "enum" in schema:
        if not isinstance(schema["enum"], list) or not schema["enum"]:
            raise ContractError("enum must be nonempty")
        try:
            json.dumps(schema["enum"], allow_nan=False)
        except (TypeError, ValueError) as error:
            raise ContractError("enum is not JSON") from error
    if "const" in schema:
        try:
            json.dumps(schema["const"], allow_nan=False)
        except (TypeError, ValueError) as error:
            raise ContractError("const is not JSON") from error
    if "uniqueItems" in schema and not isinstance(schema["uniqueItems"], bool):
        raise ContractError("uniqueItems must be boolean")
    if schema.get("type") == "object" and schema.get("additionalProperties") is not False:
        raise ContractError("objects must be closed")
    if "additionalProperties" in schema and schema["additionalProperties"] is not False:
        raise ContractError("additionalProperties must be false")
    if "properties" in schema:
        if not isinstance(schema["properties"], dict):
            raise ContractError("properties must be an object")
        for child in schema["properties"].values():
            _assert_node(child, document, root=False, stack=stack)
    if "required" in schema:
        required = schema["required"]
        if not isinstance(required, list) or any(not isinstance(x, str) for x in required) or len(set(required)) != len(required):
            raise ContractError("required must contain unique strings")
        if not set(required) <= set(schema.get("properties", {})):
            raise ContractError("required property lacks schema")
    if schema.get("type") == "array" and "items" not in schema:
        raise ContractError("array items schema is required")
    if "items" in schema:
        _assert_node(schema["items"], document, root=False, stack=stack)
    if "$defs" in schema:
        if not isinstance(schema["$defs"], dict):
            raise ContractError("$defs must be an object")
        for child in schema["$defs"].values():
            _assert_node(child, document, root=False, stack=stack)
    if "oneOf" in schema:
        if not isinstance(schema["oneOf"], list) or not schema["oneOf"]:
            raise ContractError("oneOf must be nonempty")
        for child in schema["oneOf"]:
            _assert_node(child, document, root=False, stack=stack)


def assert_schema(schema: dict, *, document: str) -> None:
    """Reject unsupported constructs and dangling/cyclic references."""
    document = _safe_name(document)
    _assert_node(schema, document, root=True, stack=frozenset())


def _matches_type(kind: str, value: object) -> bool:
    return {
        "object": lambda: isinstance(value, dict),
        "array": lambda: isinstance(value, list),
        "string": lambda: isinstance(value, str),
        "integer": lambda: type(value) is int,
        "boolean": lambda: type(value) is bool,
        "null": lambda: value is None,
    }[kind]()


def _equal(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(_equal(item, right[key]) for key, item in left.items())
    if isinstance(left, list):
        return len(left) == len(right) and all(_equal(a, b) for a, b in zip(left, right, strict=True))
    return left == right


def _format_valid(name: str, value: str) -> bool:
    if name == "uuid":
        try:
            return str(uuid.UUID(value)) == value and bool(re.fullmatch(r"[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}", value))
        except ValueError:
            return False
    if name == "date-time":
        if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:[.][0-9]+)?Z", value):
            return False
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return False
        return True
    try:
        parsed = urlsplit(value)
        port_ok = parsed.port is None or 0 < parsed.port <= 65535
    except ValueError:
        return False
    return parsed.scheme == "https" and bool(parsed.hostname) and parsed.username is None and parsed.password is None and port_ok and not any(c.isspace() for c in value)


def _validate_node(schema: dict, value: object, document: str) -> None:
    if "$ref" in schema:
        target, target_doc = resolve(schema["$ref"], document=document)
        _validate_node(target, value, target_doc)
        return
    if "type" in schema and not _matches_type(schema["type"], value):
        raise ContractError("instance type mismatch")
    if "const" in schema and not _equal(value, schema["const"]):
        raise ContractError("const mismatch")
    if "enum" in schema and not any(_equal(value, option) for option in schema["enum"]):
        raise ContractError("enum mismatch")
    if "oneOf" in schema:
        matches = 0
        for branch in schema["oneOf"]:
            try:
                _validate_node(branch, value, document)
            except ContractError:
                continue
            matches += 1
        if matches != 1:
            raise ContractError("oneOf requires exactly one matching branch")
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        if "required" in schema and not set(schema["required"]) <= value.keys():
            raise ContractError("missing required property")
        if schema.get("additionalProperties") is False and value.keys() - properties.keys():
            raise ContractError("extra property")
        for key, child in properties.items():
            if key in value:
                _validate_node(child, value[key], document)
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            raise ContractError("too few items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            raise ContractError("too many items")
        if schema.get("uniqueItems"):
            for index, item in enumerate(value):
                if any(_equal(item, prior) for prior in value[:index]):
                    raise ContractError("duplicate array item")
        if "items" in schema:
            for item in value:
                _validate_node(schema["items"], item, document)
    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            raise ContractError("string too short")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            raise ContractError("string too long")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            raise ContractError("pattern mismatch")
        if "format" in schema and not _format_valid(schema["format"], value):
            raise ContractError("format mismatch")
    if type(value) is int:
        if "minimum" in schema and value < schema["minimum"]:
            raise ContractError("below minimum")
        if "maximum" in schema and value > schema["maximum"]:
            raise ContractError("above maximum")


def validate(schema: dict, value: object, *, document: str) -> None:
    """Validate one instance against this project's supported schema subset."""
    assert_schema(schema, document=document)
    _validate_node(schema, value, document)
