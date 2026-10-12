-- One payment network per ledger. Existing historical identities remain unchanged.
CREATE TABLE ledger_network (
  singleton boolean PRIMARY KEY DEFAULT true CHECK (singleton),
  chain_id integer NOT NULL UNIQUE CHECK (chain_id IN (31611,31612))
);
INSERT INTO ledger_network(chain_id)
SELECT DISTINCT chain_id FROM quotes
UNION SELECT DISTINCT chain_id FROM chain_events;
CREATE TRIGGER immutable_ledger_network BEFORE UPDATE OR DELETE ON ledger_network
FOR EACH ROW EXECUTE FUNCTION forbid_audit_mutation();

ALTER TABLE quotes DROP CONSTRAINT quotes_network_check;
ALTER TABLE quotes DROP CONSTRAINT quotes_chain_id_check;
ALTER TABLE quotes DROP CONSTRAINT quotes_asset_check;
ALTER TABLE quotes ADD CONSTRAINT quotes_network_identity_check CHECK (
  (chain_id=31611 AND network='eip155:31611' AND asset='0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503') OR
  (chain_id=31612 AND network='eip155:31612' AND asset='0xdD468A1DDc392dcdbEf6db6e34E89AA338F9F186')
);
ALTER TABLE quotes ADD CONSTRAINT quotes_ledger_network_fk FOREIGN KEY(chain_id) REFERENCES ledger_network(chain_id);
ALTER TABLE chain_events DROP CONSTRAINT chain_events_chain_id_check;
ALTER TABLE chain_events DROP CONSTRAINT chain_events_asset_check;
ALTER TABLE chain_events ADD CONSTRAINT chain_events_network_identity_check CHECK (
  (chain_id=31611 AND asset='0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503') OR
  (chain_id=31612 AND asset='0xdD468A1DDc392dcdbEf6db6e34E89AA338F9F186')
);
ALTER TABLE chain_events ADD CONSTRAINT events_ledger_network_fk FOREIGN KEY(chain_id) REFERENCES ledger_network(chain_id);
