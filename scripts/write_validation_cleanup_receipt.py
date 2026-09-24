#!/usr/bin/env python3
from scripts._trusted_receipt import ReceiptError,atomic_write,validate
import argparse,json
FIELDS={"schema_version","repository","head_sha","run_id","run_attempt","job","shard","owned_resources","workspace_removed","output_secrets_removed","absence_proven","validation_receipt_sha256","status"}
def write_receipt(value,path):
    validate(value,FIELDS,"validation-cleanup-receipt-v1")
    if value["absence_proven"] is not True or value["workspace_removed"] is not True or value["output_secrets_removed"] is not True: raise ReceiptError("CLEANUP_UNPROVEN")
    if value["status"]!="CLEANUP_VERIFIED": raise ReceiptError("CLEANUP_STATUS_INVALID")
    atomic_write(value,path)
def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--input",required=True); p.add_argument("--output",required=True); a=p.parse_args(argv)
    write_receipt(json.load(open(a.input,encoding="utf-8")),__import__('pathlib').Path(a.output)); return 0
if __name__=="__main__": raise SystemExit(main())
