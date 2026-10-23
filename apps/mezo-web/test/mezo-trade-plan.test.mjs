import assert from 'node:assert/strict';
import test from 'node:test';
import {Interface} from 'ethers';
import * as protocol from '@liqvera/mezo-protocol';
import {minOutForQuote,parseBtcAmount,planBtcSale,quoteBtcToMusd} from '../src/mezo-trade-plan.ts';
const state={reserveBtc:1000n*10n**18n,reserveMusd:500000n*10n**18n,feeBps:4n};
test('Mezo Testnet protocol metadata includes a source ABI for exact Router swap and token allowance',()=>{
 const router=new Interface(protocol.MEZO_TESTNET_ROUTER_ABI);assert.ok(router.getFunction('swapExactTokensForTokens(uint256,uint256,(address,address,bool,address)[],address,uint256)'));assert.ok(router.getFunction('getReserves(address,address,bool,address)'));
 const token=new Interface(protocol.MEZO_TESTNET_ERC20_TRADE_ABI);assert.ok(token.getFunction('approve(address,uint256)'));assert.ok(token.getFunction('allowance(address,address)'));
 assert.equal(protocol.MEZO_TESTNET_DEX.router,'0x9a1ff7FE3a0F69959A3fBa1F1e5ee18e1A9CD7E9');
});
test('BTC sale amount parsing is exact and rejects invalid precision',()=>{assert.equal(parseBtcAmount('1.25'),125n*10n**16n);for(const x of ['0','1e2','-1','0.0000000000000000001'])assert.throws(()=>parseBtcAmount(x));});
test('pool quote uses fee truncation before constant-product division',()=>{const amount=10n**18n;const fee=amount*4n/10000n;assert.equal(quoteBtcToMusd(amount,state),state.reserveMusd*(amount-fee)/(state.reserveBtc+amount-fee));});
test('auto split keeps every slice at or below editable 1% impact and computes independent slippage minimum',()=>{
 const plan=planBtcSale(300n*10n**18n,state,100,100);assert.equal(plan.executable,true);assert.ok(plan.slices.length>1);assert.ok(plan.slices.every(x=>x.impactBps<=100));assert.equal(plan.aggregateImpactBps,plan.aggregateImpactBps);
 assert.equal(minOutForQuote(10000n,100),9900n);assert.equal(plan.slippageBps,100);
});
test('planner rejects bad pool and invalid tolerance while retaining tiny executable input',()=>{
 assert.equal(planBtcSale(10n,{...state,reserveBtc:0n}).executable,false);
 assert.equal(planBtcSale(1n,state,100,5001).executable,false);
 assert.equal(planBtcSale(1n,state).executable,true); assert.equal(planBtcSale(0n,state).executable,false);
});
