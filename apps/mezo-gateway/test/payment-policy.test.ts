import assert from 'node:assert/strict';
import test from 'node:test';
import type { PaymentPayload } from '@x402/core/types';
import { x402Client } from '@x402/core/client';
import { encodeFunctionData } from 'viem';
import { ExactEvmScheme, PERMIT2_ADDRESS, x402ExactPermit2ProxyABI, x402ExactPermit2ProxyAddress } from '@x402/evm';
import { AMOUNT, ASSET, NETWORK, PublicError, type Attempt, type Quote } from '../src/domain/model.js';
import { MezoAuthorizationPolicy, MezoFinalityPolicy } from '../src/security/payment-policy.js';
import { LivePaymentGrant } from '../src/security/live-grant.js';
import { databaseIdentity } from '../src/p3-operator.js';
import { composeOfficialX402 } from '../src/security/live-composition.js';
import { permit2Capability, settlementTransaction } from '../src/adapters/x402.js';

const payer='0x1111111111111111111111111111111111111111';
const payTo='0x2222222222222222222222222222222222222222';
const quote={id:'00000000-0000-4000-8000-000000000001',report_id:'00000000-0000-4000-8000-000000000002',report_sha256:'a'.repeat(64),terms:{expected_payer:payer,pay_to:payTo}} as Quote;
const permit2='0x000000000022D473030F116dDEE9F6B43aC78BA3';
const proxy='0x402085c248EeA27D92E8b30b2C58ed07f9E20001';
function payload(): PaymentPayload { return {x402Version:2,accepted:{scheme:'exact',network:NETWORK,asset:ASSET,amount:AMOUNT,payTo,extra:{assetTransferMethod:'permit2',name:'Mezo USD',version:'1'}},payload:{signature:`0x${'1'.repeat(130)}`,permit2Authorization:{from:payer,permitted:{token:ASSET,amount:AMOUNT},spender:proxy,nonce:'42',deadline:'1790640300',witness:{to:payTo,validAfter:'0'}}},extensions:{eip2612GasSponsoring:{info:{description:'The facilitator accepts EIP-2612 gasless Permit to `Permit2` canonical contract.',from:payer,asset:ASSET,spender:permit2,amount:AMOUNT,nonce:'7',deadline:'1790640300',signature:`0x${'2'.repeat(130)}`,version:'1'},schema:{}}}} as unknown as PaymentPayload; }

test('authorization identity binds exact Permit2 plus EIP-2612 sponsorship without raw signatures',async()=>{
  const policy=new MezoAuthorizationPolicy(()=>new Date('2026-09-29T00:00:00Z'));
  const identity=policy.identify(payload(),quote);
  assert.equal(identity.payer,payer); assert.equal(identity.version,policy.version);
  assert.match(identity.identity,/^[0-9a-f]{64}$/);
  const attempt={authorization_identity:identity.identity,identity_version:identity.version,correlation:identity.correlation,tx_hash:`0x${'3'.repeat(64)}`} as Attempt;
  assert.equal(identity.version,'liqvera-permit2-eip2612-identity/v1');
  assert.equal(JSON.stringify(identity.correlation).includes(`0x${'1'.repeat(130)}`),false);
  assert.equal(JSON.stringify(identity.correlation).includes(`0x${'2'.repeat(130)}`),false);
  const input=encodeFunctionData({abi:x402ExactPermit2ProxyABI,functionName:'settleWithPermit',args:[
    {value:BigInt(AMOUNT),deadline:1790640300n,r:`0x${'2'.repeat(64)}`,s:`0x${'2'.repeat(64)}`,v:34},
    {permitted:{token:ASSET,amount:BigInt(AMOUNT)},nonce:42n,deadline:1790640300n},payer,{to:payTo,validAfter:0n},`0x${'1'.repeat(130)}`,
  ]});
  assert.equal(await policy.bindsTransfer(attempt,{hash:attempt.tx_hash,to:proxy,input},{transactionHash:attempt.tx_hash}),true);
  assert.equal(await policy.bindsTransfer(attempt,{hash:attempt.tx_hash,to:ASSET,input:`0xdeadbeef${input.slice(10)}`},{transactionHash:attempt.tx_hash}),false);
});

