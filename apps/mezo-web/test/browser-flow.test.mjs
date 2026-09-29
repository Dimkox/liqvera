import assert from "node:assert/strict";
import test from "node:test";

import {
  beginPayment,
  canPay,
  paymentFailure,
  paymentNotice,
  readWallet,
  recoveryRequest,
  switchWalletToMezo,
  walletStatus,
} from "../src/browser-flow.ts";

const payer = "0x1111111111111111111111111111111111111111";
const other = "0x2222222222222222222222222222222222222222";
const quoteId = "11111111-1111-4111-8111-111111111111";
const requestId = "22222222-2222-4222-8222-222222222222";
const key = "33333333-3333-4333-8333-333333333333";

function flow(overrides = {}) {
  return { version: 1, side: "BUY", quantity: "0.15", payer, idempotencyKey: key, paymentGuard: "clear", ...overrides };
}

class FakeProvider {
  calls = [];
  constructor(account = payer, chain = "0x1") { this.account = account; this.chain = chain; }
  async request(input) {
    this.calls.push(input);
    if (input.method === "eth_accounts") return [this.account];
    if (input.method === "eth_chainId") return this.chain;
    if (input.method === "wallet_switchEthereumChain") { this.chain = input.params[0].chainId; return null; }
    throw new Error(`unplanned wallet request: ${input.method}`);
  }
}

test("wrong network is explicit and switching never submits payment", async () => {
  const provider = new FakeProvider();
  assert.deepEqual(await readWallet(provider), { account: payer, onMezo: false });
  assert.equal(canPay({ flow: flow(), quoteState: "READY", connectedAccount: payer, onMezo: false, paymentReady: true, adapterAvailable: true }), false);
  assert.equal(walletStatus(true, false), "Wrong network · switch to Mezo Testnet (31611).");
  assert.deepEqual(await switchWalletToMezo(provider), { account: payer, onMezo: true });
  assert.deepEqual(provider.calls.map(call => call.method), ["eth_accounts", "eth_chainId", "wallet_switchEthereumChain", "eth_accounts", "eth_chainId"]);
});

test("account and chain changes preserve the payer and disable the old quote", () => {
  const saved = flow({ quoteId });
  assert.equal(canPay({ flow: saved, quoteState: "READY", connectedAccount: other, onMezo: true, paymentReady: true, adapterAvailable: true }), false);
  assert.equal(canPay({ flow: saved, quoteState: "READY", connectedAccount: payer, onMezo: false, paymentReady: true, adapterAvailable: true }), false);
  assert.equal(saved.payer, payer);
});

test("typed pre-submit cancellation clears only with a fresh READY quote", () => {
  const started = beginPayment(flow({ quoteId }));
  assert.equal(started.paymentGuard, "started");
  assert.equal(paymentFailure(started, "cancelled-before-submission", "READY").paymentGuard, "clear");
  assert.equal(paymentFailure(started, "cancelled-before-submission", null).paymentGuard, "uncertain");
  assert.equal(paymentFailure(started, "ambiguous", "READY").paymentGuard, "uncertain");
});

test("reload recovery uses only the saved identity and exact create replay", () => {
  assert.deepEqual(recoveryRequest(flow()), {
    kind: "create",
    method: "POST",
    path: "/v1/report-quotes",
    idempotencyKey: key,
    body: { side: "BUY", quantity: "0.15", payer },
  });
  assert.deepEqual(recoveryRequest(flow({ requestId })), { kind: "request", method: "GET", path: `/v1/report-requests/${requestId}` });
  assert.deepEqual(recoveryRequest(flow({ requestId, quoteId })), { kind: "quote", method: "GET", path: `/v1/report-quotes/${quoteId}` });
});

test("pending, uncertain, manual review, paid reuse, and fixture mode cannot resettle", () => {
  for (const quoteState of ["PAYMENT_PENDING", "PAYMENT_UNCERTAIN", "MANUAL_REVIEW", "PAID"]) {
    assert.equal(canPay({ flow: flow({ quoteId, paymentGuard: "uncertain" }), quoteState, connectedAccount: payer, onMezo: true, paymentReady: true, adapterAvailable: true }), false);
  }
  assert.match(paymentNotice("PAYMENT_UNCERTAIN", "uncertain"), /Do not pay again/);
  assert.equal(paymentNotice("PAID", "clear"), null);
  assert.equal(canPay({ flow: flow({ quoteId }), quoteState: "READY", connectedAccount: payer, onMezo: true, paymentReady: false, adapterAvailable: true }), false);
});

test("one guarded invocation is the maximum across ambiguous outcome and reload", () => {
  let adapterCalls = 0;
  let saved = beginPayment(flow({ quoteId }));
  adapterCalls += 1;
  saved = paymentFailure(saved, "ambiguous", null);
  assert.equal(canPay({ flow: saved, quoteState: "PAYMENT_UNCERTAIN", connectedAccount: payer, onMezo: true, paymentReady: true, adapterAvailable: true }), false);
  assert.equal(recoveryRequest(saved).method, "GET");
  assert.equal(adapterCalls, 1);
});
