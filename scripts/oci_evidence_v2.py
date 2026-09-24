#!/usr/bin/env python3
"""Secret-free local OCI evidence verifier and Docker Hub dual acquirer."""
import argparse,gzip,hashlib,io,json,os,posixpath,platform,re,stat,tarfile,time,urllib.parse,urllib.request,uuid
from pathlib import Path,PurePosixPath
class AcquisitionError(ValueError):pass
def duplicate_reject(items):
 value={}
 for key,item in items:
  if key in value:raise ValueError('DUPLICATE_JSON_KEY')
  value[key]=item
 return value
def validate_schema(value,schema,root=None):
 root=root or schema
 if '$ref' in schema:
  target=root
  for part in schema['$ref'].removeprefix('#/').split('/'):target=target[part]
  return validate_schema(value,target,root)
 if 'const' in schema and value!=schema['const']:raise ValueError('SCHEMA_CONST')
 if 'enum' in schema and value not in schema['enum']:raise ValueError('SCHEMA_ENUM')
 kind=schema.get('type')
 if kind=='object':
  if not isinstance(value,dict):raise ValueError('SCHEMA_TYPE')
  required=set(schema.get('required',[]));properties=schema.get('properties',{})
  if not required<=set(value) or (schema.get('additionalProperties') is False and set(value)-set(properties)):raise ValueError('SCHEMA_FIELDS')
  for key,item in value.items():
   if key in properties:validate_schema(item,properties[key],root)
 elif kind=='array':
  if not isinstance(value,list):raise ValueError('SCHEMA_TYPE')
  if len(value)<schema.get('minItems',0) or len(value)>schema.get('maxItems',2**63):raise ValueError('SCHEMA_LENGTH')
  if schema.get('uniqueItems') and len({json.dumps(x,sort_keys=True) for x in value})!=len(value):raise ValueError('SCHEMA_UNIQUE')
  for item in value:validate_schema(item,schema.get('items',{}),root)
 elif kind=='string':
  if not isinstance(value,str):raise ValueError('SCHEMA_TYPE')
  if 'pattern' in schema and not re.search(schema['pattern'],value):raise ValueError('SCHEMA_PATTERN')
 elif kind=='integer' and (not isinstance(value,int) or isinstance(value,bool)):raise ValueError('SCHEMA_TYPE')
 if isinstance(value,int) and 'minimum' in schema and value<schema['minimum']:raise ValueError('SCHEMA_MINIMUM')
def digest(data):return 'sha256:'+hashlib.sha256(data).hexdigest()
SHA256_RE=re.compile(r'^sha256:[0-9a-f]{64}$')
MAX_MEMBER=256*1024*1024;MAX_LAYER=512*1024*1024;MAX_TOTAL=1024*1024*1024
def approved_http_type(role,observed,descriptor):
 value=observed.split(';',1)[0].strip()
 if role=='manifest':return value=='application/vnd.oci.image.manifest.v1+json'
 return value in {'application/octet-stream',descriptor}
def safe_member(member,allow_links=False):
 path=PurePosixPath(member.name)
 unsafe_link=False
 if member.issym() or member.islnk():
  if not allow_links:unsafe_link=True
  else:
   target=member.linkname.lstrip('/') if member.linkname.startswith('/') else posixpath.join(str(path.parent),member.linkname)
   unsafe_link=posixpath.normpath(target).startswith('../')
 if path.is_absolute() or '..' in path.parts or member.isdev() or member.isfifo() or member.type==tarfile.GNUTYPE_SPARSE or member.pax_headers or member.size>MAX_MEMBER or unsafe_link:raise ValueError('UNSAFE_TAR')
 if not (member.isfile() or member.isdir() or (allow_links and (member.issym() or member.islnk()))):raise ValueError('UNSAFE_TAR_TYPE')
def _file_identity(path):
 info=path.lstat()
 if path.is_symlink() or not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:raise ValueError('ARCHIVE_IDENTITY')
 return {'size':info.st_size,'device':info.st_dev,'inode':info.st_ino,'links':info.st_nlink}
