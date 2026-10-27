import assert from "node:assert/strict";
import { test } from "node:test";
import { armedSet, isTerminal, logLine, nicr, projectedTrove, selectReady } from "../src/logic.js";

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
