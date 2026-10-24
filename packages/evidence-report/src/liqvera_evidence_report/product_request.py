"""Closed service product dispatch; legacy market requests remain unchanged."""
from uuid import UUID

from liqvera_evidence_report.evidence_io import EvidenceRejected, identifier
from liqvera_evidence_report.report import ReportRequest, parse_request
from liqvera_evidence_report.trove_report import TroveReportRequest


def parse_product_request(body: object, *, engine_commit: str, created_at_ms: int):
    if type(body) is dict and body.get('product_id') == 'trove_risk':
        if set(body) != {'report_id', 'product_id', 'borrower'}:
            raise EvidenceRejected('INVALID_INPUT')
        return TroveReportRequest(UUID(identifier(body['report_id'])), body['borrower'],
                                  engine_commit, created_at_ms)
    return parse_request(body, engine_commit=engine_commit)


def request_identity(request: ReportRequest | TroveReportRequest) -> dict:
    if type(request) is TroveReportRequest:
        return {'product_id': 'trove_risk', 'borrower': request.borrower}
    return {'side': request.side.value, 'quantity_base': str(request.quantity_base),
            **({'mezo_dex': True} if request.include_mezo_dex else {})}
