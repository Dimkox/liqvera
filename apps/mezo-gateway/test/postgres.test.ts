import assert from 'node:assert/strict';
import { execFile, spawn } from 'node:child_process';
import { randomUUID } from 'node:crypto';
import { once } from 'node:events';
import { readFile, mkdtemp, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createServer } from 'node:http';
import { fileURLToPath } from 'node:url';
import { promisify } from 'node:util';
import test, { after, before } from 'node:test';
import { Pool } from 'pg';
import { HttpReportService } from '../src/adapters/report-service.js';
import { Ledger } from '../src/adapters/postgres.js';
import { PublicError, type MarketQuoteInput } from '../src/domain/model.js';
import type { Gateway } from '../src/application/gateway.js';
import { retainAndRecover } from '../src/workers/retention.js';
import type {LiveGrantAuthority} from '../src/security/live-grant.js';

const execFileAsync = promisify(execFile);
const databaseUrl = process.env.TEST_DATABASE_URL;
const marker = process.env.TEST_DATABASE_DISPOSABLE === '1';
const skipReason = databaseUrl && marker ? undefined : 'requires an explicitly disposable local PostgreSQL URL';
const MIGRATION_001_SHA256 = 'bc127e55c876961112f33ca2abdfac01827769d6156ddba2f42856d070c75b3b';
const MIGRATION_002_SHA256 = '981f48215e64fdd0fb72be5a6df78238cf8050de722adb454b4e28b1940ccbcb';
const MIGRATION_003_SHA256 = 'bbedff6137a648166b77233c56a466e46247480b404b8829b64f29123109bcf0';
const MIGRATION_004_SHA256 = '96bba00d344d81670a4c0f8741186004910e959f374ecd77ce78268d52fd465a';
const MIGRATION_005_SHA256 = 'e99e5cffab60c08dfb1cd73d13caf2915f31aec542c26c87b016d0e125a23b11';
const MIGRATION_006_SHA256 = '92e346b3fa49699b20d9edca9814d17bde4fb96046e71071c68b0c47326ef18a';
const BODY: MarketQuoteInput = {
  instrument_id: 'hyperliquid:BTC:perpetual',
  side: 'BUY',
  quantity_base: '0.25',
  expected_payer: '0x1111111111111111111111111111111111111111',
};

let pool: Pool;

async function runMigrator(url: string): Promise<void> {
  const migrator = fileURLToPath(new URL('../../dist/migrate.js', import.meta.url));
  const env: NodeJS.ProcessEnv = { ...process.env, DATABASE_URL: url };
  delete env.DATABASE_URL_FILE;
  await execFileAsync(process.execPath, [migrator], { env });
}

before(async () => {
  if (skipReason) return;
  const target = new URL(databaseUrl!);
  assert.match(target.hostname, /^(127\.0\.0\.1|localhost)$/);
  assert.match(target.pathname, /^\/liqvera_f4_test_[a-z0-9_]+$/);
  await runMigrator(databaseUrl!);
  await runMigrator(databaseUrl!);
  pool = new Pool({ connectionString: databaseUrl, max: 30 });
  await new Ledger(pool).assertNetwork();
});

after(async () => {
  if (pool) await pool.end();
});

