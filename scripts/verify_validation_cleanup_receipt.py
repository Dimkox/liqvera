#!/usr/bin/env python3
from scripts._trusted_receipt import ReceiptError,read,validate
from scripts.write_validation_cleanup_receipt import FIELDS
import argparse,json
def verify_receipt(path,expected):
    value=read(path); validate(value,FIELDS,"validation-cleanup-receipt-v1")
    if value!=expected or value["status"]!="CLEANUP_VERIFIED" or value["absence_proven"] is not True: raise ReceiptError("CLEANUP_UNPROVEN")
    return value
def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--receipt",required=True); p.add_argument("--expected",required=True); a=p.parse_args(argv)
    verify_receipt(__import__('pathlib').Path(a.receipt),json.load(open(a.expected,encoding="utf-8"))); return 0
if __name__=="__main__": raise SystemExit(main())
