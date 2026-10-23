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

test('Trove deposit obtains fresh hints, simulates BorrowerOperations, then returns exact wallet payload',async()=>{
 const manager=new Interface(protocol.MEZO_TESTNET_TROVE_MANAGER_ABI),hh=new Interface(protocol.MEZO_TESTNET_HINT_HELPERS_ABI),sorted=new Interface(protocol.MEZO_TESTNET_SORTED_TROVES_ABI),bo=new Interface(protocol.MEZO_TESTNET_BORROWER_OPERATIONS_ABI);
 const borrower='0x1111111111111111111111111111111111111111',upper='0x2222222222222222222222222222222222222222',lower='0x3333333333333333333333333333333333333333';const order=[];
 const provider={request:async({method,params=[]})=>{
  if(method==='eth_chainId')return '0x7b7b';if(method==='eth_blockNumber')return '0x1234';if(method==='eth_getBalance')return `0x${(10n**21n).toString(16)}`;
  if(method!=='eth_call')throw Error(method);const tx=params[0];if(tx.to===protocol.MEZO_TESTNET_TROVES.troveManager){const x=manager.parseTransaction({data:tx.data});order.push(x.name);if(x.name==='getTroveStatus')return manager.encodeFunctionResult(x.name,[1]);if(x.name==='getEntireDebtAndColl')return manager.encodeFunctionResult(x.name,[2n*10n**18n,1000n*10n**18n,1n*10n**18n,0,0,0]);}
  if(tx.to===protocol.MEZO_TESTNET_TROVES.hintHelpers){const x=hh.parseTransaction({data:tx.data});order.push(x.name);if(x.name==='computeNominalCR')return hh.encodeFunctionResult(x.name,[2n*10n**15n]);if(x.name==='getApproxHint')return hh.encodeFunctionResult(x.name,[upper,0,123]);}
  if(tx.to===protocol.MEZO_TESTNET_TROVES.sortedTroves){const x=sorted.parseTransaction({data:tx.data});order.push(x.name);return sorted.encodeFunctionResult(x.name,[upper,lower]);}
  if(tx.to===protocol.MEZO_TESTNET_TROVES.borrowerOperations){const x=bo.parseTransaction({data:tx.data});if(x.name==='addColl'){order.push('simulate');return '0x';}}
  throw Error(`unexpected ${tx.to}`);
 }};
 const prepared=await prepareTroveAction(provider,borrower,{kind:'deposit',amount:'0.25'});assert.equal(prepared.value,`0x${(25n*10n**16n).toString(16)}`);assert.equal(prepared.to,protocol.MEZO_TESTNET_TROVES.borrowerOperations);const encoded=bo.parseTransaction({data:prepared.data});assert.equal(encoded.name,'addColl');assert.deepEqual([...encoded.args],[upper,lower]);assert.deepEqual(order,['getTroveStatus','getEntireDebtAndColl','computeNominalCR','getApproxHint','findInsertPosition','simulate']);
});
test('Trove repayment enforces live debt guards, obtains new hints and simulates exact MUSD call',async()=>{
 const manager=new Interface(protocol.MEZO_TESTNET_TROVE_MANAGER_ABI),hh=new Interface(protocol.MEZO_TESTNET_HINT_HELPERS_ABI),sorted=new Interface(protocol.MEZO_TESTNET_SORTED_TROVES_ABI),bo=new Interface(protocol.MEZO_TESTNET_BORROWER_OPERATIONS_ABI),musd=new Interface(protocol.MUSD_ABI);
 const borrower='0x1111111111111111111111111111111111111111',hint='0x2222222222222222222222222222222222222222',sequence=[];
 const provider={request:async({method,params=[]})=>{if(method==='eth_chainId')return '0x7b7b';if(method==='eth_blockNumber')return '0x1234';if(method==='eth_call'){const tx=params[0];if(tx.to===protocol.MEZO_TESTNET_TROVES.troveManager){const x=manager.parseTransaction({data:tx.data});if(x.name==='getTroveStatus')return manager.encodeFunctionResult(x.name,[1]);if(x.name==='getEntireDebtAndColl')return manager.encodeFunctionResult(x.name,[2n*10n**18n,3000n*10n**18n,0,0,0,0]);if(x.name==='MUSD_GAS_COMPENSATION')return manager.encodeFunctionResult(x.name,[200n*10n**18n]);}
 if(tx.to===protocol.MEZO_TESTNET_TROVES.borrowerOperations){const x=bo.parseTransaction({data:tx.data});if(x.name==='minNetDebt')return bo.encodeFunctionResult(x.name,[1800n*10n**18n]);if(x.name==='repayMUSD'){sequence.push('simulate');return '0x';}}
 if(tx.to===protocol.MUSD_TESTNET.address)return musd.encodeFunctionResult('balanceOf',[2000n*10n**18n]);
 if(tx.to===protocol.MEZO_TESTNET_TROVES.hintHelpers){const x=hh.parseTransaction({data:tx.data});sequence.push(x.name);if(x.name==='computeNominalCR')return hh.encodeFunctionResult(x.name,[7n*10n**14n]);if(x.name==='getApproxHint')return hh.encodeFunctionResult(x.name,[hint,0,456]);}
 if(tx.to===protocol.MEZO_TESTNET_TROVES.sortedTroves)return sorted.encodeFunctionResult('findInsertPosition',[hint,hint]);}
 throw Error(`unexpected ${method}`);}};
 const prepared=await prepareTroveAction(provider,borrower,{kind:'repay',amount:'100'});assert.equal(prepared.value,'0x0');const fn=bo.parseTransaction({data:prepared.data});assert.equal(fn.name,'repayMUSD');assert.equal(fn.args[0],100n*10n**18n);assert.deepEqual(sequence,['computeNominalCR','getApproxHint','simulate']);
});
