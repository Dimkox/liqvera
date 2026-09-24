#!/usr/bin/env python3
import argparse,hashlib,json,sys
from pathlib import Path
if __package__ in (None,''):sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.oci_evidence_v2 import duplicate_reject,validate_schema,verify_receipt
def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument('--receipt',required=True);p.add_argument('--receipt-sha256',required=True);p.add_argument('--archive',required=True);p.add_argument('--layout',required=True);p.add_argument('--policy',required=True);p.add_argument('--closure',required=True);p.add_argument('--origin',required=True);p.add_argument('--commit',required=True);p.add_argument('--tree',required=True);p.add_argument('--source-image',required=True);a=p.parse_args(argv)
 data=Path(a.receipt).read_bytes();line=Path(a.receipt_sha256).read_text(encoding='ascii')
 expected_line=hashlib.sha256(data).hexdigest()+'  '+Path(a.receipt).name+'\n'
 if line!=expected_line:raise SystemExit('DETACHED_HASH_MISMATCH')
 value=json.loads(data,object_pairs_hook=duplicate_reject)
 schema=json.loads((Path(__file__).parents[1]/'schemas'/'oci-evidence-v2.schema.json').read_bytes(),object_pairs_hook=duplicate_reject);validate_schema(value,schema)
 verify_receipt(value,a.archive,a.layout,a.policy,a.closure,{'origin':a.origin,'commit':a.commit,'tree':a.tree,'source_image':a.source_image});return 0
if __name__=='__main__':raise SystemExit(main())
