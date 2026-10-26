import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import test from 'node:test';
import {Interface} from 'ethers';
import * as protocol from '@liqvera/mezo-protocol';

const root=new URL('../../../',import.meta.url);
const sourceLock=JSON.parse(await readFile(new URL('packages/mezo-protocol/source-lock.json',root),'utf8'));
const explorerContracts=sourceLock.sources.testnet_explorer.contracts;
const implementations={
 BorrowerOperations:'packages/mezo-protocol/vendor/BorrowerOperations.implementation.testnet.json',
 HintHelpers:'packages/mezo-protocol/vendor/HintHelpers.implementation.testnet.json',
};

function functionFragment(abi,signature,mutability){
 const fragment=new Interface(abi).getFunction(signature);
 assert.ok(fragment,`missing ${signature}`);
 assert.equal(fragment.stateMutability,mutability);
}

test('Trove action metadata points to the documented Mezo Testnet proxies',()=>{
 assert.equal(protocol.MEZO_TESTNET_TROVES.borrowerOperations,'0xCdF7028ceAB81fA0C6971208e83fa7872994beE5');
 assert.equal(protocol.MEZO_TESTNET_TROVES.hintHelpers,'0x4e4cBA3779d56386ED43631b4dCD6d8EacEcBCF6');
});

test('Trove transaction ABIs expose only the verified operations and required fresh-hint reads',()=>{
 functionFragment(protocol.MEZO_TESTNET_BORROWER_OPERATIONS_ABI,'addColl(address,address)','payable');
 functionFragment(protocol.MEZO_TESTNET_BORROWER_OPERATIONS_ABI,'minNetDebt()','view');
 functionFragment(protocol.MEZO_TESTNET_BORROWER_OPERATIONS_ABI,'repayMUSD(uint256,address,address)','nonpayable');
 functionFragment(protocol.MEZO_TESTNET_HINT_HELPERS_ABI,'getApproxHint(uint256,uint256,uint256)','view');
 functionFragment(protocol.MEZO_TESTNET_HINT_HELPERS_ABI,'computeNominalCR(uint256,uint256)','pure');
 functionFragment(protocol.MEZO_TESTNET_TROVE_MANAGER_ABI,'getEntireDebtAndColl(address)','view');
 functionFragment(protocol.MEZO_TESTNET_TROVE_MANAGER_ABI,'getTroveStatus(address)','view');
 functionFragment(protocol.MEZO_TESTNET_SORTED_TROVES_ABI,'findInsertPosition(uint256,address,address)','view');
});

test('BorrowerOperations and HintHelpers ABIs remain bound to verified Testnet proxy and implementation records',async()=>{
 for(const name of ['BorrowerOperations','HintHelpers']){
  const proxy=explorerContracts.find(item=>item.name===name);
  const implementation=explorerContracts.find(item=>item.name===`${name}Implementation`);
  assert.ok(proxy,`missing ${name} proxy source-lock record`);
  assert.ok(implementation,`missing ${name} implementation source-lock record`);
  assert.equal(proxy.chain_id,31611);
  assert.equal(proxy.explorer_is_proxy,'true');
  assert.equal(proxy.address,protocol.MEZO_TESTNET_TROVES[name[0].toLowerCase()+name.slice(1)]);
  assert.equal(proxy.implementation_address,implementation.address);
  for(const record of [proxy,implementation]){
   const artifacts=[[record.local_path,record.sha256],[record.source_response.local_path,record.source_response.sha256]];
   if(record.implementation_metadata)artifacts.push([record.implementation_metadata.local_path,record.implementation_metadata.sha256]);
   for(const [artifact,expectedHash] of artifacts){
    const bytes=await readFile(new URL(`packages/mezo-protocol/${artifact}`,root));
    assert.equal(createHash('sha256').update(bytes).digest('hex'),expectedHash,`${name}: ${artifact} hash mismatch`);
   }
  }
  assert.ok(implementations[name]);
 }
});

