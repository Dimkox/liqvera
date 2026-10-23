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
