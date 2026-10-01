import assert from 'node:assert/strict';
import test from 'node:test';
import { chmod, link, mkdtemp, rm, symlink, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import type { PaymentPayload } from '@x402/core/types';
import { x402Client } from '@x402/core/client';
import { encodePaymentSignatureHeader } from '@x402/core/http';
import { encodeFunctionData } from 'viem';
import { ExactEvmScheme, PERMIT2_ADDRESS, x402ExactPermit2ProxyABI, x402ExactPermit2ProxyAddress } from '@x402/evm';
import { AMOUNT, ASSET, NETWORK, PublicError, type Attempt, type Quote } from '../src/domain/model.js';
import { MezoAuthorizationPolicy, MezoFinalityPolicy } from '../src/security/payment-policy.js';
import { LivePaymentGrant } from '../src/security/live-grant.js';
import { authorizeNewSettlement, databaseIdentity } from '../src/p3-operator.js';
import { composeOfficialX402, readPrivateGrantFile } from '../src/security/live-composition.js';
import { permit2Capability, settlementTransaction } from '../src/adapters/x402.js';
import { loadConfig } from '../src/config.js';
import { assertSaleFresh, MAX_SALE_AGE_MS } from '../src/workers/builds.js';
import {createHash,generateKeyPairSync,sign} from 'node:crypto';

const payer='0x1111111111111111111111111111111111111111';
const payTo='0x2222222222222222222222222222222222222222';
const quote={id:'00000000-0000-4000-8000-000000000001',report_id:'00000000-0000-4000-8000-000000000002',report_sha256:'a'.repeat(64),terms:{expected_payer:payer,pay_to:payTo}} as Quote;
const permit2='0x000000000022D473030F116dDEE9F6B43aC78BA3';
const proxy='0x402085c248EeA27D92E8b30b2C58ed07f9E20001';

test('sale publication permits bounded packaging latency without weakening capture freshness',()=>{
  const now=Date.parse('2026-09-30T12:00:30.000Z');
  assert.equal(MAX_SALE_AGE_MS,30_000);
  assert.doesNotThrow(()=>assertSaleFresh('2026-09-30T12:00:00.000Z',now));
  assert.throws(()=>assertSaleFresh('2026-09-30T11:59:59.999Z',now),/STALE_SOURCE/);
  assert.doesNotThrow(()=>assertSaleFresh('2026-09-30T12:00:31.000Z',now));
  assert.throws(()=>assertSaleFresh('2026-09-30T12:00:31.001Z',now),/CLOCK_SKEW/);
});

test('grantless live runtime starts payment-not-ready',async()=>{
  const config=await loadConfig({DATABASE_URL:'postgresql://liqvera:test@127.0.0.1:5432/liqvera',SOURCE_MODE:'live-public',PUBLIC_BASE_URL:'https://reports.invalid',CORS_ORIGINS:'https://reports.invalid',PAY_TO:payTo});
  assert.equal(config.liveGrantFile,null); assert.equal(config.liveContext,null);
  const payment=composeOfficialX402(new MezoAuthorizationPolicy(),new MezoFinalityPolicy(12),{} as never,new URL('https://reports.invalid'),null);
  assert.ok(payment.blockers().includes('EXTERNAL_GRANT_REQUIRED'));
});
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
function signedV2(overrides:Record<string,unknown>={}){const {privateKey,publicKey}=generateKeyPairSync('ed25519');const raw=publicKey.export({format:'der',type:'spki'}).subarray(-32);const policy={approval_mode:'eip2612-gas-sponsoring',asset:ASSET,asset_transfer_method:'permit2',amount_atomic:AMOUNT,authorization_identity_version:'liqvera-permit2-eip2612-identity/v1',chain_id:31611,database_host_policy:'loopback-only/v1',database_identity:'d'.repeat(64),database_identity_kind:'sha256-credential-free-postgresql-endpoint/v1',expires_at:'2026-09-29T12:00:00.000Z',facilitator_url:'https://facilitator.vativ.io/',grant_id:'00000000-0000-4000-8000-000000000098',issued_at:'2026-09-29T00:00:00.000Z',max_buyer_native_gas_wei:'0',max_per_payer:1,max_total_amount_atomic:(BigInt(AMOUNT)*3n).toString(),maximum_settlement_submissions:3,network:NETWORK,not_before:'2026-09-29T00:00:00.000Z',pay_to:payTo,payer_policy:'ANY_VALID_X402_PAYER',permit2_address:permit2,permit2_proxy:proxy,plan_sha256:'c'.repeat(64),required_extension:'eip2612GasSponsoring',rpc_url:'https://rpc.test.mezo.org/',schema:'liqvera-mezo-payment-grant-policy/v2',scheme:'exact',settlement_broadcaster:'facilitator',subject_commit:'a'.repeat(40),subject_tree:'b'.repeat(40),...overrides};const bytes=Buffer.from(JSON.stringify(Object.fromEntries(Object.entries(policy).sort())));const envelope={schema:'liqvera-mezo-payment-grant-envelope/v2',key_id:createHash('sha256').update(raw).digest('hex'),payload:bytes.toString('base64url'),signature:sign(null,bytes,privateKey).toString('base64url')};return {bytes:Buffer.from(JSON.stringify(envelope)),publicKey:raw};}

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

test('expired consumed grant is confirm-only while expired unconsumed grant cannot settle',()=>{
  const bytes=new TextEncoder().encode(JSON.stringify(grantRaw()));
  const expiredAt=new Date('2026-09-29T00:06:00Z');
  assert.throws(()=>LivePaymentGrant.parseBytes(bytes,expiredAt),/LIVE_GRANT_EXPIRED/);
  const grant=LivePaymentGrant.parseBytesForReconciliation(bytes,expiredAt);
  const context={subjectCommit:'a'.repeat(40),subjectTree:'b'.repeat(40),planSha256:'c'.repeat(64),buyer:payer,payTo,now:expiredAt};
  let settlementCalls=0;
  if(authorizeNewSettlement(grant,context,true))settlementCalls++;
  assert.equal(settlementCalls,0);
  for(const mismatch of [
    {subjectCommit:'0'.repeat(40)},
    {subjectTree:'0'.repeat(40)},
    {planSha256:'0'.repeat(64)},
    {buyer:'0x3333333333333333333333333333333333333333'},
    {payTo:'0x4444444444444444444444444444444444444444'},
  ]) assert.throws(()=>authorizeNewSettlement(grant,{...context,...mismatch},true),/LIVE_GRANT_MISMATCH/);
  assert.throws(()=>{
    if(authorizeNewSettlement(grant,context,false))settlementCalls++;
  },/LIVE_GRANT_EXPIRED/);
  assert.equal(settlementCalls,0);
});

test('reconciliation parser does not weaken first-settlement maximum grant lifetime',()=>{
  const bytes=new TextEncoder().encode(JSON.stringify({...grantRaw(),expires_at:'2026-09-29T01:00:00Z'}));
  const now=new Date('2026-09-29T00:00:00Z');
  const grant=LivePaymentGrant.parseBytesForReconciliation(bytes,now);
  assert.throws(()=>authorizeNewSettlement(grant,{subjectCommit:'a'.repeat(40),subjectTree:'b'.repeat(40),planSha256:'c'.repeat(64),buyer:payer,payTo,now},false),/LIVE_GRANT_EXPIRED/);
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
    context:{subjectCommit:'a'.repeat(40),subjectTree:'b'.repeat(40),planSha256:'c'.repeat(64),buyer:payer,payTo,databaseIdentity:'d'.repeat(64)},
  }),/LIVE_GRANT_INVALID/);
});

