import json,os,stat
import pytest
from scripts.claw_host_bootstrap_transaction import CredentialCommitments,Deadline,Journal,OPERATIONS,TxError,create_credential_binding,durable_rmdir_empty_private,durable_unlink,is_terminal_rolled_back_journal,main,release_completed_rollback_binding

def binding(tx='tx-1'):
 return {'transaction_id':tx,'controller_sha':'a'*40,'policy_sha256':'b'*64}

def rolled_back(journal):
 journal.record('ROLLING_BACK',[]);journal.record('ROLLED_BACK',[],status='ROLLED_BACK');return journal

def test_terminal_validator_accepts_full_committed_owner_rollback():
 snapshots={op.name:{'operation':op.name} for op in OPERATIONS};results={op.name:{'operation':op.name,'status':'VERIFIED'} for op in OPERATIONS};runner={'repository':'Dimkox/multi-exchange-engine','runner_id':17,'runner_name':'claw-engine-runner','status':'online','labels':['claw','claw-engine-runner','self-hosted'],'matching_count':1,'total_count':1}
 history=['PREPARED']+[phase for op in OPERATIONS for phase in (f'APPLYING({op.name})',f'APPLIED({op.name})')]+['VERIFYING','HOST_APPLIED_PENDING_FINALIZE','FINALIZING','VERIFIED','COMMITTED','ROLLING_BACK','ROLLED_BACK']
 value={'schema_version':'claw-host-journal-v1','phase':'ROLLED_BACK','history':history,'applied':[],'current':None,'snapshot':None,'snapshots':snapshots,'verified_results':results,'deadline':Deadline('boot-a',2000,'2026-08-13T12:15:00Z').as_dict(),'finalize_projection':runner,'status':'ROLLED_BACK'}
 assert is_terminal_rolled_back_journal(value)

def test_terminal_validator_accepts_blocked_retry_after_attempted_operation():
 value={'schema_version':'claw-host-journal-v1','phase':'ROLLED_BACK','history':['PREPARED','APPLYING(freeze_inputs)','ROLLING_BACK','ROLLBACK_BLOCKED','ROLLING_BACK','ROLLED_BACK'],'applied':[],'current':None,'snapshot':None,'snapshots':{'freeze_inputs':{'operation':'freeze_inputs'}},'verified_results':{},'deadline':None,'finalize_projection':None,'status':'ROLLED_BACK'}
 assert is_terminal_rolled_back_journal(value)

def tree(tmp_path):
 root=tmp_path/'runner'; root.mkdir(); (root/'.runner').write_bytes(b'runner-secret'); (root/'.credentials').write_bytes(b'credential-secret'); return root

def test_credential_binding_is_o_excl_and_original_bytes_survive_second_apply(tmp_path):
 path=tmp_path/'tx'/'credential-binding.json';first=binding();create_credential_binding(path,first);before=path.read_bytes()
 with pytest.raises(FileExistsError):create_credential_binding(path,binding('different')|{'controller_sha':'c'*40})
 assert path.read_bytes()==before and json.loads(path.read_text())==first

