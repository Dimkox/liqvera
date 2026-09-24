"""Closed sealed Stage A economics claims. No I/O and no episode array."""

from __future__ import annotations

import json
from dataclasses import dataclass

from mee_contracts.exact import ExactDecimal

STAGE_A_SEALED_ECONOMICS_SCHEMA = "mee-stage-a-sealed-economics/v1"

_CLOSED_KEYS = frozenset(
    {
        "schema",
        "independent_episode_count",
        "total_net",
        "median_net",
        "usd_1000_net",
        "usd_5000_net",
        "largest_episode_concentration",
        "survived_delay_300ms",
        "survived_delay_500ms",
        "survived_both_fee_cases",
    }
)


def _parse_money(value: object, name: str) -> ExactDecimal:
    if type(value) is not str:
        raise TypeError(f"{name} must be an ExactDecimal string")
    return ExactDecimal.parse(value)


def _require_bool(value: object, name: str) -> bool:
    if type(value) is not bool:
        raise TypeError(f"{name} must be bool")
    return value


@dataclass(frozen=True, slots=True)
class SealedStageAEconomics:
    """Sealed aggregate claims for Stage A STOP/EXTEND. Not reconstructed P&L."""

    schema: str
    independent_episode_count: int
    total_net: ExactDecimal
    median_net: ExactDecimal
    usd_1000_net: ExactDecimal
    usd_5000_net: ExactDecimal
    largest_episode_concentration: ExactDecimal
    survived_delay_300ms: bool
    survived_delay_500ms: bool
    survived_both_fee_cases: bool

    def __post_init__(self) -> None:
        if self.schema != STAGE_A_SEALED_ECONOMICS_SCHEMA:
            raise ValueError("schema must be mee-stage-a-sealed-economics/v1")
        if type(self.independent_episode_count) is not int:
            raise TypeError("independent_episode_count must be int")
        if self.independent_episode_count < 0:
            raise ValueError("independent_episode_count must be >= 0")
        for name in (
            "total_net",
            "median_net",
            "usd_1000_net",
            "usd_5000_net",
            "largest_episode_concentration",
        ):
            if type(getattr(self, name)) is not ExactDecimal:
                raise TypeError(f"{name} must be ExactDecimal")
        for name in (
            "survived_delay_300ms",
            "survived_delay_500ms",
            "survived_both_fee_cases",
        ):
            if type(getattr(self, name)) is not bool:
                raise TypeError(f"{name} must be bool")

    @classmethod
    def from_document(cls, document: object) -> SealedStageAEconomics:
        if type(document) is not dict:
            raise TypeError("sealed economics must be an object")
        if set(document) != _CLOSED_KEYS:
            raise ValueError("sealed economics keys must match the closed set")
        if document["schema"] != STAGE_A_SEALED_ECONOMICS_SCHEMA:
            raise ValueError("schema must be mee-stage-a-sealed-economics/v1")
        count = document["independent_episode_count"]
        if type(count) is not int:
            raise TypeError("independent_episode_count must be int")
        if count < 0:
            raise ValueError("independent_episode_count must be >= 0")
        return cls(
            schema=STAGE_A_SEALED_ECONOMICS_SCHEMA,
            independent_episode_count=count,
            total_net=_parse_money(document["total_net"], "total_net"),
            median_net=_parse_money(document["median_net"], "median_net"),
            usd_1000_net=_parse_money(document["usd_1000_net"], "usd_1000_net"),
            usd_5000_net=_parse_money(document["usd_5000_net"], "usd_5000_net"),
            largest_episode_concentration=_parse_money(
                document["largest_episode_concentration"],
                "largest_episode_concentration",
            ),
            survived_delay_300ms=_require_bool(
                document["survived_delay_300ms"], "survived_delay_300ms"
            ),
            survived_delay_500ms=_require_bool(
                document["survived_delay_500ms"], "survived_delay_500ms"
            ),
            survived_both_fee_cases=_require_bool(
                document["survived_both_fee_cases"], "survived_both_fee_cases"
            ),
        )

    def to_canonical_json(self) -> bytes:
        document = {
            "independent_episode_count": self.independent_episode_count,
            "largest_episode_concentration": str(self.largest_episode_concentration),
            "median_net": str(self.median_net),
            "schema": self.schema,
            "survived_both_fee_cases": self.survived_both_fee_cases,
            "survived_delay_300ms": self.survived_delay_300ms,
            "survived_delay_500ms": self.survived_delay_500ms,
            "total_net": str(self.total_net),
            "usd_1000_net": str(self.usd_1000_net),
            "usd_5000_net": str(self.usd_5000_net),
        }
        return (json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n").encode(
            "ascii"
        )
