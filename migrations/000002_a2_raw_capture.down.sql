BEGIN;

DO $$
BEGIN
    IF pg_catalog.to_regnamespace('a2') IS NOT NULL THEN
        IF EXISTS (
            SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'a2_writer'
        ) THEN
            EXECUTE 'REVOKE SELECT, INSERT ON ALL TABLES IN SCHEMA a2 FROM a2_writer';
            EXECUTE 'REVOKE USAGE ON SCHEMA a2 FROM a2_writer';
            IF pg_catalog.to_regprocedure(
                'a2.ensure_day_partitions(date)'
            ) IS NOT NULL THEN
                EXECUTE
                    'REVOKE EXECUTE ON FUNCTION '
                    'a2.ensure_day_partitions(date) FROM a2_writer';
            END IF;
        END IF;
        IF EXISTS (
            SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'a2_maintainer'
        ) THEN
            EXECUTE 'REVOKE USAGE ON SCHEMA a2 FROM a2_maintainer';
            IF pg_catalog.to_regprocedure(
                'a2.drop_expired_raw_partitions(date)'
            ) IS NOT NULL THEN
                EXECUTE
                    'REVOKE EXECUTE ON FUNCTION '
                    'a2.drop_expired_raw_partitions(date) FROM a2_maintainer';
            END IF;
        END IF;
    END IF;
END;
$$;

DROP SCHEMA IF EXISTS a2 CASCADE;

COMMIT;
