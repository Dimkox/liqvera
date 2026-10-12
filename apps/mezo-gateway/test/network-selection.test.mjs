import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import test from 'node:test';
function model(network){return JSON.parse(execFileSync(process.execPath,['--input-type=module','-e',"import {NETWORK,CHAIN_ID,ASSET,RPC_URL} from './dist/domain/model.js'; console.log(JSON.stringify({NETWORK,CHAIN_ID,ASSET,RPC_URL}));"],{cwd:new URL('..',import.meta.url),env:{...process.env,LIQVERA_NETWORK:network},encoding:'utf8',stdio:['ignore','pipe','pipe']}));}
test('explicit Mainnet config selects the real network, token and RPC together',()=>{
 assert.deepEqual(model('mainnet'),{NETWORK:'eip155:31612',CHAIN_ID:31612,ASSET:'0xdD468A1DDc392dcdbEf6db6e34E89AA338F9F186',RPC_URL:'https://mezo-mainnet.boar.network'});
 assert.equal(model('testnet').CHAIN_ID,31611);
});
test('unknown network configuration fails closed',()=>{assert.throws(()=>model('mainnte'));});
test('Mainnet grant rejects Testnet network, token and RPC independently',()=>{
 const code=`import assert from 'node:assert/strict';import {LivePaymentGrant} from './dist/security/live-grant.js';
 import {NETWORK,CHAIN_ID,ASSET,AMOUNT,RPC_URL} from './dist/domain/model.js';
 const now=new Date();const grant={schema:'liqvera-mezo-payment-grant/v1',grant_id:'00000000-0000-4000-8000-000000000099',subject_commit:'a'.repeat(40),subject_tree:'b'.repeat(40),plan_sha256:'c'.repeat(64),scheme:'exact',settlement_broadcaster:'facilitator',network:NETWORK,chain_id:CHAIN_ID,asset:ASSET,amount_atomic:AMOUNT,buyer:'0x1111111111111111111111111111111111111111',pay_to:'0x2222222222222222222222222222222222222222',maximum_settlement_submissions:1,max_buyer_native_gas_wei:'100000000000000',asset_transfer_method:'permit2',permit2_address:'0x000000000022D473030F116dDEE9F6B43aC78BA3',permit2_proxy:'0x402085c248EeA27D92E8b30b2C58ed07f9E20001',approval_mode:'eip2612-gas-sponsoring',required_extension:'eip2612GasSponsoring',authorization_identity_version:'liqvera-permit2-eip2612-identity/v1',facilitator_url:'https://facilitator.vativ.io/',rpc_url:new URL(RPC_URL).href,database_identity_kind:'sha256-credential-free-postgresql-endpoint/v1',database_host_policy:'loopback-only/v1',database_identity:'d'.repeat(64),expires_at:new Date(now.getTime()+60000).toISOString()};
 assert.doesNotThrow(()=>LivePaymentGrant.parse(grant,now));
 for(const patch of [{network:'eip155:31611'},{chain_id:31611},{asset:'0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503'},{rpc_url:'https://rpc.test.mezo.org/'}])assert.throws(()=>LivePaymentGrant.parse({...grant,...patch},now),/LIVE_GRANT_INVALID/);`;
 execFileSync(process.execPath,['--input-type=module','-e',code],{cwd:new URL('..',import.meta.url),env:{...process.env,LIQVERA_NETWORK:'mainnet'},stdio:'pipe'});
});
