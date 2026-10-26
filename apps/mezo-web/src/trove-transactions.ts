import {Interface, getAddress, parseUnits, formatUnits} from 'ethers';
import {
 MEZO_TESTNET, MEZO_TESTNET_HINT_HELPERS_ABI, MEZO_TESTNET_SORTED_TROVES_ABI,
 MEZO_TESTNET_TROVE_MANAGER_ABI, MEZO_TESTNET_TROVES, MEZO_TESTNET_BORROWER_OPERATIONS_ABI,
 MEZO_TESTNET_PRICE_FEED_ABI, MEZO_TESTNET_GOVERNABLE_VARIABLES_ABI, MUSD_TESTNET, MUSD_ABI,
} from '@liqvera/mezo-protocol';
import type {Eip1193Provider} from './wallet.ts';
import {sendWalletTransaction} from './wallet-submission.ts';
import {FALLBACK_GAS_RESERVE,computeLimits,computeRescue,debtOf,ratio,safeRatio,validateState} from './trove-math.ts';
import type {TroveState,TroveBalances} from './trove-math.ts';
export {computeLimits,computeRescue};
export type TroveAction={kind:'deposit'|'repay'|'borrow';amount:string};
export type TroveSnapshot={coll:string;debt:string;icr:string;liquidationPrice:string};
export type PreparedTroveAction={kind:TroveAction['kind'];account:string;chainId:number;to:string;data:string;value:string;summary:string;
 amount:string;fee:string;upperHint:string;lowerHint:string;blockNumber:string;before:TroveSnapshot;after:TroveSnapshot;
 gas:string;maxFeePerGas?:string;maxPriorityFeePerGas?:string;gasReserve:string};
const bo=new Interface(MEZO_TESTNET_BORROWER_OPERATIONS_ABI),manager=new Interface(MEZO_TESTNET_TROVE_MANAGER_ABI);
const hints=new Interface(MEZO_TESTNET_HINT_HELPERS_ABI),sorted=new Interface(MEZO_TESTNET_SORTED_TROVES_ABI);
const musd=new Interface(MUSD_ABI),priceFeed=new Interface(MEZO_TESTNET_PRICE_FEED_ABI);
const governance=new Interface(MEZO_TESTNET_GOVERNABLE_VARIABLES_ABI);
const rpc=(provider:Eip1193Provider,method:string,params:unknown[]=[])=>provider.request({method,params});
const hex=(v:bigint)=>`0x${v.toString(16)}`;
async function read(provider:Eip1193Provider,to:string,abi:Interface,name:string,args:unknown[],blockTag:string){
 const result=await rpc(provider,'eth_call',[{to,data:abi.encodeFunctionData(name,args)},blockTag]);
 return abi.decodeFunctionResult(name,String(result));
}
export function parseTroveAmount(raw:string):bigint{
 if(typeof raw!=='string'||raw.length>40||!/^(0|[1-9][0-9]*)(\.[0-9]{1,18})?$/.test(raw))throw new Error('Enter a valid amount with at most 18 decimals.');
 const value=parseUnits(raw,18);if(value<=0n)throw new Error('Amount must be greater than zero.');return value;
}
async function requireChain(provider:Eip1193Provider){
 if(BigInt(String(await rpc(provider,'eth_chainId')))!==BigInt(MEZO_TESTNET.chainId))throw new Error('Switch to Mezo Testnet before preparing this action.');
}
export async function readTroveState(provider:Eip1193Provider,account:string,blockTag:string):Promise<TroveState>{
 const borrower=getAddress(account);
 const tm=(name:string,args:unknown[]=[])=>read(provider,MEZO_TESTNET_TROVES.troveManager,manager,name,args,blockTag);
 const op=(name:string)=>read(provider,MEZO_TESTNET_TROVES.borrowerOperations,bo,name,[],blockTag);
 if(Number((await tm('getTroveStatus',[borrower]))[0])!==1)throw new Error('This wallet does not have an active Trove.');
 const [values,price,minimum,gasCompensation,rate,mcr,ccr,systemColl,systemDebt,capacity,governable]=await Promise.all([
 tm('getEntireDebtAndColl',[borrower]),read(provider,MEZO_TESTNET_TROVES.priceFeed,priceFeed,'fetchPrice',[],blockTag),
 op('minNetDebt'),tm('MUSD_GAS_COMPENSATION'),op('borrowingRate'),tm('MCR'),tm('CCR'),op('getEntireSystemColl'),op('getEntireSystemDebt'),tm('getTroveMaxBorrowingCapacity',[borrower]),op('governableVariables')]);
 const feeExempt=Boolean((await read(provider,getAddress(String(governable[0])),governance,'isAccountFeeExempt',[borrower],blockTag))[0]);
 // Aggregate values already include pending redistribution; never count its breakdown twice.
 const state={coll:BigInt(values[0]),principal:BigInt(values[1]),interest:BigInt(values[2]),price:BigInt(price[0]),
 minimum:BigInt(minimum[0]),gasCompensation:BigInt(gasCompensation[0]),rate:BigInt(rate[0]),mcr:BigInt(mcr[0]),ccr:BigInt(ccr[0]),
 systemColl:BigInt(systemColl[0]),systemDebt:BigInt(systemDebt[0]),capacity:BigInt(capacity[0]),feeExempt};
 validateState(state);return state;
}
export async function readTroveContext(provider:Eip1193Provider,account:string,minimumBlock?:string){
 await requireChain(provider);const blockNumber=String(await rpc(provider,'eth_blockNumber'));
 if(minimumBlock&&BigInt(blockNumber)<BigInt(minimumBlock))throw new Error('RPC state is behind the confirmed transaction. Refresh again.');
 const [state,btc,balance]=await Promise.all([readTroveState(provider,account,blockNumber),rpc(provider,'eth_getBalance',[account,blockNumber]),read(provider,MUSD_TESTNET.address,musd,'balanceOf',[account],blockNumber)]);
 const balances:TroveBalances={btc:BigInt(String(btc)),musd:BigInt(balance[0]),gasReserve:FALLBACK_GAS_RESERVE};
 return {state,balances,blockNumber};
}
async function freshHints(provider:Eip1193Provider,coll:bigint,principal:bigint,blockTag:string){
 const nicr=BigInt((await read(provider,MEZO_TESTNET_TROVES.hintHelpers,hints,'computeNominalCR',[coll,principal],blockTag))[0]);
 const seed=BigInt(`0x${Array.from(crypto.getRandomValues(new Uint8Array(32)),b=>b.toString(16).padStart(2,'0')).join('')}`);
 const approx=(await read(provider,MEZO_TESTNET_TROVES.hintHelpers,hints,'getApproxHint',[nicr,15,seed],blockTag))[0];
 const pos=await read(provider,MEZO_TESTNET_TROVES.sortedTroves,sorted,'findInsertPosition',[nicr,approx,approx],blockTag);
 return [String(pos[0]),String(pos[1])] as const;
}
export const snapshot=(s:TroveState,coll=s.coll,debt=debtOf(s)):TroveSnapshot=>({coll:String(coll),debt:String(debt),
 icr:String(ratio(coll,debt,s.price)),liquidationPrice:String(debt*s.mcr/coll)});
