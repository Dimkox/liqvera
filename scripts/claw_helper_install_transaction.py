#!/usr/bin/env python3
"""Closed WAL controller for the privileged post-host-receipt helper install."""
import argparse,json,os,stat,tempfile
from pathlib import Path

OPERATIONS=('create_state','install_ledger','install_verifier','install_reconciler','install_sudoers','install_service','install_timer','daemon_reload','enable_timer','write_receipt')
def atomic(path,data):
 path=Path(path); path.parent.mkdir(parents=True,exist_ok=True); fd,tmp=tempfile.mkstemp(dir=path.parent,prefix=path.name+'.',suffix='.tmp')
 try:
  view=memoryview(data)
  while view:
   written=os.write(fd,view)
   if written<=0:raise OSError('short write')
   view=view[written:]
  os.fsync(fd);os.close(fd);fd=-1;os.replace(tmp,path)
  if os.name=='posix':
   parent_fd=os.open(path.parent,os.O_RDONLY)
   try:os.fsync(parent_fd)
   finally:os.close(parent_fd)
 except BaseException:
  if fd>=0:os.close(fd)
  Path(tmp).unlink(missing_ok=True)
  raise
class HelperJournal:
 def __init__(self,path):
  self.path=Path(path)
  if self.path.exists(): raise RuntimeError('JOURNAL_EXISTS')
  self.value={'schema_version':'claw-helper-install-journal-v1','phase':'PREPARED','history':['PREPARED'],'applied':[],'current':None,'snapshot':None,'snapshots':{},'failures':[],'status':'OPEN'}; self._save()
 def _save(self): atomic(self.path,(json.dumps(self.value,sort_keys=True,separators=(',',':'))+'\n').encode())
 def record(self,phase,applied,current=None,snapshot=None,status=None,failures=None):
  self.value['phase']=phase; self.value['history'].append(phase); self.value['applied']=list(applied); self.value['current']=current; self.value['snapshot']=snapshot
  if current and snapshot is not None:self.value['snapshots'][current]=snapshot
  if status:self.value['status']=status
  if failures is not None:self.value['failures']=failures
  self._save()
 @classmethod
 def resume(cls,path):
  self=object.__new__(cls); self.path=Path(path); self.value=json.loads(self.path.read_text())
  if self.value['status']!='OPEN':raise RuntimeError('JOURNAL_TERMINAL')
  return self
class FakeHelperBackend:
 def __init__(self,fail=''):self.fail=fail;self.active=[];self.events=[]
 def snapshot(self,name):return {'existed':name in self.active}
 def apply(self,name):
  self.events.append(('apply',name));self.active.append(name)
  if self.fail==f'after:{name}':raise RuntimeError('INJECTED')
 def rollback(self,name):self.events.append(('rollback',name)); self.active.remove(name) if name in self.active else None
