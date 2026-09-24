#!/usr/bin/env python3
from __future__ import annotations
import argparse,datetime as dt,hashlib,hmac,json,os,re,secrets,subprocess,sys,stat,tempfile,time
from dataclasses import dataclass
from pathlib import Path
class TxError(RuntimeError): pass
@dataclass(frozen=True)
class Deadline:
 boot_id:str
 monotonic_deadline_ns:int
 deadline_utc:str
 def __post_init__(self):
  if not isinstance(self.boot_id,str) or not re.fullmatch(r'[A-Za-z0-9._-]{1,128}',self.boot_id) or not isinstance(self.monotonic_deadline_ns,int) or isinstance(self.monotonic_deadline_ns,bool) or self.monotonic_deadline_ns<=0: raise TxError('DEADLINE_INVALID')
  if not isinstance(self.deadline_utc,str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z',self.deadline_utc): raise TxError('DEADLINE_INVALID')
  try:
   value=dt.datetime.fromisoformat(self.deadline_utc.replace('Z','+00:00'))
  except (TypeError,ValueError): raise TxError('DEADLINE_INVALID') from None
  if value.tzinfo is None or value.utcoffset()!=dt.timedelta(0): raise TxError('DEADLINE_INVALID')
 def as_dict(self): return {'boot_id':self.boot_id,'monotonic_deadline_ns':self.monotonic_deadline_ns,'deadline_utc':self.deadline_utc}
 @classmethod
 def from_dict(cls,value):
  if not isinstance(value,dict) or set(value)!={'boot_id','monotonic_deadline_ns','deadline_utc'}: raise TxError('DEADLINE_INVALID')
  return cls(**value)
def current_boot_id():
 path=Path('/proc/sys/kernel/random/boot_id')
 return path.read_text().strip() if path.is_file() else 'non-linux-process-boot'
def new_deadline(seconds=900):
 if not isinstance(seconds,int) or isinstance(seconds,bool) or not 300<=seconds<=3600: raise TxError('DEADLINE_INVALID')
 now=dt.datetime.now(dt.timezone.utc)
 return Deadline(current_boot_id(),time.monotonic_ns()+seconds*1_000_000_000,(now+dt.timedelta(seconds=seconds)).isoformat().replace('+00:00','Z'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def create_credential_binding(path,binding):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);data=(json.dumps(binding,sort_keys=True,separators=(',',':'))+'\n').encode();fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 try:
  view=memoryview(data)
  while view:
   count=os.write(fd,view)
   if count<=0:raise TxError('SHORT_WRITE')
   view=view[count:]
  os.fsync(fd)
  os.close(fd);fd=-1
  if os.name=='posix':
   parent=os.open(path.parent,os.O_RDONLY);os.fsync(parent);os.close(parent)
 except BaseException:
  if fd>=0:os.close(fd)
  try:path.unlink()
  except FileNotFoundError:pass
  if os.name=='posix':
   parent=os.open(path.parent,os.O_RDONLY);os.fsync(parent);os.close(parent)
  raise
 return path
def durable_unlink(path):
 path=Path(path);path.unlink()
 if os.name=='posix':
  fd=os.open(path.parent,os.O_RDONLY)
  try:os.fsync(fd)
  finally:os.close(fd)
def durable_rmdir_empty_private(path):
 path=Path(path);info=path.lstat()
 if path.is_symlink() or not stat.S_ISDIR(info.st_mode) or any(path.iterdir()):raise TxError('CREDENTIAL_STATE_FOREIGN')
 if os.name=='posix' and (info.st_uid!=0 or stat.S_IMODE(info.st_mode)!=0o700):raise TxError('CREDENTIAL_STATE_FOREIGN')
 path.rmdir()
 if os.name=='posix':
  fd=os.open(path.parent,os.O_RDONLY)
  try:os.fsync(fd)
  finally:os.close(fd)
def path_present_no_follow(path):
 try:Path(path).lstat()
 except FileNotFoundError:return False
 except OSError:raise TxError('PATH_IDENTITY') from None
 return True
def read_private_credential_binding(durable,binding_path):
 durable=Path(durable);binding_path=Path(binding_path)
 if binding_path.parent!=durable or binding_path.name!='credential-binding.json':raise TxError('TERMINAL_BINDING_INVALID')
 try:durable_info=durable.lstat()
 except OSError:raise TxError('TERMINAL_BINDING_INVALID') from None
 if durable.is_symlink() or not stat.S_ISDIR(durable_info.st_mode) or (os.name=='posix' and (durable_info.st_uid!=0 or durable_info.st_gid!=0 or stat.S_IMODE(durable_info.st_mode)!=0o700)):raise TxError('TERMINAL_BINDING_INVALID')
 try:binding_info=binding_path.lstat()
 except OSError:raise TxError('TERMINAL_BINDING_INVALID') from None
 if binding_path.is_symlink() or not stat.S_ISREG(binding_info.st_mode) or binding_info.st_nlink!=1 or (os.name=='posix' and (binding_info.st_uid!=0 or binding_info.st_gid!=0 or stat.S_IMODE(binding_info.st_mode)!=0o600)):raise TxError('TERMINAL_BINDING_INVALID')
 try:value=closed(binding_path,{'transaction_id','controller_sha','policy_sha256'})
 except (OSError,ValueError,TxError):raise TxError('TERMINAL_BINDING_INVALID') from None
 txid=value.get('transaction_id')
 binding_after=binding_path.lstat()
 binding_identity=lambda info:(info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_ctime_ns,info.st_uid,info.st_gid,stat.S_IMODE(info.st_mode),info.st_nlink)
 if binding_identity(binding_after)!=binding_identity(binding_info):raise TxError('TERMINAL_BINDING_INVALID')
 return value,binding_info,binding_identity
def release_completed_rollback_binding(durable,binding_path,policy_sha256):
 durable=Path(durable);binding_path=Path(binding_path);value,binding_info,binding_identity=read_private_credential_binding(durable,binding_path)
 txid=value.get('transaction_id')
 if not isinstance(txid,str) or not re.fullmatch(r'[0-9a-f]{32}',txid) or not re.fullmatch(r'[0-9a-f]{40}',value.get('controller_sha','')) or value.get('policy_sha256')!=policy_sha256:raise TxError('TERMINAL_BINDING_INVALID')
 state=durable/'credential-state'
 try:state.lstat()
 except FileNotFoundError:pass
 except OSError:raise TxError('TERMINAL_BINDING_STATE') from None
 else:raise TxError('TERMINAL_BINDING_STATE')
 journal_path=durable/f'{txid}.json'
 try:info=journal_path.lstat()
 except OSError:raise TxError('TERMINAL_BINDING_JOURNAL') from None
 if journal_path.is_symlink() or not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or (os.name=='posix' and (info.st_uid!=0 or info.st_gid!=0 or stat.S_IMODE(info.st_mode)!=0o600)):raise TxError('TERMINAL_BINDING_JOURNAL')
 try:journal=closed(journal_path,{'schema_version','phase','history','applied','current','snapshot','snapshots','verified_results','deadline','finalize_projection','status'})
 except (OSError,ValueError,TxError):raise TxError('TERMINAL_BINDING_JOURNAL') from None
 if not is_terminal_rolled_back_journal(journal):raise TxError('TERMINAL_BINDING_JOURNAL')
 journal_after=journal_path.lstat()
 if binding_identity(journal_after)!=binding_identity(info):raise TxError('TERMINAL_BINDING_JOURNAL')
 final_binding=binding_path.lstat()
 if binding_identity(final_binding)!=binding_identity(binding_info):raise TxError('TERMINAL_BINDING_INVALID')
 durable_unlink(binding_path)
def pairs(xs):
 d={}
 for k,v in xs:
  if k in d: raise TxError('DUPLICATE_KEY')
  d[k]=v
 return d
def closed(path,fields):
 v=json.loads(Path(path).read_text(),object_pairs_hook=pairs)
 if not isinstance(v,dict) or set(v)!=fields: raise TxError('MANIFEST_NOT_CLOSED')
 return v
def atomic(path,data):
 path.parent.mkdir(parents=True,exist_ok=True); fd,tmpname=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=path.parent); tmp=Path(tmpname)
 try:
  view=memoryview(data)
  while view:
   n=os.write(fd,view)
   if n<=0: raise TxError('SHORT_WRITE')
   view=view[n:]
  os.fsync(fd)
 finally: os.close(fd)
 os.replace(tmp,path)
 if os.name=='posix':
  fd=os.open(path.parent,os.O_RDONLY)
  try: os.fsync(fd)
  finally: os.close(fd)
def add_subid_entry(content,user,start,count):
 if not isinstance(start,int) or not isinstance(count,int) or start<1 or count<1 or start+count>2**32: raise TxError('SUBID_RANGE_INVALID')
 end=start+count
 kept=[]
 for line in content.splitlines():
  if not line: continue
  parts=line.split(':')
  if len(parts)!=3 or not parts[0] or not all(x.isascii() and x.isdigit() for x in parts[1:]): raise TxError('SUBID_FILE_INVALID')
  other_start,other_count=int(parts[1]),int(parts[2])
  if other_start<1 or other_count<1 or other_start+other_count>2**32: raise TxError('SUBID_FILE_INVALID')
  other_end=other_start+other_count
  if parts[0]==user:
   if (other_start,other_count)==(start,count): kept.append(line); continue
   raise TxError('SUBID_USER_CONFLICT')
  if max(start,other_start)<min(end,other_end): raise TxError('SUBID_RANGE_OVERLAP')
  kept.append(line)
 if not any(x.startswith(user+':') for x in kept): kept.append(f'{user}:{start}:{count}')
 return ('\n'.join(kept)+'\n').encode()
def regular_private(path,expected_links=1):
 info=Path(path).lstat()
 if not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode) or info.st_nlink!=expected_links: raise TxError('UNSAFE_FILE_IDENTITY')
 return info
def atomic_preserve(path,data,metadata):
 atomic(path,data); os.chmod(path,stat.S_IMODE(metadata.st_mode))
 if os.name=='posix': os.chown(path,metadata.st_uid,metadata.st_gid)
def path_projection(path,content=False):
 path=Path(path)
 if not path.exists(): return {'exists':False}
 info=path.lstat(); value={'exists':True,'kind':'directory' if stat.S_ISDIR(info.st_mode) else 'file','mode':stat.S_IMODE(info.st_mode),'uid':info.st_uid,'gid':info.st_gid,'xattrs':{}}
 if hasattr(os,'listxattr'): value['xattrs']={x:os.getxattr(path,x,follow_symlinks=False).hex() for x in sorted(os.listxattr(path,follow_symlinks=False))}
 if content and value['kind']=='file':value['content']=path.read_bytes().hex()
 return value
