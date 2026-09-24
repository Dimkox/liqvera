"""Small closed-schema atomic receipt primitive for trusted controller writers."""
from __future__ import annotations
import json, os, re, tempfile
from pathlib import Path

class ReceiptError(ValueError): pass
def validate(value,fields,schema_version):
    if not isinstance(value,dict): raise ReceiptError("RECEIPT_NOT_OBJECT")
    if set(value)-fields: raise ReceiptError("RECEIPT_UNKNOWN_FIELD")
    if fields-set(value): raise ReceiptError("RECEIPT_MISSING_FIELD")
    if value.get("schema_version")!=schema_version: raise ReceiptError("RECEIPT_SCHEMA_INVALID")
    if "repository" in value and not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+",str(value["repository"])): raise ReceiptError("RECEIPT_REPOSITORY_INVALID")
    for key,item in value.items():
        if key in {"head_sha","head_tree","controller_sha","controller_tree","workflow_blob_sha","probe_head_sha","probe_head_tree"} and not re.fullmatch(r"[0-9a-f]{40}",str(item)): raise ReceiptError("RECEIPT_GIT_IDENTITY_INVALID")
        if (key.endswith("_sha256") or key.endswith("_digest")) and key!="image_digest" and not re.fullmatch(r"[0-9a-f]{64}",str(item)): raise ReceiptError("RECEIPT_DIGEST_INVALID")
        if key in {"pr_number","run_id","run_attempt"} and (not isinstance(item,int) or isinstance(item,bool) or item<1): raise ReceiptError("RECEIPT_INTEGER_INVALID")
        if key in {"job","shard"} and not re.fullmatch(r"[a-z0-9-]{1,64}",str(item)): raise ReceiptError("RECEIPT_SCOPE_INVALID")
def atomic_write(value,path:Path):
    path.parent.mkdir(parents=True,exist_ok=True); data=(json.dumps(value,sort_keys=True,separators=(",",":"))+"\n").encode()
    fd,name=tempfile.mkstemp(prefix=".receipt-",dir=path.parent)
    try:
        os.fchmod(fd,0o600); os.write(fd,data); os.fsync(fd); os.close(fd); os.replace(name,path)
    except BaseException:
        try: os.close(fd)
        except OSError: pass
        try: os.unlink(name)
        except OSError: pass
        raise
def read(path:Path,limit=131072):
    if path.stat().st_size>limit: raise ReceiptError("RECEIPT_TOO_LARGE")
    return json.loads(path.read_text(encoding="utf-8"))