class RealHelperBackend:
 TARGETS={
  'install_ledger':('/usr/local/libexec/mee-controller-ledger-write','scripts/write_bootstrap_nonce_consumption.py',0o755),
  'install_verifier':('/usr/local/libexec/verify_github_bootstrap_approval.py','scripts/verify_github_bootstrap_approval.py',0o644),
  'install_reconciler':('/usr/local/libexec/mee-controller-reconcile','ci/claw/reconcile-owned-resources.sh',0o755),
  'install_sudoers':('/etc/sudoers.d/mee-controller-ledger','ci/claw/sudoers/mee-controller-ledger',0o440),
  'install_service':('/etc/systemd/system/mee-controller-reconcile.service','ci/claw/systemd/mee-controller-reconcile.service',0o644),
  'install_timer':('/etc/systemd/system/mee-controller-reconcile.timer','ci/claw/systemd/mee-controller-reconcile.timer',0o644)}
 def __init__(self,source,root='/',runner=None,receipt=None):self.source=Path(source);self.root=Path(root);self.runner=runner or __import__('subprocess');self.receipt=receipt;self.snapshots={}
 def path(self,p):return Path(p) if self.root==Path('/') else self.root.joinpath(*Path(p).parts[1:])
 def snapshot(self,name):
  if name in self.TARGETS:
   target=self.path(self.TARGETS[name][0]); snap=self._projection(target,content=True)
  elif name=='create_state':snap=self._projection(self.path('/var/lib/mee-controller'))
  elif name=='write_receipt':snap=self._projection(self.path('/var/lib/mee-controller/helper-install-receipt.json'),content=True)
  elif name=='enable_timer':
   snap={'enabled':self.runner.run(['systemctl','is-enabled','mee-controller-reconcile.timer'],check=False,capture_output=True,text=True).returncode==0,'active':self.runner.run(['systemctl','is-active','mee-controller-reconcile.timer'],check=False,capture_output=True,text=True).returncode==0}
  else:snap={'existed':False}
  self.snapshots[name]=snap;return snap
 def _projection(self,target,content=False):
  if not target.exists() and not target.is_symlink():return {'exists':False}
  info=target.lstat()
  if stat.S_ISLNK(info.st_mode) or not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)) or (stat.S_ISREG(info.st_mode) and info.st_nlink!=1):raise RuntimeError('UNSAFE_HELPER_TARGET')
  value={'exists':True,'kind':'directory' if stat.S_ISDIR(info.st_mode) else 'file','uid':info.st_uid,'gid':info.st_gid,'mode':stat.S_IMODE(info.st_mode),'dev':info.st_dev,'ino':info.st_ino,'nlink':info.st_nlink,'xattrs':{}}
  if hasattr(os,'listxattr'):value['xattrs']={x:os.getxattr(target,x,follow_symlinks=False).hex() for x in sorted(os.listxattr(target,follow_symlinks=False))}
  if content and value['kind']=='file':value['bytes']=target.read_bytes().hex()
  return value
 def _restore(self,target,snap):
  if not snap['exists']:
   if target.is_file():target.unlink()
   elif target.is_dir():target.rmdir()
   return
  if snap['kind']=='directory':target.mkdir(parents=True,exist_ok=True)
  else:atomic(target,bytes.fromhex(snap['bytes']))
  os.chmod(target,snap['mode'])
  if os.name=='posix':os.chown(target,snap['uid'],snap['gid'])
  if hasattr(os,'listxattr'):
   for x in os.listxattr(target,follow_symlinks=False):os.removexattr(target,x,follow_symlinks=False)
   for x,v in snap['xattrs'].items():os.setxattr(target,x,bytes.fromhex(v),follow_symlinks=False)
 def apply(self,name):
  if name=='create_state':self.path('/var/lib/mee-controller').mkdir(parents=True,exist_ok=True)
  elif name in self.TARGETS:
   target,source,mode=self.TARGETS[name]; atomic(self.path(target),(self.source/source).read_bytes());os.chmod(self.path(target),mode)
  elif name=='daemon_reload':self.runner.run(['systemctl','daemon-reload'],check=True)
  elif name=='enable_timer':self.runner.run(['systemctl','enable','--now','mee-controller-reconcile.timer'],check=True)
  elif name=='write_receipt':atomic(self.path('/var/lib/mee-controller/helper-install-receipt.json'),self.receipt or b'{}\n');os.chmod(self.path('/var/lib/mee-controller/helper-install-receipt.json'),0o600)
 def rollback(self,name):
  if name in self.TARGETS:
   self._restore(self.path(self.TARGETS[name][0]),self.snapshots[name])
  elif name=='create_state':self._restore(self.path('/var/lib/mee-controller'),self.snapshots[name])
  elif name=='enable_timer':
   snap=self.snapshots[name]
   self.runner.run(['systemctl','enable' if snap['enabled'] else 'disable','mee-controller-reconcile.timer'],check=True)
   self.runner.run(['systemctl','start' if snap['active'] else 'stop','mee-controller-reconcile.timer'],check=True)
  elif name=='daemon_reload':self.runner.run(['systemctl','daemon-reload'],check=True)
  elif name=='write_receipt':self._restore(self.path('/var/lib/mee-controller/helper-install-receipt.json'),self.snapshots[name])
def _rollback_all(backend,journal,applied,current):
 failures=[]
 for name in ([current] if current else [])+list(reversed(applied)):
  try:backend.rollback(name)
  except BaseException as e:failures.append((name,str(e)))
 if failures:journal.record('ROLLBACK_BLOCKED',applied,status='OPEN',failures=failures)
 else:journal.record('ROLLED_BACK',[],status='ROLLED_BACK')
 return failures
def execute(backend,journal):
 applied=[];current=None
 try:
  for name in OPERATIONS:
   snap=backend.snapshot(name);current=name;journal.record(f'APPLYING({name})',applied,name,snap);backend.apply(name);applied.append(name);journal.record(f'APPLIED({name})',applied);current=None
  journal.record('COMMITTED',applied,status='COMMITTED')
 except BaseException:
  journal.record('ROLLING_BACK',applied,current,journal.value.get('snapshot'))
  _rollback_all(backend,journal,applied,current);raise
def recover(backend,journal):
 backend.snapshots=getattr(backend,'snapshots',{});backend.snapshots.update(journal.value['snapshots']);current=journal.value['current'];applied=journal.value['applied'];journal.record('ROLLING_BACK',applied,current,journal.value.get('snapshot'))
 if _rollback_all(backend,journal,applied,current):raise RuntimeError('ROLLBACK_BLOCKED')
def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--journal',required=True);p.add_argument('--receipt',required=True);p.add_argument('--resume',action='store_true');a=p.parse_args(argv);backend=RealHelperBackend(a.source,receipt=Path(a.receipt).read_bytes());journal=HelperJournal.resume(a.journal) if a.resume else HelperJournal(a.journal);recover(backend,journal) if a.resume else execute(backend,journal)
if __name__=='__main__':main()
