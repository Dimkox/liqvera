DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM receipts) THEN
    RAISE EXCEPTION 'migration 005 requires zero receipts; confirmation count cannot be fabricated';
  END IF;
END $$;

ALTER TABLE receipts
  ADD COLUMN confirmations integer NOT NULL,
  ADD CONSTRAINT receipts_confirmations_final CHECK (confirmations >= 12);
