import assert from 'node:assert/strict';
import test from 'node:test';
import { MUSD_TRANSFER_EVENT } from '@liqvera/mezo-protocol';
import { MezoReceiptReader } from '../src/adapters/mezo-rpc.js';
import { AMOUNT, ASSET, NETWORK, PublicError, type Attempt, type Quote } from '../src/domain/model.js';

const buyer='0x1111111111111111111111111111111111111111';
const payTo='0x2222222222222222222222222222222222222222';
const facilitator='0x3333333333333333333333333333333333333333';
const txHash=`0x${'4'.repeat(64)}`;
const blockHash=`0x${'5'.repeat(64)}`;
const topic=(address:string)=>`0x${'0'.repeat(24)}${address.slice(2)}`;
const quote={id:'00000000-0000-4000-8000-000000000001',report_id:'00000000-0000-4000-8000-000000000002',report_sha256:'a'.repeat(64),terms:{expected_payer:buyer,pay_to:payTo}} as Quote;
const attempt={id:'00000000-0000-4000-8000-000000000003',quote_id:quote.id,state:'UNKNOWN',authorization_identity:'b'.repeat(64),identity_version:'test',authorization_valid_until:new Date('2026-09-29T00:05:00Z'),correlation:{buyer_native_balance_before:'1000'},tx_hash:txHash,submitted_at:new Date('2026-09-29T00:00:00Z'),reconciliation_count:1} as Attempt;

function rpc(change:Record<string,unknown>={}) {
  const transaction={hash:txHash,from:facilitator,to:ASSET,input:'0x',...(change.transaction as object ?? {})};
  const log={address:ASSET,topics:[MUSD_TRANSFER_EVENT.topic0,topic(buyer),topic(payTo)],data:`0x${BigInt(AMOUNT).toString(16).padStart(64,'0')}`,transactionHash:txHash,blockHash,logIndex:'0x0',...(change.log as object ?? {})};
  const receipt={status:'0x1',transactionHash:txHash,blockHash,blockNumber:'0x64',logs:[log]};
  return {call:async(method:string,params:unknown[])=>{
    if(method==='eth_chainId')return '0x7b7b';
    if(method==='eth_getTransactionReceipt')return receipt;
    if(method==='eth_getBlockByNumber')return {number:params[0],hash:blockHash};
    if(method==='eth_getTransactionByHash')return transaction;
    if(method==='eth_getBalance')return Object.hasOwn(change,'balance')?change.balance:'0x3e8';
    throw new Error(method);
  }};
}
const identity={reviewed:true,version:'test',identify(){throw new Error('unused');},async bindsTransfer(){return true;}};
const finality={reviewed:true,version:'mezo-testnet-canonical-12/v1',async isFinal(){return true;}};

test('facilitator broadcast and zero buyer native gas produce exact receipt',async()=>{
  const reader=new MezoReceiptReader(rpc() as never,identity as never,finality as never);
  const receipt=await reader.confirmation(quote,attempt);
  assert.equal(receipt?.tx_hash,txHash);
  assert.equal(receipt?.payer,buyer);
  assert.equal(receipt?.amount_atomic,AMOUNT);
});

test('buyer broadcast, buyer balance delta, or missing balance proof fails closed',async()=>{
  for(const change of [{transaction:{from:buyer},balance:'0x384'},{balance:'0x384'},{balance:null}]) {
    const reader=new MezoReceiptReader(rpc(change) as never,identity as never,finality as never);
    await assert.rejects(reader.confirmation(quote,attempt),(error:unknown)=>error instanceof PublicError&&error.code==='MANUAL_REVIEW');
  }
});

test('buyer broadcast with native gas delta above approved cap fails closed',async()=>{
  const highBalanceAttempt={...attempt,correlation:{...attempt.correlation,buyer_native_balance_before:'100000000000001'}};
  const reader=new MezoReceiptReader(rpc({transaction:{from:buyer},balance:'0x0'}) as never,identity as never,finality as never);
  await assert.rejects(reader.confirmation(quote,highBalanceAttempt),(error:unknown)=>error instanceof PublicError&&error.code==='MANUAL_REVIEW');
});

test('wrong token, payee, or value cannot bind the payment',async()=>{
  const changes=[
    {log:{address:'0x4444444444444444444444444444444444444444'}},
    {log:{topics:[MUSD_TRANSFER_EVENT.topic0,topic(buyer),topic(facilitator)]}},
    {log:{data:`0x${'0'.repeat(63)}1`}},
  ];
  for(const change of changes) {
    const reader=new MezoReceiptReader(rpc(change) as never,identity as never,finality as never);
    assert.equal(await reader.confirmation(quote,attempt),null);
  }
});
