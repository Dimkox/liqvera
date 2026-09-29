import assert from "node:assert/strict";
import test from "node:test";

import { bindWalletListeners, executePaymentAttempt, executeRecovery } from "../src/browser-orchestration.ts";

const payer = "0x1111111111111111111111111111111111111111";
const quoteId = "11111111-1111-4111-8111-111111111111";
const requestId = "22222222-2222-4222-8222-222222222222";
const key = "33333333-3333-4333-8333-333333333333";
const reportId = "44444444-4444-4444-8444-444444444444";

const baseFlow = { version: 1, side: "BUY", quantity: "0.15", payer, idempotencyKey: key, quoteId, paymentGuard: "clear" };
const ready = { quote_id: quoteId, report_id: reportId, state: "READY" };

function harness() {
  const trace = [];
  const saved = [];
  const notices = [];
  return {
    trace, saved, notices,
    persist(flow) { saved.push(structuredClone(flow)); trace.push(["persist", flow.paymentGuard]); },
    notice(message) { notices.push(message); trace.push(["notice", message]); },
  };
}

test("production recovery orchestration performs GET-only reload and paid reuse", async () => {
  const h = harness();
  let adapterCalls = 0;
  const result = await executeRecovery({ ...baseFlow, paymentGuard: "uncertain" }, {
    async getQuote(id) { h.trace.push(["GET quote", id]); return { ...ready, state: "PAID" }; },
    async getRequest() { throw new Error("unexpected request GET"); },
    async createQuote() { throw new Error("unexpected quote POST"); },
    async getPaidDelivery(id) { h.trace.push(["GET delivery", id]); return { schema: "delivery" }; },
    onQuote(quote) { h.trace.push(["render quote", quote.state]); },
    onRequest() { throw new Error("unexpected request render"); },
    onDelivery() { h.trace.push(["render delivery"]); },
    notice: h.notice,
  });
  assert.equal(result.kind, "quote");
  assert.equal(adapterCalls, 0);
  assert.deepEqual(h.trace.map(item => item[0]), ["GET quote", "render quote", "GET delivery", "render delivery", "notice"]);
});

test("lost create response replays exact body and idempotency key", async () => {
  const h = harness();
  const flow = { ...baseFlow };
  delete flow.quoteId;
  await executeRecovery(flow, {
    async getQuote() { throw new Error("unexpected quote GET"); },
    async getRequest() { throw new Error("unexpected request GET"); },
    async createQuote(input) { h.trace.push(["POST quote", input]); return { schema: "quote", quote_id: quoteId, state: "READY" }; },
    async getPaidDelivery() { throw new Error("unexpected delivery GET"); },
    onQuote(quote) { h.trace.push(["render quote", quote.state]); },
    onRequest() { throw new Error("unexpected request render"); },
    onDelivery() { throw new Error("unexpected delivery render"); },
    notice: h.notice,
  });
  assert.deepEqual(h.trace[0], ["POST quote", { side: "BUY", quantity: "0.15", payer, idempotencyKey: key }]);
});

test("recovering adapter outcome persists uncertain before visible notice and cannot clear", async () => {
  const h = harness();
  let adapterCalls = 0;
  const result = await executePaymentAttempt(baseFlow, ready, {
    async validateWallet() { h.trace.push(["wallet valid"]); },
    async requestPaidReport() { adapterCalls++; h.trace.push(["adapter"]); return "recovering"; },
    async refreshQuote() { throw new Error("recovering must not refresh as success"); },
    isPreSubmitCancellation() { return false; },
    persist: h.persist,
    notice: h.notice,
  });
  assert.equal(result.paymentGuard, "uncertain");
  assert.equal(adapterCalls, 1);
  assert.deepEqual(h.trace.map(item => item[0]), ["wallet valid", "persist", "notice", "adapter", "persist", "notice"]);
  assert.match(h.notices.at(-1), /Do not pay again/);
});

test("typed cancel clears only after authoritative READY refresh", async () => {
  for (const latest of [ready, null]) {
    const h = harness();
    const cancelled = new Error("cancelled");
    const result = await executePaymentAttempt(baseFlow, ready, {
      async validateWallet() {},
      async requestPaidReport() { throw cancelled; },
      async refreshQuote() { h.trace.push(["GET quote"]); return latest; },
      isPreSubmitCancellation(error) { return error === cancelled; },
      persist: h.persist,
      notice: h.notice,
    });
    assert.equal(result.paymentGuard, latest ? "clear" : "uncertain");
    assert.equal(h.trace.filter(item => item[0] === "GET quote").length, 1);
  }
});

test("wallet events refresh state only and never call the adapter", async () => {
  const listeners = new Map();
  const provider = {
    on(event, listener) { listeners.set(event, listener); },
    removeListener(event) { listeners.delete(event); },
  };
  let refreshes = 0;
  let adapterCalls = 0;
  const cleanup = bindWalletListeners(provider, async () => { refreshes++; });
  await listeners.get("accountsChanged")([payer]);
  await listeners.get("chainChanged")("0x1");
  assert.equal(refreshes, 2);
  assert.equal(adapterCalls, 0);
  cleanup();
  assert.equal(listeners.size, 0);
});
