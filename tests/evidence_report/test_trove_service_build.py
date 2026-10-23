"""Only fresh live fixed-block Trove packages can be offered for sale."""
import json
from pathlib import Path
from uuid import UUID

import pytest
from liqvera_evidence_report.canonical import canonical_json_bytes
from liqvera_evidence_report.evidence_io import EvidenceRejected, digest
from liqvera_evidence_report.service import build_trove_product
from liqvera_evidence_report.trove_report import TroveReportRequest

ROOT = Path(__file__).resolve().parents[2]


def setup(tmp_path):
    capture = json.loads((ROOT / 'evidence/mezo-testnet/2026-10-23-trove-active-native.json').read_bytes())
    raw = canonical_json_bytes(capture)
    (tmp_path / 'trove-capture.json').write_bytes(raw)
    (tmp_path / 'manifest.json').write_bytes(canonical_json_bytes({
        'schema': 'liqvera-trove-capture-package/v1', 'capture_id': tmp_path.name,
        'source_mode': 'live-public', 'capture_sha256': digest(raw), 'capture_length': len(raw)}))
    timestamp = int(capture['block']['result']['timestamp'], 16) * 1000
    request = TroveReportRequest(UUID('123e4567-e89b-42d3-a456-426614174050'), capture['borrower'], 'a'*40, timestamp)
    return request, timestamp


def test_service_trove_build_uses_server_clock_after_capture(tmp_path):
    request, timestamp = setup(tmp_path)
    built = build_trove_product(tmp_path, request, created_at_ms=timestamp+10_000)
    assert built.document['request']['borrower'] == request.borrower
    assert built.document['quality']['snapshot_status'] == 'VALID_FOR_SNAPSHOT_CALCULATION'


def test_service_never_sells_stale_capture(tmp_path):
    request, timestamp = setup(tmp_path)
    with pytest.raises(EvidenceRejected, match='STALE_SOURCE'):
        build_trove_product(tmp_path, request, created_at_ms=timestamp+30_001)


def test_service_preserves_clock_skew_reason(tmp_path):
    request, timestamp = setup(tmp_path)
    with pytest.raises(EvidenceRejected, match='CLOCK_SKEW'):
        build_trove_product(tmp_path, request, created_at_ms=timestamp-1001)