def test_main_new_apply_releases_only_completed_rollback_binding(tmp_path,monkeypatch):
 import hashlib
 import scripts.claw_host_bootstrap_transaction as transaction
 import scripts.verify_oci_evidence_approval as approval_verifier
 durable=tmp_path/'durable';policy=tmp_path/'policy.json';closure=tmp_path/'closure.json';debs=tmp_path/'debs';debs.mkdir()
 approval=tmp_path/'approval.json';archive=tmp_path/'image.tar';layout=tmp_path/'layout';layout.mkdir();evidence=tmp_path/'evidence.json';sidecar=tmp_path/'evidence.sha256';receipt=tmp_path/'receipt.json'
 for path in (approval,archive,evidence,sidecar):path.write_bytes(b'x')
 policy.write_text(json.dumps({'authority':'NONE','status':'PRE_HOST_OCI_EVIDENCE_APPROVED','transaction_root':str(durable),'oci_archive_sha256':'a'*64,'image':'image@sha256:'+'b'*64,'oci_evidence_approval':'approval.json'}))
 closure.write_text('{"packages":[]}')
 old_id='a'*32;new_id='b'*32;old_journal=Journal(durable/f'{old_id}.json');os.chmod(durable,0o700);rolled_back(old_journal)
 policy_sha=hashlib.sha256(policy.read_bytes()).hexdigest();create_credential_binding(durable/'credential-binding.json',{'transaction_id':old_id,'controller_sha':'c'*40,'policy_sha256':policy_sha})
 monkeypatch.setattr(approval_verifier,'main',lambda argv:0);monkeypatch.setattr(transaction,'RealBackend',lambda *args,**kwargs:object());monkeypatch.setattr(transaction,'execute',lambda *args,**kwargs:None)
 args=['--policy',str(policy),'--closure',str(closure),'--journal',str(durable/f'{new_id}.json'),'--receipt',str(receipt),'--debs',str(debs),'--oci-archive',str(archive),'--oci-layout',str(layout),'--oci-evidence-receipt',str(evidence),'--oci-evidence-sidecar',str(sidecar),'--controller-sha','d'*40,'--deadline-seconds','900']
 assert main(args)==0
 assert json.loads((durable/'credential-binding.json').read_text())=={'transaction_id':new_id,'controller_sha':'d'*40,'policy_sha256':policy_sha}
 assert json.loads((durable/f'{old_id}.json').read_text())['phase']=='ROLLED_BACK'

def test_main_rollback_cleans_prepared_journal_blocked_by_prior_completed_binding(tmp_path):
 import hashlib
 durable=tmp_path/'durable';policy=tmp_path/'policy.json';closure=tmp_path/'closure.json';receipt=tmp_path/'receipt.json'
 policy.write_text(json.dumps({'authority':'NONE','status':'PRE_HOST_OCI_EVIDENCE_APPROVED','transaction_root':str(durable),'oci_archive_sha256':'a'*64,'image':'image@sha256:'+'b'*64,'oci_evidence_approval':'approval.json'}));closure.write_text('{"packages":[]}')
 old_id='a'*32;new_id='b'*32;old_journal=Journal(durable/f'{old_id}.json');os.chmod(durable,0o700);rolled_back(old_journal);Journal(durable/f'{new_id}.json')
 create_credential_binding(durable/'credential-binding.json',{'transaction_id':old_id,'controller_sha':'c'*40,'policy_sha256':hashlib.sha256(policy.read_bytes()).hexdigest()})
 args=['--policy',str(policy),'--closure',str(closure),'--journal',str(durable/f'{new_id}.json'),'--receipt',str(receipt),'--rollback']
 assert main(args)==0
 assert not (durable/f'{new_id}.json').exists() and not (durable/'credential-binding.json').exists()
 assert json.loads((durable/f'{old_id}.json').read_text())['phase']=='ROLLED_BACK'

@pytest.mark.skipif(os.name!='posix' or os.geteuid()!=0,reason='root-owned journal contract')
@pytest.mark.parametrize('field,value',[('schema_version','claw-host-journal-v2'),('phase','APPLYING'),('history',['CORRUPT','PREPARED']),('applied',['freeze_inputs']),('current','freeze_inputs'),('snapshots',{'x':{}}),('verified_results',{'x':{}}),('snapshot',{}),('deadline',{}),('finalize_projection',{}),('status','COMMITTED')])
def test_main_rollback_rejects_malformed_fresh_prepared_journal(tmp_path,field,value):
 import hashlib
 durable=tmp_path/'durable';policy=tmp_path/'policy.json';closure=tmp_path/'closure.json';receipt=tmp_path/'receipt.json';old_id='a'*32;new_id='b'*32
 policy.write_text(json.dumps({'authority':'NONE','status':'PRE_HOST_OCI_EVIDENCE_APPROVED','transaction_root':str(durable),'oci_archive_sha256':'a'*64,'image':'image@sha256:'+'b'*64,'oci_evidence_approval':'approval.json'}));closure.write_text('{"packages":[]}')
 old=Journal(durable/f'{old_id}.json');os.chmod(durable,0o700);rolled_back(old);new=Journal(durable/f'{new_id}.json');new_value=json.loads(new.path.read_text());new_value[field]=value;new.path.write_text(json.dumps(new_value));os.chmod(new.path,0o600)
 binding_path=durable/'credential-binding.json';create_credential_binding(binding_path,{'transaction_id':old_id,'controller_sha':'c'*40,'policy_sha256':hashlib.sha256(policy.read_bytes()).hexdigest()})
 args=['--policy',str(policy),'--closure',str(closure),'--journal',str(new.path),'--receipt',str(receipt),'--rollback']
 assert main(args)==2 and new.path.exists() and binding_path.exists()

