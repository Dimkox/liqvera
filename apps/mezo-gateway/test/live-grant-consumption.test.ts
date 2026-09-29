import assert from 'node:assert/strict';
import test from 'node:test';
import { consumeLiveGrant } from '../src/adapters/postgres.js';

class TransactionalGrantStore {
  readonly digests = new Set<string>();
  readonly ids = new Set<string>();
  async query(_sql: string, params?: unknown[]) {
    const [digest, id] = params as string[];
    if (this.digests.has(digest!) || this.ids.has(id!)) return { rows: [], rowCount: 0 };
    this.digests.add(digest!); this.ids.add(id!);
    return { rows: [{ grant_digest: digest }], rowCount: 1 };
  }
}

test('durable grant consume admits one concurrent attempt and survives adapter restart', async () => {
  const store = new TransactionalGrantStore();
  const adapters = [{ query: store.query.bind(store) }, { query: store.query.bind(store) }];
  const outcomes = await Promise.all(adapters.map((db, index) =>
    consumeLiveGrant(db, 'a'.repeat(64), '00000000-0000-4000-8000-000000000013', `attempt-${index}`)));
  assert.deepEqual(outcomes.sort(), [false, true]);
  const restarted = { query: store.query.bind(store) };
  assert.equal(await consumeLiveGrant(restarted, 'a'.repeat(64), '00000000-0000-4000-8000-000000000013', 'attempt-restart'), false);
  assert.equal(await consumeLiveGrant(restarted, 'b'.repeat(64), '00000000-0000-4000-8000-000000000013', 'attempt-other-digest'), false);
});
