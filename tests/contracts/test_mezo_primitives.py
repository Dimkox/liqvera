"""Behavioral contract checks for offline schema validation and primitives."""

import json
import shutil

import mezo_evidence_support as c
import pytest


def test_rational_validates_exact_string_components():
    # Break: a valid exact rational is rejected by the contract checker.
    try:
        c.validate(
            {"$ref": "primitives.schema.json#/$defs/rational"},
            {"numerator": "300100", "denominator": "3"},
            document="primitives.schema.json",
        )
    except c.ContractError as error:
        pytest.fail(f"valid rational rejected: {error}")


@pytest.mark.parametrize(
    "value",
    [
        {"numerator": 300100, "denominator": "3"},
        {"numerator": "300100", "denominator": "0"},
        {"numerator": "1", "denominator": "3", "decimal": "0.333"},
    ],
)
def test_rational_rejects_ambiguous_or_extra_values(value):
    # Break: inexact, zero-denominator or uncontracted data is accepted.
    with pytest.raises(c.ContractError):
        c.validate(
            {"$ref": "primitives.schema.json#/$defs/rational"},
            value,
            document="primitives.schema.json",
        )


def test_all_primitive_definitions_are_well_formed():
    # Break: a primitive schema change introduces a keyword the checker ignores.
    c.assert_schema(c.load("primitives.schema.json"), document="primitives.schema.json")


@pytest.mark.parametrize(
    ("definition", "valid", "invalid"),
    [
        ("id", "123e4567-e89b-42d3-a456-426614174000", "123E4567-E89B-42D3-A456-426614174000"),
        ("sha256", "a" * 64, "A" * 64),
        ("timestamp", "2024-02-29T23:59:59Z", "2024-02-30T23:59:59Z"),
        ("quantity_input", "+0001.12345678", "1.123456789"),
        ("quantity", "1.00000001", "01.0"),
        ("address_input", "0x" + "A" * 40, "0X" + "A" * 40),
        ("address", "0x" + "a" * 40, "0x" + "A" * 40),
        ("atomic_amount", "1", "0"),
        ("display_decimal", "-1.25", "01.25"),
    ],
)
def test_primitive_accepts_canonical_shape_and_rejects_malformed_shape(definition, valid, invalid):
    # Break: any of the deliberately distinct input/canonical forms collapses.
    ref = {"$ref": f"#/$defs/{definition}"}
    c.validate(ref, valid, document="primitives.schema.json")
    with pytest.raises(c.ContractError):
        c.validate(ref, invalid, document="primitives.schema.json")


@pytest.mark.parametrize("suffix", ["\n", "\r\n", "\u2028", "\u2029"])
@pytest.mark.parametrize(
    ("definition", "valid"),
    [
        ("quantity_input", "1.25"),
        ("quantity", "1.25"),
        ("address_input", "0x" + "A" * 40),
        ("address", "0x" + "a" * 40),
        ("sha256", "a" * 64),
        ("atomic_amount", "12"),
        ("display_decimal", "12.5"),
    ],
)
def test_absolute_end_patterns_reject_all_line_terminators(definition, valid, suffix):
    # Break: an end-of-line anchor accepts a valid prefix with trailing input.
    with pytest.raises(c.ContractError):
        c.validate({"$ref": f"#/$defs/{definition}"}, valid + suffix,
                   document="primitives.schema.json")


def test_pattern_uses_search_semantics():
    # Break: the helper silently applies fullmatch to unanchored schemas.
    c.validate({"type": "string", "pattern": "BTC"}, "xBTCx", document="primitives.schema.json")


@pytest.mark.parametrize(
    ("schema", "value"),
    [
        ({"type": "integer"}, True),
        ({"type": "object", "additionalProperties": False, "required": ["x"],
          "properties": {"x": {"type": "string"}}}, {}),
        ({"type": "object", "additionalProperties": False,
          "properties": {"x": {"type": "string"}}}, {"extra": 1}),
        ({"type": "string", "const": "BTC"}, "ETH"),
        ({"type": "string", "enum": ["BTC"]}, "ETH"),
        ({"type": "string", "minLength": 2}, "x"),
        ({"type": "string", "maxLength": 2}, "xyz"),
        ({"type": "integer", "minimum": 2}, 1),
        ({"type": "integer", "maximum": 2}, 3),
        ({"type": "array", "items": {"type": "integer"}, "minItems": 2}, [1]),
        ({"type": "array", "items": {"type": "integer"}, "maxItems": 1}, [1, 2]),
        ({"type": "array", "items": {"type": "integer"}, "uniqueItems": True}, [1, 1]),
        ({"oneOf": [{"type": "string"}, {"enum": ["BTC"]}]}, "BTC"),
        ({"type": "null"}, "null"),
        ({"type": "boolean"}, 1),
    ],
)
def test_used_validation_keywords_reject_out_of_contract_values(schema, value):
    # Break: a recognized assertion keyword is treated as annotation only.
    with pytest.raises(c.ContractError):
        c.validate(schema, value, document="primitives.schema.json")


