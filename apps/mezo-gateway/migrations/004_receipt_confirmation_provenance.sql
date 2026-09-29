-- Persist the read-only observations used to authorize a confirmed entitlement.
-- These columns are append-only because the existing receipts trigger rejects
-- every UPDATE and DELETE.
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM receipts) THEN
    RAISE EXCEPTION '004 requires zero legacy receipts; preserve evidence and stop';
  END IF;
END $$;

ALTER TABLE receipts
  ADD COLUMN transaction_from text NOT NULL CHECK (transaction_from ~ '^0x[0-9a-f]{40}$'),
  ADD COLUMN buyer_native_balance_before numeric(78,0) NOT NULL CHECK (buyer_native_balance_before >= 0),
  ADD COLUMN buyer_native_balance_after numeric(78,0) NOT NULL CHECK (buyer_native_balance_after >= 0),
  ADD COLUMN buyer_native_gas_spent numeric(78,0) NOT NULL CHECK (buyer_native_gas_spent = 0),
  ADD COLUMN observation_before_block_number bigint NOT NULL CHECK (observation_before_block_number >= 0),
  ADD COLUMN observation_before_block_hash text NOT NULL CHECK (observation_before_block_hash ~ '^0x[0-9a-f]{64}$'),
  ADD COLUMN observation_after_block_number bigint NOT NULL CHECK (observation_after_block_number >= 0),
  ADD COLUMN observation_after_block_hash text NOT NULL CHECK (observation_after_block_hash ~ '^0x[0-9a-f]{64}$'),
  ADD COLUMN authorization_identity text NOT NULL CHECK (length(authorization_identity) BETWEEN 1 AND 512),
  ADD COLUMN transfer_identity char(64) NOT NULL CHECK (transfer_identity ~ '^[0-9a-f]{64}$'),
  ADD CONSTRAINT receipt_zero_buyer_native_gas CHECK (buyer_native_balance_before = buyer_native_balance_after),
  ADD CONSTRAINT receipt_observation_precedes_confirmation CHECK (observation_before_block_number <= observation_after_block_number);
