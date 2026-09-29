import assert from 'node:assert/strict';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import type { PaymentPayload, PaymentRequirements } from '@x402/core/types';
import { Gateway } from '../src/application/gateway.js';
import { Contracts } from '../src/adapters/contracts.js';
import type { Ledger } from '../src/adapters/postgres.js';
import {
  AMOUNT,
  ASSET,
  CHAIN_ID,
  NETWORK,
  PublicError,
  type Artifact,
  type Attempt,
  type AuthorizationIdentity,
  type Confirmation,
  type Quote,
  type Receipt,
} from '../src/domain/model.js';
import type { ArtifactStore, PaymentPort, ReportService } from '../src/ports/index.js';
import { reconcileOne, recoverUnsubmitted } from '../src/workers/reconciliation.js';

const payer = '0x1111111111111111111111111111111111111111';
const receiver = '0x2222222222222222222222222222222222222222';
const digest = 'a'.repeat(64);
const bundleDigest = 'b'.repeat(64);

function quote(id = '00000000-0000-4000-8000-000000000001'): Quote {
  const artifact: Artifact = {
    report_id: id,
    report_sha256: digest,
    bundle_sha256: bundleDigest,
    report_size_bytes: 2,
    bundle_size_bytes: 3,
    snapshot_at: '2026-09-29T00:00:00Z',
    snapshot_status: 'VALID_FOR_SNAPSHOT_CALCULATION',
    source_mode: 'live-public',
    limitations: [],
  };
  return {
    id,
    report_request_id: '00000000-0000-4000-8000-000000000010',
    scope_hash: 'scope',
    report_id: id,
    report_sha256: digest,
    bundle_sha256: bundleDigest,
    state: 'READY',
    expires_at: new Date('2099-01-01T00:00:00Z'),
    artifact,
    terms: {
      version: 'mee-evidence-terms/v1',
      network: NETWORK,
      chain_id: CHAIN_ID,
      asset: ASSET,
      decimals: 18,
      amount_atomic: AMOUNT,
      price_musd: '0.01',
      pay_to: receiver,
      expected_payer: payer,
      expires_at: '2099-01-01T00:00:00Z',
    },
    preview: {
      instrument_id: 'hyperliquid:BTC:perpetual',
      side: 'BUY',
      quantity_base: '0.1',
      snapshot_at: '2026-09-29T00:00:00Z',
      snapshot_status: 'VALID_FOR_SNAPSHOT_CALCULATION',
      limitations: [],
      price_musd: '0.01',
      expires_at: '2099-01-01T00:00:00Z',
    },
  };
}

function receipt(q: Quote, attempt: Attempt): Receipt {
  return {
    schema: 'mee-evidence-receipt/v1',
    quote_id: q.id,
    report_id: q.report_id,
    payment_attempt_id: attempt.id,
    report_sha256: q.report_sha256,
    network: NETWORK,
    chain_id: CHAIN_ID,
    asset: ASSET,
    amount_atomic: AMOUNT,
    payer,
    pay_to: receiver,
    tx_hash: `0x${'3'.repeat(64)}`,
    block_hash: `0x${'4'.repeat(64)}`,
    block_number: 1,
    log_index: 0,
    confirmed_at: '2026-09-29T00:00:01Z',
    finality_policy_version: 'TEST_ONLY/v1',
  };
}

class ScriptedPayment implements PaymentPort {
  settleCalls = 0;
  confirmCalls = 0;
  revalidateCalls = 0;
  constructor(
    readonly identity = 'canonical-auth-1',
    readonly settleOutcome: 'hash' | 'throw' = 'hash',
    public confirmation: Confirmation | null | undefined = undefined,
    public current = true,
  ) {}
  blockers() { return []; }
  async requirements() { return { header: 'required', value: {} as PaymentRequirements }; }
  async verify(_header: string, _quote: Quote): Promise<{ payload: PaymentPayload; requirements: PaymentRequirements; identity: AuthorizationIdentity }> {
    return {
      payload: {} as PaymentPayload,
      requirements: {} as PaymentRequirements,
      identity: { identity: this.identity, version: 'TEST_ONLY/v1', payer, valid_until: '2099-01-01T00:00:00Z', correlation: {} },
    };
  }
  async settle() {
    this.settleCalls += 1;
    if (this.settleOutcome === 'throw') throw new Error('lost settlement response');
    return { tx_hash: `0x${'3'.repeat(64)}` };
  }
  async confirm(q: Quote, attempt: Attempt) {
    this.confirmCalls += 1;
    return this.confirmation === undefined ? { receipt: receipt(q, attempt), response_header: 'paid' } : this.confirmation;
  }
  async revalidate() { this.revalidateCalls += 1; return this.current; }
}

