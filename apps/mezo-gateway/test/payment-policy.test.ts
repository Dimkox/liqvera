import assert from 'node:assert/strict';
import test from 'node:test';
import type { PaymentPayload } from '@x402/core/types';
import { AMOUNT, ASSET, NETWORK, PublicError, type Attempt, type Quote } from '../src/domain/model.js';
import { MezoAuthorizationPolicy, MezoFinalityPolicy } from '../src/security/payment-policy.js';
import { LivePaymentGrant } from '../src/security/live-grant.js';
import { databaseIdentity } from '../src/p3-operator.js';
import { composeOfficialX402 } from '../src/security/live-composition.js';
import { settlementTransaction } from '../src/adapters/x402.js';

const payer='0x1111111111111111111111111111111111111111';
const payTo='0x2222222222222222222222222222222222222222';
const quote={id:'00000000-0000-4000-8000-000000000001',report_id:'00000000-0000-4000-8000-000000000002',report_sha256:'a'.repeat(64),terms:{expected_payer:payer,pay_to:payTo}} as Quote;
function payload(): PaymentPayload { return {x402Version:2,accepted:{scheme:'exact',network:NETWORK,asset:ASSET,amount:AMOUNT,payTo},payload:{signature:`0x${'1'.repeat(128)}1b`,authorization:{from:payer,to:payTo,value:AMOUNT,validAfter:'0',validBefore:'1790640300',nonce:`0x${'2'.repeat(64)}`}}} as unknown as PaymentPayload; }

test('authorization identity binds exact EIP-3009 terms and nonce',async()=>{
  const policy=new MezoAuthorizationPolicy(()=>new Date('2026-09-29T00:00:00Z'));
  const identity=policy.identify(payload(),quote);
  assert.equal(identity.payer,payer); assert.equal(identity.version,policy.version);
  assert.match(identity.identity,/^[0-9a-f]{64}$/);
  const attempt={authorization_identity:identity.identity,identity_version:identity.version,correlation:identity.correlation,tx_hash:`0x${'3'.repeat(64)}`} as Attempt;
  const word=(value:string)=>value.replace(/^0x/,'').padStart(64,'0');
  const signature=`${'1'.repeat(128)}1b`;
  const input=`0xe3ee160e${word(payer)}${word(payTo)}${word(BigInt(AMOUNT).toString(16))}${word('0')}${word(BigInt('1790640300').toString(16))}${'2'.repeat(64)}${word('1b')}${'1'.repeat(64)}${'1'.repeat(64)}`;
  assert.equal(await policy.bindsTransfer(attempt,{hash:attempt.tx_hash,to:ASSET,input},{transactionHash:attempt.tx_hash}),true);
  assert.equal(await policy.bindsTransfer(attempt,{hash:attempt.tx_hash,to:ASSET,input:`0xdeadbeef${input.slice(10)}`},{transactionHash:attempt.tx_hash}),false);
  assert.equal(signature.length,130);
});

test('authorization identity rejects changed amount and expired validity',()=>{
  const policy=new MezoAuthorizationPolicy(()=>new Date('2026-09-29T00:00:00Z'));
  const changed=payload() as unknown as {payload:{authorization:{value:string}}}; changed.payload.authorization.value='1';
  assert.throws(()=>policy.identify(changed as unknown as PaymentPayload,quote),(e:unknown)=>e instanceof PublicError&&e.code==='PAYMENT_REJECTED');
  const expired=payload() as unknown as {payload:{authorization:{validBefore:string}}}; expired.payload.authorization.validBefore='1';
  assert.throws(()=>policy.identify(expired as unknown as PaymentPayload,quote),(e:unknown)=>e instanceof PublicError&&e.code==='PAYMENT_REJECTED');
  const wrongScheme=payload() as unknown as {accepted:{scheme:string}}; wrongScheme.accepted.scheme='upto';
  assert.throws(()=>policy.identify(wrongScheme as unknown as PaymentPayload,quote),(e:unknown)=>e instanceof PublicError&&e.code==='PAYMENT_REJECTED');
  const permit2=payload() as unknown as {accepted:{extra:Record<string,string>}}; permit2.accepted.extra={assetTransferMethod:'permit2'};
  assert.throws(()=>policy.identify(permit2 as unknown as PaymentPayload,quote),(e:unknown)=>e instanceof PublicError&&e.code==='PAYMENT_REJECTED');
});

