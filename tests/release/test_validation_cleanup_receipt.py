import pytest
from scripts._trusted_receipt import ReceiptError
from scripts.write_validation_cleanup_receipt import write_receipt

def test_cleanup_writer_rejects_unproven_absence(tmp_path):
    value={"schema_version":"validation-cleanup-receipt-v1","repository":"Dimkox/multi-exchange-engine","head_sha":"b"*40,"run_id":1,"run_attempt":1,"job":"validate","shard":"0","owned_resources":[],"workspace_removed":True,"output_secrets_removed":True,"absence_proven":False,"validation_receipt_sha256":"a"*64,"status":"CLEANUP_VERIFIED"}
    with pytest.raises(ReceiptError,match="CLEANUP_UNPROVEN"): write_receipt(value,tmp_path/"x")
