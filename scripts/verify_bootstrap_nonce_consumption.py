#!/usr/bin/env python3
"""Independent bounded verifier for a persisted bootstrap nonce claim."""
from __future__ import annotations
import json
from pathlib import Path
from scripts.write_bootstrap_nonce_consumption import ConsumptionError,validate_consumption

def verify_consumption(path:Path,expected:dict):
    if path.stat().st_size>65536: raise ConsumptionError("CONSUMPTION_TOO_LARGE")
    actual=json.loads(path.read_text(encoding="utf-8")); validate_consumption(actual)
    if actual!=expected: raise ConsumptionError("CONSUMPTION_BINDING_MISMATCH")
    return actual
