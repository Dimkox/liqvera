// LiqveraGuard panel: arm a pre-signed Trove protection on Mezo Testnet and watch its status.
// Every state change is a wallet-signed transaction or signature; the panel only prepares and checks them.
import {formatUnits,getAddress,parseUnits} from 'ethers';
import {freshHints,readTroveContext} from './trove-transactions.ts';
import {debtOf,ratio} from './trove-math.ts';
import {sendWalletTransaction} from './wallet-submission.ts';
import type {Eip1193Provider} from './wallet.ts';
import {GUARD,calldata,planGuard,readGuard,readMusdAllowance,signGuardAuthorization,validateDeadline,type GuardAction,type GuardPlan} from './guard.ts';
import {GUARD_WATCH_PRICE_ATOMIC,readWatch,subscribeWatch,type WatchTrove} from './guard-watch.ts';

export interface GuardPanelContext{provider:Eip1193Provider|null;account:string|null;onMezo:boolean}
export interface GuardPanelOptions{host:HTMLElement;getContext:()=>GuardPanelContext;watchApi:string;now?:()=>bigint}

const pct=(v:bigint)=>`${(Number(v*10000n/10n**18n)/100).toFixed(2)}%`;
const fmt=(v:bigint,unit:string,places=8)=>`${Number(formatUnits(v,18)).toFixed(places).replace(/\.?0+$/,'')} ${unit}`;
function parsePercent(raw:string,label:string):bigint{
 if(!/^[0-9]{1,4}(\.[0-9]{1,2})?$/.test(raw.trim()))throw new Error(`Enter ${label} as a percentage, for example 170.`);
 return parseUnits(raw.trim(),16);
}
function parseAmount(raw:string,label:string):bigint{
 if(raw.trim()==='')return 0n;
 if(!/^(0|[1-9][0-9]*)(\.[0-9]{1,18})?$/.test(raw.trim()))throw new Error(`Enter a valid ${label}.`);
 return parseUnits(raw.trim(),18);
}

