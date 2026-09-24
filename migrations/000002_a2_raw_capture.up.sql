BEGIN;

DO $$
DECLARE
    role_name text;
    candidate record;
BEGIN
    FOREACH role_name IN ARRAY ARRAY['a2_writer', 'a2_maintainer']
    LOOP
        IF NOT EXISTS (
            SELECT 1
              FROM pg_catalog.pg_roles
             WHERE rolname = role_name
        ) THEN
            EXECUTE format(
                'CREATE ROLE %I NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE '
                'NOINHERIT NOREPLICATION NOBYPASSRLS',
                role_name
            );
        END IF;

        SELECT *
          INTO STRICT candidate
          FROM pg_catalog.pg_roles
         WHERE rolname = role_name;
        IF candidate.rolcanlogin
           OR candidate.rolsuper
           OR candidate.rolcreatedb
           OR candidate.rolcreaterole
           OR candidate.rolinherit
           OR candidate.rolreplication
           OR candidate.rolbypassrls
           OR EXISTS (
               SELECT 1
                 FROM pg_catalog.pg_auth_members membership
                WHERE membership.member = candidate.oid
           ) THEN
            RAISE EXCEPTION
                'unsafe A2 role attributes or inherited memberships: %',
                role_name
                USING ERRCODE = '55000';
        END IF;
    END LOOP;
END;
$$;

CREATE SCHEMA a2 AUTHORIZATION CURRENT_USER;

CREATE TABLE a2.raw_capture_runs (
    run_id uuid NOT NULL,
    event_index bigint NOT NULL CHECK (event_index >= 0),
    state text NOT NULL CHECK (state IN ('PLANNED', 'WARMING', 'MEASURING', 'PASS', 'FAIL')),
    occurred_at bigint NOT NULL CHECK (occurred_at >= 0),
    boot_id uuid,
    measured_start bigint CHECK (measured_start >= 0),
    measured_end bigint CHECK (measured_end >= 0),
    reason_code text,
    run_manifest_json jsonb,
    manifest_sha256 text CHECK (manifest_sha256 ~ '^[0-9a-f]{64}$'),
    PRIMARY KEY (run_id, event_index),
    CHECK ((run_manifest_json IS NULL) = (manifest_sha256 IS NULL)),
    CHECK (
        measured_start IS NULL
        OR measured_end IS NULL
        OR measured_end > measured_start
    )
);

CREATE UNIQUE INDEX raw_capture_runs_one_terminal
    ON a2.raw_capture_runs (run_id)
    WHERE state IN ('PASS', 'FAIL');

CREATE TABLE a2.raw_instrument_mappings (
    run_id uuid NOT NULL,
    mapping_id text NOT NULL CHECK (mapping_id <> ''),
    rank integer NOT NULL CHECK (rank > 0),
    identity_json jsonb NOT NULL,
    hyperliquid_market_id text NOT NULL CHECK (hyperliquid_market_id <> ''),
    lighter_market_id text NOT NULL CHECK (lighter_market_id <> ''),
    hyperliquid_quote_volume numeric NOT NULL CHECK (hyperliquid_quote_volume > 0),
    lighter_quote_volume numeric NOT NULL CHECK (lighter_quote_volume > 0),
    shared_liquidity_score numeric NOT NULL CHECK (shared_liquidity_score > 0),
    hyperliquid_discovery_sha256 text NOT NULL
        CHECK (hyperliquid_discovery_sha256 ~ '^[0-9a-f]{64}$'),
    lighter_discovery_sha256 text NOT NULL
        CHECK (lighter_discovery_sha256 ~ '^[0-9a-f]{64}$'),
    PRIMARY KEY (run_id, mapping_id),
    UNIQUE (run_id, rank),
    UNIQUE (run_id, hyperliquid_market_id),
    UNIQUE (run_id, lighter_market_id)
);