test('valid exact grant activates facilitator-sponsored composition without network I/O',()=>{
  const payment=composeOfficialX402(new MezoAuthorizationPolicy(),new MezoFinalityPolicy(12),{} as never,new URL('https://reports.invalid'),{
    grantBytes:new TextEncoder().encode(JSON.stringify(grantRaw())),observedAt:new Date('2026-09-29T00:00:00Z'),
    context:{subjectCommit:'a'.repeat(40),subjectTree:'b'.repeat(40),planSha256:'c'.repeat(64),buyer:payer,payTo,databaseIdentity:'d'.repeat(64)},
  });
  assert.ok(payment.blockers().includes('PAYMENT_SERVICE_UNAVAILABLE'));
  assert.throws(()=>composeOfficialX402(new MezoAuthorizationPolicy(),new MezoFinalityPolicy(12),{} as never,new URL('https://reports.invalid'),{
    grantBytes:new TextEncoder().encode(JSON.stringify(grantRaw())),observedAt:new Date('2026-09-29T00:00:00Z'),
    context:{subjectCommit:'a'.repeat(40),subjectTree:'b'.repeat(40),planSha256:'c'.repeat(64),buyer:payer,payTo,databaseIdentity:'e'.repeat(64)},
  }),/LIVE_GRANT_MISMATCH/);
});

