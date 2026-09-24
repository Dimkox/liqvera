#!/usr/bin/env python3
from scripts._trusted_receipt import ReceiptError,atomic_write,validate
FIELDS={"schema_version","repository","controller_sha","controller_tree","workflow_blob_sha","probe_head_sha","probe_head_tree","actionlint_sha256","graph_result_sha256","sandbox_policy_sha256","validation_receipt_sha256","cleanup_receipt_sha256","run_id","run_attempt","runner_name","status"}
def write_receipt(value,path):
    validate(value,FIELDS,"controller-self-validation-receipt-v1")
    if value["runner_name"]!="claw-engine-runner": raise ReceiptError("RUNNER_INVALID")
    if value["status"]!="SELF_VALIDATION_VERIFIED": raise ReceiptError("STATUS_INVALID")
    atomic_write(value,path)
def main(argv=None):
    import argparse,json
    from pathlib import Path
    p=argparse.ArgumentParser(); p.add_argument("--input",required=True); p.add_argument("--output",required=True); a=p.parse_args(argv)
    write_receipt(json.load(open(a.input,encoding="utf-8")),Path(a.output)); return 0
if __name__=="__main__": raise SystemExit(main())
