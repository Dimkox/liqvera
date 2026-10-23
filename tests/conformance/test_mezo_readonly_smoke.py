"""Native smoke transport is replaceable with real retained calls for offline tests."""
import json
import zipfile
from pathlib import Path

import pytest

from tools.mezo_acceptance.live import mezo_testnet_readonly_smoke

ROOT = Path(__file__).resolve().parents[2]
BORROWER = '0xDA04759E54728B6636Fe48F7c9795c7B609bAaAa'


def test_smoke_retains_verified_raw_sources_without_payment(tmp_path, monkeypatch):
    from liqvera_public_capture.public_adapters import mezo_dex, mezo_troves
    with zipfile.ZipFile(ROOT / 'apps/mezo-web/public/demo/latest-live/evidence.zip') as archive:
        dex = json.loads(archive.read('mezo-dex/capture.json'))
    with zipfile.ZipFile(ROOT / 'evidence/mezo-testnet/2026-10-23-trove-risk-preview/evidence.zip') as archive:
        trove = json.loads(archive.read('mezo-troves/capture.json'))
    monkeypatch.setattr(mezo_dex, 'capture_live_dex', lambda *a: dex)
    monkeypatch.setattr(mezo_troves, 'capture_live_trove', lambda *a: trove)
    output = tmp_path / 'new'
    result = mezo_testnet_readonly_smoke(BORROWER, output)
    assert result['status'] == 'PASS'
    assert [item['block_number'] for item in result['sources']] == ['16321216', '16323457']
    assert [item['raw_call_count'] for item in result['sources']] == [8, 1812]
    assert {p.name for p in output.iterdir()} == {'mezo-dex.json', 'mezo-troves.json', 'result.json'}


def test_smoke_failure_is_not_replaced_by_a_fixture(tmp_path, monkeypatch):
    from liqvera_public_capture.public_adapters import mezo_dex
    monkeypatch.setattr(mezo_dex, 'capture_live_dex', lambda *a: (_ for _ in ()).throw(ValueError('RPC unavailable')))
    output = tmp_path / 'new'
    result = mezo_testnet_readonly_smoke(BORROWER, output)
    assert result['status'] == 'FAIL'
    assert result['code'] == 'MEZO_SOURCE_UNAVAILABLE'
    assert {p.name for p in output.iterdir()} == {'result.json'}


def test_invalid_borrower_does_not_start_smoke_or_create_artifacts(tmp_path):
    with pytest.raises(ValueError, match='INVALID_INPUT'):
        mezo_testnet_readonly_smoke('invalid', tmp_path / 'new')
    assert not (tmp_path / 'new').exists()
