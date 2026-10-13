import assert from "node:assert/strict";
import test from "node:test";
import { createWalletModal } from "../src/wallet-modal.ts";

test("modal restores a provider, follows replacement and clears disconnected sessions without signing", async () => {
  const old = { request() { throw new Error("Connection must not sign"); } };
  const next = { request() { throw new Error("Connection must not sign"); } };
  let notify;
  let loads = 0;
  const states = [];
  const modal = createWalletModal(async () => {
    loads++;
    return {
      subscribeProviders(callback) { notify = callback; return () => {}; },
      getWalletProvider() { return old; },
      async open() {},
    };
  }, provider => states.push(provider));
  await Promise.all([modal.restore(), modal.open()]);
  assert.equal(loads, 1);
  assert.deepEqual(states, [old]);
  notify({ eip155: next });
  notify({});
  assert.deepEqual(states, [old, next, null]);
});

test("a failed SDK load can be retried without losing the saved report", async () => {
  let attempts = 0;
  const modal = createWalletModal(async () => {
    if (++attempts === 1) throw new Error("Network unavailable");
    return { subscribeProviders() { return () => {}; }, getWalletProvider() {}, async open() {} };
  }, () => {});
  await assert.rejects(modal.open(), /Network unavailable/);
  await modal.open();
  assert.equal(attempts, 2);
});

test("network selection uses the same initialized SDK session and propagates refusal", async () => {
  const rejection = new Error("Wallet refused the network switch");
  let switched = 0;
  const modal = createWalletModal(async () => ({
    subscribeProviders() { return () => {}; }, getWalletProvider() {}, async open() {},
    async switchNetwork() { switched++; throw rejection; },
  }), () => {});
  await assert.rejects(modal.switchNetwork(), error => error === rejection);
  assert.equal(switched, 1);
});
