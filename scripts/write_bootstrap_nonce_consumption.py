#!/usr/bin/env python3
"""Trusted exclusive writer for a single bootstrap nonce consumption claim."""
from __future__ import annotations
import datetime, hashlib, json, os, re, stat, sys, urllib.request
from pathlib import Path
try:
    from verify_github_bootstrap_approval import verify_approval_comment
except ModuleNotFoundError:
    from scripts.verify_github_bootstrap_approval import verify_approval_comment

SHA1=re.compile(r"^[0-9a-f]{40}$"); SHA256=re.compile(r"^[0-9a-f]{64}$")
APPROVAL_FIELDS={"decision","repository","pr_number","commit_id","head_tree","base_sha","controller_sha","controller_tree","workflow_path","workflow_blob_sha","allowed_paths","checks","expires_at","nonce"}
IDENTITY_FIELDS={"repository","default_branch","controller_sha","controller_tree","workflow_path","workflow_blob_sha","helper_sha256","policy_sha256","image_digest","actionlint_sha256","reconciler_sha256","service_sha256","sudoers_sha256"}
ENVELOPE_FIELDS={"token","repository","pr_number","comment_id","run_id","run_attempt","job_id"}
FIELDS={"schema_version","repository","approval_comment_id","approval_body_sha256","nonce","controller_sha","controller_tree","probe_pr_number","probe_head_sha","probe_head_tree","run_id","run_attempt","runner_name","consumed_at","status"}
class ConsumptionError(ValueError): pass

def validate_consumption(value):
    if not isinstance(value,dict): raise ConsumptionError("CONSUMPTION_NOT_OBJECT")
    if set(value)-FIELDS: raise ConsumptionError("CONSUMPTION_UNKNOWN_FIELD")
    if FIELDS-set(value): raise ConsumptionError("CONSUMPTION_MISSING_FIELD")
    if value["schema_version"]!="bootstrap-nonce-consumption-v1" or value["status"]!="CONSUMED": raise ConsumptionError("CONSUMPTION_SCHEMA_INVALID")
    if value["runner_name"]!="claw-engine-runner": raise ConsumptionError("CONSUMPTION_RUNNER_INVALID")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+",str(value["repository"])): raise ConsumptionError("CONSUMPTION_REPOSITORY_INVALID")
    if not SHA256.fullmatch(str(value["approval_body_sha256"])) or not re.fullmatch(r"[A-Za-z0-9_-]{43}",str(value["nonce"])): raise ConsumptionError("CONSUMPTION_APPROVAL_INVALID")
    for field in ("controller_sha","controller_tree","probe_head_sha","probe_head_tree"):
        if not SHA1.fullmatch(str(value[field])): raise ConsumptionError("CONSUMPTION_IDENTITY_INVALID")
    for field in ("approval_comment_id","probe_pr_number","run_id","run_attempt"):
        if not isinstance(value[field],int) or isinstance(value[field],bool) or value[field]<1: raise ConsumptionError("CONSUMPTION_INTEGER_INVALID")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z",str(value["consumed_at"])): raise ConsumptionError("CONSUMPTION_TIME_INVALID")

def write_consumption(value,path:Path):
    validate_consumption(value); path.parent.mkdir(parents=True,exist_ok=True)
    data=(json.dumps(value,sort_keys=True,separators=(",",":"))+"\n").encode()
    try: fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    except FileExistsError as exc: raise ConsumptionError("NONCE_ALREADY_CONSUMED") from exc
    try:
        view=memoryview(data)
        while view:
            written=os.write(fd,view)
            if written<=0: raise ConsumptionError("CONSUMPTION_WRITE_FAILED")
            view=view[written:]
        os.fsync(fd)
    finally: os.close(fd)
    if os.name=="posix":
        dfd=os.open(path.parent,os.O_RDONLY)
        try: os.fsync(dfd)
        finally: os.close(dfd)

def load_verified_claim(path:Path,digest:str,run_id:int,run_attempt:int):
    if path.is_symlink(): raise ConsumptionError("VERIFIED_CLAIM_SYMLINK")
    raw=path.read_bytes()
    if len(raw)>65536 or not SHA256.fullmatch(digest) or hashlib.sha256(raw).hexdigest()!=digest:
        raise ConsumptionError("VERIFIED_CLAIM_DIGEST_MISMATCH")
    value=json.loads(raw); validate_consumption(value)
    if value["run_id"]!=run_id or value["run_attempt"]!=run_attempt:
        raise ConsumptionError("CLAIM_RUN_MISMATCH")
    return value

