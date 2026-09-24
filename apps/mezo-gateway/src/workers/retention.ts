import type { Artifact } from '../domain/model.js';
import { Gateway } from '../application/gateway.js';
export async function retainAndRecover(gateway:Gateway):Promise<void> {
  // Serialize cleanup with quote payment transitions. Unknown, manual, pending,
  // and paid artifacts are never selected. Dedup/ledger rows are never deleted.
  await gateway.ledger.transaction(async db=>{
    const rows=(await db.query<{id:string;report_id:string;artifact:Artifact}>(`SELECT q.id,q.report_id,a.metadata AS artifact
      FROM quotes q JOIN artifacts a USING(report_id) WHERE q.state='EXPIRED'
      AND q.expires_at<now()-interval '15 minutes' AND a.storage_state='AVAILABLE'
      AND NOT EXISTS(SELECT 1 FROM payment_attempts p WHERE p.quote_id=q.id AND p.state<>'REJECTED')
      AND NOT EXISTS(SELECT 1 FROM entitlements e WHERE e.quote_id=q.id)
      ORDER BY q.expires_at LIMIT 10 FOR UPDATE OF q,a SKIP LOCKED`)).rows;
    for(const row of rows) {
      if(!gateway.reports.cleanupReady())break;
      if(!await gateway.reports.cleanup(row.report_id,AbortSignal.timeout(2000)))continue;
      await db.query("UPDATE artifacts SET storage_state='DELETED' WHERE report_id=$1",[row.report_id]);
      await db.query("INSERT INTO audit_events(quote_id,event) VALUES($1,'UNPAID_ARTIFACT_REMOVED')",[row.id]);
    }
    await db.query("DELETE FROM rate_buckets WHERE window_start<now()-interval '1 day'");
  });
  const recovering=(await gateway.ledger.pool.query<{metadata:Artifact}>("SELECT metadata FROM artifacts WHERE storage_state='RECOVERY' LIMIT 4")).rows;
  for(const row of recovering) {
    if(await gateway.reports.recover(row.metadata,AbortSignal.timeout(15000))) {
      await Promise.all([gateway.artifacts.read(row.metadata,'report'),gateway.artifacts.read(row.metadata,'bundle')]);
      await gateway.ledger.pool.query("UPDATE artifacts SET storage_state='AVAILABLE' WHERE report_id=$1",[row.metadata.report_id]);
    }
  }
  await gateway.ledger.pool.query(`UPDATE quotes SET state='EXPIRED' WHERE state='READY' AND expires_at<=now()`);
}
