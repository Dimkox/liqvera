#!/usr/bin/python3.14
import argparse,json,sys,urllib.request
def pairs(xs):
 d={}
 for k,v in xs:
  if k in d: raise ValueError('duplicate')
  d[k]=v
 return d
def verify(token,policy,opener=urllib.request.urlopen):
 repository=policy['repository']; runner=policy['runner_name']; required=set(policy['required_labels'])
 if set(policy['required_labels'])!=required or not token:return False
 req=urllib.request.Request(f'https://api.github.com/repos/{repository}/actions/runners',headers={'Authorization':f'Bearer {token}','Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'})
 with opener(req,timeout=30) as r:data=r.read(1048577); status=r.status
 if len(data)>1048576 or status!=200:return False
 value=json.loads(data,object_pairs_hook=pairs)
 if not isinstance(value,dict) or set(value)!={'total_count','runners'} or value['total_count']!=len(value['runners']):return False
 runners=value['runners']; found=[x for x in runners if x.get('name')==runner]; labels={x.get('name') for x in found[0].get('labels',[])} if len(found)==1 else set(); unique=len({(x.get('id'),x.get('name')) for x in runners})==len(runners)
 if not (unique and len(found)==1 and found[0].get('status')=='online' and required<=labels):return False
 return {'repository':repository,'runner_id':found[0].get('id'),'runner_name':runner,'status':'online','labels':sorted(labels),'matching_count':1,'total_count':value['total_count']}
def main():
 p=argparse.ArgumentParser(); p.add_argument('--policy',required=True); a=p.parse_args(); policy=json.load(open(a.policy)); raw=sys.stdin.buffer.read(4097)
 if not 1<=len(raw)<=4096 or b'\n' in raw or b'\0' in raw:return 2
 token=raw.decode()
 try:
  result=verify(token,policy)
  if result: print(json.dumps(result,sort_keys=True,separators=(',',':')))
  return 0 if result else 2
 except (OSError,ValueError,json.JSONDecodeError):return 2
 finally:token='';raw=b''
if __name__=='__main__':raise SystemExit(main())
