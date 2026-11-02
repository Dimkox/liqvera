// Guard Watch (proposal: 2 MUSD per Trove per 30 days) client. Status reads and the x402 checkout,
// using the same pinned x402 SDK bridge and Permit2 + EIP-2612 sponsorship checks as report payments.
import {MUSD_PERMIT,X402_PERMIT2} from '@liqvera/mezo-protocol';
import type {ClientEvmSigner} from '@x402/evm';
import {getTypesForEIP712Domain,serializeTypedData} from 'viem';
import {getAddress} from 'ethers';
import {GUARD} from './guard.ts';
import type {Eip1193Provider} from './wallet.ts';
import {boundedFetchJson} from './x402-transport.mjs';
// @ts-expect-error The pinned JS SDK bridge is exercised directly by x402-production.test.mjs.
import {createProductionProtocol,requirePermit2Challenge,requireSponsoredPayment} from './x402-production.mjs';

export const GUARD_WATCH_PRICE_ATOMIC='2000000000000000000';
export interface WatchPlan{product:'guard_watch';proposal:boolean;network:string;asset:string;price_atomic:string;period_days:number;
 pay_to:string|null;payments_enabled:boolean;payments_ready?:boolean;free_trial:boolean;trial_days:number;enforced:boolean}
export interface WatchSubscription{active:boolean;source:'paid'|'trial'|'none'|'not-enforced';paidUntil:string|null;trialUntil:string|null;payments:number}
export interface WatchTrove{borrower:string;subscription:WatchSubscription;guard:{armed:boolean;terminal:boolean;status?:string;icr?:string}|null;plan:WatchPlan}

function base(api:string):string{
 const u=new URL(api);if(u.protocol!=='http:'&&u.protocol!=='https:')throw new Error('Guard Watch API must be http(s).');
 return u.href.replace(/\/$/,'');
}
export async function readWatch(api:string,borrower:string,fetcher:typeof fetch=fetch):Promise<WatchTrove>{
 const r=await boundedFetchJson(fetcher,`${base(api)}/v1/guard-watch/troves/${getAddress(borrower)}`,{headers:{Accept:'application/json'}},65_536);
 if(!r.response.ok)throw new Error('Guard Watch status is unavailable.');
 const body=r.body as WatchTrove;
 if(!body||typeof body!=='object'||!body.subscription||body.plan?.product!=='guard_watch')throw new Error('Guard Watch returned an unexpected response.');
 return body;
}
/** Exact terms the browser accepts before it asks the wallet to sign a Guard Watch payment. */
export function checkWatchTerms(accept:{scheme?:string;network?:string;asset?:string;amount?:string;payTo?:string},plan:WatchPlan):void{
 if(accept.scheme!=='exact'||accept.network!==`eip155:${GUARD.chainId}`||accept.asset?.toLowerCase()!==GUARD.musd.toLowerCase()||
  accept.amount!==GUARD_WATCH_PRICE_ATOMIC||!plan.pay_to||accept.payTo?.toLowerCase()!==plan.pay_to.toLowerCase())
  throw new Error('Guard Watch payment terms changed. No payment was submitted.');
}
/** Pay one 30-day Guard Watch period for `payer`'s Trove. Returns the settlement tx hash. */
export async function subscribeWatch(api:string,provider:Eip1193Provider,payer:string,plan:WatchPlan,fetcher:typeof fetch=fetch):Promise<string>{
 const path=`${base(api)}/v1/guard-watch/troves/${getAddress(payer)}/subscribe`;
 const signer:ClientEvmSigner={address:getAddress(payer) as `0x${string}`,signTypedData:async message=>{
  const typed=serializeTypedData<Record<string,unknown>,string>({...message,types:{...message.types,EIP712Domain:getTypesForEIP712Domain({domain:message.domain})}});
  const signature=await provider.request({method:'eth_signTypedData_v4',params:[getAddress(payer),typed]});
  if(typeof signature!=='string'||!/^0x[0-9a-fA-F]{130}$/.test(signature))throw new Error('Wallet did not sign. No payment was submitted.');
  return signature as `0x${string}`;
 }};
 const protocol=createProductionProtocol(signer,'https://rpc.test.mezo.org',`eip155:${GUARD.chainId}`);
 const challengeRead=await boundedFetchJson(fetcher,path,{headers:{Accept:'application/json'}},65_536);
 if(challengeRead.response.status!==402)throw new Error('Guard Watch checkout is not available. No payment was submitted.');
 const required=protocol.getPaymentRequiredResponse((n:string)=>challengeRead.response.headers.get(n),challengeRead.body);
 const permit={...X402_PERMIT2,domainName:MUSD_PERMIT.domainName,domainVersion:MUSD_PERMIT.domainVersion};
 requirePermit2Challenge(required,permit);
 checkWatchTerms(required.accepts[0],plan);
 const payment=await protocol.createPaymentPayload(required);
 requireSponsoredPayment(payment,permit);
 const paid=await boundedFetchJson(fetcher,path,{headers:{Accept:'application/json',...protocol.encodePaymentSignatureHeader(payment)}},65_536);
 const tx=paid.response.headers.get('x-liqvera-payment-tx');
 if(!paid.response.ok||!tx||!/^0x[0-9a-fA-F]{64}$/.test(tx))throw new Error('Guard Watch payment outcome is unknown. Check the explorer before retrying.');
 return tx.toLowerCase();
}
