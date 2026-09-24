import { isAddress, isUuid, type Side } from "./contracts";

const CAPABILITY_KEY = "liqvera:v1:capability";
const FLOW_KEY = "liqvera:v1:flow";

export interface SavedFlow {
  version: 1;
  side: Side;
  quantity: string;
  payer: string;
  idempotencyKey: string;
  requestId?: string;
  quoteId?: string;
  paymentGuard: "clear" | "started" | "uncertain";
}

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
    if (flow.version !== 1 || !["BUY", "SELL"].includes(flow.side) ||
        !/^(?:0|[1-9][0-9]*)(?:\.[0-9]{1,8})?$/.test(flow.quantity) ||
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
