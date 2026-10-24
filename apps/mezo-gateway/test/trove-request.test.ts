import assert from 'node:assert/strict';
import test from 'node:test';
import { quoteInput, decodeQuoteBody } from '../src/security/input.js';
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

test('Mezo DEX is an explicit, closed opt-in on a Market depth request',()=>{
  const selected={instrument_id:'hyperliquid:BTC:perpetual',side:'SELL',quantity_base:'0.25',expected_payer:payer,mezo_dex:true};
  assert.deepEqual(quoteInput(selected),selected);
  assert.deepEqual(decodeQuoteBody(Buffer.from(JSON.stringify(selected))),selected);
  for(const value of [false,'true',1,null])
    assert.throws(()=>quoteInput({...selected,mezo_dex:value}),PublicError);
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
