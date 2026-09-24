import { PublicError, type Quote, type QuoteInput, type Reason, type ReportRequest } from '../domain/model.js';
import type { ArtifactStore, PaymentPort, ReportService } from '../ports/index.js';
import { Ledger } from '../adapters/postgres.js';
import { Contracts } from '../adapters/contracts.js';
import { capabilitiesResource, errorResource, quoteResource, requestResource } from './presenters.js';
import { metrics } from '../security/observability.js';
export interface GatewayConfig { payTo: string|null; sourceMode:'fixture'|'live-public' }
export interface ApiResult { status:number; body?:unknown; bytes?:Buffer; headers?:Record<string,string>; shape?:string }
export class Gateway {
  constructor(readonly ledger:Ledger,readonly reports:ReportService,readonly artifacts:ArtifactStore,
    readonly payment:PaymentPort,readonly contracts:Contracts,readonly config:GatewayConfig) {}
  blockers():Reason[] {
    return [...new Set<Reason>([...this.payment.blockers(),...(!this.config.payTo?['PAY_TO_MISSING' as const]:[]),
      ...(this.config.sourceMode==='fixture'?['SIMULATED_SOURCE' as const]:[])])];
  }
  async readiness(requestId:string):Promise<ApiResult> {
    const [database,artifacts,reportHealthy]=await Promise.all([this.ledger.healthy(),this.artifacts.healthy(),this.reports.healthy()]);
    const integration=reportHealthy&&this.reports.cleanupReady();
    const blockers=this.blockers();const storage=database&&artifacts;
    if(!storage)blockers.push('STORAGE_UNAVAILABLE');
    if(!integration)blockers.push('SOURCE_UNAVAILABLE');
    if(database&&!await this.salesHealthy())blockers.push('ARTIFACT_INTEGRITY_FAILURE');
    const unique=[...new Set(blockers)];const payment=unique.length===0;
    metrics.readiness(payment);
    return {status:storage&&integration&&payment?200:503,shape:'readiness',body:{schema:'mee-evidence-readiness/v1',request_id:requestId,
      ready:storage&&integration&&payment,storage_ready:storage,integration_ready:integration,configuration_ready:!!this.config.payTo,
      payment_ready:payment,blockers:unique}};
  }
  async capabilities(requestId:string):Promise<ApiResult> {
    const blockers=this.blockers();
    if(!await this.ledger.healthy())blockers.push('STORAGE_UNAVAILABLE');
    else if(!await this.salesHealthy())blockers.push('ARTIFACT_INTEGRITY_FAILURE');
    return {status:200,shape:'capabilities',body:capabilitiesResource(requestId,this.config.sourceMode,[...new Set(blockers)])};
  }
  private async salesHealthy():Promise<boolean> {
    return !(await this.ledger.pool.query("SELECT 1 FROM artifacts WHERE storage_state='RECOVERY' LIMIT 1")).rowCount;
  }
  async create(scope:string,key:string,body:QuoteInput,requestId:string):Promise<ApiResult> {
    // Replays are readable even if external readiness has since changed.
    const existing=(await this.ledger.pool.query<ReportRequest>('SELECT * FROM report_requests WHERE scope_hash=$1 AND idempotency_key=$2',[scope,key])).rows[0];
    if(!existing) {
      if(this.config.sourceMode==='fixture')throw new PublicError('SIMULATED_SOURCE',422);
      if(this.blockers().length||!await this.salesHealthy())throw new PublicError('PAYMENT_NOT_READY');
      if(body.expected_payer===this.config.payTo)throw new PublicError('INVALID_INPUT',422);
    }
    const request=await this.ledger.createRequest(scope,key,body);
    if(request.state==='READY') {
      const quote=await this.ledger.quote(scope,request.quote_id!);
      return {status:201,shape:'quote',headers:{Location:`/v1/report-quotes/${quote.id}`},body:quoteResource(quote,requestId)};
    }
    if(request.state==='REJECTED')throw new PublicError(request.reason??'INVALID_DATASET',422);
    if(request.state==='BUILD_FAILED')throw new PublicError(request.reason??'SOURCE_UNAVAILABLE',503);
    return this.presentRequest(request,requestId);
  }
  private presentRequest(request:ReportRequest,requestId:string):ApiResult {
    return {status:request.state==='PREPARING'?202:200,shape:'request_status',body:requestResource(request,requestId),
      ...(request.state==='PREPARING'?{headers:{Location:`/v1/report-requests/${request.id}`}}:{})};
  }
  async status(scope:string,id:string,requestId:string):Promise<ApiResult> {
    return this.presentRequest(await this.ledger.request(scope,id),requestId);
  }
  private async expiry(quote:Quote):Promise<void> {
    if(quote.state==='EXPIRED')throw new PublicError('QUOTE_EXPIRED',410);
    if(quote.state==='READY'&&quote.expires_at.getTime()<=Date.now()) {
      await this.ledger.expire(quote);throw new PublicError('QUOTE_EXPIRED',410);
    }
  }
  async quote(scope:string,id:string,requestId:string):Promise<ApiResult> {
    const quote=await this.ledger.quote(scope,id);await this.expiry(quote);
    return {status:['PAYMENT_PENDING','PAYMENT_UNCERTAIN','MANUAL_REVIEW'].includes(quote.state)?202:200,
      shape:'quote',body:quoteResource(quote,requestId)};
  }
  async read(scope:string,reportId:string,kind:'report'|'bundle',signature:string|undefined,requestId:string):Promise<ApiResult> {
    let quote=await this.ledger.quote(scope,reportId,true);await this.expiry(quote);
    if(['PAYMENT_PENDING','PAYMENT_UNCERTAIN','MANUAL_REVIEW'].includes(quote.state))
      throw new PublicError(quote.state==='MANUAL_REVIEW'?'MANUAL_REVIEW':'PAYMENT_UNCERTAIN',202);
    if(quote.state==='READY') {
      if(this.blockers().length || !await this.salesHealthy())throw new PublicError('PAYMENT_NOT_READY');
      await Promise.all([this.artifacts.read(quote.artifact,'report'),this.artifacts.read(quote.artifact,'bundle')]);
      if(!signature||kind==='bundle') {
        const required=await this.payment.requirements(quote);
        metrics.increment('payment_required');
        return {status:402,shape:'error',headers:{'PAYMENT-REQUIRED':required.header},body:errorResource('PAYMENT_REQUIRED',requestId)};
      }
      const verified=await this.payment.verify(signature,quote);
      metrics.increment('payment_verified');
      this.contracts.states.next('quote',quote.state,'authorization_accepted',{
        not_expired:quote.expires_at.getTime()>Date.now(),scope_matches:true,payer_matches:verified.identity.payer===quote.terms.expected_payer,
        terms_match:true,artifact_readback_verified:true,payment_bindings_verified:this.blockers().length===0,no_active_attempt:true,authorization_unique:true});
      const attempt=await this.ledger.beginAttempt(quote,verified.identity);
      await Promise.all([this.artifacts.read(quote.artifact,'report'),this.artifacts.read(quote.artifact,'bundle')]);
      // The durable SUBMITTING boundary precedes the sole external settle call.
      // No recovery or HTTP replay path ever calls settle for this attempt.
      if(!await this.ledger.markSubmitting(attempt))throw new PublicError('QUOTE_EXPIRED',410);
      let txHash:string|null=null;
      try {
        const result=await this.payment.settle(verified.payload,verified.requirements);txHash=result.tx_hash;
        await this.ledger.unknown(attempt,txHash);
        const confirmation=await this.payment.confirm(quote,{...attempt,state:'UNKNOWN',tx_hash:txHash});
        if(!confirmation)throw new PublicError('PAYMENT_UNCERTAIN',202);
        this.contracts.assert('receipt',confirmation.receipt);
        await this.ledger.confirm(quote,attempt,confirmation);
        metrics.increment('payment_settled');
      } catch(error) {
        await this.ledger.unknown(attempt,txHash);
        if(error instanceof PublicError&&error.code==='MANUAL_REVIEW')await this.ledger.manualReview(quote,attempt);
        throw new PublicError('PAYMENT_UNCERTAIN',202);
      }
      quote=await this.ledger.quote(scope,reportId,true);
    }
    if(quote.state!=='PAID')throw new PublicError('PAYMENT_UNCERTAIN',202);
    const entitlement=await this.ledger.confirmation(quote);
    if(!entitlement||entitlement.attempt.state!=='CONFIRMED')throw new PublicError('PAYMENT_UNCERTAIN',202);
    if(entitlement.retain_until.getTime()<=Date.now())throw new PublicError('RETENTION_EXPIRED',410);
    let current=false;
    try {current=await this.payment.revalidate(quote,entitlement.attempt,entitlement.confirmation.receipt);}
    catch(error) {
      if(error instanceof PublicError&&error.code==='MANUAL_REVIEW')await this.ledger.manualReview(quote,entitlement.attempt);
      throw new PublicError('PAYMENT_UNCERTAIN',202);
    }
    if(!current) {await this.ledger.manualReview(quote,entitlement.attempt);throw new PublicError('MANUAL_REVIEW',202);}
    let bytes:Buffer;
    try {bytes=await this.artifacts.read(quote.artifact,kind);} catch {
      await this.ledger.pool.query("UPDATE artifacts SET storage_state='RECOVERY' WHERE report_id=$1",[quote.report_id]);
      await this.ledger.pool.query("INSERT INTO audit_events(quote_id,event) VALUES($1,'ARTIFACT_INTEGRITY_FAILURE')",[quote.id]);
      throw new PublicError('ARTIFACT_INTEGRITY_FAILURE',202);
    }
    this.contracts.states.next('delivery','NOT_ATTEMPTED','delivery_started',{quote_is_paid:true,attempt_is_confirmed:true,
      current_finality_verified:true,no_chain_inconsistency:true,entitlement_matches_digest:true,storage_integrity_verified:true});
    await this.ledger.recordDelivery(quote,kind,requestId);
    const headers={'PAYMENT-RESPONSE':entitlement.confirmation.response_header};
    if(kind==='bundle')return {status:200,bytes,headers:{...headers,'Content-Type':'application/zip','Content-Disposition':`attachment; filename="${quote.report_id}.zip"`}};
    const report:unknown=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));this.contracts.assert('report',report);
    const body={schema:'mee-evidence-delivery/v1',request_id:requestId,report,receipt:entitlement.confirmation.receipt};
    // Keep the immutable report's original bytes inside the delivery envelope.
    // Digest verification never relies on parsing and reserializing JSON.
    const prefix=JSON.stringify({schema:body.schema,request_id:requestId}).slice(0,-1)+',"report":';
    const envelope=Buffer.concat([Buffer.from(prefix),bytes,Buffer.from(',"receipt":'+JSON.stringify(body.receipt)+'}')]);
    return {status:200,shape:'paid_report',headers:{...headers,'Content-Type':'application/json; charset=utf-8'},body,bytes:envelope};
  }
}