@pytest.mark.skipif(os.name!='posix' or os.geteuid()!=0,reason='root-owned journal contract')
@pytest.mark.parametrize('field,value',[('history',['PREPARED',7,'ROLLED_BACK']),('history',['CORRUPT','ROLLED_BACK']),('history',['PREPARED','COMMITTED','ROLLED_BACK']),('history',['PREPARED','ROLLED_BACK']),('history',['PREPARED','ROLLING_BACK','ROLLBACK_BLOCKED','ROLLING_BACK','ROLLED_BACK']),('history',['PREPARED','APPLIED(start_engine)','APPLYING(freeze_inputs)','ROLLING_BACK','ROLLED_BACK']),('snapshots','CORRUPT'),('snapshots',{}),('snapshots',{'freeze_inputs':[]}),('snapshots',{'unknown':{}}),('snapshots',{'freeze_inputs':{'operation':'unknown'}}),('verified_results',[]),('verified_results',{}),('verified_results',{'unknown':{}}),('verified_results',{'freeze_inputs':{'operation':'unknown','status':'VERIFIED'}}),('verified_results',{'freeze_inputs':{'operation':'freeze_inputs','status':'CORRUPT'}}),('snapshot',{}),('deadline',{}),('finalize_projection',{})])
def test_main_rollback_preserves_binding_for_semantically_invalid_terminal_journal(tmp_path,field,value):
 import hashlib
 durable=tmp_path/'durable';policy=tmp_path/'policy.json';closure=tmp_path/'closure.json';receipt=tmp_path/'receipt.json';old_id='a'*32;new_id='b'*32
 policy.write_text(json.dumps({'authority':'NONE','status':'PRE_HOST_OCI_EVIDENCE_APPROVED','transaction_root':str(durable),'oci_archive_sha256':'a'*64,'image':'image@sha256:'+'b'*64,'oci_evidence_approval':'approval.json'}));closure.write_text('{"packages":[]}')
 old=Journal(durable/f'{old_id}.json');os.chmod(durable,0o700);rolled_back(old);old_value=json.loads(old.path.read_text())
 if field in {'snapshots','verified_results'}:old_value.update({'history':['PREPARED','APPLYING(freeze_inputs)','APPLIED(freeze_inputs)','ROLLING_BACK','ROLLED_BACK'],'snapshots':{'freeze_inputs':{'operation':'freeze_inputs'}},'verified_results':{'freeze_inputs':{'operation':'freeze_inputs','status':'VERIFIED'}}})
 old_value[field]=value;old.path.write_text(json.dumps(old_value));os.chmod(old.path,0o600);new=Journal(durable/f'{new_id}.json')
 binding_path=durable/'credential-binding.json';create_credential_binding(binding_path,{'transaction_id':old_id,'controller_sha':'c'*40,'policy_sha256':hashlib.sha256(policy.read_bytes()).hexdigest()})
 args=['--policy',str(policy),'--closure',str(closure),'--journal',str(new.path),'--receipt',str(receipt),'--rollback']
 assert main(args)==2 and old.path.exists() and new.path.exists() and binding_path.exists()

