#!/usr/bin/env python3
"""Authenticated archive-only GitHub materializer; never executes or extracts source."""
from __future__ import annotations
import argparse, hashlib, json, os, ssl, sys, urllib.error, urllib.request
from pathlib import Path

try:
    from scripts.verify_source_archive import ArchiveError, verify_archive
except ModuleNotFoundError:  # direct trusted-controller invocation
    from verify_source_archive import ArchiveError, verify_archive

class MaterializeError(ValueError): pass
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl): return None

def fetch(url: str, token: str, *, limit: int) -> bytes:
    if not url.startswith("https://api.github.com/"): raise MaterializeError("ARCHIVE_HOST_FORBIDDEN")
    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ssl.create_default_context()), NoRedirect)
    request = urllib.request.Request(url, headers={"Accept":"application/vnd.github+json","Authorization":f"Bearer {token}","X-GitHub-Api-Version":"2022-11-28"})
    try:
        with opener.open(request, timeout=30) as response:
            data = response.read(limit + 1)
    except urllib.error.HTTPError as exc:
        if 300 <= exc.code < 400:
            location = exc.headers.get("Location", "")
            if not location.startswith("https://codeload.github.com/"):
                raise MaterializeError("ARCHIVE_REDIRECT_FORBIDDEN") from exc
            # Deliberately omit Authorization on the frozen cross-host redirect.
            clean = urllib.request.Request(location, headers={"Accept":"application/octet-stream"})
            try:
                with opener.open(clean, timeout=30) as response:
                    data = response.read(limit + 1)
            except urllib.error.URLError as redirected:
                raise MaterializeError("ARCHIVE_HTTP_ERROR") from redirected
        else:
            raise MaterializeError("ARCHIVE_HTTP_ERROR") from exc
    if len(data) > limit: raise MaterializeError("ARCHIVE_RESPONSE_LIMIT")
    return data

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--repository",required=True); p.add_argument("--sha",required=True); p.add_argument("--expected-tree",required=True); p.add_argument("--tree-projection",type=Path,required=True); p.add_argument("--output",type=Path,required=True); a=p.parse_args(argv)
    token=os.environ.get("GITHUB_TOKEN","")
    if not token: print("SOURCE_CONTROLLER_ERROR:TOKEN_MISSING",file=sys.stderr); return 2
    try:
        if a.tree_projection.stat().st_size > 16 * 1024 * 1024: raise MaterializeError("TREE_PROJECTION_LIMIT")
        projection=json.loads(a.tree_projection.read_text(encoding="utf-8"))
        raw=fetch(f"https://api.github.com/repos/{a.repository}/tarball/{a.sha}", token, limit=300*1024*1024)
        result=verify_archive(raw, projection, expected_tree=a.expected_tree)
        a.output.write_text(json.dumps(result,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")
        return 0
    except (OSError,json.JSONDecodeError,ArchiveError,MaterializeError) as exc:
        print(f"SOURCE_CONTROLLER_ERROR:{exc}",file=sys.stderr); return 2
    finally:
        token=""
if __name__=="__main__": raise SystemExit(main())
