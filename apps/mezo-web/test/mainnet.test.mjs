import assert from 'node:assert/strict';
import test from 'node:test';
globalThis.__LIQVERA_NETWORK__='mainnet';
const {NETWORK,CHAIN_ID,ASSET,quoteIsPayable}=await import('../src/contracts.ts');
const {walletOnMezo,switchToMezo}=await import('../src/wallet.ts');
const {refreshWalletState}=await import('../src/wallet-events.ts');
const {capability,loadFlow}=await import('../src/session.ts');
test('Mainnet wallet switching uses 31612 and rejects a Testnet wallet',async()=>{
 assert.equal(NETWORK,'eip155:31612');assert.equal(CHAIN_ID,31612);assert.equal(ASSET,'0xdD468A1DDc392dcdbEf6db6e34E89AA338F9F186');
 assert.equal(await walletOnMezo({request:async()=> '0x7b7b'}),false);
 const calls=[];let chain='0x7b7b';const provider={request:async arg=>{calls.push(arg);if(arg.method==='eth_chainId')return chain;if(arg.method==='wallet_switchEthereumChain')chain=arg.params[0].chainId;}};
 await switchToMezo(provider);assert.equal(chain,'0x7b7c');assert.equal(calls[0].params[0].chainId,'0x7b7c');
});
test('Mainnet wallet events use the configured network',async()=>{
 const states=[];
 for(const chain of ['0x7b7b','0x7b7c'])await refreshWalletState({request:async({method})=>method==='eth_accounts'?['0x1111111111111111111111111111111111111111']:chain},{applyWalletState:state=>states.push(state)});
 assert.deepEqual(states.map(state=>state.onMezo),[false,true]);
});
test('Mainnet never reuses the old Testnet capability or pending flow',()=>{
 const values=new Map([['liqvera:v1:capability','a'.repeat(43)],['liqvera:v1:flow','{"paymentGuard":"uncertain"}']]);
 globalThis.window={crypto:globalThis.crypto,sessionStorage:{getItem:k=>values.get(k)??null,setItem:(k,v)=>values.set(k,v),removeItem:k=>values.delete(k)}};
 assert.equal(loadFlow(),null);assert.notEqual(capability(),'a'.repeat(43));assert.ok(values.has('liqvera:31612:v1:capability'));assert.ok(values.has('liqvera:v1:flow'));
});
test('Mainnet quote payment rejects Testnet terms and mismatched token',()=>{
 const expires=new Date(Date.now()+60000).toISOString(),payer='0x1111111111111111111111111111111111111111';
 const quote={state:'READY',preview:{snapshot_status:'VALID_FOR_SNAPSHOT_CALCULATION',instrument_id:'hyperliquid:BTC:perpetual',price_musd:'0.01',expires_at:expires},terms:{version:'liqvera-evidence-terms/v1',network:NETWORK,chain_id:CHAIN_ID,asset:ASSET,decimals:18,amount_atomic:'10000000000000000',price_musd:'0.01',pay_to:'0x2222222222222222222222222222222222222222',expected_payer:payer,expires_at:expires}};
 assert.equal(quoteIsPayable(quote,payer),true);
 assert.equal(quoteIsPayable({...quote,terms:{...quote.terms,chain_id:31611,network:'eip155:31611'}},payer),false);
 assert.equal(quoteIsPayable({...quote,terms:{...quote.terms,asset:'0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503'}},payer),false);
});
