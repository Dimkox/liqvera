// Pure keeper logic. No I/O here, so it is unit-tested without an RPC.

export type Address = `0x${string}`;

/** Mirrors LiqveraGuard.Status. */
export const STATUS = [
  "Ready", "NoPolicy", "Expired", "StaleNonce", "TroveNotActive", "Healthy", "BelowMinNetDebt", "StillBelowMCR",
] as const;
export type StatusName = (typeof STATUS)[number];

export interface ArmLog { kind: "Armed" | "Disarmed" | "Protected"; user: Address; blockNumber: bigint; logIndex: number }

const sortLogs = (logs: ArmLog[]): ArmLog[] =>
  [...logs].sort((a, b) =>
    a.blockNumber === b.blockNumber ? a.logIndex - b.logIndex : a.blockNumber < b.blockNumber ? -1 : 1);

/** Replay Armed / Disarmed / Protected logs (any order) into the set of currently armed borrowers. */
export function armedSet(logs: ArmLog[]): Set<Address> {
  const out = new Set<Address>();
  for (const l of sortLogs(logs)) {
    const u = l.user.toLowerCase() as Address;
    if (l.kind === "Armed") out.add(u); else out.delete(u);
  }
  return out;
}

/**
 * Incremental view of Guard policies for the keeper.
 *
 * `apply()` consumes new Armed / Disarmed / Protected logs once (no full-history replay per tick).
 * `markTerminal()` records that the borrower's CURRENT policy can never become Ready again
 * (Expired, StaleNonce, NoPolicy). Terminal borrowers are excluded from `pollable()` until a
 * newer Armed event arrives, so expired or nonce-invalidated policies stop costing RPC reads.
 */
export class PolicyTracker {
  private readonly armed = new Map<Address, string>();
  private readonly terminal = new Set<Address>();

  apply(logs: ArmLog[]): void {
    for (const l of sortLogs(logs)) {
      const u = l.user.toLowerCase() as Address;
      // A newer Armed event replaces the policy, so it also clears any terminal mark.
      this.terminal.delete(u);
      if (l.kind === "Armed") this.armed.set(u, `${l.blockNumber}:${l.logIndex}`);
      else this.armed.delete(u);
    }
  }

  /** Stop polling `borrower` until its next Armed event. No-op for borrowers that are not armed. */
  markTerminal(borrower: Address): void {
    const u = borrower.toLowerCase() as Address;
    if (this.armed.has(u)) this.terminal.add(u);
  }

  isTerminal(borrower: Address): boolean {
    return this.terminal.has(borrower.toLowerCase() as Address);
  }

  /** Armed borrowers whose current policy is not known to be terminal. */
  pollable(): Address[] {
    return [...this.armed.keys()].filter((u) => !this.terminal.has(u));
  }

  get armedCount(): number { return this.armed.size; }
  get terminalCount(): number { return this.terminal.size; }
}

export interface StatusRead { borrower: Address; status: number; icr: bigint }

/**
 * Read the status of every pollable borrower and mark terminal ones in `tracker`.
 * `read` must read at (or after) the block the tracker was synced to, so a terminal mark
 * never predates an Armed event the tracker has not seen yet.
 */
export async function pollStatuses(
  tracker: PolicyTracker,
  read: (borrower: Address) => Promise<readonly [number, bigint]>,
): Promise<StatusRead[]> {
  const reads: StatusRead[] = [];
  for (const borrower of tracker.pollable()) {
    const [status, icr] = await read(borrower);
    if (isTerminal(status)) tracker.markTerminal(borrower);
    reads.push({ borrower, status, icr });
  }
  return reads;
}

/** Pick borrowers that the Guard reports Ready, lowest ICR first (most urgent first). */
export function selectReady(reads: StatusRead[]): StatusRead[] {
  return reads.filter((r) => r.status === 0).sort((a, b) => (a.icr < b.icr ? -1 : a.icr > b.icr ? 1 : 0));
}

/** Statuses after which the borrower will never become Ready without a new arm(). See PolicyTracker. */
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
