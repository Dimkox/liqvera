"""Validate frozen schemas from packaged resources, with no remote resolution."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from mee_evidence_report.evidence_io import EvidenceRejected, strict_json

SCHEMAS = (
    "primitives.schema.json", "quote-request.schema.json", "reasons.schema.json",
    "report.schema.json", "capture-evidence.schema.json", "bundle-manifest.schema.json",
    "algorithm.schema.json",
)


def schema_bytes(name: str) -> bytes:
    if name not in SCHEMAS:
        raise EvidenceRejected("INVALID_DATASET")
    resource = files("mee_evidence_report").joinpath("resources", "schemas", name)
    if resource.is_file():
        return resource.read_bytes()
    # Source checkout only. Installed wheels include these exact resources.
    return (Path(__file__).resolve().parents[4] / "schemas/mezo-evidence/v1" / name).read_bytes()


def validate(name: str, value: object) -> None:
    documents = {item: strict_json(schema_bytes(item)) for item in SCHEMAS}
    registry = Registry().with_resources(
        (document["$id"], Resource.from_contents(document)) for document in documents.values()
    )
    try:
        Draft202012Validator(documents[name], registry=registry,
                             format_checker=FormatChecker()).validate(value)
    except Exception as error:
        raise EvidenceRejected("INVALID_DATASET") from error