class MemoryLedger {
  readonly quotes = new Map<string, Quote>();
  readonly attempts = new Map<string, Attempt>();
  readonly usedIdentities = new Set<string>();
  readonly entitlements = new Map<string, Confirmation>();
  readonly trace: string[] = [];
  manualCalls = 0;
  confirmMode: 'accept' | 'reject-binding' = 'accept';
  lease: Attempt | undefined;
  stale: Attempt[] = [];
  readonly pool = {
    query: async (sql: string, params?: unknown[]): Promise<{ rows: unknown[]; rowCount: number }> => {
      this.trace.push(sql.startsWith('INSERT INTO reconciliation_events') ? `reconciliation:${String(params?.[1])}` : 'pool:query');
      return { rows: [], rowCount: 0 };
    },
  };
  constructor(...quotes: Quote[]) { for (const item of quotes) this.quotes.set(item.id, item); }
  async healthy() { return true; }
  async quote(_scope: string, id: string) {
    const item = this.quotes.get(id);
    if (!item) throw new PublicError('NOT_FOUND', 404);
    return item;
  }
  async beginAttempt(q: Quote, identity: AuthorizationIdentity) {
    this.trace.push('attempt:begin');
    if (this.usedIdentities.has(identity.identity)) throw new PublicError('AUTHORIZATION_REUSED', 409);
    this.usedIdentities.add(identity.identity);
    const attempt: Attempt = {
      id: `00000000-0000-4000-8000-${String(this.attempts.size + 1).padStart(12, '0')}`,
      quote_id: q.id,
      state: 'VERIFIED',
      authorization_identity: identity.identity,
      identity_version: identity.version,
      authorization_valid_until: new Date(identity.valid_until),
      correlation: identity.correlation,
      tx_hash: null,
      submitted_at: null,
      reconciliation_count: 0,
    };
    this.attempts.set(attempt.id, attempt);
    q.state = 'PAYMENT_PENDING';
    return attempt;
  }
  async markSubmitting(attempt: Attempt) {
    this.trace.push('attempt:submitting');
    attempt.state = 'SUBMITTING';
    attempt.submitted_at = new Date('2026-09-29T00:00:00Z');
    return true;
  }
  async unknown(attempt: Attempt, txHash: string | null) {
    this.trace.push('attempt:unknown');
    attempt.state = 'UNKNOWN';
    attempt.tx_hash = txHash;
    this.quotes.get(attempt.quote_id)!.state = 'PAYMENT_UNCERTAIN';
  }
  async confirm(q: Quote, attempt: Attempt, confirmation: Confirmation) {
    this.trace.push('attempt:confirm');
    if (this.confirmMode === 'reject-binding') throw new PublicError('PAYMENT_REJECTED', 402);
    attempt.state = 'CONFIRMED';
    q.state = 'PAID';
    this.entitlements.set(q.id, confirmation);
  }
  async manualReview(q: Quote, attempt: Attempt) {
    this.trace.push('attempt:manual-review');
    this.manualCalls += 1;
    attempt.state = 'MANUAL_REVIEW';
    q.state = 'MANUAL_REVIEW';
  }
  async confirmation(q: Quote) {
    const confirmation = this.entitlements.get(q.id);
    const attempt = [...this.attempts.values()].find(item => item.quote_id === q.id);
    return confirmation && attempt ? { confirmation, attempt, retain_until: new Date('2099-01-01T00:00:00Z') } : null;
  }
  async recordDelivery() { this.trace.push('delivery'); }
  async quoteForAttempt(attempt: Attempt) { return this.quotes.get(attempt.quote_id)!; }
  async expire(q: Quote) { q.state = 'EXPIRED'; }
  async transaction<T>(callback: (db: { query: (sql: string) => Promise<{ rows: unknown[]; rowCount: number }> }) => Promise<T>) {
    const db = {
      query: async (sql: string): Promise<{ rows: unknown[]; rowCount: number }> => {
        if (sql.includes("state IN ('SUBMITTING','UNKNOWN')")) {
          const item = this.lease;
          this.lease = undefined;
          if (item) item.reconciliation_count += 1;
          return { rows: item ? [item] : [], rowCount: item ? 1 : 0 };
        }
        if (sql.includes("state IN ('RECEIVED','VERIFIED')") && sql.includes('SELECT')) {
          return { rows: this.stale.map(item => ({ id: item.id, quote_id: item.quote_id })), rowCount: this.stale.length };
        }
        if (sql.includes("SET state='REJECTED'")) {
          const id = /WHERE id=\$1/.test(sql) ? this.stale[0]?.id : undefined;
          const item = id ? this.attempts.get(id) : undefined;
          if (item) item.state = 'REJECTED';
          return { rows: item ? [{ id }] : [], rowCount: item ? 1 : 0 };
        }
        if (sql.includes('UPDATE quotes SET state=CASE')) {
          const item = this.stale.shift();
          if (item) this.quotes.get(item.quote_id)!.state = 'READY';
          return { rows: [], rowCount: item ? 1 : 0 };
        }
        return { rows: [], rowCount: 0 };
      },
    };
    return callback(db);
  }
}

