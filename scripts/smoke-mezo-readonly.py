#!/usr/bin/env python3
"""Explicit native Testnet reads only; never signs or submits a payment."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
for package in ('contracts', 'public-capture', 'readonly-analyzer', 'evidence-report'):
    sys.path.insert(0, str(ROOT / 'packages' / package / 'src'))
from tools.mezo_acceptance.live import mezo_testnet_readonly_smoke

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--live', required=True, action='store_true')
    parser.add_argument('--borrower', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = mezo_testnet_readonly_smoke(args.borrower, args.output)
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result['status'] == 'PASS' else 1)