def restore_projection(path,projection):
 path=Path(path)
 if not projection['exists']:
  if path.is_file():path.unlink()
  elif path.is_dir():path.rmdir()
  return
 if projection['kind']=='directory':path.mkdir(parents=True,exist_ok=True)
 else:atomic(path,bytes.fromhex(projection['content']))
 os.chmod(path,projection['mode'])
 if os.name=='posix':os.chown(path,projection['uid'],projection['gid'])
 if hasattr(os,'listxattr'):
  for name in os.listxattr(path,follow_symlinks=False):os.removexattr(path,name,follow_symlinks=False)
  for name,value in projection['xattrs'].items():os.setxattr(path,name,bytes.fromhex(value),follow_symlinks=False)
def _tree_members(root):
 root=Path(root)
 if root.is_symlink() or not root.is_dir(): raise TxError('RUNNER_TREE_INVALID')
 initial=root.lstat(); resolved=root.resolve(strict=True); members=[]
 for item in sorted([root,*root.rglob('*')],key=lambda p:('.' if p==root else p.relative_to(root).as_posix())):
  info=item.lstat(); relative='.' if item==root else item.relative_to(root).as_posix()
  if stat.S_ISLNK(info.st_mode):
   try: target=item.resolve(strict=True)
   except (OSError,RuntimeError) as exc: raise TxError('RUNNER_TREE_ESCAPE') from exc
   if target!=resolved and resolved not in target.parents: raise TxError('RUNNER_TREE_ESCAPE')
   kind='link'; link_target=os.readlink(item)
  elif stat.S_ISDIR(info.st_mode): kind='directory'; link_target=None
  elif stat.S_ISREG(info.st_mode):
   if info.st_nlink!=1: raise TxError('UNSAFE_FILE_IDENTITY')
   kind='file'; link_target=None
  else: raise TxError('RUNNER_TREE_INVALID')
  members.append((item,info,relative,kind,link_target))
 final=root.lstat()
 if (initial.st_dev,initial.st_ino)!=(final.st_dev,final.st_ino):raise TxError('TREE_METADATA_DRIFT')
 return resolved,members
def _identity(info): return {'dev':info.st_dev,'ino':info.st_ino,'nlink':info.st_nlink}
def tree_metadata_projection(path):
 root,members=_tree_members(path); result=[]
 for item,info,relative,kind,target in members:
  xattrs={}
  if hasattr(os,'listxattr'):
   xattrs={name:os.getxattr(item,name,follow_symlinks=False).hex() for name in sorted(os.listxattr(item,follow_symlinks=False))}
  result.append({'path':relative,'kind':kind,'target':target,'mode':stat.S_IMODE(info.st_mode),'uid':info.st_uid,'gid':info.st_gid,'xattrs':xattrs,**_identity(info)})
 return {'schema_version':'claw-runner-tree-metadata-v1','members':result}
def _open_anchored_member(root_fd,record,records):
 if record['path']=='.':
  fd=os.dup(root_fd); info=os.fstat(fd)
  if (info.st_dev,info.st_ino)!=(record['dev'],record['ino']):os.close(fd);raise TxError('TREE_METADATA_DRIFT')
  return fd
 parts=record['path'].split('/'); parent=os.dup(root_fd); prefix=[]
 try:
  for component in parts[:-1]:
   prefix.append(component); expected=records.get('/'.join(prefix))
   if not expected or expected['kind']!='directory':raise TxError('TREE_METADATA_DRIFT')
   try:child=os.open(component,os.O_RDONLY|getattr(os,'O_DIRECTORY',0)|getattr(os,'O_NOFOLLOW',0),dir_fd=parent)
   except OSError as exc:raise TxError('TREE_METADATA_DRIFT') from exc
   info=os.fstat(child)
   if (info.st_dev,info.st_ino)!=(expected['dev'],expected['ino']):os.close(child);raise TxError('TREE_METADATA_DRIFT')
   os.close(parent);parent=child
  flags=os.O_RDONLY|getattr(os,'O_NOFOLLOW',0)
  if record['kind']=='directory':flags|=getattr(os,'O_DIRECTORY',0)
  try:fd=os.open(parts[-1],flags,dir_fd=parent)
  except OSError as exc:raise TxError('TREE_METADATA_DRIFT') from exc
  info=os.fstat(fd)
  if (info.st_dev,info.st_ino)!=(record['dev'],record['ino']):os.close(fd);raise TxError('TREE_METADATA_DRIFT')
  return fd
 finally:os.close(parent)
def _open_anchored_root(path,projection):
 root_record=projection['members'][0] if projection.get('members') else None
 if not isinstance(root_record,dict) or root_record.get('path')!='.' or root_record.get('kind')!='directory':raise TxError('TREE_METADATA_INVALID')
 path=Path(path); before=path.lstat()
 if path.is_symlink() or not stat.S_ISDIR(before.st_mode):raise TxError('RUNNER_TREE_INVALID')
 try:fd=os.open(path,os.O_RDONLY|getattr(os,'O_DIRECTORY',0)|getattr(os,'O_NOFOLLOW',0))
 except OSError as exc:raise TxError('TREE_METADATA_DRIFT') from exc
 after=os.fstat(fd)
 if (before.st_dev,before.st_ino)!=(after.st_dev,after.st_ino) or (after.st_dev,after.st_ino)!=(root_record['dev'],root_record['ino']):os.close(fd);raise TxError('TREE_METADATA_DRIFT')
 return fd
def restore_tree_metadata(path,projection):
 if not isinstance(projection,dict) or set(projection)!={'schema_version','members'} or projection['schema_version']!='claw-runner-tree-metadata-v1' or not isinstance(projection['members'],list): raise TxError('TREE_METADATA_INVALID')
 root,members=_tree_members(path); current=[(relative,kind,target) for _,_,relative,kind,target in members]; expected=[(x.get('path'),x.get('kind'),x.get('target')) for x in projection['members'] if isinstance(x,dict)]
 if current!=expected or len(expected)!=len(projection['members']): raise TxError('TREE_METADATA_DRIFT')
 required={'path','kind','target','mode','uid','gid','xattrs','dev','ino','nlink'}
 if any(set(record)!=required for record in projection['members']):raise TxError('TREE_METADATA_INVALID')
 records={record['path']:record for record in projection['members']}
 if len(records)!=len(projection['members']):raise TxError('TREE_METADATA_INVALID')
 if os.name!='posix':
  by_relative={relative:item for item,_,relative,_,_ in members}
  for record in reversed(projection['members']):
   if record['kind']!='link':os.chmod(by_relative[record['path']],record['mode'],follow_symlinks=False)
  if tree_metadata_projection(root)!=projection: raise TxError('TREE_METADATA_RESTORE_FAILED')
  return
 root_fd=_open_anchored_root(path,projection)
 try:
  for record in reversed(projection['members']):
   if record['kind']=='link':continue
   fd=_open_anchored_member(root_fd,record,records)
   try:
    if os.name=='posix':os.fchown(fd,record['uid'],record['gid'])
    os.fchmod(fd,record['mode'])
    if hasattr(os,'listxattr'):
     for name in os.listxattr(fd):os.removexattr(fd,name)
     for name,value in record['xattrs'].items():os.setxattr(fd,name,bytes.fromhex(value))
   finally:os.close(fd)
 finally:os.close(root_fd)
 if tree_metadata_projection(root)!=projection: raise TxError('TREE_METADATA_RESTORE_FAILED')
def transfer_tree_ownership(path,uid,gid,projection):
 if tree_metadata_projection(path)!=projection:raise TxError('TREE_METADATA_DRIFT')
 if os.name!='posix':return
 records={record['path']:record for record in projection['members']}
 if len(records)!=len(projection['members']):raise TxError('TREE_METADATA_INVALID')
 root_fd=_open_anchored_root(path,projection)
 try:
  for record in reversed(projection['members']):
   if record['kind']=='link':continue
   fd=_open_anchored_member(root_fd,record,records)
   try:
    if os.name=='posix':os.fchown(fd,uid,gid)
   finally:os.close(fd)
 finally:os.close(root_fd)
def closed_tree(path):
 root=Path(path)
 if root.is_symlink() or not root.is_dir(): raise TxError('RUNNER_TREE_INVALID')
 return _tree_members(root)[0]
def unit_projection(raw):
 value={}
 for line in raw.splitlines():
  if '=' not in line: raise TxError('UNIT_PROJECTION_INVALID')
  key,item=line.split('=',1)
  if key in value: raise TxError('UNIT_PROJECTION_DUPLICATE')
  value[key]=item
 required={'MainPID','User','ExecStart','WorkingDirectory','FragmentPath','ActiveState'}
 if set(value)!=required: raise TxError('UNIT_PROJECTION_NOT_CLOSED')
 if not value['MainPID'].isdigit() or int(value['MainPID'])<=0 or value['ActiveState']!='active': raise TxError('UNIT_NOT_HEALTHY')
 return value
