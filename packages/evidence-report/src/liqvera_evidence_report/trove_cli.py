"""Read-only Mezo Testnet risk preview with a reproducible evidence ZIP."""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
import time
from dataclasses import asdict, replace
from pathlib import Path
from uuid import UUID, uuid4

from liqvera_public_capture.public_adapters.mezo_troves import capture_live_trove

from liqvera_evidence_report.evidence_bundle import publish_artifact
from liqvera_evidence_report.evidence_io import MAX_MEMBER_BYTES, EvidenceRejected, strict_json
from liqvera_evidence_report.trove_report import TroveReportRequest, build_trove_report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("borrower")
    parser.add_argument(
        "--engine-commit", required=True, help="Exact source revision, never a guessed identifier"
    )
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/trove-risk"))
    parser.add_argument("--report-id")
    parser.add_argument(
        "--capture", type=Path, help="Retained raw-call JSON; builds without network"
    )
    parser.add_argument(
        "--fixture", action="store_true", help="Explicit simulated output; requires --capture"
    )
    args = parser.parse_args(argv)
    try:
        if args.fixture and args.capture is None:
            raise EvidenceRejected("INVALID_INPUT")
        try:
            report_id = UUID(args.report_id) if args.report_id else uuid4()
        except ValueError as error:
            raise EvidenceRejected("INVALID_INPUT") from error
        request = TroveReportRequest(
            report_id,
            args.borrower,
            args.engine_commit,
            time.time_ns() // 1_000_000,
            "fixture" if args.fixture else "live-public",
        )
        if args.capture is not None:
            fd = os.open(args.capture, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            with os.fdopen(fd, "rb") as stream:
                if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                    raise EvidenceRejected("INVALID_DATASET")
                raw = stream.read(MAX_MEMBER_BYTES + 1)
                if len(raw) > MAX_MEMBER_BYTES:
                    raise EvidenceRejected("INVALID_DATASET")
                capture = strict_json(raw)
        else:
            capture = capture_live_trove(request.borrower)
        request = replace(request, created_at_ms=time.time_ns() // 1_000_000)
        built = build_trove_report(capture, request)
        output = args.output_root.absolute()
        output.mkdir(parents=True, exist_ok=True)
        artifact = publish_artifact(output, built)
        print(
            json.dumps(
                {
                    "status": "REPORT_BUILT",
                    "report": built.document,
                    "artifact": asdict(artifact),
                    "evidence_zip": str(output / artifact.report_id / "evidence.zip"),
                    "chargeable": False,
                    "execution_authority": "NONE",
                },
                sort_keys=True,
            )
        )
        return 0
    except (EvidenceRejected, OSError, ValueError) as error:
        code = getattr(
            error,
            "code",
            "SOURCE_UNAVAILABLE" if isinstance(error, ValueError) else "STORAGE_UNAVAILABLE",
        )
        print(json.dumps({"status": "REJECTED", "code": code}), file=sys.stderr)
        return 2
