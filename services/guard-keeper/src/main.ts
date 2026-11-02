// Liqvera Guard keeper. Testnet only (chain 31611 is enforced at startup).
// It holds only its own hot key (KEEPER_PRIVATE_KEY, from env, never logged) and only when DRY_RUN=0.
// It never holds user keys: users sign Mezo EIP-712 messages in their own wallet and the Guard stores them.
// Guard Watch: only Troves with an active subscription (paid on chain, or the testnet free trial) are served.
import { createPublicClient, createWalletClient, defineChain, http, parseAbiItem, type Hex } from "viem";
import { privateKeyToAccount } from "viem/accounts";
import { HTTPFacilitatorClient } from "@x402/core/server";
import { guardAbi, hintHelpersAbi, sortedTrovesAbi, troveManagerAbi } from "./abi.js";
import { describeConfig, loadConfig } from "./config.js";
import { type Address, type ArmLog, isTerminal, logLine, nicr, PolicyTracker, pollStatuses, projectedTrove, selectReady, STATUS } from "./logic.js";
import { WatchLedger, type WatchPayment } from "./watch.js";
import { GuardWatchCheckout, startWatchServer, type WatchView } from "./watch-http.js";

const cfg = loadConfig(process.env);
const LOG_CHUNK = 10_000n;
const log = (e: string, f: Record<string, unknown> = {}) => console.log(logLine(e, f));

const chain = defineChain({
  id: cfg.chainId, name: "Mezo Testnet", nativeCurrency: { name: "Bitcoin", symbol: "BTC", decimals: 18 },
  rpcUrls: { default: { http: [cfg.rpcUrl] } },
});
const pub = createPublicClient({ chain, transport: http(cfg.rpcUrl, { retryCount: 3 }) });
const account = cfg.dryRun ? undefined : privateKeyToAccount(process.env.KEEPER_PRIVATE_KEY as Hex);
const wallet = account ? createWalletClient({ chain, account, transport: http(cfg.rpcUrl) }) : undefined;
const transferEvent = parseAbiItem("event Transfer(address indexed from, address indexed to, uint256 value)");

let scanned = cfg.fromBlock - 1n;
const policies = new PolicyTracker();
const ledger = new WatchLedger({ enforce: cfg.watchEnforce, freeTrial: cfg.freeTrial, trialDays: cfg.trialDays });
const lastStatus = new Map<Address, { status: string; icr: string; checkedAt: string }>();
let lastTick: { at: string; head: string; armed: number; ready: number; served: number; skippedUnsubscribed: number } | null = null;
const blockTimes = new Map<bigint, bigint>();

async function blockTime(n: bigint): Promise<bigint> {
  const hit = blockTimes.get(n);
  if (hit !== undefined) return hit;
  const b = await pub.getBlock({ blockNumber: n });
  blockTimes.set(n, b.timestamp);
  return b.timestamp;
}

/** Apply new Guard and Guard Watch payment logs up to the current head and return that head. */
async function syncLogs(): Promise<bigint> {
  const head = await pub.getBlockNumber();
  while (scanned < head) {
    const from = scanned + 1n;
    const to = from + LOG_CHUNK - 1n < head ? from + LOG_CHUNK - 1n : head;
    const logs = await pub.getContractEvents({ address: cfg.guard, abi: guardAbi, fromBlock: from, toBlock: to });
    const batch: ArmLog[] = [];
    for (const l of logs) {
      if (l.eventName !== "Armed" && l.eventName !== "Disarmed" && l.eventName !== "Protected") continue;
      const user = (l.args as { user: Address }).user;
      batch.push({ kind: l.eventName, user, blockNumber: l.blockNumber, logIndex: l.logIndex });
      if (l.eventName === "Armed") {
        ledger.noteArmed({ borrower: user, timestamp: await blockTime(l.blockNumber) });
        log("armed_seen", { borrower: user, block: l.blockNumber, tx: l.transactionHash });
      }
    }
    policies.apply(batch);
    if (cfg.watchPayTo) {
      const transfers = await pub.getLogs({ address: cfg.musd, event: transferEvent, args: { to: cfg.watchPayTo }, fromBlock: from, toBlock: to });
      const payments: WatchPayment[] = [];
      for (const t of transfers) {
        payments.push({ payer: t.args.from as Address, amount: t.args.value ?? 0n, timestamp: await blockTime(t.blockNumber),
          blockNumber: t.blockNumber, logIndex: t.logIndex, tx: t.transactionHash });
      }
      ledger.applyPayments(payments);
    }
    scanned = to;
  }
  return scanned;
}

