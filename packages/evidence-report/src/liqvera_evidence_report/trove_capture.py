"""Read the private capture handoff through bounded no-follow descriptors."""
from pathlib import Path

from liqvera_public_capture.public_adapters.mezo_troves import verify_trove_capture

from liqvera_evidence_report.canonical import canonical_json_bytes
from liqvera_evidence_report.evidence_io import EvidenceRejected, digest, read_tree, strict_json


def read_trove_package(path: Path, capture_id: str) -> dict:
    members = read_tree(path)
    if set(members) != {'manifest.json', 'trove-capture.json'}:
        raise EvidenceRejected('INVALID_DATASET')
    raw = members['trove-capture.json']
    expected = {'schema': 'liqvera-trove-capture-package/v1', 'capture_id': capture_id,
                'source_mode': 'live-public', 'capture_sha256': digest(raw), 'capture_length': len(raw)}
    if members['manifest.json'] != canonical_json_bytes(expected):
        raise EvidenceRejected('INVALID_DATASET')
    capture = strict_json(raw)
    try:
        verify_trove_capture(capture)
    except (ValueError, TypeError, KeyError) as error:
        raise EvidenceRejected('INVALID_DATASET') from error
    return capture
