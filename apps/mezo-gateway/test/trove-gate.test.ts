import assert from 'node:assert/strict';
import test from 'node:test';
import {Gateway} from '../src/application/gateway.js';
import {loadConfig} from '../src/config.js';
import {PublicError,type QuoteInput,type ReportRequest} from '../src/domain/model.js';
import {quoteInput} from '../src/security/input.js';
import type {Ledger} from '../src/adapters/postgres.js';
import type {Contracts} from '../src/adapters/contracts.js';
import type {ArtifactStore,PaymentPort,ReportService} from '../src/ports/index.js';
const input:QuoteInput={product_id:'trove_risk',borrower:'0xDA04759E54728B6636Fe48F7c9795c7B609bAaAa',expected_payer:'0x1111111111111111111111111111111111111111'};
const request={id:'123e4567-e89b-42d3-a456-426614174050',report_id:'123e4567-e89b-42d3-a456-426614174051',canonical_body:input,state:'PREPARING',quote_id:null,reason:null} as ReportRequest;
function fixture(enabled?:boolean,existing=false,dexEnabled=false){
 let creates=0;
 const ledger={pool:{query:async()=>({rows:existing?[request]:[],rowCount:0})},createRequest:async()=>{creates++;return request;}};
 const gateway=new Gateway(ledger as unknown as Ledger,{} as ReportService,{} as ArtifactStore,
   {blockers:()=>[]} as unknown as PaymentPort,{} as Contracts,
   {sourceMode:'live-public',payTo:'0x2222222222222222222222222222222222222222',...(enabled===undefined?{}:{troveRiskEnabled:enabled}),mezoDexEnabled:dexEnabled});
 return {gateway,creates:()=>creates};
}

test('new Trove creation is disabled by default before any ledger write',async()=>{
 const {gateway,creates}=fixture();
 await assert.rejects(()=>gateway.create('scope','key',input,'request'),(error:unknown)=>error instanceof PublicError&&error.code==='UNSUPPORTED_INSTRUMENT');
 assert.equal(creates(),0);
});
test('enabled Trove requests use the existing request preparation path',async()=>{
 const {gateway,creates}=fixture(true);assert.equal((await gateway.create('scope','key',input,'request')).status,202);assert.equal(creates(),1);
});
test('a disabled product keeps existing hash-bound request replays readable',async()=>{
 const {gateway,creates}=fixture(false,true);assert.equal((await gateway.create('scope','key',input,'request')).status,202);assert.equal(creates(),1);
});
test('Trove enable flag is strict and cannot enable a fixture payment product',async()=>{
 for(const value of ['1','TRUE','garbage'])await assert.rejects(()=>loadConfig({DATABASE_URL:'postgresql://localhost/unused',LIQVERA_MEZO_TROVES_ENABLED:value}),PublicError);
 await assert.rejects(()=>loadConfig({DATABASE_URL:'postgresql://localhost/unused',LIQVERA_MEZO_TROVES_ENABLED:'true',SOURCE_MODE:'fixture'}),PublicError);
});

test('DEX report enable flag is strict and Testnet live-public only',async()=>{
 for(const value of ['1','TRUE','garbage'])await assert.rejects(()=>loadConfig({DATABASE_URL:'postgresql://localhost/unused',LIQVERA_MEZO_DEX_ENABLED:value}),PublicError);
 await assert.rejects(()=>loadConfig({DATABASE_URL:'postgresql://localhost/unused',LIQVERA_MEZO_DEX_ENABLED:'true',SOURCE_MODE:'fixture'}),PublicError);
 const config=await loadConfig({DATABASE_URL:'postgresql://localhost/unused',LIQVERA_MEZO_DEX_ENABLED:'true',SOURCE_MODE:'live-public'});
 assert.equal(config.mezoDexEnabled,true);
});

test('Mezo DEX quote creation is rejected before ledger work unless gateway feature is enabled',async()=>{
 const dex=quoteInput({instrument_id:'hyperliquid:BTC:perpetual',side:'SELL',quantity_base:'1',expected_payer:'0x1111111111111111111111111111111111111111',mezo_dex:true});
 const disabled=fixture();
 await assert.rejects(()=>disabled.gateway.create('scope','dex-disabled',dex,'request'),(error:unknown)=>error instanceof PublicError&&error.code==='UNSUPPORTED_INSTRUMENT');
 assert.equal(disabled.creates(),0);
 const enabled=fixture(undefined,false,true);
 assert.equal((await enabled.gateway.create('scope','dex-enabled',dex,'request')).status,202);
 assert.equal(enabled.creates(),1);
});
