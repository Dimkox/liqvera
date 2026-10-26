import assert from 'node:assert/strict';
import test from 'node:test';
import { quoteInput, decodeQuoteBody, decodeRecoveryBody } from '../src/security/input.js';
import { PublicError } from '../src/domain/model.js';
// Borrower returned by the retained SortedTroves native proof at block16320987.
const borrower='0xDA04759E54728B6636Fe48F7c9795c7B609bAaAa';
const payer='0x1111111111111111111111111111111111111111';
const input={product_id:'trove_risk',borrower,expected_payer:payer};

test('Trove request is a closed checksum-address product and preserves borrower binding',()=>{
  assert.deepEqual(quoteInput(input),input);
  assert.deepEqual(decodeQuoteBody(Buffer.from(JSON.stringify(input))),input);
  const other={...input,borrower:'0x2222222222222222222222222222222222222222'};
  assert.notEqual(JSON.stringify(quoteInput(input)),JSON.stringify(quoteInput(other)));
});

test('legacy market request keeps its exact four-field canonical representation',()=>{
  const legacy=quoteInput({instrument_id:'hyperliquid:BTC:perpetual',side:'BUY',quantity_base:'+00.2500',expected_payer:payer});
  assert.equal(JSON.stringify(legacy),'{"instrument_id":"hyperliquid:BTC:perpetual","side":"BUY","quantity_base":"0.25","expected_payer":"PAYER"}'.replace('PAYER',payer));
  assert.equal(Object.keys(legacy).length,4);
});

for(const value of [borrower.toLowerCase(),borrower.toUpperCase(),'0x'+'0'.repeat(40),'invalid',null]){
  test('invalid or noncanonical Trove borrower returns API400 before capture: '+String(value),()=>{
    assert.throws(()=>quoteInput({...input,borrower:value}),(error:unknown)=>error instanceof PublicError&&error.code==='INVALID_INPUT'&&error.status===400);
  });
}

for(const mixed of [{side:'BUY'},{instrument_id:'hyperliquid:BTC:perpetual'},{quantity_base:'1'},{extra:true}]){
  test('mixed Trove/market request fields are rejected: '+Object.keys(mixed)[0],()=>{
    assert.throws(()=>quoteInput({...input,...mixed}),PublicError);
  });
}

test('duplicate Trove JSON field names cannot change the hash-bound borrower',()=>{
  const raw=`{"product_id":"trove_risk","borrower":"${borrower}","borrower":"0x2222222222222222222222222222222222222222","expected_payer":"${payer}"}`;
  assert.throws(()=>decodeQuoteBody(Buffer.from(raw)),PublicError);
});

test('transaction recovery body accepts only one exact hash and safe block number',()=>{
  const tx=`0x${'a'.repeat(64)}`;
  assert.deepEqual(decodeRecoveryBody(Buffer.from(JSON.stringify({tx_hash:tx,block_number:'16329223'}))),{tx_hash:tx,block_number:16329223});
  for(const raw of [
    `{"tx_hash":"${tx}","tx_hash":"${tx}","block_number":16329223}`,
    JSON.stringify({tx_hash:tx,block_number:1.5}),JSON.stringify({tx_hash:'0x1234',block_number:16329223}),
    JSON.stringify({tx_hash:tx,block_number:Number.MAX_SAFE_INTEGER+1}),JSON.stringify({tx_hash:tx,block_number:16329223,extra:true}),
  ]) assert.throws(()=>decodeRecoveryBody(Buffer.from(raw)),(error:unknown)=>error instanceof PublicError&&error.code==='INVALID_INPUT');
});
