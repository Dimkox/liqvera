import assert from 'node:assert/strict';
import test from 'node:test';
import {mountTroveProtection} from '../src/trove-protection-panel.ts';
import {TroveActionStore} from '../src/trove-action-receipts.ts';
import {prepareTroveAction} from '../src/trove-transactions.ts';
import {troveProvider,borrower,hash} from './helpers/trove-provider.mjs';
import {setup,find,elements,text,tick} from './helpers/trove-dom.mjs';
const sha='d'.repeat(64),report={report_id:'report-panel',request:{borrower},trove_risk:{borrower,status:'ACTIVE'}};
const disk=()=>{const m=new Map();return {getItem:k=>m.get(k)??null,setItem:(k,v)=>m.set(k,v),removeItem:k=>m.delete(k)};};
function mount(p=troveProvider(),storage=disk(),current=()=>true){const host=setup(storage);mountTroveProtection(host,report,p,borrower,current,sha);return {host,p,storage};}
function formInput(host,label){return elements(host).find(e=>e.tagName==='input'&&e.getAttribute('aria-label')===label);}
test('panel requires borrower wallet and renders rescue plus collapsed borrowing',async()=>{
 const storage=disk(),host=setup(storage);
 mountTroveProtection(host,report,troveProvider(),'0x2222222222222222222222222222222222222222',()=>true,sha);
 assert.match(text(host),/Connect the borrower wallet/);
 const panel=mount();await tick();
 assert.ok(find(panel.host,'h4','Rescue to a target ratio'));
 assert.equal(find(panel.host,'details','').open,false);
});
test('previews appear before signing and rescue fill never submits a transaction',async()=>{
 const {host,p}=mount();await tick();await tick();
 const use=find(host,'button','Use in Add collateral');assert.ok(use);
 await use.click();
 const input=formInput(host,'BTC amount');assert.ok(Number(input.value)>0.0051);
 assert.equal(p.calls.some(x=>x.method==='eth_sendTransaction'),false);
 input.value='0.0005';await input.dispatch('input');
 await new Promise(resolve=>setTimeout(resolve,340));
 assert.match(text(host),/ICR now:.*after:/);
 const form=elements(host).find(e=>e.tagName==='form'&&elements(e).includes(input));
 await form.dispatch('submit');
 assert.match(text(host),/You will sign:/);
 assert.equal(p.calls.some(x=>x.method==='eth_sendTransaction'),false);
});
test('only second click signs, locks all action controls until receipt, and persists log',async()=>{
 let resolveReceipt;const receipt=new Promise(resolve=>resolveReceipt=resolve);
 const p=troveProvider({request:({method})=>method==='eth_getTransactionReceipt'?receipt:undefined});
 const {host,storage}=mount(p);await tick();await tick();
 const input=formInput(host,'BTC amount');input.value='0.0005';
 const form=elements(host).find(e=>e.tagName==='form'&&elements(e).includes(input));
 await form.dispatch('submit');
 const signing=find(host,'button','Sign in wallet');assert.ok(signing);
 const signingTask=signing.click();await tick();await tick();
 assert.equal(p.calls.filter(x=>x.method==='eth_sendTransaction').length,1);
 assert.ok(elements(host).filter(e=>e.tagName==='button'&&!['Download action receipts','Check confirmation'].includes(e.textContent)).every(e=>e.disabled));
 assert.equal(JSON.parse(storage.getItem('liqvera:trove-actions:report-panel'))[0].state,'pending');
 resolveReceipt({transactionHash:hash,status:'0x1',blockNumber:'0x1234',blockHash:'0x'+'b'.repeat(64)});
 await signingTask;
 assert.match(text(host),/Confirmed in block 4660/);
 assert.ok(find(host,'h4','Actions log'));
 const records=JSON.parse(storage.getItem('liqvera:trove-actions:report-panel'));
 assert.equal(records[0].receipt_status,'0x1');assert.ok(records[0].observed);
});
test('editing amount invalidates confirmation and changed wallet context cannot sign',async()=>{
 let current=true;const {host,p}=mount(troveProvider(),disk(),()=>current);await tick();
 const input=formInput(host,'BTC amount');input.value='0.0005';
 const form=elements(host).find(e=>e.tagName==='form'&&elements(e).includes(input));
 await form.dispatch('submit');
 const sign=find(host,'button','Sign in wallet');input.value='0.001';await input.dispatch('input');
 assert.equal(sign.disabled,true);
 await form.dispatch('submit');current=false;
 await find(host,'button','Sign in wallet').click();
 assert.equal(p.calls.some(x=>x.method==='eth_sendTransaction'),false);
});
test('reload of pending intent disables submission and offers confirmation only',async()=>{
 const storage=disk(),p=troveProvider();
 const store=new TroveActionStore(storage,{report_id:report.report_id,report_sha256:sha},borrower);
 const r=store.begin(await prepareTroveAction(p,borrower,{kind:'repay',amount:'0.5'}));
 store.update({...r,tx_hash:hash,state:'pending'});
 const {host}=mount(p,storage);await tick();
 assert.ok(find(host,'button','Check confirmation'));
 assert.ok(find(host,'button','Sign in wallet').disabled);
 assert.equal(p.calls.some(x=>x.method==='eth_sendTransaction'),false);
});
test('changed live terms require another confirmation without wallet submission',async()=>{
 const {host,p}=mount();await tick();const input=formInput(host,'BTC amount');input.value='0.0005';
 const form=elements(host).find(e=>e.tagName==='form'&&elements(e).includes(input));await form.dispatch('submit');
 p.state.price+=100n*10n**18n;
 await find(host,'button','Sign in wallet').click();
 assert.match(text(host),/Current terms changed/);
 assert.equal(p.calls.some(x=>x.method==='eth_sendTransaction'),false);
});
test('success persists even if refresh fails and a state-only refresh can recover',async()=>{
 let mined=false;const p=troveProvider({request:({method})=>{if(method==='eth_getTransactionReceipt')mined=true;if(mined&&method==='eth_blockNumber')throw Error('RPC unavailable');}});
 const {host,storage}=mount(p);await tick();const input=formInput(host,'BTC amount');input.value='0.0005';
 const form=elements(host).find(e=>e.tagName==='form'&&elements(e).includes(input));await form.dispatch('submit');
 await find(host,'button','Sign in wallet').click();
 assert.equal(JSON.parse(storage.getItem('liqvera:trove-actions:report-panel'))[0].receipt_status,'0x1');
 assert.match(text(host),/State refresh failed/);
 assert.ok(find(host,'button','Refresh Trove state'));
});
test('a delayed same-input preview cannot overwrite a newer reviewed preparation',async()=>{
 const {Interface}=await import('ethers');const protocol=await import('@liqvera/mezo-protocol');
 const priceAbi=new Interface(protocol.MEZO_TESTNET_PRICE_FEED_ABI);
 let release,held=false;const delayed=new Promise(resolve=>release=resolve);
 const p=troveProvider({request:({method,params=[]})=>{
  if(method==='eth_call'&&params[0].to===protocol.MEZO_TESTNET_TROVES.priceFeed&&!held){held=true;return delayed;}
 }});
 // Initial state load also reads price; let that finish before holding a preview.
 release(priceAbi.encodeFunctionResult('fetchPrice',[79740n*10n**18n]));
 const {host}=mount(p);await tick();await tick();
 held=false;const previewWait=new Promise(resolve=>release=resolve);
 // Replace the provider's request only for the next price call.
 const request=p.request;p.request=async args=>{
  if(args.method==='eth_call'&&args.params[0].to===protocol.MEZO_TESTNET_TROVES.priceFeed&&!held){held=true;return previewWait;}
  return request(args);
 };
 const input=formInput(host,'BTC amount');input.value='0.0005';await input.dispatch('input');
 await new Promise(resolve=>setTimeout(resolve,320));assert.equal(held,true);
 p.state.price+=1000n*10n**18n;
 const form=elements(host).find(e=>e.tagName==='form'&&elements(e).includes(input));await form.dispatch('submit');
 const preview=elements(form).find(e=>e.className==='trove-action-preview');const reviewed=preview.textContent;
 release(priceAbi.encodeFunctionResult('fetchPrice',[79740n*10n**18n]));await tick();await tick();
 assert.equal(preview.textContent,reviewed);
});