def test_main_rollback_rejects_and_preserves_dangling_binding_symlink(tmp_path):
 durable=tmp_path/'durable';policy=tmp_path/'policy.json';closure=tmp_path/'closure.json';receipt=tmp_path/'receipt.json';new_id='b'*32
 policy.write_text(json.dumps({'authority':'NONE','status':'PRE_HOST_OCI_EVIDENCE_APPROVED','transaction_root':str(durable),'oci_archive_sha256':'a'*64,'image':'image@sha256:'+'b'*64,'oci_evidence_approval':'approval.json'}));closure.write_text('{"packages":[]}');journal=Journal(durable/f'{new_id}.json');binding_path=durable/'credential-binding.json';binding_path.symlink_to(durable/'missing-binding')
 args=['--policy',str(policy),'--closure',str(closure),'--journal',str(journal.path),'--receipt',str(receipt),'--rollback']
 assert main(args)==2 and journal.path.exists() and binding_path.is_symlink()

@pytest.mark.skipif(os.name!='posix',reason='FIFO identity is POSIX-only')
def test_main_rollback_rejects_fifo_binding_without_reading_it(tmp_path):
 durable=tmp_path/'durable';policy=tmp_path/'policy.json';closure=tmp_path/'closure.json';receipt=tmp_path/'receipt.json';new_id='b'*32
 policy.write_text(json.dumps({'authority':'NONE','status':'PRE_HOST_OCI_EVIDENCE_APPROVED','transaction_root':str(durable),'oci_archive_sha256':'a'*64,'image':'image@sha256:'+'b'*64,'oci_evidence_approval':'approval.json'}));closure.write_text('{"packages":[]}');journal=Journal(durable/f'{new_id}.json');os.chmod(durable,0o700);binding_path=durable/'credential-binding.json';os.mkfifo(binding_path,0o600)
 args=['--policy',str(policy),'--closure',str(closure),'--journal',str(journal.path),'--receipt',str(receipt),'--rollback']
 assert main(args)==2 and journal.path.exists() and stat.S_ISFIFO(binding_path.lstat().st_mode)

@pytest.mark.skipif(os.name!='posix' or os.geteuid()!=0,reason='root-owned journal contract')
@pytest.mark.parametrize('kind',['symlink','hardlink'])
def test_main_rollback_rejects_linked_current_journal(tmp_path,kind):
 policy,closure,journal,receipt,tx=main_fixture(tmp_path,'missing_binding');outside=tmp_path/'outside.json';outside.write_bytes(journal.read_bytes());os.chmod(outside,0o600);journal.unlink()
 if kind=='symlink':journal.symlink_to(outside)
 else:os.link(outside,journal)
 args=['--policy',str(policy),'--closure',str(closure),'--journal',str(journal),'--receipt',str(receipt),'--rollback']
 assert main(args)==2 and outside.exists() and journal.exists()

def test_terminal_binding_missing_journal_fails_closed_and_preserves_binding(tmp_path):
 path=tmp_path/'credential-binding.json';value={'transaction_id':'a'*32,'controller_sha':'c'*40,'policy_sha256':'d'*64};create_credential_binding(path,value);before=path.read_bytes()
 with pytest.raises(TxError,match='TERMINAL_BINDING_JOURNAL'):release_completed_rollback_binding(tmp_path,path,'d'*64)
 assert path.read_bytes()==before

@pytest.mark.parametrize('kind',['symlink','hardlink'])
def test_terminal_binding_unsafe_file_identity_fails_closed(tmp_path,kind):
 durable=tmp_path/'durable';old_id='a'*32;journal=Journal(durable/f'{old_id}.json');os.chmod(durable,0o700);rolled_back(journal)
 outside=tmp_path/'outside-binding.json';create_credential_binding(outside,{'transaction_id':old_id,'controller_sha':'c'*40,'policy_sha256':'d'*64});path=durable/'credential-binding.json'
 if kind=='symlink':path.symlink_to(outside)
 else:os.link(outside,path)
 with pytest.raises(TxError,match='TERMINAL_BINDING_INVALID'):release_completed_rollback_binding(durable,path,'d'*64)
 assert path.exists() and outside.exists()

def test_terminal_binding_corrupt_journal_has_stable_failure_and_preserves_binding(tmp_path):
 old_id='a'*32;path=tmp_path/'credential-binding.json';create_credential_binding(path,{'transaction_id':old_id,'controller_sha':'c'*40,'policy_sha256':'d'*64});before=path.read_bytes();(tmp_path/f'{old_id}.json').write_text('{')
 with pytest.raises(TxError,match='TERMINAL_BINDING_JOURNAL'):release_completed_rollback_binding(tmp_path,path,'d'*64)
 assert path.read_bytes()==before

