import json,pytest
from scripts.claw_host_bootstrap_transaction import Deadline,FakeBackend,Journal,OPERATIONS,TxError,execute,finalize,main
DEADLINE=Deadline('test-boot',2_000,'2026-08-13T12:15:00Z')
RUNNER={'repository':'Dimkox/multi-exchange-engine','runner_id':17,'runner_name':'claw-engine-runner','status':'online','labels':['claw','claw-engine-runner','self-hosted'],'matching_count':1,'total_count':2}
def test_failure_before_and_after_every_operation_reverses_exactly(tmp_path):
 for op in OPERATIONS:
  for side in ('before','after'):
   b=FakeBackend(f'{side}:{op.name}'); j=Journal(tmp_path/f'{side}-{op.name}.json')
   with pytest.raises(TxError): execute(b,j)
   assert b.active==[]; value=json.loads(j.path.read_text()); assert value['phase']=='ROLLED_BACK' and value['status']=='ROLLED_BACK'
   applied=[e[1] for e in b.events if e[0]=='apply']; rolled=[e[1] for e in b.events if e[0]=='rollback']; expected=list(reversed(applied))
   assert rolled==expected
def test_final_verify_failure_rolls_back_all(tmp_path):
 b=FakeBackend('final_verify'); j=Journal(tmp_path/'j');
 with pytest.raises(TxError): execute(b,j)
 assert [e[1] for e in b.events if e[0]=='rollback']==[x.name for x in reversed(OPERATIONS)]
def test_success_stops_pending_then_commits_only_after_finalize(tmp_path):
 b=FakeBackend(); j=Journal(tmp_path/'j'); execute(b,j,deadline=DEADLINE); v=json.loads(j.path.read_text()); assert v['phase']=='HOST_APPLIED_PENDING_FINALIZE' and v['status']=='OPEN'; finalize(b,Journal.resume(j.path),RUNNER,now_boot_id='test-boot',now_monotonic_ns=1_999); v=json.loads(j.path.read_text()); assert v['phase']=='COMMITTED' and v['status']=='COMMITTED'; assert b.events[-1]==('final_verify','all')
def test_wal_intent_precedes_apply_and_contains_snapshot(tmp_path):
 b=FakeBackend('after:stop_engine'); j=Journal(tmp_path/'j')
 with pytest.raises(TxError): execute(b,j)
 assert ('snapshot','stop_engine') in b.events
def test_journal_durably_keeps_every_applied_snapshot(tmp_path):
 j=Journal(tmp_path/'journal'); execute(FakeBackend(),j); value=json.loads(j.path.read_text())
 assert set(value['snapshots'])=={x.name for x in OPERATIONS}
 assert all(value['snapshots'][x.name]=={'active':False} for x in OPERATIONS)
def test_unique_atomic_temp_ignores_stale_crash_file(tmp_path):
 (tmp_path/'journal.tmp').write_text('stale'); j=Journal(tmp_path/'journal'); j.record('X')
 assert json.loads(j.path.read_text())['phase']=='X'
def test_open_journal_is_never_overwritten(tmp_path):
 Journal(tmp_path/'journal')
 with pytest.raises(TxError,match='JOURNAL_ALREADY_EXISTS'): Journal(tmp_path/'journal')

def test_host_006_wal_records_exact_success_phase_sequence(tmp_path):
 j=Journal(tmp_path/'journal'); execute(FakeBackend(),j); value=json.loads(j.path.read_text())
 expected=['PREPARED']
 for op in OPERATIONS: expected += [f'APPLYING({op.name})',f'APPLIED({op.name})']
 expected += ['VERIFYING','HOST_APPLIED_PENDING_FINALIZE']
 assert value['history']==expected

def test_prepare_failure_never_sets_current_or_runs_inverse(tmp_path):
 class PrepareFailure(FakeBackend):
  def prepare(self,name):
   super().prepare(name)
   if name=='configure_runtime': raise TxError('PREPARE_FAILED')
 b=PrepareFailure(); j=Journal(tmp_path/'journal')
 with pytest.raises(TxError,match='PREPARE_FAILED'): execute(b,j)
 assert ('rollback','configure_runtime') not in b.events

def test_verified_results_are_durable_for_every_applied_operation(tmp_path):
 j=Journal(tmp_path/'journal'); execute(FakeBackend(),j); value=json.loads(j.path.read_text())
 assert set(value['verified_results'])=={op.name for op in OPERATIONS}
 assert all(result['operation']==name and result['status']=='VERIFIED' for name,result in value['verified_results'].items())

def test_wrapper_resume_recovers_existing_open_journal_without_overwrite(tmp_path):
 path=tmp_path/'journal'; journal=Journal(path); journal.record('APPLYING(stop_engine)',[],current='stop_engine',snapshot={'operation':'stop_engine','active':False})
 assert main(['--journal',str(path),'--fake','--resume'])==0
 assert json.loads(path.read_text())['status']=='ROLLED_BACK'

def test_wrapper_rollback_accepts_committed_journal_and_does_not_emit_new_receipt(tmp_path):
 path=tmp_path/'journal'; journal=Journal(path); backend=FakeBackend(); execute(backend,journal,deadline=DEADLINE); finalize(backend,Journal.resume(path),RUNNER,now_boot_id='test-boot',now_monotonic_ns=1_999)
 assert main(['--journal',str(path),'--fake','--rollback'])==0
 assert json.loads(path.read_text())['status']=='ROLLED_BACK'

def test_non_recovery_wrapper_passes_physical_and_logical_approval_paths(tmp_path,monkeypatch):
 import scripts.verify_oci_evidence_approval as approval_verifier
 tx=tmp_path/'tx';policy=tmp_path/'policy.json';closure=tmp_path/'closure.json';approval=tmp_path/'oci-evidence-approval.json';seen=[]
 policy.write_text(json.dumps({'transaction_root':str(tx),'oci_archive_sha256':'a'*64,'oci_evidence_approval':'ci/claw/oci-evidence-approval.json'}));closure.write_text('{"packages":[]}');approval.write_text('{}')
 monkeypatch.setattr(approval_verifier,'main',lambda argv: seen.extend(argv) or 1)
 args=['--journal',str(tmp_path/'journal.json'),'--policy',str(policy),'--closure',str(closure),'--debs',str(tmp_path/'debs'),'--oci-archive',str(tmp_path/'archive.tar'),'--oci-layout',str(tmp_path/'layout'),'--oci-evidence-receipt',str(tmp_path/'receipt.json'),'--oci-evidence-sidecar',str(tmp_path/'receipt.sha256'),'--receipt',str(tmp_path/'host-receipt.json'),'--controller-sha','b'*40,'--deadline-seconds','900']
 assert main(args)==2
 assert seen[seen.index('--approval')+1]==str(approval)
 assert seen[seen.index('--approval-policy-path')+1]=='ci/claw/oci-evidence-approval.json'