def fetch_json(url:str,token:str):
    request=urllib.request.Request(url,headers={"Accept":"application/vnd.github+json","Authorization":f"Bearer {token}","X-GitHub-Api-Version":"2022-11-28"})
    with urllib.request.urlopen(request,timeout=30) as response:
        if response.status!=200: raise ConsumptionError("GITHUB_RESPONSE_INVALID")
        raw=response.read(1_048_577)
    if len(raw)>1_048_576: raise ConsumptionError("GITHUB_RESPONSE_TOO_LARGE")
    return json.loads(raw)

def verified_github_consumption(repository,pr_number,comment_id,run_id,run_attempt,job_id,state:Path,token:str):
    ident_path=state/"controller-identity.json"; info=ident_path.stat()
    if info.st_uid!=0 or stat.S_IMODE(info.st_mode)!=0o600: raise ConsumptionError("ROOT_CAPABILITY_INVALID")
    if not isinstance(token,str) or not 1<=len(token)<=4096 or any(c in token for c in "\r\n\0"): raise ConsumptionError("EPHEMERAL_TOKEN_INVALID")
    ident=json.loads(ident_path.read_text()); api=f"https://api.github.com/repos/{repository}"
    if set(ident)!=IDENTITY_FIELDS or ident.get("repository")!=repository or ident.get("default_branch")!="main" or ident.get("workflow_path")!=".github/workflows/run-claw-sandbox-probe.yml": raise ConsumptionError("CONTROLLER_IDENTITY_INVALID")
    repo=fetch_json(api,token); pr=fetch_json(f"{api}/pulls/{pr_number}",token); comment=fetch_json(f"{api}/issues/comments/{comment_id}",token)
    if repo.get("full_name")!=repository or pr.get("state")!="open" or pr.get("number")!=pr_number: raise ConsumptionError("GITHUB_IDENTITY_INVALID")
    if pr.get("base",{}).get("ref")!=ident["default_branch"] or pr.get("base",{}).get("sha")!=ident.get("controller_sha") or pr.get("base",{}).get("repo",{}).get("full_name")!=repository or pr.get("head",{}).get("repo",{}).get("full_name")!=repository: raise ConsumptionError("GITHUB_PR_BOUNDARY_INVALID")
    head=pr["head"]["sha"]; commit=fetch_json(f"{api}/commits/{head}",token); compare=fetch_json(f"{api}/compare/{ident['controller_sha']}...{head}",token)
    if compare.get("status") not in ("ahead","identical") or compare.get("merge_base_commit",{}).get("sha")!=ident["controller_sha"]: raise ConsumptionError("GITHUB_ANCESTRY_INVALID")
    owner=repo.get("owner",{})
    files=[]
    for page in range(1,4):
        part=fetch_json(f"{api}/pulls/{pr_number}/files?per_page=100&page={page}",token)
        if not isinstance(part,list): raise ConsumptionError("GITHUB_FILES_INVALID")
        files.extend(part)
        if len(part)<100: break
        if page==3: raise ConsumptionError("GITHUB_FILES_PAGINATION_LIMIT")
    paths=sorted(x.get("filename") for x in files)
    proof=verify_approval_comment(comment,expected_comment_id=comment_id,repository=repository,pr_number=pr_number,expected_head=head,expected_owner_login=owner["login"],expected_owner_id=owner["id"],expected_allowed_paths=paths,expected_checks=["claw-phase-b-probe"],now=datetime.datetime.now(datetime.timezone.utc),max_ttl=datetime.timedelta(hours=1),expected_decision="APPROVE_TOFU_SANDBOX_PHASE_B_PROBE",expected_workflow_path=ident["workflow_path"],expected_workflow_blob_sha=ident["workflow_blob_sha"])
    if proof["head_tree"]!=commit["commit"]["tree"]["sha"] or proof["base_sha"]!=ident["controller_sha"] or proof["controller_tree"]!=ident["controller_tree"]: raise ConsumptionError("GITHUB_APPROVAL_BINDING_INVALID")
    run=fetch_json(f"{api}/actions/runs/{run_id}",token); workflow=fetch_json(f"{api}/actions/workflows/{run.get('workflow_id')}",token); jobs=fetch_json(f"{api}/actions/runs/{run_id}/attempts/{run_attempt}/jobs?per_page=100",token)
    title=f"run-story-1-2-phase-b-probe pr={pr_number} head={head} comment={comment_id}"
    exact=[x for x in jobs.get("jobs",[]) if x.get("id")==job_id]
    if workflow.get("path")!=ident["workflow_path"] or run.get("name")!="Run exact Story 1.2 Phase B probe" or run.get("display_title")!=title or run.get("run_attempt")!=run_attempt or run.get("event")!="repository_dispatch" or run.get("head_sha")!=ident["controller_sha"] or run.get("repository",{}).get("full_name")!=repository or run.get("actor",{}).get("id")!=owner.get("id") or len(exact)!=1: raise ConsumptionError("GITHUB_RUN_IDENTITY_INVALID")
    job=exact[0]; labels=set(job.get("labels",[]))
    if job.get("run_id")!=run_id or job.get("run_attempt")!=run_attempt or job.get("name")!="probe" or job.get("status")!="in_progress" or job.get("runner_name")!="claw-engine-runner" or not {"self-hosted","claw","claw-engine-runner"}<=labels: raise ConsumptionError("GITHUB_JOB_IDENTITY_INVALID")
    value={"schema_version":"bootstrap-nonce-consumption-v1","repository":repository,"approval_comment_id":comment_id,"approval_body_sha256":proof["approval_body_sha256"],"nonce":proof["nonce"],"controller_sha":ident["controller_sha"],"controller_tree":ident["controller_tree"],"probe_pr_number":pr_number,"probe_head_sha":head,"probe_head_tree":commit["commit"]["tree"]["sha"],"run_id":run_id,"run_attempt":run_attempt,"runner_name":"claw-engine-runner","consumed_at":datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),"status":"CONSUMED"}
    validate_consumption(value); return value