@pytest.mark.skipif(os.name!='posix' or os.geteuid()!=0,reason='root-owned state contract')
@pytest.mark.parametrize('target,drift',[('binding','mode'),('journal','mode'),('binding','owner'),('journal','owner')])
def test_terminal_binding_requires_root_owned_private_files(tmp_path,target,drift):
 old_id='a'*32;journal=Journal(tmp_path/f'{old_id}.json');rolled_back(journal);path=tmp_path/'credential-binding.json';create_credential_binding(path,{'transaction_id':old_id,'controller_sha':'c'*40,'policy_sha256':'d'*64});victim=path if target=='binding' else journal.path
 if drift=='mode':os.chmod(victim,0o640)
 else:os.chown(victim,65534,65534)
 before=path.read_bytes()
 with pytest.raises(TxError):release_completed_rollback_binding(tmp_path,path,'d'*64)
 assert path.read_bytes()==before

@pytest.mark.parametrize('kind',['open','committed','blocked','policy_drift','invalid_transaction','empty_state','key_only','map_only','dangling_state_symlink'])
def test_terminal_binding_nonterminal_or_ambiguous_state_is_preserved(tmp_path,kind):
 old_id='invalid' if kind=='invalid_transaction' else 'a'*32;path=tmp_path/'credential-binding.json';policy_sha='e'*64 if kind=='policy_drift' else 'd'*64
 if kind!='invalid_transaction':
  journal=Journal(tmp_path/f'{old_id}.json')
  if kind=='committed':journal.record('COMMITTED',[],status='COMMITTED')
  elif kind=='blocked':journal.record('ROLLBACK_BLOCKED',[],status='OPEN')
  elif kind not in {'open','policy_drift'}:rolled_back(journal)
 create_credential_binding(path,{'transaction_id':old_id,'controller_sha':'c'*40,'policy_sha256':policy_sha});before=path.read_bytes()
 if kind in {'empty_state','key_only','map_only'}:
  state=tmp_path/'credential-state';state.mkdir(mode=0o700)
  if kind=='key_only':(state/'key').write_bytes(b'x')
  if kind=='map_only':(state/'map').write_bytes(b'x')
 if kind=='dangling_state_symlink':(tmp_path/'credential-state').symlink_to(tmp_path/'missing-state')
 with pytest.raises(TxError):release_completed_rollback_binding(tmp_path,path,'d'*64)
 assert path.read_bytes()==before

def test_prepared_journal_precedes_binding_and_failed_own_inode_is_cleaned(tmp_path,monkeypatch):
 journal=tmp_path/'tx'/'journal.json';Journal(journal);path=tmp_path/'tx'/'credential-binding.json';real_write=os.write
 monkeypatch.setattr(os,'write',lambda fd,data: (_ for _ in ()).throw(OSError('injected')) if path.exists() else real_write(fd,data))
 with pytest.raises(OSError,match='injected'):create_credential_binding(path,binding())
 assert journal.exists() and json.loads(journal.read_text())['phase']=='PREPARED' and not path.exists()

def test_durable_unlink_removes_exact_file(tmp_path):
 path=tmp_path/'state';path.write_bytes(b'x');durable_unlink(path);assert not path.exists()

def test_empty_private_state_dir_cleanup_and_foreign_content_refusal(tmp_path):
 state=tmp_path/'credential-state';state.mkdir(mode=0o700);durable_rmdir_empty_private(state);assert not state.exists()
 state.mkdir(mode=0o700);(state/'foreign').write_bytes(b'x')
 with pytest.raises(TxError,match='CREDENTIAL_STATE_FOREIGN'):durable_rmdir_empty_private(state)
 assert state.exists() and (state/'foreign').exists()

