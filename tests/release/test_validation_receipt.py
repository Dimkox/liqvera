import pytest
from scripts._trusted_receipt import ReceiptError
from scripts.write_validation_receipt import write_receipt

def test_validation_receipt_rejects_mutable_image(tmp_path):
    value={k:"a"*64 for k in ("archive_sha256","policy_sha256","command_set_sha256","result_sha256")}
    value.update(schema_version="validation-receipt-v1",repository="Dimkox/multi-exchange-engine",pr_number=1,head_sha="b"*40,head_tree="b"*40,controller_sha="b"*40,controller_tree="b"*40,workflow_blob_sha="b"*40,image_digest="image:latest",run_id=1,run_attempt=1,job="validate",shard="0",status="VALIDATION_SUCCEEDED")
    with pytest.raises(ReceiptError,match="IMAGE_DIGEST_INVALID"): write_receipt(value,tmp_path/"x")
