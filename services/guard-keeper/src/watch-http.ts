// Guard Watch local API: status reads plus the x402 subscription checkout (2 MUSD / 30 days, proposal).
//
// The checkout reuses Liqvera's existing x402 payment flow unchanged: exact scheme on eip155:31611,
// MUSD via Permit2 with EIP-2612 gas sponsoring, verified and settled by the facilitator. The server
// holds no key and never moves funds itself. Entitlement is NOT granted from this HTTP response: the
// keeper's WatchLedger only counts the settled MUSD Transfer it later reads from canonical chain logs.
import { createServer, type IncomingMessage, type Server, type ServerResponse } from "node:http";
import { x402ResourceServer, type FacilitatorClient } from "@x402/core/server";
import { decodePaymentSignatureHeader, encodePaymentRequiredHeader, encodePaymentResponseHeader } from "@x402/core/http";
import { ExactEvmScheme } from "@x402/evm/exact/server";
import { declareEip2612GasSponsoringExtension } from "@x402/extensions";
import type { Address } from "./logic.js";
import { GUARD_WATCH_PERIOD_SECONDS, GUARD_WATCH_PRICE, type WatchStatus } from "./watch.js";

export const NETWORK = "eip155:31611" as const;
export const PERMIT2 = { assetTransferMethod: "permit2", requiredExtension: "eip2612GasSponsoring", domainName: "Mezo USD", domainVersion: "1" } as const;

export interface WatchView {
  /** Current subscription status for a borrower (lower-case address). */
  status(borrower: Address): WatchStatus;
  /** Last keeper observation of the borrower's Guard policy, if any. */
  guard(borrower: Address): { armed: boolean; terminal: boolean; status?: string; icr?: string; checkedAt?: string } | null;
  summary(): Record<string, unknown>;
}

export interface WatchHttpOptions {
  view: WatchView;
  payTo: Address | null;
  musd: Address;
  freeTrial: boolean;
  trialDays: number;
  enforce: boolean;
  corsOrigin: string | null;
  facilitator: FacilitatorClient;
  publicBase?: string;
}

const ADDRESS = /^0x[0-9a-fA-F]{40}$/;
const json = (v: unknown) => JSON.stringify(v, (_k, x) => (typeof x === "bigint" ? x.toString() : x));

export function planOf(o: Pick<WatchHttpOptions, "payTo" | "musd" | "freeTrial" | "trialDays" | "enforce">) {
  return {
    product: "guard_watch", proposal: true, network: NETWORK, asset: o.musd, price_atomic: GUARD_WATCH_PRICE.toString(),
    price_display: "2 MUSD", period_days: Number(GUARD_WATCH_PERIOD_SECONDS / 86_400n), per: "trove",
    pay_to: o.payTo, payments_enabled: o.payTo !== null, free_trial: o.freeTrial, trial_days: o.freeTrial ? o.trialDays : 0,
    enforced: o.enforce,
  };
}

export class GuardWatchCheckout {
  private readonly server: x402ResourceServer;
  private ready = false;
  constructor(private readonly o: WatchHttpOptions) {
    this.server = new x402ResourceServer(o.facilitator).register(NETWORK, new ExactEvmScheme());
  }
  async initialize(): Promise<void> {
    if (!this.o.payTo) return;
    await this.server.initialize();
    this.ready = true;
  }
  get enabled(): boolean { return this.ready && this.o.payTo !== null; }

  async requirements(borrower: Address) {
    if (!this.enabled || !this.o.payTo) throw new HttpError(503, "GUARD_WATCH_PAYMENTS_DISABLED");
    const values = await this.server.buildPaymentRequirements({
      scheme: "exact", network: NETWORK, payTo: this.o.payTo, price: { asset: this.o.musd, amount: GUARD_WATCH_PRICE.toString() },
      maxTimeoutSeconds: 120, extra: { assetTransferMethod: PERMIT2.assetTransferMethod, name: PERMIT2.domainName, version: PERMIT2.domainVersion },
    });
    const value = values[0];
    if (values.length !== 1 || !value || value.amount !== GUARD_WATCH_PRICE.toString() || value.payTo.toLowerCase() !== this.o.payTo.toLowerCase() ||
      value.asset.toLowerCase() !== this.o.musd.toLowerCase()) throw new HttpError(503, "GUARD_WATCH_PAYMENTS_DISABLED");
    const required = await this.server.createPaymentRequiredResponse(values, {
      url: `${this.o.publicBase ?? "http://127.0.0.1"}/v1/guard-watch/troves/${borrower}/subscribe`,
      description: "Liqvera Guard Watch: keeper monitoring for one Mezo Trove for 30 days (2 MUSD, proposal pricing)",
      mimeType: "application/json",
    }, undefined, declareEip2612GasSponsoringExtension());
    return { value, header: encodePaymentRequiredHeader(required), body: required };
  }

