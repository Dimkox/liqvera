import assert from "node:assert/strict";
import test from "node:test";
import { bindWalletStateListeners, createWalletListenerOwner, refreshWalletState } from "../src/wallet-events.ts";

const payer = "0x1111111111111111111111111111111111111111";
const tick = () => new Promise(resolve => setImmediate(resolve));
function provider(accounts) {
  const listeners = new Map();
  return {
    listeners,
    async request({ method }) { return method === "eth_accounts" ? accounts() : "0x7b7b"; },
    on(event, listener) { listeners.set(event, listener); },
    removeListener(event) { listeners.delete(event); },
  };
}

for (const fails of [false, true]) {
  test(`replaced wallet cannot erase the active account with a delayed ${fails ? "error" : "response"}`, async () => {
    let settle;
    const pending = new Promise((resolve, reject) => { settle = fails ? reject : resolve; });
    const old = provider(() => pending);
    const current = provider(() => [payer]);
    const states = [];
    const sink = { applyWalletState(state) { states.push(state); } };
    const owner = createWalletListenerOwner(sink);
    owner.replace(old);
    old.listeners.get("accountsChanged")([]);
    await tick();
    owner.replace(current);
    await refreshWalletState(current, sink);
    settle(fails ? new Error("Previous wallet disconnected") : []);
    await tick();
    assert.deepEqual(states, [{ account: payer, onMezo: true }]);
    owner.dispose();
  });
}

test("unbinding discards queued wallet refreshes before they call the provider", async () => {
  let calls = 0;
  const wallet = provider(() => { calls++; return []; });
  const states = [];
  const unbind = bindWalletStateListeners(wallet, { applyWalletState(state) { states.push(state); } });
  wallet.listeners.get("accountsChanged")([]);
  unbind();
  await tick();
  assert.equal(calls, 0);
  assert.deepEqual(states, []);
});
