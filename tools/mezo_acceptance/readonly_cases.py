"""Separate A31/A32 retained-proof suite; the immutable A01–A30 contract stays intact."""
from __future__ import annotations

import argparse
import os
import re
import stat
import subprocess
from pathlib import Path

from liqvera_evidence_report.canonical import canonical_json_bytes
from liqvera_evidence_report.evidence_bundle import verify_bundle_bytes
from liqvera_evidence_report.evidence_io import EvidenceRejected, digest, read_tree, strict_json

ROOT = Path(__file__).resolve().parents[2]
SCOPE = 'Retained native Testnet snapshots and offline recalculation only; not live payment or deployment acceptance.'
VECTORS = (
    ('A31', 'apps/mezo-web/public/demo/latest-live/evidence.zip',
     'd58728bd3df4b79c43bb2e742225e5b8f879eb0ec292213ffd3941f0f8778753',
     '0c20f41f845bd39c88286b52a64d1dad53713fd215507f611fab51d29896f51f', 'mezo_dex', 'mezo-dex'),
    ('A32', 'evidence/mezo-testnet/2026-10-23-trove-risk-preview/evidence.zip',
     '22dfc0db8355bc126f89af07914aa2601b42fd84eafc923e319b84bc2b7b60f1',
     '94c0a93520eb91382c45f4690f176e655ccc372e67b9594653ef651cfd419b10', 'trove_risk', 'mezo-troves'),
)


def read_regular(path: Path, limit: int) -> bytes:
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise EvidenceRejected('INVALID_DATASET')
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise EvidenceRejected('INVALID_DATASET')
    return raw


def cases(members: dict[str, bytes]) -> list[dict]:
    if set(members) != {'A31.zip', 'A32.zip'}:
        raise EvidenceRejected('INVALID_DATASET')
    result = []
    for case_id, _, report_sha, bundle_sha, field, prefix in VECTORS:
        raw = members[case_id + '.zip']
        if digest(raw) != bundle_sha:
            raise EvidenceRejected('ARTIFACT_INTEGRITY_FAILED')
        built = verify_bundle_bytes(raw, expected_report_sha256=report_sha)
        data = built.document[field]
        calls = strict_json(built.extra_members[prefix + '/calls.json'])
        result.append({'case_id': case_id, 'status': 'PASS', 'report_sha256': report_sha,
                       'bundle_sha256': bundle_sha, 'source_engine_commit': built.document['reproducibility']['engine_commit'],
                       'block_number': data['block_number'], 'block_hash': data['block_hash'],
                       'raw_call_count': len(calls), 'offline_byte_reconstruction': 'PASS'})
    return result


def verify_result(path: Path, expected_sha256: str, *, require_current_repository=True) -> dict:
    if re.fullmatch(r'[0-9a-f]{64}', expected_sha256) is None:
        raise EvidenceRejected('INVALID_INPUT')
    raw = read_regular(path, 16384)
    if digest(raw) != expected_sha256:
        raise EvidenceRejected('ARTIFACT_INTEGRITY_FAILED')
    value = strict_json(raw)
    if type(value) is not dict or set(value) != {'schema', 'source_commit', 'scope', 'overall_status', 'cases'}:
        raise EvidenceRejected('INVALID_DATASET')
    if (value['schema'] != 'liqvera-mezo-readonly-acceptance/v1' or value['scope'] != SCOPE
            or value['overall_status'] != 'PASS' or type(value['source_commit']) is not str
            or re.fullmatch(r'[0-9a-f]{40}', value['source_commit']) is None):
        raise EvidenceRejected('INVALID_DATASET')
    if require_current_repository:
        current = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
        if current != value['source_commit']:
            raise EvidenceRejected('INVALID_DATASET')
    expected_cases = cases(read_tree(path.with_name(path.name + '.evidence')))
    if value['cases'] != expected_cases or raw != canonical_json_bytes(value):
        raise EvidenceRejected('INVALID_DATASET')
    return value


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--mode', choices=['offline'], required=True)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    plan = strict_json(read_regular(args.plan, 16384))
    if plan != {'schema': 'liqvera-mezo-readonly-plan/v1', 'cases': ['A31', 'A32']}:
        raise EvidenceRejected('INVALID_INPUT')
    source = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    dirty = subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True)
    if dirty:
        raise EvidenceRejected('INVALID_DATASET')
    members = {case_id + '.zip': read_regular(ROOT / filename, 10*1024*1024)
               for case_id, filename, *_ in VECTORS}
    document = {'schema': 'liqvera-mezo-readonly-acceptance/v1', 'source_commit': source,
                'scope': SCOPE, 'overall_status': 'PASS', 'cases': cases(members)}
    raw = canonical_json_bytes(document)
    output = args.output.absolute()
    if output.exists() or output.is_symlink():
        raise FileExistsError('acceptance result already exists')
    evidence = output.with_name(output.name + '.evidence')
    evidence.mkdir(mode=0o755)
    for name, payload in members.items():
        with (evidence / name).open('xb') as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    with output.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    verify_result(output, digest(raw))
    print(f'PASS A31 A32; sha256={digest(raw)}; scope={SCOPE}')
    return 0
