"""A31/A32 have a separate retained-proof scope and reject changed evidence."""
from pathlib import Path

import pytest
from liqvera_evidence_report.canonical import canonical_json_bytes
from liqvera_evidence_report.evidence_io import EvidenceRejected, digest

from tools.mezo_acceptance.readonly_cases import ROOT, SCOPE, VECTORS, cases, verify_result


def native_members():
    return {case_id+'.zip': (ROOT / filename).read_bytes() for case_id, filename, *_ in VECTORS}


def test_a31_a32_recalculate_native_bundles_offline(monkeypatch):
    import socket
    monkeypatch.setattr(socket, 'create_connection', lambda *a, **k: pytest.fail('network access'))
    result = cases(native_members())
    assert [case['case_id'] for case in result] == ['A31', 'A32']
    assert all(case['status'] == 'PASS' for case in result)
    assert [case['block_number'] for case in result] == ['16321216', '16323457']
    assert [case['raw_call_count'] for case in result] == [8, 1812]


@pytest.mark.parametrize('case', ['A31', 'A32'])
def test_acceptance_rejects_one_changed_evidence_byte(case):
    members = native_members()
    value = bytearray(members[case+'.zip'])
    value[-1] ^= 1
    members[case+'.zip'] = bytes(value)
    with pytest.raises(EvidenceRejected, match='ARTIFACT_INTEGRITY_FAILED'):
        cases(members)


def test_sealed_result_replays_evidence_and_rejects_modified_summary(tmp_path):
    members = native_members()
    value = {'schema': 'liqvera-mezo-readonly-acceptance/v1', 'source_commit': 'a'*40,
             'scope': SCOPE, 'overall_status': 'PASS', 'cases': cases(members)}
    path = tmp_path / 'result.json'
    directory = tmp_path / 'result.json.evidence'
    directory.mkdir()
    for name, raw in members.items():
        (directory / name).write_bytes(raw)
    raw = canonical_json_bytes(value)
    path.write_bytes(raw)
    assert verify_result(path, digest(raw), require_current_repository=False) == value
    value['cases'][0]['block_number'] = '1'
    raw = canonical_json_bytes(value)
    path.write_bytes(raw)
    with pytest.raises(EvidenceRejected, match='INVALID_DATASET'):
        verify_result(path, digest(raw), require_current_repository=False)


def test_evidence_directory_symlink_is_rejected(tmp_path):
    path = tmp_path / 'result.json'
    value = {'schema': 'liqvera-mezo-readonly-acceptance/v1', 'source_commit': 'a'*40,
             'scope': SCOPE, 'overall_status': 'PASS', 'cases': []}
    raw = canonical_json_bytes(value)
    path.write_bytes(raw)
    path.with_name(path.name+'.evidence').symlink_to(Path('/tmp'), target_is_directory=True)
    with pytest.raises((EvidenceRejected, OSError)):
        verify_result(path, digest(raw), require_current_repository=False)


def test_formal_vectors_pin_real_calldata_results_and_recomputed_report_fragments():
    import json

    from liqvera_evidence_report.evidence_bundle import verify_bundle_bytes
    vectors = json.loads((ROOT / 'schemas/mezo-evidence/v1/vectors.json').read_bytes())['mezo_readonly']
    assert [v['case_id'] for v in vectors] == ['A31', 'A32']
    members = native_members()
    for vector, (_, _, _, _, field, prefix) in zip(vectors, VECTORS, strict=True):
        built = verify_bundle_bytes(members[vector['case_id']+'.zip'], expected_report_sha256=vector['report_sha256'])
        assert digest(canonical_json_bytes(built.document[field])) == vector['report_fragment_sha256']
        calls = __import__('json').loads(built.extra_members[prefix+'/calls.json'])
        assert all(call in calls for call in vector['raw_calls'])
        assert {int(call['block'], 16) for call in vector['raw_calls']} == {int(vector['block_number'])}


def test_acceptance_verify_cli_rejects_result_symlink(tmp_path):
    import subprocess
    import sys
    target = tmp_path / 'target.json'
    target.write_bytes(b'{}')
    link = tmp_path / 'result.json'
    link.symlink_to(target)
    result = subprocess.run([sys.executable, str(ROOT / 'scripts/verify-mezo-acceptance.py'),
                             '--suite', 'mezo-readonly', str(link), '--sha256', digest(b'{}'),
                             '--allow-detached-subject'], capture_output=True, text=True)
    assert result.returncode != 0
    assert 'Too many levels of symbolic links' in result.stderr
