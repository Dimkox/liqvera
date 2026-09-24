#!/usr/bin/python3.14
import json
from pathlib import Path
try:
 from scripts.claw_host_bootstrap_transaction import atomic,receipt
except ModuleNotFoundError:
 from claw_host_bootstrap_transaction import atomic,receipt
def write(policy,closure,oci,journal,output,controller_sha=None):
 j=json.loads(Path(journal).read_text())
 if j.get('phase')!='COMMITTED' or j.get('status')!='COMMITTED': raise ValueError('HOST_JOURNAL_NOT_COMMITTED')
 value=receipt(policy,closure,oci,journal,controller_sha); atomic(Path(output),(json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode()); return value