async function verifiedAttempt(ledger: Ledger, suffix: string,version:'v1'|'v2'='v1',payer=BODY.expected_payer,grantDigest=suffix.padStart(64,'b'),grantId=randomUUID(),merchantNonce?:string,authorizationExpires=new Date(Date.now()+600_000)) {
  const scope = suffix.padStart(64, '0');
  const request = await ledger.createRequest(scope, `grant-${suffix}`, BODY);
  await ledger.publish(request, {
    report_id: request.report_id, report_sha256: suffix.padStart(64, '1'), bundle_sha256: suffix.padStart(64, '2'),
    report_size_bytes: 1, bundle_size_bytes: 1, snapshot_at: '2026-09-29T00:00:00Z',
    snapshot_status: 'VALID_FOR_SNAPSHOT_CALCULATION', source_mode: 'live-public', limitations: [],
  }, '0x2222222222222222222222222222222222222222', new Date(Date.now()+600_000), {
    instrument_id: BODY.instrument_id, side: BODY.side, quantity_base: BODY.quantity_base,
    snapshot_at: '2026-09-29T00:00:00Z', snapshot_status: 'VALID_FOR_SNAPSHOT_CALCULATION',
    limitations: [], price_musd: '0.01', expires_at: new Date(Date.now()+600_000).toISOString(),
  });
  const quote = await ledger.quote(scope, request.report_id, true);
  const attempt = await ledger.beginAttempt(quote, {
    identity: suffix.padStart(64, 'a'), version: merchantNonce===undefined?'test/v1':'liqvera-permit2-eip2612-identity/v1', payer: BODY.expected_payer,
    valid_until: authorizationExpires.toISOString(),
    correlation: merchantNonce===undefined?{ live_grant_digest:grantDigest,live_grant_id:grantId,live_grant_version:version,from:payer }:{payment_mode:'merchant',network:'eip155:31611',asset:'0x118917a40faf1cd7a13db0ef56c86de7973ac503',amount:'10000000000000000',from:payer,to:'0x2222222222222222222222222222222222222222',nonce:merchantNonce},
  });
  return { quote, attempt };
}

test('fresh migration applies 001 through 008 once, reruns by checksum, and keeps audit rows append-only', { skip: skipReason }, async () => {
  const migrations = await pool.query<{ name: string; sha256: string }>(
    'SELECT name,sha256 FROM gateway_migrations ORDER BY name',
  );
  assert.deepEqual(migrations.rows, [
    { name: '001_ledger.sql', sha256: MIGRATION_001_SHA256 },
    { name: '002_fix_immutable_ledger_identity.sql', sha256: MIGRATION_002_SHA256 },
    { name: '003_live_grant_consumption.sql', sha256: MIGRATION_003_SHA256 },
    { name: '004_receipt_confirmation_provenance.sql', sha256: MIGRATION_004_SHA256 },
    { name: '005_receipt_confirmation_count.sql', sha256: MIGRATION_005_SHA256 },
    { name: '006_signed_live_grant_authority.sql', sha256: MIGRATION_006_SHA256 },
    { name: '007_network_identity.sql', sha256: '377120dd211d6a455f55f264dd188fdf40652be4da512c8d91652c1562f3afa6' },
    { name: '008_merchant_nonce.sql', sha256: '562504aa3b54efc7e8e5b5b3eed3a4918c85ec305da775bd33279899dab2e2fe' },
  ]);

  const audit = await pool.query<{ id: string }>("INSERT INTO audit_events(event) VALUES('TEST_ONLY') RETURNING id");
  await assert.rejects(
    pool.query("UPDATE audit_events SET event='MUTATED' WHERE id=$1", [audit.rows[0]!.id]),
    /append-only record/,
  );
  assert.equal((await pool.query('SELECT count(*)::int AS count FROM audit_events WHERE id=$1', [audit.rows[0]!.id])).rows[0]!.count, 1);
});

