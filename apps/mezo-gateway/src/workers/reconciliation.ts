import { type Attempt, PublicError } from '../domain/model.js';
import { Gateway } from '../application/gateway.js';
import { metrics } from '../security/observability.js';
export async function reconcileOne(gateway:Gateway):Promise<boolean> {
  // Lease the bounded read-only reconciliation operation, never settlement.
  const attempt=await gateway.ledger.transaction(async db => (await db.query<Attempt>(`UPDATE payment_attempts
    SET next_reconcile_at=now()+interval '60 seconds',reconciliation_count=reconciliation_count+1
    WHERE id=(SELECT id FROM payment_attempts WHERE state IN ('SUBMITTING','UNKNOWN') AND next_reconcile_at<=now()
      ORDER BY next_reconcile_at FOR UPDATE SKIP LOCKED LIMIT 1) RETURNING *`)).rows[0]);
  if(!attempt)return false;
  const started=performance.now();
  const quote=await gateway.ledger.quoteForAttempt(attempt);
  await gateway.ledger.unknown(attempt,attempt.tx_hash);
  let code='PAYMENT_UNCERTAIN';
  try {
    const confirmation=await gateway.payment.confirm(quote,{...attempt,state:'UNKNOWN'});
    if(confirmation) {gateway.contracts.assert('receipt',confirmation.receipt);await gateway.ledger.confirm(quote,attempt,confirmation);code='CONFIRMED';}
    else if(attempt.reconciliation_count>=10) {await gateway.ledger.manualReview(quote,attempt);code='MANUAL_REVIEW';}
  } catch(error) {
    if(attempt.reconciliation_count>=10||(error instanceof PublicError&&error.code==='MANUAL_REVIEW')) {await gateway.ledger.manualReview(quote,attempt);code='MANUAL_REVIEW';}
  }
  await gateway.ledger.pool.query('INSERT INTO reconciliation_events(payment_attempt_id,code) VALUES($1,$2)',[attempt.id,code]);
  metrics.increment('reconciliation_complete');
  metrics.observe('reconciliation',(performance.now()-started)/1000);
  await gateway.ledger.pool.query(`UPDATE payment_attempts SET next_reconcile_at=now()+($2::integer*interval '1 second')
    WHERE id=$1 AND state='UNKNOWN'`,[attempt.id,Math.min(3600,30*2**Math.min(attempt.reconciliation_count,7))]);
  return true;
}
export async function recoverUnsubmitted(gateway:Gateway):Promise<void> {
  // A stale VERIFIED attempt has never crossed the durable submit boundary.
  // Take quote locks first, matching all payment transactions' lock ordering.
  await gateway.ledger.transaction(async db => {
    const rows=(await db.query<{id:string;quote_id:string}>(`SELECT a.id,a.quote_id FROM payment_attempts a JOIN quotes q ON q.id=a.quote_id
      WHERE a.state IN ('RECEIVED','VERIFIED') AND a.updated_at<now()-interval '60 seconds'
      ORDER BY a.created_at LIMIT 20 FOR UPDATE OF q SKIP LOCKED`)).rows;
    for(const row of rows) {
      const changed=await db.query(`UPDATE payment_attempts SET state='REJECTED',updated_at=now()
        WHERE id=$1 AND state IN ('RECEIVED','VERIFIED') RETURNING id`,[row.id]);
      if(changed.rowCount)await db.query(`UPDATE quotes SET state=CASE WHEN expires_at<=now() THEN 'EXPIRED' ELSE 'READY' END
        WHERE id=$1 AND state='PAYMENT_PENDING'`,[row.quote_id]);
    }
  });
}
