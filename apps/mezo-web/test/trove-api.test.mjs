import assert from 'node:assert/strict';
import test from 'node:test';
import {createQuote,getQuote} from '../src/api.ts';
import {ASSET,NETWORK,CHAIN_ID} from '../src/contracts.ts';
const borrower='0xDA04759E54728B6636Fe48F7c9795c7B609bAaAa';
const payer='0x1111111111111111111111111111111111111111';
const id='11111111-1111-4111-8111-111111111111';
const status={schema:'liqvera-evidence-request-status/v1',report_request_id:id,status_location:`/v1/report-requests/${id}`,state:'PREPARING'};
test('browser sends a closed Trove body while legacy body bytes remain unchanged',async t=>{
 const bodies=[];t.mock.method(globalThis,'fetch',async(_path,options)=>{bodies.push(options.body);return new Response(JSON.stringify(status),{status:202});});
 await createQuote('cap',{product_id:'trove_risk',borrower,payer,idempotencyKey:id});
 await createQuote('cap',{side:'SELL',quantity:'1',payer,idempotencyKey:id});
 assert.equal(bodies[0],JSON.stringify({product_id:'trove_risk',borrower,expected_payer:payer}));
 assert.equal(bodies[1],JSON.stringify({instrument_id:'hyperliquid:BTC:perpetual',side:'SELL',quantity_base:'1',expected_payer:payer}));
});
test('browser recognizes a borrower-bound Trove quote without allowing mixed market fields',async t=>{
 const expires=new Date(Date.now()+60_000).toISOString();
 const quote={schema:'liqvera-evidence-quote/v1',quote_id:id,report_request_id:id,report_id:id,report_sha256:'a'.repeat(64),bundle_sha256:'b'.repeat(64),state:'READY',
  preview:{product_id:'trove_risk',borrower,trove_status:'ACTIVE',snapshot_at:new Date().toISOString(),snapshot_status:'VALID_FOR_SNAPSHOT_CALCULATION',price_musd:'0.01',expires_at:expires,limitations:[]},
  terms:{version:'liqvera-evidence-terms/v1',network:NETWORK,chain_id:CHAIN_ID,asset:ASSET,decimals:18,amount_atomic:'10000000000000000',price_musd:'0.01',pay_to:payer,expected_payer:payer,expires_at:expires},
  retention:{paid_days:7,unpaid_grace_seconds:900,ledger_days:30,authorization_validity_floor:true,deletion_must_not_enable_replay:true}};
 t.mock.method(globalThis,'fetch',async()=>new Response(JSON.stringify(quote),{status:200}));
 assert.equal((await getQuote('cap',id)).preview.borrower,borrower);
 quote.preview.side='SELL';await assert.rejects(getQuote('cap',id));
});

test('delivery subject must match the paid quote product and borrower',async()=>{
 const {reportMatchesQuote}=await import('../src/contracts.ts');
 const quote={preview:{product_id:'trove_risk',borrower}};
 const report={schema:'liqvera-trove-risk-report/v1',request:{product_id:'trove_risk',borrower}};
 assert.equal(reportMatchesQuote(report,quote),true);
 assert.equal(reportMatchesQuote({...report,request:{...report.request,borrower:payer}},quote),false);
 assert.equal(reportMatchesQuote({schema:'liqvera-evidence-report/v1',request:{side:'SELL',quantity_base:'1'}},quote),false);
});

for(const products of ['trove_risk',{},['unknown'],['trove_risk','trove_risk']])
 test(`capability product declaration fails closed: ${JSON.stringify(products)}`,async t=>{
  const {getCapabilities}=await import('../src/api.ts');
  t.mock.method(globalThis,'fetch',async()=>new Response(JSON.stringify({schema:'liqvera-evidence-capabilities/v1',
   instrument_id:'hyperliquid:BTC:perpetual',network:NETWORK,asset:ASSET,decimals:18,price_musd:'0.01',amount_atomic:'10000000000000000',
   source_mode:'live-public',payment_ready:true,limitations:[],blockers:[],products}),{status:200}));
  await assert.rejects(getCapabilities());
 });

test('paid Trove parser retains full receipt finality and sponsored-gas guards',async()=>{
 const {readFile}=await import('node:fs/promises');
 const {validateDelivery}=await import('../src/api.ts');
 const report=JSON.parse(await readFile(new URL('../../../evidence/mezo-testnet/2026-10-23-trove-risk-preview/report.json',import.meta.url),'utf8'));
 const hash='0x'+'a'.repeat(64);
 const receipt={schema:'liqvera-evidence-receipt/v1',quote_id:id,report_id:report.report_id,report_sha256:'b'.repeat(64),network:NETWORK,chain_id:CHAIN_ID,
  asset:ASSET,amount_atomic:'10000000000000000',payer,pay_to:payer,tx_hash:hash,block_hash:hash,transaction_from:borrower,
  buyer_native_balance_before:'1000',buyer_native_balance_after:'1000',buyer_native_gas_spent:'0',observation_before_block_number:1,
  observation_before_block_hash:hash,observation_after_block_number:2,observation_after_block_hash:hash,authorization_identity:'c'.repeat(64),
  confirmations:12,transfer_identity:'d'.repeat(64),block_number:2,log_index:0,confirmed_at:'2026-10-23T18:02:00Z',finality_policy_version:'stub-test/v1'};
 const delivery={schema:'liqvera-evidence-delivery/v1',report,receipt};
 assert.equal(validateDelivery(delivery,report.report_id),delivery);
 for(const patch of [{confirmations:11},{buyer_native_balance_after:'999'},{amount_atomic:'1'},{chain_id:31612}])
  assert.throws(()=>validateDelivery({...delivery,receipt:{...receipt,...patch}},report.report_id));
});
