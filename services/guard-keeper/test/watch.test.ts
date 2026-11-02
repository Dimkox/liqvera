import assert from "node:assert/strict";
import { test } from "node:test";
import type { IncomingMessage, ServerResponse } from "node:http";
import { decodePaymentRequiredHeader, encodePaymentSignatureHeader } from "@x402/core/http";
import type { FacilitatorClient } from "@x402/core/server";
import { describeConfig, loadConfig, TESTNET_GUARD, TESTNET_GUARD_DEPLOY_BLOCK } from "../src/config.js";
import { DAY, GUARD_WATCH_PERIOD_SECONDS, GUARD_WATCH_PRICE, WatchLedger } from "../src/watch.js";
import { createWatchHandler, GuardWatchCheckout, NETWORK, planOf, type WatchHttpOptions } from "../src/watch-http.js";

const A = "0x00000000000000000000000000000000000000aa" as const;
const B = "0x00000000000000000000000000000000000000bb" as const;
const PAY_TO = "0x00000000000000000000000000000000000000cc" as const;
const MUSD = "0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503" as const;
const T0 = 1_800_000_000n;
const pay = (payer: `0x${string}`, amount: bigint, timestamp: bigint, blockNumber: bigint, logIndex = 0) => ({ payer, amount, timestamp, blockNumber, logIndex });

test("price is 2 MUSD per 30 days", () => {
  assert.equal(GUARD_WATCH_PRICE, 2_000_000_000_000_000_000n);
  assert.equal(GUARD_WATCH_PERIOD_SECONDS, 30n * DAY);
});

test("a 2 MUSD transfer activates 30 days; below-price transfers buy nothing", () => {
  const l = new WatchLedger({ enforce: true, freeTrial: false, trialDays: 30 });
  l.applyPayments([pay(A, 10n ** 16n, T0, 1n), pay(B, GUARD_WATCH_PRICE - 1n, T0, 2n)]);
  assert.equal(l.status(A, T0).active, false);
  assert.equal(l.status(B, T0).active, false);
  l.applyPayments([pay(A, GUARD_WATCH_PRICE, T0, 3n)]);
  const s = l.status(A, T0 + 1n);
  assert.equal(s.active, true);
  assert.equal(s.source, "paid");
  assert.equal(s.paidUntil, T0 + GUARD_WATCH_PERIOD_SECONDS);
  assert.equal(l.status(A, T0 + GUARD_WATCH_PERIOD_SECONDS).active, false, "expires exactly at the end");
});

test("payments stack, multiples buy multiple periods, and replays are idempotent", () => {
  const l = new WatchLedger({ enforce: true, freeTrial: false, trialDays: 30 });
  const first = pay(A, GUARD_WATCH_PRICE, T0, 10n);
  l.applyPayments([first, pay(A, 2n * GUARD_WATCH_PRICE + 1n, T0 + DAY, 11n)]);
  l.applyPayments([first]);
  assert.equal(l.status(A, T0).paidUntil, T0 + 3n * GUARD_WATCH_PERIOD_SECONDS);
  assert.equal(l.status(A, T0).payments, 2);
  // A payment after expiry starts fresh from its own timestamp.
  const late = T0 + 10n * GUARD_WATCH_PERIOD_SECONDS;
  l.applyPayments([pay(A, GUARD_WATCH_PRICE, late, 12n)]);
  assert.equal(l.status(A, late).paidUntil, late + GUARD_WATCH_PERIOD_SECONDS);
});

test("free trial starts at the first Armed event only and is off by default", () => {
  const off = new WatchLedger({ enforce: true, freeTrial: false, trialDays: 30 });
  off.noteArmed({ borrower: A, timestamp: T0 });
  assert.equal(off.status(A, T0).active, false);
  const on = new WatchLedger({ enforce: true, freeTrial: true, trialDays: 7 });
  on.noteArmed({ borrower: A, timestamp: T0 });
  on.noteArmed({ borrower: A, timestamp: T0 + 6n * DAY });
  assert.deepEqual([on.status(A, T0 + DAY).active, on.status(A, T0 + DAY).source], [true, "trial"]);
  assert.equal(on.status(A, T0 + 7n * DAY).active, false, "re-arming does not restart the trial");
  assert.equal(on.status(B, T0).active, false);
});

test("paid takes precedence over trial; enforcement off serves everyone", () => {
  const l = new WatchLedger({ enforce: true, freeTrial: true, trialDays: 7 });
  l.noteArmed({ borrower: A, timestamp: T0 });
  l.applyPayments([pay(A.toUpperCase().replace("0X", "0x") as `0x${string}`, GUARD_WATCH_PRICE, T0, 1n)]);
  assert.equal(l.status(A, T0 + DAY).source, "paid");
  const open = new WatchLedger({ enforce: false, freeTrial: false, trialDays: 7 });
  assert.equal(open.status(B, T0).source, "not-enforced");
});

