"""Fail-closed authority contract for F7 allowlisted public reads.

This module validates authority and transport boundaries.  It deliberately
does not obtain authority from environment variables and performs no I/O at
import time.
"""

from __future__ import annotations

import ipaddress
import hashlib
import http.client
import json
import os
import re
import socket
import ssl
import stat
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit


class GrantError(ValueError):
    """Stable public-read stop reason without reflecting untrusted input."""


_OID = re.compile(r"[0-9a-f]{40}\Z")
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_ALLOWED = {
    # Transport primitive characterization only; the acceptance runner never
    # treats this response as A07 semantic evidence.
    ("A07", "POST", "https://api.hyperliquid.xyz/info"),
    ("A07", "LOCAL_POST", "https://source.invalid/internal/v1/reports"),
    ("A29", "GIT_CLONE", "https://github.com/Dimkox/liqvera.git"),
}
_FIELDS = {
    "schema", "grant_id", "subject_commit", "subject_tree", "plan_sha256", "case", "method",
    "url", "expires_at", "maximum_attempts", "timeout_seconds", "max_response_bytes", "body_sha256",
}
_AMBIENT_AUTHORITY = {"HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY", "http_proxy", "https_proxy", "all_proxy", "no_proxy", "NETRC"}


@dataclass(frozen=True)
class PublicReadPlan:
    case: str
    method: str
    url: str
    body: bytes
    timeout_seconds: int
    max_response_bytes: int
    maximum_attempts: int

    @property
    def body_sha256(self) -> str:
        return hashlib.sha256(self.body).hexdigest()

    @property
    def digest(self) -> str:
        value={"case":self.case,"method":self.method,"url":self.url,"body_sha256":self.body_sha256,
               "timeout_seconds":self.timeout_seconds,"max_response_bytes":self.max_response_bytes,
               "maximum_attempts":self.maximum_attempts}
        return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":")).encode()).hexdigest()


