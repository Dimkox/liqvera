import assert from 'node:assert/strict';
import test from 'node:test';
import * as receipts from '../src/trove-action-receipts.ts';
import {prepareTroveAction} from '../src/trove-transactions.ts';
import {troveProvider,borrower,hash} from './helpers/trove-provider.mjs';
const report={report_id:'sample-report',report_sha256:'d'.repeat(64)};
export function storage(){const items=new Map();return {getItem:k=>items.get(k)??null,setItem:(k,v)=>items.set(k,v),removeItem:k=>items.delete(k)};}
test('intent and hash persist before receipt, recover on reload and bind original report hash',async()=>{
 assert.equal(typeof receipts.TroveActionStore,'function');
 const disk=storage(),prepared=await prepareTroveAction(troveProvider(),borrower,{kind:'deposit',amount:'0.0005'});
 const store=new receipts.TroveActionStore(disk,report,borrower);
 const record=store.begin(prepared);assert.equal(record.tx_hash,null);
 assert.equal(new receipts.TroveActionStore(disk,report,borrower).unresolved().state,'awaiting_wallet');
 store.update({...record,tx_hash:hash,state:'pending'});
 const reload=new receipts.TroveActionStore(disk,report,borrower);
 assert.equal(reload.unresolved().tx_hash,hash);
 assert.equal(reload.records()[0].report_sha256,report.report_sha256);
 assert.equal(new receipts.TroveActionStore(disk,{...report,report_id:'another'},borrower).unresolved().tx_hash,hash);
 assert.throws(()=>reload.begin(prepared),/unresolved/i);
 const saved=reload.update({...reload.unresolved(),state:'confirmed',receipt_block:'0x1234',receipt_status:'0x1'});
 assert.equal(reload.unresolved(),null);assert.equal(saved.receipt_status,'0x1');
 assert.equal(JSON.parse(reload.exportJson())[0].tx_hash,hash);
});
test('storage failure disables new signing and corrupt guards fail closed',async()=>{
 assert.equal(typeof receipts.TroveActionStore,'function');
 const prepared=await prepareTroveAction(troveProvider(),borrower,{kind:'repay',amount:'0.5'});
 const disk={getItem:()=>null,setItem:()=>{throw Error('Quota exceeded');},removeItem:()=>{}};
 const store=new receipts.TroveActionStore(disk,report,borrower);
 assert.throws(()=>store.begin(prepared),/storage/i);
 const broken=storage();broken.setItem('liqvera:trove-unresolved:31611:'+borrower,'broken');
 assert.throws(()=>new receipts.TroveActionStore(broken,report,borrower).unresolved(),/storage|record/i);
});
test('polling requires same chain, matching hash, canonical block and valid status',async()=>{
 assert.equal(typeof receipts.waitTroveReceipt,'function');
 const p=troveProvider();const result=await receipts.waitTroveReceipt(p,hash,{attempts:1,intervalMs:0});
 assert.equal(result.blockNumber,'0x1234');
 for(const response of [{transactionHash:'0x'+'c'.repeat(64),status:'0x1',blockNumber:'0x1'},
 {transactionHash:hash,status:'0x2',blockNumber:'0x1'},
 {transactionHash:hash,status:'0x1',blockNumber:'0x1',blockHash:'0x'+'c'.repeat(64)}]){
  await assert.rejects(()=>receipts.waitTroveReceipt(troveProvider({request:({method})=>method==='eth_getTransactionReceipt'?response:undefined}),hash,{attempts:1,intervalMs:0}),/receipt|canonical/i);
 }
 await assert.rejects(()=>receipts.waitTroveReceipt(troveProvider({request:({method})=>method==='eth_chainId'?'0x1':undefined}),hash,{attempts:1,intervalMs:0}),/Mezo Testnet/);
 await assert.rejects(()=>receipts.waitTroveReceipt(troveProvider({request:({method})=>method==='eth_getTransactionReceipt'?null:undefined}),hash,{attempts:1,intervalMs:0}),/pending/i);
});
test('another tab sees newer confirmed evidence instead of its cached pending record',async()=>{
 const disk=storage(),p=troveProvider(),a=new receipts.TroveActionStore(disk,report,borrower);
 const r=a.begin(await prepareTroveAction(p,borrower,{kind:'repay',amount:'0.5'}));
 a.update({...r,tx_hash:hash,state:'pending'});
 const b=new receipts.TroveActionStore(disk,report,borrower);assert.equal(b.records()[0].state,'pending');
 a.update({...r,tx_hash:hash,state:'confirmed',receipt_block:'0x1234',receipt_status:'0x1'});
 assert.equal(b.records()[0].state,'confirmed');
 assert.equal(JSON.parse(b.exportJson())[0].receipt_status,'0x1');
});
test('failed hash persistence retains receipt-only recovery from memory without dropping the guard',async()=>{
 const disk=storage(),store=new receipts.TroveActionStore(disk,report,borrower);
 const r=store.begin(await prepareTroveAction(troveProvider(),borrower,{kind:'repay',amount:'0.5'}));
 disk.setItem=()=>{throw Error('Quota exceeded');};
 store.update({...r,tx_hash:hash,state:'pending'});
 assert.equal(store.unresolved().tx_hash,hash);
 assert.match(store.warning,/storage/);
 assert.equal(JSON.parse(store.exportJson())[0].tx_hash,hash);
});
test('terminal evidence from another tab outranks dirty unsaved pending evidence',async()=>{
 const disk=storage(),a=new receipts.TroveActionStore(disk,report,borrower),write=disk.setItem;
 const r=a.begin(await prepareTroveAction(troveProvider(),borrower,{kind:'repay',amount:'0.5'}));
 disk.setItem=(k,v)=>{if(k===a.reportKey)throw Error('Quota exceeded');write(k,v);};
 a.update({...r,tx_hash:hash,state:'pending'});disk.setItem=write;
 const b=new receipts.TroveActionStore(disk,report,borrower);
 b.update({...b.unresolved(),state:'confirmed',receipt_status:'0x1',receipt_block:'0x1234'});
 assert.equal(a.records()[0].state,'confirmed');
});
