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
