import test from 'node:test';
import assert from 'node:assert/strict';
import * as finance from '../src/mezo-finance.mjs';

const account = '0x1111111111111111111111111111111111111111';
const network = { name: 'testnet', chainId: 31611, asset: '0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503', decimals: 18 };
const block = { number: '0x123', hash: '0x' + 'a'.repeat(64) };
const price = '10000000000000000';
function wallet(balance = 10n ** 18n, override = {}) {
  const calls = [];
  return { calls, async request(args) {
    calls.push(args);
    if (override[args.method]) return override[args.method](args, calls);
    switch (args.method) {
      case 'eth_chainId': return '0x7b7b';
      case 'eth_accounts': return [account];
      case 'eth_getBlockByNumber': return block;
      case 'eth_call': return '0x' + balance.toString(16).padStart(64, '0');
      default: throw new Error('Unexpected method: ' + args.method);
    }
  }};
}

test('funding observation pins the token read to a block and exports exact budget', async () => {
  assert.equal(typeof finance.readFundingObservation, 'function');
  const provider = wallet(10n ** 18n + 1n);
  const result = await finance.readFundingObservation(provider, network, account, price);
  assert.equal(provider.calls.find(x => x.method === 'eth_call').params[1], block.number);
  assert.deepEqual(provider.calls.filter(x => x.method === 'eth_getBlockByNumber').map(x => x.params), [['latest', false], [block.number, false]]);
  assert.equal(result.block_number, '291');
  assert.equal(result.block_hash, block.hash);
  assert.equal(result.balance_atomic, '1000000000000000001');
  assert.equal(result.report_budget, '100');
  assert.equal(result.shortfall_atomic, '0');
  assert.equal(result.required_atomic, price);
  assert.equal(result.account, account);
  assert.equal(result.chain_id, 31611);
  assert.equal(result.asset, network.asset);
  assert.equal(result.payment_submitted, false);
  assert.ok(Number.isFinite(Date.parse(result.observed_at)));
  assert.doesNotThrow(() => JSON.stringify(result));
});

test('one-wei shortfall is retained without decimal rounding', async () => {
  const result = await finance.readFundingObservation(wallet(BigInt(price) - 1n), network, account, price);
  assert.equal(result.shortfall_atomic, '1');
  assert.equal(result.report_budget, '0');
});

test('changed block hash rejects the observation', async () => {
  let reads = 0;
  const provider = wallet(0n, { eth_getBlockByNumber: () => ++reads === 1 ? block : { ...block, hash: '0x' + 'b'.repeat(64) } });
  await assert.rejects(finance.readFundingObservation(provider, network, account, price), /block/i);
});

for (const bad of [null, {}, { ...block, number: '0x0123' }, { ...block, hash: '0x' }, { ...block, number: 'latest' }]) {
  test('rejects invalid block metadata ' + JSON.stringify(bad), async () => {
    await assert.rejects(finance.readFundingObservation(wallet(0n, { eth_getBlockByNumber: () => bad }), network, account, price), /block/i);
  });
}

test('wrong chain prevents the first block lookup', async () => {
  const provider = wallet(0n, { eth_chainId: () => '0x1' });
  await assert.rejects(finance.readFundingObservation(provider, network, account, price), /network/i);
  assert.equal(provider.calls.some(x => x.method === 'eth_getBlockByNumber'), false);
});

test('account change during final block read rejects the observation', async () => {
  let blocks = 0;
  const provider = wallet(0n, {
    eth_getBlockByNumber: () => { blocks++; return block; },
    eth_accounts: () => [blocks < 2 ? account : '0x2222222222222222222222222222222222222222'],
  });
  await assert.rejects(finance.readFundingObservation(provider, network, account, price), /account/i);
});

test('invalid price is rejected before any wallet call', async () => {
  for (const bad of ['0', '-1', '1e16', 1, '9'.repeat(100)]) {
    const provider = wallet();
    await assert.rejects(finance.readFundingObservation(provider, network, account, bad));
    assert.equal(provider.calls.length, 0);
  }
});

test('block lookup timeout is bounded and cannot become a zero-balance result', async () => {
  const provider = wallet(0n, { eth_getBlockByNumber: () => new Promise(() => {}) });
  await assert.rejects(finance.readFundingObservation(provider, network, account, price, 5), /timed out/i);
});

test('all observation calls share one timeout budget', async t => {
  let clock = 1000;
  t.mock.method(Date, 'now', () => clock);
  const underlying = wallet();
  const provider = { request(args) { clock += 10; return underlying.request(args); } };
  await assert.rejects(finance.readFundingObservation(provider, network, account, price, 25), /timed out/i);
});

test('Mainnet reads its own token and retains Mainnet in the observation', async () => {
  const mainnet = { name: 'mainnet', chainId: 31612, asset: '0xdD468A1DDc392dcdbEf6db6e34E89AA338F9F186', decimals: 18 };
  const provider = wallet(0n, { eth_chainId: () => '0x7b7c' });
  const result = await finance.readFundingObservation(provider, mainnet, account, price);
  assert.equal(result.network, 'eip155:31612');
  assert.equal(provider.calls.find(x => x.method === 'eth_call').params[0].to, mainnet.asset);
});