@dataclass(frozen=True)
class PublicReadGrant:
    grant_id: str
    subject_commit: str
    subject_tree: str
    plan_sha256: str
    case: str
    method: str
    url: str
    expires_at: datetime
    maximum_attempts: int
    timeout_seconds: int
    max_response_bytes: int
    body_sha256: str

    @classmethod
    def parse(cls, raw: object, *, now: datetime) -> "PublicReadGrant":
        if not isinstance(raw, dict) or set(raw) != _FIELDS or raw.get("schema") != "liqvera-public-read-grant/v1":
            raise GrantError("PUBLIC_READ_GRANT_INVALID")
        grant_id = raw.get("grant_id")
        try:
            if not isinstance(grant_id, str) or str(uuid.UUID(grant_id)) != grant_id:
                raise ValueError
        except ValueError:
            raise GrantError("PUBLIC_READ_GRANT_INVALID") from None
        values = (raw.get("subject_commit"), raw.get("subject_tree"), raw.get("plan_sha256"))
        if not all(isinstance(value, str) for value in values) or not _OID.fullmatch(values[0]) or not _OID.fullmatch(values[1]) or not _DIGEST.fullmatch(values[2]):
            raise GrantError("PUBLIC_READ_GRANT_INVALID")
        case, method, url = raw.get("case"), raw.get("method"), raw.get("url")
        if not all(isinstance(value, str) for value in (case, method, url)):
            raise GrantError("PUBLIC_READ_GRANT_INVALID")
        parsed = urlsplit(url)
        if parsed.scheme != "https":
            raise GrantError("PUBLIC_READ_TLS_REQUIRED")
        if parsed.username or parsed.password or parsed.port not in (None, 443) or (case, method, url) not in _ALLOWED:
            raise GrantError("PUBLIC_READ_DESTINATION_FORBIDDEN")
        try:
            expires = datetime.fromisoformat(str(raw["expires_at"]).replace("Z", "+00:00"))
        except (ValueError, TypeError):
            raise GrantError("PUBLIC_READ_GRANT_INVALID") from None
        if expires.tzinfo is None or expires <= now or expires > now + timedelta(minutes=15):
            raise GrantError("PUBLIC_READ_GRANT_EXPIRED")
        limits = (raw.get("maximum_attempts"), raw.get("timeout_seconds"), raw.get("max_response_bytes"))
        maximum_bytes = 52_428_800 if case == "A29" else 2_097_152
        if any(type(value) is not int for value in limits) or not (limits[0] == 1 and 1 <= limits[1] <= 15 and 1 <= limits[2] <= maximum_bytes):
            raise GrantError("PUBLIC_READ_GRANT_INVALID")
        body_sha256=raw.get("body_sha256")
        if not isinstance(body_sha256,str) or not _DIGEST.fullmatch(body_sha256):
            raise GrantError("PUBLIC_READ_GRANT_INVALID")
        return cls(grant_id, values[0], values[1], values[2], case, method, url, expires, *limits, body_sha256)

    @property
    def digest(self) -> str:
        value = {
            "schema": "liqvera-public-read-grant/v1", "grant_id": self.grant_id,
            "subject_commit": self.subject_commit, "subject_tree": self.subject_tree,
            "plan_sha256": self.plan_sha256, "case": self.case, "method": self.method,
            "url": self.url, "expires_at": self.expires_at.isoformat().replace("+00:00", "Z"),
            "maximum_attempts": self.maximum_attempts, "timeout_seconds": self.timeout_seconds,
            "max_response_bytes": self.max_response_bytes, "body_sha256": self.body_sha256,
        }
        return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    def authorize(self, plan: PublicReadPlan, *, subject_commit: str, subject_tree: str, now: datetime) -> None:
        if now >= self.expires_at:
            raise GrantError("PUBLIC_READ_GRANT_EXPIRED")
        actual = (subject_commit, subject_tree, plan.digest, plan.case, plan.method, plan.url,
                  plan.maximum_attempts, plan.timeout_seconds, plan.max_response_bytes,plan.body_sha256)
        expected = (self.subject_commit, self.subject_tree, self.plan_sha256, self.case, self.method, self.url,
                    self.maximum_attempts, self.timeout_seconds, self.max_response_bytes,self.body_sha256)
        if actual != expected:
            raise GrantError("PUBLIC_READ_GRANT_MISMATCH")

    def validate_resolution(self, before: tuple[str, ...], connected: tuple[str, ...]) -> None:
        if not before or set(before) != set(connected):
            raise GrantError("PUBLIC_READ_DNS_REBINDING")
        for value in before:
            try:
                address = ipaddress.ip_address(value)
            except ValueError:
                raise GrantError("PUBLIC_READ_PRIVATE_ADDRESS") from None
            if not address.is_global:
                raise GrantError("PUBLIC_READ_PRIVATE_ADDRESS")


def validate_public_read_evidence(grant: PublicReadGrant, raw: object, *, environ: dict[str, str],now:datetime) -> dict[str, object]:
    """Reduce untrusted transport observations to closed A07/A29 evidence."""
    if any(name in environ for name in _AMBIENT_AUTHORITY):
        raise GrantError("PUBLIC_READ_AMBIENT_AUTHORITY")
    if now>=grant.expires_at:
        raise GrantError("PUBLIC_READ_GRANT_EXPIRED")
    fields={"status","final_url","response_bytes","response_sha256","resolved_addresses","connected_address","attempts"}
    if not isinstance(raw,dict) or set(raw)!=fields or raw.get("status")!=200:
        raise GrantError("PUBLIC_READ_EVIDENCE_INVALID")
    if raw.get("final_url")!=grant.url:
        raise GrantError("PUBLIC_READ_REDIRECT_BLOCKED")
    size=raw.get("response_bytes"); attempts=raw.get("attempts")
    if type(size) is not int or size<0 or size>grant.max_response_bytes:
        raise GrantError("PUBLIC_READ_RESPONSE_TOO_LARGE")
    if type(attempts) is not int or attempts<1 or attempts>grant.maximum_attempts or not isinstance(raw.get("response_sha256"),str) or not _DIGEST.fullmatch(raw["response_sha256"]):
        raise GrantError("PUBLIC_READ_EVIDENCE_INVALID")
    addresses=raw.get("resolved_addresses"); connected=raw.get("connected_address")
    if not isinstance(addresses,list) or not all(isinstance(value,str) for value in addresses) or not isinstance(connected,str):
        raise GrantError("PUBLIC_READ_EVIDENCE_INVALID")
    grant.validate_resolution(tuple(addresses),(connected,))
    return {"case":grant.case,"method":grant.method,"url":grant.url,"status":200,"response_bytes":size,
            "response_sha256":raw["response_sha256"],"attempts":attempts}


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self,host:str,address:str,timeout:int):
        super().__init__(host,443,timeout=timeout,context=ssl.create_default_context())
        self._address=address
    def connect(self)->None:
        raw=socket.create_connection((self._address,443),self.timeout)
        self.sock=self._context.wrap_socket(raw,server_hostname=self.host)


