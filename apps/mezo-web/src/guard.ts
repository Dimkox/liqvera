// LiqveraGuard client logic for Mezo Testnet: reads, EIP-712 authorization, calldata. No DOM here.
// The wallet signs everything; this module never holds a key and never sends without the wallet.
import {Interface,TypedDataEncoder,getAddress,recoverAddress} from 'ethers';
import {computeRescue,debtOf,ratio} from './trove-math.ts';
import type {TroveState} from './trove-math.ts';
import type {Eip1193Provider} from './wallet.ts';

export const GUARD={
 address:'0x61e12BDDFa62adF0Ffa89544153954a2420cF37a',chainId:31611,chainHex:'0x7b7b',deployBlock:16524690,
 deployTx:'0x8fb90b1f369dae3041892f378c2b153533bfdd499a04ce439710ac569cf81175',
 signatures:'0xD757e3646AF370b15f32EB557F0F8380Df7D639e',musd:'0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503',
 explorer:'https://explorer.test.mezo.org',
} as const;
export const WAD=10n**18n;
export const MAX_TRIGGER_ICR=10n*WAD;
export const MAX_SIGNATURE_TTL=30n*24n*3600n;
export const HALF_N=0x7fffffffffffffffffffffffffffffff5d576e7357a4501ddfe92f46681b20a0n;
export const ACTION={RepayMUSD:1,AddColl:2} as const;
export type GuardAction=keyof typeof ACTION;
export const GUARD_STATUS=['Ready','NoPolicy','Expired','StaleNonce','TroveNotActive','Healthy','BelowMinNetDebt','StillBelowMCR'] as const;
export const GUARD_ABI=[
 'function depositMUSD(uint256 amount)','function depositBTC() payable',
 'function withdrawMUSD(uint256 amount)','function withdrawBTC(uint256 amount)',
 'function arm(uint8 action,uint96 triggerICR,uint128 amount,uint128 keeperReward,uint64 deadline,bytes signature)',
 'function disarm()','function protect(address borrower,address upperHint,address lowerHint)',
 'function status(address borrower) view returns (uint8 s,uint256 icr)',
 'function policyOf(address user) view returns (tuple(uint8 action,uint96 triggerICR,uint128 amount,uint128 keeperReward,uint64 deadline,uint256 sigNonce,bytes signature))',
 'function freeMUSD(address user) view returns (uint256)','function freeBTC(address user) view returns (uint256)',
 'function musdBalance(address user) view returns (uint256)','function btcBalance(address user) view returns (uint256)',
 'function digest(uint8 action,uint256 amount,address borrower,uint256 nonce,uint256 deadline) view returns (bytes32)',
] as const;
export const guardInterface=new Interface(GUARD_ABI);
const signaturesInterface=new Interface(['function getNonce(address user) view returns (uint256)']);
const erc20=new Interface(['function approve(address spender,uint256 amount) returns (bool)','function allowance(address owner,address spender) view returns (uint256)']);

