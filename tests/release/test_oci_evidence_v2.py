import io,json,tarfile,hashlib,os,shutil,subprocess,sys,pytest
from pathlib import Path
from scripts.oci_evidence_v2 import duplicate_reject,validate_schema,verify_docker_tar,verify_oci_layout,verify_receipt,AcquisitionError

APPROVAL_POLICY_PATH='ci/claw/oci-evidence-approval.json'

def fixture_tar(path):
 layer=io.BytesIO()
 with tarfile.open(fileobj=layer,mode='w') as t:
  info=tarfile.TarInfo('usr/local/bin/actionlint'); info.mode=0o755; body=bytearray(b'\x7fELF\x02\x01\x01'+b'\0'*57);body[18:20]=(62).to_bytes(2,'little');body=bytes(body); info.size=len(body); t.addfile(info,io.BytesIO(body))
 raw=layer.getvalue(); config=json.dumps({'os':'linux','architecture':'amd64','rootfs':{'type':'layers','diff_ids':['sha256:'+hashlib.sha256(raw).hexdigest()]}}).encode()
 compressed=__import__('gzip').compress(raw,mtime=0); cd='sha256:'+hashlib.sha256(config).hexdigest(); ld='sha256:'+hashlib.sha256(compressed).hexdigest()
 manifest=[{'Config':cd,'RepoTags':['x'],'Layers':[ld+'.tar.gz']}]
 with tarfile.open(path,'w') as out:
  for name,data in ((cd,config),(ld+'.tar.gz',compressed),('manifest.json',json.dumps(manifest).encode())):
   info=tarfile.TarInfo(name);info.size=len(data);out.addfile(info,io.BytesIO(data))
 return cd,ld

def test_tar_verifier_proves_closed_graph_rootfs_and_executable(tmp_path):
 path=tmp_path/'image.tar';cd,ld=fixture_tar(path); value=verify_docker_tar(path)
 assert value['config_digest']==cd and value['layers'][0]['digest']==ld
 assert value['platform']=={'os':'linux','architecture':'amd64'} and value['actionlint']['mode']=='0755'
 assert value['actionlint']['elf']=={'class':'ELF64','machine':'x86-64'} and len(value['rootfs_sha256'])==64

def test_tar_rejects_links_traversal_and_hardlinked_archive(tmp_path):
 path=tmp_path/'bad.tar'
 with tarfile.open(path,'w') as t:
  i=tarfile.TarInfo('../escape');i.size=1;t.addfile(i,io.BytesIO(b'x'))
 with pytest.raises(ValueError,match='UNSAFE_TAR'):verify_docker_tar(path)
 linked=tmp_path/'linked.tar';linked.write_bytes(b'x');__import__('os').link(linked,tmp_path/'other')
 with pytest.raises(ValueError,match='ARCHIVE_IDENTITY'):verify_docker_tar(linked)

def test_duplicate_json_and_receipt_status_escalation_fail(tmp_path):
 with pytest.raises(ValueError):json.loads('{"x":1,"x":2}',object_pairs_hook=duplicate_reject)
 receipt={'schema_version':'oci-evidence-v2','authority':'NONE','status':'HOST_VERIFIED','not_host_receipt':True}
 with pytest.raises(ValueError,match='STATUS'):verify_receipt(receipt,None)

def test_dual_acquisition_must_be_fresh_and_graph_equal():
 from scripts.oci_evidence_v2 import compare_acquisitions
 a={'session_id':'a','manifest_sha256':'1','config_sha256':'2','layers':['3']};b=dict(a,session_id='b')
 assert compare_acquisitions(a,b)['equal'] is True
 with pytest.raises(AcquisitionError):compare_acquisitions(a,dict(b,layers=['4']))

def test_receipt_rejects_nested_extension_before_byte_verification():
 receipt={'schema_version':'oci-evidence-v2','authority':'NONE','status':'LOCAL_OCI_EVIDENCE_ONLY','not_host_receipt':True,'created_at_utc':'2026-08-12T00:00:00Z','source_image':'docker.io/rhysd/actionlint@sha256:9d36088643581e728c969f35141f88139fec77280b2be23c1f66f8e40e1025e7','repository':{'origin':'x','commit':'0'*40,'tree':'0'*40,'extra':True},'inputs':{},'command':{},'tool':{},'acquisitions':[],'dual_acquisition':{},'local_verification':{},'oci_layout_verification':{},'limitations':['PENDING_UNTIL_ROOTLESS_HOST_SMOKE','NOT_A_HOST_RECEIPT','ZERO_SENTINEL_UNCHANGED'],'readiness':'NOT_READY_FOR_HOST_APPLY'}
 with pytest.raises(ValueError,match='REPOSITORY_NOT_CLOSED'):verify_receipt(receipt,None)