CREATE TABLE a2.raw_control_evidence (
    run_id uuid NOT NULL,
    venue text NOT NULL CHECK (venue IN ('HYPERLIQUID', 'LIGHTER')),
    evidence_kind text NOT NULL CHECK (
        evidence_kind IN (
            'HYPERLIQUID_META_AND_ASSET_CTXS',
            'LIGHTER_ORDER_BOOKS',
            'LIGHTER_MARKET_STATS_ALL'
        )
    ),
    transport text NOT NULL CHECK (transport IN ('HTTPS_REST', 'WSS_TEXT')),
    source_uri text NOT NULL,
    observed_wall_ns bigint NOT NULL CHECK (observed_wall_ns >= 0),
    payload bytea NOT NULL,
    payload_sha256 text NOT NULL
        CHECK (payload_sha256 ~ '^[0-9a-f]{64}$'),
    PRIMARY KEY (run_id, evidence_kind),
    CHECK (octet_length(payload) > 0),
    CHECK (octet_length(payload) <= 8388608),
    CHECK (
        (
            venue = 'HYPERLIQUID'
            AND evidence_kind = 'HYPERLIQUID_META_AND_ASSET_CTXS'
            AND transport = 'HTTPS_REST'
            AND source_uri = 'https://api.hyperliquid.xyz/info'
        )
        OR (
            venue = 'LIGHTER'
            AND evidence_kind = 'LIGHTER_ORDER_BOOKS'
            AND transport = 'HTTPS_REST'
            AND source_uri =
                'https://mainnet.zklighter.elliot.ai/api/v1/orderBooks'
        )
        OR (
            venue = 'LIGHTER'
            AND evidence_kind = 'LIGHTER_MARKET_STATS_ALL'
            AND transport = 'WSS_TEXT'
            AND source_uri =
                'wss://mainnet.zklighter.elliot.ai/stream?readonly=true'
        )
    )
);

CREATE TABLE a2.raw_feed_connections (
    event_day date NOT NULL,
    run_id uuid NOT NULL,
    venue text NOT NULL CHECK (venue IN ('HYPERLIQUID', 'LIGHTER')),
    venue_market_id text CHECK (
        venue_market_id IS NULL OR venue_market_id <> ''
    ),
    channel text NOT NULL CHECK (channel <> ''),
    connection_epoch bigint NOT NULL CHECK (connection_epoch >= 0),
    event_kind text NOT NULL CHECK (event_kind <> ''),
    occurred_wall_ns bigint NOT NULL CHECK (occurred_wall_ns >= 0),
    boot_id uuid NOT NULL,
    websocket_library text NOT NULL CHECK (websocket_library <> ''),
    websocket_library_version text NOT NULL CHECK (websocket_library_version <> ''),
    negotiated_extensions text[] NOT NULL,
    reason_code text,
    PRIMARY KEY (
        event_day,
        run_id,
        venue,
        channel,
        connection_epoch,
        occurred_wall_ns,
        event_kind
    )
) PARTITION BY RANGE (event_day);

CREATE TABLE a2.raw_wire_batches (
    capture_day date NOT NULL,
    run_id uuid NOT NULL,
    batch_sequence bigint NOT NULL CHECK (batch_sequence >= 0),
    first_ingest_index bigint NOT NULL CHECK (first_ingest_index >= 0),
    last_ingest_index bigint NOT NULL CHECK (last_ingest_index >= first_ingest_index),
    first_wall_ns bigint NOT NULL CHECK (first_wall_ns >= 0),
    last_wall_ns bigint NOT NULL CHECK (last_wall_ns >= first_wall_ns),
    first_monotonic_ns bigint NOT NULL CHECK (first_monotonic_ns >= 0),
    last_monotonic_ns bigint NOT NULL CHECK (last_monotonic_ns >= first_monotonic_ns),
    frame_count integer NOT NULL CHECK (frame_count > 0),
    uncompressed_bytes bigint NOT NULL CHECK (uncompressed_bytes > 0),
    compressed_bytes bigint NOT NULL CHECK (compressed_bytes > 0),
    uncompressed_sha256 text NOT NULL
        CHECK (uncompressed_sha256 ~ '^[0-9a-f]{64}$'),
    compressed_sha256 text NOT NULL
        CHECK (compressed_sha256 ~ '^[0-9a-f]{64}$'),
    compression_profile text NOT NULL
        CHECK (compression_profile = 'gzip-raw-deflate-6-mtime0-os255/v1'),
    gzip_payload bytea NOT NULL,
    PRIMARY KEY (capture_day, run_id, batch_sequence),
    CHECK (frame_count = last_ingest_index - first_ingest_index + 1),
    CHECK (octet_length(gzip_payload) = compressed_bytes)
) PARTITION BY RANGE (capture_day);

