import json,pytest
from scripts.claw_helper_install_transaction import HelperJournal,FakeHelperBackend,OPERATIONS,execute,recover

def test_failure_after_every_helper_mutation_restores_all_prior_files(tmp_path):
 for operation in OPERATIONS:
  backend=FakeHelperBackend(f'after:{operation}'); journal=HelperJournal(tmp_path/(operation+'.json'))
  with pytest.raises(RuntimeError): execute(backend,journal)
  assert backend.active==[]
  value=json.loads(journal.path.read_text()); assert value['phase']=='ROLLED_BACK' and value['status']=='ROLLED_BACK'

def test_helper_receipt_is_last_and_resume_uses_durable_snapshots(tmp_path):
 backend=FakeHelperBackend(); journal=HelperJournal(tmp_path/'journal'); execute(backend,journal)
 assert backend.events[-1]==('apply','write_receipt')
 assert json.loads(journal.path.read_text())['status']=='COMMITTED'
 interrupted=HelperJournal(tmp_path/'open'); interrupted.record('APPLYING(install_sudoers)',[],current='install_sudoers',snapshot={'existed':False})
 recovered=FakeHelperBackend(); recover(recovered,HelperJournal.resume(interrupted.path)); assert recovered.events[0]==('rollback','install_sudoers')

def test_helper_install_shell_delegates_all_mutations_to_wal_controller():
 text=open('ci/claw/install-controller-host-helper.sh').read()
 assert 'scripts/claw_helper_install_transaction.py' in text
 assert 'install -o root' not in text and 'systemctl enable --now' not in text

def test_real_helper_rejects_symlink_and_hardlink_targets(tmp_path):
 import os
 from scripts.claw_helper_install_transaction import RealHelperBackend
 source=tmp_path/'source'; (source/'scripts').mkdir(parents=True); (source/'scripts/write_bootstrap_nonce_consumption.py').write_bytes(b'new')
 root=tmp_path/'root'; target=root/'usr/local/libexec/mee-controller-ledger-write'; target.parent.mkdir(parents=True); real=root/'real'; real.write_bytes(b'old'); target.symlink_to(real)
 with pytest.raises(RuntimeError,match='UNSAFE_HELPER_TARGET'): RealHelperBackend(source,root=root).snapshot('install_ledger')
 target.unlink(); os.link(real,target)
 with pytest.raises(RuntimeError,match='UNSAFE_HELPER_TARGET'): RealHelperBackend(source,root=root).snapshot('install_ledger')

def test_helper_rollback_aggregates_inverse_failures_and_retains_open_journal(tmp_path):
 class Broken(FakeHelperBackend):
  def rollback(self,name):
   self.events.append(('rollback',name))
   if name in {'install_service','install_sudoers'}: raise RuntimeError('inverse-'+name)
   if name in self.active:self.active.remove(name)
 b=Broken('after:install_timer'); journal=HelperJournal(tmp_path/'journal')
 with pytest.raises(RuntimeError): execute(b,journal)
 value=json.loads(journal.path.read_text()); assert value['phase']=='ROLLBACK_BLOCKED' and value['status']=='OPEN'
 assert {x[0] for x in value['failures']}=={'install_service','install_sudoers'}
 assert ('rollback','create_state') in b.events

def test_real_helper_restores_preexisting_state_receipt_and_timer(tmp_path):
 from scripts.claw_helper_install_transaction import RealHelperBackend
 class Runner:
  def __init__(self):self.calls=[]
  def run(self,argv,**kwargs):
   self.calls.append(argv); return type('R',(),{'returncode':0 if argv[1] in {'is-enabled','is-active'} else 0})()
 source=tmp_path/'source'; (source/'scripts').mkdir(parents=True); (source/'scripts/write_bootstrap_nonce_consumption.py').write_bytes(b'new')
 root=tmp_path/'root'; state=root/'var/lib/mee-controller'; state.mkdir(parents=True); receipt=state/'helper-install-receipt.json'; receipt.write_bytes(b'old'); target=root/'usr/local/libexec/mee-controller-ledger-write'; target.parent.mkdir(parents=True); target.write_bytes(b'old-target')
 runner=Runner(); backend=RealHelperBackend(source,root=root,runner=runner,receipt=b'new-receipt');
 for name in ('create_state','install_ledger','enable_timer','write_receipt'):backend.snapshot(name);backend.apply(name)
 for name in reversed(('create_state','install_ledger','enable_timer','write_receipt')):backend.rollback(name)
 assert receipt.read_bytes()==b'old' and target.read_bytes()==b'old-target' and state.is_dir()
 assert ['systemctl','enable','mee-controller-reconcile.timer'] in runner.calls and ['systemctl','start','mee-controller-reconcile.timer'] in runner.calls

def test_helper_atomic_loops_short_writes_and_fsyncs_before_replace(tmp_path,monkeypatch):
 import os
 from scripts import claw_helper_install_transaction as module
 events=[]; real_write=os.write; real_fsync=os.fsync; real_replace=os.replace
 def short(fd,data): events.append(('write',len(data))); return real_write(fd,data[:max(1,len(data)//2)])
 def sync(fd): events.append(('fsync',fd)); return real_fsync(fd)
 def replace(source,target): events.append(('replace',str(target))); return real_replace(source,target)
 monkeypatch.setattr(module.os,'write',short); monkeypatch.setattr(module.os,'fsync',sync); monkeypatch.setattr(module.os,'replace',replace)
 target=tmp_path/'state/journal'; module.atomic(target,b'abcdefghij')
 assert target.read_bytes()==b'abcdefghij' and len([x for x in events if x[0]=='write'])>1
 assert events.index(next(x for x in events if x[0]=='fsync')) < events.index(next(x for x in events if x[0]=='replace'))
 if os.name=='posix': assert events[-1][0]=='fsync'

def test_helper_atomic_cleans_temp_after_write_failure(tmp_path,monkeypatch):
 from scripts import claw_helper_install_transaction as module
 monkeypatch.setattr(module.os,'write',lambda *_: (_ for _ in ()).throw(OSError('boom')))
 with pytest.raises(OSError): module.atomic(tmp_path/'state/journal',b'x')
 assert not list((tmp_path/'state').glob('journal.*.tmp'))