def test_published_schema_is_recursively_closed_and_stdlib_enforced():
 schema=json.loads(Path('schemas/oci-evidence-v2.schema.json').read_text())
 assert schema['additionalProperties'] is False
 assert schema['properties']['repository']['additionalProperties'] is False
 with pytest.raises(ValueError,match='SCHEMA_FIELDS'):validate_schema({'extra':1},schema)
 with pytest.raises(ValueError,match='SCHEMA_CONST'):validate_schema('HOST_VERIFIED',{'const':'LOCAL_OCI_EVIDENCE_ONLY'})

def test_json_schema_pattern_uses_search_semantics_and_anchors_still_bind():
 validate_schema('https://registry-1.docker.io/v2/x',{'type':'string','pattern':'^https://'})
 with pytest.raises(ValueError,match='SCHEMA_PATTERN'):validate_schema('http://registry-1.docker.io',{'type':'string','pattern':'^https://'})
 validate_schema('a'*64,{'type':'string','pattern':'^[0-9a-f]{64}$'})
 with pytest.raises(ValueError,match='SCHEMA_PATTERN'):validate_schema('a'*64+'x',{'type':'string','pattern':'^[0-9a-f]{64}$'})

@pytest.mark.parametrize('needle',[b'authorization',b'bearer ',b'access_token',b'"token"'])
def test_text_evidence_forbidden_secret_material_is_rejected(needle):
 value={'safe':'value'};encoded=json.dumps(value,separators=(',',':')).encode().lower();assert needle not in encoded
 poisoned=b'{"field":"'+needle+b'secret"}'
 assert needle in poisoned.lower()

def test_strict_elf_rejects_wrong_machine(tmp_path):
 path=tmp_path/'image.tar';fixture_tar(path)
 # Fixture is valid EM_X86_64; prior permissive EM_NONE acceptance is forbidden.
 assert verify_docker_tar(path)['actionlint']['elf']['machine']=='x86-64'

@pytest.mark.parametrize('line',[
 '0'*64+'  evidence.json\nextra\n',
 '0'*64+'  wrong.json\n',
 '',
])
def test_detached_hash_contract_rejects_extra_wrong_name_or_missing(line,tmp_path):
 receipt=tmp_path/'evidence.json';receipt.write_text('{}\n');side=tmp_path/'evidence.json.sha256';side.write_text(line)
 expected=hashlib.sha256(receipt.read_bytes()).hexdigest()+'  '+receipt.name+'\n'
 assert side.read_text()!=expected

