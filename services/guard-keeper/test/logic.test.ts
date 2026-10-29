import assert from "node:assert/strict";
import { test } from "node:test";
import { type Address, armedSet, isTerminal, logLine, nicr, PolicyTracker, pollStatuses, projectedTrove, selectReady } from "../src/logic.js";

const A = "0x00000000000000000000000000000000000000aa" as const;
const B = "0x00000000000000000000000000000000000000bb" as const;

test("armedSet replays logs in chain order", () => {
  const s = armedSet([
    { kind: "Disarmed", user: A, blockNumber: 5n, logIndex: 0 },
    { kind: "Armed", user: A, blockNumber: 3n, logIndex: 1 },
    { kind: "Armed", user: B, blockNumber: 4n, logIndex: 0 },
    { kind: "Protected", user: B, blockNumber: 4n, logIndex: 2 },
    { kind: "Armed", user: B, blockNumber: 6n, logIndex: 0 },
  ]);
  assert.deepEqual([...s], [B]);
});

test("selectReady keeps only Ready and sorts by ICR ascending", () => {
  const out = selectReady([
    { borrower: A, status: 0, icr: 1_200_000_000_000_000_000n },
    { borrower: B, status: 0, icr: 1_150_000_000_000_000_000n },
    { borrower: A, status: 5, icr: 1_000_000_000_000_000_000n },
  ]);
  assert.deepEqual(out.map((r) => r.borrower), [B, A]);
});

test("isTerminal", () => {
  assert.equal(isTerminal(1), true); // NoPolicy
  assert.equal(isTerminal(3), true); // StaleNonce
  assert.equal(isTerminal(5), false); // Healthy
  assert.equal(isTerminal(0), false); // Ready
});

test("isTerminal covers Expired and StaleNonce but not transient states", () => {
  assert.equal(isTerminal(2), true); // Expired
  assert.equal(isTerminal(4), false); // TroveNotActive: a Trove can be reopened with the same nonce
  assert.equal(isTerminal(6), false); // BelowMinNetDebt: debt can grow again
  assert.equal(isTerminal(7), false); // StillBelowMCR: price can recover
});

test("PolicyTracker stops polling terminal policies until a newer Armed event", () => {
  const t = new PolicyTracker();
  t.apply([
    { kind: "Armed", user: A, blockNumber: 1n, logIndex: 0 },
    { kind: "Armed", user: B, blockNumber: 2n, logIndex: 0 },
  ]);
  assert.deepEqual(t.pollable().sort(), [A, B]);

  // A expired, B had its nonce invalidated. Neither called disarm(): last event is still Armed.
  t.markTerminal(A);
  t.markTerminal(B.toUpperCase().replace("0X", "0x") as typeof B);
  assert.deepEqual(t.pollable(), []);
  assert.equal(t.armedCount, 2);
  assert.equal(t.terminalCount, 2);

  // Later ticks with unrelated or no logs must not bring them back (no full-history replay).
  t.apply([]);
  t.apply([{ kind: "Disarmed", user: "0x00000000000000000000000000000000000000cc", blockNumber: 3n, logIndex: 0 }]);
  assert.deepEqual(t.pollable(), []);

  // A re-arms: polled again. B stays excluded.
  t.apply([{ kind: "Armed", user: A, blockNumber: 4n, logIndex: 1 }]);
  assert.deepEqual(t.pollable(), [A]);
  assert.equal(t.isTerminal(A), false);
  assert.equal(t.isTerminal(B), true);

  // B disarms: it leaves both sets; a later Armed makes it pollable.
  t.apply([{ kind: "Disarmed", user: B, blockNumber: 5n, logIndex: 0 }]);
  assert.equal(t.terminalCount, 0);
  assert.deepEqual(t.pollable(), [A]);
  t.apply([{ kind: "Armed", user: B, blockNumber: 6n, logIndex: 0 }]);
  assert.deepEqual(t.pollable().sort(), [A, B]);
});

test("PolicyTracker ignores terminal marks for borrowers that are not armed", () => {
  const t = new PolicyTracker();
  t.markTerminal(A);
  assert.equal(t.terminalCount, 0);
  t.apply([{ kind: "Armed", user: A, blockNumber: 1n, logIndex: 0 }]);
  assert.deepEqual(t.pollable(), [A]);
});

test("PolicyTracker applies a batch in chain order and matches armedSet", () => {
  const logs = [
    { kind: "Protected" as const, user: A, blockNumber: 7n, logIndex: 3 },
    { kind: "Armed" as const, user: A, blockNumber: 7n, logIndex: 1 },
    { kind: "Armed" as const, user: B, blockNumber: 8n, logIndex: 0 },
  ];
  const t = new PolicyTracker();
  t.apply(logs);
  assert.deepEqual(t.pollable(), [...armedSet(logs)]);
  assert.deepEqual(t.pollable(), [B]);
});

test("PolicyTracker treats addresses case-insensitively across events", () => {
  const mixed: Address = "0x00000000000000000000000000000000000000Ab";
  const t = new PolicyTracker();
  t.apply([{ kind: "Armed", user: mixed, blockNumber: 1n, logIndex: 0 }]);
  assert.deepEqual(t.pollable(), [mixed.toLowerCase()]);
  t.apply([{ kind: "Disarmed", user: mixed.toLowerCase() as Address, blockNumber: 2n, logIndex: 0 }]);
  assert.equal(t.armedCount, 0);
});

test("pollStatuses marks terminal borrowers so later ticks skip them", async () => {
  const t = new PolicyTracker();
  t.apply([
    { kind: "Armed", user: A, blockNumber: 1n, logIndex: 0 },
    { kind: "Armed", user: B, blockNumber: 1n, logIndex: 1 },
  ]);
  const statusOf: Record<string, number> = { [A]: 0, [B]: 2 }; // B: Expired (terminal)
  const seen: string[] = [];
  const read = async (b: Address) => { seen.push(b); return [statusOf[b] ?? 5, 105n] as const; };
  const first = await pollStatuses(t, read);
  assert.deepEqual(first.map((r) => [r.borrower, r.status]), [[A, 0], [B, 2]]);
  assert.equal(t.isTerminal(B), true);
  const second = await pollStatuses(t, read);
  assert.deepEqual(second.map((r) => r.borrower), [A]);
  assert.deepEqual(seen, [A, B, A]);
  // A transient status (TroveNotActive) is never marked terminal.
  statusOf[A] = 4;
  await pollStatuses(t, read);
  assert.equal(t.isTerminal(A), false);
});

test("nicr and projection follow Mezo rules", () => {
  assert.equal(nicr(2n * 10n ** 18n, 10n ** 20n), 2n * 10n ** 18n);
  assert.deepEqual(projectedTrove(1, 150n, 10n, 1000n, 50n), { coll: 10n, principal: 900n });
  assert.deepEqual(projectedTrove(1, 30n, 10n, 1000n, 50n), { coll: 10n, principal: 1000n });
  assert.deepEqual(projectedTrove(2, 5n, 10n, 1000n, 50n), { coll: 15n, principal: 1000n });
});

test("logLine is one JSON line and serialises bigint", () => {
  const o = JSON.parse(logLine("x", { v: 1n }));
  assert.equal(o.event, "x");
  assert.equal(o.v, "1");
});