def _portable_local_verification(value):
 identity=value['archive_identity']
 if identity['links']!=1 or any(type(identity[field]) is not int or not 0<=identity[field]<2**63 for field in ('size','device','inode')):raise ValueError('ARCHIVE_IDENTITY')
 return {**value,'archive_identity':{'size':identity['size'],'links':identity['links']}}
def verify_docker_tar(path):
 path=Path(path);before=_file_identity(path); archive_hash=hashlib.sha256(path.read_bytes()).hexdigest()
 root={};whiteouts=[];expanded_total=0;binary=None
 with tarfile.open(path,'r:*') as outer:
  members=outer.getmembers()
  if not 1<=len(members)<=256:raise ValueError('TAR_MEMBER_COUNT')
  names=set();total=0
  for member in members:
   safe_member(member);canonical=PurePosixPath(member.name).as_posix().lstrip('./')
   if canonical in names:raise ValueError('DUPLICATE_TAR_NAME')
   names.add(canonical);total+=member.size
  if total>MAX_TOTAL:raise ValueError('TAR_TOTAL_SIZE')
  manifest=json.loads(outer.extractfile('manifest.json').read(),object_pairs_hook=duplicate_reject)
  if not isinstance(manifest,list) or len(manifest)!=1 or set(manifest[0])!={'Config','RepoTags','Layers'}:raise ValueError('MANIFEST_SHAPE')
  entry=manifest[0];config_bytes=outer.extractfile(entry['Config']).read();config_digest=digest(config_bytes)
  if entry['Config'] not in (config_digest,config_digest.split(':')[1]+'.json'):raise ValueError('CONFIG_DIGEST')
  config=json.loads(config_bytes,object_pairs_hook=duplicate_reject)
  if config.get('os')!='linux' or config.get('architecture')!='amd64':raise ValueError('PLATFORM')
  layer_results=[]; diff_ids=config.get('rootfs',{}).get('diff_ids',[])
  if len(diff_ids)!=len(entry['Layers']):raise ValueError('DIFF_ID_COUNT')
  action=None
  for ordinal,(name,expected_diff) in enumerate(zip(entry['Layers'],diff_ids)):
   compressed=outer.extractfile(name).read(); layer_digest=digest(compressed)
   if not (name.startswith(layer_digest.split(':')[1]) or name.startswith(layer_digest)):raise ValueError('LAYER_DIGEST')
   chunks=[];expanded=0
   with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as stream:
    while True:
     chunk=stream.read(min(1024*1024,MAX_LAYER-expanded+1))
     if not chunk:break
     expanded+=len(chunk);expanded_total+=len(chunk)
     if expanded>MAX_LAYER or expanded_total>MAX_TOTAL:raise ValueError('LAYER_EXPANSION')
     chunks.append(chunk)
   raw=b''.join(chunks)
   diff=digest(raw)
   if diff!=expected_diff:raise ValueError('DIFF_ID')
   with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as layer:
    layer_names=set()
    for member in layer.getmembers():
     safe_member(member,allow_links=True); key=PurePosixPath(member.name).as_posix().lstrip('./')
     if key in layer_names:raise ValueError('DUPLICATE_LAYER_NAME')
     layer_names.add(key)
     base=PurePosixPath(key).name
     if base.startswith('.wh.'):
      whiteouts.append(key);parent=str(PurePosixPath(key).parent)
      if base=='.wh..wh..opq':
       prefix='' if parent=='.' else parent+'/'
       root={k:v for k,v in root.items() if not k.startswith(prefix)}
      else:
       target=str(PurePosixPath(key).parent/base[4:]);root={k:v for k,v in root.items() if k!=target and not k.startswith(target+'/')}
      continue
     if member.isfile():
      body=layer.extractfile(member).read();root[key]={'mode':stat.S_IMODE(member.mode),'sha256':hashlib.sha256(body).hexdigest(),'size':member.size}
      if key=='usr/local/bin/actionlint':binary=body
     elif member.isdir():root[key]={'mode':stat.S_IMODE(member.mode),'directory':True}
     elif member.issym() or member.islnk():root[key]={'link':member.linkname,'hardlink':member.islnk()}
   layer_results.append({'ordinal':ordinal,'name':name,'digest':layer_digest,'diff_id':diff,'compressed_size':len(compressed),'uncompressed_size':len(raw)})
  candidate=root.get('usr/local/bin/actionlint')
  if not candidate or candidate.get('mode')!=0o755:raise ValueError('ACTIONLINT_MISSING')
  if binary is None or len(binary)<20 or binary[:4]!=b'\x7fELF' or binary[4]!=2 or binary[5]!=1 or binary[6]!=1:raise ValueError('ACTIONLINT_ELF')
  machine=int.from_bytes(binary[18:20],'little')
  if machine!=62:raise ValueError('ACTIONLINT_MACHINE')
 after=_file_identity(path)
 if before!=after or archive_hash!=hashlib.sha256(path.read_bytes()).hexdigest():raise ValueError('ARCHIVE_SWAP')
 canonical=json.dumps(root,sort_keys=True,separators=(',',':')).encode()
 return {'archive_sha256':archive_hash,'archive_identity':after,'platform':{'os':'linux','architecture':'amd64'},'config_digest':config_digest,'diff_ids':diff_ids,'layers':layer_results,'whiteouts':whiteouts,'rootfs_sha256':hashlib.sha256(canonical).hexdigest(),'rootfs_entries':len(root),'actionlint':{'path':'usr/local/bin/actionlint','mode':'0755','size':len(binary),'sha256':hashlib.sha256(binary).hexdigest(),'elf':{'class':'ELF64','machine':'x86-64'},'version_execution':'PENDING_UNTIL_ROOTLESS_HOST_SMOKE'}}
