import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import test from 'node:test';
import {Gateway} from '../src/application/gateway.js';
import {Contracts} from '../src/adapters/contracts.js';
import {buildOne} from '../src/workers/builds.js';
import type {Ledger} from '../src/adapters/postgres.js';
import type {ArtifactStore,PaymentPort,ReportService} from '../src/ports/index.js';
import type {ReportRequest,Reason} from '../src/domain/model.js';

async function fixture(change?:(report:any,request:ReportRequest)=>void) {
 const contracts=await Contracts.load(new URL('../../dist/contracts/',import.meta.url));
 const report=JSON.parse(await readFile(new URL('../../../../evidence/mezo-testnet/2026-10-23-trove-risk-preview/report.json',import.meta.url),'utf8'));
 report.source.source_at=new Date().toISOString();
 const request={id:'123e4567-e89b-42d3-a456-426614174050',report_id:report.report_id,
  canonical_body:{product_id:'trove_risk',borrower:report.request.borrower,expected_payer:'0x1111111111111111111111111111111111111111'},state:'PREPARING',quote_id:null,reason:null} as ReportRequest;
 change?.(report,request);
 const artifact={report_id:report.report_id,source_mode:'live-public',snapshot_status:'VALID_FOR_SNAPSHOT_CALCULATION',
  snapshot_at:report.source.source_at,limitations:report.quality.limitations};
 let published:any=null,rejected:Reason|null=null;
 const ledger={claimBuild:async()=>request,publish:async(_r:any,_a:any,_p:any,_e:any,preview:any)=>{published=preview;},
  rejectBuild:async(_id:string,reason:Reason)=>{rejected=reason;}};
 const gateway=new Gateway(ledger as unknown as Ledger,{build:async()=>artifact} as unknown as ReportService,
  {read:async(_a:any,kind:string)=>kind==='report'?Buffer.from(JSON.stringify(report)):Buffer.from('bundle')} as unknown as ArtifactStore,
  {blockers:()=>[]} as unknown as PaymentPort,contracts,{sourceMode:'live-public',payTo:'0x2222222222222222222222222222222222222222',troveRiskEnabled:true});
 await buildOne(gateway);return {published,rejected};
}
test('Trove worker publishes borrower and active status through the existing quote path',async()=>{
 const result=await fixture();assert.equal(result.rejected,null);assert.equal(result.published.product_id,'trove_risk');
 assert.equal(result.published.borrower,'0xDA04759E54728B6636Fe48F7c9795c7B609bAaAa');assert.equal(result.published.trove_status,'ACTIVE');
 assert.equal('side' in result.published,false);assert.equal(result.published.price_musd,'0.01');
});
test('Trove worker rejects a substituted borrower before sale',async()=>{
 const result=await fixture(report=>{report.request.borrower='0x1111111111111111111111111111111111111111';});
 assert.equal(result.published,null);assert.equal(result.rejected,'IDENTITY_MISMATCH');
});
test('Trove evidence cannot fulfill a market quote',async()=>{
 const result=await fixture((_report,request)=>{request.canonical_body={instrument_id:'hyperliquid:BTC:perpetual',side:'SELL',quantity_base:'1',expected_payer:'0x1111111111111111111111111111111111111111'};});
 assert.equal(result.published,null);assert.equal(result.rejected,'IDENTITY_MISMATCH');
});
