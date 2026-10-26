import {Interface} from 'ethers';
import * as p from '@liqvera/mezo-protocol';
export const W=10n**18n,borrower='0x1111111111111111111111111111111111111111';
export const upper='0x2222222222222222222222222222222222222222',lower='0x3333333333333333333333333333333333333333';
export const hash='0x'+'a'.repeat(64);
export function troveProvider(overrides={}){
 const calls=[],simulations=[],nominal=[];
 const s={coll:4n*W/100n,principal:2000n*W,interest:96n*W/100n,price:79740n*W,
 minimum:1800n*W,gasCompensation:200n*W,rate:W/1000n,mcr:11n*W/10n,ccr:15n*W/10n,
 systemColl:10n*W,systemDebt:100000n*W,capacity:1000000n*W,feeExempt:false,btc:W,musd:1000n*W,...overrides};
 const entries=[
 [p.MEZO_TESTNET_TROVES.troveManager,new Interface(p.MEZO_TESTNET_TROVE_MANAGER_ABI)],
 [p.MEZO_TESTNET_TROVES.borrowerOperations,new Interface(p.MEZO_TESTNET_BORROWER_OPERATIONS_ABI)],
 [p.MEZO_TESTNET_TROVES.priceFeed,new Interface(p.MEZO_TESTNET_PRICE_FEED_ABI)],
 [p.MEZO_TESTNET_TROVES.hintHelpers,new Interface(p.MEZO_TESTNET_HINT_HELPERS_ABI)],
 [p.MEZO_TESTNET_TROVES.sortedTroves,new Interface(p.MEZO_TESTNET_SORTED_TROVES_ABI)],
 [p.MUSD_TESTNET.address,new Interface(p.MUSD_ABI)],['0x4444444444444444444444444444444444444444',new Interface(p.MEZO_TESTNET_GOVERNABLE_VARIABLES_ABI)]];
 const provider={calls,simulations,nominal,state:s,request:async({method,params=[]})=>{
 calls.push({method,params});
 if(overrides.request){const r=await overrides.request({method,params});if(r!==undefined)return r;}
 if(method==='eth_chainId')return '0x7b7b';
 if(method==='eth_accounts')return [borrower];
 if(method==='eth_blockNumber')return '0x1234';
 if(method==='eth_getBalance')return '0x'+s.btc.toString(16);
 if(method==='eth_estimateGas')return '0x30d40';
 if(method==='eth_feeHistory')return {baseFeePerGas:['0x3b9aca00','0x3b9aca00'],reward:[['0x3b9aca00']]};
 if(method==='eth_sendTransaction')return hash;
 if(method==='eth_getTransactionReceipt')return {transactionHash:hash,status:'0x1',blockNumber:'0x1234',blockHash:'0x'+'b'.repeat(64)};
 if(method==='eth_getBlockByNumber')return {hash:'0x'+'b'.repeat(64)};
 if(method!=='eth_call')throw Error('Unexpected '+method);
 const tx=params[0],iface=entries.find(([address])=>address===tx.to)?.[1];
 const fn=iface?.parseTransaction({data:tx.data});if(!fn)throw Error('Unexpected call');
 const values={getTroveStatus:[1],getEntireDebtAndColl:[s.coll,s.principal,s.interest,0,0,0],
 MUSD_GAS_COMPENSATION:[s.gasCompensation],minNetDebt:[s.minimum],borrowingRate:[s.rate],
 MCR:[s.mcr],CCR:[s.ccr],getTCR:[s.systemColl*s.price/s.systemDebt],fetchPrice:[s.price],
 governableVariables:['0x4444444444444444444444444444444444444444'],isAccountFeeExempt:[s.feeExempt],getTroveMaxBorrowingCapacity:[s.capacity],getEntireSystemColl:[s.systemColl],getEntireSystemDebt:[s.systemDebt],balanceOf:[s.musd],
 getApproxHint:[upper,0,123],findInsertPosition:[upper,lower]};
 if(fn.name==='computeNominalCR'){nominal.push([...fn.args]);return iface.encodeFunctionResult(fn.name,[fn.args[0]*W/fn.args[1]]);}
 if(fn.name==='getBorrowingFee')return iface.encodeFunctionResult(fn.name,[fn.args[0]*s.rate/W]);
 if(['addColl','repayMUSD','withdrawMUSD'].includes(fn.name)){simulations.push({tx,block:params[1]});return '0x';}
 if(!values[fn.name])throw Error('Unexpected '+fn.name);
 return iface.encodeFunctionResult(fn.name,values[fn.name]);
 }};
 return provider;
}