test('uppercase wire signatures retain the same decoded settlement identity',async()=>{
  const wire=payload() as unknown as {payload:{signature:string},extensions:{eip2612GasSponsoring:{info:{signature:string}}}};
  wire.payload.signature=`0x${'A'.repeat(130)}`;
  wire.extensions.eip2612GasSponsoring.info.signature=`0x${'B'.repeat(128)}1B`;
  const policy=new MezoAuthorizationPolicy(()=>new Date('2026-09-29T00:00:00Z'));
  const identity=policy.identify(wire as unknown as PaymentPayload,quote);
  const attempt={authorization_identity:identity.identity,identity_version:identity.version,correlation:identity.correlation,tx_hash:`0x${'3'.repeat(64)}`} as Attempt;
  const input=encodeFunctionData({abi:x402ExactPermit2ProxyABI,functionName:'settleWithPermit',args:[
    {value:BigInt(AMOUNT),deadline:1790640300n,r:`0x${'b'.repeat(64)}`,s:`0x${'b'.repeat(64)}`,v:27},
    {permitted:{token:ASSET,amount:BigInt(AMOUNT)},nonce:42n,deadline:1790640300n},payer,{to:payTo,validAfter:0n},`0x${'a'.repeat(130)}`,
  ]});
  assert.equal(await policy.bindsTransfer(attempt,{hash:attempt.tx_hash,to:proxy,input},{transactionHash:attempt.tx_hash}),true);
});

test('official SDK Permit2 and merged EIP-2612 payload passes gateway policy',async()=>{
  let signatures=0;
  const signer={address:payer as `0x${string}`,readContract:async({functionName}:{functionName:string})=>functionName==='allowance'?0n:7n,
    signTypedData:async()=>`0x${(++signatures===1?'A':'B').repeat(130)}` as `0x${string}`};
  const client=new x402Client().register(NETWORK,new ExactEvmScheme(signer));
  const required={x402Version:2,resource:{url:'https://liqvera.invalid/report',description:'report',mimeType:'application/json'},accepts:[{
    scheme:'exact',network:NETWORK,asset:ASSET,amount:AMOUNT,payTo,maxTimeoutSeconds:120,
    extra:{assetTransferMethod:'permit2',name:'Mezo USD',version:'1'},
  }],extensions:{eip2612GasSponsoring:{info:{description:'The facilitator accepts EIP-2612 gasless Permit to `Permit2` canonical contract.',version:'1'},schema:{type:'object'}}}};
  const created=await client.createPaymentPayload(required as never);
  const identity=new MezoAuthorizationPolicy(()=>new Date()).identify(created as PaymentPayload,quote);
  assert.equal(identity.version,'liqvera-permit2-eip2612-identity/v1');
  assert.equal(signatures,2);
});

test('authorization identity rejects changed amount and expired validity',()=>{
  const policy=new MezoAuthorizationPolicy(()=>new Date('2026-09-29T00:00:00Z'));
  const changed=payload() as unknown as {payload:{permit2Authorization:{permitted:{amount:string}}}}; changed.payload.permit2Authorization.permitted.amount='1';
  assert.throws(()=>policy.identify(changed as unknown as PaymentPayload,quote),(e:unknown)=>e instanceof PublicError&&e.code==='PAYMENT_REJECTED');
  const expired=payload() as unknown as {payload:{permit2Authorization:{deadline:string}}}; expired.payload.permit2Authorization.deadline='1';
  assert.throws(()=>policy.identify(expired as unknown as PaymentPayload,quote),(e:unknown)=>e instanceof PublicError&&e.code==='PAYMENT_REJECTED');
  const wrongScheme=payload() as unknown as {accepted:{scheme:string}}; wrongScheme.accepted.scheme='upto';
  assert.throws(()=>policy.identify(wrongScheme as unknown as PaymentPayload,quote),(e:unknown)=>e instanceof PublicError&&e.code==='PAYMENT_REJECTED');
  const eip3009=payload() as unknown as {accepted:{extra:Record<string,string>}}; eip3009.accepted.extra={assetTransferMethod:'eip3009',name:'Mezo USD',version:'1'};
  assert.throws(()=>policy.identify(eip3009 as unknown as PaymentPayload,quote),(e:unknown)=>e instanceof PublicError&&e.code==='PAYMENT_REJECTED');
  const missingExtension=payload() as unknown as {extensions?:unknown}; delete missingExtension.extensions;
  assert.throws(()=>policy.identify(missingExtension as unknown as PaymentPayload,quote),(e:unknown)=>e instanceof PublicError&&e.code==='PAYMENT_REJECTED');
});

