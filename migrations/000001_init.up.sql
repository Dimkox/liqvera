BEGIN;

CREATE TABLE tenants (
    id uuid PRIMARY KEY,
    name text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE users (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenants(id),
    telegram_user_id bigint,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, id),
    UNIQUE (tenant_id, telegram_user_id)
);

CREATE TABLE venue_accounts (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenants(id),
    user_id uuid NOT NULL,
    venue text NOT NULL,
    venue_account_ref text NOT NULL,
    trading_enabled boolean NOT NULL DEFAULT false,
    withdrawals_enabled boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, id),
    UNIQUE (tenant_id, venue, venue_account_ref),
    FOREIGN KEY (tenant_id, user_id) REFERENCES users(tenant_id, id),
    CHECK (withdrawals_enabled = false)
);

CREATE TABLE credential_envelopes (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenants(id),
    account_id uuid NOT NULL,
    key_class text NOT NULL,
    key_version integer NOT NULL CHECK (key_version > 0),
    wrapped_dek bytea NOT NULL,
    ciphertext bytea NOT NULL,
    nonce bytea NOT NULL,
    aad jsonb NOT NULL,
    revoked_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, id),
    UNIQUE (tenant_id, account_id, key_class, key_version),
    FOREIGN KEY (tenant_id, account_id) REFERENCES venue_accounts(tenant_id, id),
    CHECK (octet_length(wrapped_dek) > 0),
    CHECK (octet_length(ciphertext) > 0),
    CHECK (octet_length(nonce) >= 12)
);

CREATE TABLE instrument_mappings (
    tenant_id uuid NOT NULL REFERENCES tenants(id),
    canonical_instrument_id text NOT NULL,
    venue text NOT NULL,
    venue_symbol text NOT NULL,
    contract_multiplier numeric(38, 8) NOT NULL,
    tick_size numeric(38, 8) NOT NULL,
    step_size numeric(38, 8) NOT NULL,
    verified_at timestamptz,
    blocked_reason text,
    PRIMARY KEY (tenant_id, canonical_instrument_id, venue),
    UNIQUE (tenant_id, venue, venue_symbol),
    CHECK (contract_multiplier > 0),
    CHECK (tick_size > 0),
    CHECK (step_size > 0),
    CHECK (verified_at IS NOT NULL OR blocked_reason IS NOT NULL)
);

CREATE TABLE execution_groups (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenants(id),
    account_id uuid NOT NULL,
    idempotency_key text NOT NULL,
    canonical_instrument_id text NOT NULL,
    state text NOT NULL,
    risk_reservation_usd numeric(38, 8) NOT NULL DEFAULT 0,
    primary_delta_base numeric(38, 8) NOT NULL DEFAULT 0,
    hedge_delta_base numeric(38, 8) NOT NULL DEFAULT 0,
    residual_delta_base numeric(38, 8) NOT NULL DEFAULT 0,
    failure_reason text,
    version bigint NOT NULL DEFAULT 0 CHECK (version >= 0),
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL,
    UNIQUE (tenant_id, id),
    UNIQUE (tenant_id, idempotency_key),
    FOREIGN KEY (tenant_id, account_id) REFERENCES venue_accounts(tenant_id, id),
    CHECK (state IN (
        'created', 'preflight_ok', 'reserved', 'submitting', 'partially_filled',
        'reconciling', 'hedging', 'open', 'closing', 'closed', 'failed',
        'manual_intervention'
    )),
    CHECK (risk_reservation_usd >= 0)
);

CREATE TABLE execution_legs (
    tenant_id uuid NOT NULL REFERENCES tenants(id),
    execution_id uuid NOT NULL,
    leg_index smallint NOT NULL CHECK (leg_index IN (0, 1)),
    account_id uuid NOT NULL,
    venue text NOT NULL,
    canonical_instrument_id text NOT NULL,
    side text NOT NULL CHECK (side IN ('buy', 'sell')),
    order_type text NOT NULL CHECK (order_type IN ('limit', 'market')),
    time_in_force text NOT NULL CHECK (time_in_force IN ('gtc', 'ioc', 'fok', 'post_only')),
    requested_base_quantity numeric(38, 8) NOT NULL CHECK (requested_base_quantity > 0),
    limit_price numeric(38, 8) NOT NULL CHECK (limit_price >= 0),
    filled_base_quantity numeric(38, 8) NOT NULL DEFAULT 0,
    client_order_id text,
    venue_order_id text,
    state text NOT NULL,
    updated_at timestamptz NOT NULL,
    PRIMARY KEY (tenant_id, execution_id, leg_index),
    FOREIGN KEY (tenant_id, execution_id) REFERENCES execution_groups(tenant_id, id),
    FOREIGN KEY (tenant_id, account_id) REFERENCES venue_accounts(tenant_id, id),
    CHECK (filled_base_quantity >= 0 AND filled_base_quantity <= requested_base_quantity),
    CHECK (state IN ('pending', 'submitted', 'open', 'partial', 'filled', 'cancelled', 'rejected', 'unknown'))
);