def verify_oci_layout(path):
 root=Path(path).resolve(strict=True)
 if root.is_symlink() or not root.is_dir():raise ValueError('OCI_LAYOUT_IDENTITY')
 for parent in (root/'blobs',root/'blobs'/'sha256'):
  if parent.is_symlink() or not parent.is_dir():raise ValueError('OCI_LAYOUT_PARENT')
 layout=json.loads((root/'oci-layout').read_bytes(),object_pairs_hook=duplicate_reject);index=json.loads((root/'index.json').read_bytes(),object_pairs_hook=duplicate_reject)
 if layout!={'imageLayoutVersion':'1.0.0'} or set(index)!={'schemaVersion','mediaType','manifests'} or index['mediaType']!='application/vnd.oci.image.index.v1+json' or len(index['manifests'])!=1:raise ValueError('OCI_LAYOUT_SHAPE')
 descriptors=[]
 def read(desc,parse=True):
  allowed={'mediaType','digest','size','annotations','platform','artifactType'}
  if not isinstance(desc,dict) or set(desc)-allowed or not {'mediaType','digest','size'}<=set(desc) or not SHA256_RE.fullmatch(desc['digest']) or not isinstance(desc['size'],int) or desc['size']<0:raise ValueError('OCI_DESCRIPTOR_FIELDS')
  algo,value=desc['digest'].split(':',1);target=root/'blobs'/algo/value;data=target.read_bytes()
  if algo!='sha256' or digest(data)!=desc['digest'] or len(data)!=desc['size'] or target.is_symlink() or target.stat().st_nlink!=1:raise ValueError('OCI_DESCRIPTOR_MISMATCH')
  descriptors.append({'mediaType':desc['mediaType'],'digest':desc['digest'],'size':desc['size']});return json.loads(data,object_pairs_hook=duplicate_reject) if parse else data
 manifest_desc=index['manifests'][0]
 if manifest_desc['mediaType']!='application/vnd.oci.image.manifest.v1+json':raise ValueError('OCI_MANIFEST_MEDIA')
 manifest=read(manifest_desc)
 if set(manifest)!={'schemaVersion','mediaType','config','layers'} or manifest['schemaVersion']!=2 or manifest['mediaType']!='application/vnd.oci.image.manifest.v1+json':raise ValueError('OCI_MANIFEST_SHAPE')
 config_desc=manifest['config']
 if config_desc['mediaType']!='application/vnd.oci.image.config.v1+json':raise ValueError('OCI_CONFIG_MEDIA')
 config=read(config_desc)
 for layer in manifest['layers']:
  if layer['mediaType'] not in {'application/vnd.oci.image.layer.v1.tar+gzip','application/vnd.docker.image.rootfs.diff.tar.gzip'}:raise ValueError('OCI_LAYER_MEDIA')
  read(layer,False)
 if config.get('os')!='linux' or config.get('architecture')!='amd64':raise ValueError('OCI_LAYOUT_PLATFORM')
 referenced={d['digest'].split(':',1)[1] for d in descriptors}
 actual={p.name for p in (root/'blobs'/'sha256').iterdir() if p.is_file()}
 if actual!=referenced:raise ValueError('OCI_UNREFERENCED_BLOB')
 return {'layout_version':'1.0.0','manifest_digest':manifest_desc['digest'],'platform':{'os':'linux','architecture':'amd64'},'descriptors':descriptors}
