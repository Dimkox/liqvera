#!/usr/bin/env python3
"""Fused verification and atomic extraction of the exact authenticated archive bytes."""
from __future__ import annotations
import argparse, io, json, os, shutil, sys, tarfile, tempfile
from pathlib import Path
from scripts.materialize_exact_source_archive import MaterializeError as FetchError, fetch
from scripts.verify_source_archive import ArchiveError,verify_archive

class MaterializationError(ValueError): pass
def _write_all(fd:int,data:bytes):
    view=memoryview(data)
    while view:
        written=os.write(fd,view)
        if written<=0: raise MaterializationError("ARCHIVE_MEMBER_WRITE_FAILED")
        view=view[written:]
def materialize_verified_tree(raw:bytes,projection:dict,expected_tree:str,destination:Path):
    if destination.exists(): raise MaterializationError("DESTINATION_EXISTS")
    try: result=verify_archive(raw,projection,expected_tree=expected_tree)
    except ArchiveError as exc: raise MaterializationError(str(exc)) from exc
    destination.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix=".verified-source-",dir=destination.parent))
    try:
        with tarfile.open(fileobj=io.BytesIO(raw),mode="r:*") as tf:
            root=tf.getmembers()[0].name.split("/")[0]
            for member in tf.getmembers():
                parts=member.name.split("/")
                if len(parts)==1 or member.isdir(): continue
                rel=Path(*parts[1:]); target=stage/rel; target.parent.mkdir(parents=True,exist_ok=True)
                source=tf.extractfile(member)
                if source is None: raise MaterializationError("ARCHIVE_MEMBER_UNREADABLE")
                fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o500 if member.mode&0o111 else 0o400)
                try: _write_all(fd,source.read()); os.fsync(fd)
                finally: os.close(fd)
        for directory,_,_ in os.walk(stage,topdown=False): os.chmod(directory,0o500)
        os.replace(stage,destination)
        if os.name=="posix":
            dfd=os.open(destination.parent,os.O_RDONLY)
            try: os.fsync(dfd)
            finally: os.close(dfd)
        return result
    except BaseException:
        shutil.rmtree(stage,ignore_errors=True); raise

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--repository",required=True); p.add_argument("--sha",required=True); p.add_argument("--expected-tree",required=True); p.add_argument("--tree-projection",type=Path,required=True); p.add_argument("--destination",type=Path,required=True); p.add_argument("--output",type=Path,required=True); a=p.parse_args(argv)
    token=os.environ.get("GITHUB_TOKEN","")
    if not token: print("SOURCE_CONTROLLER_ERROR:TOKEN_MISSING",file=sys.stderr); return 2
    try:
        projection=json.loads(a.tree_projection.read_text(encoding="utf-8"))
        raw=fetch(f"https://api.github.com/repos/{a.repository}/tarball/{a.sha}",token,limit=300*1024*1024)
        result=materialize_verified_tree(raw,projection,a.expected_tree,a.destination)
        a.output.write_text(json.dumps(result,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8"); return 0
    except (OSError,json.JSONDecodeError,MaterializationError,FetchError) as exc:
        print(f"SOURCE_CONTROLLER_ERROR:{exc}",file=sys.stderr); return 2
    finally: token=""
if __name__=="__main__": raise SystemExit(main())
