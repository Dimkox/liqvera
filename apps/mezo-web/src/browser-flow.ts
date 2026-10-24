import { MEZO, NETWORK_LABEL } from "./network.ts";
import type { BrowserFlowState, CreateInput } from "./flow-types.ts";
export type { BrowserFlowState } from "./flow-types.ts";

export interface BrowserProvider {
  request(input: { method: string; params?: unknown[] }): Promise<unknown>;
}

export type RecoveryRequest =
  | { kind: "create"; method: "POST"; path: "/v1/report-quotes"; idempotencyKey: string; body: Omit<CreateInput, "idempotencyKey"> }
  | { kind: "request"; method: "GET"; path: string }
  | { kind: "quote"; method: "GET"; path: string };

function firstAccount(value: unknown): string | null {
  if (!Array.isArray(value) || typeof value[0] !== "string" || !/^0x[0-9a-f]{40}$/i.test(value[0])) return null;
  return value[0];
}

export async function readWallet(provider: BrowserProvider): Promise<{ account: string | null; onMezo: boolean }> {
  const account = firstAccount(await provider.request({ method: "eth_accounts" }));
  const chain = await provider.request({ method: "eth_chainId" });
  return { account, onMezo: typeof chain === "string" && chain.toLowerCase() === "0x7b7b" };
}

export async function switchWalletToMezo(provider: BrowserProvider): Promise<{ account: string | null; onMezo: boolean }> {
  await provider.request({ method: "wallet_switchEthereumChain", params: [{ chainId: "0x7b7b" }] });
  return readWallet(provider);
}

export function recoveryRequest(flow: BrowserFlowState): RecoveryRequest {
  if (flow.quoteId) return { kind: "quote", method: "GET", path: `/v1/report-quotes/${flow.quoteId}` };
  if (flow.requestId) return { kind: "request", method: "GET", path: `/v1/report-requests/${flow.requestId}` };
  return { kind: "create", method: "POST", path: "/v1/report-quotes", idempotencyKey: flow.idempotencyKey,
    body: flow.version === 2 ? { product_id: flow.product_id, borrower: flow.borrower, payer: flow.payer } :
      { side: flow.side, quantity: flow.quantity, ...(flow.version===3?{mezo_dex:true as const}:{}), payer: flow.payer } };
}

export function canPay(input: {
  flow: BrowserFlowState | null;
  quoteState: string | null;
  connectedAccount: string | null;
  onMezo: boolean;
  paymentReady: boolean;
  adapterAvailable: boolean;
}): boolean {
  const { flow, quoteState, connectedAccount } = input;
  return Boolean(flow && quoteState === "READY" && connectedAccount &&
    connectedAccount.toLowerCase() === flow.payer.toLowerCase() && input.onMezo &&
    input.paymentReady && input.adapterAvailable && flow.paymentGuard === "clear");
}

export function walletStatus(providerAvailable: boolean, onMezo: boolean): string {
  if (!providerAvailable) return "No injected EVM wallet found.";
  if (onMezo) return `${NETWORK_LABEL} · chain ${MEZO.chainId}`;
  return `Wrong network · switch to ${NETWORK_LABEL} (${MEZO.chainId}).`;
}

export function paymentNotice(quoteState: string | null, guard: BrowserFlowState["paymentGuard"] | null): string | null {
  if (guard !== null && guard !== "clear" || quoteState !== null && ["PAYMENT_PENDING", "PAYMENT_UNCERTAIN", "MANUAL_REVIEW"].includes(quoteState)) {
    return "Checking the payment already submitted or possibly submitted. Do not pay again. Use Check status to recover this same report.";
  }
  return null;
}

export function beginPayment<T extends BrowserFlowState>(flow: T): T {
  if (flow.paymentGuard !== "clear") throw new Error("Payment is already guarded.");
  return { ...flow, paymentGuard: "started" };
}

export function paymentFailure<T extends BrowserFlowState>(
  flow: T,
  kind: "cancelled-before-submission" | "ambiguous",
  refreshedQuoteState: string | null,
): T {
  const paymentGuard = kind === "cancelled-before-submission" && refreshedQuoteState === "READY" ? "clear" : "uncertain";
  return { ...flow, paymentGuard };
}