def compare_acquisitions(first,second):
 if first.get('session_id')==second.get('session_id'):raise AcquisitionError('SESSIONS_NOT_FRESH')
 graph=lambda x:(x.get('manifest_sha256'),x.get('config_sha256'),x.get('layers'))
 if graph(first)!=graph(second):raise AcquisitionError('DUAL_GRAPH_MISMATCH')
 return {'equal':True,'first_session':first['session_id'],'second_session':second['session_id']}
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,request,fp,code,msg,headers,newurl):
  source=urllib.parse.urlparse(request.full_url);target=urllib.parse.urlparse(newurl)
  if code not in (302,307) or source.hostname!='registry-1.docker.io' or target.scheme!='https' or target.hostname!='production.cloudfront.docker.com':raise AcquisitionError('UNAPPROVED_REDIRECT')
  return urllib.request.Request(newurl,headers={'Accept':request.headers.get('Accept','application/octet-stream')})
def _request(opener,url,headers=None,limit=300*1024*1024):
 parsed=urllib.parse.urlparse(url)
 if parsed.scheme!='https' or parsed.hostname not in {'auth.docker.io','registry-1.docker.io','production.cloudfront.docker.com'}:raise AcquisitionError('UNAPPROVED_ENDPOINT')
 request=urllib.request.Request(url,headers=headers or {})
 with opener.open(request,timeout=60) as response:
  body=response.read(limit+1)
  if len(body)>limit:raise AcquisitionError('RESPONSE_OVERSIZE')
  metadata={'url':url,'status':response.status,'content_type':response.headers.get('Content-Type',''),'docker_content_digest':response.headers.get('Docker-Content-Digest',''),'body_sha256':hashlib.sha256(body).hexdigest(),'body_size':len(body)}
  return body,metadata
