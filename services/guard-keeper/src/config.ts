// Keeper configuration. Pure: parses an env object, so it is unit-tested without process state.
import type { Address } from "./logic.js";

export const MEZO_TESTNET_CHAIN_ID = 31611;
/** LiqveraGuard on Mezo Testnet (tx 0x8fb90b1f…1175, Blockscout-verified). */
export const TESTNET_GUARD: Address = "0x61e12BDDFa62adF0Ffa89544153954a2420cF37a";
export const TESTNET_GUARD_DEPLOY_BLOCK = 16524690n;
export const TESTNET_MUSD: Address = "0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503";

export interface KeeperConfig {
  rpcUrl: string;
  chainId: number;
  guard: Address;
  fromBlock: bigint;
  troveManager: Address;
  hintHelpers: Address;
  sortedTroves: Address;
  musd: Address;
  pollMs: number;
  /** True unless DRY_RUN=0 is set explicitly. Dry run never needs or reads a key. */
  dryRun: boolean;
  /** Only Troves with an active Guard Watch subscription are served. GUARD_WATCH_ENFORCE=0 serves every armed Trove. */
  watchEnforce: boolean;
  /** Testnet free trial: every armed Trove gets `trialDays` of Guard Watch from its first Armed event. */
  freeTrial: boolean;
  trialDays: number;
  /** Merchant that receives Guard Watch payments. Without it, paid subscriptions are not recognised. */
  watchPayTo: Address | null;
  /** Local status / subscription API. 0 disables it. */
  httpPort: number;
  httpHost: string;
  corsOrigin: string | null;
  facilitatorUrl: string;
}

const ADDRESS = /^0x[0-9a-fA-F]{40}$/;
function addr(v: string, name: string): Address {
  if (!ADDRESS.test(v) || /^0x0{40}$/.test(v)) throw new Error(`invalid address in ${name}`);
  return v as Address;
}
function int(v: string, name: string, min: number, max: number): number {
  if (!/^[0-9]+$/.test(v)) throw new Error(`invalid integer in ${name}`);
  const n = Number(v);
  if (n < min || n > max) throw new Error(`${name} out of range`);
  return n;
}
function flag(v: string | undefined, name: string, dflt: boolean): boolean {
  if (v === undefined || v === "") return dflt;
  if (v === "1" || v === "true") return true;
  if (v === "0" || v === "false") return false;
  throw new Error(`${name} must be 0 or 1`);
}

export function loadConfig(env: Record<string, string | undefined>): KeeperConfig {
  const get = (k: string, d: string): string => (env[k] === undefined || env[k] === "" ? d : env[k]!);
  const chainId = int(get("CHAIN_ID", String(MEZO_TESTNET_CHAIN_ID)), "CHAIN_ID", 1, 2 ** 31);
  // Testnet only: the keeper refuses any other chain id before it builds a client.
  if (chainId !== MEZO_TESTNET_CHAIN_ID) throw new Error("the guard keeper only runs on Mezo Testnet (31611)");
  const dryRun = flag(env.DRY_RUN, "DRY_RUN", true);
  if (!dryRun && !env.KEEPER_PRIVATE_KEY) throw new Error("DRY_RUN=0 needs KEEPER_PRIVATE_KEY (a funded testnet keeper key)");
  const payTo = env.GUARD_WATCH_PAY_TO ? addr(env.GUARD_WATCH_PAY_TO, "GUARD_WATCH_PAY_TO") : null;
  const facilitatorUrl = new URL(get("GUARD_WATCH_FACILITATOR_URL", "https://facilitator.vativ.io/")).href;
  return {
    rpcUrl: new URL(get("MEZO_RPC_URL", "https://rpc.test.mezo.org")).href.replace(/\/$/, ""),
    chainId,
    guard: addr(get("GUARD_ADDRESS", TESTNET_GUARD), "GUARD_ADDRESS"),
    fromBlock: BigInt(int(get("GUARD_DEPLOY_BLOCK", String(TESTNET_GUARD_DEPLOY_BLOCK)), "GUARD_DEPLOY_BLOCK", 0, 2 ** 48)),
    troveManager: addr(get("TROVE_MANAGER", "0xE47c80e8c23f6B4A1aE41c34837a0599D5D16bb0"), "TROVE_MANAGER"),
    hintHelpers: addr(get("HINT_HELPERS", "0x4e4cBA3779d56386ED43631b4dCD6d8EacEcBCF6"), "HINT_HELPERS"),
    sortedTroves: addr(get("SORTED_TROVES", "0x722E4D24FD6Ff8b0AC679450F3D91294607268fA"), "SORTED_TROVES"),
    musd: addr(get("MUSD_ADDRESS", TESTNET_MUSD), "MUSD_ADDRESS"),
    pollMs: int(get("POLL_INTERVAL_MS", "30000"), "POLL_INTERVAL_MS", 1000, 3_600_000),
    dryRun,
    watchEnforce: flag(env.GUARD_WATCH_ENFORCE, "GUARD_WATCH_ENFORCE", true),
    freeTrial: flag(env.GUARD_WATCH_FREE_TRIAL, "GUARD_WATCH_FREE_TRIAL", false),
    trialDays: int(get("GUARD_WATCH_TRIAL_DAYS", "30"), "GUARD_WATCH_TRIAL_DAYS", 1, 90),
    watchPayTo: payTo,
    httpPort: int(get("GUARD_WATCH_HTTP_PORT", "8795"), "GUARD_WATCH_HTTP_PORT", 0, 65535),
    httpHost: get("GUARD_WATCH_HTTP_HOST", "127.0.0.1"),
    corsOrigin: env.GUARD_WATCH_CORS_ORIGIN || null,
    facilitatorUrl,
  };
}

/** Safe-to-log view: never includes the key. */
export function describeConfig(c: KeeperConfig): Record<string, unknown> {
  return {
    chainId: c.chainId, rpc: c.rpcUrl, guard: c.guard, fromBlock: c.fromBlock, pollMs: c.pollMs, dryRun: c.dryRun,
    watchEnforce: c.watchEnforce, freeTrial: c.freeTrial, trialDays: c.trialDays, watchPayTo: c.watchPayTo,
    http: c.httpPort ? `${c.httpHost}:${c.httpPort}` : "off",
  };
}