CREATE TABLE a2.raw_decoder_observations (
    observation_day date NOT NULL,
    run_id uuid NOT NULL,
    ingest_index bigint NOT NULL CHECK (ingest_index >= 0),
    decoder_version text NOT NULL CHECK (decoder_version <> ''),
    message_class text NOT NULL CHECK (
        message_class IN (
            'CONTROL', 'SNAPSHOT', 'DELTA', 'TRADE',
            'MARKET_STATS', 'FUNDING', 'UNKNOWN'
        )
    ),
    continuity_state text NOT NULL CHECK (
        continuity_state IN (
            'NOT_APPLICABLE', 'VALID', 'GAP_OPEN',
            'AWAITING_SNAPSHOT', 'INVALID_SOURCE_TIME'
        )
    ),
    error_code text,
    error_detail text CHECK (error_detail IS NULL OR length(error_detail) <= 256),
    PRIMARY KEY (observation_day, run_id, ingest_index)
) PARTITION BY RANGE (observation_day);

CREATE TABLE a2.raw_quality_minutes (
    minute_day date NOT NULL,
    run_id uuid NOT NULL,
    venue text NOT NULL CHECK (venue IN ('HYPERLIQUID', 'LIGHTER')),
    venue_market_id text NOT NULL CHECK (venue_market_id <> ''),
    channel text NOT NULL CHECK (channel <> ''),
    minute_start bigint NOT NULL CHECK (minute_start >= 0),
    expected_slots integer NOT NULL CHECK (expected_slots >= 0),
    valid_slots integer NOT NULL CHECK (valid_slots >= 0),
    max_source_age_ms numeric CHECK (max_source_age_ms >= 0),
    max_cross_venue_receive_skew_ms numeric
        CHECK (max_cross_venue_receive_skew_ms >= 0),
    invalid_reason_counts jsonb NOT NULL,
    quality_sha256 text NOT NULL CHECK (quality_sha256 ~ '^[0-9a-f]{64}$'),
    PRIMARY KEY (
        minute_day,
        run_id,
        venue,
        venue_market_id,
        channel,
        minute_start
    ),
    CHECK (valid_slots <= expected_slots)
) PARTITION BY RANGE (minute_day);

CREATE TABLE a2.raw_soak_decisions (
    run_id uuid PRIMARY KEY,
    decided_at bigint NOT NULL CHECK (decided_at >= 0),
    decision text NOT NULL CHECK (decision IN ('PASS', 'FAIL')),
    report_sha256 text NOT NULL CHECK (report_sha256 ~ '^[0-9a-f]{64}$'),
    reason_codes text[] NOT NULL,
    measured_start bigint NOT NULL CHECK (measured_start >= 0),
    measured_end bigint NOT NULL CHECK (measured_end > measured_start)
        CHECK (
            decision = 'FAIL'
            OR measured_end - measured_start = 432000000000000
        ),
    CHECK (
        (
            decision = 'PASS'
            AND cardinality(reason_codes) = 0
        )
        OR (
            decision = 'FAIL'
            AND cardinality(reason_codes) > 0
        )
    ),
    CHECK (array_position(reason_codes, NULL) IS NULL)
);

CREATE OR REPLACE FUNCTION a2.reject_immutable_mutation()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog, a2
AS $$
BEGIN
    RAISE EXCEPTION '% is append-only', TG_TABLE_NAME
        USING ERRCODE = '55000';
END;
$$;

