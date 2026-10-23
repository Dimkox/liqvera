import { MEZO, MUSD } from "./network.ts";

export const NETWORK = MEZO.caip2;
export const CHAIN_ID = MEZO.chainId;
export const CHAIN_HEX = `0x${MEZO.chainId.toString(16)}`;
export const ASSET = MUSD.address;
export const ASSET_DECIMALS = MUSD.decimals;
export const AMOUNT_ATOMIC = "10000000000000000";
export const PRICE_MUSD = "0.01";
export const INSTRUMENT = "hyperliquid:BTC:perpetual";

export type Side = "BUY" | "SELL";
export type QuoteState = "READY" | "PAYMENT_PENDING" | "PAYMENT_UNCERTAIN" | "PAID" | "EXPIRED" | "MANUAL_REVIEW";

export interface Capabilities {
  schema: "liqvera-evidence-capabilities/v1";
  instrument_id: typeof INSTRUMENT;
  instrument_label: string;
  network: typeof NETWORK;
  asset: typeof ASSET;
  decimals: typeof ASSET_DECIMALS;
  price_musd: typeof PRICE_MUSD;
  amount_atomic: typeof AMOUNT_ATOMIC;
  source_mode: "fixture" | "live-public";
  limitations: string[];
  payment_ready: boolean;
  blockers: string[];
}

export interface Quote {
  schema: "liqvera-evidence-quote/v1";
  quote_id: string;
  report_request_id: string;
  report_id: string;
  report_sha256: string;
  bundle_sha256: string;
  state: QuoteState;
  preview: {
    instrument_id: typeof INSTRUMENT;
    side: Side;
    quantity_base: string;
    snapshot_at: string;
    snapshot_status: "VALID_FOR_SNAPSHOT_CALCULATION";
    limitations: string[];
    price_musd: typeof PRICE_MUSD;
    expires_at: string;
  };
  terms: {
    version: "liqvera-evidence-terms/v1";
    network: typeof NETWORK;
    chain_id: typeof CHAIN_ID;
    asset: typeof ASSET;
    decimals: typeof ASSET_DECIMALS;
    amount_atomic: typeof AMOUNT_ATOMIC;
    price_musd: typeof PRICE_MUSD;
    pay_to: string;
    expected_payer: string;
    expires_at: string;
  };
  retention: {
    paid_days: number;
    unpaid_grace_seconds: number;
    ledger_days: number;
    authorization_validity_floor: true;
    deletion_must_not_enable_replay: true;
  };
}

export interface RequestStatus {
  schema: "liqvera-evidence-request-status/v1";
  report_request_id: string;
  status_location: string;
  state: "PREPARING" | "READY" | "REJECTED" | "BUILD_FAILED";
  quote_id?: string;
  reason?: string;
}

export interface Receipt {
  schema: "liqvera-evidence-receipt/v1";
  quote_id: string;
  report_id: string;
  report_sha256: string;
  network: typeof NETWORK;
  chain_id: typeof CHAIN_ID;
  asset: typeof ASSET;
  amount_atomic: typeof AMOUNT_ATOMIC;
  payer: string;
  pay_to: string;
  tx_hash: string;
  block_hash: string;
  block_number: number;
  log_index: number;
  confirmed_at: string;
  finality_policy_version: string;
  transaction_from: string;
  buyer_native_balance_before: string;
  buyer_native_balance_after: string;
  buyer_native_gas_spent: "0";
  observation_before_block_number: number;
  observation_before_block_hash: string;
  observation_after_block_number: number;
  observation_after_block_hash: string;
  confirmations: number;
  authorization_identity: string;
  transfer_identity: string;
}

