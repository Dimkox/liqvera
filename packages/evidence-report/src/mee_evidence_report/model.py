"""Frozen public models for the fixture-only MVP report builder."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from uuid import UUID

from mee_contracts.exact import ExactDecimal
from mee_readonly_analyzer.vwap import Side


@dataclass(frozen=True, slots=True)
class MvpReportRequest:
    """All caller-supplied nondeterminism for one simulated report."""

    report_id: UUID
    side: Side
    quantity_base: ExactDecimal
    created_at_ms: int | None = None
    engine_commit: str = "0" * 40

    def __post_init__(self) -> None:
        if type(self.report_id) is not UUID:
            raise TypeError("report_id must be UUID")
        if type(self.side) is not Side:
            raise TypeError("side must be Side")
        if type(self.quantity_base) is not ExactDecimal:
            raise TypeError("quantity_base must be ExactDecimal")
        if self.quantity_base.scaled <= 0:
            raise ValueError("quantity_base must be positive")
        if self.created_at_ms is not None and type(self.created_at_ms) is not int:
            raise TypeError("created_at_ms must be int or None")
        if (
            type(self.engine_commit) is not str
            or len(self.engine_commit) != 40
            or any(character not in "0123456789abcdef" for character in self.engine_commit)
        ):
            raise ValueError("engine_commit must be 40 lowercase hexadecimal characters")


@dataclass(frozen=True, slots=True)
class BuiltMvpReport:
    """A report document, its canonical bytes, and the external byte digest."""

    document: dict[str, object]
    report_bytes: bytes
    report_sha256: str

    def __post_init__(self) -> None:
        if type(self.document) is not dict:
            raise TypeError("document must be dict")
        if type(self.report_bytes) is not bytes:
            raise TypeError("report_bytes must be bytes")
        if hashlib.sha256(self.report_bytes).hexdigest() != self.report_sha256:
            raise ValueError("report_sha256 does not match report_bytes")


class MvpReportRejected(ValueError):
    """Typed fail-closed outcome when no MVP report may be produced."""

    def __init__(self, code: str) -> None:
        if type(code) is not str or not code:
            raise TypeError("rejection code must be a nonempty string")
        self.code = code
        super().__init__(code)
