/** Amounts, prices and ratios are WAD-scaled bigint; no floating point math. */
export const WAD=10n**18n;
export const FALLBACK_GAS_RESERVE=WAD/10000n;
export type TroveState={coll:bigint;principal:bigint;interest:bigint;price:bigint;
 minimum:bigint;gasCompensation:bigint;rate:bigint;mcr:bigint;ccr:bigint;
 systemColl:bigint;systemDebt:bigint};
export type TroveBalances={btc:bigint;musd:bigint;gasReserve:bigint};
export const ceilDiv=(a:bigint,b:bigint)=>(a+b-1n)/b;
const max=(a:bigint,b:bigint)=>a>b?a:b;
const min=(a:bigint,b:bigint)=>a<b?a:b;
export const safeRatio=(state:TroveState)=>max(18n*WAD/10n,state.ccr+WAD/10n);
export const debtOf=(state:TroveState)=>state.principal+state.interest;
export const ratio=(coll:bigint,debt:bigint,price:bigint)=>coll*price/debt;
export function validateState(s:TroveState):void{
 if(Object.values(s).some(v=>typeof v!=='bigint'||v<0n)||s.price===0n||debtOf(s)===0n||
 s.systemDebt===0n||s.mcr===0n||s.ccr<s.mcr)throw new Error('Invalid current Trove state.');
}
export function computeLimits(s:TroveState,b:TroveBalances){
 validateState(s);
 const debt=debtOf(s),netRoom=max(0n,debt-s.gasCompensation-s.minimum);
 const room=min(max(0n,s.coll*s.price/safeRatio(s)-debt),max(0n,s.systemColl*s.price/s.ccr-s.systemDebt));
 // Binary search uses the exact contract fee truncation, including atomic boundaries.
 let lo=0n,hi=room;
 while(lo<hi){const mid=(lo+hi+1n)/2n;if(mid+mid*s.rate/WAD<=room)lo=mid;else hi=mid-1n;}
 return {deposit:max(0n,b.btc-b.gasReserve),repay:min(max(0n,b.musd),netRoom),
 borrow:s.systemColl*s.price/s.systemDebt<s.ccr?0n:lo,safeIcr:safeRatio(s)};
}
export function computeRescue(s:TroveState,targetIcr:bigint){
 validateState(s);
 if(targetIcr<s.mcr+WAD/20n||targetIcr>1000n*WAD)throw new Error('Enter a valid target ICR at or above MCR + 0.05.');
 const debt=debtOf(s),alreadyAbove=s.coll*s.price/debt>=targetIcr;
 const buffer=(x:bigint)=>ceilDiv(x*1005n,1000n);
 const deposit=alreadyAbove?0n:buffer(max(0n,ceilDiv(targetIcr*debt,s.price)-s.coll));
 const repay=alreadyAbove?0n:buffer(max(0n,debt-s.coll*s.price/targetIcr));
 return {deposit,repay,alreadyAbove,repayAvailable:repay<=max(0n,debt-s.gasCompensation-s.minimum)};
}
