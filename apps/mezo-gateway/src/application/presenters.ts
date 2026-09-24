import { AMOUNT, ASSET, INSTRUMENT, NETWORK, RETENTION, type Quote, type Reason, type ReportRequest } from '../domain/model.js';
export function quoteResource(quote: Quote,requestId: string) {
  return {schema:'mee-evidence-quote/v1',request_id:requestId,report_request_id:quote.report_request_id,quote_id:quote.id,
    report_id:quote.report_id,report_sha256:quote.report_sha256,bundle_sha256:quote.bundle_sha256,state:quote.state,
    preview:quote.preview,terms:quote.terms,retention:RETENTION};
}
export function requestResource(request: ReportRequest,requestId: string) {
  const base={schema:'mee-evidence-request-status/v1',request_id:requestId,report_request_id:request.id,
    status_location:`/v1/report-requests/${request.id}`,state:request.state};
  if(request.state==='READY')return {...base,quote_id:request.quote_id};
  if(request.state==='REJECTED'||request.state==='BUILD_FAILED')return {...base,reason:request.reason};
  return base;
}
const messages: Partial<Record<Reason,string>>={
  UNAUTHORIZED:'Authorization required.',NOT_FOUND:'Resource not found.',PAYMENT_REQUIRED:'Payment required for this report.',
  PAYMENT_UNCERTAIN:'Checking the payment already submitted.',MANUAL_REVIEW:'The existing payment requires operator review.',
  QUOTE_EXPIRED:'This unpaid quote has expired.',IDEMPOTENCY_CONFLICT:'This idempotency key is bound to a different request.',
  PAYMENT_NOT_READY:'Testnet payment is not ready.',SIMULATED_SOURCE:'Fixture reports cannot be sold.',
  ARTIFACT_INTEGRITY_FAILURE:'The retained artifact is unavailable or failed integrity verification.',
  RATE_LIMITED:'Request budget exceeded. Try again after the stated delay.'
};
export const errorResource=(code: Reason,requestId: string)=>({schema:'mee-evidence-error/v1',request_id:requestId,code,message:messages[code]??'The request cannot be completed safely.'});
export function capabilitiesResource(requestId: string,sourceMode: 'fixture'|'live-public',blockers: Reason[]) {
  return {schema:'mee-evidence-capabilities/v1',request_id:requestId,instrument_id:INSTRUMENT,
    instrument_label:'Hyperliquid BTC linear perpetual',network:NETWORK,asset:ASSET,decimals:18,price_musd:'0.01',amount_atomic:AMOUNT,
    source_mode:sourceMode,limitations:['Testnet only. Read-only analytics.',
      'Calculation over the available snapshot depth; this is not a complete exchange book or guaranteed execution.',
      'Fees, funding, and net P&L are not calculated.'],payment_ready:blockers.length===0,blockers};
}
