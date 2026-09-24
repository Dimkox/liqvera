-- Local, fixture-only demo ledger. No payment or canonical F2 state lives here.
PRAGMA foreign_keys = ON;
BEGIN IMMEDIATE;

CREATE TABLE IF NOT EXISTS access_scopes (
    capability_sha256 TEXT PRIMARY KEY CHECK (length(capability_sha256) = 64),
    created_at_ms INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS requests (
    run_id TEXT PRIMARY KEY,
    capability_sha256 TEXT NOT NULL REFERENCES access_scopes(capability_sha256),
    idempotency_key TEXT NOT NULL,
    body_sha256 TEXT NOT NULL CHECK (length(body_sha256) = 64),
    normalized_body TEXT NOT NULL,
    created_at_ms INTEGER NOT NULL,
    UNIQUE (capability_sha256, idempotency_key)
);
CREATE INDEX IF NOT EXISTS requests_scope_run ON requests(capability_sha256, run_id);

CREATE TABLE IF NOT EXISTS reports (
    report_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL UNIQUE REFERENCES requests(run_id),
    report_sha256 TEXT NOT NULL CHECK (length(report_sha256) = 64),
    bundle_sha256 TEXT NOT NULL CHECK (length(bundle_sha256) = 64),
    source_at TEXT NOT NULL,
    limitations_json TEXT NOT NULL,
    created_at_ms INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS demo_quotes (
    quote_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL UNIQUE REFERENCES requests(run_id),
    report_id TEXT NOT NULL UNIQUE REFERENCES reports(report_id),
    state TEXT NOT NULL CHECK (state IN ('OFFERED', 'EXPIRED', 'UNLOCKED')),
    expires_at_ms INTEGER NOT NULL,
    created_at_ms INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS simulated_grants (
    grant_id TEXT PRIMARY KEY,
    quote_id TEXT NOT NULL UNIQUE REFERENCES demo_quotes(quote_id),
    capability_sha256 TEXT NOT NULL REFERENCES access_scopes(capability_sha256),
    action_key TEXT NOT NULL,
    granted_at_ms INTEGER NOT NULL,
    UNIQUE (capability_sha256, action_key)
);

CREATE TABLE IF NOT EXISTS demo_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL REFERENCES requests(run_id),
    event_type TEXT NOT NULL CHECK (event_type IN ('RUN_CREATED', 'QUOTE_EXPIRED', 'SIMULATED_UNLOCK')),
    occurred_at_ms INTEGER NOT NULL,
    detail_json TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS demo_events_no_update
BEFORE UPDATE ON demo_events BEGIN SELECT RAISE(ABORT, 'demo events are append-only'); END;
CREATE TRIGGER IF NOT EXISTS demo_events_no_delete
BEFORE DELETE ON demo_events BEGIN SELECT RAISE(ABORT, 'demo events are append-only'); END;

PRAGMA user_version = 1;
COMMIT;