export interface MezoDexReport {
  side: Side; quantity_btc: string; mid_price_musd: string; avg_price_musd: string;
  amount_in: string; amount_out: string; price_impact_bps: string; fee_bps: number;
  router_amount_out: string; formula_amount_out: string; match: boolean;
  block_number: string; block_hash: string; caveats: string[];
  depth_ladder: {quantity_btc:string; price_impact_bps?:string; status?:string}[];
}
export interface Report {
  mezo_dex?: MezoDexReport;
  venue_comparison?: {hyperliquid_avg_price:string; mezo_avg_price:string; spread_bps:string;
                     better_venue:string; caveats:string[]};
  schema: "liqvera-evidence-report/v1";
  report_id: string;
  identity: { venue: string; instrument_id: string; product_kind: string; payoff_kind: string; quantity_unit: string };
  request: { side: Side; quantity_base: string };
  source: { source_mode: string; source_at: string; observed_at: string; available_bid_levels: number; available_ask_levels: number };
  calculation: {
    requested_quantity: string;
    filled_quantity: string;
    consumed_levels: number;
    display: { notional_quote: string; vwap: string; worst_price: string; price_impact_bps: string };
  };
  quality: { snapshot_status: string; reason_codes: string[]; limitations: string[]; stage_a?: { decision: string; reasons: string[] } };
  boundaries: { execution_authority: "NONE"; execution_promise: false; calculation_label: "hypothetical snapshot sweep" };
}

export interface Delivery {
  schema: "liqvera-evidence-delivery/v1";
  report: Report;
  receipt: Receipt;
}

export interface ApiErrorBody {
  schema: "liqvera-evidence-error/v1";
  request_id: string;
  code: string;
  message: string;
}

export function isAddress(value: string): boolean {
  return /^0x[0-9a-fA-F]{40}$/.test(value) && !/^0x0{40}$/i.test(value);
}

export function isUuid(value: string): boolean {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value);
}

export function isSha256(value: string): boolean {
  return /^[0-9a-f]{64}$/.test(value);
}

export function quoteIsPayable(quote: Quote, payer: string): boolean {
  const terms = quote.terms;
  return quote.state === "READY" &&
    quote.preview.snapshot_status === "VALID_FOR_SNAPSHOT_CALCULATION" &&
    quote.preview.instrument_id === INSTRUMENT &&
    quote.preview.price_musd === PRICE_MUSD &&
    terms.version === "liqvera-evidence-terms/v1" &&
    terms.network === NETWORK && terms.chain_id === CHAIN_ID &&
    terms.asset.toLowerCase() === ASSET.toLowerCase() &&
    terms.decimals === ASSET_DECIMALS && terms.amount_atomic === AMOUNT_ATOMIC &&
    terms.price_musd === PRICE_MUSD && isAddress(terms.pay_to) &&
    terms.expected_payer.toLowerCase() === payer.toLowerCase() &&
    terms.expires_at === quote.preview.expires_at &&
    Number.isFinite(Date.parse(terms.expires_at)) && Date.now() < Date.parse(terms.expires_at);
}

export function receiptMatchesQuote(receipt: Receipt, quote: Quote): boolean {
  return receipt.schema === "liqvera-evidence-receipt/v1" &&
    receipt.quote_id === quote.quote_id && receipt.report_id === quote.report_id &&
    receipt.report_sha256 === quote.report_sha256 && isSha256(receipt.report_sha256) &&
    receipt.network === NETWORK && receipt.chain_id === CHAIN_ID &&
    receipt.asset.toLowerCase() === ASSET.toLowerCase() &&
    receipt.amount_atomic === AMOUNT_ATOMIC &&
    receipt.payer.toLowerCase() === quote.terms.expected_payer.toLowerCase() &&
    receipt.pay_to.toLowerCase() === quote.terms.pay_to.toLowerCase() &&
    /^0x[0-9a-f]{64}$/.test(receipt.tx_hash) &&
    Number.isSafeInteger(receipt.block_number) && receipt.block_number >= 0 &&
    Number.isSafeInteger(receipt.log_index) && receipt.log_index >= 0;
}