test('settlement_pending transaction is spent confirm-only and other failures are not transaction hints',()=>{
  const transaction=`0x${'3'.repeat(64)}`;
  assert.equal(settlementTransaction({success:false,errorReason:'settlement_pending',transaction}),transaction);
  assert.equal(settlementTransaction({success:false,errorReason:'invalid_payload',transaction}),null);
});

test('facilitator capability must be exact Permit2 with EIP-2612 gas sponsorship',()=>{
  assert.equal(PERMIT2_ADDRESS,permit2);
  assert.equal(x402ExactPermit2ProxyAddress,proxy);
  const musd={address:ASSET,symbol:'MUSD',decimals:18,eip712:{name:'Mezo USD',version:'1'},assetTransferMethod:'permit2',supportsEip2612:true};
  const live={x402Version:2,scheme:'exact',network:NETWORK,extra:{assets:[musd]}};
  assert.equal(permit2Capability(live,['eip2612GasSponsoring']),true);
  assert.equal(permit2Capability({...live,extra:{assets:[]}},['eip2612GasSponsoring']),false);
  assert.equal(permit2Capability({...live,extra:{assets:[musd,{...musd}]}},['eip2612GasSponsoring']),false);
  for(const changed of [{assetTransferMethod:'eip3009'},{supportsEip2612:false},{decimals:6},{symbol:'USDC'},{address:payer},{eip712:{name:'MUSD',version:'1'}}])
    assert.equal(permit2Capability({...live,extra:{assets:[{...musd,...changed}]}},['eip2612GasSponsoring']),false);
  assert.equal(permit2Capability(live,[]),false);
  assert.equal(permit2Capability(live,['eip2612GasSponsoring','other']),false);
  assert.equal(permit2Capability(live,['erc20ApprovalGasSponsoring']),false);
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

function grantRaw(){return {schema:'liqvera-mezo-payment-grant/v1',grant_id:'00000000-0000-4000-8000-000000000099',subject_commit:'a'.repeat(40),subject_tree:'b'.repeat(40),plan_sha256:'c'.repeat(64),scheme:'exact',settlement_broadcaster:'facilitator',network:NETWORK,chain_id:31611,asset:ASSET,amount_atomic:AMOUNT,buyer:payer,pay_to:payTo,maximum_settlement_submissions:1,max_buyer_native_gas_wei:'100000000000000',asset_transfer_method:'permit2',permit2_address:permit2,permit2_proxy:proxy,approval_mode:'eip2612-gas-sponsoring',required_extension:'eip2612GasSponsoring',authorization_identity_version:'liqvera-permit2-eip2612-identity/v1',facilitator_url:'https://facilitator.vativ.io/',rpc_url:'https://rpc.test.mezo.org/',database_identity_kind:'sha256-credential-free-postgresql-endpoint/v1',database_host_policy:'loopback-only/v1',database_identity:'d'.repeat(64),expires_at:'2026-09-29T00:05:00Z'};}

test('live grant binds exact facilitator-sponsored settlement and buyer gas authority',()=>{
  const raw=grantRaw();
  const grant=LivePaymentGrant.parse(raw,new Date('2026-09-29T00:00:00Z'));
  grant.authorize({subjectCommit:'a'.repeat(40),subjectTree:'b'.repeat(40),planSha256:'c'.repeat(64),buyer:payer,payTo,now:new Date('2026-09-29T00:01:00Z')});
  assert.match(grant.digest,/^[0-9a-f]{64}$/);
  assert.throws(()=>LivePaymentGrant.parse({...raw,settlement_broadcaster:'buyer'},new Date('2026-09-29T00:00:00Z')),/LIVE_GRANT_INVALID/);
  assert.throws(()=>LivePaymentGrant.parse({...raw,scheme:'upto'},new Date('2026-09-29T00:00:00Z')),/LIVE_GRANT_INVALID/);
  for(const changed of [{asset_transfer_method:'eip3009'},{permit2_address:payer},{permit2_proxy:payer},{approval_mode:'preapproved'},{required_extension:'other'}])
    assert.throws(()=>LivePaymentGrant.parse({...raw,...changed},new Date('2026-09-29T00:00:00Z')),/LIVE_GRANT_INVALID/);
  assert.throws(()=>LivePaymentGrant.parse({...raw,facilitator_url:'https://evil.invalid/'},new Date('2026-09-29T00:00:00Z')),/LIVE_GRANT_INVALID/);
  assert.throws(()=>LivePaymentGrant.parse({...raw,rpc_url:'https://evil.invalid/'},new Date('2026-09-29T00:00:00Z')),/LIVE_GRANT_INVALID/);
  assert.throws(()=>LivePaymentGrant.parse({...raw,database_identity:'0'.repeat(63)},new Date('2026-09-29T00:00:00Z')),/LIVE_GRANT_INVALID/);
  assert.throws(()=>grant.authorize({subjectCommit:'a'.repeat(40),subjectTree:'b'.repeat(40),planSha256:'c'.repeat(64),buyer:payer,payTo,now:new Date('2026-09-29T00:05:00Z')}),/LIVE_GRANT_EXPIRED/);
  const bytes=new TextEncoder().encode(`${JSON.stringify(raw)}\n`);
  assert.notEqual(LivePaymentGrant.parseBytes(bytes,new Date('2026-09-29T00:00:00Z')).digest,grant.digest);
});

test('operator database identity accepts only resolved loopback and binds port/database',async()=>{
  const loopback=async()=>[{address:'127.0.0.1'},{address:'::1'}];
  const approved=await databaseIdentity('postgresql://alice:one@localhost:5433/liqvera_f7',loopback);
  assert.equal(approved,await databaseIdentity('postgresql://bob:two@localhost:5433/liqvera_f7',loopback));
  assert.notEqual(approved,await databaseIdentity('postgresql://alice:one@localhost:5432/liqvera_f7',loopback));
  assert.notEqual(approved,await databaseIdentity('postgresql://alice:one@localhost:5433/other',loopback));
  assert.match(await databaseIdentity('postgresql://127.0.0.1/liqvera'),/^[0-9a-f]{64}$/);
  assert.match(await databaseIdentity('postgresql://[::1]/liqvera'),/^[0-9a-f]{64}$/);
  await assert.rejects(databaseIdentity('postgresql://localhost/liqvera',async()=>[{address:'192.0.2.1'}]),/P3_DATABASE_HOST_NOT_LOOPBACK/);
  for(const remote of ['db.internal','192.0.2.1','8.8.8.8','example.com'])
    await assert.rejects(databaseIdentity(`postgresql://${remote}/liqvera`),/P3_DATABASE_HOST_NOT_LOOPBACK/);
  for(const rejected of [
    'postgresql://db.internal/liqvera?sslmode=require',
    'postgresql://db.internal/liqvera?sslmode=disable',
    'postgresql://db.internal/liqvera?host=/tmp',
    'postgresql://db.internal/liqvera#fragment',
    'postgresql:///liqvera?host=/tmp',
  ]) await assert.rejects(databaseIdentity(rejected),/P3_DATABASE_CONFIG_INVALID/);
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
