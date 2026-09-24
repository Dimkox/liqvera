import json
import hashlib
from scripts.claw_host_bootstrap_transaction import Journal,OPERATIONS,RealBackend,recover,restore_tree_metadata,transfer_tree_ownership,tree_metadata_projection
class Stub:
 def __init__(self,outputs=None,fail=()): self.calls=[]; self.outputs=outputs or {}; self.fail=set(fail)
 def run(self,argv,input=None):
  self.calls.append(argv)
  key=tuple(argv)
  if key in self.fail: raise RuntimeError('stub failure')
  default='User=claw-engine-runner\nGroup=claw-engine-runner\nWorkingDirectory=/home/pall/actions-runner-engine\nActiveState=active\n' if argv[:3]==['systemctl','show','engine.service'] else ''
  return type('Result',(),{'stdout':self.outputs.get(key,default)})()
def policy():
 return {'oci_archive_sha256':'a'*64,'runner_uid':980,'runner_gid':980,'subuid_start':165536,'subgid_start':165536,'subid_count':65536,'runner_user':'claw-engine-runner','runner_group':'claw-engine-runner','runner_home':'/var/lib/claw-engine-runner','runner_tree':'/home/pall/actions-runner-engine','engine_service':'engine.service','app_service':'app.service','app_working_directory':'/home/pall/actions-runner','transaction_root':'/var/lib/claw-engine-runner-bootstrap','image':'image@sha256:'+'b'*64}
def test_real_backend_closed_argv_and_inverses(tmp_path):
 (tmp_path/'home/pall/actions-runner-engine').mkdir(parents=True)
 s=Stub(); b=RealBackend(policy(),s,root=tmp_path)
 b.snapshot('snapshot_host')
 for name in ('create_identity','stop_engine','transfer_ownership','start_engine'): b.prepare(name); b.apply(name); b.verify(name)
 b.rollback('start_engine'); b.rollback('stop_engine'); b.rollback('transfer_ownership'); b.final_verify()
 assert ['systemctl','stop','engine.service'] in s.calls and ['systemctl','start','engine.service'] in s.calls
 assert all(isinstance(x,list) for x in s.calls)
def test_all_operations_have_apply_verify_and_inverse(tmp_path):
 (tmp_path/'home/pall/actions-runner-engine').mkdir(parents=True); (tmp_path/'etc').mkdir(); (tmp_path/'etc/subuid').write_text('pall:100000:65536\n'); (tmp_path/'etc/subgid').write_text('pall:100000:65536\n'); (tmp_path/'sys/fs/cgroup').mkdir(parents=True); (tmp_path/'sys/fs/cgroup/cgroup.controllers').write_text('cpu memory')
 sub=('sh','-c','printf "SUBUID\\n"; cat "$1"; printf "SUBGID\\n"; cat "$2"','subids',str(tmp_path/'etc/subuid'),str(tmp_path/'etc/subgid'))
 s=Stub({sub:'SUBUID\npall:100000:65536\nSUBGID\npall:100000:65536\n'}); b=RealBackend(policy(),s,root=tmp_path)
 foundation=[x for x in OPERATIONS if x.name in {'freeze_inputs','snapshot_host','install_packages','create_identity','configure_subids','configure_runtime','stop_engine','transfer_ownership','install_dropin'}]
 for op in foundation: b.prepare(op.name); b.snapshot(op.name); b.apply(op.name); b.verify(op.name)
 for op in reversed(foundation): b.rollback(op.name)
 assert len(s.calls)>=len(foundation)*2
def test_resume_rolls_back_recorded_operations(tmp_path):
 j=Journal(tmp_path/'j'); j.record('APPLYING(start_engine)',['freeze_inputs','stop_engine'],current='start_engine',snapshot={'operation':'start_engine','probe':'inactive'}); j2=Journal.resume(tmp_path/'j'); s=Stub(); b=RealBackend(policy(),s); recover(b,j2)
 assert json.loads((tmp_path/'j').read_text())['status']=='ROLLED_BACK'
 assert s.calls[0]==['systemctl','stop','engine.service']

