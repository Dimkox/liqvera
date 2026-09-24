#!/usr/bin/env python3
import argparse,hashlib,json,os,subprocess,sys,tempfile,time
from pathlib import Path
if __package__ in (None,''):sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.oci_evidence_v2 import acquire_once,compare_acquisitions,verify_docker_tar,verify_oci_layout,verify_receipt
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def atomic(path,data):
 path=Path(path);fd,name=tempfile.mkstemp(prefix='.'+path.name+'.',dir=path.parent)
 try:
  view=memoryview(data)
  while view:
   count=os.write(fd,view)
   if count<=0:raise OSError('SHORT_WRITE')
   view=view[count:]
  os.fsync(fd);os.close(fd);fd=-1;os.replace(name,path)
  if os.name=='posix':
   directory=os.open(path.parent,os.O_RDONLY);os.fsync(directory);os.close(directory)
 finally:
  if fd>=0:os.close(fd)
  try:os.unlink(name)
  except FileNotFoundError:pass
def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--layout',required=True);p.add_argument('--artifact-root',required=True);p.add_argument('--policy',required=True);p.add_argument('--closure',required=True);p.add_argument('--output',required=True);a=p.parse_args(argv)
 archive=Path(a.archive).resolve(strict=True);root=Path(a.artifact_root).resolve(strict=True);output=Path(a.output).resolve()
 if root not in archive.parents or output.parent!=root or archive.name!='actionlint-linux-amd64.tar':return 2
 source='docker.io/rhysd/actionlint@sha256:9d36088643581e728c969f35141f88139fec77280b2be23c1f66f8e40e1025e7'; repo='rhysd/actionlint'; dg=source.rsplit('@',1)[1]
 first=acquire_once(repo,dg);second=acquire_once(repo,dg);dual=compare_acquisitions(first,second);local=verify_docker_tar(archive);layout=verify_oci_layout(a.layout)
 command=['python','-B','scripts/build_oci_evidence_v2.py','--archive',archive.name,'--layout',Path(a.layout).name,'--artifact-root','<ARTIFACT_ROOT>','--policy',a.policy,'--closure',a.closure,'--output',output.name]
 receipt={'schema_version':'oci-evidence-v2','authority':'NONE','status':'LOCAL_OCI_EVIDENCE_ONLY','not_host_receipt':True,'created_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'source_image':source,'repository':{'origin':subprocess.check_output(['git','remote','get-url','origin'],text=True).strip(),'commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'tree':subprocess.check_output(['git','rev-parse','HEAD^{tree}'],text=True).strip()},'inputs':{'policy_sha256':sha(a.policy),'closure_sha256':sha(a.closure),'archive_name':archive.name,'resolved_path_diagnostic':str(archive),'archive_post_sha256':sha(archive)},'command':{'argv':command,'sha256':hashlib.sha256(json.dumps(command,separators=(',',':')).encode()).hexdigest()},'tool':{'python':sys.version.split()[0],'verifier_source_sha256':sha('scripts/oci_evidence_v2.py'),'builder_source_sha256':sha(__file__),'independent_verifier_sha256':sha('scripts/verify_oci_evidence_v2.py'),'schema_sha256':sha('schemas/oci-evidence-v2.schema.json')},'acquisitions':[first,second],'dual_acquisition':dual,'local_verification':local,'oci_layout_verification':layout,'limitations':['PENDING_UNTIL_ROOTLESS_HOST_SMOKE','NOT_A_HOST_RECEIPT','ZERO_SENTINEL_UNCHANGED'],'readiness':'NOT_READY_FOR_HOST_APPLY'}
 expected={'origin':receipt['repository']['origin'],'commit':receipt['repository']['commit'],'tree':receipt['repository']['tree'],'source_image':source}
 verify_receipt(receipt,archive,a.layout,a.policy,a.closure,expected);data=(json.dumps(receipt,sort_keys=True,separators=(',',':'))+'\n').encode();atomic(output,data);atomic(output.with_suffix(output.suffix+'.sha256'),(hashlib.sha256(data).hexdigest()+'  '+output.name+'\n').encode());return 0
if __name__=='__main__':raise SystemExit(main())