class CredentialCommitments:
 DOMAIN=b'MEE_CLAW_CREDENTIAL_STATE_V1\0'
 def _xattrs(self,path):
  if not hasattr(os,'listxattr'): return {}
  return {name:os.getxattr(path,name,follow_symlinks=False).hex() for name in sorted(os.listxattr(path,follow_symlinks=False))}
 def __init__(self,transaction_root,binding):
  self.root=Path(transaction_root)/'credential-state'; self.binding=dict(binding)
  if set(self.binding)!={'transaction_id','controller_sha','policy_sha256'}: raise TxError('CREDENTIAL_BINDING_NOT_CLOSED')
  self.key_path=self.root/'key'; self.map_path=self.root/'map'
 def _assert_private(self,path,mode):
  info=path.lstat()
  if path.is_symlink() or not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or (os.name=='posix' and stat.S_IMODE(info.st_mode)!=mode): raise TxError('CREDENTIAL_STATE_PERMISSIONS')
  if os.name=='posix' and info.st_uid!=0: raise TxError('CREDENTIAL_STATE_OWNER')
 def _mac_file(self,key,root,relative,metadata,post_owner,header_override=None):
  target=root/relative; before=regular_private(target); digest=hmac.new(key,self.DOMAIN,digestmod='sha256')
  header={'binding':self.binding,'ordinal':metadata['ordinal'],'path':relative.as_posix(),'mode':stat.S_IMODE(before.st_mode),'uid':before.st_uid,'gid':before.st_gid,'size':before.st_size,'dev':before.st_dev,'ino':before.st_ino,'nlink':before.st_nlink,'xattrs':self._xattrs(target),'post_uid':post_owner[0],'post_gid':post_owner[1]}
  digest.update(json.dumps(header_override or header,sort_keys=True,separators=(',',':')).encode()+b'\0')
  fd=os.open(target,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0)|getattr(os,'O_BINARY',0))
  try:
   while True:
    chunk=os.read(fd,1024*1024)
    if not chunk: break
    digest.update(chunk)
   after=os.fstat(fd)
  finally: os.close(fd)
  if (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns): raise TxError('CREDENTIAL_CONCURRENT_CHANGE')
  return header,digest.hexdigest()
 def create(self,runner_tree,post_owner,baseline_projection=None):
  if baseline_projection is not None and tree_metadata_projection(runner_tree)!=baseline_projection: raise TxError('TREE_METADATA_DRIFT')
  self.root.mkdir(parents=True,mode=0o700,exist_ok=False); os.chmod(self.root,0o700)
  key=secrets.token_bytes(32); fd=os.open(self.key_path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,'O_BINARY',0),0o600)
  try: os.write(fd,key); os.fsync(fd)
  finally: os.close(fd)
  root,members=_tree_members(runner_tree); names=[]; links=[]
  for item,_,relative,kind,_ in members:
   if kind=='file': names.append(Path(relative))
   elif kind=='link': links.append((item,relative))
  entries=[]; directories=[]; link_entries=[]
  for ordinal,item in enumerate([x[0] for x in members if x[3]=='directory']):
   info=item.lstat(); header={'ordinal':ordinal,'path':'.' if item==root else item.relative_to(root).as_posix(),'mode':stat.S_IMODE(info.st_mode),'uid':info.st_uid,'gid':info.st_gid,'dev':info.st_dev,'ino':info.st_ino,'nlink':info.st_nlink,'xattrs':self._xattrs(item),'post_uid':post_owner[0],'post_gid':post_owner[1]}; mac=hmac.new(key,self.DOMAIN+b'DIR\0'+json.dumps(header,sort_keys=True,separators=(',',':')).encode(),digestmod='sha256').hexdigest(); directories.append({'header':header,'mac':mac})
  for ordinal,name in enumerate(names):
   header,mac=self._mac_file(key,root,name,{'ordinal':ordinal},post_owner); entries.append({'header':header,'mac':mac})
  for ordinal,(item,relative) in enumerate(links):
   info=item.lstat(); header={'ordinal':ordinal,'path':relative,'target':os.readlink(item),'mode':stat.S_IMODE(info.st_mode),'uid':info.st_uid,'gid':info.st_gid,'dev':info.st_dev,'ino':info.st_ino,'nlink':info.st_nlink,'xattrs':self._xattrs(item),'post_uid':info.st_uid,'post_gid':info.st_gid}; mac=hmac.new(key,self.DOMAIN+b'LINK\0'+json.dumps(header,sort_keys=True,separators=(',',':')).encode(),digestmod='sha256').hexdigest(); link_entries.append({'header':header,'mac':mac})
  set_mac=hmac.new(key,self.DOMAIN+b'SET\0'+json.dumps(self.binding,sort_keys=True,separators=(',',':')).encode(),digestmod='sha256')
  for entry in directories+entries+link_entries:set_mac.update(json.dumps(entry,sort_keys=True,separators=(',',':')).encode()+b'\n')
  if baseline_projection is not None and tree_metadata_projection(runner_tree)!=baseline_projection: raise TxError('TREE_METADATA_DRIFT')
  atomic(self.map_path,(json.dumps({'binding':self.binding,'directories':directories,'entries':entries,'links':link_entries,'set_mac':set_mac.hexdigest()},sort_keys=True,separators=(',',':'))+'\n').encode()); os.chmod(self.map_path,0o600)
  self._assert_private(self.key_path,0o600); self._assert_private(self.map_path,0o600)
  return len(entries)
 def verify(self,runner_tree,expect_post=False):
  self._assert_private(self.key_path,0o600); self._assert_private(self.map_path,0o600); key=self.key_path.read_bytes()
  value=json.loads(self.map_path.read_text(),object_pairs_hook=pairs)
  if set(value)!={'binding','directories','entries','links','set_mac'} or value['binding']!=self.binding: raise TxError('CREDENTIAL_STATE_REPLAY')
  set_mac=hmac.new(key,self.DOMAIN+b'SET\0'+json.dumps(self.binding,sort_keys=True,separators=(',',':')).encode(),digestmod='sha256')
  root,members=_tree_members(runner_tree); seen=[]
  current_dirs=[x[0] for x in members if x[3]=='directory']
  if len(current_dirs)!=len(value['directories']): raise TxError('CREDENTIAL_SET_MISMATCH')
  for ordinal,(item,entry) in enumerate(zip(current_dirs,value['directories'])):
   info=item.lstat(); expected=dict(entry['header']); owner=(expected['post_uid'],expected['post_gid']) if expect_post else (expected['uid'],expected['gid']); header={'ordinal':ordinal,'path':'.' if item==root else item.relative_to(root).as_posix(),'mode':stat.S_IMODE(info.st_mode),'uid':expected['uid'],'gid':expected['gid'],'dev':info.st_dev,'ino':info.st_ino,'nlink':info.st_nlink,'xattrs':self._xattrs(item),'post_uid':expected['post_uid'],'post_gid':expected['post_gid']}
   mac=hmac.new(key,self.DOMAIN+b'DIR\0'+json.dumps(expected,sort_keys=True,separators=(',',':')).encode(),digestmod='sha256').hexdigest()
   if header!=expected or (info.st_uid,info.st_gid)!=owner or not hmac.compare_digest(mac,entry['mac']): raise TxError('CREDENTIAL_STATE_MISMATCH')
   set_mac.update(json.dumps(entry,sort_keys=True,separators=(',',':')).encode()+b'\n')
  for ordinal,entry in enumerate(value['entries']):
   if set(entry)!={'header','mac'} or entry['header'].get('ordinal')!=ordinal: raise TxError('CREDENTIAL_MAP_INVALID')
   relative=Path(entry['header']['path']); seen.append(relative.as_posix())
   expected=dict(entry['header']); header,mac=self._mac_file(key,root,relative,{'ordinal':ordinal},(expected['post_uid'],expected['post_gid']),header_override=expected)
   wanted_owner=(expected['post_uid'],expected['post_gid']) if expect_post else (expected['uid'],expected['gid'])
   comparable={k:v for k,v in header.items() if k not in {'uid','gid'}}; expected_comparable={k:v for k,v in expected.items() if k not in {'uid','gid'}}
   if comparable!=expected_comparable or (header['uid'],header['gid'])!=wanted_owner or not hmac.compare_digest(mac,entry['mac']): raise TxError('CREDENTIAL_STATE_MISMATCH')
   set_mac.update(json.dumps(entry,sort_keys=True,separators=(',',':')).encode()+b'\n')
  current_links=[x for x in members if x[3]=='link']
  if len(current_links)!=len(value['links']): raise TxError('CREDENTIAL_SET_MISMATCH')
  for ordinal,((item,info,relative,_,target),entry) in enumerate(zip(current_links,value['links'])):
   expected=dict(entry['header']); owner=(expected['post_uid'],expected['post_gid']) if expect_post else (expected['uid'],expected['gid']); header={'ordinal':ordinal,'path':relative,'target':target,'mode':stat.S_IMODE(info.st_mode),'uid':expected['uid'],'gid':expected['gid'],'dev':info.st_dev,'ino':info.st_ino,'nlink':info.st_nlink,'xattrs':self._xattrs(item),'post_uid':expected['post_uid'],'post_gid':expected['post_gid']}; mac=hmac.new(key,self.DOMAIN+b'LINK\0'+json.dumps(expected,sort_keys=True,separators=(',',':')).encode(),digestmod='sha256').hexdigest()
   if header!=expected or (info.st_uid,info.st_gid)!=owner or not hmac.compare_digest(mac,entry['mac']): raise TxError('CREDENTIAL_STATE_MISMATCH')
   set_mac.update(json.dumps(entry,sort_keys=True,separators=(',',':')).encode()+b'\n')
  current=sorted(x[2] for x in members if x[3]=='file')
  if current!=seen or not hmac.compare_digest(set_mac.hexdigest(),value['set_mac']): raise TxError('CREDENTIAL_SET_MISMATCH')
  return len(seen)
 def close(self,terminal):
  if terminal not in {'ROLLED_BACK','OWNER_ROLLBACK_CLOSURE'}: raise TxError('CREDENTIAL_STATE_RETAIN_REQUIRED')
  if not self.root.exists(): return
  if self.root.is_symlink() or not self.root.is_dir(): raise TxError('CREDENTIAL_STATE_PARTIAL')
  if not self.key_path.exists() and not self.map_path.exists(): durable_rmdir_empty_private(self.root); return
  if not self.key_path.exists() or not self.map_path.exists(): raise TxError('CREDENTIAL_STATE_PARTIAL')
  self.key_path.unlink(); self.map_path.unlink(); os.rmdir(self.root)
  if os.name=='posix':
   fd=os.open(self.root.parent,os.O_RDONLY)
   try: os.fsync(fd)
   finally: os.close(fd)