def test_package_rollback_refuses_concurrent_dependency_drift():
 archives=('/tx/podman_1_amd64.deb','/tx/uidmap_1_amd64.deb')
 simulation=('apt-get','remove','--simulate','podman','uidmap')
 s=Stub({simulation:'Remv podman [1]\nRemv unrelated [2]\n'})
 b=RealBackend(policy(),s,archives); b.snapshots['install_packages']={'probe':''}
 import pytest
 with pytest.raises(Exception,match='ROLLBACK_DEPENDENCY_DRIFT'): b.rollback('install_packages')
 assert not any(x[:3]==['apt-get','remove','--yes'] for x in s.calls)

def test_package_archive_is_closed_copied_and_rehashed_before_offline_apply(tmp_path):
 archive=tmp_path/'input.deb'; archive.write_bytes(b'exact-deb-fixture')
 record={'name':'podman','version':'1.0','architecture':'amd64','sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}
 show=('dpkg-deb','--show','--showformat=${Package}\t${Version}\t${Architecture}\n',str(archive))
 s=Stub({show:'podman\t1.0\tamd64\n'}); b=RealBackend(policy(),s,[archive],[record],root=tmp_path)
 b.prepare('install_packages')
 staged=tmp_path/'var/lib/claw-engine-runner-bootstrap/packages/podman.deb'
 assert staged.read_bytes()==archive.read_bytes()
 staged.write_bytes(b'swapped')
 import pytest
 with pytest.raises(Exception,match='PACKAGE_ARCHIVE_SWAP'): b.apply('install_packages')
 assert not any(x and x[0]=='apt-get' and '--yes' in x for x in s.calls)

def test_offline_package_plan_rejects_dependency_outside_exact_closure(tmp_path):
 archive=tmp_path/'input.deb'; archive.write_bytes(b'exact')
 record={'name':'podman','version':'1.0','architecture':'amd64','sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}
 show=('dpkg-deb','--show','--showformat=${Package}\t${Version}\t${Architecture}\n',str(archive))
 p=policy(); s=Stub({show:'podman\t1.0\tamd64\n'}); b=RealBackend(p,s,[archive],[record],root=tmp_path); b.prepare('install_packages')
 simulate=('apt-get','-o',f"Dir::Cache::archives={tmp_path/'var/lib/claw-engine-runner-bootstrap/apt-cache'}",'-o','Dir::Cache::pkgcache=/dev/null','-o','Dir::Cache::srcpkgcache=/dev/null','-o','Acquire::Retries=0','install','--simulate','--no-install-recommends','--no-download',str(tmp_path/'var/lib/claw-engine-runner-bootstrap/packages/podman.deb'))
 s.outputs[simulate]='Inst podman (1.0 local [amd64])\nInst surprise (2.0 local [amd64])\n'
 import pytest
 with pytest.raises(Exception,match='PACKAGE_PLAN_OUTSIDE_CLOSURE'): b.apply('install_packages')
 assert not any(x and x[0]=='apt-get' and '--yes' in x for x in s.calls)

def test_offline_package_plan_rejects_missing_wrong_and_noop_closure_member(tmp_path):
 import pytest
 archive=tmp_path/'input.deb'; archive.write_bytes(b'exact')
 record={'name':'podman','version':'1.0','architecture':'amd64','sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}
 show=('dpkg-deb','--show','--showformat=${Package}\t${Version}\t${Architecture}\n',str(archive))
 for plan in ('','Inst podman (9.9 local [amd64])\n'):
  s=Stub({show:'podman\t1.0\tamd64\n'}); b=RealBackend(policy(),s,[archive],[record],root=tmp_path); b.prepare('install_packages')
  staged=str(tmp_path/'var/lib/claw-engine-runner-bootstrap/packages/podman.deb')
  simulate=next_call=['apt-get','-o',f"Dir::Cache::archives={tmp_path/'var/lib/claw-engine-runner-bootstrap/apt-cache'}",'-o','Dir::Cache::pkgcache=/dev/null','-o','Dir::Cache::srcpkgcache=/dev/null','-o','Acquire::Retries=0','install','--simulate','--no-install-recommends','--no-download',staged]
  s.outputs[tuple(simulate)]=plan
  b.snapshots['install_packages']={'probe':'','selections':''}
  with pytest.raises(Exception,match='PACKAGE_PLAN_OUTSIDE_CLOSURE'): b.apply('install_packages')

def test_offline_package_plan_uses_only_transaction_cache_and_staged_archives(tmp_path):
 archive=tmp_path/'input.deb'; archive.write_bytes(b'exact'); record={'name':'podman','version':'1.0','architecture':'amd64','sha256':hashlib.sha256(b'exact').hexdigest()}
 show=('dpkg-deb','--show','--showformat=${Package}\t${Version}\t${Architecture}\n',str(archive)); s=Stub({show:'podman\t1.0\tamd64\n'}); b=RealBackend(policy(),s,[archive],[record],root=tmp_path); b.prepare('install_packages'); b.snapshots['install_packages']={'probe':'','selections':''}
 staged=str(tmp_path/'var/lib/claw-engine-runner-bootstrap/packages/podman.deb'); prefix=['apt-get','-o',f"Dir::Cache::archives={tmp_path/'var/lib/claw-engine-runner-bootstrap/apt-cache'}",'-o','Dir::Cache::pkgcache=/dev/null','-o','Dir::Cache::srcpkgcache=/dev/null','-o','Acquire::Retries=0','install']
 s.outputs[tuple([*prefix,'--simulate','--no-install-recommends','--no-download',staged])]='Inst podman (1.0 local [amd64])\n'
 b.apply('install_packages')
 assert [*prefix,'--yes','--no-install-recommends','--no-download',staged] in s.calls

def test_package_closure_rejects_duplicate_tuple_and_extra_fields(tmp_path):
 import pytest
 archive=tmp_path/'a.deb'; archive.write_bytes(b'x'); digest=hashlib.sha256(b'x').hexdigest(); record={'name':'p','version':'1','architecture':'amd64','sha256':digest}
 with pytest.raises(Exception,match='DUPLICATE'): RealBackend(policy(),Stub(),[archive,archive],[record,record],root=tmp_path).prepare('install_packages')
 bad=dict(record,extra=True)
 with pytest.raises(Exception,match='NOT_CLOSED'): RealBackend(policy(),Stub(),[archive],[bad],root=tmp_path).prepare('install_packages')

def test_fresh_backend_package_rollback_requires_exact_baseline_and_selections():
 query=('dpkg-query','-W','-f=${Package}\t${Version}\t${Architecture}\t${db:Status-Abbrev}\n'); selections=('dpkg','--get-selections')
 baseline='base\t1\tamd64\tii \n'; selected='base\tinstall\n'; s=Stub({query:'base\t2\tamd64\tii \n',selections:selected})
 b=RealBackend(policy(),s); b.snapshots['install_packages']={'operation':'install_packages','probe':baseline,'selections':selected}
 import pytest
 with pytest.raises(Exception,match='ROLLBACK_PACKAGE_STATE_DRIFT'): b.rollback('install_packages')

def test_apply_refuses_any_preexisting_closure_member(tmp_path):
 archive=tmp_path/'p.deb'; archive.write_bytes(b'p'); record={'name':'podman','version':'1','architecture':'amd64','sha256':hashlib.sha256(b'p').hexdigest()}; show=('dpkg-deb','--show','--showformat=${Package}\t${Version}\t${Architecture}\n',str(archive)); s=Stub({show:'podman\t1\tamd64\n'}); b=RealBackend(policy(),s,[archive],[record],root=tmp_path); b.prepare('install_packages'); b.snapshots['install_packages']={'probe':'podman\t0.9\tamd64\tii \n','selections':'podman\tinstall\n'}
 import pytest
 with pytest.raises(Exception,match='PACKAGE_BASELINE_MEMBER_PRESENT'): b.apply('install_packages')

def test_subid_apply_and_mixed_state_recovery_are_exact(tmp_path):
 p=policy(); sub=('sh','-c','printf "SUBUID\\n"; cat "$1"; printf "SUBGID\\n"; cat "$2"','subids',str(tmp_path/'etc/subuid'),str(tmp_path/'etc/subgid')); s=Stub({sub:'SUBUID\npall:100000:65536\nSUBGID\npall:100000:65536\n'}); b=RealBackend(p,s,root=tmp_path)
 (tmp_path/'etc').mkdir(); (tmp_path/'etc/subuid').write_text('pall:100000:65536\n'); (tmp_path/'etc/subgid').write_text('pall:100000:65536\n'); (tmp_path/'etc/subuid').chmod(0o640); (tmp_path/'etc/subgid').chmod(0o644)
 uid_mode=(tmp_path/'etc/subuid').stat().st_mode & 0o777; gid_mode=(tmp_path/'etc/subgid').stat().st_mode & 0o777
 b.snapshot('configure_subids')
 b.apply('configure_subids')
 assert (tmp_path/'etc/subuid').read_text().endswith('claw-engine-runner:165536:65536\n')
 (tmp_path/'etc/subuid').write_text('mixed\n')
 b.rollback('configure_subids')
 assert (tmp_path/'etc/subuid').read_text()=='pall:100000:65536\n'
 assert (tmp_path/'etc/subgid').read_text()=='pall:100000:65536\n'
 assert ((tmp_path/'etc/subuid').stat().st_mode & 0o777)==uid_mode
 assert ((tmp_path/'etc/subgid').stat().st_mode & 0o777)==gid_mode

def test_subid_reconcile_in_fresh_backend_restores_mixed_files(tmp_path):
 p=policy()
 (tmp_path/'etc').mkdir(); (tmp_path/'etc/subuid').write_text('pall:100000:65536\n'); (tmp_path/'etc/subgid').write_text('pall:100000:65536\n')
 sub=('sh','-c','printf "SUBUID\\n"; cat "$1"; printf "SUBGID\\n"; cat "$2"','subids',str(tmp_path/'etc/subuid'),str(tmp_path/'etc/subgid')); first=RealBackend(p,Stub({sub:'SUBUID\npall:100000:65536\nSUBGID\npall:100000:65536\n'}),root=tmp_path); snapshot=first.snapshot('configure_subids'); first.apply('configure_subids')
 (tmp_path/'etc/subuid').write_text('crash-mid-write\n')
 RealBackend(p,Stub(),root=tmp_path).reconcile('configure_subids',snapshot)
 assert (tmp_path/'etc/subuid').read_text()=='pall:100000:65536\n'
 assert (tmp_path/'etc/subgid').read_text()=='pall:100000:65536\n'

def test_subid_rejects_overlap_symlink_hardlink_and_bad_grammar(tmp_path):
 import pytest,os
 from scripts.claw_host_bootstrap_transaction import add_subid_entry
 with pytest.raises(Exception,match='SUBID_RANGE_OVERLAP'): add_subid_entry('other:165536:1\n','claw',165536,65536)
 with pytest.raises(Exception,match='SUBID_FILE_INVALID'): add_subid_entry('other:+1:2\n','claw',20,2)
 etc=tmp_path/'etc'; etc.mkdir(); real=etc/'real'; real.write_text('pall:100000:65536\n'); (etc/'subuid').symlink_to(real); (etc/'subgid').write_text('pall:100000:65536\n')
 with pytest.raises(Exception,match='UNSAFE_FILE_IDENTITY'): RealBackend(policy(),Stub(),root=tmp_path).prepare('configure_subids')
 (etc/'subuid').unlink(); os.link(real,etc/'subuid')
 with pytest.raises(Exception,match='UNSAFE_FILE_IDENTITY'): RealBackend(policy(),Stub(),root=tmp_path).prepare('configure_subids')

def test_runtime_and_service_rollbacks_restore_only_prior_state(tmp_path):
 s=Stub(); b=RealBackend(policy(),s,root=tmp_path)
 b.snapshots['configure_runtime']={'linger_was_enabled':True}
 b.snapshots['stop_engine']={'was_active':False}; b.snapshots['start_engine']={'was_active':True}
 b.rollback('configure_runtime'); b.rollback('stop_engine'); b.rollback('start_engine')
 assert not any(x[:2]==['loginctl','disable-linger'] for x in s.calls)
 assert not any(x[:2]==['systemctl','start'] for x in s.calls)
 assert ['systemctl','stop','engine.service'] not in s.calls

def test_runtime_and_dropin_use_fake_root_and_restore_content(tmp_path):
 p=policy(); s=Stub(); b=RealBackend(p,s,root=tmp_path)
 target=tmp_path/'etc/systemd/system/engine.service.d/10-claw-user.conf'; target.parent.mkdir(parents=True); target.write_text('old\n')
 b.snapshot('install_dropin'); b.apply('install_dropin'); b.verify('install_dropin')
 assert 'User=claw-engine-runner' in target.read_text()
 b.rollback('install_dropin'); assert target.read_text()=='old\n'
 (tmp_path/'sys/fs/cgroup').mkdir(parents=True); (tmp_path/'sys/fs/cgroup/cgroup.controllers').write_text('cpu memory')
 b.snapshot('configure_runtime'); b.apply('configure_runtime'); b.verify('configure_runtime')
 assert 'runroot="/run/user/980/containers"' in (tmp_path/'var/lib/claw-engine-runner/.config/containers/storage.conf').read_text()
 b.rollback('configure_runtime'); assert not (tmp_path/'var/lib/claw-engine-runner/.config/containers').exists()

def test_runtime_rollback_preserves_preexisting_tree_and_storage(tmp_path):
 p=policy(); containers=tmp_path/'var/lib/claw-engine-runner/.config/containers'; containers.mkdir(parents=True); (containers/'storage.conf').write_text('old-storage\n')
 runtime=tmp_path/'run/user/980'; runtime.mkdir(parents=True)
 s=Stub(); b=RealBackend(p,s,root=tmp_path); b.snapshot('configure_runtime'); b.apply('configure_runtime'); b.rollback('configure_runtime')
 assert containers.is_dir() and runtime.is_dir()
 assert (containers/'storage.conf').read_text()=='old-storage\n'

def test_runtime_rollback_restores_home_metadata_and_removes_only_owned_parents(tmp_path):
 home=tmp_path/'var/lib/claw-engine-runner'; home.mkdir(parents=True); before=home.stat().st_mode & 0o777
 b=RealBackend(policy(),Stub(),root=tmp_path); b.snapshot('configure_runtime'); b.apply('configure_runtime'); b.rollback('configure_runtime')
 assert home.is_dir() and (home.stat().st_mode & 0o777)==before
 assert not (home/'.config').exists()

def test_runtime_rollback_blocks_on_unowned_resource_but_attempts_service_inverse(tmp_path):
 import pytest
 runtime=tmp_path/'run/user/980'; containers=tmp_path/'var/lib/claw-engine-runner/.config/containers'; runtime.mkdir(parents=True); containers.mkdir(parents=True); (containers/'foreign').write_text('not-created-by-transaction')
 b=RealBackend(policy(),Stub(),root=tmp_path); b.snapshots['configure_runtime']={'runtime_existed':False,'containers_existed':False,'storage_existed':False,'runtime_unit_was_active':False,'linger_was_enabled':False}
 with pytest.raises(Exception,match='RUNTIME_FOREIGN_RESOURCE'): b.rollback('configure_runtime')
 assert ['systemctl','stop','user-runtime-dir@980.service'] in b.r.calls
 assert ['loginctl','disable-linger','claw-engine-runner'] in b.r.calls

def test_dropin_rollback_restores_preexisting_empty_file(tmp_path):
 p=policy(); target=tmp_path/'etc/systemd/system/engine.service.d/10-claw-user.conf'; target.parent.mkdir(parents=True); target.write_bytes(b'')
 b=RealBackend(p,Stub(),root=tmp_path); b.snapshot('install_dropin'); b.apply('install_dropin'); b.rollback('install_dropin')
 assert target.is_file() and target.read_bytes()==b''

def test_oci_stage_load_digest_rootless_smoke_and_inverse(tmp_path):
 archive=tmp_path/'image.oci'; archive.write_bytes(b'oci-fixture'); p=policy(); p['oci_archive_sha256']=hashlib.sha256(archive.read_bytes()).hexdigest()
 inspect=('runuser','-u','claw-engine-runner','--','env','HOME=/var/lib/claw-engine-runner','XDG_RUNTIME_DIR=/run/user/980','podman','image','inspect','--format={{.Digest}}',p['image'])
 ps=('runuser','-u','claw-engine-runner','--','env','HOME=/var/lib/claw-engine-runner','XDG_RUNTIME_DIR=/run/user/980','podman','ps','-aq','--filter',f"ancestor={p['image']}")
 s=Stub({inspect:p['image'].split('@',1)[1]+'\n',ps:''}); b=RealBackend(p,s,root=tmp_path,oci_archive=archive)
 b.prepare('load_oci'); b.apply('load_oci'); b.verify('load_oci'); b.apply('rootless_smoke'); b.verify('rootless_smoke'); b.rollback('load_oci')
 assert (tmp_path/'var/lib/claw-engine-runner-bootstrap/image.oci').read_bytes()==archive.read_bytes()
 smoke=next(x for x in s.calls if 'podman' in x and 'run' in x)
 assert '--pull=never' in smoke and '--network=none' in smoke and '--rm' in smoke and 'timeout' in smoke
 assert any('image' in x and 'rm' in x and '--force' in x for x in s.calls)

def test_oci_rejects_zero_unapproved_and_post_stage_swap(tmp_path):
 import pytest
 archive=tmp_path/'image.oci'; archive.write_bytes(b'oci')
 with pytest.raises(Exception,match='OCI_ARCHIVE_UNRESOLVED'): RealBackend(policy()|{'oci_archive_sha256':'0'*64},Stub(),root=tmp_path,oci_archive=archive).prepare('load_oci')
 p=policy(); p['oci_archive_sha256']=hashlib.sha256(archive.read_bytes()).hexdigest(); b=RealBackend(p,Stub(),root=tmp_path,oci_archive=archive); b.prepare('load_oci'); b.staged_oci.write_bytes(b'swap')
 with pytest.raises(Exception,match='OCI_ARCHIVE_SWAP'): b.apply('load_oci')

def test_oci_inverse_preserves_preexisting_image(tmp_path):
 p=policy(); inspect=('runuser','-u','claw-engine-runner','--','env','HOME=/var/lib/claw-engine-runner','XDG_RUNTIME_DIR=/run/user/980','podman','image','inspect','--format={{.Digest}}',p['image']); s=Stub({inspect:p['image'].split('@',1)[1]+'\n'}); b=RealBackend(p,s,root=tmp_path); b.snapshot('load_oci'); b.rollback('load_oci')
 assert not any('rm' in x and 'image' in x for x in s.calls)

def test_oci_baseline_accepts_exact_not_found_only(tmp_path):
 class NotFoundStub(Stub):
  def run(self,argv,input=None):
   if 'image' in argv and 'inspect' in argv:
    error=__import__('subprocess').CalledProcessError(125,argv,stderr='no such image')
    raise error
   return super().run(argv,input)
 b=RealBackend(policy(),NotFoundStub(),root=tmp_path); assert b.snapshot('load_oci')['image_existed'] is False
 class BrokenStub(NotFoundStub):
  def run(self,argv,input=None):
   if 'image' in argv and 'inspect' in argv: raise __import__('subprocess').CalledProcessError(1,argv,stderr='permission denied')
   return super().run(argv,input)
 import pytest
 with pytest.raises(Exception,match='OCI_BASELINE_INSPECT_FAILED'): RealBackend(policy(),BrokenStub(),root=tmp_path).snapshot('load_oci')

def test_identity_absent_snapshot_is_nonfailing_and_inverse_is_created_only(tmp_path):
 absent=('sh','-c','getent passwd "$1" || true','identity','claw-engine-runner'); s=Stub({absent:''}); b=RealBackend(policy(),s,root=tmp_path); snap=b.snapshot('create_identity'); assert snap['identity_existed'] is False; b.apply('create_identity'); b.rollback('create_identity'); assert ['userdel','claw-engine-runner'] in s.calls
 existing=Stub({absent:'claw-engine-runner:x:980:980::/var/lib/claw-engine-runner:/usr/sbin/nologin\n'}); b=RealBackend(policy(),existing,root=tmp_path); b.snapshot('create_identity'); b.apply('create_identity'); b.rollback('create_identity'); assert ['userdel','claw-engine-runner'] not in existing.calls

def test_app_canary_freezes_closed_healthy_projection_and_detects_pid_drift(tmp_path):
 p=policy(); show=('systemctl','show','app.service','--property=MainPID,User,ExecStart,WorkingDirectory,FragmentPath,ActiveState')
 baseline='MainPID=42\nUser=pall\nExecStart=/home/pall/actions-runner/runsvc.sh\nWorkingDirectory=/home/pall/actions-runner\nFragmentPath=/etc/systemd/system/app.service\nActiveState=active\n'
 (tmp_path/'home/pall/actions-runner-engine').mkdir(parents=True)
 s=Stub({show:baseline}); b=RealBackend(p,s,root=tmp_path); b.snapshot('snapshot_host'); b.verify('app_canary')
 s.outputs[show]=baseline.replace('MainPID=42','MainPID=43')
 import pytest
 with pytest.raises(Exception,match='APP_CANARY_DRIFT'): b.verify('app_canary')

def test_app_canary_requires_pre_mutation_snapshot_host_baseline(tmp_path):
 import pytest
 p=policy(); show=('systemctl','show','app.service','--property=MainPID,User,ExecStart,WorkingDirectory,FragmentPath,ActiveState')
 baseline='MainPID=42\nUser=pall\nExecStart=/home/pall/actions-runner/runsvc.sh\nWorkingDirectory=/home/pall/actions-runner\nFragmentPath=/etc/systemd/system/app.service\nActiveState=active\n'
 b=RealBackend(p,Stub({show:baseline}),root=tmp_path)
 with pytest.raises(Exception,match='APP_BASELINE_MISSING'): b.verify('app_canary')

def test_every_host_filesystem_argv_is_rootpaths_backed(tmp_path):
 runner_tree=tmp_path/'home/pall/actions-runner-engine'; runner_tree.mkdir(parents=True)
 s=Stub(); b=RealBackend(policy(),s,root=tmp_path)
 b.snapshot('snapshot_host'); b.apply('snapshot_host')
 raw='/home/pall/actions-runner-engine'
 assert all(raw != arg for call in s.calls for arg in call)
 assert not any(call and call[0] in {'getfacl','setfacl'} for call in s.calls)

def test_pre_snapshot_recovery_closes_without_credential_state(tmp_path):
 p=policy(); p['transaction_root']='/tx'; binding={'transaction_id':'journal','controller_sha':'a'*40,'policy_sha256':'b'*64}
 journal=Journal(tmp_path/'journal'); journal.record('APPLIED(freeze_inputs)',['freeze_inputs'],current='freeze_inputs',snapshot={'operation':'freeze_inputs','probe':''}); journal.record('ROLLING_BACK',['freeze_inputs'])
 backend=RealBackend(p,Stub(),root=tmp_path,credential_binding=binding)
 recover(backend,Journal.resume(journal.path))
 assert json.loads(journal.path.read_text())['status']=='ROLLED_BACK'

def test_tree_metadata_round_trip_preserves_internal_link_and_rejects_retarget(tmp_path):
 import os,pytest
 root=tmp_path/'runner'; target=root/'bin.v1'; target.mkdir(parents=True); binary=target/'run'; binary.write_bytes(b'exact'); link=root/'bin'; link.symlink_to('bin.v1')
 projection=tree_metadata_projection(root); binary.chmod(0o600); restore_tree_metadata(root,projection)
 assert tree_metadata_projection(root)==projection and os.readlink(link)=='bin.v1'
 link.unlink(); link.symlink_to(binary)
 with pytest.raises(Exception,match='TREE_METADATA_DRIFT'): restore_tree_metadata(root,projection)

def test_tree_mutation_rejects_swapped_root_without_touching_outside(tmp_path):
 import os,pytest
 root=tmp_path/'runner'; root.mkdir(); (root/'file').write_bytes(b'exact'); projection=tree_metadata_projection(root)
 original=tmp_path/'runner.original'; root.rename(original); outside=tmp_path/'outside'; outside.mkdir(); victim=outside/'victim'; victim.write_bytes(b'outside'); root.symlink_to(outside,target_is_directory=True)
 before=victim.stat().st_uid
 with pytest.raises(Exception,match='RUNNER_TREE_INVALID|TREE_METADATA_DRIFT'): transfer_tree_ownership(root,980,980,projection)
 assert victim.stat().st_uid==before

def test_tree_mutation_rejects_intermediate_directory_swap(tmp_path,monkeypatch):
 import os,pytest
 if os.name!='posix':pytest.skip('POSIX directory-fd contract')
 root=tmp_path/'runner'; child=root/'child'; child.mkdir(parents=True); victim=child/'victim'; victim.write_bytes(b'exact'); projection=tree_metadata_projection(root); before=victim.stat().st_uid
 moved=tmp_path/'moved'; real_open=os.open; swapped=False
 def racing_open(path,flags,*args,**kwargs):
  nonlocal swapped
  fd=real_open(path,flags,*args,**kwargs)
  if not swapped and str(path)==str(root):
   child.rename(moved); child.symlink_to(moved,target_is_directory=True); swapped=True
  return fd
 monkeypatch.setattr(os,'open',racing_open)
 with pytest.raises(Exception,match='TREE_METADATA_DRIFT|LOOP|symlink|Too many levels'): transfer_tree_ownership(root,980,980,projection)
 assert victim.stat().st_uid==before

def test_app_canary_rejects_inactive_duplicate_or_wrong_identity(tmp_path):
 import pytest
 p=policy(); show=('systemctl','show','app.service','--property=MainPID,User,ExecStart,WorkingDirectory,FragmentPath,ActiveState')
 for raw in ('MainPID=0\nUser=pall\nExecStart=x\nWorkingDirectory=/home/pall/actions-runner\nFragmentPath=x.service\nActiveState=inactive\n','MainPID=1\nMainPID=2\nUser=pall\nExecStart=x\nWorkingDirectory=/home/pall/actions-runner\nFragmentPath=x.service\nActiveState=active\n'):
  with pytest.raises(Exception): RealBackend(p,Stub({show:raw}),root=tmp_path).snapshot('app_canary')
