"""Canonical build and archive-first verifier commands; fixture CLI is retained."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from mee_evidence_report.evidence_bundle import publish_artifact, verify_bundle
from mee_evidence_report.evidence_io import EvidenceRejected
from mee_evidence_report.report import build_report, parse_request


def verify_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline bundle integrity and exact recalculation; no authenticity claim.")
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--report-sha256", help="Optional trusted receipt/report digest")
    args = parser.parse_args(argv)
    try:
        built = verify_bundle(args.bundle, expected_report_sha256=args.report_sha256)
    except (EvidenceRejected, OSError, ValueError) as error:
        print(json.dumps({"status": "REJECTED", "code": getattr(error, "code", "INVALID_DATASET")}), file=sys.stderr)
        return 2
    print(json.dumps({"status": "INTEGRITY_REPRODUCED", "report_sha256": built.report_sha256,
                      "snapshot_status": built.document["quality"]["snapshot_status"],
                      "exchange_authenticity_verified": False, "execution_authority": "NONE"}))
    return 0


def build_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build an immutable F3 report; live identity remains fail-closed.")
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--report-id", required=True)
    parser.add_argument("--side", choices=["BUY", "SELL"], required=True)
    parser.add_argument("--quantity", required=True)
    parser.add_argument("--engine-commit", required=True)
    args = parser.parse_args(argv)
    try:
        request = parse_request({"report_id": args.report_id, "side": args.side,
                                 "quantity_base": args.quantity, "instrument_id": "hyperliquid:BTC:perpetual"},
                                engine_commit=args.engine_commit)
        built = build_report(args.package, request)
        artifact = publish_artifact(args.output_root, built)
    except (EvidenceRejected, OSError, ValueError) as error:
        print(json.dumps({"status": "REJECTED", "code": getattr(error, "code", "INVALID_DATASET")}), file=sys.stderr)
        return 2
    print(json.dumps({**asdict(artifact), "snapshot_status": built.document["quality"]["snapshot_status"],
                      "chargeable": False, "execution_authority": "NONE"}))
    return 0
