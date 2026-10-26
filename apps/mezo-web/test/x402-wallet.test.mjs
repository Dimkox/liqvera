import assert from 'node:assert/strict';
import test, { after } from 'node:test';
import { mkdtemp, rm } from 'node:fs/promises';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { build } from 'esbuild';

// Compile the real browser adapter and its local imports; keep the installed SDK real.
const scratch = await mkdtemp(fileURLToPath(new URL('.x402-wallet-', import.meta.url)));
after(() => rm(scratch, { recursive: true, force: true }));
await build({ entryPoints: [fileURLToPath(new URL('../src/x402.ts', import.meta.url))],
  outfile: `${scratch}/adapter.mjs`, bundle: true, platform: 'node', format: 'esm', packages: 'external' });
const { installProductionX402Adapter, requestPaidReport, X402CancelledBeforeSubmission } = await import(pathToFileURL(`${scratch}/adapter.mjs`));
installProductionX402Adapter();
const payer = '0x1111111111111111111111111111111111111111';
const reportId = '44444444-4444-4444-8444-444444444444';
const asset = '0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503';
const required = { x402Version: 2, resource: { url: `https://liqvera.invalid/v1/reports/${reportId}`, description: 'report', mimeType: 'application/json' }, accepts: [{
  scheme: 'exact', network: 'eip155:31611', asset, amount: '10000000000000000',
  payTo: '0x2222222222222222222222222222222222222222', maxTimeoutSeconds: 120,
  extra: { assetTransferMethod: 'permit2', name: 'Mezo USD', version: '1' },
}], extensions: { eip2612GasSponsoring: { info: { description: 'Gasless permit', version: '1' }, schema: { type: 'object' } } } };
const quote = { report_id: reportId, terms: { expected_payer: payer, network: 'eip155:31611', asset, amount_atomic: '10000000000000000' } };

function transport(t, { paidResponse } = {}) {
  const calls = { challenges: 0, submissions: 0, rpc: 0 };
  const previous = globalThis.fetch;
  t.after(() => { globalThis.fetch = previous; });
  globalThis.fetch = async (url, init = {}) => {
    if (String(url).startsWith('https://rpc.test.mezo.org')) {
      calls.rpc++;
      const request = JSON.parse(init.body);
      const reply = item => ({ jsonrpc: '2.0', id: item.id, result: `0x${'0'.repeat(64)}` });
      return Response.json(Array.isArray(request) ? request.map(reply) : reply(request));
    }
    assert.equal(url, `/v1/reports/${reportId}`);
    const headers = new Headers(init.headers);
    if (headers.has('payment-signature')) {
      calls.submissions++;
      if (paidResponse) return paidResponse();
      return Response.json({ state: 'PAYMENT_PENDING' }, { status: 202 });
    }
    calls.challenges++;
    return Response.json({ code: 'PAYMENT_REQUIRED' }, { status: 402,
      headers: { 'payment-required': Buffer.from(JSON.stringify(required)).toString('base64') } });
  };
  return calls;
}

function pay(provider, onRecoveryInfo) {
  return requestPaidReport({ path: `/v1/reports/${reportId}`, bearerCapability: 'test-only-capability', quote, provider, payer, onRecoveryInfo });
}

test('production adapter sends exact SDK integer values to the wallet before submission', async t => {
  const calls = transport(t);
  const messages = [];
  const result = await pay({ request: async ({ method, params }) => {
    assert.equal(method, 'eth_signTypedData_v4');
    assert.equal(params[0], payer);
    const typed = JSON.parse(params[1]);
    messages.push(typed);
    return `0x${'A'.repeat(130)}`;
  } });
  assert.equal(messages.length, 2, 'Both Permit2 and EIP-2612 requests must actually reach the wallet');
  assert.deepEqual(messages.map(m => m.primaryType), ['PermitWitnessTransferFrom', 'Permit']);
  assert.deepEqual(messages[0].types.EIP712Domain, [
    { name: 'name', type: 'string' }, { name: 'chainId', type: 'uint256' },
    { name: 'verifyingContract', type: 'address' },
  ], 'The wallet must hash the actual Permit2 domain, not an empty domain');
  assert.deepEqual(messages[1].types.EIP712Domain, [
    { name: 'name', type: 'string' }, { name: 'version', type: 'string' },
    { name: 'chainId', type: 'uint256' }, { name: 'verifyingContract', type: 'address' },
  ]);
  assert.equal(Number(messages[0].domain.chainId), 31611);
  assert.equal(messages[0].domain.verifyingContract.toLowerCase(), '0x000000000022d473030f116ddee9f6b43ac78ba3');
  assert.equal(messages[1].domain.verifyingContract.toLowerCase(), asset.toLowerCase());
  assert.equal(messages[0].message.permitted.amount, '10000000000000000');
  assert.match(messages[0].message.nonce, /^\d+$/);
  assert.equal(messages[1].message.value, '10000000000000000');
  assert.equal(calls.submissions, 1);
  assert.equal(result, 'recovering');
});

for (const rejectionAt of [1, 2]) {
  test(`wallet rejection at signature ${rejectionAt} is a proven pre-submit cancellation`, async t => {
    const calls = transport(t);
    let signatures = 0;
    const error = await pay({ request: async () => {
      signatures++;
      if (signatures === rejectionAt) throw Object.assign(new Error('User rejected request'), { code: 4001 });
      return `0x${'A'.repeat(130)}`;
    } }).then(() => null, error => error);
    assert.equal(signatures, rejectionAt, 'The wallet rejection must be exercised');
    assert.ok(error instanceof X402CancelledBeforeSubmission);
    assert.equal(calls.submissions, 0);
  });
}

test('a transport error after signature submission remains confirm-only', async t => {
  const calls = transport(t, { paidResponse: () => { throw Object.assign(new Error('Connection lost'), { code: 4001 }); } });
  const result = await pay({ request: async () => `0x${'A'.repeat(130)}` });
  assert.equal(calls.submissions, 1, 'The failure must happen after the payment payload was sent');
  assert.equal(result, 'recovering');
});

test('pending response persists the gateway attempt and facilitator transaction hash for recovery',async t=>{
  const txHash=`0x${'a'.repeat(64)}`;const paymentAttemptId='33333333-3333-4333-8333-333333333333';const seen=[];
  const calls=transport(t,{paidResponse:()=>Response.json({state:'PAYMENT_UNCERTAIN'},{status:202,headers:{'x-liqvera-payment-tx':txHash,'x-liqvera-payment-attempt':paymentAttemptId}})});
  const result=await pay({request:async()=>`0x${'A'.repeat(130)}`},info=>seen.push(info));
  assert.equal(result,'recovering');assert.equal(calls.submissions,1);
  assert.deepEqual(seen,[{txHash,paymentAttemptId}]);
});
