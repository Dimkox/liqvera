import {
  AMOUNT_ATOMIC, ASSET, ASSET_DECIMALS, CHAIN_ID, INSTRUMENT, NETWORK, PRICE_MUSD,
  isAddress, isSha256, isUuid,
  type ApiErrorBody, type Capabilities, type Delivery, type Quote, type RequestStatus, type Side,
} from "./contracts";

export class ApiFailure extends Error {
  constructor(readonly status: number, readonly code: string, message: string, readonly requestId?: string) {
    super(message);
  }
}

function record(value: unknown): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) throw new Error("Unexpected API response.");
  return value as Record<string, unknown>;
}

function string(value: unknown): string {
  if (typeof value !== "string") throw new Error("Unexpected API response.");
  return value;
}

function strings(value: unknown): string[] {
  if (!Array.isArray(value) || !value.every(item => typeof item === "string")) throw new Error("Unexpected API response.");
  return value;
}

function validateCapabilities(value: unknown): Capabilities {
  const data = record(value);
  if (data.schema !== "mee-evidence-capabilities/v1" || data.instrument_id !== INSTRUMENT ||
      data.network !== NETWORK || data.asset !== ASSET || data.decimals !== ASSET_DECIMALS ||
      data.price_musd !== PRICE_MUSD || data.amount_atomic !== AMOUNT_ATOMIC ||
      (data.source_mode !== "live-public" && data.source_mode !== "fixture") ||
      typeof data.payment_ready !== "boolean") throw new Error("Gateway capability terms do not match this testnet app.");
  strings(data.limitations);
  strings(data.blockers);
  return data as unknown as Capabilities;
}

function validateQuote(value: unknown): Quote {
  const data = record(value);
  const preview = record(data.preview);
  const terms = record(data.terms);
  const retention = record(data.retention);
  if (data.schema !== "mee-evidence-quote/v1" || !isUuid(string(data.quote_id)) ||
      !isUuid(string(data.report_request_id)) || !isUuid(string(data.report_id)) ||
      !isSha256(string(data.report_sha256)) || !isSha256(string(data.bundle_sha256)) ||
      !["READY", "PAYMENT_PENDING", "PAYMENT_UNCERTAIN", "PAID", "EXPIRED", "MANUAL_REVIEW"].includes(string(data.state)) ||
      preview.instrument_id !== INSTRUMENT || !["BUY", "SELL"].includes(string(preview.side)) ||
      preview.snapshot_status !== "VALID_FOR_SNAPSHOT_CALCULATION" ||
      preview.price_musd !== PRICE_MUSD ||
      terms.version !== "mee-evidence-terms/v1" || terms.network !== NETWORK ||
      terms.chain_id !== CHAIN_ID || terms.asset !== ASSET || terms.decimals !== ASSET_DECIMALS ||
      terms.amount_atomic !== AMOUNT_ATOMIC || terms.price_musd !== PRICE_MUSD ||
      !isAddress(string(terms.pay_to)) || !isAddress(string(terms.expected_payer)) ||
      terms.expires_at !== preview.expires_at ||
      typeof retention.paid_days !== "number" || retention.paid_days < 7 ||
      typeof retention.unpaid_grace_seconds !== "number" || retention.unpaid_grace_seconds < 900 ||
      typeof retention.ledger_days !== "number" || retention.ledger_days < 30 ||
      retention.authorization_validity_floor !== true || retention.deletion_must_not_enable_replay !== true) {
    throw new Error("Quote terms failed local contract checks. No payment is available.");
  }
  string(preview.quantity_base);
  string(preview.snapshot_at);
  string(preview.expires_at);
  strings(preview.limitations);
  return data as unknown as Quote;
}

function validateRequest(value: unknown): RequestStatus {
  const data = record(value);
  if (data.schema !== "mee-evidence-request-status/v1" || !isUuid(string(data.report_request_id)) ||
      data.status_location !== `/v1/report-requests/${data.report_request_id}` ||
      !["PREPARING", "READY", "REJECTED", "BUILD_FAILED"].includes(string(data.state))) {
    throw new Error("Unexpected request status.");
  }
  if (data.state === "READY" && !isUuid(string(data.quote_id))) throw new Error("Ready request has no quote.");
  if ((data.state === "REJECTED" || data.state === "BUILD_FAILED") && typeof data.reason !== "string") throw new Error("Rejected request has no reason.");
  return data as unknown as RequestStatus;
}

