import hashlib,json,pytest
from scripts.claw_host_bootstrap_transaction import Journal,receipt
from scripts.verify_claw_host_bootstrap_receipt import verify

def test_receipt_binds_journal_controller_inventory_projections_and_rollback(tmp_path):
 policy=tmp_path/'policy'; closure=tmp_path/'closure'; oci=tmp_path/'oci'; policy.write_text('{}'); closure.write_text('{}'); oci.write_bytes(b'oci')
 names=('freeze_inputs','snapshot_host','install_packages','create_identity','configure_subids','configure_runtime','stop_engine','transfer_ownership','install_dropin','load_oci','rootless_smoke','host_capability_precondition','start_engine','runner_api_canary','app_canary')
 journal=Journal(tmp_path/'transaction-7.json'); results={name:{'operation':name,'status':'VERIFIED','evidence':name} for name in names}; results['snapshot_host']['inventory_sha256']='9'*64; runner={'repository':'Dimkox/multi-exchange-engine','runner_id':1,'runner_name':'claw-engine-runner','status':'online','labels':['claw','claw-engine-runner','self-hosted'],'matching_count':1,'total_count':1}; results['runner_api_canary']['runner_api']=runner; journal.value['verified_results']=results; journal.record('COMMITTED',list(names),status='COMMITTED',finalize_projection=runner)
 value=receipt(policy,closure,oci,journal.path,'a'*40); assert verify(value,value)==value
 assert value['transaction_id']=='transaction-7' and value['controller_sha']=='a'*40
 assert value['host_inventory_sha256']==results['snapshot_host']['inventory_sha256']
 assert value['runner_api']==results['runner_api_canary']['runner_api']
 assert value['rollback_capability']=='ROOT_JOURNAL_AND_CREDENTIAL_HMAC_RETAINED'
 assert value['projections']['rootless_smoke']==hashlib.sha256(json.dumps(results['rootless_smoke'],sort_keys=True,separators=(',',':')).encode()).hexdigest()

def test_receipt_requires_committed_journal_and_every_verified_projection(tmp_path):
 policy=tmp_path/'policy'; closure=tmp_path/'closure'; oci=tmp_path/'oci'; policy.write_text('{}'); closure.write_text('{}'); oci.write_bytes(b'oci'); journal=Journal(tmp_path/'tx.json')
 with pytest.raises(Exception,match='HOST_JOURNAL_NOT_COMMITTED'): receipt(policy,closure,oci,journal.path,'a'*40)
 journal.value['phase']='COMMITTED'; journal.value['status']='COMMITTED'; journal.record('COMMITTED',status='COMMITTED',finalize_projection={'repository':'Dimkox/multi-exchange-engine'})
 with pytest.raises(Exception,match='HOST_VERIFIED_RESULTS_INCOMPLETE'): receipt(policy,closure,oci,journal.path,'a'*40)

def test_receipt_rejects_projection_or_rollback_lie(tmp_path):
 from scripts.verify_claw_host_bootstrap_receipt import verify
 import pytest
 fields={'schema_version':'claw-host-bootstrap-receipt-v1','transaction_id':'x','controller_sha':'a'*40,'policy_sha256':'b'*64,'closure_sha256':'c'*64,'oci_archive_sha256':'d'*64,'journal_sha256':'e'*64,'host_inventory_sha256':'f'*64,'runner_api':{'repository':'r','runner_id':1,'runner_name':'n','status':'online','labels':['self-hosted'],'matching_count':1,'total_count':1},'operation_set_sha256':'1'*64,'projections':{'x':'2'*64},'rollback_capability':'ROOT_JOURNAL_AND_CREDENTIAL_HMAC_RETAINED','status':'VERIFIED'}
 with pytest.raises(ValueError): verify(fields,fields|{'rollback_capability':'lie'})
 with pytest.raises(ValueError): verify(fields|{'projections':{}},fields|{'projections':{}})