test('an existing empty-receipt 001 ledger upgrades through 004 without replacing state', { skip: skipReason }, async () => {
  const source = new URL(databaseUrl!);
  const sourceName = source.pathname.slice(1);
  const upgradeName = `${sourceName}_upgrade`;
  assert.match(upgradeName, /^liqvera_f4_test_[a-z0-9_]+_upgrade$/);
  const adminUrl = new URL(source);
  adminUrl.pathname = '/postgres';
  const admin = new Pool({ connectionString: adminUrl.toString(), max: 1 });
  await admin.query(`CREATE DATABASE "${upgradeName}"`);
  await admin.end();

  const upgradeUrl = new URL(source);
  upgradeUrl.pathname = `/${upgradeName}`;
  const upgrade = new Pool({ connectionString: upgradeUrl.toString(), max: 2 });
  try {
    const migration001 = await readFile(new URL('../../migrations/001_ledger.sql', import.meta.url), 'utf8');
    await upgrade.query(migration001);
    await upgrade.query('CREATE TABLE gateway_migrations(name text PRIMARY KEY,sha256 text NOT NULL,applied_at timestamptz NOT NULL DEFAULT now())');
    await upgrade.query('INSERT INTO gateway_migrations(name,sha256) VALUES($1,$2)', ['001_ledger.sql', MIGRATION_001_SHA256]);
    const scope = '9'.repeat(64);
    const requestId = randomUUID();
    const reportId = randomUUID();
    await upgrade.query('INSERT INTO access_scopes(scope_hash) VALUES($1)', [scope]);
    await upgrade.query(`INSERT INTO report_requests(id,scope_hash,idempotency_key,body_hash,canonical_body,report_id)
      VALUES($1,$2,'upgrade-key',$3,$4,$5)`, [requestId, scope, '8'.repeat(64), BODY, reportId]);
    await upgrade.query(`INSERT INTO artifacts(report_id,scope_hash,report_sha256,bundle_sha256,report_size_bytes,bundle_size_bytes,metadata)
      VALUES($1,$2,$3,$4,1,1,'{}')`, [reportId, scope, '7'.repeat(64), '6'.repeat(64)]);
    await assert.rejects(
      upgrade.query("UPDATE artifacts SET storage_state='DELETED' WHERE report_id=$1", [reportId]),
      /record "old" has no field "tx_hash"/,
    );

    await runMigrator(upgradeUrl.toString());
    await runMigrator(upgradeUrl.toString());
    assert.equal((await upgrade.query('SELECT storage_state FROM artifacts WHERE report_id=$1', [reportId])).rows[0]!.storage_state, 'AVAILABLE');
    await upgrade.query("UPDATE artifacts SET storage_state='DELETED' WHERE report_id=$1", [reportId]);
    assert.equal((await upgrade.query('SELECT storage_state FROM artifacts WHERE report_id=$1', [reportId])).rows[0]!.storage_state, 'DELETED');
    assert.deepEqual((await upgrade.query('SELECT name,sha256 FROM gateway_migrations ORDER BY name')).rows, [
      { name: '001_ledger.sql', sha256: MIGRATION_001_SHA256 },
      { name: '002_fix_immutable_ledger_identity.sql', sha256: MIGRATION_002_SHA256 },
      { name: '003_live_grant_consumption.sql', sha256: MIGRATION_003_SHA256 },
      { name: '004_receipt_confirmation_provenance.sql', sha256: MIGRATION_004_SHA256 },
      { name: '005_receipt_confirmation_count.sql', sha256: MIGRATION_005_SHA256 },
      { name: '006_signed_live_grant_authority.sql', sha256: MIGRATION_006_SHA256 },
    { name: '007_network_identity.sql', sha256: '377120dd211d6a455f55f264dd188fdf40652be4da512c8d91652c1562f3afa6' },
    { name: '008_merchant_nonce.sql', sha256: '562504aa3b54efc7e8e5b5b3eed3a4918c85ec305da775bd33279899dab2e2fe' },
    ]);
  } finally {
    await upgrade.end();
  }
});

test('twenty concurrent identical creates converge and preserve scope conflict boundaries', { skip: skipReason }, async () => {
  const ledger = new Ledger(pool);
  const scopeA = 'a'.repeat(64);
  const scopeB = 'b'.repeat(64);
  const key = 'same-request-key';
  const requests = await Promise.all(Array.from({ length: 20 }, () => ledger.createRequest(scopeA, key, BODY)));
  assert.equal(new Set(requests.map(row => row.id)).size, 1);
  assert.equal(new Set(requests.map(row => row.report_id)).size, 1);
  assert.equal(
    (await pool.query('SELECT count(*)::int AS count FROM report_requests WHERE scope_hash=$1 AND idempotency_key=$2', [scopeA, key])).rows[0]!.count,
    1,
  );
  assert.equal(
    (await pool.query('SELECT hits FROM rate_buckets WHERE bucket_hash IS NOT NULL')).rows[0]!.hits,
    1,
  );

  await assert.rejects(
    ledger.createRequest(scopeA, key, { ...BODY, side: 'SELL' }),
    (error: unknown) => error instanceof PublicError && error.code === 'IDEMPOTENCY_CONFLICT',
  );
  const sibling = await ledger.createRequest(scopeB, key, BODY);
  assert.notEqual(sibling.id, requests[0]!.id);
  assert.notEqual(sibling.report_id, requests[0]!.report_id);
});