/** Mezo BorrowerOperationsSignatures domain and the two Guard-supported message types. */
export function guardTypedData(action:GuardAction,amount:bigint,borrower:string,nonce:bigint,deadline:bigint){
 const domain={name:'BorrowerOperationsSignatures',version:'1',chainId:GUARD.chainId,verifyingContract:GUARD.signatures};
 const types=action==='AddColl'
  ?{AddColl:[{name:'assetAmount',type:'uint256'},{name:'borrower',type:'address'},{name:'nonce',type:'uint256'},{name:'deadline',type:'uint256'}]}
  :{RepayMUSD:[{name:'amount',type:'uint256'},{name:'borrower',type:'address'},{name:'nonce',type:'uint256'},{name:'deadline',type:'uint256'}]};
 const message=action==='AddColl'
  ?{assetAmount:amount.toString(),borrower:getAddress(borrower),nonce:nonce.toString(),deadline:deadline.toString()}
  :{amount:amount.toString(),borrower:getAddress(borrower),nonce:nonce.toString(),deadline:deadline.toString()};
 return {domain,types,primaryType:action,message};
}
/** JSON for eth_signTypedData_v4, including EIP712Domain as wallets require. */
export function typedDataJson(t:ReturnType<typeof guardTypedData>):string{
 return JSON.stringify({...t,types:{EIP712Domain:[{name:'name',type:'string'},{name:'version',type:'string'},{name:'chainId',type:'uint256'},{name:'verifyingContract',type:'address'}],...t.types}});
}
export function guardDigest(t:ReturnType<typeof guardTypedData>):string{
 return TypedDataEncoder.hash(t.domain,t.types as unknown as Record<string,{name:string;type:string}[]>,t.message);
}
/** Same acceptance rule as LiqveraGuard._recover: 65 bytes, v in {27,28}, low s, signer = borrower. */
export function checkSignature(t:ReturnType<typeof guardTypedData>,signature:string,borrower:string):void{
 if(!/^0x[0-9a-fA-F]{130}$/.test(signature))throw new Error('The wallet returned a malformed signature.');
 const v=Number.parseInt(signature.slice(130),16),s=BigInt(`0x${signature.slice(66,130)}`);
 if((v!==27&&v!==28)||s>HALF_N)throw new Error('The wallet signature is not in the canonical form the Guard accepts.');
 if(getAddress(recoverAddress(guardDigest(t),signature))!==getAddress(borrower))throw new Error('The signature was not made by the borrower wallet.');
}

export interface GuardPlan{action:GuardAction;trigger:bigint;target:bigint;amount:bigint;priceAtTrigger:bigint;icrNow:bigint;
 immediatelyReady:boolean;repayAvailable:boolean;afterAtTrigger:bigint}
/**
 * Size the top-up so that, at the moment the trigger fires (ICR == trigger), executing it lifts ICR to the target.
 * Reuses the 'Protect this Trove' calculation (computeRescue, +0.5% buffer) evaluated at the trigger price,
 * so the amount does not depend on today's price.
 */
export function planGuard(s:TroveState,trigger:bigint,target:bigint,action:GuardAction):GuardPlan{
 const debt=debtOf(s);
 if(trigger<=s.mcr)throw new Error('The trigger ratio must be above the Mezo minimum (MCR).');
 if(trigger>MAX_TRIGGER_ICR)throw new Error('The trigger ratio must be at most 1000%.');
 if(target<=trigger)throw new Error('The target ratio must be above the trigger ratio.');
 const priceAtTrigger=(trigger*debt+s.coll-1n)/s.coll;
 const rescue=computeRescue({...s,price:priceAtTrigger},target);
 const amount=action==='AddColl'?rescue.deposit:rescue.repay;
 if(amount<=0n)throw new Error('No top-up is needed for this target.');
 if(action==='RepayMUSD'&&!rescue.repayAvailable)throw new Error('Repaying this much would break the Mezo minimum net debt. Use BTC collateral instead.');
 const afterAtTrigger=action==='AddColl'?ratio(s.coll+amount,debt,priceAtTrigger):ratio(s.coll,debt-amount,priceAtTrigger);
 const icrNow=ratio(s.coll,debt,s.price);
 return {action,trigger,target,amount,priceAtTrigger,icrNow,immediatelyReady:icrNow<trigger,repayAvailable:rescue.repayAvailable,afterAtTrigger};
}
export function validateDeadline(deadline:bigint,now:bigint):void{
 if(deadline<now||deadline>now+MAX_SIGNATURE_TTL)throw new Error('The authorization deadline must be within 30 days.');
}

