import assert from 'node:assert/strict';
import test from 'node:test';
import {createServer} from 'node:http';
import {once} from 'node:events';
import {loadConfig} from '../dist/config.js';
import {OfficialX402} from '../dist/adapters/x402.js';
import {MezoAuthorizationPolicy,MezoFinalityPolicy} from '../dist/security/payment-policy.js';
import {AMOUNT,ASSET,NETWORK} from '../dist/domain/model.js';
import {x402Client} from '@x402/core/client';
import {ExactEvmScheme} from '@x402/evm';
import {decodePaymentRequiredHeader,encodePaymentSignatureHeader} from '@x402/core/http';
const payTo='0x2222222222222222222222222222222222222222';
const payer='0x1111111111111111111111111111111111111111';
const env={DATABASE_URL:'postgresql://localhost/test',SOURCE_MODE:'live-public',PUBLIC_BASE_URL:'https://liqvera.invalid',PAY_TO:payTo};
test('merchant payments require explicit mode and reject ambiguous or fixture configuration',async()=>{
 assert.equal((await loadConfig(env)).paymentMode,'grant');
 assert.equal((await loadConfig({...env,LIQVERA_PAYMENT_MODE:'merchant'})).paymentMode,'merchant');
 for(const patch of [{LIQVERA_PAYMENT_MODE:'merhcant'},{LIQVERA_PAYMENT_MODE:'merchant',SOURCE_MODE:'fixture'},{LIQVERA_PAYMENT_MODE:'merchant',PAY_TO:''},{LIQVERA_PAYMENT_MODE:'merchant',LIQVERA_LIVE_GRANT_FILE:'/unread'},{LIQVERA_PAYMENT_MODE:'merchant',LIQVERA_ANY_PAYER:'1'}]) await assert.rejects(loadConfig({...env,...patch}));
});
test('merchant SDK handshake verifies each wallet authorization without operator grant',async(t)=>{
 let allow=true;let settles=0;
 const server=createServer(async(req,res)=>{
  res.setHeader('content-type','application/json');
  if(req.url==='/supported')res.end(JSON.stringify({kinds:[{x402Version:2,scheme:'exact',network:NETWORK,extra:{assets:[{address:ASSET,symbol:'MUSD',decimals:18,eip712:{name:'Mezo USD',version:'1'},assetTransferMethod:'permit2',supportsEip2612:true}]}}],extensions:['eip2612GasSponsoring'],signers:{}}));
  else if(req.url==='/verify')res.end(JSON.stringify(allow?{isValid:true,payer}:{isValid:false,invalidReason:'invalid_signature'}));
  else {settles++;res.statusCode=500;res.end('{}');}
 });
 server.listen(0,'127.0.0.1');await once(server,'listening');t.after(()=>server.close());
 const payment=new OfficialX402(new MezoAuthorizationPolicy(),new MezoFinalityPolicy(),{nativeBalanceSnapshot:async()=>({balance:'0',block_number:'1',block_hash:'0x'+'3'.repeat(64)})},new URL('https://liqvera.invalid'),null,null,()=>new Date(),new URL(`http://127.0.0.1:${server.address().port}`),payTo);
 await payment.initialize();assert.deepEqual(payment.blockers(),[]);
 const quote={id:'00000000-0000-4000-8000-000000000001',report_id:'00000000-0000-4000-8000-000000000002',report_sha256:'a'.repeat(64),terms:{pay_to:payTo,expected_payer:payer}};
 const required=decodePaymentRequiredHeader((await payment.requirements(quote)).header);
 assert.equal(required.accepts[0].amount,AMOUNT);assert.equal(required.accepts[0].network,NETWORK);
 const client=new x402Client().register(NETWORK,new ExactEvmScheme({address:payer,readContract:async()=>0n,signTypedData:async()=>`0x${'1'.repeat(130)}`}));
 const payload=await client.createPaymentPayload(required);
 const verified=await payment.verify(encodePaymentSignatureHeader(payload),quote);
 assert.equal(verified.identity.correlation.payment_mode,'merchant');assert.equal(verified.identity.correlation.live_grant_digest,undefined);
 assert.equal(verified.identity.payer,payer);
 await assert.rejects(payment.requirements({...quote,terms:{...quote.terms,pay_to:payer}}));
 for(const field of ['network','asset','amount','payTo']){
  const bad=structuredClone(payload);bad.accepted[field]=field==='amount'?'1':field==='network'?'eip155:1':payer;
  await assert.rejects(payment.verify(encodePaymentSignatureHeader(bad),quote));
 }
 await assert.rejects(payment.verify(encodePaymentSignatureHeader(payload),{...quote,terms:{...quote.terms,expected_payer:payTo}}));
 for(const policies of [[{reviewed:false},new MezoFinalityPolicy()],[new MezoAuthorizationPolicy(),{reviewed:false}]]) {
  const closed=new OfficialX402(...policies,{},new URL('https://liqvera.invalid'),null,null,undefined,undefined,payTo);
  await closed.initialize();assert.ok(closed.blockers().length);
 }
 allow=false;await assert.rejects(payment.verify(encodePaymentSignatureHeader(payload),quote));
 assert.equal(settles,0);
});