test('twenty pools consume one grant once; restart loses and rollback preserves VERIFIED', { skip: skipReason }, async () => {
  const setup = new Ledger(pool);
  const first = await verifiedAttempt(setup, '31');
  const pools = Array.from({ length: 20 }, () => new Pool({ connectionString: databaseUrl, max: 1 }));
  try {
    const outcomes = await Promise.all(pools.map(value => new Ledger(value).markSubmitting(first.attempt)));
    assert.equal(outcomes.filter(value=>value==='SUBMITTING').length, 1);
  } finally {
    await Promise.all(pools.map(value => value.end()));
  }
  const restartedPool = new Pool({ connectionString: databaseUrl, max: 1 });
  try { assert.equal(await new Ledger(restartedPool).markSubmitting(first.attempt), 'INVALID_STATE'); }
  finally { await restartedPool.end(); }

  const second = await verifiedAttempt(setup, '32');
  await pool.query(`CREATE FUNCTION test_fail_submitting() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN IF NEW.id='${second.attempt.id}'::uuid AND NEW.state='SUBMITTING' THEN RAISE EXCEPTION 'test rollback'; END IF; RETURN NEW; END $$`);
  await pool.query('CREATE TRIGGER test_fail_submitting BEFORE UPDATE ON payment_attempts FOR EACH ROW EXECUTE FUNCTION test_fail_submitting()');
  await assert.rejects(setup.markSubmitting(second.attempt), /test rollback/);
  await pool.query('DROP TRIGGER test_fail_submitting ON payment_attempts');
  await pool.query('DROP FUNCTION test_fail_submitting()');
  assert.equal((await pool.query('SELECT state FROM payment_attempts WHERE id=$1',[second.attempt.id])).rows[0]!.state,'VERIFIED');
  assert.equal((await pool.query('SELECT count(*)::int AS count FROM live_grant_consumptions WHERE payment_attempt_id=$1',[second.attempt.id])).rows[0]!.count,0);
  const consumption=(await pool.query('SELECT grant_digest FROM live_grant_consumptions WHERE payment_attempt_id=$1',[first.attempt.id])).rows[0]!;
  await assert.rejects(pool.query('UPDATE live_grant_consumptions SET grant_digest=$2 WHERE grant_digest=$1',[consumption.grant_digest,'f'.repeat(64)]),/append-only record/);
  await assert.rejects(pool.query('DELETE FROM live_grant_consumptions WHERE grant_digest=$1',[consumption.grant_digest]),/append-only record/);
});

test('signed v2 authority reserves atomically, exhausts budget, survives restart, and is append-only',{skip:skipReason},async()=>{
  const ledger=new Ledger(pool),digest='d'.repeat(64),grantId=randomUUID(),now=Date.now();
  const authority:LiveGrantAuthority={grantDigest:digest,grantId,schemaVersion:'v2',policySha256:'e'.repeat(64),keyId:'f'.repeat(64),signatureSha256:'1'.repeat(64),issuedAt:new Date(now-1000),notBefore:new Date(now-1000),expiresAt:new Date(now+600_000),payTo:'0x2222222222222222222222222222222222222222',amountPer:'10000000000000000',maxSubmissions:2,maxTotal:'20000000000000000',maxPerPayer:1,payerPolicy:'ANY_VALID_X402_PAYER'};
  await ledger.activateGrant(authority);assert.equal(await ledger.grantAvailable(digest),true);
  const first=await verifiedAttempt(ledger,'41','v2','0x1111111111111111111111111111111111111111',digest,grantId);
  const pools=Array.from({length:20},()=>new Pool({connectionString:databaseUrl,max:1}));
  try{const results=await Promise.all(pools.map(value=>new Ledger(value).markSubmitting(first.attempt)));assert.equal(results.filter(value=>value==='SUBMITTING').length,1);}finally{await Promise.all(pools.map(value=>value.end()));}
  const second=await verifiedAttempt(ledger,'42','v2','0x3333333333333333333333333333333333333333',digest,grantId);const restarted=new Pool({connectionString:databaseUrl,max:1});try{assert.equal(await new Ledger(restarted).markSubmitting(second.attempt),'SUBMITTING');}finally{await restarted.end();}
  assert.equal(await ledger.grantAvailable(digest),false);
  const third=await verifiedAttempt(ledger,'43','v2','0x4444444444444444444444444444444444444444',digest,grantId);assert.equal(await ledger.markSubmitting(third.attempt),'GRANT_CONSUMED');
  assert.equal((await pool.query('SELECT count(*)::int AS count FROM live_grant_reservations WHERE grant_digest=$1',[digest])).rows[0]!.count,2);
  await assert.rejects(pool.query('DELETE FROM live_grant_reservations WHERE grant_digest=$1',[digest]),/append-only record/);
});

