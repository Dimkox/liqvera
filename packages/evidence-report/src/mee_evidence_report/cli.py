"""Command line entry point for the intentionally unverified Liqvera MVP."""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TextIO
from uuid import UUID, uuid4

from mee_contracts.exact import ExactDecimal
from mee_evidence_report.builder import build_simulated_report
from mee_evidence_report.bundle import write_mvp_artifact
from mee_evidence_report.canonical import canonical_json_bytes
from mee_evidence_report.model import MvpReportRejected, MvpReportRequest
from mee_readonly_analyzer.vwap import Side

_COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}")


def _uuid(value: str) -> UUID:
    try:
        return UUID(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be a UUID") from error


def _quantity(value: str) -> ExactDecimal:
    try:
        quantity = ExactDecimal.parse(value)
    except (TypeError, ValueError) as error:
        raise argparse.ArgumentTypeError("must be an exact decimal string") from error
    if quantity.scaled <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return quantity


def _engine_commit(value: str) -> str:
    if _COMMIT_PATTERN.fullmatch(value) is None:
        raise argparse.ArgumentTypeError("must be 40 lowercase hexadecimal characters")
    return value


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build an unverified simulated Liqvera MVP report")
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--side", required=True, choices=tuple(Side))
    parser.add_argument("--quantity", required=True, type=_quantity)
    parser.add_argument("--report-id", type=_uuid)
    parser.add_argument("--engine-commit", type=_engine_commit, default="0" * 40)
    return parser


def _write_json_line(stream: TextIO, value: object) -> None:
    stream.write(canonical_json_bytes(value).decode("utf-8"))


def main(argv: Sequence[str] | None = None) -> int:
    """Build the local-only simulated artifact and return a stable process code."""

    args = _parser().parse_args(argv)
    report_id = args.report_id or uuid4()
    request = MvpReportRequest(
        report_id=report_id,
        side=Side(args.side),
        quantity_base=args.quantity,
        engine_commit=args.engine_commit,
    )
    try:
        built = build_simulated_report(args.package, request)
        artifact = write_mvp_artifact(args.output, built, args.package)
    except (MvpReportRejected, FileExistsError, OSError, ValueError) as error:
        _write_json_line(sys.stderr, {"error": "REJECTED", "message": str(error)})
        return 1

    _write_json_line(
        sys.stdout,
        {
            "mode": "SIMULATED",
            "report_id": str(report_id),
            "report_sha256": artifact.report_sha256,
            "bundle_sha256": artifact.bundle_sha256,
            "warning": "UNVERIFIED_MVP_NO_PAYMENT",
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