test("partition keeps only subscribed Ready borrowers", () => {
  const l = new WatchLedger({ enforce: true, freeTrial: false, trialDays: 30 });
  l.applyPayments([pay(B, GUARD_WATCH_PRICE, T0, 1n)]);
  const { served, skipped } = l.partition([{ borrower: A, icr: 1n }, { borrower: B, icr: 2n }], T0 + 1n);
  assert.deepEqual(served.map((x) => x.borrower), [B]);
  assert.deepEqual(skipped.map((x) => x.borrower), [A]);
});

test("config defaults to the deployed testnet Guard in dry run with enforcement on", () => {
  const c = loadConfig({});
  assert.equal(c.chainId, 31611);
  assert.equal(c.guard, TESTNET_GUARD);
  assert.equal(c.fromBlock, TESTNET_GUARD_DEPLOY_BLOCK);
  assert.equal(c.dryRun, true);
  assert.equal(c.watchEnforce, true);
  assert.equal(c.freeTrial, false);
  assert.equal(c.watchPayTo, null);
});

test("config refuses other chains, live mode without a key, and never describes the key", () => {
  assert.throws(() => loadConfig({ CHAIN_ID: "31612" }), /only runs on Mezo Testnet/);
  assert.throws(() => loadConfig({ DRY_RUN: "0" }), /KEEPER_PRIVATE_KEY/);
  assert.throws(() => loadConfig({ DRY_RUN: "yes" }), /DRY_RUN/);
  assert.throws(() => loadConfig({ GUARD_ADDRESS: "0x123" }), /GUARD_ADDRESS/);
  const secret = "0x" + "11".repeat(32);
  const c = loadConfig({ DRY_RUN: "0", KEEPER_PRIVATE_KEY: secret, GUARD_WATCH_FREE_TRIAL: "1", GUARD_WATCH_PAY_TO: PAY_TO });
  assert.equal(c.dryRun, false);
  assert.equal(c.freeTrial, true);
  assert.ok(!JSON.stringify(describeConfig(c), (_k, v) => (typeof v === "bigint" ? v.toString() : v)).includes("11".repeat(32)));
});

// ---- HTTP + x402 checkout with an in-memory facilitator (no network) ----
function fakeFacilitator(payer: string) {
  const calls: string[] = [];
  const f: FacilitatorClient = {
    async getSupported() { return { kinds: [{ x402Version: 2, scheme: "exact", network: NETWORK }], extensions: ["eip2612GasSponsoring"], signers: {} }; },
    async verify() { calls.push("verify"); return { isValid: true, payer }; },
    async settle() { calls.push("settle"); return { success: true, transaction: "0x" + "ab".repeat(32), network: NETWORK, payer }; },
  } as FacilitatorClient;
  return { f, calls };
}
function opts(f: FacilitatorClient, payTo: `0x${string}` | null = PAY_TO): WatchHttpOptions {
  const ledger = new WatchLedger({ enforce: true, freeTrial: true, trialDays: 30 });
  ledger.noteArmed({ borrower: A, timestamp: BigInt(Math.floor(Date.now() / 1000)) });
  return {
    view: { status: (b) => ledger.status(b, BigInt(Math.floor(Date.now() / 1000))), guard: () => null, summary: () => ({}) },
    payTo, musd: MUSD, freeTrial: true, trialDays: 30, enforce: true, corsOrigin: "http://localhost:5173", facilitator: f,
  };
}
async function call(handler: ReturnType<typeof createWatchHandler>, url: string, headers: Record<string, string> = {}) {
  let status = 0, body = "", out: Record<string, string> = {};
  const res = { writeHead(s: number, h: Record<string, string>) { status = s; out = h; }, end(b?: string) { body = b ?? ""; } } as unknown as ServerResponse;
  await handler({ method: "GET", url, headers } as unknown as IncomingMessage, res);
  return { status, headers: out, json: body ? JSON.parse(body) : null };
}

test("plan advertises 2 MUSD / 30 days per Trove as a proposal", async () => {
  const { f } = fakeFacilitator(A);
  const o = opts(f);
  const r = await call(createWatchHandler(o, new GuardWatchCheckout(o)), "/v1/guard-watch/plan");
  assert.equal(r.status, 200);
  assert.equal(r.json.price_atomic, "2000000000000000000");
  assert.equal(r.json.period_days, 30);
  assert.equal(r.json.proposal, true);
  assert.equal(r.json.free_trial, true);
  assert.deepEqual(planOf(o).network, "eip155:31611");
});