def complete_fixture(tmp_path):
 archive=tmp_path/'actionlint-linux-amd64.tar';cd,ld=fixture_tar(archive);local=verify_docker_tar(archive)
 with tarfile.open(archive) as outer:
  config=outer.extractfile(cd).read();layer=outer.extractfile(ld+'.tar.gz').read()
 config_desc={'mediaType':'application/vnd.oci.image.config.v1+json','digest':cd,'size':len(config)}
 layer_desc={'mediaType':'application/vnd.oci.image.layer.v1.tar+gzip','digest':ld,'size':len(layer)}
 manifest=json.dumps({'schemaVersion':2,'mediaType':'application/vnd.oci.image.manifest.v1+json','config':config_desc,'layers':[layer_desc]},sort_keys=True,separators=(',',':')).encode();md='sha256:'+hashlib.sha256(manifest).hexdigest()
 layout=tmp_path/'layout';(layout/'blobs'/'sha256').mkdir(parents=True);(layout/'oci-layout').write_text('{"imageLayoutVersion":"1.0.0"}')
 index={'schemaVersion':2,'mediaType':'application/vnd.oci.image.index.v1+json','manifests':[{'mediaType':'application/vnd.oci.image.manifest.v1+json','digest':md,'size':len(manifest),'platform':{'os':'linux','architecture':'amd64'}}]};(layout/'index.json').write_text(json.dumps(index,separators=(',',':')))
 for dg,data in ((md,manifest),(cd,config),(ld,layer)):(layout/'blobs'/'sha256'/dg.split(':')[1]).write_bytes(data)
 lv=verify_oci_layout(layout);source='docker.io/rhysd/actionlint@'+md
 responses=[{'url':'https://registry-1.docker.io/v2/rhysd/actionlint/manifests/'+md,'status':200,'content_type':'application/vnd.oci.image.manifest.v1+json','docker_content_digest':md,'body_sha256':md.split(':')[1],'body_size':len(manifest)},{'url':'https://registry-1.docker.io/v2/rhysd/actionlint/blobs/'+cd,'status':200,'content_type':'application/vnd.oci.image.config.v1+json','docker_content_digest':'','body_sha256':cd.split(':')[1],'body_size':len(config)},{'url':'https://production.cloudfront.docker.com/v2/rhysd/actionlint/blobs/'+ld,'status':200,'content_type':'application/vnd.oci.image.layer.v1.tar+gzip','docker_content_digest':'','body_sha256':ld.split(':')[1],'body_size':len(layer)}]
 def acq(s):return {'session_id':s,'acquired_at_utc':'2026-08-12T00:00:00Z','repository':'rhysd/actionlint','manifest_sha256':md,'manifest_media_type':'application/vnd.oci.image.manifest.v1+json','config_sha256':cd,'platform':{'os':'linux','architecture':'amd64'},'layers':[layer_desc],'responses':responses,'auth':{'realm':'https://auth.docker.io/token','service':'registry.docker.io','scope':'repository:rhysd/actionlint:pull','token_persisted':False,'token_response_status':200}}
 argv=['python','builder'];policy=tmp_path/'policy';policy.write_text('p');closure=tmp_path/'closure';closure.write_text('c')
 tool={'python':'3','verifier_source_sha256':hashlib.sha256(Path('scripts/oci_evidence_v2.py').read_bytes()).hexdigest(),'builder_source_sha256':hashlib.sha256(Path('scripts/build_oci_evidence_v2.py').read_bytes()).hexdigest(),'independent_verifier_sha256':hashlib.sha256(Path('scripts/verify_oci_evidence_v2.py').read_bytes()).hexdigest(),'schema_sha256':hashlib.sha256(Path('schemas/oci-evidence-v2.schema.json').read_bytes()).hexdigest()}
 value={'schema_version':'oci-evidence-v2','authority':'NONE','status':'LOCAL_OCI_EVIDENCE_ONLY','not_host_receipt':True,'created_at_utc':'2026-08-12T00:00:00Z','source_image':source,'repository':{'origin':'origin','commit':'0'*40,'tree':'1'*40},'inputs':{'policy_sha256':hashlib.sha256(b'p').hexdigest(),'closure_sha256':hashlib.sha256(b'c').hexdigest(),'archive_name':archive.name,'resolved_path_diagnostic':str(archive),'archive_post_sha256':local['archive_sha256']},'command':{'argv':argv,'sha256':hashlib.sha256(json.dumps(argv,separators=(',',':')).encode()).hexdigest()},'tool':tool,'acquisitions':[acq('a'),acq('b')],'dual_acquisition':{'equal':True,'first_session':'a','second_session':'b'},'local_verification':local,'oci_layout_verification':lv,'limitations':['PENDING_UNTIL_ROOTLESS_HOST_SMOKE','NOT_A_HOST_RECEIPT','ZERO_SENTINEL_UNCHANGED'],'readiness':'NOT_READY_FOR_HOST_APPLY'}
 return value,archive,layout,policy,closure

def test_complete_valid_receipt_and_local_bytes(tmp_path):
 value,archive,layout,policy,closure=complete_fixture(tmp_path)
 assert verify_receipt(value,archive,layout,policy,closure,{'origin':'origin','commit':'0'*40,'tree':'1'*40,'source_image':value['source_image']}) is value

def test_receipt_archive_identity_is_producer_local_but_candidate_stays_strict(tmp_path):
 value,archive,layout,policy,closure=complete_fixture(tmp_path)
 expected={'origin':'origin','commit':'0'*40,'tree':'1'*40,'source_image':value['source_image']}
 copied=tmp_path/'copied-actionlint.tar';shutil.copyfile(archive,copied)
 assert archive.stat().st_ino!=copied.stat().st_ino
 assert verify_receipt(value,copied,layout,policy,closure,expected) is value

 hardlinked=tmp_path/'hardlinked-actionlint.tar';os.link(copied,hardlinked)
 with pytest.raises(ValueError,match='ARCHIVE_IDENTITY'):verify_receipt(value,hardlinked,layout,policy,closure,expected)
 hardlinked.unlink()
 symlinked=tmp_path/'symlinked-actionlint.tar';symlinked.symlink_to(copied)
 with pytest.raises(ValueError,match='ARCHIVE_IDENTITY'):verify_receipt(value,symlinked,layout,policy,closure,expected)
 symlinked.unlink()
 copied.write_bytes(copied.read_bytes()+b'mutated')
 with pytest.raises(ValueError):verify_receipt(value,copied,layout,policy,closure,expected)

