import json
from pathlib import Path

import pytest

from scripts.write_source_materialization_receipt import FIELDS, ObservationError, write_observation


def observation():
    h = "a" * 64; s = "b" * 40
    return {"schema_version":"source-materialization-observation-v1","authority":"NONE","repository":"Dimkox/multi-exchange-engine","pr_number":7,"head_sha":s,"head_tree":s,"base_sha":s,"controller_sha":s,"controller_tree":s,"workflow_path":".github/workflows/validate-pr-on-claw.yml","workflow_blob_sha":s,"action_set_sha256":h,"input_sha256":h,"archive_sha256":h,"member_policy_sha256":h,"approval_comment_id":9,"approval_comment_url":"https://github.com/Dimkox/multi-exchange-engine/pull/7#issuecomment-9","approval_owner_id":42,"approval_owner_login":"Dimkox","approval_body_sha256":h,"approval_nonce":"N"*43,"approval_created_at":"2026-08-12T00:00:00Z","cleanup":{"intent":"REMOVE_ALL","outcome":"REMOVED"}}


def test_atomic_closed_non_authoritative_observation(tmp_path):
    path = tmp_path / "observation.json"
    write_observation(observation(), path)
    assert json.loads(path.read_text())["authority"] == "NONE"


def test_rejects_extra_and_receipt_authority(tmp_path):
    value = observation(); value["receipt"] = True
    with pytest.raises(ObservationError, match="OBSERVATION_UNKNOWN_FIELD"): write_observation(value, tmp_path / "x")


def test_writer_contract_has_schema_parity(tmp_path):
    value=observation(); schema=json.loads(Path("schemas/source-materialization-receipt-v1.schema.json").read_text())
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == FIELDS == set(value)
    assert schema["properties"]["authority"]["const"] == "NONE"
    assert schema["properties"]["workflow_path"]["const"] == ".github/workflows/validate-pr-on-claw.yml"
    for field,bad in (("pr_number",True),("approval_comment_id",0),("workflow_path","other"),("approval_nonce","short"),("repository","a"*100+"/"+"b"*102)):
        mutated={**value,field:bad}
        with pytest.raises(ObservationError): write_observation(mutated,tmp_path/field)
