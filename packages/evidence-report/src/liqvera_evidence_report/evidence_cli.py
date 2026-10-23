"""Canonical build and archive-first verifier commands; fixture CLI is retained."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from liqvera_evidence_report.evidence_bundle import publish_artifact, verify_bundle
from liqvera_evidence_report.evidence_io import EvidenceRejected
from liqvera_evidence_report.report import build_report, parse_request


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
    recheck = {}
    if "mezo-dex/capture.json" in built.extra_members:
        from liqvera_public_capture.public_adapters.mezo_dex import POOL
        block = hex(int(built.document["mezo_dex"]["block_number"]))
        payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_call",
                              "params": [{"to": POOL, "data": "0x0902f1ac"}, block]},
                             separators=(",", ":"))
        import shlex
        recheck = {"mezo_block_number": built.document["mezo_dex"]["block_number"],
                   "online_recheck_command": "curl --fail --silent --show-error -H 'Content-Type: application/json' --data "
                                             + shlex.quote(payload) + " https://rpc.test.mezo.org",
                   "online_recheck_executed": False}
    if "mezo-troves/capture.json" in built.extra_members:
        import shlex

        from liqvera_public_capture.public_adapters.mezo_troves import PRICE_FEED
        number = built.document["trove_risk"]["block_number"]
        payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_call",
            "params": [{"to": PRICE_FEED, "data": "0x0fdb11cf"}, hex(int(number))]}, separators=(",", ":"))
        recheck = {"mezo_block_number": number,
            "online_recheck_command": "curl --fail --silent --show-error -H 'Content-Type: application/json' --data "
                + shlex.quote(payload) + " https://rpc.test.mezo.org",
            "online_recheck_executed": False}
    print(json.dumps({**recheck, "status": "INTEGRITY_REPRODUCED", "report_sha256": built.report_sha256,
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
