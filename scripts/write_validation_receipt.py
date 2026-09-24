#!/usr/bin/env python3
import re
from scripts._trusted_receipt import ReceiptError,atomic_write,validate
import argparse,json
FIELDS={"schema_version","repository","pr_number","head_sha","head_tree","controller_sha","controller_tree","workflow_blob_sha","archive_sha256","policy_sha256","image_digest","command_set_sha256","run_id","run_attempt","job","shard","result_sha256","status"}
def write_receipt(value,path):
    validate(value,FIELDS,"validation-receipt-v1")
    if not re.fullmatch(r"[^@\s]+@sha256:[0-9a-f]{64}",str(value["image_digest"])): raise ReceiptError("IMAGE_DIGEST_INVALID")
    if value["status"]!="VALIDATION_SUCCEEDED": raise ReceiptError("STATUS_INVALID")
    atomic_write(value,path)
def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--input",required=True); p.add_argument("--output",required=True); a=p.parse_args(argv)
    write_receipt(json.load(open(a.input,encoding="utf-8")),__import__('pathlib').Path(a.output)); return 0
if __name__=="__main__": raise SystemExit(main())