export function validateDelivery(value: unknown, reportId: string): Delivery {
  const data = record(value);
  const report = record(data.report);
  const receipt = record(data.receipt);
  const identity = record(report.identity);
  const requestBody = record(report.request);
  const source = record(report.source);
  const calculation = record(report.calculation);
  const display = record(calculation.display);
  const quality = record(report.quality);
  const boundaries = record(report.boundaries);
  if (data.schema !== "mee-evidence-delivery/v1" || report.schema !== "mee-evidence-report/v1" ||
      report.report_id !== reportId || receipt.report_id !== reportId ||
      receipt.schema !== "mee-evidence-receipt/v1" ||
      identity.instrument_id !== INSTRUMENT || identity.product_kind !== "perpetual" ||
      !isUuid(string(receipt.quote_id)) || !isSha256(string(receipt.report_sha256)) ||
      receipt.network !== NETWORK || receipt.chain_id !== CHAIN_ID || receipt.asset !== ASSET ||
      receipt.amount_atomic !== AMOUNT_ATOMIC ||
      !isAddress(string(receipt.payer)) || !isAddress(string(receipt.pay_to)) ||
      !/^0x[0-9a-f]{64}$/.test(string(receipt.tx_hash)) ||
      !Number.isSafeInteger(receipt.block_number) || !Number.isSafeInteger(receipt.log_index) ||
      !Number.isFinite(Date.parse(string(receipt.confirmed_at))) ||
      !string(receipt.finality_policy_version) ||
      !["BUY", "SELL"].includes(string(requestBody.side)) ||
      !/^(0|[1-9][0-9]*)(\.[0-9]{0,7}[1-9])?$/.test(string(requestBody.quantity_base)) ||
      source.source_mode !== "live-public" ||
      !Number.isFinite(Date.parse(string(source.source_at))) ||
      !Number.isSafeInteger(source.available_bid_levels) || !Number.isSafeInteger(source.available_ask_levels) ||
      !Number.isSafeInteger(calculation.consumed_levels) ||
      quality.snapshot_status !== "VALID_FOR_SNAPSHOT_CALCULATION" ||
      boundaries.execution_authority !== "NONE" || boundaries.execution_promise !== false ||
      boundaries.calculation_label !== "hypothetical snapshot sweep") throw new Error("Paid response failed local integrity checks.");
  string(display.notional_quote);
  string(display.vwap);
  string(display.worst_price);
  string(display.price_impact_bps);
  strings(quality.limitations);
  strings(quality.reason_codes);
  return data as unknown as Delivery;
}

async function errorFor(response: Response): Promise<ApiFailure> {
  let code = `HTTP_${response.status}`;
  let message = "The service could not complete this request.";
  let requestId: string | undefined;
  try {
    const body = await response.json() as ApiErrorBody;
    if (body.schema === "mee-evidence-error/v1") {
      code = body.code;
      message = body.message;
      requestId = body.request_id;
    }
  } catch { /* The status remains useful if the body is unavailable. */ }
  return new ApiFailure(response.status, code, message, requestId);
}

async function request(path: string, capability: string | null, init: RequestInit = {}): Promise<Response> {
  if (!/^\/v1\/[A-Za-z0-9/-]+$/.test(path)) throw new Error("Invalid API path.");
  const headers = new Headers(init.headers);
  if (capability) headers.set("Authorization", `Bearer ${capability}`);
  if (!headers.has("Accept")) headers.set("Accept", "application/json");
  const response = await fetch(path, { ...init, headers, cache: "no-store", credentials: "omit", redirect: "error" });
  return response;
}

export async function getCapabilities(): Promise<Capabilities> {
  const response = await request("/v1/capabilities", null);
  if (!response.ok) throw await errorFor(response);
  return validateCapabilities(await response.json());
}

export async function createQuote(capability: string, input: { side: Side; quantity: string; payer: string; idempotencyKey: string }): Promise<Quote | RequestStatus> {
  const response = await request("/v1/report-quotes", capability, {
    method: "POST",
    headers: { "Content-Type": "application/json", "Idempotency-Key": input.idempotencyKey },
    body: JSON.stringify({ instrument_id: INSTRUMENT, side: input.side, quantity_base: input.quantity, expected_payer: input.payer }),
  });
  if (response.status === 201) return validateQuote(await response.json());
  if (response.status === 202) return validateRequest(await response.json());
  throw await errorFor(response);
}

export async function getRequest(capability: string, id: string): Promise<RequestStatus> {
  if (!isUuid(id)) throw new Error("Invalid request identifier.");
  const response = await request(`/v1/report-requests/${id}`, capability);
  if (response.status !== 200 && response.status !== 202) throw await errorFor(response);
  return validateRequest(await response.json());
}

export async function getQuote(capability: string, id: string): Promise<Quote> {
  if (!isUuid(id)) throw new Error("Invalid quote identifier.");
  const response = await request(`/v1/report-quotes/${id}`, capability);
  if (response.status !== 200 && response.status !== 202) throw await errorFor(response);
  return validateQuote(await response.json());
}

export async function getReport(capability: string, id: string): Promise<Delivery | "payment-required" | "recovering"> {
  if (!isUuid(id)) throw new Error("Invalid report identifier.");
  const response = await request(`/v1/reports/${id}`, capability);
  if (response.status === 402) return "payment-required";
  if (response.status === 202) return "recovering";
  if (response.status !== 200) throw await errorFor(response);
  return validateDelivery(await response.json(), id);
}

export async function getEvidence(capability: string, id: string): Promise<Blob> {
  if (!isUuid(id)) throw new Error("Invalid report identifier.");
  const response = await request(`/v1/reports/${id}/evidence`, capability, { headers: { Accept: "application/zip" } });
  if (response.status !== 200) throw await errorFor(response);
  const type = response.headers.get("Content-Type")?.split(";")[0]?.trim();
  if (type !== "application/zip") throw new Error("Evidence response was not a ZIP bundle.");
  const blob = await response.blob();
  if (blob.size === 0 || blob.size > 10 * 1024 * 1024) throw new Error("Evidence bundle size is outside the permitted range.");
  return blob;
}
