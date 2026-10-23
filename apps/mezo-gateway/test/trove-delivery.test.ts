import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import test from 'node:test';
import {Gateway} from '../src/application/gateway.js';
import {Contracts} from '../src/adapters/contracts.js';
import type {Ledger} from '../src/adapters/postgres.js';
import type {ArtifactStore,PaymentPort,ReportService} from '../src/ports/index.js';

test('paid historical Trove delivery preserves bytes with creation disabled and never rebuilds or resettles',async()=>{
 const contracts=await Contracts.load(new URL('../../dist/contracts/',import.meta.url));
 const bytes=await readFile(new URL('../../../../evidence/mezo-testnet/2026-10-23-trove-risk-preview/report.json',import.meta.url));
 const report=JSON.parse(bytes.toString('utf8'));
 // Payment finality is stubbed here; native payment guards have their separate suite.
 const quote={state:'PAID',report_id:report.report_id,artifact:{},expires_at:new Date(0)};
 const deliveries:string[]=[];let finality=0;
 const ledger={quote:async()=>quote,confirmation:async()=>({attempt:{state:'CONFIRMED'},retain_until:new Date(Date.now()+60_000),
  confirmation:{receipt:{report_id:report.report_id},response_header:'stub-finality-response'}}),
  recordDelivery:async(_q:unknown,kind:string)=>{deliveries.push(kind);}};
 const gateway=new Gateway(ledger as unknown as Ledger,{build:async()=>assert.fail('recaptured paid report')} as unknown as ReportService,
  {read:async()=>bytes} as unknown as ArtifactStore,
  {revalidate:async()=>{finality++;return true;},requirements:async()=>assert.fail('new payment requirement'),settle:async()=>assert.fail('resettled')} as unknown as PaymentPort,
  contracts,{sourceMode:'live-public',payTo:null,troveRiskEnabled:false});
 const result=await gateway.read('scope',report.report_id,'report',undefined,'request');
 assert.equal(result.status,200);assert.equal(finality,1);assert.deepEqual(deliveries,['report']);
 const envelope=result.bytes!;assert.ok(envelope.includes(bytes));
 assert.deepEqual(JSON.parse(envelope.toString('utf8')).report,report);
});