async function fixture(options: { settle?: 'hash' | 'throw'; rejectBinding?: boolean } = {}) {
  const q = quote();
  const ledger = new MemoryLedger(q);
  ledger.confirmMode = options.rejectBinding ? 'reject-binding' : 'accept';
  const payment = new ScriptedPayment('canonical-auth-1', options.settle);
  const root = await mkdtemp(join(tmpdir(), 'liqvera-f5-'));
  await writeFile(join(root, 'report.json'), '{}');
  await writeFile(join(root, 'evidence.zip'), 'zip');
  const artifacts: ArtifactStore = {
    async healthy() { return true; },
    async read(_artifact, kind) { return readFile(join(root, kind === 'report' ? 'report.json' : 'evidence.zip')); },
  };
  const reports = { async healthy() { return true; }, cleanupReady() { return true; } } as ReportService;
  const contracts = await Contracts.load(new URL('../../dist/contracts/', import.meta.url));
  const validate = contracts.assert.bind(contracts);
  contracts.assert = (name, value) => { if (name !== 'report') validate(name, value); };
  const gateway = new Gateway(ledger as unknown as Ledger, reports, artifacts, payment, contracts, { payTo: receiver, sourceMode: 'live-public' });
  return { q, ledger, payment, gateway, cleanup: () => rm(root, { recursive: true, force: true }) };
}

async function expectPublicError(code: string, operation: () => Promise<unknown>) {
  await assert.rejects(operation, (error: unknown) => error instanceof PublicError && error.code === code);
}

test('direct receipt-binding rejection immediately enters manual review without entitlement or delivery', async t => {
  const f = await fixture({ rejectBinding: true });
  t.after(f.cleanup);
  await expectPublicError('PAYMENT_UNCERTAIN', () => f.gateway.read('scope', f.q.id, 'report', 'signature', 'request-1'));
  const attempt = [...f.ledger.attempts.values()][0]!;
  assert.equal(f.payment.settleCalls, 1);
  assert.equal(f.ledger.manualCalls, 1);
  assert.equal(f.q.state, 'MANUAL_REVIEW');
  assert.equal(attempt.state, 'MANUAL_REVIEW');
  assert.equal(f.ledger.entitlements.size, 0);
  assert.ok(!f.ledger.trace.includes('delivery'));
});

test('reconciliation receipt-binding rejection immediately enters manual review and never settles', async t => {
  const f = await fixture({ rejectBinding: true });
  t.after(f.cleanup);
  const attempt: Attempt = {
    id: '00000000-0000-4000-8000-000000000020', quote_id: f.q.id, state: 'UNKNOWN', authorization_identity: 'canonical-auth-1',
    identity_version: 'TEST_ONLY/v1', authorization_valid_until: new Date('2099-01-01T00:00:00Z'),
    correlation: {}, tx_hash: `0x${'3'.repeat(64)}`, submitted_at: new Date(), reconciliation_count: 1,
  };
  f.q.state = 'PAYMENT_UNCERTAIN';
  f.ledger.attempts.set(attempt.id, attempt);
  f.ledger.lease = attempt;
  assert.equal(await reconcileOne(f.gateway), true);
  assert.equal(f.payment.settleCalls, 0);
  assert.equal(f.ledger.manualCalls, 1);
  assert.equal(f.q.state, 'MANUAL_REVIEW');
  assert.equal(attempt.state, 'MANUAL_REVIEW');
  assert.equal(f.ledger.entitlements.size, 0);
  assert.deepEqual(f.ledger.trace.filter(event => event !== 'pool:query'), [
    'attempt:unknown',
    'attempt:confirm',
    'attempt:manual-review',
    'reconciliation:MANUAL_REVIEW',
  ]);
  assert.ok(!f.ledger.trace.includes('delivery'));
});

