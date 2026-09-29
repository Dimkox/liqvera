"""Fail-closed authority contract for F7 allowlisted public reads.

This module validates authority and transport boundaries.  It deliberately
does not obtain authority from environment variables and performs no I/O at
import time.
"""

from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit


class GrantError(ValueError):
    """Stable public-read stop reason without reflecting untrusted input."""


_OID = re.compile(r"[0-9a-f]{40}\Z")
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_ALLOWED = {
    ("A07", "POST", "https://api.hyperliquid.xyz/info"),
    ("A07", "POST", "https://rpc.test.mezo.org"),
    ("A07", "GET", "https://facilitator.vativ.io/supported"),
    ("A29", "GET", "https://github.com/Dimkox/liqvera.git/info/refs?service=git-upload-pack"),
}
_FIELDS = {
    "schema", "subject_commit", "subject_tree", "plan_sha256", "case", "method",
    "url", "expires_at", "maximum_attempts", "timeout_seconds", "max_response_bytes",
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


@dataclass(frozen=True)
class PublicReadGrant:
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

    @classmethod
    def parse(cls, raw: object, *, now: datetime) -> "PublicReadGrant":
        if not isinstance(raw, dict) or set(raw) != _FIELDS or raw.get("schema") != "liqvera-public-read-grant/v1":
            raise GrantError("PUBLIC_READ_GRANT_INVALID")
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
        if any(type(value) is not int for value in limits) or not (1 <= limits[0] <= 2 and 1 <= limits[1] <= 15 and 1 <= limits[2] <= 2_097_152):
            raise GrantError("PUBLIC_READ_GRANT_INVALID")
        return cls(values[0], values[1], values[2], case, method, url, expires, *limits)

    def authorize(self, plan: PublicReadPlan, *, subject_commit: str, subject_tree: str, plan_sha256: str) -> None:
        actual = (subject_commit, subject_tree, plan_sha256, plan.case, plan.method, plan.url,
                  plan.maximum_attempts, plan.timeout_seconds, plan.max_response_bytes)
        expected = (self.subject_commit, self.subject_tree, self.plan_sha256, self.case, self.method, self.url,
                    self.maximum_attempts, self.timeout_seconds, self.max_response_bytes)
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


def validate_public_read_evidence(grant: PublicReadGrant, raw: object, *, environ: dict[str, str]) -> dict[str, object]:
    """Reduce untrusted transport observations to closed A07/A29 evidence."""
    if any(name in environ for name in _AMBIENT_AUTHORITY):
        raise GrantError("PUBLIC_READ_AMBIENT_AUTHORITY")
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
