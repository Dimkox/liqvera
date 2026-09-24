#!/usr/bin/env python3
"""Phase A source interface: no context can be admitted before Phase C2 evidence."""
from scripts._trusted_receipt import ReceiptError
def verify_context(*_args,**_kwargs): raise ReceiptError("CONTROLLER_TRUST_CONTEXT_PHASE_A_AUTHORITY_NONE")
