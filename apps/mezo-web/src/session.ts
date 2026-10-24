import { CHAIN_ID, isAddress, isUuid } from "./contracts.ts";

const PREFIX = CHAIN_ID === 31611 ? "liqvera:v1" : `liqvera:${CHAIN_ID}:v1`;
const CAPABILITY_KEY = `${PREFIX}:capability`;
const FLOW_KEY = `${PREFIX}:flow`;

import type { BrowserFlowState } from "./flow-types.ts";
type Mutable<T> = {-readonly [K in keyof T]: T[K]};
export type SavedFlow = Mutable<BrowserFlowState>;

function storage(): Storage {
  try {
    const store = window.sessionStorage;
    const probe = "liqvera:storage-probe";
    store.setItem(probe, "1");
    store.removeItem(probe);
    return store;
  } catch {
    throw new Error("Session storage is required to recover a report. Enable it before continuing.");
  }
}

export function capability(): string {
  const store = storage();
  const existing = store.getItem(CAPABILITY_KEY);
  if (existing && /^[A-Za-z0-9_-]{43}$/.test(existing)) return existing;
  if (!window.crypto?.getRandomValues) throw new Error("A secure browser context is required.");
  const bytes = crypto.getRandomValues(new Uint8Array(32));
  const encoded = btoa(String.fromCharCode(...bytes)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  store.setItem(CAPABILITY_KEY, encoded);
  return encoded;
}

export function loadFlow(): SavedFlow | null {
  const raw = storage().getItem(FLOW_KEY);
  if (!raw) return null;
  try {
    const data: unknown = JSON.parse(raw);
    if (!data || typeof data !== "object") return null;
    const flow = data as SavedFlow;
    const productValid = flow.version === 1 ? flow.product_id === undefined && flow.borrower === undefined && flow.mezo_dex === undefined &&
      ["BUY", "SELL"].includes(flow.side) && /^(?:0|[1-9][0-9]*)(?:\.[0-9]{1,8})?$/.test(flow.quantity) :
      flow.version === 2 && flow.product_id === "trove_risk" && isAddress(flow.borrower) &&
      flow.side === undefined && flow.quantity === undefined ? true :
      flow.version === 3 && flow.product_id === undefined && flow.borrower === undefined && flow.mezo_dex === true &&
      ["BUY", "SELL"].includes(flow.side) && /^(?:0|[1-9][0-9]*)(?:\.[0-9]{1,8})?$/.test(flow.quantity);
    if (!productValid ||
        !isAddress(flow.payer) || !isUuid(flow.idempotencyKey) ||
        (flow.requestId !== undefined && !isUuid(flow.requestId)) ||
        (flow.quoteId !== undefined && !isUuid(flow.quoteId)) ||
        !["clear", "started", "uncertain"].includes(flow.paymentGuard)) return null;
    return flow;
  } catch {
    return null;
  }
}

export function saveFlow(flow: SavedFlow): void {
  storage().setItem(FLOW_KEY, JSON.stringify(flow));
}

export function clearFlow(): void {
  storage().removeItem(FLOW_KEY);
}
