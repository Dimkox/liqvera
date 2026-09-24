#!/usr/bin/env python3
from scripts._trusted_receipt import ReceiptError,read,validate
from scripts.write_controller_self_validation_receipt import FIELDS
def verify_receipt(path,expected):
    value=read(path); validate(value,FIELDS,"controller-self-validation-receipt-v1")
    if value!=expected or value["runner_name"]!="claw-engine-runner" or value["status"]!="SELF_VALIDATION_VERIFIED": raise ReceiptError("SELF_VALIDATION_INVALID")
    return value
def main(argv=None):
    import argparse,json
    from pathlib import Path
    p=argparse.ArgumentParser(); p.add_argument("--receipt",required=True); p.add_argument("--expected",required=True); a=p.parse_args(argv)
    verify_receipt(Path(a.receipt),json.load(open(a.expected,encoding="utf-8"))); return 0
if __name__=="__main__": raise SystemExit(main())
