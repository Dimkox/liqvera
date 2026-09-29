import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { randomUUID } from 'node:crypto';
import { once } from 'node:events';
import { readFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import { fileURLToPath } from 'node:url';
import { promisify } from 'node:util';
import test, { after, before } from 'node:test';
import { Pool } from 'pg';
import { HttpReportService } from '../src/adapters/report-service.js';
import { Ledger } from '../src/adapters/postgres.js';
import { PublicError, type QuoteInput } from '../src/domain/model.js';
import type { Gateway } from '../src/application/gateway.js';
import { retainAndRecover } from '../src/workers/retention.js';

const execFileAsync = promisify(execFile);
const databaseUrl = process.env.TEST_DATABASE_URL;
const marker = process.env.TEST_DATABASE_DISPOSABLE === '1';
const skipReason = databaseUrl && marker ? undefined : 'requires an explicitly disposable local PostgreSQL URL';
const MIGRATION_001_SHA256 = 'bc127e55c876961112f33ca2abdfac01827769d6156ddba2f42856d070c75b3b';
const MIGRATION_002_SHA256 = '981f48215e64fdd0fb72be5a6df78238cf8050de722adb454b4e28b1940ccbcb';
const BODY: QuoteInput = {
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
});

after(async () => {
  if (pool) await pool.end();
});

test('fresh migration applies 001 then 002 once, reruns by checksum, and keeps audit rows append-only', { skip: skipReason }, async () => {
  const migrations = await pool.query<{ name: string; sha256: string }>(
    'SELECT name,sha256 FROM gateway_migrations ORDER BY name',
  );
  assert.deepEqual(migrations.rows, [
    { name: '001_ledger.sql', sha256: MIGRATION_001_SHA256 },
    { name: '002_fix_immutable_ledger_identity.sql', sha256: MIGRATION_002_SHA256 },
  ]);

  const audit = await pool.query<{ id: string }>("INSERT INTO audit_events(event) VALUES('TEST_ONLY') RETURNING id");
  await assert.rejects(
    pool.query("UPDATE audit_events SET event='MUTATED' WHERE id=$1", [audit.rows[0]!.id]),
    /append-only record/,
  );
  assert.equal((await pool.query('SELECT count(*)::int AS count FROM audit_events WHERE id=$1', [audit.rows[0]!.id])).rows[0]!.count, 1);
});

test('an existing 001 ledger upgrades to 002 without replacing state', { skip: skipReason }, async () => {
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