test('null confirmation stays uncertain below the bound and enters manual review at returned count ten', async t => {
  const f = await fixture();
  t.after(f.cleanup);
  f.payment.confirmation = null;
  const attempt: Attempt = {
    id: '00000000-0000-4000-8000-000000000021', quote_id: f.q.id, state: 'UNKNOWN', authorization_identity: 'canonical-auth-1',
    identity_version: 'TEST_ONLY/v1', authorization_valid_until: new Date('2099-01-01T00:00:00Z'),
    correlation: {}, tx_hash: `0x${'3'.repeat(64)}`, submitted_at: new Date(), reconciliation_count: 8,
  };
  f.q.state = 'PAYMENT_UNCERTAIN';
  f.ledger.attempts.set(attempt.id, attempt);
  f.ledger.lease = attempt;
  assert.equal(await reconcileOne(f.gateway), true);
  assert.equal(attempt.reconciliation_count, 9);
  assert.equal(attempt.state, 'UNKNOWN');
  assert.equal(f.q.state, 'PAYMENT_UNCERTAIN');
  assert.equal(f.ledger.trace.includes('reconciliation:PAYMENT_UNCERTAIN'), true);
  f.ledger.lease = attempt;
  assert.equal(await reconcileOne(f.gateway), true);
  assert.equal(attempt.reconciliation_count, 10);
  assert.equal(attempt.state, 'MANUAL_REVIEW');
  assert.equal(f.q.state, 'MANUAL_REVIEW');
  assert.equal(f.ledger.trace.at(-2), 'reconciliation:MANUAL_REVIEW');
  assert.equal(f.payment.settleCalls, 0);
  assert.equal(f.ledger.entitlements.size, 0);
  assert.ok(!f.ledger.trace.includes('delivery'));
});

test('packaged frozen state machine accepts scoped guards and rejects one unmet guard', async t => {
  const f = await fixture();
  t.after(f.cleanup);
  const guards = {
    not_expired: true,
    scope_matches: true,
    payer_matches: true,
    terms_match: true,
    artifact_readback_verified: true,
    payment_bindings_verified: true,
    no_active_attempt: true,
    authorization_unique: true,
  };
  assert.equal(f.gateway.contracts.states.next('quote', 'READY', 'authorization_accepted', guards), 'PAYMENT_PENDING');
  assert.throws(
    () => f.gateway.contracts.states.next('quote', 'READY', 'authorization_accepted', { ...guards, scope_matches: false }),
    (error: unknown) => error instanceof PublicError && error.code === 'INVALID_STATE',
  );
});

test('post-submit lost response stays unknown and replay cannot resettle', async t => {
  const f = await fixture({ settle: 'throw' });
  t.after(f.cleanup);
  await expectPublicError('PAYMENT_UNCERTAIN', () => f.gateway.read('scope', f.q.id, 'report', 'signature', 'request-1'));
  await expectPublicError('PAYMENT_UNCERTAIN', () => f.gateway.read('scope', f.q.id, 'report', 'signature', 'request-2'));
  assert.equal(f.payment.settleCalls, 1);
  assert.equal(f.q.state, 'PAYMENT_UNCERTAIN');
  assert.equal([...f.ledger.attempts.values()][0]!.state, 'UNKNOWN');
  assert.equal(f.ledger.entitlements.size, 0);
});

test('canonical authorization identity cannot be reused by another quote', async t => {
  const f = await fixture({ rejectBinding: true });
  t.after(f.cleanup);
  await expectPublicError('PAYMENT_UNCERTAIN', () => f.gateway.read('scope', f.q.id, 'report', 'encoding-a', 'request-1'));
  const second = quote('00000000-0000-4000-8000-000000000002');
  f.ledger.quotes.set(second.id, second);
  await expectPublicError('AUTHORIZATION_REUSED', () => f.gateway.read('scope', second.id, 'report', 'encoding-b', 'request-2'));
  assert.equal(f.payment.settleCalls, 1);
  assert.equal(f.ledger.entitlements.has(second.id), false);
});

test('stale verified attempt is definitively rejected and quote reopened without settlement', async t => {
  const f = await fixture();
  t.after(f.cleanup);
  const identity = (await f.payment.verify('signature', f.q)).identity;
  const attempt = await f.ledger.beginAttempt(f.q, identity);
  f.ledger.stale.push(attempt);
  await recoverUnsubmitted(f.gateway);
  assert.equal(attempt.state, 'REJECTED');
  assert.equal(f.q.state, 'READY');
  assert.equal(f.payment.settleCalls, 0);
});

test('confirmed entitlement is reused, then reorg withholds delivery without resettlement', async t => {
  const f = await fixture();
  t.after(f.cleanup);
  const first = await f.gateway.read('scope', f.q.id, 'report', 'signature', 'request-1');
  assert.equal(first.status, 200);
  assert.equal(f.ledger.entitlements.size, 1);
  const repeat = await f.gateway.read('scope', f.q.id, 'bundle', undefined, 'request-2');
  assert.equal(repeat.status, 200);
  assert.equal(f.payment.settleCalls, 1);
  f.payment.current = false;
  await expectPublicError('MANUAL_REVIEW', () => f.gateway.read('scope', f.q.id, 'report', undefined, 'request-3'));
  assert.equal(f.payment.settleCalls, 1);
  assert.equal(f.q.state, 'MANUAL_REVIEW');
  assert.equal([...f.ledger.attempts.values()][0]!.state, 'MANUAL_REVIEW');
});
