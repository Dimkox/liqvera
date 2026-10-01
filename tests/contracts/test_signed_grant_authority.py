from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_migration_006_is_additive_immutable_and_budget_bounded() -> None:
    sql = (ROOT / "apps/mezo-gateway/migrations/006_signed_live_grant_authority.sql").read_text()
    assert "CREATE TABLE live_grant_authorities" in sql
    assert "CREATE TABLE live_grant_reservations" in sql
    assert "UNIQUE (grant_digest, payer)" in sql
    assert "max_per_payer = 1" in sql
    assert "expires_at <= issued_at + interval '24 hours'" in sql
    assert sql.count("forbid_audit_mutation()") == 2
    assert "DROP " not in sql and "ALTER TABLE" not in sql


def test_v2_authority_is_signed_and_v1_has_no_ambient_any_payer_widening() -> None:
    grant = (ROOT / "apps/mezo-gateway/src/security/live-grant.ts").read_text()
    adapter = (ROOT / "apps/mezo-gateway/src/adapters/x402.ts").read_text()
    assert "LIVE_GRANT_SIGNATURE_INVALID" in grant
    assert "LIVE_GRANT_NOT_CANONICAL" in grant
    assert "ANY_VALID_X402_PAYER" in grant
    assert "demoAnyPayer" not in grant
    assert "demoAnyPayer" not in adapter
