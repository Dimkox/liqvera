from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_live_grant_consumption_is_one_shot_append_only_and_precedes_submission() -> None:
    migration = (ROOT / "apps/mezo-gateway/migrations/003_live_grant_consumption.sql").read_text()
    ledger = (ROOT / "apps/mezo-gateway/src/adapters/postgres.ts").read_text()
    assert "grant_digest char(64) PRIMARY KEY" in migration
    assert "grant_id uuid NOT NULL UNIQUE" in migration
    assert "payment_attempt_id uuid NOT NULL UNIQUE" in migration
    assert "BEFORE UPDATE OR DELETE" in migration
    consume = ledger.index("INSERT INTO live_grant_consumptions")
    submitting = ledger.index("SET state='SUBMITTING'", consume)
    assert consume < submitting
    assert "ON CONFLICT DO NOTHING RETURNING grant_digest" in ledger[consume:submitting]


def test_ordinary_gateway_startup_has_no_grant_composition() -> None:
    main = (ROOT / "apps/mezo-gateway/src/main.ts").read_text()
    assert "composeOfficialX402(identity,finality,reader,config.publicBase,null)" in main
    assert "process.env" not in main