@pytest.mark.parametrize('path,replacement,error',[
 (('repository','origin'),'evil','REPOSITORY_BINDING'),(('source_image',),'docker.io/evil@sha256:'+'0'*64,'SOURCE'),
 (('inputs','policy_sha256'),'0'*64,'INPUT_BYTES'),(('command','sha256'),'0'*64,'COMMAND_HASH'),
 (('tool','schema_sha256'),'0'*64,'TOOL_BYTES'),(('dual_acquisition','first_session'),'x','DUAL'),
 (('acquisitions',0,'responses',0,'content_type'),'','RESPONSE_CONTENT'),(('acquisitions',0,'responses',0,'body_size'),0,'RESPONSE_BINDING')])
def test_complete_receipt_mutations_fail(tmp_path,path,replacement,error):
 value,archive,layout,policy,closure=complete_fixture(tmp_path);approved=value['source_image'];cur=value
 for key in path[:-1]:cur=cur[key]
 cur[path[-1]]=replacement
 with pytest.raises(ValueError,match=error):verify_receipt(value,archive,layout,policy,closure,{'origin':'origin','commit':'0'*40,'tree':'1'*40,'source_image':approved})

def test_receipt_rejects_html_and_wrong_layer_media_type(tmp_path):
 value,archive,layout,policy,closure=complete_fixture(tmp_path);expected={'origin':'origin','commit':'0'*40,'tree':'1'*40,'source_image':value['source_image']}
 value['acquisitions'][0]['responses'][0]['content_type']='text/html'
 with pytest.raises(ValueError,match='RESPONSE_CONTENT_TYPE'):verify_receipt(value,archive,layout,policy,closure,expected)
 second=tmp_path/'second';second.mkdir();value,archive,layout,policy,closure=complete_fixture(second);expected={'origin':'origin','commit':'0'*40,'tree':'1'*40,'source_image':value['source_image']}
 value['acquisitions'][0]['layers'][0]['mediaType']='text/plain';value['acquisitions'][1]['layers'][0]['mediaType']='text/plain'
 with pytest.raises(ValueError):verify_receipt(value,archive,layout,policy,closure,expected)

def test_live_observed_octet_stream_is_accepted_only_for_blobs(tmp_path):
 value,archive,layout,policy,closure=complete_fixture(tmp_path);expected={'origin':'origin','commit':'0'*40,'tree':'1'*40,'source_image':value['source_image']}
 for acquisition in value['acquisitions']:
  for response in acquisition['responses'][1:]:response['content_type']='application/octet-stream'
 assert verify_receipt(value,archive,layout,policy,closure,expected) is value
 value['acquisitions'][0]['responses'][1]['content_type']='application/x-arbitrary'
 with pytest.raises(ValueError,match='RESPONSE_CONTENT_TYPE'):verify_receipt(value,archive,layout,policy,closure,expected)

def test_blob_dcd_is_empty_or_exact_descriptor_only(tmp_path):
 value,archive,layout,policy,closure=complete_fixture(tmp_path);expected={'origin':'origin','commit':'0'*40,'tree':'1'*40,'source_image':value['source_image']}
 for acquisition in value['acquisitions']:
  acquisition['responses'][1]['docker_content_digest']=acquisition['config_sha256'];acquisition['responses'][2]['docker_content_digest']=acquisition['layers'][0]['digest']
 assert verify_receipt(value,archive,layout,policy,closure,expected) is value
 value['acquisitions'][0]['responses'][1]['docker_content_digest']='sha256:'+'0'*64
 with pytest.raises(ValueError,match='RESPONSE_DCD'):verify_receipt(value,archive,layout,policy,closure,expected)

