import type { ReportService } from '../ports/index.js';
import { INSTRUMENT, PublicError, isReason, shaPattern, uuidPattern, type Artifact, type QuoteInput } from '../domain/model.js';
import { boundedJson } from './http.js';
export class HttpReportService implements ReportService {
  constructor(private readonly base: URL,private readonly token: string|null=null) {}
  private headers():Record<string,string> {return this.token?{Authorization:`Bearer ${this.token}`}:{ };}
  async healthy(): Promise<boolean> {
    try { const result=await boundedJson(new URL('/healthz',this.base),{method:'GET',headers:this.headers()},4096,1500);
      return !!result && typeof result==='object'; } catch { return false; }
  }
  async build(reportId: string, input: QuoteInput, signal: AbortSignal): Promise<Artifact> {
    const value=await boundedJson(new URL('/internal/v1/reports',this.base),{method:'POST',signal,headers:this.headers(),
      body:JSON.stringify({report_id:reportId,instrument_id:INSTRUMENT,side:input.side,quantity_base:input.quantity_base})},65536,15000,[422,503]);
    if (!value || typeof value !== 'object') throw new PublicError('INVALID_DATASET',422);
    const raw=value as Record<string,unknown>;
    if (isReason(raw.code)) throw new PublicError(raw.code,422);
    if (raw.report_id!==reportId || typeof raw.report_sha256!=='string' || !shaPattern.test(raw.report_sha256) ||
      typeof raw.bundle_sha256!=='string' || !shaPattern.test(raw.bundle_sha256) || typeof raw.snapshot_at!=='string' ||
      !Number.isFinite(Date.parse(raw.snapshot_at)) || typeof raw.snapshot_status!=='string' ||
      !['fixture','live-public'].includes(String(raw.source_mode)) || !Array.isArray(raw.limitations) ||
      raw.limitations.length<1 || raw.limitations.length>32 || raw.limitations.some(x=>typeof x!=='string'||x.length===0) ||
      !Number.isInteger(raw.report_size_bytes) || !Number.isInteger(raw.bundle_size_bytes)) throw new PublicError('INVALID_DATASET',422);
    // Project a closed metadata object; ignore service paths and unknown fields.
    return { report_id:reportId,report_sha256:raw.report_sha256,bundle_sha256:raw.bundle_sha256,
      report_size_bytes:raw.report_size_bytes as number,bundle_size_bytes:raw.bundle_size_bytes as number,
      snapshot_at:raw.snapshot_at,snapshot_status:raw.snapshot_status,source_mode:raw.source_mode as Artifact['source_mode'],limitations:raw.limitations as string[] };
  }
  async recover(_artifact: Artifact, _signal: AbortSignal): Promise<boolean> {
    // A reviewed sealed-input recovery endpoint must guarantee the old digest.
    // Its absence is explicit: never rebuild using a fresh market snapshot.
    return false;
  }
  cleanupReady():boolean {return !!this.token;}
  async cleanup(reportId:string,signal:AbortSignal):Promise<boolean> {
    if(!this.cleanupReady()||!uuidPattern.test(reportId))return false;
    const value=await boundedJson(new URL(`/internal/v1/reports/${reportId}`,this.base),{method:'DELETE',signal,headers:this.headers()},4096,2000);
    if(!value||typeof value!=='object')return false;
    const body=value as Record<string,unknown>;
    return body.report_id===reportId&&body.deleted===true;
  }
}
