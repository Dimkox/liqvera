"""Closed Stage A decision document. No I/O and no GO."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

STAGE_A_DECISION_SCHEMA = "mee-stage-a-decision/v1"
STAGE_A_PACKAGE_SCHEMA = "mee-readonly-frozen-package/v1"


class StageADecisionCode(StrEnum):
    """PROD-002 closed set. GO, NO_GO, and KILL are not members."""

    INVALID_DATASET = "INVALID_DATASET"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    STOP = "STOP"
    EXTEND_LONGER_SHADOW = "EXTEND_LONGER_SHADOW"


class StageAReasonCode(StrEnum):
    """Reason codes for one decision class. STOP_* and EXTEND_* match that class."""

    INVALID_MEMBER_SET_MISMATCH = "INVALID_MEMBER_SET_MISMATCH"
    INVALID_MEMBER_HASH_MISMATCH = "INVALID_MEMBER_HASH_MISMATCH"
    INVALID_MANIFEST = "INVALID_MANIFEST"
    INVALID_RECORD = "INVALID_RECORD"
    INVALID_SYMLINK = "INVALID_SYMLINK"
    INVALID_UNSUPPORTED_VERSION = "INVALID_UNSUPPORTED_VERSION"
    INVALID_PATH = "INVALID_PATH"
    INSUFFICIENT_ACQUISITION_WINDOW = "INSUFFICIENT_ACQUISITION_WINDOW"
    INSUFFICIENT_COMPLETE_UTC_DAYS = "INSUFFICIENT_COMPLETE_UTC_DAYS"
    INSUFFICIENT_STRICT_HEALTHY_MINUTES = "INSUFFICIENT_STRICT_HEALTHY_MINUTES"
    INSUFFICIENT_INDEPENDENT_EPISODES = "INSUFFICIENT_INDEPENDENT_EPISODES"
    STOP_TOTAL_NET_NON_POSITIVE = "STOP_TOTAL_NET_NON_POSITIVE"
    STOP_MEDIAN_NET_NON_POSITIVE = "STOP_MEDIAN_NET_NON_POSITIVE"
    STOP_USD_1000_NET_NON_POSITIVE = "STOP_USD_1000_NET_NON_POSITIVE"
    STOP_USD_5000_NET_NEGATIVE = "STOP_USD_5000_NET_NEGATIVE"
    STOP_DELAY_300MS_NOT_SURVIVED = "STOP_DELAY_300MS_NOT_SURVIVED"
    STOP_DELAY_500MS_NOT_SURVIVED = "STOP_DELAY_500MS_NOT_SURVIVED"
    STOP_FEE_CASE_NOT_SURVIVED = "STOP_FEE_CASE_NOT_SURVIVED"
    STOP_CONCENTRATION_NOT_BELOW_25_PERCENT = "STOP_CONCENTRATION_NOT_BELOW_25_PERCENT"
    EXTEND_ALL_V2_GATES_PASS = "EXTEND_ALL_V2_GATES_PASS"


_REASON_INDEX = {code: index for index, code in enumerate(StageAReasonCode)}

_DECISION_CLASS = {
    StageADecisionCode.INVALID_DATASET: "INVALID",
    StageADecisionCode.INSUFFICIENT_EVIDENCE: "INSUFFICIENT",
    StageADecisionCode.STOP: "STOP",
    StageADecisionCode.EXTEND_LONGER_SHADOW: "EXTEND",
}


def _reason_class(reason: StageAReasonCode) -> str:
    value = reason.value
    for prefix in ("INVALID_", "INSUFFICIENT_", "STOP_", "EXTEND_"):
        if value.startswith(prefix):
            return prefix[:-1]
    raise ValueError(f"reason {value} has no class prefix")


@dataclass(frozen=True, slots=True)
class StageADecision:
    """Stdout AnalysisRun projection. Not a frozen-package member."""

    decision: StageADecisionCode
    reasons: tuple[StageAReasonCode, ...]
    capture_run_id: UUID | None
    schema: str = STAGE_A_DECISION_SCHEMA
    package_schema: str = STAGE_A_PACKAGE_SCHEMA

    def __post_init__(self) -> None:
        if type(self.decision) is not StageADecisionCode:
            raise TypeError("decision must be StageADecisionCode")
        if type(self.reasons) is not tuple or not self.reasons:
            raise ValueError("reasons must be a nonempty tuple")
        if any(type(item) is not StageAReasonCode for item in self.reasons):
            raise TypeError("reasons must be StageAReasonCode values")
        classes = {_reason_class(item) for item in self.reasons}
        if len(classes) != 1:
            raise ValueError("reasons must belong to one class")
        expected = _DECISION_CLASS[self.decision]
        if classes.pop() != expected:
            raise ValueError("reasons must belong to one class")
        if self.capture_run_id is not None and type(self.capture_run_id) is not UUID:
            raise TypeError("capture_run_id must be UUID or None")
        if self.schema != STAGE_A_DECISION_SCHEMA:
            raise ValueError("schema must be mee-stage-a-decision/v1")
        if self.package_schema != STAGE_A_PACKAGE_SCHEMA:
            raise ValueError("package_schema must be mee-readonly-frozen-package/v1")
        ordered = tuple(sorted(set(self.reasons), key=_REASON_INDEX.__getitem__))
        object.__setattr__(self, "reasons", ordered)

    def to_canonical_json(self) -> bytes:
        document = {
            "capture_run_id": (
                None if self.capture_run_id is None else str(self.capture_run_id)
            ),
            "decision": self.decision.value,
            "package_schema": self.package_schema,
            "reasons": [reason.value for reason in self.reasons],
            "schema": self.schema,
        }
        return (json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n").encode(
            "ascii"
        )
