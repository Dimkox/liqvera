#!/usr/bin/python3.14
import argparse,json,re
FIELDS={'schema_version','transaction_id','controller_sha','policy_sha256','closure_sha256','oci_archive_sha256','journal_sha256','host_inventory_sha256','runner_api','operation_set_sha256','projections','rollback_capability','status'}
def verify(value,expected):
 if not isinstance(value,dict) or set(value)!=FIELDS or value!=expected: raise ValueError('HOST_RECEIPT_INVALID')
 if value['schema_version']!='claw-host-bootstrap-receipt-v1' or value['status']!='VERIFIED': raise ValueError('HOST_RECEIPT_SCHEMA')
 if not all(re.fullmatch('[0-9a-f]{64}',value[k]) for k in FIELDS if k.endswith('sha256')) or not re.fullmatch('[0-9a-f]{40}',value['controller_sha']): raise ValueError('HOST_RECEIPT_DIGEST')
 if value['rollback_capability']!='ROOT_JOURNAL_AND_CREDENTIAL_HMAC_RETAINED' or not value['transaction_id']: raise ValueError('HOST_RECEIPT_ROLLBACK')
 if not isinstance(value['projections'],dict) or not value['projections'] or not all(re.fullmatch('[0-9a-f]{64}',x) for x in value['projections'].values()): raise ValueError('HOST_RECEIPT_PROJECTION')
 if not isinstance(value['runner_api'],dict) or set(value['runner_api'])!={'repository','runner_id','runner_name','status','labels','matching_count','total_count'} or value['runner_api']['status']!='online' or value['runner_api']['matching_count']!=1: raise ValueError('HOST_RECEIPT_RUNNER_API')
 return value
def main(argv=None):
 p=argparse.ArgumentParser(); p.add_argument('--receipt',required=True); p.add_argument('--policy',required=True); p.add_argument('--closure',required=True); p.add_argument('--oci-archive',required=True); p.add_argument('--journal',required=True); p.add_argument('--controller-sha',required=True); a=p.parse_args(argv)
 try:
  try:
   from scripts.claw_host_bootstrap_transaction import receipt
  except ModuleNotFoundError:
   from claw_host_bootstrap_transaction import receipt
  value=json.load(open(a.receipt)); verify(value,receipt(a.policy,a.closure,a.oci_archive,a.journal,a.controller_sha)); return 0
 except (OSError,ValueError,KeyError,json.JSONDecodeError): return 2
if __name__=='__main__':raise SystemExit(main())
