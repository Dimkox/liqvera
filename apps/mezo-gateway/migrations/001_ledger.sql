-- Forward-only ledger foundation. Preserve dedup and scope rows during recovery.
CREATE TABLE access_scopes (
  scope_hash text PRIMARY KEY CHECK (scope_hash ~ '^[0-9a-f]{64}$'),
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE report_requests (
  id uuid PRIMARY KEY, scope_hash text NOT NULL REFERENCES access_scopes,
  idempotency_key varchar(128) NOT NULL, body_hash text NOT NULL CHECK (body_hash ~ '^[0-9a-f]{64}$'),
  canonical_body jsonb NOT NULL, report_id uuid NOT NULL UNIQUE,
  state text NOT NULL DEFAULT 'PREPARING' CHECK (state IN ('PREPARING','READY','REJECTED','BUILD_FAILED')),
  reason text, quote_id uuid, created_at timestamptz NOT NULL DEFAULT now(),
  lease_until timestamptz, version bigint NOT NULL DEFAULT 0,
  UNIQUE(scope_hash,idempotency_key), UNIQUE(id,scope_hash), UNIQUE(id,report_id,scope_hash),
  CHECK ((state='READY') = (quote_id IS NOT NULL)),
  CHECK ((state IN ('REJECTED','BUILD_FAILED')) = (reason IS NOT NULL))
);
CREATE INDEX build_queue ON report_requests(created_at) WHERE state='PREPARING';
CREATE TABLE artifacts (
  report_id uuid PRIMARY KEY REFERENCES report_requests(report_id),
  scope_hash text NOT NULL REFERENCES access_scopes,
  report_sha256 text NOT NULL CHECK (report_sha256 ~ '^[0-9a-f]{64}$'),
  bundle_sha256 text NOT NULL CHECK (bundle_sha256 ~ '^[0-9a-f]{64}$'),
  report_size_bytes integer NOT NULL CHECK (report_size_bytes BETWEEN 1 AND 1048576),
  bundle_size_bytes integer NOT NULL CHECK (bundle_size_bytes BETWEEN 1 AND 10485760),
  metadata jsonb NOT NULL, published_at timestamptz NOT NULL DEFAULT now(),
  storage_state text NOT NULL DEFAULT 'AVAILABLE' CHECK (storage_state IN ('AVAILABLE','RECOVERY','DELETED')),
  UNIQUE(report_id,scope_hash), UNIQUE(report_id,report_sha256)
);
CREATE TABLE quotes (
  id uuid PRIMARY KEY, report_request_id uuid NOT NULL UNIQUE,
  scope_hash text NOT NULL, report_id uuid NOT NULL UNIQUE,
  state text NOT NULL DEFAULT 'READY' CHECK (state IN ('READY','PAYMENT_PENDING','PAYMENT_UNCERTAIN','PAID','EXPIRED','MANUAL_REVIEW')),
  network text NOT NULL CHECK (network='eip155:31611'), chain_id integer NOT NULL CHECK (chain_id=31611),
  asset text NOT NULL CHECK (asset='0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503'),
  amount_atomic numeric(78,0) NOT NULL CHECK (amount_atomic=10000000000000000),
  pay_to text NOT NULL CHECK (pay_to ~ '^0x[0-9a-f]{40}$' AND pay_to <> '0x0000000000000000000000000000000000000000'),
  expected_payer text NOT NULL CHECK (expected_payer ~ '^0x[0-9a-f]{40}$' AND expected_payer <> pay_to),
  expires_at timestamptz NOT NULL, preview jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(), version bigint NOT NULL DEFAULT 0,
  FOREIGN KEY(report_request_id,report_id,scope_hash) REFERENCES report_requests(id,report_id,scope_hash),
  FOREIGN KEY(report_id,scope_hash) REFERENCES artifacts(report_id,scope_hash),
  UNIQUE(id,report_id,scope_hash), UNIQUE(id,report_id), CHECK (expires_at > created_at)
);
ALTER TABLE report_requests ADD CONSTRAINT request_quote_fk FOREIGN KEY(quote_id) REFERENCES quotes(id) DEFERRABLE INITIALLY DEFERRED;
CREATE TABLE payment_attempts (
  id uuid PRIMARY KEY, quote_id uuid NOT NULL REFERENCES quotes,
  authorization_identity text NOT NULL UNIQUE CHECK (length(authorization_identity) BETWEEN 1 AND 512),
  identity_version text NOT NULL, authorization_valid_until timestamptz NOT NULL,
  correlation jsonb NOT NULL,
  state text NOT NULL CHECK (state IN ('RECEIVED','VERIFIED','SUBMITTING','CONFIRMED','REJECTED','UNKNOWN','MANUAL_REVIEW')),
  tx_hash text CHECK (tx_hash ~ '^0x[0-9a-f]{64}$'),
  created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
  submitted_at timestamptz, reconciliation_count integer NOT NULL DEFAULT 0 CHECK (reconciliation_count >= 0),
  next_reconcile_at timestamptz NOT NULL DEFAULT now(), version bigint NOT NULL DEFAULT 0,
  UNIQUE(id,quote_id)
);
CREATE UNIQUE INDEX one_active_attempt ON payment_attempts(quote_id) WHERE state <> 'REJECTED';
CREATE INDEX reconcile_queue ON payment_attempts(next_reconcile_at) WHERE state IN ('SUBMITTING','UNKNOWN');
CREATE TABLE chain_events (
  chain_id integer NOT NULL CHECK (chain_id=31611), tx_hash text NOT NULL CHECK (tx_hash ~ '^0x[0-9a-f]{64}$'),
  log_index integer NOT NULL CHECK (log_index>=0), block_hash text NOT NULL CHECK (block_hash ~ '^0x[0-9a-f]{64}$'),
  block_number bigint NOT NULL CHECK (block_number>=0), payment_attempt_id uuid NOT NULL REFERENCES payment_attempts,
  asset text NOT NULL CHECK (asset='0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503'),
  amount_atomic numeric(78,0) NOT NULL CHECK (amount_atomic=10000000000000000), payer text NOT NULL, pay_to text NOT NULL,
  PRIMARY KEY(chain_id,tx_hash,log_index), UNIQUE(payment_attempt_id)
);
CREATE TABLE receipts (
  payment_attempt_id uuid PRIMARY KEY REFERENCES payment_attempts, quote_id uuid NOT NULL UNIQUE REFERENCES quotes,
  report_id uuid NOT NULL, report_sha256 text NOT NULL,
  chain_id integer NOT NULL, tx_hash text NOT NULL, log_index integer NOT NULL,
  confirmed_at timestamptz NOT NULL, finality_policy_version text NOT NULL,
  response_header text NOT NULL CHECK (length(response_header) BETWEEN 1 AND 32768),
  FOREIGN KEY(chain_id,tx_hash,log_index) REFERENCES chain_events,
  FOREIGN KEY(report_id,report_sha256) REFERENCES artifacts(report_id,report_sha256),
  FOREIGN KEY(quote_id,report_id) REFERENCES quotes(id,report_id),
  FOREIGN KEY(payment_attempt_id,quote_id) REFERENCES payment_attempts(id,quote_id)
);
CREATE TABLE entitlements (
  quote_id uuid PRIMARY KEY, report_id uuid NOT NULL, scope_hash text NOT NULL,
  report_sha256 text NOT NULL, payment_attempt_id uuid NOT NULL UNIQUE REFERENCES receipts(payment_attempt_id),
  retain_until timestamptz NOT NULL,
  FOREIGN KEY(quote_id,report_id,scope_hash) REFERENCES quotes(id,report_id,scope_hash),
  FOREIGN KEY(report_id,report_sha256) REFERENCES artifacts(report_id,report_sha256),
  UNIQUE(quote_id,report_id,report_sha256)
);
CREATE TABLE delivery_attempts (
  id bigserial PRIMARY KEY, quote_id uuid NOT NULL REFERENCES entitlements,
  kind text NOT NULL CHECK (kind IN ('report','bundle')), state text NOT NULL DEFAULT 'ATTEMPTED' CHECK (state='ATTEMPTED'),
  request_id uuid NOT NULL, attempted_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE reconciliation_events (
  id bigserial PRIMARY KEY, payment_attempt_id uuid NOT NULL REFERENCES payment_attempts,
  code text NOT NULL, occurred_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE audit_events (
  id bigserial PRIMARY KEY, request_id uuid, quote_id uuid, payment_attempt_id uuid,
  event text NOT NULL, occurred_at timestamptz NOT NULL DEFAULT now()
);
CREATE FUNCTION forbid_audit_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'append-only record'; END $$;
CREATE TRIGGER audit_immutable BEFORE UPDATE OR DELETE ON audit_events FOR EACH ROW EXECUTE FUNCTION forbid_audit_mutation();
CREATE TRIGGER reconciliation_immutable BEFORE UPDATE OR DELETE ON reconciliation_events FOR EACH ROW EXECUTE FUNCTION forbid_audit_mutation();
CREATE TRIGGER receipt_immutable BEFORE UPDATE OR DELETE ON receipts FOR EACH ROW EXECUTE FUNCTION forbid_audit_mutation();
CREATE TRIGGER chain_event_immutable BEFORE UPDATE OR DELETE ON chain_events FOR EACH ROW EXECUTE FUNCTION forbid_audit_mutation();
CREATE FUNCTION enforce_state_transition() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE allowed boolean := false;
BEGIN
  IF OLD.state=NEW.state THEN RETURN NEW; END IF;
  IF TG_TABLE_NAME='report_requests' THEN allowed := OLD.state='PREPARING' AND NEW.state IN ('READY','REJECTED','BUILD_FAILED');
  ELSIF TG_TABLE_NAME='quotes' THEN allowed :=
    (OLD.state='READY' AND NEW.state IN ('PAYMENT_PENDING','EXPIRED')) OR
    (OLD.state='PAYMENT_PENDING' AND NEW.state IN ('PAYMENT_UNCERTAIN','PAID','READY','EXPIRED','MANUAL_REVIEW')) OR
    (OLD.state='PAYMENT_UNCERTAIN' AND NEW.state IN ('PAID','MANUAL_REVIEW')) OR
    (OLD.state='PAID' AND NEW.state='MANUAL_REVIEW') OR
    (OLD.state='MANUAL_REVIEW' AND NEW.state='PAID');
  ELSIF TG_TABLE_NAME='payment_attempts' THEN allowed :=
    (OLD.state='RECEIVED' AND NEW.state IN ('VERIFIED','REJECTED')) OR
    (OLD.state='VERIFIED' AND NEW.state IN ('SUBMITTING','REJECTED')) OR
    (OLD.state='SUBMITTING' AND NEW.state IN ('CONFIRMED','UNKNOWN','REJECTED')) OR
    (OLD.state='UNKNOWN' AND NEW.state IN ('CONFIRMED','MANUAL_REVIEW')) OR
    (OLD.state='CONFIRMED' AND NEW.state='MANUAL_REVIEW') OR
    (OLD.state='MANUAL_REVIEW' AND NEW.state='CONFIRMED');
  END IF;
  IF NOT allowed THEN RAISE EXCEPTION 'invalid state transition'; END IF;
  NEW.version := OLD.version+1;
  RETURN NEW;
END $$;
CREATE TRIGGER request_transition BEFORE UPDATE ON report_requests FOR EACH ROW EXECUTE FUNCTION enforce_state_transition();
CREATE TRIGGER quote_transition BEFORE UPDATE ON quotes FOR EACH ROW EXECUTE FUNCTION enforce_state_transition();
CREATE TRIGGER attempt_transition BEFORE UPDATE ON payment_attempts FOR EACH ROW EXECUTE FUNCTION enforce_state_transition();
CREATE FUNCTION immutable_ledger_identity() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_TABLE_NAME='quotes' AND
    (to_jsonb(NEW)-ARRAY['state','version']) IS DISTINCT FROM (to_jsonb(OLD)-ARRAY['state','version'])
    THEN RAISE EXCEPTION 'immutable quote terms'; END IF;
  IF TG_TABLE_NAME='artifacts' AND
    (to_jsonb(NEW)-'storage_state') IS DISTINCT FROM (to_jsonb(OLD)-'storage_state')
    THEN RAISE EXCEPTION 'immutable artifact identity'; END IF;
  IF TG_TABLE_NAME='report_requests' AND
    (to_jsonb(NEW)-ARRAY['state','reason','quote_id','lease_until','version']) IS DISTINCT FROM
    (to_jsonb(OLD)-ARRAY['state','reason','quote_id','lease_until','version'])
    THEN RAISE EXCEPTION 'immutable request identity'; END IF;
  IF TG_TABLE_NAME='payment_attempts' AND
    (to_jsonb(NEW)-ARRAY['state','tx_hash','updated_at','submitted_at','reconciliation_count','next_reconcile_at','version']) IS DISTINCT FROM
    (to_jsonb(OLD)-ARRAY['state','tx_hash','updated_at','submitted_at','reconciliation_count','next_reconcile_at','version'])
    THEN RAISE EXCEPTION 'immutable authorization identity'; END IF;
  IF TG_TABLE_NAME='payment_attempts' AND OLD.tx_hash IS NOT NULL AND NEW.tx_hash IS DISTINCT FROM OLD.tx_hash
    THEN RAISE EXCEPTION 'immutable transaction association'; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER quote_identity BEFORE UPDATE ON quotes FOR EACH ROW EXECUTE FUNCTION immutable_ledger_identity();
CREATE TRIGGER artifact_identity BEFORE UPDATE ON artifacts FOR EACH ROW EXECUTE FUNCTION immutable_ledger_identity();
CREATE TRIGGER request_identity BEFORE UPDATE ON report_requests FOR EACH ROW EXECUTE FUNCTION immutable_ledger_identity();
CREATE TRIGGER authorization_identity BEFORE UPDATE ON payment_attempts FOR EACH ROW EXECUTE FUNCTION immutable_ledger_identity();
CREATE TABLE rate_buckets (
  bucket_hash text PRIMARY KEY, window_start timestamptz NOT NULL, hits integer NOT NULL CHECK (hits>0)
);