CREATE OR REPLACE FUNCTION a2.enforce_run_transition()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog, a2
AS $$
DECLARE
    previous_index bigint;
    previous_state text;
    previous_measured_start bigint;
    previous_measured_end bigint;
BEGIN
    PERFORM pg_advisory_xact_lock(
        (('x' || substr(md5(NEW.run_id::text), 1, 16))::bit(64)::bigint)
    );

    SELECT event_index, state, measured_start, measured_end
      INTO previous_index, previous_state,
           previous_measured_start, previous_measured_end
      FROM a2.raw_capture_runs
     WHERE run_id = NEW.run_id
     ORDER BY event_index DESC
     LIMIT 1;

    IF previous_index IS NULL THEN
        IF NEW.event_index <> 0
           OR NEW.state <> 'PLANNED'
           OR NEW.measured_start IS NOT NULL
           OR NEW.measured_end IS NOT NULL
           OR NEW.reason_code IS NOT NULL THEN
            RAISE EXCEPTION 'first run event must be PLANNED at index zero'
                USING ERRCODE = '55000';
        END IF;
        RETURN NEW;
    END IF;

    IF NEW.event_index <> previous_index + 1 THEN
        RAISE EXCEPTION 'run event index is not contiguous'
            USING ERRCODE = '55000';
    END IF;

    IF NEW.state = 'FAIL' AND NEW.reason_code IS NULL THEN
        RAISE EXCEPTION 'failed run requires a typed reason'
            USING ERRCODE = '55000';
    END IF;

    IF NEW.state IN ('PLANNED', 'MEASURING', 'PASS')
       AND NEW.reason_code IS NOT NULL THEN
        RAISE EXCEPTION 'state cannot carry a failure reason'
            USING ERRCODE = '55000';
    END IF;

    IF NEW.state = 'WARMING'
       AND (
           (
               previous_state = 'PLANNED'
               AND NEW.reason_code IS NOT NULL
           )
           OR (
               previous_state = 'WARMING'
               AND NEW.reason_code IS DISTINCT FROM 'WARMUP_RESET'
           )
       ) THEN
        RAISE EXCEPTION 'warming reset reason is invalid'
            USING ERRCODE = '55000';
    END IF;

    IF (NEW.measured_start IS NULL) <> (NEW.measured_end IS NULL) THEN
        RAISE EXCEPTION 'measured window bounds must be a pair'
            USING ERRCODE = '55000';
    END IF;

    IF NEW.state IN ('PLANNED', 'WARMING')
       AND NEW.measured_start IS NOT NULL THEN
        RAISE EXCEPTION 'state cannot carry a measured window'
            USING ERRCODE = '55000';
    END IF;

    IF NEW.state IN ('MEASURING', 'PASS')
       AND (
           NEW.measured_start IS NULL
           OR NEW.measured_end - NEW.measured_start <> 432000000000000
       ) THEN
        RAISE EXCEPTION 'measured window must be exactly five days'
            USING ERRCODE = '55000';
    END IF;

    IF NEW.state = 'FAIL'
       AND (
           (
               previous_state <> 'MEASURING'
               AND NEW.measured_start IS NOT NULL
           )
           OR (
               NEW.measured_start IS NOT NULL
               AND NEW.measured_end - NEW.measured_start
                   <> 432000000000000
           )
       ) THEN
        RAISE EXCEPTION 'failed run has an invalid measured window'
            USING ERRCODE = '55000';
    END IF;

    IF previous_state = 'MEASURING'
       AND (
           NEW.measured_start IS DISTINCT FROM previous_measured_start
           OR NEW.measured_end IS DISTINCT FROM previous_measured_end
       ) THEN
        RAISE EXCEPTION 'terminal event changed the measured window'
            USING ERRCODE = '55000';
    END IF;

    IF NOT (
        (previous_state = 'PLANNED' AND NEW.state IN ('WARMING', 'FAIL'))
        OR (previous_state = 'WARMING' AND NEW.state IN ('WARMING', 'MEASURING', 'FAIL'))
        OR (previous_state = 'MEASURING' AND NEW.state IN ('PASS', 'FAIL'))
    ) THEN
        RAISE EXCEPTION 'invalid run lifecycle transition'
            USING ERRCODE = '55000';
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER raw_capture_runs_transition
    BEFORE INSERT ON a2.raw_capture_runs
    FOR EACH ROW EXECUTE FUNCTION a2.enforce_run_transition();