test("trove status reports the trial subscription", async () => {
  const { f } = fakeFacilitator(A);
  const o = opts(f);
  const r = await call(createWatchHandler(o, new GuardWatchCheckout(o)), `/v1/guard-watch/troves/${A}`);
  assert.equal(r.status, 200);
  assert.equal(r.json.subscription.source, "trial");
  assert.equal(r.json.subscription.active, true);
});

test("subscribe without a merchant is disabled; with one it returns an exact Permit2 402 challenge for 2 MUSD", async () => {
  const { f } = fakeFacilitator(A);
  const off = opts(f, null), offCheckout = new GuardWatchCheckout(off);
  await offCheckout.initialize();
  assert.equal((await call(createWatchHandler(off, offCheckout), `/v1/guard-watch/troves/${A}/subscribe`)).status, 503);
  const o = opts(f), checkout = new GuardWatchCheckout(o);
  await checkout.initialize();
  const r = await call(createWatchHandler(o, checkout), `/v1/guard-watch/troves/${A}/subscribe`);
  assert.equal(r.status, 402);
  const required = decodePaymentRequiredHeader(r.headers["PAYMENT-REQUIRED"]!);
  assert.equal(required.accepts.length, 1);
  const a = required.accepts[0]!;
  assert.equal(a.scheme, "exact");
  assert.equal(a.network, "eip155:31611");
  assert.equal(a.amount, "2000000000000000000");
  assert.equal(a.payTo.toLowerCase(), PAY_TO);
  assert.equal(a.asset.toLowerCase(), MUSD.toLowerCase());
  assert.equal(a.extra?.assetTransferMethod, "permit2");
  assert.ok(required.extensions && "eip2612GasSponsoring" in required.extensions);
  assert.match(r.headers["access-control-expose-headers"] ?? "", /PAYMENT-REQUIRED/);
});

test("subscribe settles only when terms match and the payer is the borrower", async () => {
  for (const [payer, expected, settled] of [[A, 200, true], [B, 409, false]] as const) {
    const { f, calls } = fakeFacilitator(payer);
    const o = opts(f), checkout = new GuardWatchCheckout(o);
    await checkout.initialize();
    const handler = createWatchHandler(o, checkout);
    const challenge = decodePaymentRequiredHeader((await call(handler, `/v1/guard-watch/troves/${A}/subscribe`)).headers["PAYMENT-REQUIRED"]!);
    const header = encodePaymentSignatureHeader({ x402Version: 2, accepted: challenge.accepts[0]!, payload: { signature: "0x" }, resource: challenge.resource });
    const r = await call(handler, `/v1/guard-watch/troves/${A}/subscribe`, { "payment-signature": header });
    assert.equal(r.status, expected);
    assert.equal(calls.includes("settle"), settled);
    if (settled) assert.equal(r.json.tx, "0x" + "ab".repeat(32));
  }
});

test("subscribe rejects a payload for a different amount without settling", async () => {
  const { f, calls } = fakeFacilitator(A);
  const o = opts(f), checkout = new GuardWatchCheckout(o);
  await checkout.initialize();
  const handler = createWatchHandler(o, checkout);
  const challenge = decodePaymentRequiredHeader((await call(handler, `/v1/guard-watch/troves/${A}/subscribe`)).headers["PAYMENT-REQUIRED"]!);
  const header = encodePaymentSignatureHeader({ x402Version: 2, accepted: { ...challenge.accepts[0]!, amount: "10000000000000000" }, payload: {}, resource: challenge.resource });
  const r = await call(handler, `/v1/guard-watch/troves/${A}/subscribe`, { "payment-signature": header });
  assert.equal(r.status, 409);
  assert.deepEqual(calls, []);
});

test("unknown routes and bad addresses are 404", async () => {
  const { f } = fakeFacilitator(A);
  const o = opts(f);
  const h = createWatchHandler(o, new GuardWatchCheckout(o));
  assert.equal((await call(h, "/v1/guard-watch/troves/0x1234")).status, 404);
  assert.equal((await call(h, "/nope")).status, 404);
});

test("CORS allowlist echoes only listed origins", async () => {
  const { cors } = await import("../src/watch-http.js");
  assert.equal(cors(null, "http://a")["access-control-allow-origin"], undefined);
  assert.equal(cors("http://a", "http://evil")["access-control-allow-origin"], "http://a");
  assert.equal(cors("http://a, http://b", "http://b")["access-control-allow-origin"], "http://b");
  assert.equal(cors("http://a,http://b", "http://evil")["access-control-allow-origin"], undefined);
});
