// Guard Watch subscription ledger (proposal: 2 MUSD per Trove per 30 days). Pure, no I/O.
//
// Source of truth is the chain: a subscription payment is an MUSD Transfer from the borrower to the
// Guard Watch merchant. The x402 exact/Permit2 flow settles exactly such a Transfer, so whatever
// relayed the payment, the keeper recognises it from canonical logs. Each full 2 MUSD buys 30 days;
// payments made while a subscription is active extend it (stacking). Transfers below the price
// (for example 0.01 MUSD report purchases to the same merchant) buy nothing.
import type { Address } from "./logic.js";

export const GUARD_WATCH_PRICE = 2n * 10n ** 18n;
export const GUARD_WATCH_PERIOD_SECONDS = 30n * 24n * 3600n;
export const DAY = 86_400n;

export interface WatchPayment { payer: Address; amount: bigint; timestamp: bigint; blockNumber: bigint; logIndex: number; tx?: string }
export interface WatchTrial { borrower: Address; timestamp: bigint }
export type WatchSource = "paid" | "trial" | "none" | "not-enforced";
export interface WatchStatus { active: boolean; source: WatchSource; paidUntil: bigint | null; trialUntil: bigint | null; payments: number }

const order = (a: WatchPayment, b: WatchPayment): number =>
  a.blockNumber === b.blockNumber ? a.logIndex - b.logIndex : a.blockNumber < b.blockNumber ? -1 : 1;

export class WatchLedger {
  private readonly paid = new Map<Address, bigint>();
  private readonly count = new Map<Address, number>();
  private readonly trialStart = new Map<Address, bigint>();
  private readonly seen = new Set<string>();

  constructor(private readonly opts: { enforce: boolean; freeTrial: boolean; trialDays: number }) {}

  /** Apply payments once each (idempotent on blockNumber:logIndex), in chain order. */
  applyPayments(payments: WatchPayment[]): void {
    for (const p of [...payments].sort(order)) {
      const key = `${p.blockNumber}:${p.logIndex}`;
      if (this.seen.has(key)) continue;
      this.seen.add(key);
      const units = p.amount / GUARD_WATCH_PRICE;
      if (units === 0n) continue;
      const u = p.payer.toLowerCase() as Address;
      const current = this.paid.get(u) ?? 0n;
      const start = current > p.timestamp ? current : p.timestamp;
      this.paid.set(u, start + units * GUARD_WATCH_PERIOD_SECONDS);
      this.count.set(u, (this.count.get(u) ?? 0) + 1);
    }
  }

  /** First Armed event starts the (testnet-only) free trial. Later re-arms do not restart it. */
  noteArmed(t: WatchTrial): void {
    const u = t.borrower.toLowerCase() as Address;
    const prev = this.trialStart.get(u);
    if (prev === undefined || t.timestamp < prev) this.trialStart.set(u, t.timestamp);
  }

  status(borrower: Address, now: bigint): WatchStatus {
    const u = borrower.toLowerCase() as Address;
    const paidUntil = this.paid.get(u) ?? null;
    const start = this.trialStart.get(u);
    const trialUntil = this.opts.freeTrial && start !== undefined ? start + BigInt(this.opts.trialDays) * DAY : null;
    const payments = this.count.get(u) ?? 0;
    if (!this.opts.enforce) return { active: true, source: "not-enforced", paidUntil, trialUntil, payments };
    if (paidUntil !== null && paidUntil > now) return { active: true, source: "paid", paidUntil, trialUntil, payments };
    if (trialUntil !== null && trialUntil > now) return { active: true, source: "trial", paidUntil, trialUntil, payments };
    return { active: false, source: "none", paidUntil, trialUntil, payments };
  }

  /** Split candidate borrowers into served (active subscription) and skipped. */
  partition<T extends { borrower: Address }>(items: T[], now: bigint): { served: T[]; skipped: T[] } {
    const served: T[] = [], skipped: T[] = [];
    for (const i of items) (this.status(i.borrower, now).active ? served : skipped).push(i);
    return { served, skipped };
  }
}