@pytest.mark.parametrize(
    "schema",
    [
        {"type": "string", "default": "x"},
        {"$ref": "#/$defs/x", "type": "string"},
        {"type": "number"},
        {"type": "object"},
        {"type": "array"},
        {"type": "string", "minLength": True},
        {"type": "string", "minLength": -1},
        {"type": "string", "maxLength": "2"},
        {"type": "array", "minItems": -1, "items": {}},
        {"type": "array", "uniqueItems": "yes", "items": {}},
        {"type": "integer", "minimum": True},
        {"type": "integer", "minimum": 3, "maximum": 2},
        {"type": "string", "format": "email"},
        {"type": "string", "pattern": "^a$"},
        {"type": "string", "pattern": "\\d"},
        {"type": "object", "additionalProperties": False, "properties": {"x": {}},
         "required": ["missing"]},
        {"type": "object", "additionalProperties": False, "properties": [], "required": []},
        {"oneOf": []},
        {"enum": []},
        {"$defs": []},
        {"title": 1},
        {"description": 1},
        {"$schema": 1},
        {"$id": "https://other.invalid/a"},
        {"type": "object", "additionalProperties": False,
         "properties": {"child": {"$id": "https://schemas.liqvera.invalid/mezo-evidence/v1/child.json"}}},
    ],
)
def test_malformed_schema_is_rejected_before_instance_validation(schema):
    # Break: malformed contract metadata is silently ignored.
    with pytest.raises(c.ContractError):
        c.assert_schema(schema, document="primitives.schema.json")


@pytest.mark.parametrize("ref", [
    "#/$defs/nope", "#/$defs/~2", "#/$defs/~", "missing.schema.json#/$defs/x",
    "../../secrets.schema.json", "/tmp/x.schema.json", "file:///tmp/x.schema.json",
    "https://elsewhere.invalid/x.schema.json", "primitives%2eschema.json#/$defs/id",
])
def test_reference_escape_or_dangling_target_is_rejected(ref):
    # Break: reference resolution reads arbitrary files or treats dangling refs as valid.
    with pytest.raises(c.ContractError):
        c.resolve(ref, document="primitives.schema.json")


def test_reference_pointer_decodes_escaped_tokens_and_rejects_cycles(tmp_path, monkeypatch):
    # Break: escaped JSON Pointers fail or a cyclic contract recurses forever.
    document = "custom.schema.json"
    schema = {"$id": c.BASE + document, "$defs": {"a/b~c": {"type": "string"}}}
    (tmp_path / document).write_text(json.dumps(schema))
    monkeypatch.setattr(c, "ROOT", tmp_path)
    assert c.resolve("#/$defs/a~1b~0c", document=document) == (
        {"type": "string"}, document,
    )
    schema["$defs"] = {"loop": {"$ref": "#/$defs/loop"}}
    (tmp_path / document).write_text(json.dumps(schema))
    with pytest.raises(c.ContractError):
        c.assert_schema(c.load(document), document=document)


def test_registered_absolute_ref_matches_relative_ref_after_checkout_move(tmp_path, monkeypatch):
    # Break: refs depend on checkout location or require a network fetch.
    root = tmp_path / "schemas"
    shutil.copytree(c.ROOT, root)
    monkeypatch.setattr(c, "ROOT", root)
    relative = c.resolve("primitives.schema.json#/$defs/id", document="openapi.json")
    absolute = c.resolve(
        "https://schemas.liqvera.invalid/mezo-evidence/v1/primitives.schema.json#/$defs/id",
        document="openapi.json",
    )
    assert relative == absolute == ({"type": "string", "format": "uuid"}, "primitives.schema.json")


def test_whole_document_ref_accepts_registered_root_id():
    # Break: an ordinary reference to a schema root is mistaken for nested $id rebasing.
    c.validate({"$ref": "primitives.schema.json"}, "ignored",
               document="openapi.json")


