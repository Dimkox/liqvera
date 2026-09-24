import pytest
from scripts._trusted_receipt import ReceiptError
from scripts.write_controller_self_validation_receipt import write_receipt

def test_self_validation_writer_rejects_other_runner(tmp_path):
    value={"schema_version":"controller-self-validation-receipt-v1","repository":"Dimkox/multi-exchange-engine","controller_sha":"b"*40,"controller_tree":"b"*40,"workflow_blob_sha":"b"*40,"probe_head_sha":"b"*40,"probe_head_tree":"b"*40,"actionlint_sha256":"a"*64,"graph_result_sha256":"a"*64,"sandbox_policy_sha256":"a"*64,"validation_receipt_sha256":"a"*64,"cleanup_receipt_sha256":"a"*64,"run_id":1,"run_attempt":1,"runner_name":"other","status":"SELF_VALIDATION_VERIFIED"}
    with pytest.raises(ReceiptError,match="RUNNER_INVALID"): write_receipt(value,tmp_path/"x")
