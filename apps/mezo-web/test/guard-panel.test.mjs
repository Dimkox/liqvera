import test from 'node:test';
import assert from 'node:assert/strict';
import {Interface,Wallet} from 'ethers';
import {setup,find,text,tick} from './helpers/trove-dom.mjs';
import {troveProvider} from './helpers/trove-provider.mjs';
import {GUARD,GUARD_ABI} from '../src/guard.ts';
import {mountGuardPanel} from '../src/guard-panel.ts';

const guard=new Interface(GUARD_ABI),sigs=new Interface(['function getNonce(address) view returns (uint256)']);
const NOW=1_800_000_000n;
function guardProvider(wallet,opts={}){
 const g={btc:0n,policy:null,nonce:0n,sent:[],signed:[]};
 const p=troveProvider({request:async({method,params})=>{
  if(method==='eth_chainId')return opts.chain??'0x7b7b';
  if(method==='eth_signTypedData_v4'){const t=JSON.parse(params[1]);delete t.types.EIP712Domain;g.signed.push(t);return wallet.signTypedData(t.domain,t.types,t.message);}
  if(method==='eth_sendTransaction'){
   const tx=params[0];g.sent.push(tx);
   if(tx.to===GUARD.address){const fn=guard.parseTransaction({data:tx.data,value:BigInt(tx.value)});
    if(fn.name==='depositBTC')g.btc+=BigInt(tx.value);
    if(fn.name==='arm')g.policy=[Number(fn.args[0]),fn.args[1],fn.args[2],fn.args[3],fn.args[4],g.nonce,fn.args[5]];
    if(fn.name==='disarm')g.policy=null;}
   return undefined;
  }
  if(method==='eth_call'&&params[0].to===GUARD.signatures)return sigs.encodeFunctionResult('getNonce',[g.nonce]);
  if(method==='eth_call'&&params[0].to===GUARD.address){
   const fn=guard.parseTransaction({data:params[0].data});
   const reserved=g.policy?g.policy[2]+g.policy[3]:0n;
   const v={status:[g.policy?0:1,0n],policyOf:[g.policy??[0,0n,0n,0n,0n,0n,'0x']],btcBalance:[g.btc],musdBalance:[0n],freeBTC:[g.btc-reserved],freeMUSD:[0n]}[fn.name];
   if(v)return guard.encodeFunctionResult(fn.name,v);
   return '0x'; // simulation of a state-changing call
  }
  return undefined;
 }});
 return {p,g};
}
const watchFetch=(sub={active:false,source:'none',paidUntil:null,trialUntil:null,payments:0})=>async url=>new Response(JSON.stringify({borrower:'x',subscription:sub,guard:null,
 plan:{product:'guard_watch',proposal:true,network:'eip155:31611',asset:GUARD.musd,price_atomic:'2000000000000000000',period_days:30,pay_to:'0xd7f52d1ddb5dc8678191f14e439fc5db67541535',payments_enabled:true,free_trial:true,trial_days:30,enforced:true}}),{status:200,headers:{'content-type':'application/json'}});

