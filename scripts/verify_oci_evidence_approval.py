#!/usr/bin/env python3
import argparse,hashlib,json,sys
from pathlib import Path
if __package__ in (None,''):sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
EXPECTED_APPROVAL_POLICY_PATH='ci/claw/oci-evidence-approval.json'
try:
 from scripts.oci_evidence_v2 import duplicate_reject,verify_receipt
except ModuleNotFoundError:
 from oci_evidence_v2 import duplicate_reject,verify_receipt
class Once(argparse.Action):
 def __call__(self,parser,namespace,values,option_string=None):
  if getattr(namespace,self.dest,None) is not None:parser.error(f'argument {option_string}: may not be repeated')
  setattr(namespace,self.dest,values)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main(argv=None):
 p=argparse.ArgumentParser();
 for name in ('policy','approval','receipt','receipt-sha256','archive','layout','closure'):p.add_argument('--'+name,required=True)
 p.add_argument('--approval-policy-path',required=True,action=Once);p.add_argument('--origin',required=True);a=p.parse_args(argv)
 if a.approval_policy_path!=EXPECTED_APPROVAL_POLICY_PATH:p.error('CURRENT_POLICY_APPROVAL_PATH')
 policy=json.loads(Path(a.policy).read_bytes(),object_pairs_hook=duplicate_reject);approval=json.loads(Path(a.approval).read_bytes(),object_pairs_hook=duplicate_reject);receipt=json.loads(Path(a.receipt).read_bytes(),object_pairs_hook=duplicate_reject)
 fields={'schema_version','authority','status','not_host_receipt','source_image','source_commit','source_tree','receipt_sha256','sidecar_file_sha256','evidence_policy_sha256','closure_sha256','archive','manifest','config','layers','rootfs_sha256','executable_sha256','version_execution','external_locator','v1_receipt_accepted'}
 if set(approval)!=fields or approval['schema_version']!='oci-evidence-approval-v1' or approval['external_locator']!='OWNER_PROVIDED_EXACT_ARTIFACT_ROOT' or approval['authority']!='NONE' or approval['status']!='PRE_HOST_OCI_EVIDENCE_APPROVED' or approval['not_host_receipt'] is not True or approval['v1_receipt_accepted'] is not False:raise ValueError('APPROVAL_NOT_CLOSED')
 if policy.get('authority')!='NONE' or policy.get('status')!='PRE_HOST_OCI_EVIDENCE_APPROVED' or policy.get('image')!=approval['source_image'] or policy.get('oci_archive_sha256')!=approval['archive']['sha256'] or policy.get('oci_evidence_approval')!=a.approval_policy_path:raise ValueError('CURRENT_POLICY_BINDING')
 if sha(a.receipt)!=approval['receipt_sha256'] or sha(a.receipt_sha256)!=approval['sidecar_file_sha256'] or sha(a.archive)!=approval['archive']['sha256'] or Path(a.archive).stat().st_size!=approval['archive']['size']:raise ValueError('APPROVED_BYTES_MISMATCH')
 if Path(a.receipt_sha256).read_text(encoding='ascii')!=approval['receipt_sha256']+'  '+Path(a.receipt).name+'\n':raise ValueError('DETACHED_HASH_MISMATCH')
 if sha(a.closure)!=approval['closure_sha256'] or receipt['inputs']['policy_sha256']!=approval['evidence_policy_sha256'] or receipt['inputs']['closure_sha256']!=approval['closure_sha256'] or receipt['local_verification']['rootfs_sha256']!=approval['rootfs_sha256'] or receipt['local_verification']['actionlint']['sha256']!=approval['executable_sha256']:raise ValueError('APPROVED_PROJECTION_MISMATCH')
 if receipt['local_verification']['actionlint']['version_execution']!='PENDING_UNTIL_ROOTLESS_HOST_SMOKE' or approval['version_execution']!='PENDING_UNTIL_ROOTLESS_HOST_SMOKE':raise ValueError('HOST_SMOKE_STATE')
 if approval['archive']!={'name':Path(a.archive).name,'format':'docker-save-tar','size':Path(a.archive).stat().st_size,'sha256':sha(a.archive)} or approval['manifest']!=receipt['oci_layout_verification']['manifest_digest'] or approval['config']!=receipt['local_verification']['config_digest'] or approval['layers']!=[x['digest'] for x in receipt['local_verification']['layers']]:raise ValueError('APPROVED_GRAPH_MISMATCH')
 verify_receipt(receipt,a.archive,a.layout,None,a.closure,{'origin':a.origin,'commit':approval['source_commit'],'tree':approval['source_tree'],'source_image':approval['source_image']});return 0
if __name__=='__main__':raise SystemExit(main())
