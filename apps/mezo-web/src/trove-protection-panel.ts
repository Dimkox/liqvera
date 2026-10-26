import {formatUnits,parseUnits} from 'ethers';
import {MEZO_TESTNET} from '@liqvera/mezo-protocol';
import type {TroveReport} from './contracts.ts';
import type {Eip1193Provider} from './wallet.ts';
import {prepareTroveAction,submitTroveAction,readTroveContext,computeLimits,computeRescue,maxTroveAction,
 sameTroveTerms,snapshot} from './trove-transactions.ts';
import type {TroveAction,PreparedTroveAction} from './trove-transactions.ts';
import {WAD,safeRatio} from './trove-math.ts';
import {TroveActionStore,waitTroveReceipt} from './trove-action-receipts.ts';
import type {ActionReceipt} from './trove-action-receipts.ts';
import {WalletSubmissionUnknown} from './wallet-submission.ts';
const units=(value:string|bigint)=>formatUnits(value,18);
function readable(value:string,places=5){const [whole,decimal='']=units(value).split('.');return `${whole}.${decimal.slice(0,places)}`;}
function node<K extends keyof HTMLElementTagNameMap>(tag:K,text=''):HTMLElementTagNameMap[K]{const e=document.createElement(tag);e.textContent=text;return e;}
const errorText=(error:unknown)=>{
 if(error&&typeof error==='object'&&'code' in error&&(error.code===4001||error.code==='4001'||error.code==='ACTION_REJECTED'))return 'You rejected the request in your wallet.';
 return error instanceof Error?error.message:'Trove action failed.';
};
export function mountTroveProtection(host:HTMLElement,report:TroveReport,provider:Eip1193Provider|null,
 account:string|null,isCurrent:()=>boolean=()=>true,reportSha256=''):void{
 if(report.trove_risk.status!=='ACTIVE')return;
 const section=node('section');section.className='trove-actions';section.append(node('h3','Protect this Trove'));host.append(section);
 if(!provider||!account||account.toLowerCase()!==report.request.borrower.toLowerCase()){
  section.append(node('p','Connect the borrower wallet to act on this Trove.'));return;
 }
 const wallet=provider,borrower=account;
 let storage:Storage|null=null;try{storage=globalThis.localStorage;}catch{/* Store will disable signing. */}
 const store=new TroveActionStore(storage,{report_id:report.report_id,report_sha256:reportSha256},borrower);
 let context:Awaited<ReturnType<typeof readTroveContext>>|null=null,busy=false,stateReady=false;
 let pending:ActionReceipt|null=null,guardError='';
 const controls:{element:HTMLButtonElement|HTMLInputElement;allowed:()=>boolean}[]=[];
 const status=node('p');status.className='form-note';status.setAttribute('role','status');
 const warning=node('p');warning.className='safety-note';
 const recovery=node('div');
 section.append(node('p','Fresh Testnet state and hints are simulated before signing. Previews are predictions; confirmation records first canonical inclusion.'),status,warning,recovery);
 function current(){return section.isConnected&&isCurrent();}
 function checkCurrent(){if(!current())throw new Error('Wallet context changed. Prepare the Trove action again.');}
 function register<T extends HTMLButtonElement|HTMLInputElement>(element:T,allowed:()=>boolean=()=>true):T{controls.push({element,allowed});return element;}
 function sync(){
  try{pending=store.unresolved();guardError='';}catch(error){guardError=errorText(error);}
  const locked=busy||Boolean(pending)||Boolean(guardError)||!stateReady||!current();
  for(const c of controls)c.element.disabled=locked||!c.allowed();
  warning.textContent=[guardError,store.warning].filter(Boolean).join(' ');
  recovery.replaceChildren();
  if(!stateReady&&!pending){const refresh=node('button','Refresh Trove state');refresh.type='button';refresh.disabled=busy;
   refresh.addEventListener('click',async()=>{if(busy)return;busy=true;sync();try{await load();status.textContent='Current Trove state refreshed.';}catch(error){status.textContent=errorText(error);}finally{busy=false;sync();}});recovery.append(refresh);}
  if(pending){
   recovery.append(node('p',pending.tx_hash?'A Trove action is pending. Check confirmation before signing again.':'Wallet submission is unresolved. Check your wallet and explorer before taking another action.'));
   recovery.append(explorer(pending.tx_hash?'tx':'address',pending.tx_hash??borrower));
   if(pending.tx_hash){const check=node('button','Check confirmation');check.type='button';check.disabled=busy;
    const record=pending;check.addEventListener('click',async()=>{if(busy)return;busy=true;sync();try{await confirm(record);}finally{busy=false;sync();}});recovery.append(check);}
  }
 }
 function explorer(kind:'tx'|'address',value:string){const link=node('a',kind==='tx'?`Transaction ${value.slice(0,12)}… ↗`:'View borrower in explorer ↗');
  link.href=`${MEZO_TESTNET.explorerUrl}/${kind}/${value}`;link.target='_blank';link.rel='noopener noreferrer';return link;}
 const rescue=node('div');rescue.className='trove-rescue';rescue.append(node('h4','Rescue to a target ratio'));
 const targetLabel=node('label','Target ICR'),target=register(node('input'));target.type='number';target.value='1.8';target.step='0.05';target.setAttribute('aria-label','Target ICR');targetLabel.append(target);
 const rescueText=node('p'),repayRescueText=node('p');let rescueDeposit=0n,rescueRepay=0n,canRescueRepay=false,canRescueDeposit=false;
 const useDeposit=register(node('button','Use in Add collateral'),()=>canRescueDeposit),useRepay=register(node('button','Use in Repay'),()=>canRescueRepay);
 useDeposit.type=useRepay.type='button';rescue.append(targetLabel,rescueText,useDeposit,repayRescueText,useRepay);section.append(rescue);
 const forms=new Map<TroveAction['kind'],{input:HTMLInputElement;invalidate:()=>void;preview:()=>Promise<void>}>();
 function renderRescue(){
  if(!context)return;
  try{
   if(!/^(0|[1-9][0-9]*)(\.[0-9]{1,18})?$/.test(target.value)||target.value.length>24)throw new Error('Enter a valid target ICR.');
   const r=computeRescue(context.state,parseUnits(target.value,18)),limits=computeLimits(context.state,context.balances);
   target.min=units(context.state.mcr+WAD/20n);rescueDeposit=r.deposit;rescueRepay=r.repay;
   canRescueDeposit=!r.alreadyAbove&&r.deposit<=limits.deposit;canRescueRepay=!r.alreadyAbove&&r.repayAvailable&&r.repay<=limits.repay;
   rescueText.textContent=r.alreadyAbove?'Already above target':`Add ${units(r.deposit)} BTC → ICR ${target.value}${r.deposit>limits.deposit?' — Wallet BTC balance is too low for this rescue.':''}`;
   repayRescueText.textContent=r.alreadyAbove?'':canRescueRepay?`Repay ${units(r.repay)} MUSD → ICR ${target.value}`:
    r.repayAvailable?'Wallet MUSD balance is too low for this rescue.':'Repayment cannot reach this target: minimum debt limit.';
  }catch(error){canRescueDeposit=canRescueRepay=false;rescueText.textContent=errorText(error);repayRescueText.textContent='';}
  sync();
 }
 target.addEventListener('input',renderRescue);
 async function fill(kind:TroveAction['kind'],amount:string){const form=forms.get(kind)!;form.input.value=amount;form.invalidate();await form.preview();}
 useDeposit.addEventListener('click',async()=>{if(!useDeposit.disabled)await fill('deposit',units(rescueDeposit));});
 useRepay.addEventListener('click',async()=>{if(!useRepay.disabled)await fill('repay',units(rescueRepay));});
 const limitsText=node('p'),borrowNote=node('p');
 async function load(minimumBlock?:string){
  const result=await readTroveContext(wallet,borrower,minimumBlock);checkCurrent();context=result;stateReady=true;
  const limits=computeLimits(result.state,result.balances);
  limitsText.textContent=`Max repayable now: ${units(limits.repay)} MUSD (minimum net debt ${units(result.state.minimum)} MUSD).`;
  borrowNote.textContent=result.state.systemColl*result.state.price/result.state.systemDebt<result.state.ccr?
   'Borrowing is disabled in Recovery Mode.':`Only allowed while ICR stays at or above ${units(safeRatio(result.state))}.`;
  renderRescue();
 }
 function make(kind:TroveAction['kind'],label:string){
  const form=node('form');form.className='trove-action-form';form.append(node('h4',label));
  const input=register(node('input'));input.type='text';input.inputMode='decimal';input.required=true;
  input.setAttribute('aria-label',kind==='deposit'?'BTC amount':kind==='repay'?'MUSD amount':'MUSD to borrow');input.placeholder=kind==='deposit'?'BTC amount':'MUSD amount';
  const max=register(node('button','Max'));max.type='button';max.setAttribute('aria-label',`Max ${label}`);
  const preview=node('p');preview.className='trove-action-preview';
  const formStatus=node('p');formStatus.className='form-note';formStatus.setAttribute('role','status');
  let prepared:PreparedTroveAction|null=null,revision=0,timer:ReturnType<typeof setTimeout>|undefined;
  const submit=register(node('button',label));submit.type='submit';submit.className='secondary-button';
  const sign=register(node('button','Sign in wallet'),()=>prepared!==null);sign.type='button';sign.className='primary-button';
  const summary=node('p');summary.className='safety-note';
  function invalidate(){revision++;prepared=null;summary.textContent='';formStatus.textContent='';
   submit.textContent=input.value?`${kind==='deposit'?'Add':kind==='repay'?'Repay':'Borrow'} ${input.value} ${kind==='deposit'?'BTC':'MUSD'}`:label;sync();}
  function show(p:PreparedTroveAction){
   preview.textContent=`ICR now: ${readable(p.before.icr)} → after: ${readable(p.after.icr)}. Debt: ${units(p.before.debt)} → ${units(p.after.debt)} MUSD. Collateral: ${units(p.before.coll)} → ${units(p.after.coll)} BTC. Liquidation price: ${readable(p.before.liquidationPrice)} → ${readable(p.after.liquidationPrice)} MUSD.${kind==='borrow'?` Borrowing fee: ${units(p.fee)} MUSD.`:''}`;
  }
  async function updatePreview(){
   const version=revision,amount=input.value;if(!amount||!current())return;
   try{const result=await prepareTroveAction(wallet,borrower,{kind,amount});if(version!==revision||!current())return;show(result);formStatus.textContent='';}
   catch(error){if(version===revision&&current()){preview.textContent='';formStatus.textContent=errorText(error);}}
  }
  input.addEventListener('input',()=>{clearTimeout(timer);invalidate();preview.textContent='';timer=setTimeout(()=>{void updatePreview();},300);});
  forms.set(kind,{input,invalidate,preview:updatePreview});
  max.addEventListener('click',async()=>{
   if(max.disabled)return;busy=true;sync();
   try{const amount=await maxTroveAction(wallet,borrower,kind);checkCurrent();await fill(kind,amount);}
   catch(error){formStatus.textContent=errorText(error);}finally{busy=false;sync();}
  });
  form.addEventListener('submit',async event=>{
   event.preventDefault();if(busy||pending||guardError||!stateReady||!current())return;
   const amount=input.value,version=revision;busy=true;prepared=null;sync();formStatus.textContent='Reading current Trove state and simulating…';
   try{const result=await prepareTroveAction(wallet,borrower,{kind,amount});checkCurrent();if(version!==revision)return;
    prepared=result;show(result);summary.textContent=`You will sign: ${result.summary}. ICR after: ${readable(result.after.icr)}.`;formStatus.textContent='Review the summary, then choose Sign in wallet.';
   }catch(error){formStatus.textContent=errorText(error);}finally{busy=false;sync();}
  });
  sign.addEventListener('click',async()=>{
   if(sign.disabled||!prepared)return;
   const reviewed=prepared,version=revision;busy=true;sync();
   try{
    checkCurrent();if(!navigator.locks)throw new Error('This browser cannot lock wallet actions safely. Use a browser with Web Locks support.');
    await navigator.locks.request(store.guardKey,{ifAvailable:true},async lock=>{
     if(!lock)throw new Error('Another tab is preparing a Trove action. Wait for it to finish.');
     if(store.unresolved())throw new Error('A Trove action is unresolved. Check its confirmation.');
     formStatus.textContent='Reading current Trove state and simulating…';
     const fresh=await prepareTroveAction(wallet,borrower,{kind,amount:input.value});checkCurrent();if(version!==revision)return;
     if(!sameTroveTerms(reviewed,fresh)){
      prepared=fresh;show(fresh);summary.textContent=`You will sign: ${fresh.summary}. ICR after: ${readable(fresh.after.icr)}.`;
      formStatus.textContent='Current terms changed. Review the new summary, then choose Sign in wallet again.';return;
     }
     let record=store.begin(fresh);prepared=null;formStatus.textContent='Confirm in your wallet…';renderLog();
     try{const hash=await submitTroveAction(wallet,fresh,current);record=store.update({...record,tx_hash:hash,state:'pending'});}
     catch(error){
      if(error instanceof WalletSubmissionUnknown){record=store.update({...record,state:'unknown'});}
      else store.cancelRejected(record);
      throw error;
     }
     status.textContent='Waiting for confirmation…';formStatus.textContent='Waiting for confirmation…';renderLog();sync();await confirm(record);
     formStatus.textContent=status.textContent;
    });
   }catch(error){formStatus.textContent=errorText(error);}finally{busy=false;sync();}
  });
  form.append(input,max);if(kind==='repay')form.append(limitsText);if(kind==='borrow')form.append(borrowNote);
  form.append(preview,submit,summary,sign,formStatus);
  if(kind==='borrow'){const details=node('details');details.open=false;details.append(node('summary',label),form);section.append(details);}else section.append(form);
 }
 make('deposit','Add collateral');make('repay','Repay MUSD');make('borrow','Borrow more MUSD');
 const log=node('div');section.append(log);
 function renderLog(){
  log.replaceChildren(node('h4','Actions log'));
  for(const r of store.records()){
   const item=node('p',`${r.kind}: ${units(r.amount)} — ${r.state}. Prepared ICR ${readable(r.before.icr)} → ${readable(r.after.icr)}. `);
   if(r.tx_hash)item.append(explorer('tx',r.tx_hash));log.append(item);
  }
  const download=node('button','Download action receipts');download.type='button';
  download.addEventListener('click',()=>{const url=URL.createObjectURL(new Blob([store.exportJson()],{type:'application/json'}));
   const link=node('a');link.href=url;link.download=`liqvera-trove-actions-${report.report_id}.json`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});log.append(download);
 }
 async function confirm(record:ActionReceipt){
  const owner=record.report_id===report.report_id?store:new TroveActionStore(storage,{report_id:record.report_id,report_sha256:record.report_sha256},borrower);
  try{
   status.textContent='Waiting for confirmation…';
   const receipt=await waitTroveReceipt(wallet,record.tx_hash!);
   record=owner.update({...record,receipt_block:receipt.blockNumber,receipt_status:receipt.status,state:receipt.status==='0x1'?'confirmed':'reverted'});
   status.textContent=receipt.status==='0x1'?`Confirmed in block ${BigInt(receipt.blockNumber)}.`:'Transaction reverted. Refresh the Trove state and try again.';
   for(const f of forms.values())f.invalidate();
   stateReady=false;
   try{await load(receipt.blockNumber);if(receipt.status==='0x1'&&context)owner.update({...record,observed:{block:context.blockNumber,snapshot:snapshot(context.state)}});}
   catch(error){status.textContent+=` State refresh failed: ${errorText(error)}`;}
  }catch(error){status.textContent=errorText(error);}
  renderLog();sync();
 }
 renderLog();sync();void load().catch(error=>{status.textContent=errorText(error);sync();});
 globalThis.addEventListener('storage',event=>{
  if(!section.isConnected)return;
  if(event.key===store.guardKey||event.key===store.reportKey){for(const f of forms.values())f.invalidate();renderLog();sync();}
 });
}
