"""The private service binds each product to a closed, replayable request."""
from uuid import UUID

import pytest
from liqvera_evidence_report.evidence_io import EvidenceRejected
from liqvera_evidence_report.product_request import parse_product_request, request_identity
from liqvera_evidence_report.report import ReportRequest
from liqvera_evidence_report.trove_report import TroveReportRequest

REPORT_ID = '123e4567-e89b-42d3-a456-426614174050'
BORROWER = '0xDA04759E54728B6636Fe48F7c9795c7B609bAaAa'


def test_trove_request_preserves_borrower_and_server_context():
    request = parse_product_request({'report_id': REPORT_ID, 'product_id': 'trove_risk',
                                     'borrower': BORROWER}, engine_commit='a'*40, created_at_ms=1234)
    assert request == TroveReportRequest(UUID(REPORT_ID), BORROWER, 'a'*40, 1234)
    assert request_identity(request) == {'product_id': 'trove_risk', 'borrower': BORROWER}


def test_legacy_request_stays_byte_compatible():
    request = parse_product_request({'report_id': REPORT_ID, 'instrument_id': 'hyperliquid:BTC:perpetual',
                                     'side': 'SELL', 'quantity_base': '1'}, engine_commit='a'*40, created_at_ms=1234)
    assert type(request) is ReportRequest
    assert request.created_at_ms is None
    assert request_identity(request) == {'side': 'SELL', 'quantity_base': '1'}


def test_market_dex_opt_in_is_retained_in_canonical_request_identity():
    request = parse_product_request({'report_id': REPORT_ID, 'instrument_id': 'hyperliquid:BTC:perpetual',
                                     'side': 'SELL', 'quantity_base': '1', 'mezo_dex': True},
                                    engine_commit='a'*40, created_at_ms=1234)
    assert type(request) is ReportRequest
    assert request.include_mezo_dex is True
    assert request_identity(request) == {'side': 'SELL', 'quantity_base': '1', 'mezo_dex': True}


@pytest.mark.parametrize('value', [False, 'true', 1, None])
def test_market_dex_opt_in_requires_literal_true(value):
    with pytest.raises(EvidenceRejected, match='INVALID_INPUT'):
        parse_product_request({'report_id': REPORT_ID, 'instrument_id': 'hyperliquid:BTC:perpetual',
                               'side': 'SELL', 'quantity_base': '1', 'mezo_dex': value},
                              engine_commit='a'*40, created_at_ms=1234)


@pytest.mark.parametrize('extra', [{'side': 'SELL'}, {'source_mode': 'fixture'}, {'created_at_ms': 1}])
def test_trove_request_rejects_mixed_or_caller_context(extra):
    with pytest.raises(EvidenceRejected, match='INVALID_INPUT'):
        parse_product_request({'report_id': REPORT_ID, 'product_id': 'trove_risk',
                               'borrower': BORROWER, **extra}, engine_commit='a'*40, created_at_ms=1234)