CREATE TRIGGER raw_capture_runs_immutable
    BEFORE UPDATE OR DELETE ON a2.raw_capture_runs
    FOR EACH ROW EXECUTE FUNCTION a2.reject_immutable_mutation();

CREATE TRIGGER raw_instrument_mappings_immutable
    BEFORE UPDATE OR DELETE ON a2.raw_instrument_mappings
    FOR EACH ROW EXECUTE FUNCTION a2.reject_immutable_mutation();

CREATE TRIGGER raw_control_evidence_immutable
    BEFORE UPDATE OR DELETE ON a2.raw_control_evidence
    FOR EACH ROW EXECUTE FUNCTION a2.reject_immutable_mutation();

CREATE TRIGGER raw_feed_connections_immutable
    BEFORE UPDATE OR DELETE ON a2.raw_feed_connections
    FOR EACH ROW EXECUTE FUNCTION a2.reject_immutable_mutation();

CREATE TRIGGER raw_wire_batches_immutable
    BEFORE UPDATE OR DELETE ON a2.raw_wire_batches
    FOR EACH ROW EXECUTE FUNCTION a2.reject_immutable_mutation();

CREATE TRIGGER raw_decoder_observations_immutable
    BEFORE UPDATE OR DELETE ON a2.raw_decoder_observations
    FOR EACH ROW EXECUTE FUNCTION a2.reject_immutable_mutation();

CREATE TRIGGER raw_quality_minutes_immutable
    BEFORE UPDATE OR DELETE ON a2.raw_quality_minutes
    FOR EACH ROW EXECUTE FUNCTION a2.reject_immutable_mutation();

CREATE TRIGGER raw_soak_decisions_immutable
    BEFORE UPDATE OR DELETE ON a2.raw_soak_decisions
    FOR EACH ROW EXECUTE FUNCTION a2.reject_immutable_mutation();

CREATE OR REPLACE FUNCTION a2.ensure_day_partitions(target_day date)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, a2
AS $$
DECLARE
    utc_day date := (CURRENT_TIMESTAMP AT TIME ZONE 'UTC')::date;
    partition_name text;
BEGIN
    IF target_day IS NULL
       OR target_day NOT IN (utc_day - 1, utc_day) THEN
        RAISE EXCEPTION 'target_day is outside the authorized UTC window'
            USING ERRCODE = '22023';
    END IF;

    PERFORM pg_advisory_xact_lock(
        ((
            'x' || substr(
                md5('a2.partition:' || target_day::text),
                1,
                16
            )
        )::bit(64)::bigint)
    );

    partition_name := 'raw_feed_connections_' || to_char(target_day, 'YYYYMMDD');
    IF partition_name !~ '^raw_feed_connections_[0-9]{8}$' THEN
        RAISE EXCEPTION 'invalid partition identifier' USING ERRCODE = '22023';
    END IF;
    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS a2.%I PARTITION OF a2.raw_feed_connections '
        'FOR VALUES FROM (%L) TO (%L)',
        partition_name,
        target_day,
        target_day + 1
    );

    partition_name := 'raw_wire_batches_' || to_char(target_day, 'YYYYMMDD');
    IF partition_name !~ '^raw_wire_batches_[0-9]{8}$' THEN
        RAISE EXCEPTION 'invalid partition identifier' USING ERRCODE = '22023';
    END IF;
    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS a2.%I PARTITION OF a2.raw_wire_batches '
        'FOR VALUES FROM (%L) TO (%L)',
        partition_name,
        target_day,
        target_day + 1
    );

    partition_name := 'raw_decoder_observations_' || to_char(target_day, 'YYYYMMDD');
    IF partition_name !~ '^raw_decoder_observations_[0-9]{8}$' THEN
        RAISE EXCEPTION 'invalid partition identifier' USING ERRCODE = '22023';
    END IF;
    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS a2.%I PARTITION OF a2.raw_decoder_observations '
        'FOR VALUES FROM (%L) TO (%L)',
        partition_name,
        target_day,
        target_day + 1
    );

    partition_name := 'raw_quality_minutes_' || to_char(target_day, 'YYYYMMDD');
    IF partition_name !~ '^raw_quality_minutes_[0-9]{8}$' THEN
        RAISE EXCEPTION 'invalid partition identifier' USING ERRCODE = '22023';
    END IF;
    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS a2.%I PARTITION OF a2.raw_quality_minutes '
        'FOR VALUES FROM (%L) TO (%L)',
        partition_name,
        target_day,
        target_day + 1
    );