def main(argv=None):
    args=sys.argv[1:] if argv is None else argv
    if args: print("NONCE_WRITER_ERROR:ARGV_FORBIDDEN",file=sys.stderr); return 2
    if os.name!="posix" or os.geteuid()!=0:
        print("NONCE_WRITER_ERROR:HOST_AUTHORITY_INVALID",file=sys.stderr); return 2
    state=Path("/var/lib/mee-controller")
    envelope=None
    try:
        raw=sys.stdin.buffer.read(16385)
        if len(raw)>16384: raise ConsumptionError("EPHEMERAL_ENVELOPE_TOO_LARGE")
        def closed_pairs(items):
            out={}
            for key,val in items:
                if key in out: raise ConsumptionError("EPHEMERAL_ENVELOPE_DUPLICATE")
                out[key]=val
            return out
        envelope=json.loads(raw,object_pairs_hook=closed_pairs)
        if not isinstance(envelope,dict) or set(envelope)!=ENVELOPE_FIELDS: raise ConsumptionError("EPHEMERAL_ENVELOPE_NOT_CLOSED")
        for field in ("pr_number","comment_id","run_id","run_attempt","job_id"):
            if not isinstance(envelope[field],int) or isinstance(envelope[field],bool) or envelope[field]<1: raise ConsumptionError("EPHEMERAL_ENVELOPE_ID_INVALID")
        value=verified_github_consumption(envelope["repository"],envelope["pr_number"],envelope["comment_id"],envelope["run_id"],envelope["run_attempt"],envelope["job_id"],state,envelope["token"])
        if value["approval_comment_id"]==5264583724: raise ConsumptionError("RETIRED_NONCE_FORBIDDEN")
        info=state.stat()
        if info.st_uid!=0 or stat.S_IMODE(info.st_mode) not in {0o700,0o750}: raise ConsumptionError("STATE_ROOT_AUTHORITY_INVALID")
        import fcntl
        lockfd=os.open(state/".nonce.lock",os.O_WRONLY|os.O_CREAT,0o600)
        try:
            fcntl.flock(lockfd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            name=hashlib.sha256(value["nonce"].encode()).hexdigest()+".json"
            write_consumption(value,state/name)
        finally: os.close(lockfd)
        print(name); return 0
    except (OSError,json.JSONDecodeError,ConsumptionError,BlockingIOError) as exc:
        print(f"NONCE_WRITER_ERROR:{exc}",file=sys.stderr); return 2
    finally:
        envelope=None

if __name__=="__main__": raise SystemExit(main())