def main_fixture(tmp_path,kind):
 tx=tmp_path/'tx';txid='b'*32;policy=tmp_path/'policy.json';closure=tmp_path/'closure.json';journal=tx/f'{txid}.json';receipt=tx/'VERIFIED.json'
 value={'authority':'NONE','status':'PRE_HOST_OCI_EVIDENCE_APPROVED','transaction_root':str(tx),'oci_archive_sha256':'a'*64,'image':'image@sha256:'+'b'*64,'oci_evidence_approval':'approval.json'};policy.write_text(json.dumps(value));closure.write_text('{"packages":[]}');Journal(journal)
 if os.name=='posix':os.chmod(tx,0o700)
 b={'transaction_id':txid,'controller_sha':'a'*40,'policy_sha256':__import__('hashlib').sha256(policy.read_bytes()).hexdigest()}
 if kind!='missing_binding':
  create_credential_binding(tx/'credential-binding.json',b)
 if kind in {'empty_state','key_only','map_only'}:
  state=tx/'credential-state';state.mkdir(mode=0o700)
  if kind=='key_only':(state/'key').write_bytes(b'x')
  if kind=='map_only':(state/'map').write_bytes(b'x')
 return policy,closure,journal,receipt,tx

@pytest.mark.parametrize('kind',['missing_binding','binding_absent_state','empty_state'])
def test_main_rollback_cleans_prepared_initialization_and_allows_retry_boundary(tmp_path,kind,monkeypatch):
 policy,closure,journal,receipt,tx=main_fixture(tmp_path,kind)
 args=['--policy',str(policy),'--closure',str(closure),'--journal',str(journal),'--receipt',str(receipt),'--rollback']
 assert main(args)==0 and not journal.exists() and not (tx/'credential-binding.json').exists()
 # A new apply reaches its controlled evidence verification boundary, not an orphan/FileExists boundary.
 Journal(journal);assert journal.exists()

@pytest.mark.parametrize('kind',['key_only','map_only'])
def test_main_rollback_rejects_and_preserves_partial_credential_state(tmp_path,kind):
 policy,closure,journal,receipt,tx=main_fixture(tmp_path,kind);before=(tx/'credential-binding.json').read_bytes()
 args=['--policy',str(policy),'--closure',str(closure),'--journal',str(journal),'--receipt',str(receipt),'--rollback']
 assert main(args)==2 and journal.exists() and (tx/'credential-binding.json').read_bytes()==before
 assert (tx/'credential-state'/('key' if kind=='key_only' else 'map')).exists()

def test_main_rollback_rejects_dangling_current_credential_state_root(tmp_path):
 policy,closure,journal,receipt,tx=main_fixture(tmp_path,'binding_absent_state');state=tx/'credential-state';state.symlink_to(tx/'missing-state')
 args=['--policy',str(policy),'--closure',str(closure),'--journal',str(journal),'--receipt',str(receipt),'--rollback']
 assert main(args)==2 and journal.exists() and (tx/'credential-binding.json').exists() and state.is_symlink()

def test_commitment_detects_bytes_metadata_set_and_replay_without_leakage(tmp_path):
 root=tree(tmp_path); store=CredentialCommitments(tmp_path/'tx',binding()); assert store.create(root,(980,980))==2; assert store.verify(root)==2
 persisted=store.map_path.read_text()+store.key_path.read_bytes().hex()
 assert 'runner-secret' not in persisted and 'credential-secret' not in persisted
 (root/'.runner').write_bytes(b'changed')
 with pytest.raises(TxError,match='MISMATCH'): store.verify(root)
 (root/'.runner').write_bytes(b'runner-secret'); (root/'new').write_text('new')
 with pytest.raises(TxError,match='SET_MISMATCH'): store.verify(root)
 value=json.loads(store.map_path.read_text()); value['binding']['transaction_id']='replayed'; store.map_path.write_text(json.dumps(value)); os.chmod(store.map_path,0o600)
 with pytest.raises(TxError,match='REPLAY'): store.verify(root)

def test_commitment_accepts_contained_symlink_and_rejects_escape_or_target_drift(tmp_path):
 root=tree(tmp_path); target=root/'tool'; target.mkdir(); (target/'bin').write_bytes(b'tool')
 link=root/'bin'; link.symlink_to('tool')
 store=CredentialCommitments(tmp_path/'tx',binding()); assert store.create(root,(980,980))==3; assert store.verify(root)==3
 link.unlink(); link.symlink_to('.runner')
 with pytest.raises(TxError,match='CREDENTIAL_STATE_MISMATCH'): store.verify(root)
 link.unlink(); outside=tmp_path/'outside'; outside.write_bytes(b'outside'); link.symlink_to(outside)
 with pytest.raises(TxError,match='RUNNER_TREE_ESCAPE'): CredentialCommitments(tmp_path/'escape',binding('escape')).create(root,(980,980))

