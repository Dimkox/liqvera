import io, tarfile
from pathlib import Path

import pytest

from scripts.materialize_verified_source_tree import MaterializationError, materialize_verified_tree
from scripts.verify_source_archive import _blob, reconstruct_tree


def archive(name="root/a.txt", data=b"ok"):
    out=io.BytesIO()
    with tarfile.open(fileobj=out,mode="w:gz") as tf:
        i=tarfile.TarInfo(name); i.size=len(data); i.mode=0o644; tf.addfile(i,io.BytesIO(data))
    return out.getvalue()


def test_verified_bytes_are_atomically_extracted_read_only(tmp_path):
    projection={"a.txt":{"mode":"100644","type":"blob","oid":_blob(b"ok")}}
    result=materialize_verified_tree(archive(),projection,reconstruct_tree(projection),tmp_path/"source")
    assert (tmp_path/"source"/"a.txt").read_bytes()==b"ok"
    assert result["tree"]==reconstruct_tree(projection)


def test_rejects_projection_mismatch_before_destination_exists(tmp_path):
    projection={"a.txt":{"mode":"100644","type":"blob","oid":_blob(b"no")}}
    with pytest.raises(MaterializationError): materialize_verified_tree(archive(),projection,reconstruct_tree(projection),tmp_path/"source")
    assert not (tmp_path/"source").exists()