CREATE UNIQUE INDEX execution_legs_client_order_unique
    ON execution_legs (tenant_id, account_id, venue, client_order_id)
    WHERE client_order_id IS NOT NULL;

CREATE TABLE order_ownership (
    tenant_id uuid NOT NULL REFERENCES tenants(id),
    account_id uuid NOT NULL,
    venue text NOT NULL,
    client_order_id text NOT NULL,
    venue_order_id text,
    execution_id uuid NOT NULL,
    leg_index smallint NOT NULL CHECK (leg_index IN (0, 1)),
    claimed_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, account_id, venue, client_order_id),
    FOREIGN KEY (tenant_id, account_id) REFERENCES venue_accounts(tenant_id, id),
    FOREIGN KEY (tenant_id, execution_id, leg_index) REFERENCES execution_legs(tenant_id, execution_id, leg_index)
);

CREATE UNIQUE INDEX order_ownership_venue_order_unique
    ON order_ownership (tenant_id, account_id, venue, venue_order_id)
    WHERE venue_order_id IS NOT NULL;

CREATE TABLE execution_events (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenants(id),
    execution_id uuid NOT NULL,
    event_key text NOT NULL,
    event_type text NOT NULL,
    payload jsonb NOT NULL,
    observed_at timestamptz NOT NULL,
    recorded_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, id),
    UNIQUE (tenant_id, execution_id, event_key),
    FOREIGN KEY (tenant_id, execution_id) REFERENCES execution_groups(tenant_id, id)
);

CREATE TABLE risk_reservations (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenants(id),
    account_id uuid NOT NULL,
    execution_id uuid NOT NULL,
    reserved_usd numeric(38, 8) NOT NULL CHECK (reserved_usd > 0),
    status text NOT NULL CHECK (status IN ('active', 'consumed', 'released', 'expired')),
    approved_at timestamptz NOT NULL,
    expires_at timestamptz NOT NULL,
    released_at timestamptz,
    UNIQUE (tenant_id, id),
    UNIQUE (tenant_id, execution_id),
    FOREIGN KEY (tenant_id, account_id) REFERENCES venue_accounts(tenant_id, id),
    FOREIGN KEY (tenant_id, execution_id) REFERENCES execution_groups(tenant_id, id),
    CHECK (expires_at > approved_at)
);

CREATE TABLE outbox_events (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenants(id),
    aggregate_type text NOT NULL,
    aggregate_id uuid NOT NULL,
    event_type text NOT NULL,
    payload jsonb NOT NULL,
    available_at timestamptz NOT NULL DEFAULT now(),
    claimed_at timestamptz,
    published_at timestamptz,
    attempts integer NOT NULL DEFAULT 0 CHECK (attempts >= 0),
    last_error text,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, id)
);

CREATE INDEX outbox_events_ready_idx
    ON outbox_events (available_at, created_at)
    WHERE published_at IS NULL AND claimed_at IS NULL;

CREATE TABLE audit_log (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenants(id),
    user_id uuid,
    action text NOT NULL,
    resource_type text NOT NULL,
    resource_id text NOT NULL,
    command_nonce text,
    idempotency_key text,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id, user_id) REFERENCES users(tenant_id, id)
);

CREATE OR REPLACE FUNCTION reject_immutable_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION '% is append-only', TG_TABLE_NAME;
END;
$$;

CREATE TRIGGER execution_events_immutable
    BEFORE UPDATE OR DELETE ON execution_events
    FOR EACH ROW EXECUTE FUNCTION reject_immutable_mutation();

CREATE TRIGGER audit_log_immutable
    BEFORE UPDATE OR DELETE ON audit_log
    FOR EACH ROW EXECUTE FUNCTION reject_immutable_mutation();

DO $$
DECLARE
    table_name text;
BEGIN
    FOREACH table_name IN ARRAY ARRAY[
        'users', 'venue_accounts', 'credential_envelopes', 'instrument_mappings',
        'execution_groups', 'execution_legs', 'order_ownership', 'execution_events',
        'risk_reservations', 'outbox_events', 'audit_log'
    ]
    LOOP
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', table_name);
        EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY', table_name);
        EXECUTE format(
            'CREATE POLICY tenant_isolation ON %I USING (tenant_id = NULLIF(current_setting(''app.tenant_id'', true), '''')::uuid) WITH CHECK (tenant_id = NULLIF(current_setting(''app.tenant_id'', true), '''')::uuid)',
            table_name
        );
    END LOOP;
END;
$$;

COMMIT;