async function hintsFor(borrower: Address): Promise<[Address, Address]> {
  const p = await pub.readContract({ address: cfg.guard, abi: guardAbi, functionName: "policyOf", args: [borrower] });
  const [coll, principal, interest] = await pub.readContract({ address: cfg.troveManager, abi: troveManagerAbi, functionName: "getEntireDebtAndColl", args: [borrower] });
  const next = projectedTrove(p.action as 1 | 2, p.amount, coll, principal, interest);
  const target = nicr(next.coll, next.principal);
  const [approx] = await pub.readContract({ address: cfg.hintHelpers, abi: hintHelpersAbi, functionName: "getApproxHint", args: [target, 15n, BigInt(Date.now())] });
  const [upper, lower] = await pub.readContract({ address: cfg.sortedTroves, abi: sortedTrovesAbi, functionName: "findInsertPosition", args: [target, approx, approx] });
  return [upper, lower];
}

async function tick(): Promise<void> {
  const head = await syncLogs();
  const now = await blockTime(head);
  const reads = await pollStatuses(policies, async (b) => {
    // Read at the synced head so a terminal mark never predates an Armed event we have not seen.
    const [s, icr] = await pub.readContract({ address: cfg.guard, abi: guardAbi, functionName: "status", args: [b], blockNumber: head });
    lastStatus.set(b.toLowerCase() as Address, { status: STATUS[s] ?? String(s), icr: icr.toString(), checkedAt: new Date().toISOString() });
    if (s !== 0) log("skip", { borrower: b, status: STATUS[s] ?? s, icr, terminal: isTerminal(s) });
    return [s, icr] as const;
  });
  const ready = selectReady(reads);
  const { served, skipped } = ledger.partition(ready, now);
  for (const r of skipped) log("skip_unsubscribed", { borrower: r.borrower, icr: r.icr, subscription: ledger.status(r.borrower, now) });
  for (const r of served) {
    try {
      const [upper, lower] = await hintsFor(r.borrower);
      // Simulate first: a front-run or a stale nonce reverts here and costs no gas.
      const { request } = await pub.simulateContract({
        address: cfg.guard, abi: guardAbi, functionName: "protect", args: [r.borrower, upper, lower], account: account?.address,
      });
      if (!wallet) { log("dry_run_ready", { borrower: r.borrower, icr: r.icr, upper, lower, subscription: ledger.status(r.borrower, now).source }); continue; }
      const hash = await wallet.writeContract(request);
      const rcpt = await pub.waitForTransactionReceipt({ hash });
      log("protected", { borrower: r.borrower, icrBefore: r.icr, tx: hash, status: rcpt.status, gasUsed: rcpt.gasUsed });
    } catch (err) {
      log("protect_failed", { borrower: r.borrower, error: (err as Error).message.split("\n")[0] });
    }
  }
  lastTick = { at: new Date().toISOString(), head: head.toString(), armed: policies.armedCount, ready: ready.length, served: served.length, skippedUnsubscribed: skipped.length };
  log("tick", lastTick);
}

const view: WatchView = {
  status: (b) => ledger.status(b, BigInt(Math.floor(Date.now() / 1000))),
  guard: (b) => {
    const armed = policies.pollable().includes(b) || policies.isTerminal(b);
    const s = lastStatus.get(b);
    return armed || s ? { armed, terminal: policies.isTerminal(b), ...(s ?? {}) } : null;
  },
  summary: () => ({ guard: cfg.guard, chainId: cfg.chainId, dryRun: cfg.dryRun, scannedTo: scanned.toString(), lastTick }),
};

async function main(): Promise<void> {
  const rpcChain = await pub.getChainId();
  if (rpcChain !== cfg.chainId) throw new Error(`RPC chain id ${rpcChain} is not ${cfg.chainId}`);
  log("start", { ...describeConfig(cfg), keeper: account?.address ?? "dry-run (no key)" });
  if (cfg.httpPort) {
    const opts = { view, payTo: cfg.watchPayTo, musd: cfg.musd, freeTrial: cfg.freeTrial, trialDays: cfg.trialDays, enforce: cfg.watchEnforce,
      corsOrigin: cfg.corsOrigin, facilitator: new HTTPFacilitatorClient({ url: cfg.facilitatorUrl }), publicBase: `http://${cfg.httpHost}:${cfg.httpPort}` };
    const checkout = new GuardWatchCheckout(opts);
    try { await checkout.initialize(); } catch (err) { log("watch_payments_unavailable", { error: (err as Error).message.split("\n")[0] }); }
    startWatchServer(opts, checkout, cfg.httpPort, cfg.httpHost);
    log("watch_api", { url: `http://${cfg.httpHost}:${cfg.httpPort}`, paymentsReady: checkout.enabled });
  }
  for (;;) {
    try { await tick(); } catch (err) { log("tick_failed", { error: (err as Error).message.split("\n")[0] }); }
    await new Promise((r) => setTimeout(r, cfg.pollMs));
  }
}

main().catch((err) => { log("fatal", { error: (err as Error).message.split("\n")[0] }); process.exit(1); });