test('unimplemented artifact recovery stays fail closed in RECOVERY', { skip: skipReason }, async () => {
  const ledger = new Ledger(pool);
  const request = await ledger.createRequest('5'.repeat(64), 'recovery-key', BODY);
  const artifact = {
    report_id: request.report_id,
    report_sha256: '4'.repeat(64),
    bundle_sha256: '3'.repeat(64),
    report_size_bytes: 10,
    bundle_size_bytes: 20,
    snapshot_at: '2026-09-29T00:00:00Z',
    snapshot_status: 'VALID_FOR_SNAPSHOT_CALCULATION',
    source_mode: 'live-public',
    limitations: ['synthetic local test'],
  };
  await pool.query(`INSERT INTO artifacts(report_id,scope_hash,report_sha256,bundle_sha256,report_size_bytes,bundle_size_bytes,metadata,storage_state)
    VALUES($1,$2,$3,$4,$5,$6,$7,'RECOVERY')`,
  [artifact.report_id, request.scope_hash, artifact.report_sha256, artifact.bundle_sha256, artifact.report_size_bytes, artifact.bundle_size_bytes, artifact]);
  let recoverCalls = 0;
  const gateway = {
    ledger,
    reports: {
      cleanupReady: () => false,
      recover: async () => { recoverCalls += 1; return false; },
    },
    artifacts: { read: async () => { throw new Error('recovery must not claim readable bytes'); } },
  } as unknown as Gateway;

  await retainAndRecover(gateway);

  assert.equal(recoverCalls, 1);
  assert.equal((await pool.query('SELECT storage_state FROM artifacts WHERE report_id=$1', [request.report_id])).rows[0]!.storage_state, 'RECOVERY');
});