END;
$$;

CREATE OR REPLACE FUNCTION a2.drop_expired_raw_partitions(reference_day date)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, a2
AS $$
DECLARE
    utc_day date := (CURRENT_TIMESTAMP AT TIME ZONE 'UTC')::date;
    partition_name text;
    partition_day date;
    has_nonterminal boolean;
BEGIN
    IF reference_day IS DISTINCT FROM utc_day THEN
        RAISE EXCEPTION 'reference_day must be the server UTC date'
            USING ERRCODE = '22023';
    END IF;

    FOR partition_name IN
        SELECT child.relname
          FROM pg_catalog.pg_inherits inheritance
          JOIN pg_catalog.pg_class child
            ON child.oid = inheritance.inhrelid
          JOIN pg_catalog.pg_class parent
            ON parent.oid = inheritance.inhparent
          JOIN pg_catalog.pg_namespace child_namespace
            ON child_namespace.oid = child.relnamespace
          JOIN pg_catalog.pg_namespace parent_namespace
            ON parent_namespace.oid = parent.relnamespace
         WHERE child_namespace.nspname = 'a2'
           AND parent_namespace.nspname = 'a2'
           AND parent.relname = 'raw_wire_batches'
         ORDER BY child.relname
    LOOP
        IF partition_name !~ '^raw_wire_batches_[0-9]{8}$' THEN
            RAISE EXCEPTION 'invalid partition identifier' USING ERRCODE = '22023';
        END IF;
        partition_day := to_date(
            substring(partition_name FROM '[0-9]{8}$'),
            'YYYYMMDD'
        );
        IF partition_day < utc_day - 7 THEN
            EXECUTE format(
                'LOCK TABLE a2.%I IN ACCESS EXCLUSIVE MODE',
                partition_name
            );
            EXECUTE format(
                'SELECT EXISTS ('
                'SELECT 1 FROM a2.%I batch '
                'WHERE NOT EXISTS ('
                'SELECT 1 FROM a2.raw_capture_runs run_event '
                'WHERE run_event.run_id = batch.run_id '
                'AND run_event.state IN (''PASS'', ''FAIL'')'
                '))',
                partition_name
            ) INTO has_nonterminal;
            IF has_nonterminal THEN
                RAISE EXCEPTION
                    'raw wire partition contains a nonterminal run'
                    USING ERRCODE = '55000';
            END IF;
            EXECUTE format('DROP TABLE a2.%I', partition_name);
        END IF;
    END LOOP;
END;
$$;

REVOKE ALL ON FUNCTION a2.ensure_day_partitions(date) FROM PUBLIC;
REVOKE ALL ON FUNCTION a2.drop_expired_raw_partitions(date) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION a2.ensure_day_partitions(date) TO a2_writer;
GRANT EXECUTE ON FUNCTION a2.drop_expired_raw_partitions(date) TO a2_maintainer;

GRANT USAGE ON SCHEMA a2 TO a2_writer;
GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA a2 TO a2_writer;
REVOKE UPDATE, DELETE, TRUNCATE ON ALL TABLES IN SCHEMA a2 FROM a2_writer;
GRANT USAGE ON SCHEMA a2 TO a2_maintainer;

COMMIT;
