"""The action writer's actual output must satisfy the independent export schema."""
import json
import subprocess
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def action():
    script = """
import {TroveActionStore} from './apps/mezo-web/src/trove-action-receipts.ts';
import {prepareTroveAction} from './apps/mezo-web/src/trove-transactions.ts';
import {troveProvider,borrower} from './apps/mezo-web/test/helpers/trove-provider.mjs';
const data=new Map();
const disk={getItem:k=>data.get(k)??null,setItem:(k,v)=>data.set(k,v),removeItem:k=>data.delete(k)};
const store=new TroveActionStore(disk,{report_id:'report-schema',report_sha256:'d'.repeat(64)},borrower);
store.begin(await prepareTroveAction(troveProvider(),borrower,{kind:'repay',amount:'0.5'}));
console.log(store.exportJson());
"""
    result = subprocess.run(
        ["node", "--input-type=module", "-"], input=script, cwd=ROOT,
        capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout)[0]


def test_actual_action_export_matches_schema(action):
    schema = json.loads((ROOT / "schemas/liqvera-trove-action-v1.schema.json").read_text())
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.validate(action, schema, format_checker=jsonschema.FormatChecker())


@pytest.mark.parametrize("change", [
    {"chain_id": 1}, {"amount": "0.5"}, {"report_sha256": "bad"},
    {"state": "confirmed", "receipt_status": None},
])
def test_action_schema_rejects_wrong_network_units_binding_and_confirmation(action, change):
    schema = json.loads((ROOT / "schemas/liqvera-trove-action-v1.schema.json").read_text())
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({**action, **change}, schema)
