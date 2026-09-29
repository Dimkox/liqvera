import assert from 'node:assert/strict';
import test from 'node:test';
import type { PaymentPayload } from '@x402/core/types';
import { AMOUNT, ASSET, NETWORK, PublicError, type Attempt, type Quote } from '../src/domain/model.js';
import { MezoAuthorizationPolicy, MezoFinalityPolicy } from '../src/security/payment-policy.js';
import { LivePaymentGrant } from '../src/security/live-grant.js';

const payer='0x1111111111111111111111111111111111111111';
const payTo='0x2222222222222222222222222222222222222222';
const quote={id:'00000000-0000-4000-8000-000000000001',report_id:'00000000-0000-4000-8000-000000000002',report_sha256:'a'.repeat(64),terms:{expected_payer:payer,pay_to:payTo}} as Quote;
function payload(): PaymentPayload { return {x402Version:2,accepted:{scheme:'exact',network:NETWORK,asset:ASSET,amount:AMOUNT,payTo},payload:{signature:`0x${'1'.repeat(130)}`,authorization:{from:payer,to:payTo,value:AMOUNT,validAfter:'0',validBefore:'1790640300',nonce:`0x${'2'.repeat(64)}`}}} as unknown as PaymentPayload; }

test('authorization identity binds exact EIP-3009 terms and nonce',async()=>{
  const policy=new MezoAuthorizationPolicy(()=>new Date('2026-09-29T00:00:00Z'));
  const identity=policy.identify(payload(),quote);
  assert.equal(identity.payer,payer); assert.equal(identity.version,policy.version);
  assert.match(identity.identity,/^[0-9a-f]{64}$/);
  const attempt={authorization_identity:identity.identity,identity_version:identity.version,correlation:identity.correlation,tx_hash:`0x${'3'.repeat(64)}`} as Attempt;
  assert.equal(await policy.bindsTransfer(attempt,{hash:attempt.tx_hash,to:ASSET,input:`0xdead${'2'.repeat(64)}`},{transactionHash:attempt.tx_hash}),true);
});

test('authorization identity rejects changed amount and expired validity',()=>{
  const policy=new MezoAuthorizationPolicy(()=>new Date('2026-09-29T00:00:00Z'));
  const changed=payload() as unknown as {payload:{authorization:{value:string}}}; changed.payload.authorization.value='1';
  assert.throws(()=>policy.identify(changed as unknown as PaymentPayload,quote),(e:unknown)=>e instanceof PublicError&&e.code==='PAYMENT_REJECTED');
  const expired=payload() as unknown as {payload:{authorization:{validBefore:string}}}; expired.payload.authorization.validBefore='1';
  assert.throws(()=>policy.identify(expired as unknown as PaymentPayload,quote),(e:unknown)=>e instanceof PublicError&&e.code==='PAYMENT_REJECTED');
});

test('finality requires twelve canonical confirmations and rejects reorg',async()=>{
  const policy=new MezoFinalityPolicy(12);
  const receipt={blockNumber:'0x64',blockHash:`0x${'4'.repeat(64)}`};
  const block={number:'0x64',hash:receipt.blockHash};
  const rpc={call:async(method:string,params:unknown[])=>method==='eth_getBlockByNumber'&&params[0]==='latest'?{number:'0x6f',hash:`0x${'5'.repeat(64)}`}:{number:'0x64',hash:receipt.blockHash}};
  assert.equal(await policy.isFinal(receipt,block,rpc as never),true);
  const shallow={call:async(method:string)=>method==='eth_getBlockByNumber'?{number:'0x6e',hash:receipt.blockHash}:null};
  assert.equal(await policy.isFinal(receipt,block,shallow as never),false);
  const reorg={call:async(method:string,params:unknown[])=>method==='eth_getBlockByNumber'&&params[0]==='latest'?{number:'0x70'}:{number:'0x64',hash:`0x${'6'.repeat(64)}`}};
  assert.equal(await policy.isFinal(receipt,block,reorg as never),false);
});

test('live grant binds one exact testnet settlement and gas cap',()=>{
  const raw={schema:'liqvera-mezo-payment-grant/v1',subject_commit:'a'.repeat(40),subject_tree:'b'.repeat(40),plan_sha256:'c'.repeat(64),network:NETWORK,chain_id:31611,asset:ASSET,amount_atomic:AMOUNT,buyer:payer,pay_to:payTo,maximum_settlement_submissions:1,max_gas_wei:'100000000000000',expires_at:'2026-09-29T00:05:00Z'};
  const grant=LivePaymentGrant.parse(raw,new Date('2026-09-29T00:00:00Z'));
  grant.authorize({subjectCommit:'a'.repeat(40),subjectTree:'b'.repeat(40),planSha256:'c'.repeat(64),buyer:payer,payTo,gasEstimateWei:100000000000000n});
  assert.throws(()=>grant.authorize({subjectCommit:'a'.repeat(40),subjectTree:'b'.repeat(40),planSha256:'c'.repeat(64),buyer:payer,payTo,gasEstimateWei:100000000000001n}),/LIVE_GRANT_MISMATCH/);
  grant.consume(); assert.throws(()=>grant.consume(),/SETTLEMENT_BUDGET_EXHAUSTED/);
});