class Journal:
 def __init__(self,path):
  self.path=Path(path)
  if self.path.exists(): raise TxError('JOURNAL_ALREADY_EXISTS')
  self.value={'schema_version':'claw-host-journal-v1','phase':'PREPARED','history':['PREPARED'],'applied':[],'current':None,'snapshot':None,'snapshots':{},'verified_results':{},'deadline':None,'finalize_projection':None,'status':'OPEN'}; atomic(self.path,(json.dumps(self.value,sort_keys=True,separators=(',',':'))+'\n').encode())
 def record(self,phase,applied=None,current=None,snapshot=None,status=None,verified_result=None,deadline=None,finalize_projection=None):
  self.value['phase']=phase
  self.value['history'].append(phase)
  if applied is not None:self.value['applied']=list(applied)
  self.value['current']=current; self.value['snapshot']=snapshot
  if current is not None and snapshot is not None:self.value['snapshots'][current]=snapshot
  if current is not None and verified_result is not None:self.value['verified_results'][current]=verified_result
  if deadline is not None:self.value['deadline']=deadline
  if finalize_projection is not None:self.value['finalize_projection']=finalize_projection
  if status is not None:self.value['status']=status
  atomic(self.path,(json.dumps(self.value,sort_keys=True,separators=(',',':'))+'\n').encode())
 @classmethod
 def load(cls,path,allowed_statuses=('OPEN',)):
  self=object.__new__(cls); self.path=Path(path); self.value=closed(self.path,{'schema_version','phase','history','applied','current','snapshot','snapshots','verified_results','deadline','finalize_projection','status'})
  if self.value['status'] not in allowed_statuses: raise TxError('JOURNAL_TERMINAL')
  return self
 @classmethod
 def resume(cls,path): return cls.load(path,('OPEN',))
 @classmethod
 def for_rollback(cls,path): return cls.load(path,('OPEN','COMMITTED'))
 @classmethod
 def load_private(cls,durable,path,allowed_statuses):
  durable=Path(durable);path=Path(path)
  if path.parent!=durable or not re.fullmatch(r'[0-9a-f]{32}\.json',path.name):raise TxError('JOURNAL_IDENTITY')
  try:root_info=durable.lstat();info=path.lstat()
  except OSError:raise TxError('JOURNAL_IDENTITY') from None
  if durable.is_symlink() or not stat.S_ISDIR(root_info.st_mode) or path.is_symlink() or not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:raise TxError('JOURNAL_IDENTITY')
  if os.name=='posix' and (root_info.st_uid!=0 or root_info.st_gid!=0 or stat.S_IMODE(root_info.st_mode)!=0o700 or info.st_uid!=0 or info.st_gid!=0 or stat.S_IMODE(info.st_mode)!=0o600):raise TxError('JOURNAL_IDENTITY')
  try:value=closed(path,{'schema_version','phase','history','applied','current','snapshot','snapshots','verified_results','deadline','finalize_projection','status'})
  except (OSError,ValueError,TxError):raise TxError('JOURNAL_IDENTITY') from None
  after=path.lstat();identity=lambda x:(x.st_dev,x.st_ino,x.st_size,x.st_mtime_ns,x.st_ctime_ns,x.st_uid,x.st_gid,stat.S_IMODE(x.st_mode),x.st_nlink)
  if identity(after)!=identity(info) or value.get('schema_version')!='claw-host-journal-v1' or value.get('status') not in allowed_statuses:raise TxError('JOURNAL_IDENTITY')
  self=object.__new__(cls);self.path=path;self.value=value;self._private_identity=identity(info);return self
 def assert_private_identity(self):
  try:info=self.path.lstat()
  except OSError:raise TxError('JOURNAL_IDENTITY') from None
  identity=(info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_ctime_ns,info.st_uid,info.st_gid,stat.S_IMODE(info.st_mode),info.st_nlink)
  if getattr(self,'_private_identity',None)!=identity:raise TxError('JOURNAL_IDENTITY')

def is_fresh_prepared_journal(value):
 return value=={'schema_version':'claw-host-journal-v1','phase':'PREPARED','history':['PREPARED'],'applied':[],'current':None,'snapshot':None,'snapshots':{},'verified_results':{},'deadline':None,'finalize_projection':None,'status':'OPEN'}

class Backend:
 def snapshot(self,name): raise NotImplementedError
 def reconcile(self,name,snapshot): raise NotImplementedError
 def prepare(self,name): raise NotImplementedError
 def apply(self,name): raise NotImplementedError
 def verify(self,name): raise NotImplementedError
 def rollback(self,name): raise NotImplementedError
 def final_verify(self): raise NotImplementedError
class FakeBackend(Backend):
 def __init__(self,fail=''): self.active=[]; self.events=[]; self.fail=fail
 def apply(self,name):
  self.events.append(('apply',name))
  if self.fail==f'before:{name}': raise TxError('INJECTED')
  self.active.append(name)
  if self.fail==f'after:{name}': raise TxError('INJECTED')
 def prepare(self,name): self.events.append(('prepare',name))
 def snapshot(self,name): self.events.append(('snapshot',name)); return {'active':name in self.active}
 def reconcile(self,name,snapshot): self.events.append(('reconcile',name)); self.rollback(name)
 def verify(self,name):
  self.events.append(('verify',name))
  result={'operation':name,'status':'VERIFIED'}
  if name=='runner_api_canary':result['runner_api']={'repository':'Dimkox/multi-exchange-engine','runner_id':17,'runner_name':'claw-engine-runner','status':'online','labels':['claw','claw-engine-runner','self-hosted'],'matching_count':1,'total_count':2}
  return result
 def rollback(self,name): self.events.append(('rollback',name)); self.active.remove(name) if name in self.active else None
 def final_verify(self):
  self.events.append(('final_verify','all'))
  if self.fail=='final_verify': raise TxError('INJECTED')
class CommandRunner:
 def run(self,argv,input=None): return __import__('subprocess').run(argv,input=input,text=True,check=True,capture_output=True)
class RootPaths:
 def __init__(self,root='/'): self.root=Path(root)
 def __call__(self,path):
  path=Path(path)
  return path if self.root==Path('/') else self.root.joinpath(*path.parts[1:])
