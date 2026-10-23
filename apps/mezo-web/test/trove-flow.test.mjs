import assert from 'node:assert/strict';
import test from 'node:test';
import {executeRecovery,executePaymentAttempt} from '../src/browser-orchestration.ts';
import {recoveryRequest} from '../src/browser-flow.ts';
import {loadFlow,saveFlow} from '../src/session.ts';
const borrower='0xDA04759E54728B6636Fe48F7c9795c7B609bAaAa';
const flow={version:2,product_id:'trove_risk',borrower,payer:'0x1111111111111111111111111111111111111111',
 idempotencyKey:'33333333-3333-4333-8333-333333333333',paymentGuard:'clear'};
const quote={quote_id:'11111111-1111-4111-8111-111111111111',report_id:'44444444-4444-4444-8444-444444444444',state:'READY'};

test('Trove recovery preserves product and borrower in an unacknowledged request',async()=>{
 const expected={product_id:'trove_risk',borrower,payer:flow.payer};
 assert.deepEqual(recoveryRequest(flow).body,expected);
 let sent;
 await executeRecovery(flow,{createQuote:async input=>{sent=input;return quote;},onQuote(){}});
 assert.deepEqual(sent,{...expected,idempotencyKey:flow.idempotencyKey});
});
test('Trove uncertain recovery performs GET only and recovers paid delivery',async()=>{
 const calls=[];
 await executeRecovery({...flow,quoteId:quote.quote_id,paymentGuard:'uncertain'}, {
  getQuote:async id=>{calls.push(['quote',id]);return {...quote,state:'PAID'};},
  getPaidDelivery:async id=>{calls.push(['delivery',id]);return {report:{}};},
  createQuote:async()=>assert.fail('recreated request'),onQuote(){},onDelivery(){},notice(){}
 });
 assert.deepEqual(calls,[['quote',quote.quote_id],['delivery',quote.report_id]]);
});
test('Trove session survives reload while legacy sessions keep their original representation',()=>{
 const values=new Map();globalThis.window={sessionStorage:{getItem:k=>values.get(k)??null,setItem:(k,v)=>values.set(k,v),removeItem:k=>values.delete(k)}};
 saveFlow(flow);assert.deepEqual(loadFlow(),flow);
 const legacy={version:1,side:'SELL',quantity:'0.15',payer:flow.payer,idempotencyKey:flow.idempotencyKey,paymentGuard:'uncertain'};
 saveFlow(legacy);assert.deepEqual(loadFlow(),legacy);
 saveFlow({...flow,side:'SELL',quantity:'1'});assert.equal(loadFlow(),null);
});
test('Trove ambiguous wallet outcome retains the same borrower and blocks another submission',async()=>{
 const saved=[];
 const next=await executePaymentAttempt(flow,quote,{
  validateWallet:async()=>{},requestPaidReport:async()=>{throw Error('lost response');},
  isPreSubmitCancellation:()=>false,persist:value=>saved.push(value),notice(){}
 });
 assert.equal(next.paymentGuard,'uncertain');assert.equal(next.borrower,borrower);assert.equal(next.version,2);
 assert.equal(saved[0].paymentGuard,'started');
});
