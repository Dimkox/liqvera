import { INSTRUMENT, PublicError, type Reason } from '../domain/model.js';
import { Gateway } from '../application/gateway.js';
import { metrics } from '../security/observability.js';
const rejectedReasons:Reason[]=['MEZO_DEX_INVALID_EVIDENCE','INVALID_INPUT','INVALID_DATASET','STALE_SOURCE','CLOCK_SKEW','IDENTITY_UNVERIFIED',
  'IDENTITY_MISMATCH','CROSSED_BOOK','DEPTH_INSUFFICIENT','UNSUPPORTED_INSTRUMENT','SIMULATED_SOURCE'];
export const MAX_SALE_AGE_MS=30_000;
export function assertSaleFresh(snapshotAt:string,now=Date.now()):void {
  const age=now-Date.parse(snapshotAt);
  if(age>MAX_SALE_AGE_MS)throw new PublicError('STALE_SOURCE',422);
  if(age < -1000)throw new PublicError('CLOCK_SKEW',422);
}
export async function buildOne(gateway:Gateway):Promise<boolean> {
  const request=await gateway.ledger.claimBuild();if(!request)return false;
  const started=performance.now();
  const signal=AbortSignal.timeout(15000);
  try {
    const artifact=await gateway.reports.build(request.report_id,request.canonical_body,signal);
    const [reportBytes]=await Promise.all([gateway.artifacts.read(artifact,'report'),gateway.artifacts.read(artifact,'bundle')]);
    const report=JSON.parse(reportBytes.toString('utf8'));gateway.contracts.assert('report',report);
    const trove=request.canonical_body.product_id==='trove_risk';
    if(artifact.report_id!==request.report_id||report.report_id!==request.report_id)throw new PublicError('IDENTITY_MISMATCH',422);
    if(trove) {
      if(report.schema!=='liqvera-trove-risk-report/v1'||report.request.product_id!=='trove_risk'||
         report.request.borrower!==request.canonical_body.borrower)throw new PublicError('IDENTITY_MISMATCH',422);
    } else if(report.schema!=='liqvera-evidence-report/v1'||report.request.side!==request.canonical_body.side||
      report.request.quantity_base!==request.canonical_body.quantity_base||report.identity.instrument_id!==INSTRUMENT)
      throw new PublicError('IDENTITY_MISMATCH',422);
    if(request.canonical_body.product_id!=='trove_risk'&&request.canonical_body.mezo_dex===true&&
      (report.request.mezo_dex!==true||!report.mezo_dex||report.mezo_dex.match!==true))throw new PublicError('IDENTITY_MISMATCH',422);
    if(report.quality.snapshot_status==='REJECTED') {
      const reason=report.quality.reason_codes.find((r:Reason)=>rejectedReasons.includes(r))??'INVALID_DATASET';throw new PublicError(reason,422);
    }
    if(artifact.source_mode!=='live-public'||report.source.source_mode!=='live-public'||report.quality.snapshot_status==='SIMULATED')throw new PublicError('SIMULATED_SOURCE',422);
    if(artifact.snapshot_status!=='VALID_FOR_SNAPSHOT_CALCULATION'||report.quality.snapshot_status!=='VALID_FOR_SNAPSHOT_CALCULATION'||
      report.quality.reason_codes.length!==0||report.quality.checks.some((c:{result:string})=>c.result!=='PASS')||
      artifact.snapshot_at!==report.source.source_at)throw new PublicError('INVALID_DATASET',422);
    // Current freshness is checked once for sale. Paid historical delivery uses
    // the immutable original snapshot and never recalculates market data.
    assertSaleFresh(artifact.snapshot_at);
    if(signal.aborted)throw new PublicError('SOURCE_UNAVAILABLE');
    if(gateway.blockers().length||!gateway.config.payTo)throw new PublicError('SOURCE_UNAVAILABLE');
    gateway.contracts.states.next('report_request','PREPARING','artifact_verified',{semantic_report_valid:true,live_source:true,
      immutable_publish_complete:true,report_and_bundle_readback_verified:true});
    const expires=new Date(Date.now()+120000);
    const common={snapshot_at:artifact.snapshot_at,snapshot_status:'VALID_FOR_SNAPSHOT_CALCULATION' as const,
      limitations:artifact.limitations,price_musd:'0.01' as const,expires_at:expires.toISOString()};
    const preview=request.canonical_body.product_id==='trove_risk'?
      {...common,product_id:'trove_risk' as const,borrower:request.canonical_body.borrower,trove_status:report.trove_risk.status}:
      {instrument_id:INSTRUMENT,side:request.canonical_body.side,quantity_base:request.canonical_body.quantity_base,
        ...(request.canonical_body.mezo_dex===true?{mezo_dex:true as const}:{}),...common};
    await gateway.ledger.publish(request,artifact,gateway.config.payTo,expires,preview);
    metrics.increment('build_complete');
  } catch(error) {
    const reason=error instanceof PublicError?error.code:'SOURCE_UNAVAILABLE';const rejected=rejectedReasons.includes(reason);
    await gateway.ledger.rejectBuild(request.id,rejected?reason:['MEZO_SOURCE_UNAVAILABLE','STORAGE_UNAVAILABLE','ARTIFACT_INTEGRITY_FAILURE'].includes(reason)?reason:'SOURCE_UNAVAILABLE',rejected);
    metrics.increment('build_rejected');
  } finally {metrics.observe('build',(performance.now()-started)/1000);}
  return true;
}