class RealBackend(Backend):
 def __init__(self,policy,runner=None,archives=(),package_records=(),root='/',oci_archive=None,token_reader=None,credential_binding=None):
  self.p=policy; self.r=runner or CommandRunner(); self.archives=tuple(map(str,archives)); self.package_records=tuple(package_records); self.paths=RootPaths(root); self.oci_archive=Path(oci_archive) if oci_archive else None; self.token_reader=token_reader; self.done=[]; self.snapshots={}; self.staged_archives=(); self.staged_oci=None
  self.credential_state=CredentialCommitments(self.paths(policy['transaction_root']),credential_binding) if credential_binding else None
 def prepare(self,name):
  if self.p['oci_archive_sha256']=='0'*64: raise TxError('OCI_ARCHIVE_UNRESOLVED')
  if name in {'snapshot_host','transfer_ownership'}: closed_tree(self.paths(self.p['runner_tree']))
  if name=='create_identity' and self.paths(self.p['runner_home']).exists(): raise TxError('RUNNER_HOME_PREEXISTS')
  if name=='configure_subids':
   regular_private(self.paths('/etc/subuid')); regular_private(self.paths('/etc/subgid'))
  if name=='install_packages': self._stage_packages()
  if name=='load_oci': self._stage_oci()
 def _stage_oci(self):
  if self.oci_archive is None or self.oci_archive.is_symlink() or not self.oci_archive.is_file(): raise TxError('OCI_ARCHIVE_INVALID')
  expected=self.p['oci_archive_sha256']
  if expected=='0'*64 or sha(self.oci_archive)!=expected: raise TxError('OCI_ARCHIVE_HASH')
  target=self.paths(self.p['transaction_root']+'/image.oci'); atomic(target,self.oci_archive.read_bytes())
  if sha(target)!=expected: raise TxError('OCI_ARCHIVE_SWAP')
  self.staged_oci=target
 def _stage_packages(self):
  if len(self.archives)!=len(self.package_records): raise TxError('PACKAGE_CLOSURE_COUNT')
  required={'name','version','architecture','sha256'}
  if any(not isinstance(x,dict) or set(x)!=required for x in self.package_records): raise TxError('PACKAGE_CLOSURE_NOT_CLOSED')
  tuples=[(x['name'],x['version'],x['architecture'],x['sha256']) for x in self.package_records]
  if len(set(tuples))!=len(tuples) or len({x[0] for x in tuples})!=len(tuples): raise TxError('PACKAGE_CLOSURE_DUPLICATE')
  destination=self.paths(self.p['transaction_root']+'/packages'); destination.mkdir(parents=True,exist_ok=True)
  staged=[]
  for source,record in zip(self.archives,self.package_records):
   source=Path(source); info=source.lstat()
   if not stat.S_ISREG(info.st_mode) or source.is_symlink(): raise TxError('PACKAGE_ARCHIVE_NOT_REGULAR')
   if sha(source)!=record['sha256']: raise TxError('PACKAGE_ARCHIVE_HASH')
   metadata=self.r.run(['dpkg-deb','--show','--showformat=${Package}\t${Version}\t${Architecture}\n',str(source)]).stdout.strip().split('\t')
   if metadata!=[record['name'],record['version'],record['architecture']]: raise TxError('PACKAGE_ARCHIVE_METADATA')
   target=destination/(record['name']+'.deb'); data=source.read_bytes(); atomic(target,data)
   if sha(target)!=record['sha256']: raise TxError('PACKAGE_ARCHIVE_SWAP')
   staged.append(str(target))
  self.staged_archives=tuple(staged)
 def snapshot(self,name):
  p=self.p
  probes={
   'freeze_inputs':['test','-e',str(self.paths(p['transaction_root']))],
   'install_packages':['dpkg-query','-W','-f=${Package}\t${Version}\t${Architecture}\t${db:Status-Abbrev}\n'],
   'create_identity':['sh','-c','getent passwd "$1" || true','identity',p['runner_user']],
   'configure_subids':['sh','-c',f'printf "SUBUID\\n"; cat "$1"; printf "SUBGID\\n"; cat "$2"','subids',str(self.paths('/etc/subuid')),str(self.paths('/etc/subgid'))],
   'configure_runtime':['loginctl','show-user',p['runner_user'],'-p','Linger'],
   'stop_engine':['systemctl','is-active',p['engine_service']],
   'start_engine':['systemctl','is-active',p['engine_service']],
   'app_canary':['systemctl','show',p['app_service'],'--property=MainPID,User,ExecStart,WorkingDirectory,FragmentPath,ActiveState'],
  }
  result=self.r.run(probes[name]) if name in probes else None
  probe=getattr(result,'stdout','') if result is not None else ''
  if name=='install_dropin':
   target=self.paths(f"/etc/systemd/system/{p['engine_service']}.d/10-claw-user.conf")
   probe=target.read_text() if target.is_file() and not target.is_symlink() else ''
   snap_target_existed=target.is_file() and not target.is_symlink()
  snap={'probe':probe,'operation':name}
  if name=='snapshot_host':
   metadata=tree_metadata_projection(self.paths(p['runner_tree'])); metadata_path=self.paths(p['transaction_root']+'/ownership.before.json'); raw=(json.dumps(metadata,sort_keys=True,separators=(',',':'))+'\n').encode(); atomic(metadata_path,raw); os.chmod(metadata_path,0o600); snap['metadata_path']=str(metadata_path); snap['metadata_sha256']=hashlib.sha256(raw).hexdigest(); snap['app_projection']=self.r.run(['systemctl','show',p['app_service'],'--property=MainPID,User,ExecStart,WorkingDirectory,FragmentPath,ActiveState']).stdout
  if name=='transfer_ownership':
   baseline=self.snapshots.get('snapshot_host',{}); snap['metadata_path']=baseline.get('metadata_path'); snap['metadata_sha256']=baseline.get('metadata_sha256')
  if name=='install_packages': snap['selections']=self.r.run(['dpkg','--get-selections']).stdout
  if name=='configure_subids':
   for kind in ('subuid','subgid'):
    info=regular_private(self.paths('/etc/'+kind)); snap[kind+'_metadata']={'mode':stat.S_IMODE(info.st_mode),'uid':info.st_uid,'gid':info.st_gid,'dev':info.st_dev,'ino':info.st_ino}
  if name=='load_oci':
   try: image=self.r.run(['runuser','-u',p['runner_user'],'--','env',f"HOME={p['runner_home']}",f"XDG_RUNTIME_DIR=/run/user/{p['runner_uid']}",'podman','image','inspect','--format={{.Digest}}',p['image']]).stdout.strip()
   except __import__('subprocess').CalledProcessError as e:
    if e.returncode==125 and 'no such image' in (e.stderr or '').lower(): image=''
    else: raise TxError('OCI_BASELINE_INSPECT_FAILED') from e
   snap['image_existed']=bool(image); snap['image_digest']=image
  if name in {'stop_engine','start_engine'}: snap['was_active']=probe.strip()=='active'
  if name=='create_identity': snap['identity_existed']=bool(probe.strip())
  if name in {'stop_engine','start_engine'}:
   snap['unit_projection']=self.r.run(['systemctl','show',p['engine_service'],'--property=User,Group,ExecStart,WorkingDirectory,FragmentPath,ActiveState']).stdout
  if name=='configure_runtime': snap['linger_was_enabled']='Linger=yes' in probe
  if name=='configure_runtime':
   runtime=self.paths(f"/run/user/{p['runner_uid']}"); containers=self.paths(f"{p['runner_home']}/.config/containers"); storage=containers/'storage.conf'
   runtime_unit=self.r.run(['systemctl','is-active',f"user-runtime-dir@{p['runner_uid']}.service"]).stdout.strip()
   home=self.paths(p['runner_home']); config=home/'.config'; snap.update({'runtime_existed':runtime.is_dir(),'runtime_unit_was_active':runtime_unit=='active','containers_existed':containers.is_dir(),'storage_existed':storage.is_file() and not storage.is_symlink(),'storage_content':storage.read_text() if storage.is_file() and not storage.is_symlink() else '','runtime_projection':path_projection(runtime),'home_projection':path_projection(home),'config_projection':path_projection(config),'containers_projection':path_projection(containers),'storage_projection':path_projection(storage,content=True),'owned_paths':[str(runtime),str(config),str(containers),str(storage)]})
  if name=='install_dropin': snap['previous_content']=probe
  if name=='install_dropin': snap['target_existed']=snap_target_existed
  if name=='app_canary':
   app=unit_projection(probe)
   if app['User']!='pall' or app['WorkingDirectory']!=p['app_working_directory'] or not app['ExecStart'] or not app['FragmentPath'].endswith('.service'): raise TxError('APP_BASELINE_INVALID')
  self.snapshots[name]=snap; return snap
 def reconcile(self,name,snapshot):
  if not isinstance(snapshot,dict) or snapshot.get('operation')!=name: raise TxError('WAL_SNAPSHOT_INVALID')
  self.snapshots[name]=snapshot
  self.rollback(name)
 def apply(self,name):
  p=self.p; commands={
   'freeze_inputs':['install','-d','-o','root','-g','root','-m','0700',str(self.paths(p['transaction_root']))],
   'install_packages':['apt-get','install','--yes','--no-install-recommends','--no-download',*(self.staged_archives or self.archives)],
   'create_identity':['sh','-eu','-c','groupadd --system --gid "$1" "$2"; useradd --system --uid "$3" --gid "$1" --home-dir "$4" --create-home --shell /usr/sbin/nologin "$2"','host-bootstrap',str(p['runner_gid']),p['runner_user'],str(p['runner_uid']),p['runner_home']],
   'configure_subids':['usermod','--add-subuids',f"{p['subuid_start']}-{p['subuid_start']+p['subid_count']-1}",'--add-subgids',f"{p['subgid_start']}-{p['subgid_start']+p['subid_count']-1}",p['runner_user']],
   'configure_runtime':['sh','-eu','-c','loginctl enable-linger "$1"; install -d -o "$1" -g "$1" -m 0700 "$2" "$3/.config/containers"','host-bootstrap',p['runner_user'],f"/run/user/{p['runner_uid']}",p['runner_home']],
   'stop_engine':['systemctl','stop',p['engine_service']], 'start_engine':['systemctl','start',p['engine_service']],
   'install_dropin':['sh','-eu','-c','install -d -m 0755 "$(dirname "$1")"; printf "%s" "$2" > "$1"; systemctl daemon-reload','host-bootstrap',f"/etc/systemd/system/{p['engine_service']}.d/10-claw-user.conf",f"[Service]\nUser={p['runner_user']}\nGroup={p['runner_group']}\nWorkingDirectory={p['runner_tree']}\nEnvironment=HOME={p['runner_home']}\nEnvironment=XDG_RUNTIME_DIR=/run/user/{p['runner_uid']}\n"],
   'load_oci':['runuser','-u',p['runner_user'],'--','env',f"HOME={p['runner_home']}",f"XDG_RUNTIME_DIR=/run/user/{p['runner_uid']}",'podman','load','--input',str(self.staged_oci or self.paths(p['transaction_root']+'/image.oci'))],
   'host_capability_precondition':['test','-f','/var/lib/mee-claw-host-deploy/D0-VERIFIED.json'],
   'runner_api_canary':['/usr/bin/python3.14','-B','/usr/local/libexec/mee-claw-host-deploy-lib/verify_claw_runner_api_canary.py','--policy','/usr/local/libexec/mee-claw-host-deploy-lib/host-bootstrap-policy.json'],
   'app_canary':['systemctl','show',p['app_service'],'--property=MainPID,User,ExecStart,WorkingDirectory,FragmentPath,ActiveState'],
  }
  if name=='snapshot_host':
   if self.credential_state:
    baseline_path=self.paths(p['transaction_root']+'/ownership.before.json'); raw=baseline_path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=self.snapshots[name]['metadata_sha256']:raise TxError('OWNERSHIP_SNAPSHOT_MISMATCH')
    self.credential_state.create(self.paths(p['runner_tree']),(p['runner_uid'],p['runner_gid']),json.loads(raw,object_pairs_hook=pairs))
  elif name=='create_identity':
   if not self.snapshots.get(name,{}).get('identity_existed'): self.r.run(commands[name])
  elif name=='configure_subids':
   before=self.snapshots[name]['probe'].split('SUBGID\n',1)
   if len(before)!=2 or not before[0].startswith('SUBUID\n'): raise TxError('SUBID_SNAPSHOT_INVALID')
   uid_before='\n'.join(before[0].removeprefix('SUBUID\n').splitlines())+'\n'; gid_before='\n'.join(before[1].splitlines())+'\n'
   uid_path=self.paths('/etc/subuid'); gid_path=self.paths('/etc/subgid'); uid_meta=regular_private(uid_path); gid_meta=regular_private(gid_path)
   atomic(self.paths(p['transaction_root']+'/subuid.before'),uid_before.encode()); atomic(self.paths(p['transaction_root']+'/subgid.before'),gid_before.encode())
   atomic_preserve(uid_path,add_subid_entry(uid_before,p['runner_user'],p['subuid_start'],p['subid_count']),uid_meta)
   atomic_preserve(gid_path,add_subid_entry(gid_before,p['runner_user'],p['subgid_start'],p['subid_count']),gid_meta)
  elif name=='configure_runtime':
   runtime=self.paths(f"/run/user/{p['runner_uid']}"); containers=self.paths(f"{p['runner_home']}/.config/containers")
   runtime.mkdir(parents=True,exist_ok=True); containers.mkdir(parents=True,exist_ok=True)
   os.chmod(runtime,0o700); os.chmod(containers,0o700)
   storage=f'[storage]\ndriver="overlay"\nrunroot="/run/user/{p["runner_uid"]}/containers"\ngraphroot="{p["runner_home"]}/storage"\n'.encode()
   atomic(containers/'storage.conf',storage)
   self.r.run(['loginctl','enable-linger',p['runner_user']]); self.r.run(['systemctl','start',f"user-runtime-dir@{p['runner_uid']}.service"]); self.r.run(['chown',f"{p['runner_user']}:{p['runner_group']}",str(self.paths(p['runner_home'])),str(runtime),str(containers)])
  elif name=='install_packages':
   baseline_rows=[x.split('\t') for x in self.snapshots.get(name,{}).get('probe','').splitlines() if x]
   closure_names={x['name'] for x in self.package_records}
   if any(row and row[0] in closure_names for row in baseline_rows): raise TxError('PACKAGE_BASELINE_MEMBER_PRESENT')
   for target,record in zip(self.staged_archives,self.package_records):
    if sha(target)!=record['sha256']: raise TxError('PACKAGE_ARCHIVE_SWAP')
   apt_closed=['apt-get','-o',f"Dir::Cache::archives={self.paths(p['transaction_root']+'/apt-cache')}",'-o','Dir::Cache::pkgcache=/dev/null','-o','Dir::Cache::srcpkgcache=/dev/null','-o','Acquire::Retries=0','install']
   plan=self.r.run([*apt_closed,'--simulate','--no-install-recommends','--no-download',*self.staged_archives]).stdout
   planned=[]
   for line in plan.splitlines():
    if line.startswith('Inst '):
     parts=line.split(); planned.append((parts[1].split(':',1)[0],parts[2].lstrip('('),parts[-1].strip('[])')))
   expected=sorted((x['name'],x['version'],x['architecture']) for x in self.package_records)
   if sorted(planned)!=expected: raise TxError('PACKAGE_PLAN_OUTSIDE_CLOSURE')
   self.r.run([*apt_closed,'--yes','--no-install-recommends','--no-download',*self.staged_archives])
  elif name=='transfer_ownership':
   if name not in self.snapshots: self.snapshot(name)
   baseline_path=self.paths(p['transaction_root']+'/ownership.before.json'); raw=baseline_path.read_bytes()
   if hashlib.sha256(raw).hexdigest()!=self.snapshots[name]['metadata_sha256']:raise TxError('OWNERSHIP_SNAPSHOT_MISMATCH')
   transfer_tree_ownership(self.paths(p['runner_tree']),p['runner_uid'],p['runner_gid'],json.loads(raw,object_pairs_hook=pairs))
  elif name=='load_oci':
   if self.staged_oci is None or sha(self.staged_oci)!=p['oci_archive_sha256']: raise TxError('OCI_ARCHIVE_SWAP')
   self.r.run(commands[name])
  elif name=='rootless_smoke':
   self.r.run(['runuser','-u',p['runner_user'],'--','env',f"HOME={p['runner_home']}",f"XDG_RUNTIME_DIR=/run/user/{p['runner_uid']}",'timeout','30','podman','run','--pull=never','--rm','--network=none','--cap-drop=ALL','--security-opt=no-new-privileges',p['image'],'-version'])
  elif name=='runner_api_canary':
   if self.token_reader is None: raise TxError('RUNNER_API_TOKEN_MISSING')
   token=self.token_reader()
   try: self.runner_api_projection=json.loads(self.r.run(commands[name],input=token).stdout,object_pairs_hook=pairs)
   finally: token=None
  elif name=='install_dropin':
   target=self.paths(f"/etc/systemd/system/{p['engine_service']}.d/10-claw-user.conf")
   content=f"[Service]\nUser={p['runner_user']}\nGroup={p['runner_group']}\nWorkingDirectory={p['runner_tree']}\nEnvironment=HOME={p['runner_home']}\nEnvironment=XDG_RUNTIME_DIR=/run/user/{p['runner_uid']}\n".encode()
   atomic(target,content); os.chmod(target,0o644); self.r.run(['systemctl','daemon-reload'])
  elif name in commands:self.r.run(commands[name])
  self.done.append(name)
 def verify(self,name):
  p=self.p; result={'operation':name,'status':'VERIFIED'}; checks={'freeze_inputs':['test','-d',str(self.paths(p['transaction_root']))],'snapshot_host':['test','-f',str(self.paths(p['transaction_root']+'/ownership.before.json'))],'create_identity':['getent','passwd',p['runner_user']]}
  if name in checks:self.r.run(checks[name])
  if name=='snapshot_host':
   inventory={'runner_metadata_sha256':self.snapshots[name]['metadata_sha256'],'app_projection':self.snapshots[name]['app_projection']}
   result['inventory_sha256']=hashlib.sha256(json.dumps(inventory,sort_keys=True,separators=(',',':')).encode()).hexdigest()
  elif name=='install_packages':
   for record in self.package_records:
    got=self.r.run(['dpkg-query','-W','-f=${Package}\t${Version}\t${Architecture}\n',record['name']]).stdout.strip().split('\t')
    if got!=[record['name'],record['version'],record['architecture']]: raise TxError('PACKAGE_INSTALL_MISMATCH')
  elif name=='configure_subids':
   for kind,start in (('subuid',p['subuid_start']),('subgid',p['subgid_start'])):
    lines=self.paths('/etc/'+kind).read_text().splitlines()
    if lines.count(f"{p['runner_user']}:{start}:{p['subid_count']}")!=1: raise TxError('SUBID_VERIFY')
  elif name=='configure_runtime':
   runtime=self.paths(f"/run/user/{p['runner_uid']}"); storage=self.paths(f"{p['runner_home']}/.config/containers/storage.conf")
   if not runtime.is_dir() or not storage.is_file() or (os.name=='posix' and stat.S_IMODE(runtime.stat().st_mode)!=0o700): raise TxError('RUNTIME_VERIFY')
   if not self.paths('/sys/fs/cgroup/cgroup.controllers').is_file(): raise TxError('CGROUP_V2_REQUIRED')
   self.r.run(['systemctl','is-active','--quiet',f"user-runtime-dir@{p['runner_uid']}.service"])
  elif name=='stop_engine':
   self.r.run(['systemctl','is-inactive','--quiet',p['engine_service']])
  elif name=='transfer_ownership':
   if not self.paths(f"{p['transaction_root']}/ownership.before.json").is_file(): raise TxError('OWNERSHIP_SNAPSHOT_MISSING')
   if self.credential_state:self.credential_state.verify(self.paths(p['runner_tree']),expect_post=True)
  elif name=='install_dropin':
   if not self.paths(f"/etc/systemd/system/{p['engine_service']}.d/10-claw-user.conf").is_file(): raise TxError('DROPIN_VERIFY')
  elif name=='load_oci':
   got=self.r.run(['runuser','-u',p['runner_user'],'--','env',f"HOME={p['runner_home']}",f"XDG_RUNTIME_DIR=/run/user/{p['runner_uid']}",'podman','image','inspect','--format={{.Digest}}',p['image']]).stdout.strip()
   if got!=p['image'].split('@',1)[1]: raise TxError('OCI_IMAGE_DIGEST')
  elif name=='rootless_smoke':
   left=self.r.run(['runuser','-u',p['runner_user'],'--','env',f"HOME={p['runner_home']}",f"XDG_RUNTIME_DIR=/run/user/{p['runner_uid']}",'podman','ps','-aq','--filter',f"ancestor={p['image']}"]).stdout.strip()
   if left: raise TxError('ROOTLESS_SMOKE_LEAK')
   result.update(remaining_containers=0,network='none',pull='never')
  elif name=='host_capability_precondition':
   receipt_path=self.paths('/var/lib/mee-claw-host-deploy/D0-VERIFIED.json');self.r.run(['test','-f',str(receipt_path)])
   result['d0_receipt_sha256']=sha(receipt_path)
  elif name=='runner_api_canary':
   projection=getattr(self,'runner_api_projection',None)
   required={'repository','runner_id','runner_name','status','labels','matching_count','total_count'}
   if not isinstance(projection,dict) or set(projection)!=required: raise TxError('RUNNER_API_PROJECTION_MISSING')
   result['runner_api']=projection
  elif name=='app_canary':
   now=self.r.run(['systemctl','show',p['app_service'],'--property=MainPID,User,ExecStart,WorkingDirectory,FragmentPath,ActiveState']).stdout
   result['unit']=unit_projection(now)
   baseline=self.snapshots.get('snapshot_host',{}).get('app_projection')
   if baseline is None: raise TxError('APP_BASELINE_MISSING')
   if now!=baseline: raise TxError('APP_CANARY_DRIFT')
  elif name=='start_engine':
   self.r.run(['systemctl','is-active','--quiet',self.p['engine_service']])
   projection=self.r.run(['systemctl','show',p['engine_service'],'--property=User,Group,ExecStart,WorkingDirectory,FragmentPath,ActiveState']).stdout
   required=(f"User={p['runner_user']}",f"Group={p['runner_group']}",f"WorkingDirectory={p['runner_tree']}",'ActiveState=active')
   if not all(x in projection for x in required): raise TxError('ENGINE_UNIT_MISMATCH')
   result['unit_projection']=projection
  result['result_sha256']=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(',',':')).encode()).hexdigest()
  return result
 def rollback(self,name):
  p=self.p
  if name=='install_packages':
   baseline=self.snapshots.get(name,{}).get('probe',''); rows=[x.split('\t') for x in baseline.splitlines() if x]
   if any(len(x)!=4 or len(x[3])!=3 for x in rows): raise TxError('PACKAGE_BASELINE_INVALID')
   before={x[0] for x in rows}
   names=[x['name'] for x in self.package_records] if self.package_records else [Path(x).name.split('_',1)[0] for x in self.archives]
   added=[x for x in names if x not in before]
   if added:
    simulation=self.r.run(['apt-get','remove','--simulate',*added])
    removed=[line.split()[1].split(':',1)[0] for line in getattr(simulation,'stdout','').splitlines() if line.startswith('Remv ') and len(line.split())>1]
    if set(removed)-set(added): raise TxError('ROLLBACK_DEPENDENCY_DRIFT')
    self.r.run(['apt-get','remove','--yes','--no-download',*added])
   current=self.r.run(['dpkg-query','-W','-f=${Package}\t${Version}\t${Architecture}\t${db:Status-Abbrev}\n']).stdout
   selections=self.r.run(['dpkg','--get-selections']).stdout
   if current!=baseline or selections!=self.snapshots.get(name,{}).get('selections',''): raise TxError('ROLLBACK_PACKAGE_STATE_DRIFT')
   return
  if name=='create_identity':
   if not self.snapshots.get(name,{}).get('identity_existed'): self.r.run(['userdel',p['runner_user']]); self.r.run(['groupdel',p['runner_group']])
   return
  if name=='configure_subids':
   failures=[]
   for source,target in ((self.paths(f"{p['transaction_root']}/subuid.before"),self.paths('/etc/subuid')),(self.paths(f"{p['transaction_root']}/subgid.before"),self.paths('/etc/subgid'))):
    try:
     meta=self.snapshots.get(name,{}).get(target.name+'_metadata')
     if not meta: raise TxError('SUBID_METADATA_MISSING')
     regular_private(target); atomic(target,source.read_bytes()); os.chmod(target,meta['mode'])
     if os.name=='posix': os.chown(target,meta['uid'],meta['gid'])
    except BaseException as e: failures.append(str(e))
   if failures: raise TxError('SUBID_RESTORE_FAILED:'+';'.join(failures))
   return
  if name=='configure_runtime':
   snap=self.snapshots.get(name,{}); runtime=self.paths(f"/run/user/{p['runner_uid']}"); containers=self.paths(f"{p['runner_home']}/.config/containers"); storage=containers/'storage.conf'
   failures=[]
   try:
    if snap.get('storage_existed'): atomic(storage,snap.get('storage_content','').encode())
    elif storage.exists(): storage.unlink()
   except BaseException as e: failures.append(str(e))
   if not snap.get('containers_existed'):
    try: containers.rmdir()
    except FileNotFoundError: pass
    except OSError as e: failures.append('RUNTIME_FOREIGN_RESOURCE:'+str(e))
   if not snap.get('runtime_existed'):
    try: runtime.rmdir()
    except FileNotFoundError: pass
    except OSError as e: failures.append('RUNTIME_FOREIGN_RESOURCE:'+str(e))
   try:
    if not snap.get('runtime_unit_was_active'): self.r.run(['systemctl','stop',f"user-runtime-dir@{p['runner_uid']}.service"])
   except BaseException as e: failures.append(str(e))
   try:
    if not snap.get('linger_was_enabled'): self.r.run(['loginctl','disable-linger',p['runner_user']])
   except BaseException as e: failures.append(str(e))
   try:
    home=self.paths(p['runner_home']); config=home/'.config'; projections=((runtime,'runtime_projection'),(storage,'storage_projection'),(containers,'containers_projection'),(config,'config_projection'),(home,'home_projection'))
    if all(key in snap for _,key in projections):
     for path,key in projections: restore_projection(path,snap[key])
     if any(path_projection(path,content=(key=='storage_projection'))!=snap[key] for path,key in projections): failures.append('RUNTIME_FINAL_EQUALITY')
   except BaseException as e: failures.append(str(e))
   if failures: raise TxError('RUNTIME_FOREIGN_RESOURCE:'+';'.join(failures))
   return
  if name=='stop_engine':
   if self.snapshots.get(name,{}).get('was_active'): self.r.run(['systemctl','start',p['engine_service']])
   return
  if name=='transfer_ownership':
   metadata_path=self.paths(p['transaction_root']+'/ownership.before.json'); raw=metadata_path.read_bytes()
   expected=self.snapshots.get(name,{}).get('metadata_sha256') or self.snapshots.get('snapshot_host',{}).get('metadata_sha256')
   if not expected or hashlib.sha256(raw).hexdigest()!=expected: raise TxError('OWNERSHIP_SNAPSHOT_MISMATCH')
   restore_tree_metadata(self.paths(p['runner_tree']),json.loads(raw,object_pairs_hook=pairs))
   if self.credential_state:self.credential_state.verify(self.paths(p['runner_tree']),expect_post=False)
   return
  if name=='install_dropin':
   target=self.paths(f"/etc/systemd/system/{p['engine_service']}.d/10-claw-user.conf"); previous=self.snapshots.get(name,{}).get('previous_content','')
   if self.snapshots.get(name,{}).get('target_existed'): atomic(target,previous.encode()); os.chmod(target,0o644)
   elif target.exists(): target.unlink()
   self.r.run(['systemctl','daemon-reload']); return
  if name=='start_engine':
   if not self.snapshots.get(name,{}).get('was_active'): self.r.run(['systemctl','stop',p['engine_service']])
   return
  if name=='load_oci':
   if not self.snapshots.get(name,{}).get('image_existed'):
    self.r.run(['runuser','-u',p['runner_user'],'--','env',f"HOME={p['runner_home']}",f"XDG_RUNTIME_DIR=/run/user/{p['runner_uid']}",'podman','image','rm','--force',p['image']])
   return
  p=self.p; commands={'freeze_inputs':['true'],'snapshot_host':['true'],'install_packages':['apt-get','remove','--yes','--no-download'],'create_identity':['userdel',p['runner_user']],'configure_subids':['cp',f"{p['transaction_root']}/subuid.before",'/etc/subuid'],'configure_runtime':['loginctl','disable-linger',p['runner_user']],'stop_engine':['systemctl','start',p['engine_service']],'start_engine':['systemctl','stop',p['engine_service']],'transfer_ownership':['setfacl',f"--restore={p['transaction_root']}/ownership.acl"],'install_dropin':['rm','-f',f"/etc/systemd/system/{p['engine_service']}.d/10-claw-user.conf"],'load_oci':['runuser','-u',p['runner_user'],'--','env',f"HOME={p['runner_home']}",f"XDG_RUNTIME_DIR=/run/user/{p['runner_uid']}",'podman','image','rm','--force',p['image']],'rootless_smoke':['true'],'host_capability_precondition':['true'],'runner_api_canary':['true'],'app_canary':['true']}
  if name in commands:self.r.run(commands[name])
 def final_verify(self):
  self.r.run(['systemctl','is-active','--quiet',self.p['engine_service']]); self.r.run(['systemctl','is-active','--quiet',self.p['app_service']])
  if self.credential_state:self.credential_state.verify(self.paths(self.p['runner_tree']),expect_post=True)
 def terminal_close(self,status):
  if self.credential_state:self.credential_state.close(status)