test('lost cleanup response retries already-absent result and updates the ledger once', { skip: skipReason }, async () => {
  const scope = 'c'.repeat(64);
  const requestId = randomUUID();
  const reportId = randomUUID();
  const quoteId = randomUUID();
  await pool.query('BEGIN');
  try {
    await pool.query('SET CONSTRAINTS ALL DEFERRED');
    await pool.query('INSERT INTO access_scopes(scope_hash) VALUES($1)', [scope]);
    await pool.query(`INSERT INTO report_requests(id,scope_hash,idempotency_key,body_hash,canonical_body,report_id,state,quote_id,created_at)
      VALUES($1,$2,'cleanup-key',$3,$4,$5,'READY',$6,now()-interval '20 minutes')`,
    [requestId, scope, 'd'.repeat(64), BODY, reportId, quoteId]);
    const artifact = {
      report_id: reportId,
      report_sha256: 'e'.repeat(64),
      bundle_sha256: 'f'.repeat(64),
      report_size_bytes: 100,
      bundle_size_bytes: 200,
      snapshot_at: '2026-09-29T00:00:00Z',
      snapshot_status: 'VALID_FOR_SNAPSHOT_CALCULATION',
      source_mode: 'live-public',
      limitations: ['synthetic local test'],
    };
    await pool.query(`INSERT INTO artifacts(report_id,scope_hash,report_sha256,bundle_sha256,report_size_bytes,bundle_size_bytes,metadata,published_at)
      VALUES($1,$2,$3,$4,$5,$6,$7,now()-interval '20 minutes')`,
    [reportId, scope, artifact.report_sha256, artifact.bundle_sha256, artifact.report_size_bytes, artifact.bundle_size_bytes, artifact]);
    await pool.query(`INSERT INTO quotes(id,report_request_id,scope_hash,report_id,state,network,chain_id,asset,amount_atomic,pay_to,expected_payer,expires_at,preview,created_at)
      VALUES($1,$2,$3,$4,'EXPIRED','eip155:31611',31611,'0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503',10000000000000000,
      '0x2222222222222222222222222222222222222222',$5,now()-interval '16 minutes',$6,now()-interval '17 minutes')`,
    [quoteId, requestId, scope, reportId, BODY.expected_payer, {
      instrument_id: BODY.instrument_id,
      side: BODY.side,
      quantity_base: BODY.quantity_base,
      snapshot_at: artifact.snapshot_at,
      snapshot_status: artifact.snapshot_status,
      limitations: artifact.limitations,
      price_musd: '0.01',
      expires_at: '2026-09-29T00:00:00Z',
    }]);
    await pool.query("INSERT INTO audit_events(quote_id,event) VALUES($1,'ARTIFACT_PUBLISHED')", [quoteId]);
    await pool.query(`INSERT INTO payment_attempts(id,quote_id,authorization_identity,identity_version,authorization_valid_until,correlation,state,tx_hash)
      VALUES($1,$2,'test-authorization','test/v1',now()+interval '1 hour','{}','REJECTED',$3)`,
    [randomUUID(), quoteId, `0x${'1'.repeat(64)}`]);
    await pool.query('COMMIT');
  } catch (error) {
    await pool.query('ROLLBACK');
    throw error;
  }

  let calls = 0;
  const server = createServer((request, response) => {
    calls += 1;
    assert.equal(request.method, 'DELETE');
    assert.equal(request.url, `/internal/v1/reports/${reportId}`);
    assert.equal(request.headers.authorization, 'Bearer test_cleanup_token_1234567890');
    if (calls === 1) {
      response.socket?.destroy();
      return;
    }
    response.writeHead(200, { 'content-type': 'application/json' });
    response.end(JSON.stringify({ report_id: reportId, deleted: false }));
  });
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
  const address = server.address();
  assert(address && typeof address === 'object');
  const reports = new HttpReportService(new URL(`http://127.0.0.1:${address.port}`), 'test_cleanup_token_1234567890');
  const gateway = { ledger: new Ledger(pool), reports } as unknown as Gateway;
  try {
    await assert.rejects(retainAndRecover(gateway));
    assert.equal((await pool.query('SELECT storage_state FROM artifacts WHERE report_id=$1', [reportId])).rows[0]!.storage_state, 'AVAILABLE');
    assert.equal((await pool.query("SELECT count(*)::int AS count FROM audit_events WHERE quote_id=$1 AND event='UNPAID_ARTIFACT_REMOVED'", [quoteId])).rows[0]!.count, 0);

    await retainAndRecover(gateway);
    await retainAndRecover(gateway);
  } finally {
    server.close();
    await once(server, 'close');
  }
  assert.equal(calls, 2);
  assert.equal((await pool.query('SELECT storage_state FROM artifacts WHERE report_id=$1', [reportId])).rows[0]!.storage_state, 'DELETED');
  assert.equal((await pool.query("SELECT count(*)::int AS count FROM audit_events WHERE quote_id=$1 AND event='UNPAID_ARTIFACT_REMOVED'", [quoteId])).rows[0]!.count, 1);
  assert.equal((await pool.query('SELECT count(*)::int AS count FROM report_requests WHERE id=$1', [requestId])).rows[0]!.count, 1);
  assert.equal((await pool.query('SELECT count(*)::int AS count FROM quotes WHERE id=$1', [quoteId])).rows[0]!.count, 1);
  assert.equal((await pool.query('SELECT count(*)::int AS count FROM access_scopes WHERE scope_hash=$1', [scope])).rows[0]!.count, 1);
  await assert.rejects(
    pool.query('UPDATE artifacts SET report_sha256=$2 WHERE report_id=$1', [reportId, '0'.repeat(64)]),
    /immutable artifact identity/,
  );
  await assert.rejects(
    pool.query("UPDATE payment_attempts SET identity_version='mutated' WHERE quote_id=$1", [quoteId]),
    /immutable authorization identity/,
  );
  await assert.rejects(
    pool.query('UPDATE payment_attempts SET tx_hash=$2 WHERE quote_id=$1', [quoteId, `0x${'2'.repeat(64)}`]),
    /immutable transaction association/,
  );
});


