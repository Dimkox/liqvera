import io
import tarfile

import pytest
import urllib.error

from scripts.verify_source_archive import ArchiveError, verify_archive
from scripts.materialize_exact_source_archive import MaterializeError, fetch


def archive(entries):
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode="w:gz") as tf:
        for name, body, kind in entries:
            info = tarfile.TarInfo(name)
            if kind == "file":
                data = body.encode(); info.size = len(data); info.mode = 0o100644; tf.addfile(info, io.BytesIO(data))
            else:
                info.type = tarfile.SYMTYPE; info.linkname = body; tf.addfile(info)
    return out.getvalue()


def test_verifies_exact_blob_projection():
    import hashlib
    body = b"ok\n"
    oid = hashlib.sha1(b"blob 3\0" + body).hexdigest()
    result = verify_archive(archive([("root/a.txt", "ok\n", "file")]), {"a.txt": {"mode": "100644", "type": "blob", "oid": oid}})
    assert result["member_count"] == 1


@pytest.mark.parametrize("name", ["root/../x", "/root/x", "root/A", "root/a"])
def test_rejects_unsafe_or_colliding_members(name):
    entries = [("root/a", "x", "file"), (name, "y", "file")] if name != "root/a" else [("root/a", "x", "file"), ("root/a", "y", "file")]
    with pytest.raises(ArchiveError): verify_archive(archive(entries), {})


def test_rejects_links():
    with pytest.raises(ArchiveError, match="ARCHIVE_MEMBER_TYPE_FORBIDDEN"):
        verify_archive(archive([("root/link", "target", "link")]), {})


@pytest.mark.parametrize("typecode", [tarfile.LNKTYPE, tarfile.CHRTYPE, tarfile.BLKTYPE, tarfile.FIFOTYPE])
def test_rejects_all_special_member_types(typecode):
    out=io.BytesIO()
    with tarfile.open(fileobj=out,mode="w:gz") as tf:
        info=tarfile.TarInfo("root/special"); info.type=typecode; info.linkname="target"; tf.addfile(info)
    with pytest.raises(ArchiveError,match="ARCHIVE_MEMBER_TYPE_FORBIDDEN"): verify_archive(out.getvalue(),{})


@pytest.mark.parametrize("kwargs,code", [({"max_members":0},"ARCHIVE_MEMBER_LIMIT"),({"max_total":0},"ARCHIVE_EXPANDED_LIMIT"),({"max_member":0},"ARCHIVE_MEMBER_LIMIT")])
def test_archive_bounds_fail_closed(kwargs,code):
    with pytest.raises(ArchiveError,match=code): verify_archive(archive([("root/a","x","file")]),{},**kwargs)


def test_rejects_submodule_symlink_projection_and_file_directory_collision():
    with pytest.raises(ArchiveError,match="PROJECTION_MEMBER_FORBIDDEN"): verify_archive(archive([("root/a","x","file")]),{"a":{"mode":"160000","type":"commit","oid":"a"*40}})
    with pytest.raises(ArchiveError,match="PROJECTION_MEMBER_FORBIDDEN"): verify_archive(archive([("root/a","x","file")]),{"a":{"mode":"120000","type":"blob","oid":"a"*40}})
    with pytest.raises(ArchiveError,match="ARCHIVE_FILE_DIRECTORY_COLLISION"): verify_archive(archive([("root/a","x","file"),("root/a/b","y","file")]),{})


def test_rejects_unicode_normalization_collision():
    with pytest.raises(ArchiveError,match="ARCHIVE_PATH_COLLISION"):
        verify_archive(archive([("root/café","x","file"),("root/cafe\u0301","y","file")]),{})


def test_redirect_is_frozen_to_codeload_and_strips_authorization(monkeypatch):
    class Response:
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def read(self,size): return b"archive"
    class Opener:
        def __init__(self): self.requests=[]
        def open(self,request,timeout):
            self.requests.append(request)
            if len(self.requests)==1:
                raise urllib.error.HTTPError(request.full_url,302,"redirect",{"Location":"https://codeload.github.com/o/r/tar.gz/a"},None)
            return Response()
    opener=Opener(); monkeypatch.setattr("scripts.materialize_exact_source_archive.urllib.request.build_opener",lambda *args: opener)
    assert fetch("https://api.github.com/repos/o/r/tarball/"+"a"*40,"secret",limit=20)==b"archive"
    assert "Authorization" in opener.requests[0].headers and "Authorization" not in opener.requests[1].headers


def test_redirect_to_unfrozen_host_fails(monkeypatch):
    class Opener:
        def open(self,request,timeout): raise urllib.error.HTTPError(request.full_url,302,"redirect",{"Location":"https://evil.invalid/x"},None)
    monkeypatch.setattr("scripts.materialize_exact_source_archive.urllib.request.build_opener",lambda *args: Opener())
    with pytest.raises(MaterializeError,match="ARCHIVE_REDIRECT_FORBIDDEN"): fetch("https://api.github.com/repos/o/r/tarball/"+"a"*40,"secret",limit=20)