@dataclass(frozen=True)
class Operation: name:str
OPERATIONS=tuple(Operation(x) for x in ('freeze_inputs','snapshot_host','install_packages','create_identity','configure_subids','configure_runtime','stop_engine','transfer_ownership','install_dropin','load_oci','rootless_smoke','host_capability_precondition','start_engine','runner_api_canary','app_canary'))
@dataclass(frozen=True)
class PendingFinalize:
 transaction_id:str
 deadline:Deadline
def _finalize_projection(value):
 fields={'repository','runner_id','runner_name','status','labels','matching_count','total_count'}
 if not isinstance(value,dict) or set(value)!=fields: raise TxError('FINALIZE_PROJECTION')
 if value['repository']!='Dimkox/multi-exchange-engine' or not isinstance(value['runner_id'],int) or isinstance(value['runner_id'],bool) or value['runner_id']<=0: raise TxError('FINALIZE_PROJECTION')
 if value['runner_name']!='claw-engine-runner' or value['status']!='online' or not isinstance(value['matching_count'],int) or isinstance(value['matching_count'],bool) or value['matching_count']!=1 or not isinstance(value['total_count'],int) or isinstance(value['total_count'],bool) or value['total_count']<1: raise TxError('FINALIZE_PROJECTION')
 labels=value['labels']
 if not isinstance(labels,list) or not all(isinstance(x,str) and re.fullmatch(r'[A-Za-z0-9._-]{1,64}',x) for x in labels) or labels!=sorted(labels) or len(labels)!=len(set(labels)) or not {'self-hosted','claw','claw-engine-runner'}<=set(labels): raise TxError('FINALIZE_PROJECTION')
 return dict(value)
