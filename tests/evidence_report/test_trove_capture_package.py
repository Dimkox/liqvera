"""Private Trove captures are closed atomic packages, never Hyperliquid fallbacks."""
import json
from pathlib import Path
from uuid import UUID

import pytest
from liqvera_evidence_report.evidence_io import EvidenceRejected
from liqvera_evidence_report.trove_capture import read_trove_package
from liqvera_public_capture.evidence_capture import CaptureRejected
from liqvera_public_capture.evidence_package import capture_package

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / 'evidence/mezo-testnet/2026-10-23-trove-active-native.json'
ID = UUID('123e4567-e89b-42d3-a456-426614174050')


def publish(tmp_path, monkeypatch):
    from liqvera_public_capture import evidence_package
    from liqvera_public_capture.public_adapters import mezo_troves
    capture = json.loads(CAPTURE.read_bytes())
    monkeypatch.setattr(mezo_troves, 'capture_live_trove', lambda borrower: capture)
    monkeypatch.setattr(evidence_package, 'capture_responses', lambda *a: pytest.fail('Unrelated HL capture'))
    path = capture_package(tmp_path, ID, source_mode='live-public', trove_request={'borrower': capture['borrower']})
    return path, capture


def test_trove_package_is_separate_and_readable_without_network(tmp_path, monkeypatch):
    path, capture = publish(tmp_path, monkeypatch)
    assert {p.name for p in path.iterdir()} == {'manifest.json', 'trove-capture.json'}
    assert read_trove_package(path, str(ID)) == capture


@pytest.mark.parametrize('change', ['byte', 'extra', 'symlink', 'capture_id'])
def test_trove_capture_package_rejects_corruption(tmp_path, monkeypatch, change):
    path, _ = publish(tmp_path, monkeypatch)
    if change == 'byte':
        (path / 'trove-capture.json').write_bytes(b'{}')
    elif change == 'extra':
        (path / 'unknown').write_bytes(b'x')
    elif change == 'symlink':
        (path / 'trove-capture.json').unlink()
        (path / 'trove-capture.json').symlink_to(CAPTURE)
    else:
        manifest = json.loads((path / 'manifest.json').read_bytes())
        manifest['capture_id'] = '00000000-0000-0000-0000-000000000000'
        (path / 'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(EvidenceRejected):
        read_trove_package(path, str(ID))


def test_trove_capture_rejects_fixture_mode_and_mixed_sources(tmp_path):
    for kwargs in ({'source_mode': 'fixture'}, {'source_mode': 'live-public', 'mezo_request': {'side': 'SELL', 'quantity_wei': '1'}}):
        with pytest.raises(CaptureRejected, match='INVALID_INPUT'):
            capture_package(tmp_path, ID, trove_request={'borrower': '0x'+'1'*40}, **kwargs)
