import json
from scripts.verify_claw_runner_api_canary import verify

class Response:
 def __init__(self,value,status=200): self.value=value; self.status=status
 def __enter__(self): return self
 def __exit__(self,*args): pass
 def read(self,n): return self.value

def policy(): return {'repository':'Dimkox/multi-exchange-engine','runner_name':'claw-engine-runner','required_labels':['self-hosted','claw','claw-engine-runner']}
def body(runners): return json.dumps({'total_count':len(runners),'runners':runners}).encode()
def runner(id=1,status='online',name='claw-engine-runner',labels=None): return {'id':id,'name':name,'status':status,'labels':[{'name':x} for x in (labels or ['self-hosted','claw','claw-engine-runner'])]}

def test_unique_online_exact_runner_and_labels_passes_without_token_leak():
 seen={}
 def open_(request,timeout): seen['authorization']=request.headers['Authorization']; return Response(body([runner()]))
 result=verify('ephemeral-token',policy(),open_); assert result
 assert seen['authorization']=='Bearer ephemeral-token'
 assert result=={'repository':'Dimkox/multi-exchange-engine','runner_id':1,'runner_name':'claw-engine-runner','status':'online','labels':['claw','claw-engine-runner','self-hosted'],'matching_count':1,'total_count':1}

def test_duplicate_offline_missing_label_and_count_mismatch_fail():
 cases=[body([runner(),runner(2)]),body([runner(status='offline')]),body([runner(labels=['self-hosted'])]),json.dumps({'total_count':2,'runners':[runner()]}).encode()]
 for value in cases: assert not verify('token',policy(),lambda *_args,**_kwargs:Response(value))

def test_duplicate_json_key_and_oversize_fail_closed():
 import pytest
 with pytest.raises(ValueError): verify('token',policy(),lambda *_args,**_kwargs:Response(b'{"total_count":0,"total_count":0,"runners":[]}'))
 assert not verify('token',policy(),lambda *_args,**_kwargs:Response(b'x'*1048577))
