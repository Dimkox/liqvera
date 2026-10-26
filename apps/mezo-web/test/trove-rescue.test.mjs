import assert from 'node:assert/strict';
import test from 'node:test';
import * as math from '../src/trove-math.ts';
const W=10n**18n;
const state={coll:4n*W/100n,principal:2000n*W,interest:96n*W/100n,price:79740n*W,
 minimum:1800n*W,gasCompensation:200n*W,rate:W/1000n,mcr:11n*W/10n,ccr:15n*W/10n,
 systemColl:10n*W,systemDebt:100000n*W};
const balances={btc:W,musd:1000n*W,gasReserve:W/10000n};
test('rescue rounds upward with buffer and hides repayment beyond minimum debt',()=>{
 assert.equal(typeof math.computeRescue,'function');
 const rescue=math.computeRescue(state,18n*W/10n);
 assert.ok(rescue.deposit>517n*W/100000n&&rescue.deposit<525n*W/100000n);
 assert.equal(rescue.repayAvailable,false);
 assert.ok(rescue.repay>229n*W);
 assert.equal(math.computeRescue(state,15n*W/10n).alreadyAbove,true);
});
test('limits reserve BTC gas and enforce minimum debt with exact atomic rounding',()=>{
 assert.equal(typeof math.computeLimits,'function');
 const limits=math.computeLimits(state,balances);
 assert.equal(limits.deposit,9999n*W/10000n);
 assert.equal(limits.repay,96n*W/100n);
 assert.equal(limits.borrow,0n);
 assert.equal(math.computeLimits(state,{...balances,btc:0n}).deposit,0n);
 assert.equal(math.computeLimits({...state,interest:0n},balances).repay,0n);
});
test('borrow maximum includes system TCR and exact truncated fee',()=>{
 assert.equal(typeof math.computeLimits,'function');
 const s={...state,coll:W,systemColl:W,systemDebt:53000n*W};
 const x=math.computeLimits(s,balances).borrow;
 assert.ok(x>0n);
 const fee=x*s.rate/W;
 assert.ok(s.systemColl*s.price/(s.systemDebt+x+fee)>=s.ccr);
 assert.ok(s.systemColl*s.price/(s.systemDebt+x+1n+(x+1n)*s.rate/W)<s.ccr);
 assert.equal(math.computeLimits({...s,systemDebt:60000n*W},balances).borrow,0n);
});
test('rescue checks buffer against limits and validates target/state',()=>{
 assert.equal(typeof math.computeRescue,'function');
 assert.throws(()=>math.computeRescue(state,0n),/target/i);
 assert.throws(()=>math.computeRescue({...state,price:0n},2n*W),/state/i);
 const s={...state,coll:W/5n,principal:6000n*W,interest:0n};
 const r=math.computeRescue(s,2n*W);
 assert.equal(r.deposit,0n); assert.equal(r.repay,0n);
 const boundary={...state,principal:2200n*W,interest:0n,coll:5n*W/100n,price:79740n*W};
 assert.equal(math.computeRescue(boundary,2n*W).repayAvailable,false);
});
test('borrowing limit includes per-Trove capacity and account fee exemption',()=>{
 const s={...state,coll:W/10n,capacity:2002n*W,feeExempt:false};
 const cap=math.computeLimits(s,balances).borrow;
 assert.ok(cap+cap*s.rate/W<=104n*W/100n);
 assert.ok(cap+1n+(cap+1n)*s.rate/W>104n*W/100n);
 assert.equal(math.computeLimits({...s,feeExempt:true},balances).borrow,104n*W/100n);
});
