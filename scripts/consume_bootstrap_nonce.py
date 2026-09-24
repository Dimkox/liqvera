#!/usr/bin/env python3
"""Eligibility boundary for Phase A nonce claims; persistence belongs to the writer."""
from __future__ import annotations
from scripts.write_bootstrap_nonce_consumption import ConsumptionError,validate_consumption

RETIRED_COMMENT_ID=5264583724
def validate_eligible_claim(value):
    validate_consumption(value)
    if value["approval_comment_id"]==RETIRED_COMMENT_ID: raise ConsumptionError("RETIRED_NONCE_FORBIDDEN")
    return value