test('real startup survives invalid grant and keeps new payments disabled', {skip:skipReason,timeout:15000}, async()=>{
  const directory=await mkdtemp(join(tmpdir(),'liqvera-startup-'));
  const grant=join(directory,'invalid-grant');
  await writeFile(grant,'{}',{mode:0o600});
  const reserve=createServer();reserve.listen(0,'127.0.0.1');await once(reserve,'listening');
  const address=reserve.address();assert.ok(address&&typeof address==='object');const port=address.port;
  await new Promise<void>(resolve=>reserve.close(()=>resolve()));
  const metrics=createServer();metrics.listen(0,'127.0.0.1');await once(metrics,'listening');
  const metricsAddress=metrics.address();assert.ok(metricsAddress&&typeof metricsAddress==='object');
  await new Promise<void>(resolve=>metrics.close(()=>resolve()));
  const env={PATH:process.env.PATH,DATABASE_URL:databaseUrl!,SOURCE_MODE:'live-public',HOST:'127.0.0.1',PORT:String(port),
    METRICS_PORT:String(metricsAddress.port),PUBLIC_BASE_URL:`http://127.0.0.1:${port}`,ARTIFACT_ROOT:directory,
    LIQVERA_LIVE_GRANT_FILE:grant,LIQVERA_SUBJECT_COMMIT:'a'.repeat(40),LIQVERA_SUBJECT_TREE:'b'.repeat(40),LIQVERA_PLAN_SHA256:'c'.repeat(64),
    LIQVERA_LIVE_BUYER:'0x1111111111111111111111111111111111111111',PAY_TO:'0x2222222222222222222222222222222222222222'};
  const child=spawn(process.execPath,[fileURLToPath(new URL('../../dist/main.js',import.meta.url))],{env,stdio:['ignore','pipe','pipe']});
  let output='';child.stdout.on('data',chunk=>{output+=String(chunk);});child.stderr.on('data',chunk=>{output+=String(chunk);});
  const exited=once(child,'exit');
  try {
    const deadline=Date.now()+10000;
    while(!output.includes('GATEWAY_STARTED')&&child.exitCode===null&&Date.now()<deadline)await new Promise(resolve=>setTimeout(resolve,25));
    assert.match(output,/GATEWAY_STARTED/);
    assert.match(output,/PAYMENTS_DISABLED/);assert.match(output,/LIVE_GRANT_INVALID/);
    assert.doesNotMatch(output,/STARTUP_FAILED/);
    assert.equal((await fetch(`http://127.0.0.1:${port}/healthz`)).status,200);
    const capabilities=await fetch(`http://127.0.0.1:${port}/v1/capabilities`);assert.equal(capabilities.status,200);
    const body=await capabilities.json() as {payment_ready:boolean;blockers:string[]};
    assert.equal(body.payment_ready,false);assert.ok(body.blockers.includes('EXTERNAL_GRANT_REQUIRED'));
    const post=await fetch(`http://127.0.0.1:${port}/v1/report-quotes`,{method:'POST'});
    assert.notEqual(post.status,201);assert.notEqual(post.status,202);
  }finally{child.kill('SIGTERM');await exited;await rm(directory,{recursive:true,force:true});}
});

test('Mainnet ledger has a distinct immutable network identity and rejects Testnet startup', {skip:skipReason}, async()=>{
  const url=new URL(databaseUrl!);const name=url.pathname.slice(1)+'_network';
  assert.match(name,/^liqvera_f4_test_[a-z0-9_]+_network$/);
  const adminUrl=new URL(url);adminUrl.pathname='/postgres';
  const admin=new Pool({connectionString:adminUrl.toString()});await admin.query(`CREATE DATABASE "${name}"`);await admin.end();
  url.pathname='/'+name;await runMigrator(url.toString());
  const script=`import {Pool} from 'pg';import {Ledger} from './dist/adapters/postgres.js';
    const pool=new Pool({connectionString:process.argv[1]});const ledger=new Ledger(pool);await ledger.assertNetwork();
    console.log(JSON.stringify((await pool.query('SELECT chain_id FROM ledger_network')).rows));await pool.end();`;
  const result=await execFileAsync(process.execPath,['--input-type=module','-e',script,url.toString()],{env:{...process.env,LIQVERA_NETWORK:'mainnet'}});
  assert.deepEqual(JSON.parse(result.stdout),[{chain_id:31612}]);
  const mainnet=new Pool({connectionString:url.toString()});
  try {
    await assert.rejects(()=>new Ledger(mainnet).assertNetwork(),/LEDGER_NETWORK_MISMATCH/);
    await assert.rejects(()=>mainnet.query('UPDATE ledger_network SET chain_id=31611'),/append-only/);
    assert.deepEqual((await mainnet.query('SELECT chain_id FROM ledger_network')).rows,[{chain_id:31612}]);
  } finally {await mainnet.end();}
});