def test_resolver_rejects_nested_id_even_before_validation(tmp_path, monkeypatch):
    # Break: resolving a nested target silently changes the reference base.
    document = "custom.schema.json"
    schema = {"$id": c.BASE + document, "$defs": {
        "nested": {"$id": c.BASE + "other.schema.json", "type": "string"},
    }}
    (tmp_path / document).write_text(json.dumps(schema))
    monkeypatch.setattr(c, "ROOT", tmp_path)
    with pytest.raises(c.ContractError):
        c.resolve("#/$defs/nested", document=document)


def test_registry_rejects_mismatched_id_and_symlink(tmp_path, monkeypatch):
    # Break: an attacker substitutes a schema document under a trusted URI.
    root = tmp_path / "schemas"
    root.mkdir()
    original = json.loads((c.ROOT / "primitives.schema.json").read_text())
    original["$id"] = "https://schemas.liqvera.invalid/mezo-evidence/v1/other.schema.json"
    (root / "primitives.schema.json").write_text(json.dumps(original))
    monkeypatch.setattr(c, "ROOT", root)
    with pytest.raises(c.ContractError):
        c.resolve("#/$defs/id", document="primitives.schema.json")
    (root / "primitives.schema.json").unlink()
    (root / "primitives.schema.json").symlink_to(c.ROOT.parent / "missing")
    with pytest.raises(c.ContractError):
        c.resolve("#/$defs/id", document="primitives.schema.json")


@pytest.mark.parametrize("payload", [
    '{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}',
    '{"a":1e999}', '{"a":[-1e999]}',
])
def test_strict_json_loader_rejects_duplicate_or_nonfinite_values(tmp_path, monkeypatch, payload):
    # Break: parser ambiguity or non-JSON numerics enter the contract registry.
    (tmp_path / "malformed.json").write_text(payload)
    monkeypatch.setattr(c, "ROOT", tmp_path)
    with pytest.raises(c.ContractError):
        c.load("malformed.json")


def test_strict_json_loader_accepts_finite_decimal_number(tmp_path, monkeypatch):
    # Break: guarding overflow rejects ordinary finite JSON decimals too.
    (tmp_path / "finite.json").write_text('{"a":1.5}')
    monkeypatch.setattr(c, "ROOT", tmp_path)
    assert c.load("finite.json") == {"a": 1.5}


@pytest.mark.parametrize(
    ("schema", "invalid", "boundary"),
    [
        ({"minimum": 2}, 1.5, 2.0),
        ({"maximum": 2}, 2.5, 2.0),
    ],
)
def test_numeric_bounds_apply_to_finite_float_instances(schema, invalid, boundary):
    # Break: minimum/maximum silently skip JSON decimal numbers.
    with pytest.raises(c.ContractError):
        c.validate(schema, invalid, document="primitives.schema.json")
    c.validate(schema, boundary, document="primitives.schema.json")


def test_boolean_is_not_an_integer_instance():
    # Break: Python bool passes numeric type checks through int inheritance.
    with pytest.raises(c.ContractError):
        c.validate({"type": "integer", "minimum": 0}, True,
                   document="primitives.schema.json")


@pytest.mark.parametrize("schema", [{"const": 1}, {"enum": [1]}])
def test_json_numeric_equality_accepts_integer_decimal_equivalence(schema):
    # Break: 1.0 is rejected despite equaling JSON numeric value 1.
    c.validate(schema, 1.0, document="primitives.schema.json")


@pytest.mark.parametrize("schema", [{"const": 1}, {"enum": [1]}])
def test_json_numeric_equality_keeps_boolean_distinct(schema):
    # Break: Python treats True as 1 in JSON const/enum membership.
    with pytest.raises(c.ContractError):
        c.validate(schema, True, document="primitives.schema.json")


def test_unique_items_rejects_equivalent_integer_and_decimal():
    # Break: numeric duplicates survive because their Python types differ.
    schema = {"type": "array", "items": {}, "uniqueItems": True}
    with pytest.raises(c.ContractError):
        c.validate(schema, [1, 1.0], document="primitives.schema.json")
    c.validate(schema, [1, True], document="primitives.schema.json")


@pytest.mark.parametrize("value", [
    "https://example.com/report", "https://example.com:443/report",
])
def test_uri_format_accepts_https_without_credentials(value):
    c.validate({"type": "string", "format": "uri"}, value, document="primitives.schema.json")


@pytest.mark.parametrize("value", [
    "http://example.com", "https://user:pass@example.com", "https:///missing-host",
])
def test_uri_format_rejects_unsafe_or_relative_urls(value):
    with pytest.raises(c.ContractError):
        c.validate({"type": "string", "format": "uri"}, value,
                   document="primitives.schema.json")
