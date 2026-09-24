"""Offline checks for the proposed Liqvera HTTP boundary, not a live gateway."""

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2] / "schemas/mezo-evidence/v1"
UUID = "01234567-89ab-4def-8abc-0123456789ab"
ERROR_REF = {"$ref": "error.schema.json"}
BEARER = [{"CapabilityBearer": []}]
OPERATIONS = {
    ("/healthz", "get"): ("getHealth", {"200"}),
    ("/readyz", "get"): ("getReadiness", {"200", "503"}),
    ("/v1/capabilities", "get"): ("getCapabilities", {"200", "503"}),
    ("/v1/report-quotes", "post"): (
        "createReportQuote", {"201", "202", "401", "409", "422", "429", "503"}),
    ("/v1/report-requests/{report_request_id}", "get"): (
        "getReportRequest", {"200", "202", "401", "404", "429", "503"}),
    ("/v1/report-quotes/{quote_id}", "get"): (
        "getReportQuote", {"200", "202", "401", "404", "410", "429", "503"}),
    ("/v1/reports/{report_id}", "get"): (
        "getReport", {"200", "202", "401", "402", "404", "409", "410", "429", "503"}),
    ("/v1/reports/{report_id}/evidence", "get"): (
        "getEvidence", {"200", "401", "402", "404", "410", "429", "503"}),
}


def api():
    path = ROOT / "openapi.json"
    assert path.is_file(), "HTTP contract is missing"
    return json.loads(path.read_text(encoding="utf-8"))


def response_schema(operation, status):
    return operation["responses"][status]["content"]["application/json"]["schema"]


def test_paid_body_is_only_the_entitled_report_response():
    contract = api()
    operation = contract["paths"]["/v1/reports/{report_id}"]["get"]
    assert operation["security"] == BEARER
    assert response_schema(operation, "200") == {
        "$ref": "resources.schema.json#/$defs/paid_report"}
    assert "PAYMENT-REQUIRED" in operation["responses"]["402"]["headers"]
    assert response_schema(operation, "402") == ERROR_REF
    assert "PAYMENT-RESPONSE" in operation["responses"]["200"]["headers"]
    for path, method in (("/v1/reports/{report_id}", "get"),
                         ("/v1/reports/{report_id}/evidence", "get")):
        for status, response in contract["paths"][path][method]["responses"].items():
            if status == "200":
                continue
            assert response_schema({"responses": {status: response}}, status) == ERROR_REF


def test_exact_operations_codes_auth_and_request_correlation():
    contract = api()
    assert contract["openapi"] == "3.1.0"
    assert contract["info"]["version"] == "1.0.0"
    assert contract["jsonSchemaDialect"] == "https://json-schema.org/draft/2020-12/schema"
    assert "servers" not in contract
    actual = {(path, method) for path, item in contract["paths"].items()
              for method in item if method in {"get", "post"}}
    assert actual == set(OPERATIONS)
    ids = []
    for (path, method), (operation_id, statuses) in OPERATIONS.items():
        operation = contract["paths"][path][method]
        ids.append(operation["operationId"])
        assert operation["operationId"] == operation_id
        assert set(operation["responses"]) == statuses
        assert operation["security"] == ([] if path in
            {"/healthz", "/readyz", "/v1/capabilities"} else BEARER)
        for response in operation["responses"].values():
            assert response["headers"]["X-Request-ID"]["required"] is True
            assert response["headers"]["X-Request-ID"]["schema"] == {
                "$ref": "primitives.schema.json#/$defs/id"}
            if path.startswith("/v1/") and path != "/v1/capabilities":
                assert response["headers"]["Cache-Control"]["required"] is True
                assert response["headers"]["Cache-Control"]["schema"] == {
                    "type": "string", "const": "private, no-store"}
        if "429" in statuses:
            assert operation["responses"]["429"]["headers"]["Retry-After"]["required"] is True
            retry = operation["responses"]["429"]["headers"]["Retry-After"]["schema"]
            assert retry["type"] == "string"
            assert retry["pattern"] == "^(0|[1-9][0-9]*)(?![\\s\\S])"
    assert len(ids) == len(set(ids))
    assert contract["components"]["securitySchemes"]["CapabilityBearer"] == {
        "type": "http", "scheme": "bearer"}