test('merchant ledger allows repeat buyers with fresh nonces and submits each attempt once', {skip:skipReason}, async()=>{
 const merchant=Reflect.construct(Ledger,[pool,'0x2222222222222222222222222222222222222222']) as Ledger;
 const first=await verifiedAttempt(merchant,'71','v1',BODY.expected_payer,undefined,undefined,'701');
 assert.equal(await new Ledger(pool).markSubmitting(first.attempt),'INVALID_STATE');
 const results=await Promise.all(Array.from({length:20},()=>merchant.markSubmitting(first.attempt)));
 assert.equal(results.filter(x=>x==='SUBMITTING').length,1);
 assert.equal(await merchant.markSubmitting(first.attempt),'INVALID_STATE');
 await merchant.unknown(first.attempt,null);
 assert.equal(await merchant.markSubmitting(first.attempt),'INVALID_STATE');
 const second=await verifiedAttempt(merchant,'72','v1',BODY.expected_payer,undefined,undefined,'702');
 assert.equal(await new Ledger(pool,BODY.expected_payer).markSubmitting(second.attempt),'INVALID_STATE');
 assert.equal(await merchant.markSubmitting(second.attempt),'SUBMITTING');
 assert.equal((await pool.query('SELECT count(*)::int AS n FROM live_grant_consumptions WHERE payment_attempt_id=ANY($1::uuid[])',[[first.attempt.id,second.attempt.id]])).rows[0].n,0);
});
test('merchant nonce cannot be replayed across different quotes', {skip:skipReason}, async()=>{
 const ledger=new Ledger(pool);
 const results=await Promise.allSettled(['73','74'].map(suffix=>verifiedAttempt(ledger,suffix,'v1',BODY.expected_payer,undefined,undefined,'703')));
 assert.equal(results.filter(x=>x.status==='fulfilled').length,1);
 const rejected=results.find(x=>x.status==='rejected') as PromiseRejectedResult;
 assert.equal(rejected.reason.code,'AUTHORIZATION_REUSED');
});

test('merchant mode cannot submit grant attempts or expired wallet authorizations', {skip:skipReason}, async()=>{
 const ledger=new Ledger(pool,'0x2222222222222222222222222222222222222222');
 const grant=await verifiedAttempt(ledger,'75');
 assert.equal(await ledger.markSubmitting(grant.attempt),'INVALID_STATE');
 const expired=await verifiedAttempt(ledger,'76','v1',BODY.expected_payer,undefined,undefined,'706',new Date(Date.now()-1000));
 assert.equal(await ledger.markSubmitting(expired.attempt),'EXPIRED');
 assert.equal((await pool.query('SELECT state FROM payment_attempts WHERE id=$1',[expired.attempt.id])).rows[0].state,'REJECTED');
});

test('merchant startup refuses absent nonce index or absent migration receipt', {skip:skipReason}, async()=>{
 const ledger=new Ledger(pool,'0x2222222222222222222222222222222222222222');
 await ledger.assertNetwork();
 const sql=await readFile(new URL('../../migrations/008_merchant_nonce.sql',import.meta.url),'utf8');
 await pool.query('DROP INDEX merchant_permit2_nonce');
 try { await assert.rejects(ledger.assertNetwork(),/MERCHANT_MIGRATION_REQUIRED/); }
 finally { await pool.query(sql); }
 const receipt=(await pool.query("DELETE FROM gateway_migrations WHERE name='008_merchant_nonce.sql' RETURNING *")).rows[0];
 try { await assert.rejects(ledger.assertNetwork(),/MERCHANT_MIGRATION_REQUIRED/); }
 finally { await pool.query('INSERT INTO gateway_migrations(name,sha256,applied_at) VALUES($1,$2,$3)',[receipt.name,receipt.sha256,receipt.applied_at]); }
 await ledger.assertNetwork();
});