test('signed v2 authority permits any quote payer while v1 remains buyer bound',()=>{
  const context={subjectCommit:'a'.repeat(40),subjectTree:'b'.repeat(40),planSha256:'c'.repeat(64),buyer:payer,payTo,databaseIdentity:'d'.repeat(64)};
  const bound=composeOfficialX402(new MezoAuthorizationPolicy(),new MezoFinalityPolicy(12),{} as never,new URL('https://liqvera.site'),{grantBytes:Buffer.from(JSON.stringify(grantRaw())),observedAt:new Date('2026-09-29T00:00:00Z'),context});
  const signed=signedV2();const reusable=composeOfficialX402(new MezoAuthorizationPolicy(),new MezoFinalityPolicy(12),{} as never,new URL('https://liqvera.site'),{grantBytes:signed.bytes,publicKey:signed.publicKey,observedAt:new Date('2026-09-29T00:01:00Z'),context});
  assert.equal(bound.expectedPayer,payer);assert.equal(reusable.expectedPayer,undefined);assert.equal(reusable.liveGrantAuthority?.maxSubmissions,3);assert.match(reusable.liveGrantDigest!,/^[0-9a-f]{64}$/);
});

test('signed v2 rejects bad signatures, noncanonical payloads and lifetime over 24 hours',()=>{
  const now=new Date('2026-09-29T00:01:00Z');const good=signedV2();assert.doesNotThrow(()=>LivePaymentGrant.parseBytes(good.bytes,now,good.publicKey));
  const tampered=JSON.parse(good.bytes.toString());tampered.signature=`A${tampered.signature.slice(1)}`;assert.throws(()=>LivePaymentGrant.parseBytes(Buffer.from(JSON.stringify(tampered)),now,good.publicKey),/SIGNATURE/);
  const tooLong=signedV2({expires_at:'2026-09-30T00:00:00.001Z'});assert.throws(()=>LivePaymentGrant.parseBytes(tooLong.bytes,now,tooLong.publicKey),/INVALID/);
  const duplicate=Buffer.from('{"schema":"liqvera-mezo-payment-grant-envelope/v2","schema":"x"}');assert.throws(()=>LivePaymentGrant.parseBytes(duplicate,now,good.publicKey),/INVALID/);
});