def test_request_body_status_locations_and_uuid_parameters():
    contract = api()
    post = contract["paths"]["/v1/report-quotes"]["post"]
    assert post["requestBody"]["required"] is True
    assert set(post["requestBody"]["content"]) == {"application/json"}
    assert post["requestBody"]["content"]["application/json"]["schema"] == {
        "$ref": "quote-request.schema.json"}
    assert len(post["parameters"]) == 1
    key = post["parameters"][0]
    assert (key["name"], key["in"], key["required"]) == (
        "Idempotency-Key", "header", True)
    assert key["schema"] == {
        "type": "string", "minLength": 1, "maxLength": 128,
        "pattern": "^[A-Za-z0-9._:-]+(?![\\s\\S])"}
    for status, target in (("201", "/v1/report-quotes/{quote_id}"),
                           ("202", "/v1/report-requests/{report_request_id}")):
        response = post["responses"][status]
        assert response["headers"]["Location"]["required"] is True
        assert response["headers"]["Location"]["x-liqvera-location-template"] == target
    assert response_schema(post, "201") == {"$ref": "resources.schema.json#/$defs/quote"}
    assert response_schema(post, "202") == {
        "$ref": "resources.schema.json#/$defs/request_status"}
    preparing = post["responses"]["202"]["content"]["application/json"]["example"]
    assert preparing["state"] == "PREPARING"
    assert preparing["status_location"] == (
        "/v1/report-requests/" + preparing["report_request_id"])
    assert not set(preparing) & {"quote_id", "terms", "receipt", "report"}
    status_get = contract["paths"]["/v1/report-requests/{report_request_id}"]["get"]
    assert response_schema(status_get, "202") == response_schema(status_get, "200")
    for (path, method) in OPERATIONS:
        operation = contract["paths"][path][method]
        names = {p["name"] for p in operation.get("parameters", []) if p["in"] == "path"}
        expected = {part[1:-1] for part in path.split("/") if part.startswith("{")}
        assert names == expected
        for parameter in operation.get("parameters", []):
            if parameter["in"] == "path":
                assert parameter["required"] is True
                assert parameter["schema"] == {"$ref": "primitives.schema.json#/$defs/id"}


def test_raw_evidence_has_no_json_schema_or_payment_signature_input():
    contract = api()
    evidence = contract["paths"]["/v1/reports/{report_id}/evidence"]["get"]
    report = contract["paths"]["/v1/reports/{report_id}"]["get"]
    assert evidence["responses"]["200"]["content"] == {"application/zip": {}}
    assert "PAYMENT-SIGNATURE" not in {p["name"] for p in evidence["parameters"]}
    signature = next(p for p in report["parameters"] if p["name"] == "PAYMENT-SIGNATURE")
    assert signature["in"] == "header" and signature["required"] is False
    assert signature["x-liqvera-decoded-max-bytes"] == 16384
    for operation in (report, evidence):
        assert operation["responses"]["402"]["headers"]["PAYMENT-REQUIRED"]["required"] is True
        assert "PAYMENT-REQUIRED" in operation["responses"]["402"]["headers"]
        assert response_schema(operation, "402") == ERROR_REF
    assert report["responses"]["200"]["headers"]["PAYMENT-RESPONSE"]["required"] is True


def test_error_examples_hide_existence_and_payment_details():
    contract = api()
    for path in ("/v1/report-requests/{report_request_id}",
                 "/v1/report-quotes/{quote_id}",
                 "/v1/reports/{report_id}",
                 "/v1/reports/{report_id}/evidence"):
        operation = contract["paths"][path]["get"]
        examples = operation["responses"]["404"]["content"]["application/json"]["examples"]
        assert set(examples) == {"missing", "other_scope", "guessed_id", "public_tx_hash"}
        assert len({json.dumps(v["value"], sort_keys=True) for v in examples.values()}) == 1
        assert next(iter(examples.values()))["value"] == {
            "schema": "mee-evidence-error/v1", "request_id": UUID,
            "code": "NOT_FOUND", "message": "Resource not found."}
    report = contract["paths"]["/v1/reports/{report_id}"]["get"]
    assert report["responses"]["402"]["content"]["application/json"]["example"]["code"] == "PAYMENT_REQUIRED"
    assert contract["paths"]["/v1/reports/{report_id}/evidence"]["get"]["responses"]["402"]["content"]["application/json"]["example"]["code"] == "PAYMENT_REQUIRED"


def test_payment_extension_preserves_unresolved_f5_bindings():
    contract = api()
    assert contract["x-liqvera-payment"] == {
        "protocol_version": 2, "scheme": "exact", "sdk_family_version": "2.16.0",
        "requirements_header": "PAYMENT-REQUIRED",
        "authorization_header": "PAYMENT-SIGNATURE",
        "receipt_header": "PAYMENT-RESPONSE",
        "authorization_identity_status": "UNRESOLVED_F5",
        "finality_status": "FINALITY_RULE_UNVERIFIED"}
    assert contract["x-liqvera-capability"]["minimum_entropy_bits"] == 256
    assert contract["x-liqvera-capability"]["storage"] == "hash_only"
    assert contract["x-liqvera-capability"]["payer_authenticity"] == "not_established"


