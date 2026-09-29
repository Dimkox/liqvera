export interface BrowserFlowState {
  readonly version: 1;
  readonly side: "BUY" | "SELL";
  readonly quantity: string;
  readonly payer: string;
  readonly idempotencyKey: string;
  readonly requestId?: string;
  readonly quoteId?: string;
  readonly paymentGuard: "clear" | "started" | "uncertain";
}

function beginPayment<T extends BrowserFlowState>(flow: T): T {
  if (flow.paymentGuard !== "clear") throw new Error("Payment is already guarded.");
  return { ...flow, paymentGuard: "started" };
}

function paymentFailure<T extends BrowserFlowState>(flow: T, preSubmitCancel: boolean, ready: boolean): T {
  return { ...flow, paymentGuard: preSubmitCancel && ready ? "clear" : "uncertain" };
}

interface QuoteLike { quote_id: string; state: string; report_id?: string }
interface RequestLike { state: string; quote_id?: string }

export interface RecoveryDependencies<Q extends QuoteLike, R extends RequestLike, D> {
  getQuote(id: string): Promise<Q>;
  getRequest(id: string): Promise<R>;
  createQuote(input: { side: "BUY" | "SELL"; quantity: string; payer: string; idempotencyKey: string }): Promise<Q | R>;
  getPaidDelivery(id: string): Promise<D | null>;
  onQuote(quote: Q): void;
  onRequest(request: R): void;
  onDelivery(delivery: D): void;
  notice(message: string): void;
}

export type RecoveryResult<Q, R> =
  | { kind: "quote"; quote: Q }
  | { kind: "request"; request: R };

function isQuote<Q extends QuoteLike, R extends RequestLike>(value: Q | R): value is Q {
  return "quote_id" in value && typeof value.quote_id === "string";
}

export async function executeRecovery<Q extends QuoteLike, R extends RequestLike, D>(
  flow: BrowserFlowState,
  dependencies: RecoveryDependencies<Q, R, D>,
): Promise<RecoveryResult<Q, R>> {
  if (flow.quoteId) {
    const quote = await dependencies.getQuote(flow.quoteId!);
    dependencies.onQuote(quote);
    if (quote.state === "PAID" && quote.report_id) {
      const delivery = await dependencies.getPaidDelivery(quote.report_id);
      if (delivery !== null) {
        dependencies.onDelivery(delivery);
        dependencies.notice("Paid report recovered without another payment.");
      }
    }
    return { kind: "quote", quote };
  }
  if (flow.requestId) {
    const request = await dependencies.getRequest(flow.requestId!);
    dependencies.onRequest(request);
    if (request.state === "READY" && request.quote_id) {
      const quote = await dependencies.getQuote(request.quote_id);
      dependencies.onQuote(quote);
      return { kind: "quote", quote };
    }
    return { kind: "request", request };
  }
  const created = await dependencies.createQuote({ side: flow.side, quantity: flow.quantity, payer: flow.payer,
    idempotencyKey: flow.idempotencyKey });
  if (isQuote(created)) {
    dependencies.onQuote(created);
    return { kind: "quote", quote: created };
  }
  dependencies.onRequest(created);
  return { kind: "request", request: created };
}

export interface PaymentDependencies<Q extends QuoteLike> {
  validateWallet(): Promise<void>;
  requestPaidReport(): Promise<"recovering" | "submitted">;
  refreshQuote(): Promise<Q | null>;
  isPreSubmitCancellation(error: unknown): boolean;
  persist(flow: BrowserFlowState): void;
  notice(message: string): void;
}

export async function executePaymentAttempt<T extends BrowserFlowState, Q extends QuoteLike>(
  original: T,
  _quote: Q,
  dependencies: PaymentDependencies<Q>,
): Promise<T> {
  await dependencies.validateWallet();
  let flow = beginPayment(original);
  dependencies.persist(flow);
  dependencies.notice("Opening the reviewed x402 wallet flow.");
  try {
    const result = await dependencies.requestPaidReport();
    if (result === "recovering") {
      flow = paymentFailure(flow, false, false);
      dependencies.persist(flow);
      dependencies.notice("Checking the payment already submitted. Do not pay again.");
      return flow;
    }
    const latest = await dependencies.refreshQuote();
    if (latest?.state !== "PAID") {
      flow = paymentFailure(flow, false, latest?.state === "READY");
      dependencies.persist(flow);
      dependencies.notice("The payment outcome is not yet confirmed. Check status; do not pay again.");
    }
    return flow;
  } catch (error) {
    if (dependencies.isPreSubmitCancellation(error)) {
      const latest = await dependencies.refreshQuote().catch(() => null);
      flow = paymentFailure(flow, true, latest?.state === "READY");
      dependencies.persist(flow);
      dependencies.notice(flow.paymentGuard === "clear"
        ? "Wallet payment was canceled before submission. The quote remains unpaid."
        : "Payment status needs checking before another wallet action.");
      return flow;
    }
    flow = paymentFailure(flow, false, false);
    dependencies.persist(flow);
    dependencies.notice("Payment status needs checking. Do not pay again.");
    return flow;
  }
}

interface EventProvider {
  on?(event: string, listener: (...args: unknown[]) => void): void;
  removeListener?(event: string, listener: (...args: unknown[]) => void): void;
}

export function bindWalletListeners(provider: EventProvider | null, refresh: () => void | Promise<void>): () => void {
  if (!provider?.on) return () => undefined;
  const listener = (): void => { void refresh(); };
  provider.on("accountsChanged", listener);
  provider.on("chainChanged", listener);
  return () => {
    provider.removeListener?.("accountsChanged", listener);
    provider.removeListener?.("chainChanged", listener);
  };
}