def approval_verifier_inputs(tmp_path):
 value,archive,layout,evidence_policy,closure=complete_fixture(tmp_path);receipt=tmp_path/'evidence-v2.json';data=(json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode();receipt.write_bytes(data);side=tmp_path/'evidence-v2.json.sha256';side.write_text(hashlib.sha256(data).hexdigest()+'  '+receipt.name+'\n')
 approval={'schema_version':'oci-evidence-approval-v1','authority':'NONE','status':'PRE_HOST_OCI_EVIDENCE_APPROVED','not_host_receipt':True,'source_image':value['source_image'],'source_commit':'0'*40,'source_tree':'1'*40,'receipt_sha256':hashlib.sha256(data).hexdigest(),'sidecar_file_sha256':hashlib.sha256(side.read_bytes()).hexdigest(),'evidence_policy_sha256':value['inputs']['policy_sha256'],'closure_sha256':value['inputs']['closure_sha256'],'archive':{'name':archive.name,'format':'docker-save-tar','size':archive.stat().st_size,'sha256':value['local_verification']['archive_sha256']},'manifest':value['oci_layout_verification']['manifest_digest'],'config':value['local_verification']['config_digest'],'layers':[x['digest'] for x in value['local_verification']['layers']],'rootfs_sha256':value['local_verification']['rootfs_sha256'],'executable_sha256':value['local_verification']['actionlint']['sha256'],'version_execution':'PENDING_UNTIL_ROOTLESS_HOST_SMOKE','external_locator':'OWNER_PROVIDED_EXACT_ARTIFACT_ROOT','v1_receipt_accepted':False}
 ap=tmp_path/'approval.json';ap.write_text(json.dumps(approval));current=tmp_path/'current-policy.json';current.write_text(json.dumps({'authority':'NONE','status':'PRE_HOST_OCI_EVIDENCE_APPROVED','image':value['source_image'],'oci_archive_sha256':approval['archive']['sha256'],'oci_evidence_approval':APPROVAL_POLICY_PATH}))
 return approval,ap,['--policy',str(current),'--approval',str(ap),'--receipt',str(receipt),'--receipt-sha256',str(side),'--archive',str(archive),'--layout',str(layout),'--closure',str(closure),'--origin','origin']

def copy_valid_approval_to(approval,target):
 target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(approval,target);return target

def verify_approval_cli(args,approval,approval_policy_path):
 from scripts.verify_oci_evidence_approval import main
 args=list(args);args[args.index('--approval')+1]=str(approval)
 if approval_policy_path is not None:args.extend(['--approval-policy-path',approval_policy_path])
 return main(args)

def test_installed_physical_approval_uses_source_relative_policy_identity(tmp_path):
 _,source,args=approval_verifier_inputs(tmp_path)
 approval=copy_valid_approval_to(source,tmp_path/'installed'/'approval.json')
 assert verify_approval_cli(args,approval,APPROVAL_POLICY_PATH)==0

def test_installed_layout_approval_verifier_resolves_receipt_bound_source_bytes(tmp_path):
 _,approval,args=approval_verifier_inputs(tmp_path)
 lib=tmp_path/'installed'/'libexec'/'mee-claw-host-deploy-lib';schema=tmp_path/'installed'/'libexec'/'schemas'
 lib.mkdir(parents=True);schema.mkdir()
 for name in ('oci_evidence_v2.py','verify_oci_evidence_approval.py','build_oci_evidence_v2.py','verify_oci_evidence_v2.py'):
  shutil.copyfile(Path('scripts')/name,lib/name)
 shutil.copyfile(Path('schemas/oci-evidence-v2.schema.json'),schema/'oci-evidence-v2.schema.json')
 installed_approval=copy_valid_approval_to(approval,lib/'approval.json')
 argv=list(args);argv[argv.index('--approval')+1]=str(installed_approval);argv.extend(['--approval-policy-path',APPROVAL_POLICY_PATH])
 result=subprocess.run([sys.executable,'-B',str(lib/'verify_oci_evidence_approval.py'),*argv],cwd=tmp_path,text=True,capture_output=True)
 assert result.returncode==0,result.stderr

@pytest.mark.parametrize('logical',[None,'/ci/claw/oci-evidence-approval.json',r'ci\claw\oci-evidence-approval.json','ci/claw/../claw/oci-evidence-approval.json','ci/claw/other.json'])
def test_logical_approval_policy_path_is_exact_and_closed(tmp_path,logical):
 _,approval,args=approval_verifier_inputs(tmp_path)
 with pytest.raises(SystemExit):verify_approval_cli(args,approval,logical)

def test_duplicate_approval_policy_path_is_rejected(tmp_path,capsys):
 _,approval,args=approval_verifier_inputs(tmp_path)
 args.extend(['--approval-policy-path',APPROVAL_POLICY_PATH,'--approval-policy-path',APPROVAL_POLICY_PATH])
 with pytest.raises(SystemExit) as exc:
  verify_approval_cli(args,approval,None)
 assert exc.value.code==2
 assert 'argument --approval-policy-path: may not be repeated' in capsys.readouterr().err

def test_current_policy_binding_rejects_mismatched_logical_approval_path(tmp_path):
 _,approval,args=approval_verifier_inputs(tmp_path)
 policy=Path(args[args.index('--policy')+1])
 value=json.loads(policy.read_text());value['oci_evidence_approval']='ci/claw/other.json';policy.write_text(json.dumps(value))
 with pytest.raises(ValueError,match='CURRENT_POLICY_BINDING'):
  verify_approval_cli(args,approval,APPROVAL_POLICY_PATH)

def test_approval_verifier_executes_full_tuple_and_rejects_graph_mutation(tmp_path):
 from scripts.verify_oci_evidence_approval import main
 value,archive,layout,evidence_policy,closure=complete_fixture(tmp_path);receipt=tmp_path/'evidence-v2.json';data=(json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode();receipt.write_bytes(data);side=tmp_path/'evidence-v2.json.sha256';side.write_text(hashlib.sha256(data).hexdigest()+'  '+receipt.name+'\n')
 approval={'schema_version':'oci-evidence-approval-v1','authority':'NONE','status':'PRE_HOST_OCI_EVIDENCE_APPROVED','not_host_receipt':True,'source_image':value['source_image'],'source_commit':'0'*40,'source_tree':'1'*40,'receipt_sha256':hashlib.sha256(data).hexdigest(),'sidecar_file_sha256':hashlib.sha256(side.read_bytes()).hexdigest(),'evidence_policy_sha256':value['inputs']['policy_sha256'],'closure_sha256':value['inputs']['closure_sha256'],'archive':{'name':archive.name,'format':'docker-save-tar','size':archive.stat().st_size,'sha256':value['local_verification']['archive_sha256']},'manifest':value['oci_layout_verification']['manifest_digest'],'config':value['local_verification']['config_digest'],'layers':[x['digest'] for x in value['local_verification']['layers']],'rootfs_sha256':value['local_verification']['rootfs_sha256'],'executable_sha256':value['local_verification']['actionlint']['sha256'],'version_execution':'PENDING_UNTIL_ROOTLESS_HOST_SMOKE','external_locator':'OWNER_PROVIDED_EXACT_ARTIFACT_ROOT','v1_receipt_accepted':False}
 ap=tmp_path/'approval.json';ap.write_text(json.dumps(approval));current=tmp_path/'current-policy.json';current.write_text(json.dumps({'authority':'NONE','status':'PRE_HOST_OCI_EVIDENCE_APPROVED','image':value['source_image'],'oci_archive_sha256':approval['archive']['sha256'],'oci_evidence_approval':APPROVAL_POLICY_PATH}))
 args=['--policy',str(current),'--approval',str(ap),'--approval-policy-path',APPROVAL_POLICY_PATH,'--receipt',str(receipt),'--receipt-sha256',str(side),'--archive',str(archive),'--layout',str(layout),'--closure',str(closure),'--origin','origin']
 assert main(args)==0;base=json.loads(json.dumps(approval))
 approval['layers'][0]='sha256:'+'0'*64;ap.write_text(json.dumps(approval))
 with pytest.raises(ValueError,match='APPROVED_GRAPH_MISMATCH'):main(args)
 for key,bad,error in (('schema_version','v1','APPROVAL_NOT_CLOSED'),('external_locator','file:///tmp','APPROVAL_NOT_CLOSED'),('closure_sha256','0'*64,'APPROVED_PROJECTION_MISMATCH')):
  approval=json.loads(json.dumps(base));approval[key]=bad;ap.write_text(json.dumps(approval))
  with pytest.raises(ValueError,match=error):main(args)
 second=tmp_path/'layer';second.mkdir();value,archive,layout,policy,closure=complete_fixture(second);expected={'origin':'origin','commit':'0'*40,'tree':'1'*40,'source_image':value['source_image']};value['acquisitions'][0]['responses'][2]['docker_content_digest']='sha256:'+'0'*64
 with pytest.raises(ValueError,match='RESPONSE_DCD'):verify_receipt(value,archive,layout,policy,closure,expected)
