import {Interface, getAddress, parseUnits} from 'ethers';
import {
  MEZO_TESTNET, MEZO_TESTNET_HINT_HELPERS_ABI, MEZO_TESTNET_SORTED_TROVES_ABI,
  MEZO_TESTNET_TROVE_MANAGER_ABI, MEZO_TESTNET_TROVES, MEZO_TESTNET_BORROWER_OPERATIONS_ABI,
  MUSD_TESTNET, MUSD_ABI,
} from '@liqvera/mezo-protocol';
import type {Eip1193Provider} from './wallet.ts';

export type TroveAction = {kind:'deposit'; amount:string}|{kind:'repay';amount:string};
export type PreparedTroveAction={kind:TroveAction['kind'];account:string;chainId:number;to:string;data:string;value:string;summary:string};
const bo=new Interface(MEZO_TESTNET_BORROWER_OPERATIONS_ABI);
const manager=new Interface(MEZO_TESTNET_TROVE_MANAGER_ABI);
const operations=new Interface(MEZO_TESTNET_BORROWER_OPERATIONS_ABI);
const hints=new Interface(MEZO_TESTNET_HINT_HELPERS_ABI);
const sorted=new Interface(MEZO_TESTNET_SORTED_TROVES_ABI);
const musd=new Interface(MUSD_ABI);
const rpc=async(provider:Eip1193Provider,method:string,params:unknown[]=[])=>provider.request({method,params});
const call=async(provider:Eip1193Provider,to:string,data:string,from?:string)=>String(await rpc(provider,'eth_call',[{to,data,...(from?{from}:{})},'latest']));
function amount18(raw:string){if(typeof raw!=='string'||raw.length>40||!/^(0|[1-9][0-9]*)(\.[0-9]{1,18})?$/.test(raw))throw new Error('Enter a valid amount with at most 18 decimals.');const value=parseUnits(raw,18);if(value<=0n)throw new Error('Amount must be greater than zero.');return value;}
async function freshHints(provider:Eip1193Provider,coll:bigint,debt:bigint){
 const nicr=BigInt(hints.decodeFunctionResult('computeNominalCR',await call(provider,MEZO_TESTNET_TROVES.hintHelpers,hints.encodeFunctionData('computeNominalCR',[coll,debt])))[0]);
 const seed=BigInt(`0x${crypto.getRandomValues(new Uint8Array(32)).reduce((s,b)=>s+b.toString(16).padStart(2,'0'),'')}`);
 const approx=hints.decodeFunctionResult('getApproxHint',await call(provider,MEZO_TESTNET_TROVES.hintHelpers,hints.encodeFunctionData('getApproxHint',[nicr,15,seed])))[0];
 const pos=sorted.decodeFunctionResult('findInsertPosition',await call(provider,MEZO_TESTNET_TROVES.sortedTroves,sorted.encodeFunctionData('findInsertPosition',[nicr,approx,approx])));
 return [pos[0] as string,pos[1] as string];
}
export async function prepareTroveAction(provider:Eip1193Provider,account:string,action:TroveAction):Promise<PreparedTroveAction>{
 const borrower=getAddress(account);const chain=BigInt(String(await rpc(provider,'eth_chainId')));if(chain!==BigInt(MEZO_TESTNET.chainId))throw new Error('Switch to Mezo Testnet before preparing this action.');
 const amount=amount18(action.amount);
 const status=Number(manager.decodeFunctionResult('getTroveStatus',await call(provider,MEZO_TESTNET_TROVES.troveManager,manager.encodeFunctionData('getTroveStatus',[borrower])))[0]);
 if(status!==1)throw new Error('This wallet does not have an active Trove.');
 const values=manager.decodeFunctionResult('getEntireDebtAndColl',await call(provider,MEZO_TESTNET_TROVES.troveManager,manager.encodeFunctionData('getEntireDebtAndColl',[borrower])));
 const coll=BigInt(values[0])+BigInt(values[3]);const debt=BigInt(values[1])+BigInt(values[2])+BigInt(values[4])+BigInt(values[5]);
 let data:string,value=0n;
 if(action.kind==='deposit'){
  const balance=BigInt(String(await rpc(provider,'eth_getBalance',[borrower,'latest'])));if(balance<amount)throw new Error('Wallet BTC balance is too low for this deposit.');
  const nextColl=coll+amount;const [upper,lower]=await freshHints(provider,nextColl,debt);
  data=bo.encodeFunctionData('addColl',[upper,lower]);value=amount;
 }else{
  const minimum=BigInt(operations.decodeFunctionResult('minNetDebt',await call(provider,MEZO_TESTNET_TROVES.borrowerOperations,operations.encodeFunctionData('minNetDebt')))[0]);
  const gasReserve=BigInt(manager.decodeFunctionResult('MUSD_GAS_COMPENSATION',await call(provider,MEZO_TESTNET_TROVES.troveManager,manager.encodeFunctionData('MUSD_GAS_COMPENSATION')))[0]);
  if(amount>=debt)throw new Error('Repayment cannot close the Trove; use an amount below the outstanding debt.');
  const bal=BigInt(musd.decodeFunctionResult('balanceOf',await call(provider,MUSD_TESTNET.address,musd.encodeFunctionData('balanceOf',[borrower])))[0]);if(bal<amount)throw new Error('Wallet MUSD balance is too low for this repayment.');
  const nextDebt=debt-amount;if(nextDebt<=minimum+gasReserve)throw new Error('Repayment must leave the protocol minimum net debt and gas reserve.');
  const [upper,lower]=await freshHints(provider,coll,nextDebt);
  data=bo.encodeFunctionData('repayMUSD',[amount,upper,lower]);
 }
 const tx={from:borrower,to:MEZO_TESTNET_TROVES.borrowerOperations,data,value:`0x${value.toString(16)}`};
 await rpc(provider,'eth_call',[tx,'latest']);
 return {kind:action.kind,account:borrower,chainId:MEZO_TESTNET.chainId,to:tx.to,data,value:tx.value,summary:action.kind==='deposit'?`Deposit ${action.amount} BTC into your Trove`:`Repay ${action.amount} MUSD`};
}
export async function submitTroveAction(provider:Eip1193Provider,prepared:PreparedTroveAction):Promise<string>{
 if(BigInt(String(await rpc(provider,'eth_chainId')))!==BigInt(prepared.chainId))throw new Error('Wallet network changed. Prepare the Trove action again.');
 const accounts=await rpc(provider,'eth_accounts') as string[];if(accounts.length!==1||!accounts[0]||getAddress(accounts[0])!==prepared.account)throw new Error('Wallet account changed. Prepare the Trove action again.');
 return String(await rpc(provider,'eth_sendTransaction',[{from:prepared.account,to:prepared.to,data:prepared.data,value:prepared.value}]));
}
