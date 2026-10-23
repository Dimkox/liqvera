import {CHAIN_ID,isAddress} from './contracts.ts';
import type {TroveReport} from './contracts.ts';

/** Local rendering checks supplement the hash-bound report and offline verifier. */
export function validateTroveReport(value: unknown): TroveReport {
  const report=value as TroveReport;
  const risk=report?.trove_risk;
  const decimal=(v:unknown)=>typeof v==='string'&&v.length<=100&&/^-?(0|[1-9][0-9]*)(\.[0-9]+)?$/.test(v);
  const nullable=(v:unknown)=>v===null||decimal(v);
  const strings=(v:unknown)=>Array.isArray(v)&&v.every(item=>typeof item==='string');
  if(CHAIN_ID!==31611||!risk||report.schema!=='liqvera-trove-risk-report/v1'||report.request?.product_id!=='trove_risk'||
    !isAddress(report.request.borrower)||risk.borrower.toLowerCase()!==report.request.borrower.toLowerCase()||
    !['ACTIVE','NOT_ACTIVE'].includes(risk.status)||
    ![risk.debt_musd,risk.collateral_btc,risk.price_musd,risk.mcr,risk.ccr,risk.tcr].every(decimal)||
    ![risk.icr,risk.liquidation_price_musd,risk.buffer_pct,risk.debt_ahead_musd].every(nullable)||
    typeof risk.block_number!=="string"||typeof risk.block_hash!=="string"||
    !/^[1-9][0-9]*$/.test(risk.block_number)||!/^0x[0-9a-f]{64}$/.test(risk.block_hash)||
    !Number.isSafeInteger(risk.sorted_troves_size)||risk.sorted_troves_size<0||
    !(risk.redemption_position===null||(Number.isSafeInteger(risk.redemption_position)&&risk.redemption_position>=1&&risk.redemption_position<=risk.sorted_troves_size))||
    typeof risk.queue_status!=='string'||!strings(risk.caveats)||
    !Array.isArray(risk.scenarios)||risk.scenarios.length!==3||risk.scenarios.some((s,index)=>
      s.price_change_pct!==['-10','-20','-30'][index]||!decimal(s.price_musd)||!nullable(s.icr)||typeof s.status!=='string')||
    report.source?.source_mode!=='live-public'||!Number.isFinite(Date.parse(report.source.source_at))||
    !strings(report.quality?.limitations)||!strings(report.quality?.reason_codes)||
    report.boundaries?.execution_authority!=='NONE'||report.boundaries.execution_promise!==false)
    throw new Error('Trove report failed local integrity checks.');
  return report;
}
