-- Reserve each wallet's Permit2 nonce across quotes, including uncertain attempts.
-- Historical grant attempts are unchanged; merchant mode has no prior rows.
CREATE UNIQUE INDEX merchant_permit2_nonce ON payment_attempts
  ((correlation->>'network'), (correlation->>'from'), (correlation->>'nonce'))
  WHERE correlation->>'payment_mode' = 'merchant';
