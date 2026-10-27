// Pure keeper logic. No I/O here, so it is unit-tested without an RPC.

export type Address = `0x${string}`;

/** Mirrors LiqveraGuard.Status. */
export const STATUS = [
  "Ready", "NoPolicy", "Expired", "StaleNonce", "TroveNotActive", "Healthy", "BelowMinNetDebt", "StillBelowMCR",
] as const;
export type StatusName = (typeof STATUS)[number];

export interface ArmLog { kind: "Armed" | "Disarmed" | "Protected"; user: Address; blockNumber: bigint; logIndex: number }

/** Replay Armed / Disarmed / Protected logs (any order) into the set of currently armed borrowers. */
export function armedSet(logs: ArmLog[]): Set<Address> {
  const sorted = [...logs].sort((a, b) =>
    a.blockNumber === b.blockNumber ? a.logIndex - b.logIndex : a.blockNumber < b.blockNumber ? -1 : 1);
  const out = new Set<Address>();
  for (const l of sorted) {
    const u = l.user.toLowerCase() as Address;
    if (l.kind === "Armed") out.add(u); else out.delete(u);
  }
  return out;
}

export interface StatusRead { borrower: Address; status: number; icr: bigint }

/** Pick borrowers that the Guard reports Ready, lowest ICR first (most urgent first). */
export function selectReady(reads: StatusRead[]): StatusRead[] {
  return reads.filter((r) => r.status === 0).sort((a, b) => (a.icr < b.icr ? -1 : a.icr > b.icr ? 1 : 0));
}

/** Statuses after which the borrower will never become Ready without a new arm(). The keeper stops polling them. */
export function isTerminal(status: number): boolean {
  const n = STATUS[status];
  return n === "NoPolicy" || n === "Expired" || n === "StaleNonce";
}

/** Mezo nominal ICR used for sorted-list hints: coll * 1e20 / principal. */
export function nicr(coll: bigint, principal: bigint): bigint {
  if (principal === 0n) return 2n ** 256n - 1n;
  return (coll * 10n ** 20n) / principal;
}

/** Trove state after the policy executes, for hint computation. */
export function projectedTrove(action: 1 | 2, amount: bigint, coll: bigint, principal: bigint, interest: bigint): { coll: bigint; principal: bigint } {
  if (action === 2) return { coll: coll + amount, principal };
  // Mezo repays interest first, then principal.
  const toPrincipal = amount > interest ? amount - interest : 0n;
  return { coll, principal: principal - toPrincipal };
}

export function logLine(event: string, fields: Record<string, unknown>): string {
  return JSON.stringify({ ts: new Date().toISOString(), event, ...fields }, (_k, v) => (typeof v === "bigint" ? v.toString() : v));
}
