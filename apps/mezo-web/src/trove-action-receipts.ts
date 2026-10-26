import {MEZO_TESTNET,MEZO_TESTNET_TROVES} from '@liqvera/mezo-protocol';
import type {Eip1193Provider} from './wallet.ts';
import type {PreparedTroveAction,TroveSnapshot} from './trove-transactions.ts';
export type ActionReceipt={schema:'liqvera-trove-action/v1';id:string;report_id:string;report_sha256:string;
 borrower:string;chain_id:31611;kind:'addColl'|'repayMUSD'|'withdrawMUSD';to:string;calldata:string;value_wei:string;
 amount:string;fee:string;upper_hint:string;lower_hint:string;prepared_block:string;before:TroveSnapshot;after:TroveSnapshot;
 tx_hash:string|null;receipt_block:string|null;receipt_status:'0x0'|'0x1'|null;created_at:string;
 state:'awaiting_wallet'|'pending'|'unknown'|'confirmed'|'reverted';
 observed?:{block:string;snapshot:TroveSnapshot}};
export type ActionReport={report_id:string;report_sha256:string};
const address=/^0x[0-9a-fA-F]{40}$/,hash=/^0x[0-9a-fA-F]{64}$/,quantity=/^(0|[1-9][0-9]*)$/,block=/^0x[0-9a-fA-F]+$/;
const unresolved=(r:ActionReceipt)=>!['confirmed','reverted'].includes(r.state);
const validSnapshot=(v:unknown):v is TroveSnapshot=>{
 if(!v||typeof v!=='object')return false;const s=v as TroveSnapshot;
 return [s.coll,s.debt,s.icr,s.liquidationPrice].every(x=>typeof x==='string'&&quantity.test(x));
};
export function validActionReceipt(value:unknown):value is ActionReceipt{
 if(!value||typeof value!=='object')return false;const r=value as ActionReceipt;
 return r.schema==='liqvera-trove-action/v1'&&typeof r.id==='string'&&r.id.length>0&&
 typeof r.report_id==='string'&&r.report_id.length>0&&typeof r.report_sha256==='string'&&/^[0-9a-f]{64}$/.test(r.report_sha256)&&
 address.test(r.borrower)&&r.chain_id===31611&&['addColl','repayMUSD','withdrawMUSD'].includes(r.kind)&&
 r.to?.toLowerCase()===MEZO_TESTNET_TROVES.borrowerOperations.toLowerCase()&&/^0x(?:[0-9a-fA-F]{2})+$/.test(r.calldata)&&
 [r.value_wei,r.amount,r.fee].every(x=>typeof x==='string'&&quantity.test(x))&&
 address.test(r.upper_hint)&&address.test(r.lower_hint)&&block.test(r.prepared_block)&&validSnapshot(r.before)&&validSnapshot(r.after)&&
 (r.tx_hash===null||hash.test(r.tx_hash))&&(r.receipt_block===null||block.test(r.receipt_block))&&
 [null,'0x0','0x1'].includes(r.receipt_status)&&['awaiting_wallet','pending','unknown','confirmed','reverted'].includes(r.state)&&
 /^\d{4}-\d\d-\d\dT.*Z$/.test(r.created_at)&&Number.isFinite(Date.parse(r.created_at))&&
 (r.state!=='pending'||r.tx_hash!==null)&&
 (r.state!=='confirmed'||(r.tx_hash!==null&&r.receipt_block!==null&&r.receipt_status==='0x1'))&&
 (r.state!=='reverted'||(r.tx_hash!==null&&r.receipt_block!==null&&r.receipt_status==='0x0'))&&
 (!r.observed||(block.test(r.observed.block)&&validSnapshot(r.observed.snapshot)));
}
/** Persistent intent is separate from report records and shared across reports/tabs. */
export class TroveActionStore{
 private memory:ActionReceipt[]=[];
 warning='';
 readonly reportKey:string;readonly guardKey:string;
 constructor(privateStorage:Storage|null,report:ActionReport,borrower:string){
  this.storage=privateStorage;this.report=report;this.borrower=borrower.toLowerCase();
  this.reportKey=`liqvera:trove-actions:${report.report_id}`;
  this.guardKey=`liqvera:trove-unresolved:31611:${this.borrower}`;
 }
 private storage:Storage|null;private report:ActionReport;private borrower:string;
 private read(key:string):unknown{
  if(!this.storage)throw new Error('Browser storage is unavailable. New signing is disabled.');
  const raw=this.storage.getItem(key);return raw===null?null:JSON.parse(raw);
 }
 private validForBorrower(r:unknown):r is ActionReceipt{return validActionReceipt(r)&&r.borrower.toLowerCase()===this.borrower;}
 records():ActionReceipt[]{
  try{
   const data=this.read(this.reportKey);
   if(data!==null&&(!Array.isArray(data)||!data.every(r=>this.validForBorrower(r)&&r.report_id===this.report.report_id&&r.report_sha256===this.report.report_sha256)))throw new Error('Invalid action records');
   const merged=new Map<string,ActionReceipt>();
   for(const r of [...(data??[]) as ActionReceipt[],...this.memory])merged.set(r.id,r);
   this.memory=[...merged.values()];
  }catch{this.warning='Browser action storage could not be read. Keep the downloaded action receipts.';}
  return this.memory.slice();
 }
 unresolved():ActionReceipt|null{
  try{
   const guard=this.read(this.guardKey);
   if(guard===null)return null;
   if(!this.validForBorrower(guard))throw new Error('Invalid unresolved record');
   return unresolved(guard)?guard:null;
  }catch{throw new Error('Unresolved action storage is unavailable or contains an invalid record. New signing is disabled.');}
 }
 begin(prepared:PreparedTroveAction):ActionReceipt{
  if(this.unresolved())throw new Error('A Trove action is unresolved. Check its outcome before signing again.');
  const r:ActionReceipt={schema:'liqvera-trove-action/v1',id:crypto.randomUUID(),...this.report,
   borrower:prepared.account,chain_id:31611,kind:prepared.kind==='deposit'?'addColl':prepared.kind==='repay'?'repayMUSD':'withdrawMUSD',
   to:prepared.to,calldata:prepared.data,value_wei:BigInt(prepared.value).toString(),amount:prepared.amount,fee:prepared.fee,
   upper_hint:prepared.upperHint,lower_hint:prepared.lowerHint,prepared_block:prepared.blockNumber,before:prepared.before,after:prepared.after,
   tx_hash:null,receipt_block:null,receipt_status:null,created_at:new Date().toISOString(),state:'awaiting_wallet'};
  if(!validActionReceipt(r)||r.borrower.toLowerCase()!==this.borrower)throw new Error('Invalid action receipt or report binding.');
  try{this.storage!.setItem(this.guardKey,JSON.stringify(r));}catch{throw new Error('Browser storage could not save the action intent. New signing is disabled.');}
  this.update(r);return r;
 }
 update(r:ActionReceipt):ActionReceipt{
  if(!this.validForBorrower(r))throw new Error('Invalid action receipt.');
  const previous=this.records();this.memory=[...previous.filter(item=>item.id!==r.id),r];
  try{
   if(unresolved(r))this.storage!.setItem(this.guardKey,JSON.stringify(r));
   this.storage!.setItem(this.reportKey,JSON.stringify(this.memory));
   if(!unresolved(r)){
    const guard=this.read(this.guardKey) as ActionReceipt|null;
    if(guard?.id===r.id)this.storage!.removeItem(this.guardKey);
   }
  }catch{this.warning='Browser action storage could not be saved. Keep the downloaded action receipts. Pending guards remain in place.';}
  return r;
 }
 cancelRejected(r:ActionReceipt):void{
  // Only an explicit wallet rejection proves no transaction was submitted.
  const guard=this.unresolved();
  if(guard?.id!==r.id)return;
  this.storage!.removeItem(this.guardKey);
  this.memory=this.records().filter(item=>item.id!==r.id);
  try{this.storage!.setItem(this.reportKey,JSON.stringify(this.memory));}catch{this.warning='Browser action storage could not be saved.';}
 }
 exportJson():string{return JSON.stringify(this.records(),null,2)+'\n';}
}
export type TroveReceipt={transactionHash:string;blockNumber:string;blockHash:string;status:'0x0'|'0x1'};
export async function waitTroveReceipt(provider:Eip1193Provider,txHash:string,
 options:{attempts?:number;intervalMs?:number}={}):Promise<TroveReceipt>{
 if(!hash.test(txHash))throw new Error('Invalid transaction hash.');
 for(let i=0;i<(options.attempts??60);i++){
  if(BigInt(String(await provider.request({method:'eth_chainId'})))!==BigInt(MEZO_TESTNET.chainId))throw new Error('Switch to Mezo Testnet to check this pending transaction.');
  const r=await provider.request({method:'eth_getTransactionReceipt',params:[txHash]}) as TroveReceipt|null;
  if(r){
   if(typeof r.transactionHash!=='string'||r.transactionHash.toLowerCase()!==txHash.toLowerCase()||
    !block.test(r.blockNumber)||!hash.test(r.blockHash)||!['0x0','0x1'].includes(r.status))throw new Error('Invalid transaction receipt. The action remains unresolved.');
   const canonical=await provider.request({method:'eth_getBlockByNumber',params:[r.blockNumber,false]}) as {hash?:string}|null;
   if(canonical?.hash?.toLowerCase()!==r.blockHash.toLowerCase())throw new Error('Transaction receipt is not canonical. Check again.');
   return r;
  }
  if(i+1<(options.attempts??60))await new Promise(resolve=>setTimeout(resolve,options.intervalMs??2000));
 }
 throw new Error('Transaction is still pending. Check confirmation again; do not submit it again.');
}
