import {MEZO_TESTNET} from '@liqvera/mezo-protocol';
import type {TroveReport} from './contracts.ts';
import type {Eip1193Provider} from './wallet.ts';
import {prepareTroveAction,submitTroveAction} from './trove-transactions.ts';
export function mountTroveProtection(host:HTMLElement,report:TroveReport,provider:Eip1193Provider|null,account:string|null):void{
 if(report.trove_risk.status!=='ACTIVE'||!provider||!account||account.toLowerCase()!==report.trove_risk.borrower.toLowerCase())return;
 const section=document.createElement('section');section.className='trove-actions';
 const title=document.createElement('h3');title.textContent='Protect this Trove';section.append(title);
 const note=document.createElement('p');note.className='form-note';note.textContent='Fresh Testnet state and insertion hints are simulated before your wallet is asked to sign.';section.append(note);
 const status=document.createElement('p');status.className='form-note';status.setAttribute('role','status');section.append(status);
 const make= (kind:'deposit'|'repay',label:string)=>{
  const form=document.createElement('form');form.className='trove-action-form';
  const input=document.createElement('input');input.type='number';input.min='0';input.step='any';input.required=true;input.inputMode='decimal';input.setAttribute('aria-label',kind==='deposit'?'BTC to deposit':'MUSD to repay');input.placeholder=kind==='deposit'?'BTC amount':'MUSD amount';
  if(kind==='repay')input.addEventListener('input',()=>{button.textContent=input.value?`Repay ${input.value} MUSD`:'Repay MUSD';});
  const button=document.createElement('button');button.type='submit';button.className='secondary-button';button.textContent=label;
  form.append(input,button);form.addEventListener('submit',async event=>{
   event.preventDefault();button.disabled=true;status.textContent='Reading current Trove state and simulating…';
   try{const prepared=await prepareTroveAction(provider!,account!,{kind,amount:input.value});status.textContent=`Confirm in wallet: ${prepared.summary}`;
    const hash=await submitTroveAction(provider!,prepared);const link=document.createElement('a');link.href=`${MEZO_TESTNET.explorerUrl}/tx/${hash}`;link.target='_blank';link.rel='noopener noreferrer';link.textContent=`Transaction submitted: ${hash.slice(0,12)}… ↗`;status.replaceChildren(link);
   }catch(error){status.textContent=error instanceof Error?error.message:'Transaction preparation failed.';}finally{button.disabled=false;}
  });section.append(form);
 };
 make('deposit','Deposit BTC');make('repay','Repay MUSD');host.append(section);
}
