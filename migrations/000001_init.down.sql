BEGIN;

DROP TABLE IF EXISTS audit_log;
DROP TABLE IF EXISTS outbox_events;
DROP TABLE IF EXISTS risk_reservations;
DROP TABLE IF EXISTS execution_events;
DROP TABLE IF EXISTS order_ownership;
DROP TABLE IF EXISTS execution_legs;
DROP TABLE IF EXISTS execution_groups;
DROP TABLE IF EXISTS instrument_mappings;
DROP TABLE IF EXISTS credential_envelopes;
DROP TABLE IF EXISTS venue_accounts;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS tenants;
DROP FUNCTION IF EXISTS reject_immutable_mutation();

COMMIT;
