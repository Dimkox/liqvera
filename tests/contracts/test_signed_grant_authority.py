import hashlib
import json
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


def test_release_allowlist_pins_public_key_and_rotation_requires_edit() -> None:
    value = json.loads((ROOT / "apps/mezo-gateway/config/live-grant-issuer-allowlist.json").read_text())
    assert value["schema"] == "liqvera-live-grant-issuer-allowlist/v1"
    assert len(value["issuers"]) == 1
    issuer = value["issuers"][0]
    raw = bytes.fromhex(issuer["public_key_hex"])
    assert len(raw) == 32
    assert hashlib.sha256(raw).hexdigest() == issuer["key_id"]
    compiled = (ROOT / "apps/mezo-gateway/src/security/live-grant-issuers.ts").read_text()
    assert issuer["key_id"] in compiled
    assert issuer["public_key_hex"] in compiled
    assert "LIVE_GRANT_ISSUER_UNAPPROVED" in compiled
