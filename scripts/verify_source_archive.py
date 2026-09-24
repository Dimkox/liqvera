#!/usr/bin/env python3
"""Verify a GitHub tar archive against an exact Git blob projection without extraction."""
from __future__ import annotations

import hashlib
import io
import posixpath
import re
import tarfile
import unicodedata


class ArchiveError(ValueError): pass


def _blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def reconstruct_tree(projection: dict[str, dict[str, str]]) -> str:
    root: dict[str, object] = {}
    for path, entry in projection.items():
        parts = path.split("/"); cursor = root
        for part in parts[:-1]: cursor = cursor.setdefault(part, {})  # type: ignore[assignment]
        cursor[parts[-1]] = entry
    def digest(node: dict[str, object]) -> str:
        encoded = bytearray()
        for name, value in sorted(node.items(), key=lambda item: item[0] + ("/" if isinstance(item[1], dict) else "")):
            if isinstance(value, dict) and "oid" not in value:
                mode, oid = "40000", digest(value)
            else:
                assert isinstance(value, dict); mode, oid = str(value["mode"]), str(value["oid"])
            encoded += f"{mode} {name}".encode() + b"\0" + bytes.fromhex(oid)
        return hashlib.sha1(b"tree " + str(len(encoded)).encode() + b"\0" + encoded).hexdigest()
    return digest(root)


def verify_archive(raw: bytes, projection: object, *, expected_tree: str | None = None, max_members: int = 10000,
                   max_total: int = 256 * 1024 * 1024, max_member: int = 32 * 1024 * 1024) -> dict[str, object]:
    if not isinstance(raw, bytes) or not raw: raise ArchiveError("ARCHIVE_EMPTY")
    if not isinstance(projection, dict): raise ArchiveError("PROJECTION_INVALID")
    for path, entry in projection.items():
        if not isinstance(path,str) or not path or path.startswith("/") or "\\" in path or any(part in {"",".",".."} for part in path.split("/")): raise ArchiveError("PROJECTION_PATH_INVALID")
        if not isinstance(entry,dict) or set(entry) != {"mode","type","oid"}: raise ArchiveError("PROJECTION_ENTRY_INVALID")
        if entry["type"] != "blob" or entry["mode"] not in {"100644","100755"}: raise ArchiveError("PROJECTION_MEMBER_FORBIDDEN")
        if not isinstance(entry["oid"],str) or not re.fullmatch(r"[0-9a-f]{40}",entry["oid"]):
            raise ArchiveError("PROJECTION_OID_INVALID")
    actual, folded, total, root = {}, set(), 0, None
    try:
        tf = tarfile.open(fileobj=io.BytesIO(raw), mode="r:*")
    except tarfile.TarError as exc: raise ArchiveError("ARCHIVE_FORMAT_INVALID") from exc
    with tf:
        members = tf.getmembers()
        if len(members) > max_members: raise ArchiveError("ARCHIVE_MEMBER_LIMIT")
        for member in members:
            name = unicodedata.normalize("NFC", member.name)
            if name.startswith("/") or "\\" in name: raise ArchiveError("ARCHIVE_PATH_INVALID")
            parts = name.split("/")
            if any(p in {"", ".", ".."} for p in parts): raise ArchiveError("ARCHIVE_PATH_INVALID")
            root = root or parts[0]
            if parts[0] != root: raise ArchiveError("ARCHIVE_ROOT_MISMATCH")
            if len(parts) == 1 and member.isdir(): continue
            rel = posixpath.join(*parts[1:])
            if not rel or member.isdir(): continue
            key = rel.casefold()
            if key in folded: raise ArchiveError("ARCHIVE_PATH_COLLISION")
            if any(rel.startswith(existing + "/") or existing.startswith(rel + "/") for existing in actual): raise ArchiveError("ARCHIVE_FILE_DIRECTORY_COLLISION")
            folded.add(key)
            if not member.isfile(): raise ArchiveError("ARCHIVE_MEMBER_TYPE_FORBIDDEN")
            if member.size > max_member: raise ArchiveError("ARCHIVE_MEMBER_LIMIT")
            total += member.size
            if total > max_total: raise ArchiveError("ARCHIVE_EXPANDED_LIMIT")
            fileobj = tf.extractfile(member)
            if fileobj is None: raise ArchiveError("ARCHIVE_MEMBER_UNREADABLE")
            data = fileobj.read(max_member + 1)
            mode = "100755" if member.mode & 0o111 else "100644"
            actual[rel] = {"mode": mode, "type": "blob", "oid": _blob(data)}
    if actual != projection: raise ArchiveError("ARCHIVE_TREE_PROJECTION_MISMATCH")
    tree = reconstruct_tree(actual)
    if expected_tree is not None and tree != expected_tree: raise ArchiveError("ARCHIVE_ROOT_TREE_MISMATCH")
    return {"archive_sha256": hashlib.sha256(raw).hexdigest(), "tree": tree, "member_count": len(actual), "expanded_bytes": total}