def test_public_examples_show_payment_is_blocked():
    contract = api()
    readiness = contract["paths"]["/readyz"]["get"]["responses"]["503"]
    capability = contract["paths"]["/v1/capabilities"]["get"]["responses"]["200"]
    for response in (readiness, capability):
        body = response["content"]["application/json"]["example"]
        assert body["payment_ready"] is False
        assert set(body["blockers"]) == {"PAY_TO_MISSING", "FINALITY_RULE_UNVERIFIED"}
        assert body["request_id"] == UUID


def test_response_media_references_and_examples_are_safely_bounded():
    contract = api()
    allowed = {
        "error.schema.json", "quote-request.schema.json",
        "primitives.schema.json#/$defs/id",
        *{f"resources.schema.json#/$defs/{name}" for name in
          ("health", "readiness", "capabilities", "quote", "request_status", "paid_report")},
    }
    refs = set()

    def walk(value):
        if isinstance(value, dict):
            if "$ref" in value:
                refs.add(value["$ref"])
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(contract)
    assert refs == allowed
    for (path, method), (_, statuses) in OPERATIONS.items():
        operation = contract["paths"][path][method]
        for status in statuses:
            response = operation["responses"][status]
            media = response["content"]
            if status == "200" and method == "get" and path.endswith("/evidence"):
                assert media == {"application/zip": {}}
                continue
            assert set(media) == {"application/json"}
            body = media["application/json"]
            if status in {"401", "402", "404", "409", "410", "422", "429", "503"} \
                    and not (path == "/readyz" and status == "503"):
                assert body["schema"] == ERROR_REF
            for example in ([body["example"]] if "example" in body else []):
                assert example.get("request_id") == UUID
                assert not set(example) & {"capability", "signature", "access_scope_hash"}
            for named in body.get("examples", {}).values():
                assert named["value"]["request_id"] == UUID


def test_location_and_idempotency_patterns_reject_ambiguous_inputs():
    contract = api()
    post = contract["paths"]["/v1/report-quotes"]["post"]
    key = post["parameters"][0]["schema"]
    for valid in ("a", "scope-1:report_2", "a" * 128):
        assert key["minLength"] <= len(valid) <= key["maxLength"]
        assert re.search(key["pattern"], valid)
    for invalid in ("", "a" * 129, "a b", "a\n", "é"):
        assert not (key["minLength"] <= len(invalid) <= key["maxLength"]
                    and re.search(key["pattern"], invalid))
    for status, prefix in (("201", "/v1/report-quotes/"),
                           ("202", "/v1/report-requests/")):
        schema = post["responses"][status]["headers"]["Location"]["schema"]
        assert re.search(schema["pattern"], prefix + UUID)
        for invalid in (prefix + "not-a-uuid", prefix + UUID + "\n", "https://evil.invalid" + prefix + UUID):
            assert not re.search(schema["pattern"], invalid)


def test_local_schema_references_and_all_declared_examples_validate():
    import mezo_evidence_support as c

    contract = api()
    for operation in (item[method] for item in contract["paths"].values()
                      for method in item if method in {"get", "post"}):
        for parameter in operation.get("parameters", []):
            c.assert_schema(parameter["schema"], document="openapi.json")
        for media in operation.get("requestBody", {}).get("content", {}).values():
            schema = media["schema"]
            c.assert_schema(schema, document="openapi.json")
            if "example" in media:
                c.validate(schema, media["example"], document="openapi.json")
        for response in operation["responses"].values():
            for header in response["headers"].values():
                c.assert_schema(header["schema"], document="openapi.json")
            for media_type, media in response.get("content", {}).items():
                if media_type == "application/zip":
                    assert media == {}
                    continue
                assert media_type == "application/json"
                schema = media["schema"]
                c.assert_schema(schema, document="openapi.json")
                for value in ([media["example"]] if "example" in media else []):
                    c.validate(schema, value, document="openapi.json")
                for named in media.get("examples", {}).values():
                    c.validate(schema, named["value"], document="openapi.json")
    header_schema = contract["paths"]["/healthz"]["get"]["responses"]["200"]["headers"]["X-Request-ID"]["schema"]
    c.validate(header_schema, UUID, document="openapi.json")
    for invalid in ("not-a-uuid", UUID + "\n"):
        with pytest.raises(c.ContractError):
            c.validate(header_schema, invalid, document="openapi.json")
    pending = contract["paths"]["/v1/report-quotes"]["post"]["responses"]["202"]["content"]["application/json"]
    for forbidden in ("quote_id", "terms", "report", "receipt", "vwap", "bundle"):
        with pytest.raises(c.ContractError):
            c.validate(pending["schema"], {**pending["example"], forbidden: "private"},
                       document="openapi.json")
