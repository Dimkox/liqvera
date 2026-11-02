import test from 'node:test';
import assert from 'node:assert/strict';
import {Interface,Signature,Wallet,AbiCoder,keccak256,toUtf8Bytes,concat} from 'ethers';
import {GUARD,GUARD_ABI,HALF_N,calldata,checkSignature,guardDigest,guardTypedData,planGuard,readGuard,signGuardAuthorization,typedDataJson,validateDeadline} from '../src/guard.ts';
import {computeRescue,ratio,debtOf} from '../src/trove-math.ts';

const W=10n**18n;
// Snapshot of the team test wallet's Trove read from Mezo Testnet on 2026-11-02.
const s={coll:405n*W/10000n,principal:2000n*W,interest:8156n*W/10000n,price:77879n*W,minimum:1800n*W,gasCompensation:200n*W,rate:W/1000n,
 mcr:11n*W/10n,ccr:15n*W/10n,systemColl:10n*W,systemDebt:100000n*W,capacity:1000000n*W,feeExempt:false,btc:W,musd:1000n*W};
const wallet=Wallet.createRandom();
const guard=new Interface(GUARD_ABI);

test('planGuard sizes the top-up at the trigger price so it lifts ICR to the target', ()=>{
 const p=planGuard(s,170n*W/100n,180n*W/100n,'AddColl');
 const debt=debtOf(s);
 assert.ok(ratio(s.coll,debt,p.priceAtTrigger)>=170n*W/100n);
 assert.equal(p.amount,computeRescue({...s,price:p.priceAtTrigger},180n*W/100n).deposit);
 assert.ok(p.afterAtTrigger>=180n*W/100n);
 assert.equal(p.immediatelyReady,true,'ICR ~1.576 is below a 170% trigger');
 const later=planGuard(s,130n*W/100n,160n*W/100n,'AddColl');
 assert.equal(later.immediatelyReady,false);
 assert.ok(later.afterAtTrigger>=160n*W/100n);
});
test('planGuard rejects unsafe inputs and repays that break minimum net debt', ()=>{
 assert.throws(()=>planGuard(s,110n*W/100n,150n*W/100n,'AddColl'),/MCR/);
 assert.throws(()=>planGuard(s,1001n*W/100n,1100n*W/100n,'AddColl'),/1000%/);
 assert.throws(()=>planGuard(s,150n*W/100n,150n*W/100n,'AddColl'),/above the trigger/);
 assert.throws(()=>planGuard(s,170n*W/100n,180n*W/100n,'RepayMUSD'),/minimum net debt/);
});
test('typed data matches the Mezo BorrowerOperationsSignatures domain', ()=>{
 const t=guardTypedData('AddColl',123n,wallet.address,4n,1_800_000_000n);
 assert.deepEqual(t.domain,{name:'BorrowerOperationsSignatures',version:'1',chainId:31611,verifyingContract:GUARD.signatures});
 assert.deepEqual(t.types.AddColl.map(x=>x.name),['assetAmount','borrower','nonce','deadline']);
 const r=guardTypedData('RepayMUSD',1n,wallet.address,0n,1n);
 assert.deepEqual(r.types.RepayMUSD.map(x=>x.name),['amount','borrower','nonce','deadline']);
 const parsed=JSON.parse(typedDataJson(t));
 assert.equal(parsed.primaryType,'AddColl');assert.ok(parsed.types.EIP712Domain);
 // Manual EIP-712 encoding, independent of TypedDataEncoder.hash.
 const abi=AbiCoder.defaultAbiCoder(),k=x=>keccak256(toUtf8Bytes(x));
 const domainSep=keccak256(abi.encode(['bytes32','bytes32','bytes32','uint256','address'],[k('EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)'),k('BorrowerOperationsSignatures'),k('1'),31611n,GUARD.signatures]));
 const struct=keccak256(abi.encode(['bytes32','uint256','address','uint256','uint256'],[k('AddColl(uint256 assetAmount,address borrower,uint256 nonce,uint256 deadline)'),123n,wallet.address,4n,1_800_000_000n]));
 assert.equal(guardDigest(t),keccak256(concat(['0x1901',domainSep,struct])));
});
test('checkSignature accepts only what LiqveraGuard accepts', async ()=>{
 const t=guardTypedData('AddColl',5n,wallet.address,0n,1_800_000_000n);
 const sig=await wallet.signTypedData(t.domain,t.types,t.message);
 checkSignature(t,sig,wallet.address);
 assert.throws(()=>checkSignature(t,sig,Wallet.createRandom().address),/not made by the borrower/i);
 const parsed=Signature.from(sig),highS='0x'+(BigInt('0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141')-BigInt(parsed.s)).toString(16).padStart(64,'0');
 assert.ok(BigInt(highS)>HALF_N);
 assert.throws(()=>checkSignature(t,parsed.r+highS.slice(2)+(parsed.v===27?'1c':'1b'),wallet.address),/canonical form/);
 assert.throws(()=>checkSignature(t,'0x1234',wallet.address),/malformed/);
});
test('signGuardAuthorization normalizes v=0/1 and verifies the signer', async ()=>{
 const t=guardTypedData('AddColl',5n,wallet.address,0n,1_800_000_000n);
 const sig=await wallet.signTypedData(t.domain,t.types,t.message),low=sig.slice(0,130)+(sig.slice(130)==='1b'?'00':'01');
 const provider={request:async({method,params})=>{assert.equal(method,'eth_signTypedData_v4');assert.equal(params[0],wallet.address);return low;}};
 const r=await signGuardAuthorization(provider,wallet.address,'AddColl',5n,0n,1_800_000_000n);
 assert.equal(r.signature,sig);assert.equal(r.digest,guardDigest(t));
});
test('validateDeadline enforces the 30-day authorization window', ()=>{
 validateDeadline(1000n+86400n,1000n);
 assert.throws(()=>validateDeadline(999n,1000n),/30 days/);
 assert.throws(()=>validateDeadline(1000n+30n*86400n+1n,1000n),/30 days/);
});
test('calldata encodes the Guard entry points', ()=>{
 const sig='0x'+'11'.repeat(65);
 const arm=guard.parseTransaction({data:calldata.arm('AddColl',17n*W/10n,10n,1n,99n,sig)});
 assert.equal(arm.name,'arm');assert.deepEqual([...arm.args].slice(0,5),[2n,17n*W/10n,10n,1n,99n]);
 assert.equal(guard.parseTransaction({data:calldata.depositBTC()}).name,'depositBTC');
 assert.equal(guard.parseTransaction({data:calldata.protect(wallet.address,GUARD.address,GUARD.address)}).name,'protect');
});
test('readGuard decodes status, policy, escrow and nonce', async ()=>{
 const sigs=new Interface(['function getNonce(address) view returns (uint256)']);
 const provider={request:async({method,params})=>{
  assert.equal(method,'eth_call');const {to,data}=params[0];
  if(to===GUARD.signatures)return sigs.encodeFunctionResult('getNonce',[3n]);
  assert.equal(to,GUARD.address);const fn=guard.parseTransaction({data});
  const v={status:[0,15n*W/10n],policyOf:[[2,17n*W/10n,10n,1n,99n,3n,'0x'+'22'.repeat(65)]],btcBalance:[11n],musdBalance:[0n],freeBTC:[0n],freeMUSD:[0n]}[fn.name];
  return guard.encodeFunctionResult(fn.name,v);
 }};
 const g=await readGuard(provider,wallet.address);
 assert.equal(g.status,'Ready');assert.equal(g.nonce,3n);
 assert.deepEqual(g.policy,{action:2,triggerICR:17n*W/10n,amount:10n,keeperReward:1n,deadline:99n,sigNonce:3n});
 assert.equal(g.btcEscrow,11n);
});
test('Guard Watch checkout only accepts the exact 2 MUSD terms on Mezo Testnet', async ()=>{
 const {checkWatchTerms}=await import('../src/guard-watch.ts');
 const plan={pay_to:'0xd7f52d1ddb5dc8678191f14e439fc5db67541535'};
 const ok={scheme:'exact',network:'eip155:31611',asset:GUARD.musd,amount:'2000000000000000000',payTo:plan.pay_to};
 checkWatchTerms(ok,plan);
 for(const bad of [{amount:'2000000000000000001'},{network:'eip155:31612'},{payTo:wallet.address},{asset:wallet.address},{scheme:'upto'}])
  assert.throws(()=>checkWatchTerms({...ok,...bad},plan),/terms changed/);
 assert.throws(()=>checkWatchTerms(ok,{pay_to:null}),/terms changed/);
});
