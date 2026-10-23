import {parseUnits} from 'ethers';
export type BtcSaleSlice={amountIn:bigint;amountOut:bigint;feeBtc:bigint;impactBps:number};
export type BtcSalePlan={executable:boolean;reason?:string;totalIn:bigint;estimatedOut:bigint;estimatedFeeBtc:bigint;feeBps:bigint;slices:BtcSaleSlice[];aggregateImpactBps:number;impactCapBps:number;slippageBps:number};
export type PoolState={reserveBtc:bigint;reserveMusd:bigint;feeBps:bigint};
export function parseBtcAmount(value:string):bigint{if(typeof value!=='string'||value.length>40||!/^(0|[1-9][0-9]*)(\.[0-9]{1,18})?$/.test(value))throw new Error('Enter a valid BTC amount with at most 18 decimals.');const amount=parseUnits(value,18);if(amount<=0n)throw new Error('Amount must be greater than zero.');return amount;}
export function quoteBtcToMusd(amount:bigint,state:PoolState):bigint{
 if(amount<=0n||state.reserveBtc<=0n||state.reserveMusd<=0n||state.feeBps<0n||state.feeBps>=10000n)throw new Error('Pool state or amount is not executable.');
 const net=amount-(amount*state.feeBps/10000n);return state.reserveMusd*net/(state.reserveBtc+net);
}
function impactBps(amount:bigint,out:bigint,state:PoolState){const spotOutput=amount*state.reserveMusd;const actualOutput=out*state.reserveBtc;return Number((spotOutput-actualOutput)*10000n/spotOutput);}
function maxPart(state:PoolState,cap:number):bigint{
 let lo=1n,hi=state.reserveBtc;
 while(lo<hi){const mid=(lo+hi+1n)/2n;const out=quoteBtcToMusd(mid,state);if(impactBps(mid,out,state)<=cap)lo=mid;else hi=mid-1n;}
 return lo;
}
export function planBtcSale(totalIn:bigint,state:PoolState,impactCapBps=100,slippageBps=100):BtcSalePlan{
 if(!Number.isInteger(impactCapBps)||impactCapBps<=0||impactCapBps>5000||!Number.isInteger(slippageBps)||slippageBps<0||slippageBps>5000)return {executable:false,reason:'Impact and slippage settings must be between 0.01% and 50%.',totalIn,estimatedOut:0n,estimatedFeeBtc:0n,feeBps:state.feeBps,slices:[],aggregateImpactBps:0,impactCapBps,slippageBps};
 if(totalIn<=0n||state.reserveBtc<=0n||state.reserveMusd<=0n||state.feeBps<0n||state.feeBps>=10000n)return {executable:false,reason:'Amount or pool state is not executable.',totalIn,estimatedOut:0n,estimatedFeeBtc:0n,feeBps:state.feeBps,slices:[],aggregateImpactBps:0,impactCapBps,slippageBps};
 const slices:BtcSaleSlice[]=[];let remaining=totalIn,resBtc=state.reserveBtc,resMusd=state.reserveMusd;
 while(remaining>0n&&slices.length<1000){const current={...state,reserveBtc:resBtc,reserveMusd:resMusd};const max=maxPart(current,impactCapBps);const part=remaining<max?remaining:max;if(part<=0n)break;const out=quoteBtcToMusd(part,current);const impact=impactBps(part,out,current);if(out<=0n||impact>impactCapBps)return {executable:false,reason:'Trade cannot be split into executable parts under this impact cap.',totalIn,estimatedOut:0n,estimatedFeeBtc:0n,feeBps:state.feeBps,slices:[],aggregateImpactBps:0,impactCapBps,slippageBps};const feeBtc=part*state.feeBps/10000n;slices.push({amountIn:part,amountOut:out,feeBtc,impactBps:impact});remaining-=part;resBtc+=part;resMusd-=out;}
 if(remaining>0n)return {executable:false,reason:'Trade requires too many parts.',totalIn,estimatedOut:0n,estimatedFeeBtc:0n,feeBps:state.feeBps,slices:[],aggregateImpactBps:0,impactCapBps,slippageBps};
 const output=slices.reduce((n,s)=>n+s.amountOut,0n);const estimatedFeeBtc=slices.reduce((n,s)=>n+s.feeBtc,0n);const aggregate=impactBps(totalIn,output,state);
 return {executable:true,totalIn,estimatedOut:output,estimatedFeeBtc,feeBps:state.feeBps,slices,aggregateImpactBps:aggregate,impactCapBps,slippageBps};
}
export function minOutForQuote(quoted:bigint,slippageBps:number):bigint{if(quoted<=0n||!Number.isInteger(slippageBps)||slippageBps<0||slippageBps>5000)throw new Error('Invalid quote or slippage tolerance.');return quoted*BigInt(10000-slippageBps)/10000n;}