def is_terminal_rolled_back_journal(value):
 if value.get('schema_version')!='claw-host-journal-v1' or value.get('phase')!='ROLLED_BACK' or value.get('status')!='ROLLED_BACK' or value.get('applied')!=[] or value.get('current') is not None or value.get('snapshot') is not None:return False
 ordered=[op.name for op in OPERATIONS];history=value.get('history');snapshots=value.get('snapshots');results=value.get('verified_results')
 if not isinstance(history,list) or not history or history[0]!='PREPARED' or history[-1]!='ROLLED_BACK':return False
 cursor=0;pending=None;post='operations';rollback=False;blocked=False;terminal=False;attempted=set();completed=set()
 for phase in history[1:]:
  if not isinstance(phase,str):return False
  if terminal:return False
  if phase=='ROLLING_BACK':
   rollback=True;blocked=False;pending=None;continue
  if phase=='ROLLBACK_BLOCKED':
   if not rollback or not (attempted or completed):return False
   rollback=False;blocked=True;continue
  if phase=='ROLLED_BACK':
   if not rollback:return False
   rollback=False;terminal=True;continue
  if rollback or blocked:return False
  if pending is not None:
   if phase!=f'APPLIED({pending})':return False
   completed.add(pending);pending=None;cursor+=1;continue
  if cursor<len(ordered):
   if phase!=f'APPLYING({ordered[cursor]})':return False
   pending=ordered[cursor];attempted.add(pending);continue
  transitions={'operations':('VERIFYING','verifying'),'verifying':('HOST_APPLIED_PENDING_FINALIZE','pending_finalize'),'pending_finalize':('FINALIZING','finalizing'),'finalizing':('VERIFIED','verified'),'verified':('COMMITTED','committed')}
  expected,next_post=transitions.get(post,(None,None))
  if phase!=expected:return False
  post=next_post
 if not terminal or rollback or blocked or pending is not None:return False
 if not isinstance(snapshots,dict) or not isinstance(results,dict) or set(snapshots)!=attempted or set(results)!=completed:return False
 if any(name not in attempted or not isinstance(snapshot,dict) or snapshot.get('operation')!=name for name,snapshot in snapshots.items()):return False
 if any(name not in completed or name not in snapshots or not isinstance(result,dict) or result.get('operation')!=name or result.get('status')!='VERIFIED' for name,result in results.items()):return False
 try:
  if post in {'pending_finalize','finalizing','verified','committed'}:Deadline.from_dict(value.get('deadline'))
  elif value.get('deadline') is not None:return False
  if post in {'finalizing','verified','committed'}:_finalize_projection(value.get('finalize_projection'))
  elif value.get('finalize_projection') is not None:return False
 except TxError:return False
 return True
def execute(backend,journal,deadline=None):
 applied=[]; current=None
 try:
  for op in OPERATIONS:
   backend.prepare(op.name); snap=backend.snapshot(op.name); current=op.name; journal.record('APPLYING('+op.name+')',applied,current=op.name,snapshot=snap); backend.apply(op.name); result=backend.verify(op.name) or {'status':'VERIFIED','operation':op.name}; applied.append(op.name); journal.record('APPLIED('+op.name+')',applied,current=op.name,verified_result=result); current=None
  journal.record('VERIFYING',applied); backend.final_verify(); deadline=deadline or new_deadline(); journal.record('HOST_APPLIED_PENDING_FINALIZE',applied,status='OPEN',deadline=deadline.as_dict()); return PendingFinalize(journal.path.stem,deadline)
 except BaseException:
  journal.record('ROLLING_BACK',applied,current=current,snapshot=journal.value.get('snapshot'))
  failures=[]
  if current is not None:
   try: backend.rollback(current)
   except BaseException as e: failures.append((current,str(e)))
  for name in reversed(applied):
   try: backend.rollback(name)
   except BaseException as e: failures.append((name,str(e)))
  if failures: journal.record('ROLLBACK_BLOCKED',applied,status='OPEN',snapshot={'failures':failures})
  else:
   if hasattr(backend,'terminal_close'): backend.terminal_close('ROLLED_BACK')
   journal.record('ROLLED_BACK',[],status='ROLLED_BACK')
  raise
