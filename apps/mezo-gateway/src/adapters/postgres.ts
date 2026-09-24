import { randomUUID } from 'node:crypto';
import { Pool, type PoolClient, type QueryResultRow } from 'pg';
import { AMOUNT, ASSET, CHAIN_ID, NETWORK, PublicError, type Artifact, type Attempt, type AuthorizationIdentity,
  type Confirmation, type Preview, type Quote, type QuoteInput, type Reason, type ReportRequest } from '../domain/model.js';
import { digest } from '../security/input.js';

const QUOTE_SELECT = `SELECT q.*,a.report_sha256,a.bundle_sha256,a.metadata AS artifact FROM quotes q JOIN artifacts a USING(report_id)`;
function toQuote(row: QueryResultRow): Quote {
  return { id: row.id, report_request_id: row.report_request_id, scope_hash: row.scope_hash, report_id: row.report_id,
    report_sha256: row.report_sha256, bundle_sha256: row.bundle_sha256, state: row.state, expires_at: row.expires_at,
    preview: row.preview, artifact: row.artifact,
    terms: { version: 'mee-evidence-terms/v1', network: NETWORK, chain_id: CHAIN_ID, asset: ASSET,
      amount_atomic: AMOUNT, decimals: 18, price_musd: '0.01', pay_to: row.pay_to,
      expected_payer: row.expected_payer, expires_at: row.expires_at.toISOString() } };
}
export class Ledger {
  constructor(readonly pool: Pool) {}
  async transaction<T>(run: (db: PoolClient) => Promise<T>): Promise<T> {
    const db = await this.pool.connect();
    try { await db.query('BEGIN'); await db.query("SET LOCAL statement_timeout='5s'");
      const result = await run(db); await db.query('COMMIT'); return result;
    } catch (error) { await db.query('ROLLBACK'); throw error; } finally { db.release(); }
  }
  async healthy(): Promise<boolean> {
    try { await this.pool.query('SELECT scope_hash FROM access_scopes LIMIT 0'); return true; } catch { return false; }
  }
  async createRequest(scope: string, key: string, body: QuoteInput): Promise<ReportRequest> {
    return this.transaction(async db => {
      const bodyHash = digest(JSON.stringify(body));
      await db.query('INSERT INTO access_scopes(scope_hash) VALUES($1) ON CONFLICT DO NOTHING', [scope]);
      const inserted=await db.query(`INSERT INTO report_requests(id,scope_hash,idempotency_key,body_hash,canonical_body,report_id)
        VALUES($1,$2,$3,$4,$5,$6) ON CONFLICT(scope_hash,idempotency_key) DO NOTHING RETURNING id`,
      [randomUUID(),scope,key,bodyHash,body,randomUUID()]);
      if(inserted.rowCount) {
        const budget=(await db.query<{hits:number}>(`INSERT INTO rate_buckets(bucket_hash,window_start,hits) VALUES($1,date_trunc('minute',now()),1)
          ON CONFLICT(bucket_hash) DO UPDATE SET window_start=EXCLUDED.window_start,
          hits=CASE WHEN rate_buckets.window_start=EXCLUDED.window_start THEN rate_buckets.hits+1 ELSE 1 END RETURNING hits`,[digest(`quote-scope:${scope}`)])).rows[0]!;
        if(budget.hits>5)throw new PublicError('RATE_LIMITED',429);
      }
      const row = (await db.query<ReportRequest>('SELECT * FROM report_requests WHERE scope_hash=$1 AND idempotency_key=$2 FOR UPDATE', [scope,key])).rows[0]!;
      if (row.body_hash !== bodyHash) throw new PublicError('IDEMPOTENCY_CONFLICT', 409);
      return row;
    });
  }
  async request(scope: string, id: string): Promise<ReportRequest> {
    const row = (await this.pool.query<ReportRequest>('SELECT * FROM report_requests WHERE id=$1 AND scope_hash=$2',[id,scope])).rows[0];
    if (!row) throw new PublicError('NOT_FOUND',404); return row;
  }
  async quote(scope: string, id: string, byReport = false): Promise<Quote> {
    const row = (await this.pool.query(`${QUOTE_SELECT} WHERE q.${byReport ? 'report_id' : 'id'}=$1 AND q.scope_hash=$2`,[id,scope])).rows[0];
    if (!row) throw new PublicError('NOT_FOUND',404); return toQuote(row);
  }
  async quoteForAttempt(attempt: Attempt): Promise<Quote> {
    const row = (await this.pool.query(`${QUOTE_SELECT} WHERE q.id=$1`,[attempt.quote_id])).rows[0];
    if (!row) throw new PublicError('NOT_FOUND',404); return toQuote(row);
  }
  async claimBuild(): Promise<ReportRequest | null> {
    return this.transaction(async db => {
      // Global transaction advisory lock serializes slot claims across replicas.
      await db.query('SELECT pg_advisory_xact_lock(31611,4)');
      await db.query(`UPDATE report_requests SET state='BUILD_FAILED',reason='SOURCE_UNAVAILABLE',lease_until=NULL
        WHERE state='PREPARING' AND lease_until < now()`);
      const active = (await db.query<{ count: string }>("SELECT count(*) FROM report_requests WHERE state='PREPARING' AND lease_until>now()")).rows[0]!;
      if (BigInt(active.count) >= 4n) return null;
      return (await db.query<ReportRequest>(`UPDATE report_requests SET lease_until=now()+interval '20 seconds'
        WHERE id=(SELECT id FROM report_requests WHERE state='PREPARING' AND lease_until IS NULL
        ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1) RETURNING *`)).rows[0] ?? null;
    });
  }
  async rejectBuild(id: string, reason: Reason, rejected: boolean): Promise<void> {
    await this.pool.query(`UPDATE report_requests SET state=$2,reason=$3,lease_until=NULL
      WHERE id=$1 AND state='PREPARING'`,[id,rejected ? 'REJECTED':'BUILD_FAILED',reason]);
  }
  async publish(request: ReportRequest, artifact: Artifact, payTo: string, expires: Date, preview: Preview): Promise<void> {
    await this.transaction(async db => {
      const current = (await db.query<ReportRequest>('SELECT * FROM report_requests WHERE id=$1 FOR UPDATE',[request.id])).rows[0];
      if (current?.state !== 'PREPARING') throw new PublicError('INVALID_STATE',409);
      const quoteId = randomUUID();
      await db.query(`INSERT INTO artifacts(report_id,scope_hash,report_sha256,bundle_sha256,report_size_bytes,bundle_size_bytes,metadata)
        VALUES($1,$2,$3,$4,$5,$6,$7)`,[artifact.report_id,request.scope_hash,artifact.report_sha256,artifact.bundle_sha256,artifact.report_size_bytes,artifact.bundle_size_bytes,artifact]);
      await db.query(`INSERT INTO quotes(id,report_request_id,scope_hash,report_id,network,chain_id,asset,amount_atomic,pay_to,expected_payer,expires_at,preview)
        VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)`,
      [quoteId,request.id,request.scope_hash,artifact.report_id,NETWORK,CHAIN_ID,ASSET,AMOUNT,payTo,request.canonical_body.expected_payer,expires,preview]);
      await db.query("UPDATE report_requests SET state='READY',quote_id=$2,lease_until=NULL WHERE id=$1",[request.id,quoteId]);
      await db.query("INSERT INTO audit_events(quote_id,event) VALUES($1,'ARTIFACT_PUBLISHED')",[quoteId]);
    });
  }
  async expire(quote: Quote): Promise<void> {
    await this.pool.query("UPDATE quotes SET state='EXPIRED' WHERE id=$1 AND state='READY' AND expires_at<=now()",[quote.id]);
  }
  async beginAttempt(quote: Quote, identity: AuthorizationIdentity): Promise<Attempt> {
    return this.transaction(async db => {
      const row = (await db.query('SELECT state,expires_at FROM quotes WHERE id=$1 FOR UPDATE',[quote.id])).rows[0]!;
      if (row.state !== 'READY') throw new PublicError('PAYMENT_UNCERTAIN',202);
      if (row.expires_at <= new Date()) throw new PublicError('QUOTE_EXPIRED',410);
      const attemptId = randomUUID();
      const inserted = await db.query<Attempt>(`INSERT INTO payment_attempts(id,quote_id,authorization_identity,identity_version,authorization_valid_until,correlation,state)
        VALUES($1,$2,$3,$4,$5,$6,'RECEIVED') ON CONFLICT(authorization_identity) DO NOTHING RETURNING *`,
      [attemptId,quote.id,identity.identity,identity.version,identity.valid_until,identity.correlation]);
      if (!inserted.rows[0]) throw new PublicError('AUTHORIZATION_REUSED',409);
      await db.query("UPDATE payment_attempts SET state='VERIFIED',updated_at=now() WHERE id=$1",[attemptId]);
      await db.query("UPDATE quotes SET state='PAYMENT_PENDING' WHERE id=$1",[quote.id]);
      await db.query("INSERT INTO audit_events(quote_id,payment_attempt_id,event) VALUES($1,$2,'AUTHORIZATION_VERIFIED')",[quote.id,attemptId]);
      return { ...inserted.rows[0], state:'VERIFIED' };
    });
  }
  async markSubmitting(attempt: Attempt): Promise<boolean> {
    return this.transaction(async db => {
      const q = (await db.query('SELECT * FROM quotes WHERE id=$1 FOR UPDATE',[attempt.quote_id])).rows[0]!;
      const current = (await db.query<Attempt>('SELECT * FROM payment_attempts WHERE id=$1 FOR UPDATE',[attempt.id])).rows[0]!;
      if (current.state !== 'VERIFIED') return false;
      if (q.expires_at <= new Date()) {
        await db.query("UPDATE payment_attempts SET state='REJECTED',updated_at=now() WHERE id=$1",[attempt.id]);
        await db.query("UPDATE quotes SET state='EXPIRED' WHERE id=$1",[attempt.quote_id]); return false;
      }
      await db.query("UPDATE payment_attempts SET state='SUBMITTING',submitted_at=now(),updated_at=now(),next_reconcile_at=now()+interval '30 seconds' WHERE id=$1",[attempt.id]);
      await db.query("INSERT INTO audit_events(quote_id,payment_attempt_id,event) VALUES($1,$2,'SUBMIT_COMMITTED')",[attempt.quote_id,attempt.id]);
      return true;
    });
  }
  async unknown(attempt: Attempt, txHash: string | null): Promise<void> {
    await this.transaction(async db => {
      await db.query('SELECT id FROM quotes WHERE id=$1 FOR UPDATE',[attempt.quote_id]);
      await db.query(`UPDATE payment_attempts SET state='UNKNOWN',tx_hash=COALESCE(tx_hash,$2),updated_at=now()
        WHERE id=$1 AND state IN ('SUBMITTING','UNKNOWN')`,[attempt.id,txHash]);
      await db.query("UPDATE quotes SET state='PAYMENT_UNCERTAIN' WHERE id=$1 AND state='PAYMENT_PENDING'",[attempt.quote_id]);
      await db.query("INSERT INTO audit_events(quote_id,payment_attempt_id,event) VALUES($1,$2,'PAYMENT_UNCERTAIN')",[attempt.quote_id,attempt.id]);
    });
  }
  async confirmation(quote: Quote): Promise<{ attempt: Attempt; confirmation: Confirmation; retain_until: Date } | null> {
    const row = (await this.pool.query(`SELECT a.*,row_to_json(a) AS attempt,r.*,e.retain_until,c.* FROM entitlements e
      JOIN receipts r USING(payment_attempt_id) JOIN payment_attempts a ON a.id=e.payment_attempt_id
      JOIN chain_events c ON c.payment_attempt_id=a.id
      WHERE e.quote_id=$1 AND e.scope_hash=$2 AND e.report_id=$3 AND e.report_sha256=$4`,
    [quote.id,quote.scope_hash,quote.report_id,quote.report_sha256])).rows[0];
    if (!row) return null;
    const attempt: Attempt = { ...row.attempt, authorization_valid_until: new Date(row.attempt.authorization_valid_until), submitted_at: row.attempt.submitted_at ? new Date(row.attempt.submitted_at):null };
    return { attempt, retain_until:row.retain_until, confirmation: { response_header:row.response_header, receipt: {
      schema:'mee-evidence-receipt/v1',quote_id:quote.id,report_id:quote.report_id,payment_attempt_id:attempt.id,report_sha256:quote.report_sha256,
      network:NETWORK,chain_id:CHAIN_ID,asset:ASSET,amount_atomic:AMOUNT,payer:row.payer,pay_to:row.pay_to,
      tx_hash:row.tx_hash,block_hash:row.block_hash,block_number:Number(row.block_number),log_index:row.log_index,
      confirmed_at:row.confirmed_at.toISOString(),finality_policy_version:row.finality_policy_version } } };
  }
  async confirm(quote: Quote, attempt: Attempt, confirmation: Confirmation): Promise<void> {
    const r = confirmation.receipt;
    await this.transaction(async db => {
      await db.query('SELECT id FROM quotes WHERE id=$1 FOR UPDATE',[quote.id]);
      const current = (await db.query<Attempt>('SELECT * FROM payment_attempts WHERE id=$1 FOR UPDATE',[attempt.id])).rows[0]!;
      if (current.state === 'CONFIRMED') return;
      if (!['SUBMITTING','UNKNOWN','MANUAL_REVIEW'].includes(current.state)) throw new PublicError('INVALID_STATE',409);
      if (r.quote_id !== quote.id || r.report_id !== quote.report_id || r.report_sha256 !== quote.report_sha256 || r.payment_attempt_id !== attempt.id ||
        r.chain_id !== CHAIN_ID || r.network !== NETWORK || r.asset !== ASSET || r.amount_atomic !== AMOUNT ||
        r.payer !== quote.terms.expected_payer || r.pay_to !== quote.terms.pay_to) throw new PublicError('PAYMENT_REJECTED',422);
      await db.query(`INSERT INTO chain_events(chain_id,tx_hash,log_index,block_hash,block_number,payment_attempt_id,asset,amount_atomic,payer,pay_to)
        VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)`,[CHAIN_ID,r.tx_hash,r.log_index,r.block_hash,r.block_number,attempt.id,ASSET,AMOUNT,r.payer,r.pay_to]);
      await db.query(`INSERT INTO receipts(payment_attempt_id,quote_id,report_id,report_sha256,chain_id,tx_hash,log_index,confirmed_at,finality_policy_version,response_header)
        VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)`,[attempt.id,quote.id,quote.report_id,quote.report_sha256,CHAIN_ID,r.tx_hash,r.log_index,r.confirmed_at,r.finality_policy_version,confirmation.response_header]);
      await db.query(`INSERT INTO entitlements(quote_id,report_id,scope_hash,report_sha256,payment_attempt_id,retain_until)
        VALUES($1,$2,$3,$4,$5,$6::timestamptz+interval '7 days')`,[quote.id,quote.report_id,quote.scope_hash,quote.report_sha256,attempt.id,r.confirmed_at]);
      await db.query("UPDATE payment_attempts SET state='CONFIRMED',tx_hash=$2,updated_at=now() WHERE id=$1",[attempt.id,r.tx_hash]);
      await db.query("UPDATE quotes SET state='PAID' WHERE id=$1",[quote.id]);
      await db.query("INSERT INTO audit_events(quote_id,payment_attempt_id,event) VALUES($1,$2,'ENTITLEMENT_COMMITTED')",[quote.id,attempt.id]);
    });
  }
  async manualReview(quote: Quote, attempt: Attempt): Promise<void> {
    await this.transaction(async db => {
      await db.query('SELECT id FROM quotes WHERE id=$1 FOR UPDATE',[quote.id]);
      await db.query("UPDATE payment_attempts SET state='UNKNOWN' WHERE id=$1 AND state='SUBMITTING'",[attempt.id]);
      await db.query("UPDATE payment_attempts SET state='MANUAL_REVIEW',updated_at=now() WHERE id=$1 AND state IN ('UNKNOWN','CONFIRMED')",[attempt.id]);
      await db.query("UPDATE quotes SET state='MANUAL_REVIEW' WHERE id=$1 AND state IN ('PAYMENT_PENDING','PAYMENT_UNCERTAIN','PAID')",[quote.id]);
      await db.query("INSERT INTO audit_events(quote_id,payment_attempt_id,event) VALUES($1,$2,'MANUAL_REVIEW')",[quote.id,attempt.id]);
    });
  }
  async recordDelivery(quote: Quote, kind: 'report'|'bundle', requestId: string): Promise<void> {
    await this.transaction(async db=>{
      const current=(await db.query('SELECT state FROM quotes WHERE id=$1 AND scope_hash=$2 FOR UPDATE',[quote.id,quote.scope_hash])).rows[0];
      if(current?.state!=='PAID')throw new PublicError('PAYMENT_UNCERTAIN',202);
      const bound=(await db.query(`SELECT a.state FROM entitlements e JOIN payment_attempts a ON a.id=e.payment_attempt_id
        WHERE e.quote_id=$1 AND e.report_id=$2 AND e.report_sha256=$3 AND e.scope_hash=$4 AND e.retain_until>now()
        FOR UPDATE OF a`,[quote.id,quote.report_id,quote.report_sha256,quote.scope_hash])).rows[0];
      if(bound?.state!=='CONFIRMED')throw new PublicError('PAYMENT_UNCERTAIN',202);
      await db.query('INSERT INTO delivery_attempts(quote_id,kind,request_id) VALUES($1,$2,$3)',[quote.id,kind,requestId]);
    });
  }
  async rateLimit(bucket: string, limit: number): Promise<void> {
    const row = (await this.pool.query<{ hits: number }>(`INSERT INTO rate_buckets(bucket_hash,window_start,hits) VALUES($1,date_trunc('minute',now()),1)
      ON CONFLICT(bucket_hash) DO UPDATE SET window_start=EXCLUDED.window_start,
      hits=CASE WHEN rate_buckets.window_start=EXCLUDED.window_start THEN rate_buckets.hits+1 ELSE 1 END RETURNING hits`,[digest(bucket)])).rows[0]!;
    if (row.hits > limit) throw new PublicError('RATE_LIMITED',429);
  }
}
