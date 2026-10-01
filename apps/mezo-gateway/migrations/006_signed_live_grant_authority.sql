-- Signed v2 grant authority and its permanently spent settlement reservations.
CREATE TABLE live_grant_authorities (
  grant_digest char(64) PRIMARY KEY CHECK (grant_digest ~ '^[0-9a-f]{64}$'),
  grant_id uuid NOT NULL UNIQUE,
  schema_version text NOT NULL CHECK (schema_version IN ('v1','v2')),
  policy_sha256 char(64) NOT NULL UNIQUE CHECK (policy_sha256 ~ '^[0-9a-f]{64}$'),
  key_id text NOT NULL CHECK (key_id ~ '^[0-9a-f]{64}$'),
  signature_sha256 char(64) NOT NULL CHECK (signature_sha256 ~ '^[0-9a-f]{64}$'),
  issued_at timestamptz NOT NULL,
  not_before timestamptz NOT NULL,
  expires_at timestamptz NOT NULL,
  pay_to char(42) NOT NULL CHECK (pay_to ~ '^0x[0-9a-f]{40}$'),
  amount_per numeric(78,0) NOT NULL CHECK (amount_per > 0),
  max_submissions integer NOT NULL CHECK (max_submissions BETWEEN 1 AND 1000),
  max_total numeric(78,0) NOT NULL CHECK (max_total >= amount_per AND max_total = amount_per * max_submissions),
  max_per_payer integer NOT NULL CHECK (max_per_payer = 1),
  payer_policy text NOT NULL CHECK (payer_policy = 'ANY_VALID_X402_PAYER'),
  activated_at timestamptz NOT NULL DEFAULT now(),
  CHECK (not_before >= issued_at AND expires_at > not_before AND expires_at <= issued_at + interval '24 hours')
);

CREATE TABLE live_grant_reservations (
  grant_digest char(64) NOT NULL REFERENCES live_grant_authorities(grant_digest),
  ordinal integer NOT NULL CHECK (ordinal > 0),
  payment_attempt_id uuid NOT NULL UNIQUE REFERENCES payment_attempts(id),
  payer char(42) NOT NULL CHECK (payer ~ '^0x[0-9a-f]{40}$'),
  amount_atomic numeric(78,0) NOT NULL CHECK (amount_atomic > 0),
  reserved_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (grant_digest, ordinal),
  UNIQUE (grant_digest, payer)
);

CREATE TRIGGER live_grant_authority_immutable
BEFORE UPDATE OR DELETE ON live_grant_authorities
FOR EACH ROW EXECUTE FUNCTION forbid_audit_mutation();

CREATE TRIGGER live_grant_reservation_immutable
BEFORE UPDATE OR DELETE ON live_grant_reservations
FOR EACH ROW EXECUTE FUNCTION forbid_audit_mutation();