  /** Verify then settle one payment for `borrower`. The payer must be the borrower itself. */
  async pay(borrower: Address, header: string) {
    if (header.length > 16_384) throw new HttpError(400, "PAYMENT_HEADER_TOO_LARGE");
    let payload;
    try { payload = decodePaymentSignatureHeader(header); } catch { throw new HttpError(400, "PAYMENT_HEADER_INVALID"); }
    const { value } = await this.requirements(borrower);
    const a = payload.accepted;
    if (payload.x402Version !== 2 || a?.scheme !== "exact" || a.network !== NETWORK || a.asset?.toLowerCase() !== this.o.musd.toLowerCase() ||
      a.amount !== GUARD_WATCH_PRICE.toString() || a.payTo?.toLowerCase() !== value.payTo.toLowerCase() ||
      a.extra?.assetTransferMethod !== PERMIT2.assetTransferMethod) throw new HttpError(409, "PAYMENT_TERMS_MISMATCH");
    const verified = await this.server.verifyPayment(payload, value);
    if (verified.isValid !== true) throw new HttpError(409, "PAYMENT_REJECTED", reasonOf(verified.invalidReason));
    if (verified.payer?.toLowerCase() !== borrower.toLowerCase()) throw new HttpError(409, "PAYER_IS_NOT_BORROWER");
    const settled = await this.server.settlePayment(payload, value);
    const tx = typeof settled.transaction === "string" && /^0x[0-9a-fA-F]{64}$/.test(settled.transaction) ? settled.transaction.toLowerCase() : null;
    if (!tx) throw new HttpError(502, "SETTLEMENT_UNCONFIRMED");
    return { tx, success: settled.success === true, header: encodePaymentResponseHeader({ success: true, transaction: tx, network: NETWORK, payer: borrower }) };
  }
}

export class HttpError extends Error { constructor(readonly status: number, readonly code: string, readonly reason?: string) { super(code); } }

/** The facilitator's machine-readable rejection reason (e.g. permit2_insufficient_balance), bounded and sanitized. */
function reasonOf(value: unknown): string | undefined {
  return typeof value === "string" && /^[A-Za-z0-9_.:-]{1,80}$/.test(value) ? value : undefined;
}

export function createWatchHandler(o: WatchHttpOptions, checkout: GuardWatchCheckout) {
  return async (req: IncomingMessage, res: ServerResponse): Promise<void> => {
    const send = (status: number, body: unknown, headers: Record<string, string> = {}) => {
      res.writeHead(status, { "content-type": "application/json", "cache-control": "no-store", ...cors(o.corsOrigin, req.headers.origin), ...headers });
      res.end(json(body));
    };
    try {
      if (req.method === "OPTIONS") { res.writeHead(204, cors(o.corsOrigin, req.headers.origin)); res.end(); return; }
      if (req.method !== "GET") throw new HttpError(405, "METHOD_NOT_ALLOWED");
      const path = new URL(req.url ?? "/", "http://local").pathname;
      if (path === "/healthz") return send(200, { ok: true, ...o.view.summary() });
      if (path === "/v1/guard-watch/plan") return send(200, { ...planOf(o), payments_ready: checkout.enabled });
      const m = /^\/v1\/guard-watch\/troves\/(0x[0-9a-fA-F]{40})(\/subscribe)?$/.exec(path);
      if (!m || !ADDRESS.test(m[1]!)) throw new HttpError(404, "NOT_FOUND");
      const borrower = m[1]!.toLowerCase() as Address;
      if (!m[2]) return send(200, { borrower, subscription: o.view.status(borrower), guard: o.view.guard(borrower), plan: planOf(o) });
      const header = req.headers["payment-signature"];
      if (typeof header !== "string" || header === "") {
        const r = await checkout.requirements(borrower);
        return send(402, r.body, { "PAYMENT-REQUIRED": r.header });
      }
      const paid = await checkout.pay(borrower, header);
      return send(200, { borrower, tx: paid.tx, note: "Subscription activates once the keeper reads this MUSD transfer from chain logs." },
        { "PAYMENT-RESPONSE": paid.header, "x-liqvera-payment-tx": paid.tx });
    } catch (err) {
      if (err instanceof HttpError) return send(err.status, err.reason ? { error: err.code, reason: err.reason } : { error: err.code });
      return send(500, { error: "INTERNAL" });
    }
  };
}

/** `allowed` is one origin or a comma-separated allowlist; only a listed request Origin is echoed back. */
export function cors(allowed: string | null, requestOrigin?: string): Record<string, string> {
  if (!allowed) return {};
  const list = allowed.split(",").map(x => x.trim()).filter(Boolean);
  const origin = list.length === 1 ? list[0]! : list.find(x => x === requestOrigin);
  if (!origin) return { "vary": "Origin" };
  return {
    "access-control-allow-origin": origin, "vary": "Origin", "access-control-allow-methods": "GET, OPTIONS",
    "access-control-allow-headers": "PAYMENT-SIGNATURE, Content-Type", "access-control-expose-headers": "PAYMENT-REQUIRED, PAYMENT-RESPONSE, x-liqvera-payment-tx",
  };
}

export function startWatchServer(o: WatchHttpOptions, checkout: GuardWatchCheckout, port: number, host: string): Server {
  const handler = createWatchHandler(o, checkout);
  const server = createServer((req, res) => { void handler(req, res); });
  // A busy port must not stop the keeper loop; the caller logs it.
  server.on("error", (err) => console.log(JSON.stringify({ ts: new Date().toISOString(), event: "watch_api_failed", error: err.message })));
  server.listen(port, host);
  return server;
}
