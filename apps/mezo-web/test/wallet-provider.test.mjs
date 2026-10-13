import assert from 'node:assert/strict';
import test from 'node:test';
import { injectedWallet } from '../src/wallet.ts';

test('Trust Wallet in-app provider is discovered without window.ethereum', t => {
  const previous = globalThis.window;
  t.after(() => { if (previous === undefined) delete globalThis.window; else globalThis.window = previous; });
  const provider = { request: async () => [] };
  globalThis.window = { trustwallet: { ethereum: provider } };
  assert.equal(injectedWallet(), provider);
});

test('ordinary browsers have no provider; existing injected wallets remain supported', t => {
  const previous = globalThis.window;
  t.after(() => { if (previous === undefined) delete globalThis.window; else globalThis.window = previous; });
  globalThis.window = {};
  assert.equal(injectedWallet(), null);
  const provider = { request: async () => [] };
  globalThis.window = { ethereum: provider };
  assert.equal(injectedWallet(), provider);
});