test('settlement_pending transaction is spent confirm-only and other failures are not transaction hints',()=>{
  const transaction=`0x${'3'.repeat(64)}`;
  assert.equal(settlementTransaction({success:false,errorReason:'settlement_pending',transaction}),transaction);
  assert.equal(settlementTransaction({success:false,errorReason:'invalid_payload',transaction}),null);
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

function grantRaw(){return {schema:'liqvera-mezo-payment-grant/v1',grant_id:'00000000-0000-4000-8000-000000000099',subject_commit:'a'.repeat(40),subject_tree:'b'.repeat(40),plan_sha256:'c'.repeat(64),scheme:'exact',settlement_broadcaster:'facilitator',network:NETWORK,chain_id:31611,asset:ASSET,amount_atomic:AMOUNT,buyer:payer,pay_to:payTo,maximum_settlement_submissions:1,max_buyer_native_gas_wei:'100000000000000',facilitator_url:'https://facilitator.vativ.io/',rpc_url:'https://rpc.test.mezo.org/',database_identity_kind:'sha256-credential-free-postgresql-endpoint/v1',database_identity:'d'.repeat(64),expires_at:'2026-09-29T00:05:00Z'};}

test('live grant binds exact facilitator-sponsored settlement and buyer gas authority',()=>{
  const raw=grantRaw();
  const grant=LivePaymentGrant.parse(raw,new Date('2026-09-29T00:00:00Z'));
  grant.authorize({subjectCommit:'a'.repeat(40),subjectTree:'b'.repeat(40),planSha256:'c'.repeat(64),buyer:payer,payTo,now:new Date('2026-09-29T00:01:00Z')});
  assert.match(grant.digest,/^[0-9a-f]{64}$/);
  assert.throws(()=>LivePaymentGrant.parse({...raw,settlement_broadcaster:'buyer'},new Date('2026-09-29T00:00:00Z')),/LIVE_GRANT_INVALID/);
  assert.throws(()=>LivePaymentGrant.parse({...raw,scheme:'upto'},new Date('2026-09-29T00:00:00Z')),/LIVE_GRANT_INVALID/);
  assert.throws(()=>LivePaymentGrant.parse({...raw,facilitator_url:'https://evil.invalid/'},new Date('2026-09-29T00:00:00Z')),/LIVE_GRANT_INVALID/);
  assert.throws(()=>LivePaymentGrant.parse({...raw,rpc_url:'https://evil.invalid/'},new Date('2026-09-29T00:00:00Z')),/LIVE_GRANT_INVALID/);
  assert.throws(()=>LivePaymentGrant.parse({...raw,database_identity:'0'.repeat(63)},new Date('2026-09-29T00:00:00Z')),/LIVE_GRANT_INVALID/);
  assert.throws(()=>grant.authorize({subjectCommit:'a'.repeat(40),subjectTree:'b'.repeat(40),planSha256:'c'.repeat(64),buyer:payer,payTo,now:new Date('2026-09-29T00:05:00Z')}),/LIVE_GRANT_EXPIRED/);
  const bytes=new TextEncoder().encode(`${JSON.stringify(raw)}\n`);
  assert.notEqual(LivePaymentGrant.parseBytes(bytes,new Date('2026-09-29T00:00:00Z')).digest,grant.digest);
});

test('operator database identity ignores credentials but binds host port and database',()=>{
  const approved=databaseIdentity('postgresql://alice:one@db.internal:5433/liqvera_f7');
  assert.equal(approved,databaseIdentity('postgresql://bob:two@db.internal:5433/liqvera_f7'));
  assert.notEqual(approved,databaseIdentity('postgresql://alice:one@other.internal:5433/liqvera_f7'));
  assert.notEqual(approved,databaseIdentity('postgresql://alice:one@db.internal:5432/liqvera_f7'));
  assert.notEqual(approved,databaseIdentity('postgresql://alice:one@db.internal:5433/other'));
});

test('production composition is grantless by default and rejects malformed harness authority',()=>{
  const identity=new MezoAuthorizationPolicy(()=>new Date('2026-09-29T00:00:00Z'));
  const finality=new MezoFinalityPolicy(12);
  const reader={} as never;
  const ordinary=composeOfficialX402(identity,finality,reader,new URL('https://reports.invalid'),null);
  assert.ok(ordinary.blockers().includes('EXTERNAL_GRANT_REQUIRED'));
  assert.throws(()=>composeOfficialX402(identity,finality,reader,new URL('https://reports.invalid'),{
    grantBytes:new TextEncoder().encode('{}'),observedAt:new Date('2026-09-29T00:00:00Z'),
    context:{subjectCommit:'a'.repeat(40),subjectTree:'b'.repeat(40),planSha256:'c'.repeat(64),buyer:payer,payTo},
  }),/LIVE_GRANT_INVALID/);
});

test('valid exact grant activates facilitator-sponsored composition without network I/O',()=>{
  const payment=composeOfficialX402(new MezoAuthorizationPolicy(),new MezoFinalityPolicy(12),{} as never,new URL('https://reports.invalid'),{
    grantBytes:new TextEncoder().encode(JSON.stringify(grantRaw())),observedAt:new Date('2026-09-29T00:00:00Z'),
    context:{subjectCommit:'a'.repeat(40),subjectTree:'b'.repeat(40),planSha256:'c'.repeat(64),buyer:payer,payTo},
  });
  assert.ok(payment.blockers().includes('PAYMENT_SERVICE_UNAVAILABLE'));
});