def _resolve(host:str)->tuple[str,...]:
    return tuple(sorted({item[4][0] for item in socket.getaddrinfo(host,443,type=socket.SOCK_STREAM)}))


def consume_public_read_grant(state_dir, grant:PublicReadGrant)->str:
    state_dir = os.fspath(state_dir)
    info = os.lstat(state_dir)
    if not stat.S_ISDIR(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o700:
        raise GrantError("PUBLIC_READ_STATE_DIR_INVALID")
    identity = hashlib.sha256(f"{info.st_dev}:{info.st_ino}".encode()).hexdigest()
    marker = hashlib.sha256(f"{grant.grant_id}:{grant.digest}".encode()).hexdigest()
    path = os.path.join(state_dir, marker)
    try:
        descriptor=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o400)
    except FileExistsError:
        raise GrantError("PUBLIC_READ_GRANT_ALREADY_CONSUMED") from None
    try:
        os.write(descriptor,(grant.digest+"\n").encode());os.fsync(descriptor)
    finally: os.close(descriptor)
    directory = os.open(state_dir, os.O_RDONLY | os.O_DIRECTORY)
    try: os.fsync(directory)
    finally: os.close(directory)
    return identity


def execute_public_read(plan:PublicReadPlan,grant:PublicReadGrant,*,subject_commit:str,subject_tree:str,now,
                        environ:dict[str,str],resolver=_resolve,connection=_PinnedHTTPSConnection,state_dir)->dict[str,object]:
    """Perform one exact HTTPS read through a directly connected validated IP."""
    grant.authorize(plan,subject_commit=subject_commit,subject_tree=subject_tree,now=now())
    if any(name in environ for name in _AMBIENT_AUTHORITY): raise GrantError("PUBLIC_READ_AMBIENT_AUTHORITY")
    parsed=urlsplit(plan.url); before=tuple(resolver(parsed.hostname)); grant.validate_resolution(before,before)
    connected=tuple(resolver(parsed.hostname)); grant.validate_resolution(before,connected)
    if now()>=grant.expires_at: raise GrantError("PUBLIC_READ_GRANT_EXPIRED")
    state_identity = consume_public_read_grant(state_dir,grant)
    client=connection(parsed.hostname,connected[0],plan.timeout_seconds)
    try:
        path=parsed.path+(f"?{parsed.query}" if parsed.query else "")
        client.request(plan.method,path,body=plan.body,headers={"Host":parsed.hostname,"Accept":"application/json","Content-Type":"application/json","Connection":"close"})
        response=client.getresponse()
        if 300<=response.status<400: raise GrantError("PUBLIC_READ_REDIRECT_BLOCKED")
        if response.status!=200: raise GrantError("PUBLIC_READ_HTTP_STATUS")
        chunks=[];size=0
        while True:
            chunk=response.read(min(65536,plan.max_response_bytes-size+1))
            if not chunk: break
            size+=len(chunk)
            if size>plan.max_response_bytes: raise GrantError("PUBLIC_READ_RESPONSE_TOO_LARGE")
            chunks.append(chunk)
        if now()>=grant.expires_at: raise GrantError("PUBLIC_READ_GRANT_EXPIRED")
        raw=b"".join(chunks)
        evidence={"status":200,"final_url":plan.url,"response_bytes":len(raw),"response_sha256":hashlib.sha256(raw).hexdigest(),
                  "resolved_addresses":list(before),"connected_address":connected[0],"attempts":1}
        reduced = validate_public_read_evidence(grant,evidence,environ=environ,now=now())
        return {**reduced, "grant_id": grant.grant_id, "grant_digest": grant.digest,
                "plan_sha256": plan.digest, "subject_commit": subject_commit,
                "subject_tree": subject_tree, "state_dir_identity": state_identity}
    finally: client.close()
