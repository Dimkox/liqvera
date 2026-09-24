import pytest
from scripts._trusted_receipt import ReceiptError
from scripts.write_controller_trust_context import write_context
from scripts.verify_controller_trust_context import verify_context

def test_phase_a_cannot_write_or_admit_realized_trust_context():
    with pytest.raises(ReceiptError,match="PHASE_A_AUTHORITY_NONE"): write_context({})
    with pytest.raises(ReceiptError,match="PHASE_A_AUTHORITY_NONE"): verify_context({})
