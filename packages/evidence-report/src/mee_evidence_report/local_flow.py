"""Capability-scoped, fixture-only report flow with an explicit no-transfer unlock."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import sqlite3
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from mee_contracts.exact import ExactDecimal
from mee_evidence_report.builder import build_simulated_report
from mee_evidence_report.bundle import write_mvp_artifact
from mee_evidence_report.canonical import canonical_json_bytes
from mee_evidence_report.local_store import LocalDemoError, LocalDemoStore, capability_digest
from mee_evidence_report.model import MvpReportRejected, MvpReportRequest
from mee_readonly_analyzer.vwap import Side

_INSTRUMENT = "hyperliquid:BTC:perpetual"
_FIELDS = frozenset({"instrument_id", "side", "quantity_base", "expected_payer"})
_QUANTITY = re.compile(r"[+]?[0-9]+(?:\.[0-9]{1,8})?\Z")
_PAYER = re.compile(r"0x[0-9a-fA-F]{40}\Z")
_KEY = re.compile(r"[0-9a-f]{64}\Z")
_OFFER_MS = 15 * 60 * 1000
_PRICE_DISPLAY = "0 MUSD (simulated demo; NO TRANSFER)"


def _now_ms() -> int:
    return time.time_ns() // 1_000_000


def _timestamp(milliseconds: int) -> str:
    return (
        datetime.fromtimestamp(milliseconds / 1000, tz=UTC)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def _key(value: str, code: str) -> str:
    if type(value) is not str or _KEY.fullmatch(value) is None:
        raise LocalDemoError(code)
    return value


def _normalized_body(body: dict[str, object]) -> tuple[dict[str, str], ExactDecimal]:
    if type(body) is not dict or body.keys() != _FIELDS:
        raise LocalDemoError("INVALID_REQUEST_BODY")
    instrument = body["instrument_id"]
    side = body["side"]
    quantity_raw = body["quantity_base"]
    payer = body["expected_payer"]
    if instrument != _INSTRUMENT or type(instrument) is not str:
        raise LocalDemoError("UNSUPPORTED_INSTRUMENT")
    if type(side) is not str or side not in {"BUY", "SELL"}:
        raise LocalDemoError("INVALID_SIDE")
    if (
        type(quantity_raw) is not str
        or len(quantity_raw) > 32
        or _QUANTITY.fullmatch(quantity_raw) is None
    ):
        raise LocalDemoError("INVALID_QUANTITY")
    try:
        quantity = ExactDecimal.parse(quantity_raw)
    except (TypeError, ValueError) as error:
        raise LocalDemoError("INVALID_QUANTITY") from error
    if quantity.scaled <= 0:
        raise LocalDemoError("INVALID_QUANTITY")
    if type(payer) is not str or _PAYER.fullmatch(payer) is None:
        raise LocalDemoError("INVALID_EXPECTED_PAYER")
    normalized = {
        "instrument_id": _INSTRUMENT,
        "side": side,
        "quantity_base": str(quantity),
        "expected_payer": payer.lower(),
    }
    return normalized, quantity


class LocalDemoFlow:
    """Build, recover, and unlock local simulated reports without payment authority."""

    def __init__(self, store: LocalDemoStore, package_root: Path) -> None:
        if not isinstance(store, LocalDemoStore) or not isinstance(package_root, Path):
            raise TypeError("store must be LocalDemoStore and package_root must be Path")
        self.store = store
        self.package_root = package_root

    def create_run(
        self, capability: str, idempotency_key: str, body: dict[str, object]
    ) -> dict[str, object]:
        scope = capability_digest(capability)
        _key(idempotency_key, "INVALID_IDEMPOTENCY_KEY")
        normalized, quantity = _normalized_body(body)
        body_json = canonical_json_bytes(normalized).decode("utf-8")
        body_sha256 = hashlib.sha256(body_json.encode("utf-8")).hexdigest()
        with self.store.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            output_dir: Path | None = None
            artifact_written = False
            try:
                prior = connection.execute(
                    "SELECT run_id, body_sha256 FROM requests WHERE capability_sha256 = ? "
                    "AND idempotency_key = ?",
                    (scope, idempotency_key),
                ).fetchone()
                if prior is not None:
                    if prior["body_sha256"] != body_sha256:
                        raise LocalDemoError("IDEMPOTENCY_BODY_CONFLICT", 409)
                    row = self._row(connection, scope, UUID(prior["run_id"]))
                    self._expire(connection, row)
                    result = self._response(self._row(connection, scope, UUID(prior["run_id"])))
                    connection.execute("COMMIT")
                    return result

                run_id = uuid4()
                report_id = uuid4()
                quote_id = uuid4()
                now = _now_ms()
                try:
                    built = build_simulated_report(
                        self.package_root,
                        MvpReportRequest(
                            report_id=report_id,
                            side=Side(normalized["side"]),
                            quantity_base=quantity,
                        ),
                    )
                except MvpReportRejected as error:
                    raise LocalDemoError(error.code, 422) from error
                output_dir = self.store.artifact_root / str(report_id)
                artifact = write_mvp_artifact(output_dir, built, self.package_root)
                artifact_written = True
                self.store.read_artifact(report_id, "report.json", artifact.report_sha256)
                self.store.read_artifact(report_id, "evidence.zip", artifact.bundle_sha256)

                connection.execute(
                    "INSERT INTO access_scopes(capability_sha256, created_at_ms) VALUES (?, ?) "
                    "ON CONFLICT(capability_sha256) DO NOTHING",
                    (scope, now),
                )
                connection.execute(
                    "INSERT INTO requests(run_id, capability_sha256, idempotency_key, body_sha256, "
                    "normalized_body, created_at_ms) VALUES (?, ?, ?, ?, ?, ?)",
                    (str(run_id), scope, idempotency_key, body_sha256, body_json, now),
                )
                source = built.document["source"]
                quality = built.document["quality"]
                assert isinstance(source, dict) and isinstance(quality, dict)
                connection.execute(
                    "INSERT INTO reports(report_id, run_id, report_sha256, bundle_sha256, "
                    "source_at, limitations_json, created_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        str(report_id), str(run_id), artifact.report_sha256, artifact.bundle_sha256,
                        source["source_at"], json.dumps(quality["limitations"]), now,
                    ),
                )
                connection.execute(
                    "INSERT INTO demo_quotes(quote_id, run_id, report_id, state, expires_at_ms, "
                    "created_at_ms) VALUES (?, ?, ?, 'OFFERED', ?, ?)",
                    (str(quote_id), str(run_id), str(report_id), now + _OFFER_MS, now),
                )
                self._event(connection, run_id, "RUN_CREATED", now)
                result = self._response(self._row(connection, scope, run_id))
                connection.execute("COMMIT")
                return result
            except BaseException:
                if connection.in_transaction:
                    connection.execute("ROLLBACK")
                if artifact_written and output_dir is not None:
                    shutil.rmtree(output_dir)
                raise

    def get_run(self, capability: str, run_id: UUID) -> dict[str, object]:
        scope = capability_digest(capability)
        with self.store.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                row = self._row(connection, scope, run_id)
                self._expire(connection, row)
                result = self._response(self._row(connection, scope, run_id))
                connection.execute("COMMIT")
                return result
            except BaseException:
                connection.execute("ROLLBACK")
                raise

    def confirm_simulated(
        self, capability: str, run_id: UUID, action_key: str
    ) -> dict[str, object]:
        scope = capability_digest(capability)
        _key(action_key, "INVALID_ACTION_KEY")
        with self.store.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                row = self._row(connection, scope, run_id)
                self._expire(connection, row)
                row = self._row(connection, scope, run_id)
                if row["state"] == "EXPIRED":
                    raise LocalDemoError("DEMO_QUOTE_EXPIRED", 410)
                existing = connection.execute(
                    "SELECT quote_id, action_key FROM simulated_grants WHERE quote_id = ?",
                    (row["quote_id"],),
                ).fetchone()
                if existing is not None:
                    if existing["action_key"] != action_key:
                        raise LocalDemoError("SIMULATED_ACTION_CONFLICT", 409)
                    if row["state"] != "UNLOCKED":
                        raise LocalDemoError("SIMULATED_GRANT_INCONSISTENT", 500)
                else:
                    reused = connection.execute(
                        "SELECT quote_id FROM simulated_grants WHERE capability_sha256 = ? "
                        "AND action_key = ?",
                        (scope, action_key),
                    ).fetchone()
                    if reused is not None:
                        raise LocalDemoError("SIMULATED_ACTION_CONFLICT", 409)
                    now = _now_ms()
                    connection.execute(
                        "INSERT INTO simulated_grants(grant_id, quote_id, capability_sha256, "
                        "action_key, granted_at_ms) VALUES (?, ?, ?, ?, ?)",
                        (str(uuid4()), row["quote_id"], scope, action_key, now),
                    )
                    connection.execute(
                        "UPDATE demo_quotes SET state = 'UNLOCKED' "
                        "WHERE quote_id = ? AND state = 'OFFERED'",
                        (row["quote_id"],),
                    )
                    self._event(connection, run_id, "SIMULATED_UNLOCK", now)
                result = self._response(self._row(connection, scope, run_id))
                result["grant"] = {
                    "mode": "SIMULATED", "transferred": False, "message": "NO TRANSFER"
                }
                connection.execute("COMMIT")
                return result
            except BaseException:
                connection.execute("ROLLBACK")
                raise

    def get_report(self, capability: str, run_id: UUID) -> bytes:
        row = self._entitled_row(capability, run_id)
        return self.store.read_artifact(UUID(row["report_id"]), "report.json", row["report_sha256"])

    def get_evidence(self, capability: str, run_id: UUID) -> bytes:
        row = self._entitled_row(capability, run_id)
        return self.store.read_artifact(
            UUID(row["report_id"]), "evidence.zip", row["bundle_sha256"]
        )

    def _entitled_row(self, capability: str, run_id: UUID) -> sqlite3.Row:
        scope = capability_digest(capability)
        with self.store.connect() as connection:
            row = self._row(connection, scope, run_id)
            if row["state"] != "UNLOCKED":
                raise LocalDemoError("SIMULATED_UNLOCK_REQUIRED", 403)
            grant = connection.execute(
                "SELECT 1 FROM simulated_grants WHERE quote_id = ? AND capability_sha256 = ?",
                (row["quote_id"], scope),
            ).fetchone()
            if grant is None:
                raise LocalDemoError("SIMULATED_UNLOCK_REQUIRED", 403)
            return row

    @staticmethod
    def _row(connection: sqlite3.Connection, scope: str, run_id: UUID) -> sqlite3.Row:
        if type(run_id) is not UUID:
            raise LocalDemoError("INVALID_RUN_ID")
        row = connection.execute(
            "SELECT r.run_id, r.normalized_body, p.report_id, p.report_sha256, "
            "p.bundle_sha256, p.source_at, p.limitations_json, q.quote_id, q.state, "
            "q.expires_at_ms FROM requests AS r JOIN reports AS p ON p.run_id = r.run_id "
            "JOIN demo_quotes AS q ON q.run_id = r.run_id WHERE r.capability_sha256 = ? "
            "AND r.run_id = ?",
            (scope, str(run_id)),
        ).fetchone()
        if row is None:
            raise LocalDemoError("RUN_NOT_FOUND", 404)
        return row

    @staticmethod
    def _event(connection: sqlite3.Connection, run_id: UUID, event_type: str, at_ms: int) -> None:
        connection.execute(
            "INSERT INTO demo_events(run_id, event_type, occurred_at_ms, detail_json) "
            "VALUES (?, ?, ?, '{}')",
            (str(run_id), event_type, at_ms),
        )

    def _expire(self, connection: sqlite3.Connection, row: sqlite3.Row) -> None:
        now = _now_ms()
        if row["state"] == "OFFERED" and now >= row["expires_at_ms"]:
            connection.execute(
                "UPDATE demo_quotes SET state = 'EXPIRED' WHERE quote_id = ? AND state = 'OFFERED'",
                (row["quote_id"],),
            )
            self._event(connection, UUID(row["run_id"]), "QUOTE_EXPIRED", now)

    @staticmethod
    def _response(row: sqlite3.Row) -> dict[str, object]:
        body = json.loads(row["normalized_body"])
        preview: dict[str, object] = {
            **body,
            "snapshot_at": row["source_at"],
            "snapshot_status": "SIMULATED",
            "limitations": [
                *json.loads(row["limitations_json"]),
                "Expected payer is illustrative and has no wallet authentication.",
                "Unlock is a local simulation; NO TRANSFER occurs.",
            ],
            "price_display": _PRICE_DISPLAY,
            "expires_at": _timestamp(row["expires_at_ms"]),
        }
        response: dict[str, object] = {
            "run_id": row["run_id"],
            "report_id": row["report_id"],
            "quote_id": row["quote_id"],
            "quote_state": row["state"],
            "preview": preview,
            "mode": "SIMULATED",
            "verification_status": "UNVERIFIED",
            "execution_authority": "NONE",
        }
        if row["state"] == "UNLOCKED":
            response["report_sha256"] = row["report_sha256"]
            response["bundle_sha256"] = row["bundle_sha256"]
        return response
