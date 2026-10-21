import test from 'node:test';
import assert from 'node:assert/strict';

import * as finance from '../src/mezo-finance.mjs';

test('finance module exists', () => assert.ok(finance, 'Mezo finance implementation is missing'));

const payer = '0x1111111111111111111111111111111111111111';
const merchant = '0x2222222222222222222222222222222222222222';
const token = '0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503';
const network = { name: 'testnet', chainId: 31611, asset: token, decimals: 18 };
const now = Date.parse('2026-10-13T15:00:00Z');
const unit = 10n ** 18n;
const quote = () => ({
  quote_id: '11111111-1111-4111-8111-111111111111', state: 'READY',
  terms: { network: 'eip155:31611', chain_id: 31611, asset: token, decimals: 18,
    amount_atomic: '10000000000000000', expected_payer: payer, pay_to: merchant,
    expires_at: '2026-10-13T15:05:00Z' },
});
const context = () => ({ network, account: payer, quote: quote(), paymentGuard: 'clear', busy: false, onMezo: true });
if (finance) {
  test('network URLs never fall back across environments', () => {
    assert.equal(finance.financeLinks('testnet').borrow, 'https://testnet.mezo.org/feature/borrow');
    assert.equal(finance.financeLinks('mainnet').borrow, 'https://mezo.org/feature/borrow');
    assert.throws(() => finance.financeLinks('other'));
  });
  test('eligible quote uses exact atomic price', () => {
    assert.deepEqual(finance.fundingEligibility(context(), now), { allowed: true, reason: '', requiredAtomic: 10000000000000000n });
  });
  test('missing initial quote has actionable guidance while unknown outcomes retain recovery guidance', () => {
    const c = {...context(),quote:null,paymentGuard:'unavailable',account:null};
    const initial = finance.fundingEligibility(c, now);
    assert.equal(initial.allowed, false);
    assert.match(initial.reason, /Connect your wallet.*unpaid report/);
    c.account = payer;
    assert.match(finance.fundingEligibility(c, now).reason, /Request an unpaid report/);
    c.paymentGuard = 'unknown';
    assert.match(finance.fundingEligibility(c, now).reason, /existing payment outcome/);
    assert.equal(finance.fundingEligibility(c, now).allowed, false);
  });
  for (const [label, change] of [
    ['wrong wallet network', c => { c.onMezo = false; }],
    ['missing payer', c => { c.account = null; }],
    ['different payer', c => { c.account = merchant; }],
    ['wrong quote chain', c => { c.quote.terms.chain_id = 31612; }],
    ['wrong asset', c => { c.quote.terms.asset = merchant; }],
    ['wrong decimals', c => { c.quote.terms.decimals = 6; }],
    ['wrong CAIP network', c => { c.quote.terms.network = 'eip155:1'; }],
    ['expired quote', c => { c.quote.terms.expires_at = '2026-10-13T14:00:00Z'; }],
    ['invalid expiry', c => { c.quote.terms.expires_at = 'invalid'; }],
    ['uncertain payment', c => { c.quote.state = 'PAYMENT_UNCERTAIN'; }],
    ['pending guard', c => { c.paymentGuard = 'unknown'; }],
    ['busy checkout', c => { c.busy = true; }],
    ['zero amount', c => { c.quote.terms.amount_atomic = '0'; }],
    ['numeric amount', c => { c.quote.terms.amount_atomic = 1; }],
    ['exponent amount', c => { c.quote.terms.amount_atomic = '1e16'; }],
    ['oversized amount', c => { c.quote.terms.amount_atomic = '9'.repeat(100); }],
  ]) test(`blocks ${label}`, () => { const c = context(); change(c); assert.equal(finance.fundingEligibility(c, now).allowed, false); });

  test('integer formatting does not round monetary values', () => {
    assert.equal(finance.formatMusd(10000000000000000n), '0.01');
    assert.equal(finance.formatMusd(unit + 1n), '1.000000000000000001');
    assert.equal(finance.formatMusd(0n), '0');
    assert.throws(() => finance.formatMusd(-1n));
  });
  const provider = (overrides = {}) => {
    const calls = [];
    return { calls, async request(request) {
      calls.push(request);
      if (overrides[request.method]) return overrides[request.method](request, calls);
      if (request.method === 'eth_chainId') return '0x7b7b';
      if (request.method === 'eth_accounts') return [payer];
      if (request.method === 'eth_call') return '0x' + (123n * unit).toString(16).padStart(64, '0');
      throw new Error(`Unexpected wallet method: ${request.method}`);
    }};
  };
  test('balance lookup is read-only and encodes the current payer', async () => {
    const wallet = provider();
    assert.equal(await finance.readMusdBalance(wallet, network, payer), 123n * unit);
    assert.deepEqual(new Set(wallet.calls.map(c => c.method)), new Set(['eth_chainId', 'eth_accounts', 'eth_call']));
    const read = wallet.calls.find(c => c.method === 'eth_call');
    assert.equal(read.params[0].to, token);
    assert.equal(read.params[0].data, '0x70a08231' + payer.slice(2).padStart(64, '0'));
  });
  test('wrong wallet chain fails before token read', async () => {
    const wallet = provider({ eth_chainId: () => '0x1' });
    await assert.rejects(finance.readMusdBalance(wallet, network, payer), /network/i);
    assert.equal(wallet.calls.some(c => c.method === 'eth_call'), false);
  });
  test('chain change during balance call invalidates result', async () => {
    let reads = 0;
    const wallet = provider({ eth_chainId: () => ++reads === 1 ? '0x7b7b' : '0x1' });
    await assert.rejects(finance.readMusdBalance(wallet, network, payer), /network/i);
  });
  test('account change during balance call invalidates result', async () => {
    let reads = 0;
    const wallet = provider({ eth_accounts: () => ++reads === 1 ? [payer] : [merchant] });
    await assert.rejects(finance.readMusdBalance(wallet, network, payer), /account/i);
  });
  for (const bad of ['0x', '0x1', '0xzz', 123, null, '0x' + '0'.repeat(66)]) {
    test(`rejects malformed balance ${String(bad).slice(0, 14)}`, async () => {
      await assert.rejects(finance.readMusdBalance(provider({ eth_call: () => bad }), network, payer), /balance/i);
    });
  }
  test('RPC timeout is bounded', async () => {
    await assert.rejects(finance.readMusdBalance(provider({ eth_call: () => new Promise(() => {}) }), network, payer, 5), /timed out/i);
  });
}