def acquire_once(repository,manifest_digest,opener=None):
 if repository!='rhysd/actionlint' or manifest_digest!='sha256:9d36088643581e728c969f35141f88139fec77280b2be23c1f66f8e40e1025e7':raise AcquisitionError('SOURCE_NOT_APPROVED')
 opener=opener or urllib.request.build_opener(NoRedirect())
 realm='https://auth.docker.io/token';service='registry.docker.io';scope='repository:rhysd/actionlint:pull'
 token_body,token_meta=_request(opener,realm+'?'+urllib.parse.urlencode({'service':service,'scope':scope}),limit=64*1024)
 token_value=json.loads(token_body,object_pairs_hook=duplicate_reject)
 if not isinstance(token_value,dict) or set(token_value)-{'token','access_token','expires_in','issued_at'} or not (token_value.get('token') or token_value.get('access_token')):raise AcquisitionError('TOKEN_RESPONSE')
 token=token_value.get('token') or token_value.get('access_token'); auth={'Authorization':'Bearer '+token,'Accept':'application/vnd.oci.image.manifest.v1+json'}
 base='https://registry-1.docker.io/v2/'+repository
 manifest_bytes,manifest_meta=_request(opener,base+'/manifests/'+manifest_digest,auth,4*1024*1024)
 if manifest_meta['docker_content_digest']!=manifest_digest or digest(manifest_bytes)!=manifest_digest:raise AcquisitionError('MANIFEST_DIGEST')
 manifest=json.loads(manifest_bytes,object_pairs_hook=duplicate_reject)
 if manifest.get('mediaType')!='application/vnd.oci.image.manifest.v1+json' or set(manifest)!={'schemaVersion','mediaType','config','layers'}:raise AcquisitionError('MANIFEST_MEDIA_TYPE')
 config_desc=manifest['config'];layer_desc=manifest['layers']; graph=[]
 if config_desc.get('mediaType')!='application/vnd.oci.image.config.v1+json' or any(x.get('mediaType')!='application/vnd.oci.image.layer.v1.tar+gzip' for x in layer_desc):raise AcquisitionError('DESCRIPTOR_MEDIA_TYPE')
 config_bytes,config_meta=_request(opener,base+'/blobs/'+config_desc['digest'],auth|{'Accept':config_desc['mediaType']},8*1024*1024)
 if not approved_http_type('config',config_meta['content_type'],config_desc['mediaType']) or not approved_http_type('manifest',manifest_meta['content_type'],manifest['mediaType']):raise AcquisitionError('RESPONSE_MEDIA_TYPE')
 if digest(config_bytes)!=config_desc['digest'] or len(config_bytes)!=config_desc['size'] or config_meta['docker_content_digest'] not in ('',config_desc['digest']):raise AcquisitionError('CONFIG_DESCRIPTOR')
 config=json.loads(config_bytes,object_pairs_hook=duplicate_reject)
 if config.get('os')!='linux' or config.get('architecture')!='amd64':raise AcquisitionError('CONFIG_PLATFORM')
 responses=[manifest_meta,config_meta]
 for descriptor in layer_desc:
  body,meta=_request(opener,base+'/blobs/'+descriptor['digest'],auth|{'Accept':descriptor['mediaType']})
  if digest(body)!=descriptor['digest'] or len(body)!=descriptor['size'] or meta['docker_content_digest'] not in ('',descriptor['digest']) or not approved_http_type('layer',meta['content_type'],descriptor['mediaType']):raise AcquisitionError('LAYER_DESCRIPTOR')
  graph.append({'digest':descriptor['digest'],'size':descriptor['size'],'mediaType':descriptor['mediaType']});responses.append(meta)
 token=None;auth=None
 return {'session_id':uuid.uuid4().hex,'acquired_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'repository':repository,'manifest_sha256':manifest_digest,'manifest_media_type':manifest['mediaType'],'config_sha256':config_desc['digest'],'platform':{'os':'linux','architecture':'amd64'},'layers':graph,'responses':responses,'auth':{'realm':realm,'service':service,'scope':scope,'token_persisted':False,'token_response_status':token_meta['status']}}
def _closed(value,keys,error):
 if not isinstance(value,dict) or set(value)!=set(keys):raise ValueError(error)
def _closed_receipt_projection(value):
 _closed(value['repository'],('origin','commit','tree'),'REPOSITORY_NOT_CLOSED')
 _closed(value['inputs'],('policy_sha256','closure_sha256','archive_name','resolved_path_diagnostic','archive_post_sha256'),'INPUTS_NOT_CLOSED')
 _closed(value['command'],('argv','sha256'),'COMMAND_NOT_CLOSED');_closed(value['tool'],('python','verifier_source_sha256','builder_source_sha256','independent_verifier_sha256','schema_sha256'),'TOOL_NOT_CLOSED')
 _closed(value['dual_acquisition'],('equal','first_session','second_session'),'DUAL_NOT_CLOSED')
 for item in value['acquisitions']:
  _closed(item,('session_id','acquired_at_utc','repository','manifest_sha256','manifest_media_type','config_sha256','platform','layers','responses','auth'),'ACQUISITION_NOT_CLOSED')
  _closed(item['platform'],('os','architecture'),'PLATFORM_NOT_CLOSED');_closed(item['auth'],('realm','service','scope','token_persisted','token_response_status'),'AUTH_NOT_CLOSED')
  for layer in item['layers']:_closed(layer,('digest','size','mediaType'),'LAYER_NOT_CLOSED')
  for response in item['responses']:_closed(response,('url','status','content_type','docker_content_digest','body_sha256','body_size'),'RESPONSE_NOT_CLOSED')
 local=value['local_verification'];_closed(local,('archive_sha256','archive_identity','platform','config_digest','diff_ids','layers','whiteouts','rootfs_sha256','rootfs_entries','actionlint'),'LOCAL_NOT_CLOSED')
 _closed(local['archive_identity'],('size','device','inode','links'),'IDENTITY_NOT_CLOSED');_closed(local['platform'],('os','architecture'),'PLATFORM_NOT_CLOSED')
 for layer in local['layers']:_closed(layer,('ordinal','name','digest','diff_id','compressed_size','uncompressed_size'),'LOCAL_LAYER_NOT_CLOSED')
 _closed(local['actionlint'],('path','mode','size','sha256','elf','version_execution'),'ACTIONLINT_NOT_CLOSED');_closed(local['actionlint']['elf'],('class','machine'),'ELF_NOT_CLOSED')
 layout=value['oci_layout_verification'];_closed(layout,('layout_version','manifest_digest','platform','descriptors'),'LAYOUT_NOT_CLOSED');_closed(layout['platform'],('os','architecture'),'PLATFORM_NOT_CLOSED')
 for descriptor in layout['descriptors']:_closed(descriptor,('mediaType','digest','size'),'DESCRIPTOR_NOT_CLOSED')
def verify_receipt(value,archive,layout=None,policy=None,closure=None,expected=None):
 receipt_fields={'schema_version','authority','status','not_host_receipt','created_at_utc','source_image','repository','inputs','command','tool','acquisitions','dual_acquisition','local_verification','oci_layout_verification','limitations','readiness'}
 if not isinstance(value,dict):raise ValueError('RECEIPT_NOT_CLOSED')
 if value.get('authority')!='NONE' or value.get('status')!='LOCAL_OCI_EVIDENCE_ONLY' or value.get('not_host_receipt') is not True:raise ValueError('STATUS_ESCALATION')
 if set(value)!=receipt_fields:raise ValueError('RECEIPT_NOT_CLOSED')
 _closed_receipt_projection(value)
 if value['readiness']!='NOT_READY_FOR_HOST_APPLY' or set(value['limitations'])!={'PENDING_UNTIL_ROOTLESS_HOST_SMOKE','NOT_A_HOST_RECEIPT','ZERO_SENTINEL_UNCHANGED'}:raise ValueError('READINESS_ESCALATION')
 if len(value['acquisitions'])!=2:raise ValueError('ACQUISITION_COUNT')
 compare_acquisitions(*value['acquisitions'])
 source_repo,source_digest=value['source_image'].removeprefix('docker.io/').split('@',1)
 if source_repo!='rhysd/actionlint' or not SHA256_RE.fullmatch(source_digest):raise ValueError('SOURCE_IMAGE')
 for acquisition in value['acquisitions']:
  if acquisition['repository']!=source_repo or acquisition['manifest_sha256']!=source_digest or acquisition['platform']!={'os':'linux','architecture':'amd64'}:raise ValueError('SOURCE_ACQUISITION_BINDING')
  if acquisition['auth']!={'realm':'https://auth.docker.io/token','service':'registry.docker.io','scope':'repository:rhysd/actionlint:pull','token_persisted':False,'token_response_status':200}:raise ValueError('AUTH_PROJECTION')
  if acquisition['manifest_media_type']!='application/vnd.oci.image.manifest.v1+json' or acquisition['config_sha256']!=value['local_verification']['config_digest']:raise ValueError('ACQUISITION_PROJECTION')
  if len(acquisition['responses'])!=2+len(acquisition['layers']):raise ValueError('RESPONSE_COUNT')
  expected_responses=[('manifests/'+source_digest,source_digest,value['oci_layout_verification']['descriptors'][0]['size']),('blobs/'+acquisition['config_sha256'],acquisition['config_sha256'],value['oci_layout_verification']['descriptors'][1]['size'])]+[('blobs/'+x['digest'],x['digest'],x['size']) for x in acquisition['layers']]
  descriptor_types=['application/vnd.oci.image.manifest.v1+json','application/vnd.oci.image.config.v1+json']+[x['mediaType'] for x in acquisition['layers']]
  for ordinal,(response,(suffix,response_digest,response_size),descriptor_type) in enumerate(zip(acquisition['responses'],expected_responses,descriptor_types)):
   parsed=urllib.parse.urlparse(response['url'])
   if parsed.scheme!='https' or parsed.hostname not in {'registry-1.docker.io','production.cloudfront.docker.com'} or response['status'] not in (200,206) or not re.fullmatch(r'[0-9a-f]{64}',response['body_sha256']) or response['body_size']<0:raise ValueError('RESPONSE_PROJECTION')
   if not parsed.path.endswith('/'+suffix) or response['body_sha256']!=response_digest.split(':',1)[1] or (response_size is not None and response['body_size']!=response_size):raise ValueError('RESPONSE_BINDING')
   if suffix.startswith('manifests/') and response['docker_content_digest']!=source_digest:raise ValueError('RESPONSE_BINDING')
   if not suffix.startswith('manifests/') and response['docker_content_digest'] not in ('',response_digest):raise ValueError('RESPONSE_DCD')
   if not approved_http_type('manifest' if ordinal==0 else 'blob',response['content_type'],descriptor_type):raise ValueError('RESPONSE_CONTENT_TYPE')
 if value['oci_layout_verification']['manifest_digest']!=source_digest or value['oci_layout_verification']['platform']!={'os':'linux','architecture':'amd64'}:raise ValueError('SOURCE_LAYOUT_BINDING')
 graph=[{'digest':x['digest'],'size':x['compressed_size']} for x in value['local_verification']['layers']]
 acquired=[{'digest':x['digest'],'size':x['size']} for x in value['acquisitions'][0]['layers']]
 layout_layers=[{'digest':x['digest'],'size':x['size']} for x in value['oci_layout_verification']['descriptors'][2:]]
 if graph!=acquired or acquired!=layout_layers or value['local_verification']['config_digest']!=value['acquisitions'][0]['config_sha256'] or value['oci_layout_verification']['descriptors'][1]['digest']!=value['local_verification']['config_digest']:raise ValueError('GRAPH_CROSS_BINDING')
 if value['dual_acquisition']!={'equal':True,'first_session':value['acquisitions'][0]['session_id'],'second_session':value['acquisitions'][1]['session_id']}:raise ValueError('DUAL_PROJECTION')
 if value['command']['sha256']!=hashlib.sha256(json.dumps(value['command']['argv'],separators=(',',':')).encode()).hexdigest():raise ValueError('COMMAND_HASH')
 if value['local_verification']['archive_sha256']!=value['inputs']['archive_post_sha256']:raise ValueError('ARCHIVE_BINDING')
 if expected:
  for key in ('origin','commit','tree'):
   if value['repository'][key]!=expected[key]:raise ValueError('REPOSITORY_BINDING')
  if value['source_image']!=expected['source_image']:raise ValueError('SOURCE_BINDING')
 serialized=json.dumps(value,sort_keys=True,separators=(',',':')).lower()
 if 'authorization' in serialized or 'bearer ' in serialized or 'access_token' in serialized or '"token"' in serialized:raise ValueError('SECRET_MATERIAL')
 if archive is not None and _portable_local_verification(value['local_verification'])!=_portable_local_verification(verify_docker_tar(archive)):raise ValueError('LOCAL_BYTES_MISMATCH')
 if layout is not None and value.get('oci_layout_verification')!=verify_oci_layout(layout):raise ValueError('LAYOUT_BYTES_MISMATCH')
 for label,path in (('policy_sha256',policy),('closure_sha256',closure)):
  if path is not None and value['inputs'][label]!=hashlib.sha256(Path(path).read_bytes()).hexdigest():raise ValueError('INPUT_BYTES_MISMATCH')
 for label,path in (('verifier_source_sha256',Path(__file__)),('builder_source_sha256',Path(__file__).with_name('build_oci_evidence_v2.py')),('independent_verifier_sha256',Path(__file__).with_name('verify_oci_evidence_v2.py')),('schema_sha256',Path(__file__).parents[1]/'schemas'/'oci-evidence-v2.schema.json')):
  if value['tool'][label]!=hashlib.sha256(path.read_bytes()).hexdigest():raise ValueError('TOOL_BYTES_MISMATCH')
 return value
