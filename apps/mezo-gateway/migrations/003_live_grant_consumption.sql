-- One durable row is the settlement budget.  It is inserted in the same
-- transaction that crosses VERIFIED -> SUBMITTING, before facilitator I/O.
CREATE TABLE live_grant_consumptions (
  grant_digest char(64) PRIMARY KEY CHECK (grant_digest ~ '^[0-9a-f]{64}$'),
  grant_id uuid NOT NULL UNIQUE,
  payment_attempt_id uuid NOT NULL UNIQUE REFERENCES payment_attempts(id),
  consumed_at timestamptz NOT NULL DEFAULT now()
);

CREATE TRIGGER live_grant_consumption_immutable
BEFORE UPDATE OR DELETE ON live_grant_consumptions
FOR EACH ROW EXECUTE FUNCTION forbid_audit_mutation();