import {prepareTroveAction,submitTroveAction} from '../src/trove-transactions.ts';
const wallet=(responses)=>({request:async({method,params})=>{
 const value=responses[method];if(typeof value==='function')return value(params);if(value instanceof Error)throw value;return value;
}});
test('Trove preparation rejects wrong chain and malformed or zero amounts before simulation',async()=>{
 const p=wallet({'eth_chainId':'0x1'});
 await assert.rejects(()=>prepareTroveAction(p,'0x1111111111111111111111111111111111111111',{kind:'deposit',amount:'0.1'}),/Mezo Testnet/);
 const correct=wallet({'eth_chainId':'0x7b7b'});
 for(const amount of ['0','1.0000000000000000001','-1','1e2']) await assert.rejects(()=>prepareTroveAction(correct,'0x1111111111111111111111111111111111111111',{kind:'deposit',amount}),/amount|greater than zero/i);
});
test('Trove submission rechecks chain and account before asking wallet to sign',async()=>{
 let sent=false;const p=wallet({'eth_chainId':'0x7b7b','eth_accounts':['0x2222222222222222222222222222222222222222'],'eth_sendTransaction':()=>{sent=true;return '0xabc'}});
 const prepared={kind:'deposit',account:'0x1111111111111111111111111111111111111111',chainId:31611,to:'0xCdF7028ceAB81fA0C6971208e83fa7872994beE5',data:'0x',value:'0x1',summary:'deposit'};
 await assert.rejects(()=>submitTroveAction(p,prepared),/account changed/i);assert.equal(sent,false);
});

test('Trove stale app context blocks submission and ambiguous wallet send is confirm-only',async()=>{
 const prepared={kind:'deposit',account:'0x1111111111111111111111111111111111111111',chainId:31611,to:protocol.MEZO_TESTNET_TROVES.borrowerOperations,data:'0x',value:'0x1',summary:'deposit'};
 let sent=false;const p=wallet({'eth_chainId':'0x7b7b','eth_accounts':[prepared.account],'eth_sendTransaction':()=>{sent=true;throw new Error('socket timeout');}});
 await assert.rejects(()=>submitTroveAction(p,prepared,()=>false),/Selected wallet changed/i);assert.equal(sent,false);
 await assert.rejects(()=>submitTroveAction(p,prepared),/outcome is unknown/i);assert.equal(sent,true);
 const rejected=Object.assign(new Error('User rejected request'),{code:4001});await assert.rejects(()=>submitTroveAction(wallet({'eth_chainId':'0x7b7b','eth_accounts':[prepared.account],'eth_sendTransaction':rejected}),prepared),error=>error===rejected);
});

