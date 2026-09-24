import { MEZO_TESTNET, MUSD_TESTNET } from '@liqvera/mezo-protocol';
export const NETWORK = MEZO_TESTNET.caip2;
export const CHAIN_ID = MEZO_TESTNET.chainId;
export const ASSET = MUSD_TESTNET.address;
export const DECIMALS = MUSD_TESTNET.decimals;
export const AMOUNT = '10000000000000000' as const;
export const INSTRUMENT = 'hyperliquid:BTC:perpetual' as const;
export const RETENTION = Object.freeze({ paid_days: 7, unpaid_grace_seconds: 900, ledger_days: 30,
  authorization_validity_floor: true, deletion_must_not_enable_replay: true });
export const REASONS = ['INVALID_INPUT','INVALID_DATASET','STALE_SOURCE','CLOCK_SKEW','IDENTITY_UNVERIFIED',
  'IDENTITY_MISMATCH','CROSSED_BOOK','DEPTH_INSUFFICIENT','UNSUPPORTED_INSTRUMENT','SIMULATED_SOURCE',
  'SOURCE_UNAVAILABLE','STORAGE_UNAVAILABLE','PAYMENT_SERVICE_UNAVAILABLE','PAYMENT_NOT_READY',
  'PAY_TO_MISSING','FINALITY_RULE_UNVERIFIED','AUTHORIZATION_IDENTITY_UNVERIFIED','ARTIFACT_INTEGRITY_FAILURE',
  'UNAUTHORIZED','NOT_FOUND','IDEMPOTENCY_CONFLICT','INVALID_STATE','PAYMENT_REJECTED','AUTHORIZATION_REUSED',
  'QUOTE_EXPIRED','RETENTION_EXPIRED','RATE_LIMITED','PAYMENT_REQUIRED','PAYMENT_UNCERTAIN','MANUAL_REVIEW'] as const;
export type Reason = typeof REASONS[number];
export type RequestState = 'PREPARING' | 'READY' | 'REJECTED' | 'BUILD_FAILED';
export type QuoteState = 'READY' | 'PAYMENT_PENDING' | 'PAYMENT_UNCERTAIN' | 'PAID' | 'EXPIRED' | 'MANUAL_REVIEW';
export type AttemptState = 'RECEIVED' | 'VERIFIED' | 'SUBMITTING' | 'CONFIRMED' | 'REJECTED' | 'UNKNOWN' | 'MANUAL_REVIEW';
export interface QuoteInput { instrument_id: typeof INSTRUMENT; side: 'BUY' | 'SELL'; quantity_base: string; expected_payer: string }
export interface ReportRequest { id: string; scope_hash: string; canonical_body: QuoteInput; body_hash: string;
  state: RequestState; report_id: string; quote_id: string | null; reason: Reason | null; created_at: Date }
export interface Terms { version: 'mee-evidence-terms/v1'; network: typeof NETWORK; chain_id: typeof CHAIN_ID;
  asset: typeof ASSET; decimals: 18; amount_atomic: typeof AMOUNT; price_musd: '0.01'; pay_to: string;
  expected_payer: string; expires_at: string }
export interface Preview { instrument_id: typeof INSTRUMENT; side: 'BUY' | 'SELL'; quantity_base: string;
  snapshot_at: string; snapshot_status: 'VALID_FOR_SNAPSHOT_CALCULATION'; limitations: string[];
  price_musd: '0.01'; expires_at: string }
export interface Artifact { report_id: string; report_sha256: string; bundle_sha256: string;
  report_size_bytes: number; bundle_size_bytes: number; snapshot_at: string;
  snapshot_status: string; source_mode: 'live-public' | 'fixture'; limitations: string[] }
export interface Quote { id: string; report_request_id: string; scope_hash: string; report_id: string;
  report_sha256: string; bundle_sha256: string; state: QuoteState; terms: Terms; preview: Preview;
  expires_at: Date; artifact: Artifact }
export interface AuthorizationIdentity { identity: string; version: string; payer: string;
  valid_until: string; correlation: Record<string, string> }
export interface Attempt { id: string; quote_id: string; state: AttemptState; authorization_identity: string;
  identity_version: string; authorization_valid_until: Date; correlation: Record<string,string>;
  tx_hash: string | null; submitted_at: Date | null; reconciliation_count: number }
export interface Receipt { schema: 'mee-evidence-receipt/v1'; quote_id: string; report_id: string;
  payment_attempt_id: string; report_sha256: string; network: typeof NETWORK; chain_id: typeof CHAIN_ID;
  asset: typeof ASSET; amount_atomic: typeof AMOUNT; payer: string; pay_to: string;
  tx_hash: string; block_hash: string; block_number: number; log_index: number; confirmed_at: string;
  finality_policy_version: string }
export interface Confirmation { receipt: Receipt; response_header: string }
export class PublicError extends Error {
  constructor(public readonly code: Reason, public readonly status: number = 503) { super(code); }
}
export const isReason = (value: unknown): value is Reason => typeof value === 'string' && REASONS.includes(value as Reason);
export const shaPattern = /^[0-9a-f]{64}(?![\s\S])/;
export const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}(?![\s\S])/;
export function address(value: unknown): string {
  if (typeof value !== 'string' || value.length !== 42 || !/^0x[0-9a-fA-F]{40}$/.test(value) || /^0x0{40}$/.test(value))
    throw new PublicError('INVALID_INPUT', 422);
  return value.toLowerCase();
}
