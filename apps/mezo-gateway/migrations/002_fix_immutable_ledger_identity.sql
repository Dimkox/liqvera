-- Forward-only repair: table-specific guards must precede field access because
-- PostgreSQL does not guarantee short-circuit evaluation for trigger records.
CREATE OR REPLACE FUNCTION immutable_ledger_identity() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_TABLE_NAME='quotes' THEN
    IF (to_jsonb(NEW)-ARRAY['state','version']) IS DISTINCT FROM (to_jsonb(OLD)-ARRAY['state','version'])
      THEN RAISE EXCEPTION 'immutable quote terms'; END IF;
  ELSIF TG_TABLE_NAME='artifacts' THEN
    IF (to_jsonb(NEW)-'storage_state') IS DISTINCT FROM (to_jsonb(OLD)-'storage_state')
      THEN RAISE EXCEPTION 'immutable artifact identity'; END IF;
  ELSIF TG_TABLE_NAME='report_requests' THEN
    IF (to_jsonb(NEW)-ARRAY['state','reason','quote_id','lease_until','version']) IS DISTINCT FROM
      (to_jsonb(OLD)-ARRAY['state','reason','quote_id','lease_until','version'])
      THEN RAISE EXCEPTION 'immutable request identity'; END IF;
  ELSIF TG_TABLE_NAME='payment_attempts' THEN
    IF (to_jsonb(NEW)-ARRAY['state','tx_hash','updated_at','submitted_at','reconciliation_count','next_reconcile_at','version']) IS DISTINCT FROM
      (to_jsonb(OLD)-ARRAY['state','tx_hash','updated_at','submitted_at','reconciliation_count','next_reconcile_at','version'])
      THEN RAISE EXCEPTION 'immutable authorization identity'; END IF;
    IF OLD.tx_hash IS NOT NULL AND NEW.tx_hash IS DISTINCT FROM OLD.tx_hash
      THEN RAISE EXCEPTION 'immutable transaction association'; END IF;
  END IF;
  RETURN NEW;
END $$;