class GasBalanceError extends Error{
 reserve:bigint;
 constructor(reserve:bigint){super('Wallet BTC balance is too low for this deposit or transaction gas.');this.reserve=reserve;}
}
export async function prepareTroveAction(provider:Eip1193Provider,account:string,action:TroveAction):Promise<PreparedTroveAction>{
 await requireChain(provider);const amount=parseTroveAmount(action.amount),borrower=getAddress(account);
 if(!['deposit','repay','borrow'].includes(action.kind))throw new Error('Unsupported Trove action.');
 const {state:s,balances,blockNumber}=await readTroveContext(provider,borrower);
 let coll=s.coll,debt=debtOf(s),principal=s.principal,fee=0n,value=0n;
 if(action.kind==='deposit'){coll+=amount;value=amount;if(balances.btc<amount)throw new GasBalanceError(FALLBACK_GAS_RESERVE);}
 else if(action.kind==='repay'){
  if(amount>balances.musd)throw new Error('Wallet MUSD balance is too low for this repayment.');
  const max=computeLimits(s,balances).repay;
  if(amount>max)throw new Error(`Repayment must leave the protocol minimum net debt and gas reserve. Max repayable now: ${formatUnits(max,18)} MUSD.`);
  debt-=amount;principal-=amount>s.interest?amount-s.interest:0n;
 }else{
  if(s.systemColl*s.price/s.systemDebt<s.ccr)throw new Error('Borrowing is disabled in Recovery Mode.');
  fee=s.feeExempt?0n:BigInt((await read(provider,MEZO_TESTNET_TROVES.borrowerOperations,bo,'getBorrowingFee',[amount],blockNumber))[0]);
  debt+=amount+fee;principal+=amount+fee;
  if(debt>s.capacity!)throw new Error('This would exceed the Trove borrowing capacity.');
  if(ratio(coll,debt,s.price)<safeRatio(s))throw new Error(`This would lower ICR below ${formatUnits(safeRatio(s),18)}.`);
  if(s.systemColl*s.price/(s.systemDebt+amount+fee)<s.ccr)throw new Error('This would lower the system collateral ratio below CCR.');
 }
 const [upperHint,lowerHint]=await freshHints(provider,coll,principal,blockNumber);
 const method=action.kind==='deposit'?'addColl':action.kind==='repay'?'repayMUSD':'withdrawMUSD';
 const data=bo.encodeFunctionData(method,action.kind==='deposit'?[upperHint,lowerHint]:[amount,upperHint,lowerHint]);
 const tx={from:borrower,to:MEZO_TESTNET_TROVES.borrowerOperations,data,value:hex(value)};
 await rpc(provider,'eth_call',[tx,blockNumber]);
 const estimate=BigInt(String(await rpc(provider,'eth_estimateGas',[tx,blockNumber])));
 if(estimate<=0n)throw new Error('Gas estimation failed.');
 const gas=hex((estimate*120n+99n)/100n);let reserve=FALLBACK_GAS_RESERVE;
 let fees:{maxFeePerGas?:string;maxPriorityFeePerGas?:string}={};
 try{
  const history=await rpc(provider,'eth_feeHistory',['0x1',blockNumber,[50]]) as {baseFeePerGas:string[];reward?:string[][]};
  const base=BigInt(history.baseFeePerGas.at(-1)!),tip=BigInt(history.reward?.[0]?.[0]??'0x0');
  const cap=base*2n+tip;if(cap<=0n)throw new Error('Invalid fee data');
  fees={maxFeePerGas:hex(cap),maxPriorityFeePerGas:hex(tip)};
  const estimated=BigInt(gas)*cap;if(estimated>reserve)reserve=estimated;
 }catch{/* Conservative native reserve remains visible if fee history is unavailable. */}
 if(value+reserve>balances.btc)throw new GasBalanceError(reserve);
 return {kind:action.kind,account:borrower,chainId:MEZO_TESTNET.chainId,to:tx.to,data,value:tx.value,
 amount:String(amount),fee:String(fee),upperHint,lowerHint,blockNumber,before:snapshot(s),after:snapshot(s,coll,debt),gas,...fees,gasReserve:String(reserve),
 summary:action.kind==='deposit'?`Add ${action.amount} BTC to your Trove`:action.kind==='repay'?`Repay ${action.amount} MUSD`:`Borrow ${action.amount} MUSD`};
}
export async function maxTroveAction(provider:Eip1193Provider,account:string,kind:TroveAction['kind']):Promise<string>{
 const context=await readTroveContext(provider,account);let amount=computeLimits(context.state,context.balances)[kind];
 for(let i=0;i<4;i++){
  if(amount<=0n)throw new Error('No amount is available for this action.');
  try{await prepareTroveAction(provider,account,{kind,amount:formatUnits(amount,18)});return formatUnits(amount,18);}
  catch(error){if(kind!=='deposit'||!(error instanceof GasBalanceError))throw error;amount=context.balances.btc-error.reserve;}
 }
 throw new Error('Max could not be simulated. Refresh the Trove state and try again.');
}
/** Human review uses declared conservative display bounds; exact state remains in evidence. */
export function displayTroveSnapshot(s:TroveSnapshot){
 const rounded=(raw:string,places:number,up=false)=>{
  const factor=10n**BigInt(18-places),n=BigInt(raw);
  return formatUnits((up?(n+factor-1n)/factor:n/factor)*factor,18);
 };
 return {coll:formatUnits(s.coll,18),debt:rounded(s.debt,3,true),icr:rounded(s.icr,5),liquidationPrice:rounded(s.liquidationPrice,2,true)};
}
export function sameTroveTerms(a:PreparedTroveAction,b:PreparedTroveAction):boolean{
 // Hints and sub-display interest accrual may change. Every exact safety guard is rechecked.
 return JSON.stringify([a.kind,a.account,a.amount,a.fee,a.value,displayTroveSnapshot(a.before),displayTroveSnapshot(a.after),a.gas,a.maxFeePerGas,a.maxPriorityFeePerGas])===
 JSON.stringify([b.kind,b.account,b.amount,b.fee,b.value,displayTroveSnapshot(b.before),displayTroveSnapshot(b.after),b.gas,b.maxFeePerGas,b.maxPriorityFeePerGas]);
}
export async function submitTroveAction(provider:Eip1193Provider,prepared:PreparedTroveAction,isCurrent:()=>boolean=()=>true):Promise<string>{
 if(BigInt(String(await rpc(provider,'eth_chainId')))!==BigInt(prepared.chainId))throw new Error('Wallet network changed. Prepare the Trove action again.');
 const accounts=await rpc(provider,'eth_accounts') as string[];
 if(!accounts.some(v=>typeof v==='string'&&getAddress(v)===prepared.account))throw new Error('Wallet account changed. Prepare the Trove action again.');
 if(!isCurrent())throw new Error('Selected wallet changed. Prepare the Trove action again.');
 return sendWalletTransaction(provider,{from:prepared.account,to:prepared.to,data:prepared.data,value:prepared.value,
 ...(prepared.gas?{gas:prepared.gas}:{}),...(prepared.maxFeePerGas?{maxFeePerGas:prepared.maxFeePerGas}:{}),
 ...(prepared.maxPriorityFeePerGas?{maxPriorityFeePerGas:prepared.maxPriorityFeePerGas}:{})});
}