import {troveProvider,W,borrower,upper,lower} from './helpers/trove-provider.mjs';
for(const [kind,method,amount] of [['deposit','addColl','0.0005'],['repay','repayMUSD','0.5'],['borrow','withdrawMUSD','1']]){
 test(`${kind} prepares exact payload, post-action hints and a same-block preview`,async()=>{
  const p=troveProvider(kind==='borrow'?{coll:W/10n}:{});
  const prepared=await prepareTroveAction(p,borrower,{kind,amount});
  const fn=new Interface(protocol.MEZO_TESTNET_BORROWER_OPERATIONS_ABI).parseTransaction({data:prepared.data});
  assert.equal(fn.name,method); assert.deepEqual([...fn.args].slice(-2),[upper,lower]);
  assert.equal(prepared.value,kind==='deposit'?'0x'+(W/2000n).toString(16):'0x0');
  assert.equal(prepared.blockNumber,'0x1234');
  assert.equal(prepared.before.debt,String(200096n*W/100n));
  assert.equal(prepared.after.debt,String(kind==='repay'?200046n*W/100n:kind==='borrow'?2001961n*W/1000n:200096n*W/100n));
  assert.deepEqual(p.nominal[0],[kind==='deposit'?405n*W/10000n:p.state.coll,kind==='borrow'?2001001n*W/1000n:2000n*W]);
  assert.equal(p.simulations[0].block,'0x1234');
  assert.ok(p.calls.filter(x=>x.method==='eth_call').every(x=>x.params[1]==='0x1234'));
  assert.ok(p.calls.some(x=>x.method==='eth_estimateGas'));
  assert.equal(p.calls.some(x=>x.method==='eth_sendTransaction'),false);
  assert.equal(p.calls.some(x=>x.method==='eth_call'&&x.params[0].data.startsWith('0x095ea7b3')),false);
 });
}
test('repayment above protocol limit rejects before simulation and reports maximum',async()=>{
 const p=troveProvider();
 await assert.rejects(()=>prepareTroveAction(p,borrower,{kind:'repay',amount:'1'}),/minimum net debt.*0.96/s);
 assert.equal(p.simulations.length,0);
});
test('repayment hints subtract principal only after paying interest',async()=>{
 const p=troveProvider({principal:3000n*W,interest:50n*W});
 await prepareTroveAction(p,borrower,{kind:'repay',amount:'100'});
 assert.deepEqual(p.nominal[0],[p.state.coll,2950n*W]);
});
test('borrow rejects unsafe ICR, Recovery Mode and unsafe system TCR before simulation',async()=>{
 for(const [state,message] of [[{},/below 1.8/],[{coll:W,systemDebt:600000n*W},/Recovery Mode/],[{coll:W,systemColl:W,systemDebt:53159n*W},/system collateral ratio/i]]){
  const p=troveProvider(state);
  await assert.rejects(()=>prepareTroveAction(p,borrower,{kind:'borrow',amount:'100'}),message);
  assert.equal(p.simulations.length,0);
 }
});
test('gas funding is checked for every action and exact deposit reserve is returned',async()=>{
 for(const kind of ['deposit','repay','borrow']){
  const p=troveProvider({btc:kind==='deposit'?W/2000n:0n,coll:W/10n});
  await assert.rejects(()=>prepareTroveAction(p,borrower,{kind,amount:kind==='deposit'?'0.0005':'0.5'}),/BTC balance|gas/i);
 }
 const p=troveProvider();const prepared=await prepareTroveAction(p,borrower,{kind:'deposit',amount:'0.1'});
 assert.ok(BigInt(prepared.gas)>200000n);assert.ok(BigInt(prepared.maxFeePerGas)>0n);
});
test('borrow respects account borrowing capacity and exempts protocol fee-exempt borrowers',async()=>{
 const capped=troveProvider({coll:W/10n,capacity:2002n*W});
 await assert.rejects(()=>prepareTroveAction(capped,borrower,{kind:'borrow',amount:'2'}),/borrowing capacity/i);
 const exempt=troveProvider({coll:W/10n,feeExempt:true});
 const p=await prepareTroveAction(exempt,borrower,{kind:'borrow',amount:'1'});
 assert.equal(p.fee,'0');assert.equal(p.after.debt,String(200196n*W/100n));
 assert.deepEqual(exempt.nominal[0],[W/10n,2001n*W]);
});
test('display-bound review tolerates sub-display accrual but requires review of visible changes',async()=>{
 const p=troveProvider({interest:96n*W/100n+123n});
 const first=await prepareTroveAction(p,borrower,{kind:'deposit',amount:'0.0005'});
 p.state.interest+=1n;
 const next=await prepareTroveAction(p,borrower,{kind:'deposit',amount:'0.0005'});
 const {sameTroveTerms}=await import('../src/trove-transactions.ts');
 assert.equal(sameTroveTerms(first,next),true);
 p.state.interest+=W/100n;
 assert.equal(sameTroveTerms(first,await prepareTroveAction(p,borrower,{kind:'deposit',amount:'0.0005'})),false);
});
