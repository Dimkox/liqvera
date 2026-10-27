// Minimal Liqvera Guard keeper. Testnet only.
// It holds only its own hot key (KEEPER_PRIVATE_KEY, from env). It never holds user keys:
// users sign Mezo EIP-712 messages in their own wallet and the Guard stores them.
import { createPublicClient, createWalletClient, defineChain, http, type Hex } from "viem";
import { privateKeyToAccount } from "viem/accounts";
import { guardAbi, hintHelpersAbi, sortedTrovesAbi, troveManagerAbi } from "./abi.js";
import { type Address, type ArmLog, armedSet, isTerminal, logLine, nicr, projectedTrove, selectReady, STATUS } from "./logic.js";

const env = (k: string, d?: string): string => {
  const v = process.env[k] ?? d;
  if (v === undefined || v === "") throw new Error(`missing env ${k}`);
  return v;
};

const RPC = env("MEZO_RPC_URL", "https://rpc.test.mezo.org");
const GUARD = env("GUARD_ADDRESS") as Address;
const FROM_BLOCK = BigInt(env("GUARD_DEPLOY_BLOCK", "0"));
const TM = env("TROVE_MANAGER", "0xE47c80e8c23f6B4A1aE41c34837a0599D5D16bb0") as Address;
const HINTS = env("HINT_HELPERS", "0x4e4cBA3779d56386ED43631b4dCD6d8EacEcBCF6") as Address;
const SORTED = env("SORTED_TROVES", "0x722E4D24FD6Ff8b0AC679450F3D91294607268fA") as Address;
const POLL_MS = Number(env("POLL_INTERVAL_MS", "30000"));
const LOG_CHUNK = 10_000n;
const DRY_RUN = process.env.DRY_RUN === "1";

const chain = defineChain({
  id: 31611, name: "Mezo Testnet", nativeCurrency: { name: "Bitcoin", symbol: "BTC", decimals: 18 },
  rpcUrls: { default: { http: [RPC] } },
});
const pub = createPublicClient({ chain, transport: http(RPC, { retryCount: 3 }) });
const account = DRY_RUN ? undefined : privateKeyToAccount(env("KEEPER_PRIVATE_KEY") as Hex);
const wallet = account ? createWalletClient({ chain, account, transport: http(RPC) }) : undefined;

const log = (e: string, f: Record<string, unknown> = {}) => console.log(logLine(e, f));

let scanned = FROM_BLOCK - 1n;
const history: ArmLog[] = [];

async function syncLogs(): Promise<Set<Address>> {
  const head = await pub.getBlockNumber();
  while (scanned < head) {
    const from = scanned + 1n;
    const to = from + LOG_CHUNK - 1n < head ? from + LOG_CHUNK - 1n : head;
    const logs = await pub.getContractEvents({ address: GUARD, abi: guardAbi, fromBlock: from, toBlock: to });
    for (const l of logs) {
      if (l.eventName !== "Armed" && l.eventName !== "Disarmed" && l.eventName !== "Protected") continue;
      history.push({ kind: l.eventName, user: (l.args as { user: Address }).user, blockNumber: l.blockNumber, logIndex: l.logIndex });
    }
    scanned = to;
  }
  return armedSet(history);
}

async function hintsFor(borrower: Address): Promise<[Address, Address]> {
  const p = await pub.readContract({ address: GUARD, abi: guardAbi, functionName: "policyOf", args: [borrower] });
  const [coll, principal, interest] = await pub.readContract({ address: TM, abi: troveManagerAbi, functionName: "getEntireDebtAndColl", args: [borrower] });
  const next = projectedTrove(p.action as 1 | 2, p.amount, coll, principal, interest);
  const target = nicr(next.coll, next.principal);
  const [approx] = await pub.readContract({ address: HINTS, abi: hintHelpersAbi, functionName: "getApproxHint", args: [target, 15n, BigInt(Date.now())] });
  const [upper, lower] = await pub.readContract({ address: SORTED, abi: sortedTrovesAbi, functionName: "findInsertPosition", args: [target, approx, approx] });
  return [upper, lower];
}

async function tick(): Promise<void> {
  const armed = await syncLogs();
  const reads = [];
  for (const b of armed) {
    const [s, icr] = await pub.readContract({ address: GUARD, abi: guardAbi, functionName: "status", args: [b] });
    if (s !== 0) log("skip", { borrower: b, status: STATUS[s] ?? s, icr, terminal: isTerminal(s) });
    reads.push({ borrower: b, status: s, icr });
  }
  for (const r of selectReady(reads)) {
    try {
      const [upper, lower] = await hintsFor(r.borrower);
      // Simulate first: a front-run or a stale nonce reverts here and costs no gas.
      const { request } = await pub.simulateContract({
        address: GUARD, abi: guardAbi, functionName: "protect", args: [r.borrower, upper, lower], account: account?.address,
      });
      if (!wallet) { log("dry_run_ready", { borrower: r.borrower, icr: r.icr, upper, lower }); continue; }
      const hash = await wallet.writeContract(request);
      const rcpt = await pub.waitForTransactionReceipt({ hash });
      log("protected", { borrower: r.borrower, icrBefore: r.icr, tx: hash, status: rcpt.status, gasUsed: rcpt.gasUsed });
    } catch (err) {
      log("protect_failed", { borrower: r.borrower, error: (err as Error).message.split("\n")[0] });
    }
  }
}

async function main(): Promise<void> {
  log("start", { guard: GUARD, rpc: RPC, keeper: account?.address ?? "dry-run", pollMs: POLL_MS });
  for (;;) {
    try { await tick(); } catch (err) { log("tick_failed", { error: (err as Error).message.split("\n")[0] }); }
    await new Promise((r) => setTimeout(r, POLL_MS));
  }
}

void main();
