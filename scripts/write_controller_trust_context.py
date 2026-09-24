#!/usr/bin/env python3
"""Phase A source interface: realized trust writes remain fail-closed until Phase C2."""
from scripts._trusted_receipt import ReceiptError
def write_context(*_args,**_kwargs): raise ReceiptError("CONTROLLER_TRUST_CONTEXT_PHASE_A_AUTHORITY_NONE")