export const calldata={
 depositBTC:()=>guardInterface.encodeFunctionData('depositBTC',[]),
 depositMUSD:(amount:bigint)=>guardInterface.encodeFunctionData('depositMUSD',[amount]),
 approveMUSD:(amount:bigint)=>erc20.encodeFunctionData('approve',[GUARD.address,amount]),
 arm:(action:GuardAction,trigger:bigint,amount:bigint,reward:bigint,deadline:bigint,signature:string)=>
  guardInterface.encodeFunctionData('arm',[ACTION[action],trigger,amount,reward,deadline,signature]),
 disarm:()=>guardInterface.encodeFunctionData('disarm',[]),
 protect:(borrower:string,upper:string,lower:string)=>guardInterface.encodeFunctionData('protect',[getAddress(borrower),upper,lower]),
 withdrawBTC:(amount:bigint)=>guardInterface.encodeFunctionData('withdrawBTC',[amount]),
 withdrawMUSD:(amount:bigint)=>guardInterface.encodeFunctionData('withdrawMUSD',[amount]),
};

const call=async(provider:Eip1193Provider,to:string,data:string)=>String(await provider.request({method:'eth_call',params:[{to,data},'latest']}));
export interface GuardSnapshot{status:typeof GUARD_STATUS[number];icr:bigint;policy:{action:number;triggerICR:bigint;amount:bigint;keeperReward:bigint;deadline:bigint;sigNonce:bigint}|null;
 btcEscrow:bigint;musdEscrow:bigint;freeBTC:bigint;freeMUSD:bigint;nonce:bigint}
export async function readGuard(provider:Eip1193Provider,borrower:string):Promise<GuardSnapshot>{
 const b=getAddress(borrower),g=(name:string,args:unknown[]=[b])=>call(provider,GUARD.address,guardInterface.encodeFunctionData(name,args)).then(r=>guardInterface.decodeFunctionResult(name,r));
 const [st,pol,btc,musd,fb,fm,nonce]=await Promise.all([g('status'),g('policyOf'),g('btcBalance'),g('musdBalance'),g('freeBTC'),g('freeMUSD'),
  call(provider,GUARD.signatures,signaturesInterface.encodeFunctionData('getNonce',[b])).then(r=>signaturesInterface.decodeFunctionResult('getNonce',r))]);
 const p=pol[0];
 return {status:GUARD_STATUS[Number(st[0])]??'NoPolicy',icr:BigInt(st[1]),
  policy:Number(p.action)===0?null:{action:Number(p.action),triggerICR:BigInt(p.triggerICR),amount:BigInt(p.amount),keeperReward:BigInt(p.keeperReward),deadline:BigInt(p.deadline),sigNonce:BigInt(p.sigNonce)},
  btcEscrow:BigInt(btc[0]),musdEscrow:BigInt(musd[0]),freeBTC:BigInt(fb[0]),freeMUSD:BigInt(fm[0]),nonce:BigInt(nonce[0])};
}
export async function readMusdAllowance(provider:Eip1193Provider,owner:string):Promise<bigint>{
 const r=await call(provider,GUARD.musd,erc20.encodeFunctionData('allowance',[getAddress(owner),GUARD.address]));
 return BigInt(erc20.decodeFunctionResult('allowance',r)[0]);
}
/** Ask the wallet for the Mezo EIP-712 authorization and check it the same way the Guard will. */
export async function signGuardAuthorization(provider:Eip1193Provider,borrower:string,action:GuardAction,amount:bigint,nonce:bigint,deadline:bigint){
 const t=guardTypedData(action,amount,borrower,nonce,deadline);
 let signature=String(await provider.request({method:'eth_signTypedData_v4',params:[getAddress(borrower),typedDataJson(t)]}));
 // Some wallets return v as 0/1; the Guard (like ecrecover) needs 27/28.
 if(/^0x[0-9a-fA-F]{128}0[01]$/.test(signature))signature=`${signature.slice(0,130)}${(Number.parseInt(signature.slice(130),16)+27).toString(16)}`;
 checkSignature(t,signature,borrower);
 return {signature,digest:guardDigest(t),typed:t};
}
export {debtOf};