export function mountGuardPanel(o:GuardPanelOptions):{update():void;refresh():Promise<void>}{
 const now=o.now??(()=>BigInt(Math.floor(Date.now()/1000)));
 const make=<K extends keyof HTMLElementTagNameMap>(tag:K,text='',cls=''):HTMLElementTagNameMap[K]=>{const e=document.createElement(tag);e.textContent=text;if(cls)e.className=cls;return e;};
 const field=(label:string,value:string,aria:string)=>{const l=make('label',label,'field-label');const i=make('input');i.value=value;i.setAttribute('aria-label',aria);i.setAttribute('autocomplete','off');l.append(i);return {l,i};};
 const root=make('div','','guard-body');
 const intro=make('p',`Pre-sign one Mezo Trove top-up. When your ICR falls below the trigger, any keeper can execute it via LiqveraGuard ${GUARD.address} on Mezo Testnet (chain ${GUARD.chainId}). Testnet only, not audited.`,'supporting');
 const status=make('p','','field-hint');status.setAttribute('role','status');status.setAttribute('aria-live','polite');
 const trove=make('div','','guard-trove');
 const action=make('select');action.setAttribute('aria-label','Protection asset');
 for(const [v,t] of [['AddColl','Add BTC collateral'],['RepayMUSD','Repay MUSD']] as const){const opt=make('option',t);opt.value=v;action.append(opt);}action.value='AddColl';
 const trigger=field('Trigger ICR (%)','170','Trigger ICR percent'),target=field('Target ICR (%)','180','Target ICR percent');
 const reward=field('Keeper reward (same asset)','0','Keeper reward'),days=field('Authorization valid for (days, max 30)','29','Validity days');
 const calc=make('button','Calculate top-up','secondary-button');calc.setAttribute('type','button');
 const planOut=make('div','','guard-plan');
 const deposit=make('button','1. Deposit escrow','secondary-button');const sign=make('button','2. Sign authorization','secondary-button');
 const arm=make('button','3. Arm protection','secondary-button');
 for(const b of [deposit,sign,arm])b.setAttribute('type','button');
 const registered=make('div','','guard-registered');
 const refreshBtn=make('button','Refresh status','text-button');refreshBtn.setAttribute('type','button');
 const protect=make('button','Execute protect() now','secondary-button');protect.setAttribute('type','button');
 const disarm=make('button','Disarm','text-button');disarm.setAttribute('type','button');
 const withdraw=make('button','Withdraw free escrow','text-button');withdraw.setAttribute('type','button');
 const watch=make('div','','guard-watch');
 const subscribe=make('button','Subscribe Guard Watch (2 MUSD / 30 days)','secondary-button');subscribe.setAttribute('type','button');
 root.append(intro,status,trove,action,trigger.l,target.l,reward.l,days.l,calc,planOut,deposit,sign,arm,make('h4','Registered protection'),registered,refreshBtn,protect,disarm,withdraw,make('h4','Guard Watch'),watch,subscribe);
 o.host.replaceChildren(make('h3','LiqveraGuard: automatic Trove protection'),root);

 let plan:GuardPlan|null=null,auth:{signature:string;deadline:bigint;nonce:bigint;amount:bigint;action:GuardAction}|null=null;
 let snapshot:Awaited<ReturnType<typeof readGuard>>|null=null,watchState:WatchTrove|null=null,busy=false;
 const say=(t:string,kind='normal')=>{status.textContent=t;status.setAttribute('data-kind',kind);};
 const ready=()=>{const c=o.getContext();return c.provider&&c.account&&c.onMezo?{provider:c.provider,account:getAddress(c.account)}:null;};

 function update():void{
  const c=ready();
  for(const b of [calc,deposit,sign,arm,refreshBtn,protect,disarm,withdraw,subscribe])b.disabled=busy||!c;
  if(!c){const ctx=o.getContext();say(!ctx.provider||!ctx.account?'Connect your wallet to use LiqveraGuard.':'Switch the wallet to Mezo Testnet (chain 31611).');return;}
  deposit.disabled=busy||!plan;sign.disabled=busy||!plan;arm.disabled=busy||!plan||!auth;
  disarm.disabled=busy||!snapshot?.policy;protect.disabled=busy||snapshot?.status!=='Ready';withdraw.disabled=busy||!snapshot||(snapshot.freeBTC===0n&&snapshot.freeMUSD===0n);
  subscribe.disabled=busy||!o.watchApi||!watchState?.plan.payments_enabled;
 }
 async function run(label:string,fn:()=>Promise<void>):Promise<void>{
  busy=true;update();
  try{await fn();}catch(e){say(`${label}: ${(e as Error).message}`,'error');}
  finally{busy=false;update();}
 }
 async function send(provider:Eip1193Provider,account:string,to:string,data:string,value=0n,what=''):Promise<string>{
  const chain=String(await provider.request({method:'eth_chainId'}));
  if(BigInt(chain)!==BigInt(GUARD.chainId))throw new Error('Wallet is not on Mezo Testnet. Nothing was sent.');
  const tx={from:account,to,data,value:`0x${value.toString(16)}`};
  await provider.request({method:'eth_call',params:[tx,'latest']}); // simulate: a revert stops here, before the wallet prompt
  const hash=await sendWalletTransaction(provider,tx);
  say(`${what} submitted: ${hash}. Waiting for confirmation…`);
  for(let i=0;i<60;i++){
   const r=await provider.request({method:'eth_getTransactionReceipt',params:[hash]}) as {status?:string}|null;
   if(r?.status){if(r.status!=='0x1')throw new Error(`${what} reverted (${hash}).`);say(`${what} confirmed: ${GUARD.explorer}/tx/${hash}`);return hash;}
   await new Promise(res=>setTimeout(res,2000));
  }
  say(`${what} sent (${hash}); confirmation still pending. Refresh later.`);return hash;
 }
 async function refresh():Promise<void>{
  const c=ready();if(!c){update();return;}
  let s:Awaited<ReturnType<typeof readTroveContext>>['state']|null=null;
  try{s=(await readTroveContext(c.provider,c.account)).state;}
  catch(e){if(!/active Trove/.test((e as Error).message))throw e;}
  if(!s)trove.replaceChildren(make('p',`${c.account} has no active Mezo Trove. Open one in the Mezo app before arming a protection. Guard Watch status is still shown below.`));
  else trove.replaceChildren(make('p',`Trove ${c.account}: collateral ${fmt(s.coll,'BTC')}, debt ${fmt(debtOf(s),'MUSD',4)}, ICR now ${pct(ratio(s.coll,debtOf(s),s.price))} (MCR ${pct(s.mcr)}), BTC price ${fmt(s.price,'USD',2)}.`));
  snapshot=await readGuard(c.provider,c.account);
  const p=snapshot.policy;
  registered.replaceChildren(
   make('p',`Guard status: ${snapshot.status}${snapshot.icr?` at ICR ${pct(snapshot.icr)}`:''}. Mezo signature nonce ${snapshot.nonce}.`),
   make('p',p?`Armed: ${p.action===2?'add':'repay'} ${fmt(p.amount,p.action===2?'BTC':'MUSD')} when ICR < ${pct(p.triggerICR)}; keeper reward ${fmt(p.keeperReward,p.action===2?'BTC':'MUSD')}; valid until ${new Date(Number(p.deadline)*1000).toISOString()}; signed nonce ${p.sigNonce}${p.sigNonce!==snapshot.nonce?' (STALE: re-sign and re-arm)':''}.`:'No protection is armed for this wallet.'),
   make('p',`Escrow: ${fmt(snapshot.btcEscrow,'BTC')} (free ${fmt(snapshot.freeBTC,'BTC')}), ${fmt(snapshot.musdEscrow,'MUSD',4)} (free ${fmt(snapshot.freeMUSD,'MUSD',4)}).`));
  if(o.watchApi){
   try{
    watchState=await readWatch(o.watchApi,c.account);const w=watchState.subscription;
    watch.replaceChildren(make('p',w.active?`Active (${w.source}${w.source==='paid'&&w.paidUntil?` until ${new Date(Number(w.paidUntil)*1000).toISOString()}`:w.source==='trial'&&w.trialUntil?` until ${new Date(Number(w.trialUntil)*1000).toISOString()}`:''}). The keeper serves this Trove.`
     :`Not active. The keeper only executes protections for Troves with Guard Watch. Price (proposal): 2 MUSD per Trove per 30 days.${watchState.plan.free_trial?` Testnet free trial: ${watchState.plan.trial_days} days from your first arm.`:''}`));
   }catch{watchState=null;watch.replaceChildren(make('p','Guard Watch keeper API is unreachable. protect() stays permissionless: you or any keeper can still call it.'));}
  }else watch.replaceChildren(make('p','Guard Watch keeper API is not configured in this build. protect() stays permissionless.'));
  say('Status refreshed.');
 }
 calc.addEventListener('click',()=>run('Calculate',async()=>{
  const c=ready();if(!c)return;
  const {state:s}=await readTroveContext(c.provider,c.account);
  const act:GuardAction=action.value==='RepayMUSD'?'RepayMUSD':'AddColl';
  plan=planGuard(s,parsePercent(trigger.i.value,'the trigger'),parsePercent(target.i.value,'the target'),act);auth=null;
  const unit=plan.action==='AddColl'?'BTC':'MUSD',r=parseAmount(reward.i.value,'reward');
  planOut.replaceChildren(
   make('p',`Top-up: ${fmt(plan.amount,unit)}. At the trigger (BTC ≈ ${fmt(plan.priceAtTrigger,'USD',2)}) it lifts ICR from ${pct(plan.trigger)} to about ${pct(plan.afterAtTrigger)}.`),
   make('p',`Escrow needed: ${fmt(plan.amount+r,unit)} (top-up + keeper reward).`),
   make('p',plan.immediatelyReady?`Note: current ICR ${pct(plan.icrNow)} is already below this trigger, so the protection becomes executable as soon as it is armed.`:`Current ICR ${pct(plan.icrNow)} is above the trigger; the protection waits.`));
  say('Top-up calculated. Next: deposit escrow, sign, then arm.');
 }));
 deposit.addEventListener('click',()=>run('Deposit',async()=>{
  const c=ready();if(!c||!plan)return;const need=plan.amount+parseAmount(reward.i.value,'reward');
  const g=await readGuard(c.provider,c.account),free=plan.action==='AddColl'?g.freeBTC:g.freeMUSD;
  if(free>=need){say('Escrow already covers this protection. Next: sign.');return;}
  const total=need-free;
  if(plan.action==='AddColl')await send(c.provider,c.account,GUARD.address,calldata.depositBTC(),total,'BTC escrow deposit');
  else{
   if(await readMusdAllowance(c.provider,c.account)<total)await send(c.provider,c.account,GUARD.musd,calldata.approveMUSD(total),0n,'MUSD approval');
   await send(c.provider,c.account,GUARD.address,calldata.depositMUSD(total),0n,'MUSD escrow deposit');
  }
  await refresh();
 }));
 sign.addEventListener('click',()=>run('Sign',async()=>{
  const c=ready();if(!c||!plan)return;
  const d=Number(days.i.value);if(!Number.isInteger(d)||d<1||d>30)throw new Error('Validity must be 1 to 30 days.');
  const deadline=now()+BigInt(d)*86_400n-600n;validateDeadline(deadline,now());
  const g=await readGuard(c.provider,c.account);
  const r=await signGuardAuthorization(c.provider,c.account,plan.action,plan.amount,g.nonce,deadline);
  auth={signature:r.signature,deadline,nonce:g.nonce,amount:plan.amount,action:plan.action};
  say(`Authorization signed for Mezo nonce ${g.nonce} (digest ${r.digest}). It is not sent anywhere until you arm.`);
 }));
 arm.addEventListener('click',()=>run('Arm',async()=>{
  const c=ready();if(!c||!plan||!auth)return;
  const g=await readGuard(c.provider,c.account);
  if(g.nonce!==auth.nonce)throw new Error('Your Mezo nonce changed since signing. Sign again.');
  validateDeadline(auth.deadline,now());
  await send(c.provider,c.account,GUARD.address,calldata.arm(auth.action,plan.trigger,auth.amount,parseAmount(reward.i.value,'reward'),auth.deadline,auth.signature),0n,'Arm');
  auth=null;await refresh();
 }));
 refreshBtn.addEventListener('click',()=>run('Refresh',refresh));
 // protect() is permissionless. Without a funded keeper, the borrower (or anyone) can execute a Ready protection.
 protect.addEventListener('click',()=>run('Protect',async()=>{
  const c=ready();if(!c)return;
  const g=await readGuard(c.provider,c.account);
  if(g.status!=='Ready'||!g.policy)throw new Error(`Guard status is ${g.status}; protect() would revert. Nothing was sent.`);
  const {state:s,blockNumber}=await readTroveContext(c.provider,c.account);
  const coll=g.policy.action===2?s.coll+g.policy.amount:s.coll,principal=g.policy.action===1?s.principal-g.policy.amount:s.principal;
  const [upper,lower]=await freshHints(c.provider,coll,principal,blockNumber);
  await send(c.provider,c.account,GUARD.address,calldata.protect(c.account,upper,lower),0n,'protect()');
  await refresh();
 }));
 disarm.addEventListener('click',()=>run('Disarm',async()=>{const c=ready();if(!c)return;await send(c.provider,c.account,GUARD.address,calldata.disarm(),0n,'Disarm');await refresh();}));
 withdraw.addEventListener('click',()=>run('Withdraw',async()=>{
  const c=ready();if(!c||!snapshot)return;
  if(snapshot.freeBTC>0n)await send(c.provider,c.account,GUARD.address,calldata.withdrawBTC(snapshot.freeBTC),0n,'BTC withdrawal');
  if(snapshot.freeMUSD>0n)await send(c.provider,c.account,GUARD.address,calldata.withdrawMUSD(snapshot.freeMUSD),0n,'MUSD withdrawal');
  await refresh();
 }));
 subscribe.addEventListener('click',()=>run('Guard Watch',async()=>{
  const c=ready();if(!c||!watchState)return;
  if(watchState.plan.price_atomic!==GUARD_WATCH_PRICE_ATOMIC)throw new Error('Guard Watch price changed. No payment was submitted.');
  const tx=await subscribeWatch(o.watchApi,c.provider,c.account,watchState.plan);
  say(`Guard Watch payment settled: ${GUARD.explorer}/tx/${tx}. The keeper activates it after reading the transfer from chain.`);
 }));
 update();
 return {update,refresh:()=>run('Refresh',refresh)};
}