def test_commitment_rejects_hardlink_and_bad_state_permissions(tmp_path):
 root=tree(tmp_path); os.link(root/'.runner',root/'hard')
 with pytest.raises(TxError,match='UNSAFE_FILE_IDENTITY'): CredentialCommitments(tmp_path/'tx2',binding('tx-2')).create(root,(980,980))
 (root/'hard').unlink(); store=CredentialCommitments(tmp_path/'tx3',binding('tx-3')); store.create(root,(980,980)); os.chmod(store.key_path,0o644)
 if os.name=='posix':
  with pytest.raises(TxError,match='PERMISSIONS'): store.verify(root)

def test_commitment_retained_for_open_blocked_and_unlinked_only_at_closure(tmp_path):
 root=tree(tmp_path); store=CredentialCommitments(tmp_path/'tx',binding()); store.create(root,(980,980))
 for state in ('OPEN','VERIFIED','COMMITTED','ROLLBACK_BLOCKED'):
  with pytest.raises(TxError,match='RETAIN_REQUIRED'): store.close(state)
  assert store.key_path.exists() and store.map_path.exists()
 store.close('ROLLED_BACK'); assert not store.root.exists()

def test_binding_is_closed_and_duplicate_map_keys_fail(tmp_path):
 with pytest.raises(TxError,match='NOT_CLOSED'): CredentialCommitments(tmp_path/'x',{'transaction_id':'x'})
 root=tree(tmp_path); store=CredentialCommitments(tmp_path/'tx',binding()); store.create(root,(980,980)); store.map_path.write_text('{"binding":{},"binding":{},"entries":[],"set_mac":"x"}'); os.chmod(store.map_path,0o600)
 with pytest.raises(TxError): store.verify(root)

def test_directory_metadata_is_part_of_commitment(tmp_path,monkeypatch):
 root=tree(tmp_path); child=root/'private'; child.mkdir(); (child/'state').write_bytes(b'x')
 store=CredentialCommitments(tmp_path/'tx',binding()); store.create(root,(980,980)); original=store._xattrs
 monkeypatch.setattr(store,'_xattrs',lambda path: {'user.changed':'01'} if path==child else original(path))
 with pytest.raises(TxError,match='CREDENTIAL_STATE_MISMATCH'): store.verify(root)

def test_directory_inode_replacement_is_rejected(tmp_path):
 root=tree(tmp_path); child=root/'empty'; child.mkdir(); store=CredentialCommitments(tmp_path/'tx',binding()); store.create(root,(980,980)); child.rename(tmp_path/'old-empty'); child.mkdir()
 with pytest.raises(TxError,match='CREDENTIAL_STATE_MISMATCH'):store.verify(root)

def test_terminal_close_is_idempotent_before_credential_state_creation(tmp_path):
 store=CredentialCommitments(tmp_path/'tx',binding()); store.close('ROLLED_BACK'); assert not store.root.exists()
 store.root.mkdir(mode=0o700,parents=True); store.close('ROLLED_BACK'); assert not store.root.exists()
 store.root.mkdir(mode=0o700,parents=True); (store.root/'key').write_bytes(b'partial')
 with pytest.raises(TxError,match='CREDENTIAL_STATE_PARTIAL'): store.close('ROLLED_BACK')

def test_commitment_requires_exact_snapshotted_tree_identity(tmp_path):
 from scripts.claw_host_bootstrap_transaction import tree_metadata_projection
 root=tree(tmp_path); baseline=tree_metadata_projection(root); (root/'new').write_bytes(b'drift')
 with pytest.raises(TxError,match='TREE_METADATA_DRIFT'):
  CredentialCommitments(tmp_path/'tx',binding()).create(root,(980,980),baseline)