test('panel stays disabled until a wallet is connected on Mezo Testnet', ()=>{
 const host=setup(new Map());
 const ctx={provider:null,account:null,onMezo:false};
 const panel=mountGuardPanel({host,getContext:()=>ctx,watchApi:'',now:()=>NOW});
 assert.match(text(host),/Connect your wallet/);
 assert.equal(find(host,'button','Calculate').disabled,true);
 Object.assign(ctx,{provider:{request:async()=>null},account:'0x1111111111111111111111111111111111111111',onMezo:false});panel.update();
 assert.match(text(host),/Switch the wallet to Mezo Testnet/);
});
test('calculate, deposit, sign and arm send exactly the expected Guard transactions', async ()=>{
 const wallet=Wallet.createRandom(),host=setup(new Map());
 const {p,g}=guardProvider(wallet);
 globalThis.fetch=watchFetch();
 const panel=mountGuardPanel({host,getContext:()=>({provider:p,account:wallet.address,onMezo:true}),watchApi:'http://127.0.0.1:8795',now:()=>NOW});
 await panel.refresh();
 assert.match(text(host),/No protection is armed/);
 assert.match(text(host),/Not active\. The keeper only executes protections for Troves with Guard Watch/);
 await find(host,'button','Calculate').click();
 assert.match(text(host),/Top-up: [0-9.]+ BTC/);
 assert.match(text(host),/already below this trigger/);
 await find(host,'button','1. Deposit').click();
 assert.equal(g.sent.length,1);assert.equal(g.sent[0].to,GUARD.address);assert.ok(BigInt(g.sent[0].value)>0n);
 const deposited=g.btc;
 await find(host,'button','2. Sign').click();
 assert.equal(g.signed.length,1);assert.equal(g.signed[0].primaryType,'AddColl');
 assert.equal(BigInt(g.signed[0].message.assetAmount),deposited,'reward 0: escrow equals signed amount');
 assert.equal(g.signed[0].domain.verifyingContract,GUARD.signatures);
 const dl=BigInt(g.signed[0].message.deadline);assert.ok(dl>NOW&&dl<=NOW+30n*86400n);
 await find(host,'button','3. Arm').click();
 assert.equal(g.sent.length,2);
 const arm=guard.parseTransaction({data:g.sent[1].data});
 assert.equal(arm.name,'arm');assert.equal(arm.args[0],2n);assert.equal(arm.args[1],17n*10n**17n);assert.equal(arm.args[2],deposited);
 assert.match(text(host),/Armed: add/);
 // every send was simulated first
 assert.ok(p.calls.filter(c=>c.method==='eth_call'&&c.params[0].from).length>=2);
});
test('arm refuses a signature whose Mezo nonce went stale', async ()=>{
 const wallet=Wallet.createRandom(),host=setup(new Map());
 const {p,g}=guardProvider(wallet);
 const panel=mountGuardPanel({host,getContext:()=>({provider:p,account:wallet.address,onMezo:true}),watchApi:'',now:()=>NOW});
 await panel.refresh();
 await find(host,'button','Calculate').click();
 await find(host,'button','2. Sign').click();
 g.nonce=1n;
 await find(host,'button','3. Arm').click();
 assert.match(text(host),/nonce changed since signing/);
 assert.equal(g.sent.filter(t=>guard.parseTransaction({data:t.data})?.name==='arm').length,0);
 assert.match(text(host),/not configured in this build/);
});
test('wallet on the wrong chain gets nothing sent', async ()=>{
 const wallet=Wallet.createRandom(),host=setup(new Map());
 const {p,g}=guardProvider(wallet,{chain:'0x1'});
 const panel=mountGuardPanel({host,getContext:()=>({provider:p,account:wallet.address,onMezo:true}),watchApi:'',now:()=>NOW});
 await panel.refresh();
 await find(host,'button','Calculate').click();
 await find(host,'button','1. Deposit').click();
 assert.equal(g.sent.length,0);assert.match(text(host),/Mezo Testnet/);assert.equal(p.calls.filter(c=>c.method==='eth_sendTransaction').length,0);
});
test('active Guard Watch trial is shown', async ()=>{
 const wallet=Wallet.createRandom(),host=setup(new Map());
 const {p}=guardProvider(wallet);
 globalThis.fetch=watchFetch({active:true,source:'trial',paidUntil:null,trialUntil:String(NOW+86400n),payments:0});
 const panel=mountGuardPanel({host,getContext:()=>({provider:p,account:wallet.address,onMezo:true}),watchApi:'http://127.0.0.1:8795',now:()=>NOW});
 await panel.refresh();await tick();
 assert.match(text(host),/Active \(trial until/);
});
test('a wallet without a Trove still sees Guard and Guard Watch status', async ()=>{
 const wallet=Wallet.createRandom(),host=setup(new Map());
 const {p}=guardProvider(wallet);p.state.coll=0n;
 const orig=p.request;p.request=async a=>{if(a.method==='eth_call'){const d=a.params[0].data;if(d.startsWith('0x21e37801'))return '0x'+'0'.repeat(64);}return orig(a);};
 globalThis.fetch=watchFetch();
 const panel=mountGuardPanel({host,getContext:()=>({provider:p,account:wallet.address,onMezo:true}),watchApi:'http://127.0.0.1:8795',now:()=>NOW});
 await panel.refresh();
 assert.match(text(host),/has no active Mezo Trove/);
 assert.match(text(host),/No protection is armed/);
 assert.match(text(host),/Price \(proposal\): 2 MUSD/);
});
test('protect() is offered only when the Guard reports Ready and uses fresh hints', async ()=>{
 const wallet=Wallet.createRandom(),host=setup(new Map());
 const {p,g}=guardProvider(wallet);
 const panel=mountGuardPanel({host,getContext:()=>({provider:p,account:wallet.address,onMezo:true}),watchApi:'',now:()=>NOW});
 await panel.refresh();
 assert.equal(find(host,'button','protect()').disabled,true);
 g.policy=[2,17n*10n**17n,10n**15n,0n,NOW+86400n,0n,'0x'+'11'.repeat(65)];g.btc=10n**15n;
 await panel.refresh();
 assert.equal(find(host,'button','protect()').disabled,false);
 await find(host,'button','protect()').click();
 const tx=g.sent.at(-1),fn=guard.parseTransaction({data:tx.data});
 assert.equal(fn.name,'protect');assert.equal(fn.args[0],wallet.address);
 assert.equal(fn.args[1],'0x2222222222222222222222222222222222222222');assert.equal(fn.args[2],'0x3333333333333333333333333333333333333333');
 assert.equal(p.nominal.at(-1)[0],p.state.coll+10n**15n);
});