test('full signed v2 verification binds the quote payer',async()=>{
  const quotePayer='0x3333333333333333333333333333333333333333';
  const demoQuote={...quote,terms:{...quote.terms,expected_payer:quotePayer}} as Quote;
  const wire=payload() as unknown as Record<string,unknown>;
  ((wire.payload as {permit2Authorization:{from:string}}).permit2Authorization.from)=quotePayer;
  ((wire.extensions as {eip2612GasSponsoring:{info:{from:string}}}).eip2612GasSponsoring.info.from)=quotePayer;
  const policy={reviewed:true,version:'test/v1',identify:()=>({payer:quotePayer,identity:'a'.repeat(64),version:'test/v1',valid_until:'2099-01-01T00:00:00Z',correlation:{}}),async bindsTransfer(){return true;}};
  const reader={nativeBalanceSnapshot:async()=>({balance:'0',block_number:'0x1',block_hash:`0x${'1'.repeat(64)}`})};
  const signed=signedV2();
  const payment=composeOfficialX402(policy as never,new MezoFinalityPolicy(12),reader as never,new URL('https://liqvera.site'),{
    grantBytes:signed.bytes,publicKey:signed.publicKey,observedAt:new Date('2026-09-29T00:01:00Z'),
    context:{subjectCommit:'a'.repeat(40),subjectTree:'b'.repeat(40),planSha256:'c'.repeat(64),buyer:payer,payTo,databaseIdentity:'d'.repeat(64)},
    now:()=>new Date('2026-09-29T00:01:00Z'),
  });
  const requirements={scheme:'exact',network:NETWORK,asset:ASSET,amount:AMOUNT,payTo,extra:{assetTransferMethod:'permit2',name:'Mezo USD',version:'1'}};
  const target=payment as unknown as {initialized:boolean;server:{buildPaymentRequirements():Promise<unknown[]>;createPaymentRequiredResponse():Promise<unknown>;verifyPayment():Promise<unknown>}};
  target.initialized=true;target.server={async buildPaymentRequirements(){return [requirements];},async createPaymentRequiredResponse(){return {x402Version:2,accepts:[requirements],resource:{url:'https://liqvera.site'}};},async verifyPayment(){return {isValid:true,payer:quotePayer};}};
  const verified=await payment.verify(encodePaymentSignatureHeader(wire as never),demoQuote);
  assert.equal(verified.identity.payer,quotePayer);
});

test('live grant expiry becomes a readiness blocker after startup',()=>{
  let now=new Date('2026-09-29T00:00:00Z');
  const payment=composeOfficialX402(new MezoAuthorizationPolicy(),new MezoFinalityPolicy(12),{} as never,new URL('https://reports.invalid'),{
    grantBytes:new TextEncoder().encode(JSON.stringify(grantRaw())),observedAt:now,
    context:{subjectCommit:'a'.repeat(40),subjectTree:'b'.repeat(40),planSha256:'c'.repeat(64),buyer:payer,payTo,databaseIdentity:'d'.repeat(64)},
    now:()=>now,
  });
  assert.ok(!payment.blockers().includes('EXTERNAL_GRANT_REQUIRED'));
  now=new Date('2026-09-29T00:10:01Z');
  assert.ok(payment.blockers().includes('EXTERNAL_GRANT_REQUIRED'));
});

test('private grant reader accepts only one stable bounded private regular file',async()=>{
  const root=await mkdtemp(join(tmpdir(),'liqvera-grant-'));
  try {
    const path=join(root,'grant.json');const bytes=new TextEncoder().encode('{"grant":true}');
    await writeFile(path,bytes,{mode:0o600});
    assert.deepEqual(await readPrivateGrantFile(path),Buffer.from(bytes));
    await chmod(path,0o644);await assert.rejects(readPrivateGrantFile(path),/LIVE_GRANT_FILE_UNSAFE/);
    await chmod(path,0o600);const hard=join(root,'hard');await link(path,hard);
    await assert.rejects(readPrivateGrantFile(path),/LIVE_GRANT_FILE_UNSAFE/);await rm(hard);
    const symbolic=join(root,'symbolic');await symlink(path,symbolic);
    await assert.rejects(readPrivateGrantFile(symbolic),/LIVE_GRANT_FILE_UNSAFE/);
    const empty=join(root,'empty');await writeFile(empty,new Uint8Array(),{mode:0o600});
    await assert.rejects(readPrivateGrantFile(empty),/LIVE_GRANT_FILE_UNSAFE/);
    const large=join(root,'large');await writeFile(large,new Uint8Array(16_385),{mode:0o600});
    await assert.rejects(readPrivateGrantFile(large),/LIVE_GRANT_FILE_UNSAFE/);
    await chmod(path,0o600);
    await assert.rejects(readPrivateGrantFile(path,{afterOpen:async()=>{await chmod(path,0o644);}}),/LIVE_GRANT_FILE_CHANGED/);
    await chmod(path,0o600);
    await assert.rejects(readPrivateGrantFile(path,{afterRead:async()=>{await writeFile(path,new TextEncoder().encode('{"other":true}'));}}),/LIVE_GRANT_FILE_CHANGED/);
  } finally { await rm(root,{recursive:true,force:true}); }
});