def finalize(backend,journal,authenticated_projection,now_boot_id=None,now_monotonic_ns=None):
 phase=journal.value.get('phase')
 if phase not in {'HOST_APPLIED_PENDING_FINALIZE','FINALIZING','VERIFIED'} or journal.value.get('status')!='OPEN': raise TxError('FINALIZE_STATE')
 projection=_finalize_projection(authenticated_projection); deadline=Deadline.from_dict(journal.value.get('deadline'))
 boot=now_boot_id if now_boot_id is not None else current_boot_id(); now=now_monotonic_ns if now_monotonic_ns is not None else time.monotonic_ns()
 if boot!=deadline.boot_id or now>=deadline.monotonic_deadline_ns: raise TxError('FINALIZE_DEADLINE')
 applied=list(journal.value['applied'])
 prior=journal.value.get('verified_results',{}).get('runner_api_canary',{}).get('runner_api')
 stable_fields=('repository','runner_id','runner_name','status','labels','matching_count')
 if not isinstance(prior,dict) or any(prior.get(field)!=projection[field] for field in stable_fields): raise TxError('FINALIZE_PROJECTION_DRIFT')
 prior_finalize=journal.value.get('finalize_projection')
 if phase in {'FINALIZING','VERIFIED'} and (not isinstance(prior_finalize,dict) or any(prior_finalize.get(field)!=projection[field] for field in stable_fields)): raise TxError('FINALIZE_PROJECTION_DRIFT')
 if hasattr(backend,'snapshots'):backend.snapshots.update(journal.value.get('snapshots',{}))
 if phase=='HOST_APPLIED_PENDING_FINALIZE': journal.record('FINALIZING',applied,finalize_projection=projection)
 if phase!='VERIFIED':
  backend.final_verify()
  journal.record('VERIFIED',applied)
 journal.record('COMMITTED',applied,status='COMMITTED')
 return projection
def deadline_due(journal,now_boot_id=None,now_monotonic_ns=None):
 if journal.value.get('phase') not in {'HOST_APPLIED_PENDING_FINALIZE','FINALIZING','VERIFIED'} or journal.value.get('status')!='OPEN': raise TxError('DEADLINE_STATE')
 deadline=Deadline.from_dict(journal.value.get('deadline')); boot=now_boot_id if now_boot_id is not None else current_boot_id(); now=now_monotonic_ns if now_monotonic_ns is not None else time.monotonic_ns()
 return boot!=deadline.boot_id or now>=deadline.monotonic_deadline_ns
def reconcile_deadline(backend,journal,now_boot_id=None,now_monotonic_ns=None):
 if not deadline_due(journal,now_boot_id,now_monotonic_ns):return False
 recover(backend,journal);return True
def recover(backend,journal):
 applied=list(journal.value['applied'])
 if hasattr(backend,'snapshots'): backend.snapshots.update(journal.value.get('snapshots',{}))
 current=journal.value.get('current')
 failures=[]
 journal.record('ROLLING_BACK',applied,current=current,snapshot=journal.value.get('snapshot'))
 if current is not None:
  try: backend.reconcile(current,journal.value.get('snapshot'))
  except BaseException as e: failures.append((current,str(e)))
 for name in reversed(applied):
  try: backend.rollback(name)
  except BaseException as e: failures.append((name,str(e)))
 if failures: journal.record('ROLLBACK_BLOCKED',applied,status='OPEN',snapshot={'failures':failures}); raise TxError('ROLLBACK_BLOCKED')
 if hasattr(backend,'terminal_close'): backend.terminal_close('ROLLED_BACK')
 journal.record('ROLLED_BACK',[],status='ROLLED_BACK')
def receipt(policy,closure,oci,journal=None,controller_sha=None):
 j=json.loads(Path(journal).read_text(),object_pairs_hook=pairs) if journal else None
 snapshots=j.get('verified_results',{}) if j else {}
 projection_names=('freeze_inputs','snapshot_host','install_packages','create_identity','configure_subids','configure_runtime','stop_engine','transfer_ownership','install_dropin','load_oci','rootless_smoke','host_capability_precondition','start_engine','runner_api_canary','app_canary')
 if j is None or j.get('phase')!='COMMITTED' or j.get('status')!='COMMITTED' or not isinstance(j.get('finalize_projection'),dict): raise TxError('HOST_JOURNAL_NOT_COMMITTED')
 if set(snapshots)!=set(projection_names) or any(x.get('operation')!=name or x.get('status')!='VERIFIED' for name,x in snapshots.items()): raise TxError('HOST_VERIFIED_RESULTS_INCOMPLETE')
 projections={name:hashlib.sha256(json.dumps(snapshots.get(name,{}),sort_keys=True,separators=(',',':')).encode()).hexdigest() for name in projection_names}
 return {'schema_version':'claw-host-bootstrap-receipt-v1','transaction_id':Path(journal).stem if journal else 'unbound','controller_sha':controller_sha or '0'*40,'policy_sha256':sha(policy),'closure_sha256':sha(closure),'oci_archive_sha256':sha(oci),'journal_sha256':sha(journal) if journal else '0'*64,'host_inventory_sha256':snapshots['snapshot_host']['inventory_sha256'],'runner_api':_finalize_projection(j['finalize_projection']),'operation_set_sha256':hashlib.sha256(('\n'.join(x.name for x in OPERATIONS)+'\n').encode()).hexdigest(),'projections':projections,'rollback_capability':'ROOT_JOURNAL_AND_CREDENTIAL_HMAC_RETAINED','status':'VERIFIED'}
def main(argv=None,token_reader=None):
 p=argparse.ArgumentParser(); p.add_argument('--journal',required=True); p.add_argument('--fake',action='store_true'); p.add_argument('--failpoint',default=''); p.add_argument('--policy'); p.add_argument('--closure'); p.add_argument('--debs'); p.add_argument('--oci-archive'); p.add_argument('--oci-layout'); p.add_argument('--oci-evidence-receipt'); p.add_argument('--oci-evidence-sidecar'); p.add_argument('--receipt'); p.add_argument('--controller-sha'); p.add_argument('--deadline-seconds',type=int); mode=p.add_mutually_exclusive_group(); mode.add_argument('--resume',action='store_true'); mode.add_argument('--rollback',action='store_true'); a=p.parse_args(argv)
 try:
  if a.fake:
   backend=FakeBackend(a.failpoint)
   if a.resume: recover(backend,Journal.resume(a.journal))
   elif a.rollback: recover(backend,Journal.for_rollback(a.journal))
   else: execute(backend,Journal(a.journal))
   return 0
  if not all((a.policy,a.closure,a.receipt)): raise TxError('REAL_ARGUMENTS_REQUIRED')
  policy=json.loads(Path(a.policy).read_text(),object_pairs_hook=pairs); closure=json.loads(Path(a.closure).read_text(),object_pairs_hook=pairs)
  if policy.get('oci_archive_sha256')=='0'*64: raise TxError('OCI_ARCHIVE_UNRESOLVED')
  recovery=a.resume or a.rollback
  if not recovery:
   if not all((a.debs,a.oci_archive,a.oci_layout,a.oci_evidence_receipt,a.oci_evidence_sidecar,a.controller_sha,a.deadline_seconds)):raise TxError('APPLY_EVIDENCE_REQUIRED')
   try:
    from scripts.verify_oci_evidence_approval import main as verify_oci
   except ModuleNotFoundError:
    from verify_oci_evidence_approval import main as verify_oci
   approval_path=Path(policy['oci_evidence_approval'])
   if not approval_path.is_absolute():approval_path=Path(a.policy).parent/approval_path.name
   if verify_oci(['--policy',a.policy,'--approval',str(approval_path),'--approval-policy-path','ci/claw/oci-evidence-approval.json','--receipt',a.oci_evidence_receipt,'--receipt-sha256',a.oci_evidence_sidecar,'--archive',a.oci_archive,'--layout',a.oci_layout,'--closure',a.closure,'--origin','https://github.com/Dimkox/multi-exchange-engine.git'])!=0:raise TxError('OCI_EVIDENCE_INVALID')
  durable=Path(policy['transaction_root']); records=sorted(closure['packages'],key=lambda x:x['name']); archives=sorted((durable/'packages' if recovery else Path(a.debs)).glob('*.deb'));oci=str(durable/'image.oci') if recovery else a.oci_archive
  effective_token_reader=token_reader or (lambda:sys.stdin.buffer.read(4097).decode())
  binding_path=durable/'credential-binding.json';policy_sha256=sha(a.policy)
  if not recovery and path_present_no_follow(binding_path):release_completed_rollback_binding(durable,binding_path,policy_sha256)
  if Path(a.journal).parent!=durable or not re.fullmatch(r'[0-9a-f]{32}\.json',Path(a.journal).name):raise TxError('JOURNAL_IDENTITY')
  journal=Journal.load_private(durable,a.journal,('OPEN',)) if a.resume else Journal.load_private(durable,a.journal,('OPEN','COMMITTED')) if a.rollback else Journal(a.journal)
  if recovery:
   fresh_prepared=is_fresh_prepared_journal(journal.value)
   if path_present_no_follow(binding_path) and fresh_prepared:
    existing,_,_=read_private_credential_binding(durable,binding_path)
    if existing.get('transaction_id')!=Path(a.journal).stem:release_completed_rollback_binding(durable,binding_path,policy_sha256)
   if not path_present_no_follow(binding_path) and fresh_prepared:
    if a.rollback:journal.assert_private_identity();durable_unlink(a.journal);return 0
    raise TxError('INITIALIZATION_INCOMPLETE_USE_ROLLBACK')
   binding,_,_=read_private_credential_binding(durable,binding_path)
   if binding['transaction_id']!=Path(a.journal).stem or binding['policy_sha256']!=sha(a.policy) or not __import__('re').fullmatch(r'[0-9a-f]{40}',binding['controller_sha']):raise TxError('RECOVERY_BINDING_INVALID')
   if fresh_prepared:
    state=durable/'credential-state';key=state/'key';mapping=state/'map'
    state_present=path_present_no_follow(state);key_present=path_present_no_follow(key);mapping_present=path_present_no_follow(mapping)
    if key_present!=mapping_present:raise TxError('CREDENTIAL_STATE_PARTIAL')
    if not key_present:
     if a.rollback:
      if state_present:durable_rmdir_empty_private(state)
      journal.assert_private_identity();durable_unlink(binding_path);durable_unlink(a.journal);return 0
     raise TxError('INITIALIZATION_INCOMPLETE_USE_ROLLBACK')
  else:
   binding={'transaction_id':Path(a.journal).stem,'controller_sha':a.controller_sha,'policy_sha256':policy_sha256};create_credential_binding(binding_path,binding)
  backend=RealBackend(policy,archives=archives,package_records=records,oci_archive=oci,token_reader=effective_token_reader,credential_binding=binding)
  if a.resume or a.rollback: recover(backend,journal); return 0
  execute(backend,journal,deadline=new_deadline(a.deadline_seconds))
  # Apply deliberately stops at HOST_APPLIED_PENDING_FINALIZE.  The committed
  # receipt is written only by the later authenticated local finalize path.
  return 0
 except (OSError,ValueError,TxError): return 2
if __name__=='__main__': raise SystemExit(main())
