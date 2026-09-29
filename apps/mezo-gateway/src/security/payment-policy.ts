import { createHash } from 'node:crypto';
import type { PaymentPayload } from '@x402/core/types';
import { AMOUNT, ASSET, NETWORK, PublicError, type Attempt, type AuthorizationIdentity, type Quote } from '../domain/model.js';
import type { AuthorizationPolicy, FinalityPolicy, ReadonlyRpc } from '../ports/index.js';

const ADDRESS=/^0x[0-9a-f]{40}$/;
const HASH=/^0x[0-9a-f]{64}$/;
const UINT=/^(0|[1-9][0-9]*)$/;
function object(value: unknown): Record<string,unknown> { if(!value||typeof value!=='object'||Array.isArray(value))throw new PublicError('PAYMENT_REJECTED',409); return value as Record<string,unknown>; }
function exactKeys(value: Record<string,unknown>,keys: string[]): void { if(Object.keys(value).sort().join()!==[...keys].sort().join())throw new PublicError('PAYMENT_REJECTED',409); }
function canonical(value: Record<string,string>): string { return Object.keys(value).sort().map(key=>`${key}=${value[key]}`).join('\n'); }

export class MezoAuthorizationPolicy implements AuthorizationPolicy {
  readonly reviewed=true;
  readonly version='liqvera-eip3009-identity/v1';
  constructor(private readonly now:()=>Date=()=>new Date()) {}
  identify(payment: PaymentPayload,quote: Quote): AuthorizationIdentity {
    const outer=object(payment); const accepted=object(outer.accepted); const body=object(outer.payload);
    if(accepted.extra!==undefined) {
      const extra=object(accepted.extra); exactKeys(extra,['assetTransferMethod']);
      if(extra.assetTransferMethod!=='eip3009')throw new PublicError('PAYMENT_REJECTED',409);
    }
    exactKeys(body,['authorization','signature']); const authorization=object(body.authorization);
    exactKeys(authorization,['from','to','value','validAfter','validBefore','nonce']);
    const values={from:String(authorization.from).toLowerCase(),to:String(authorization.to).toLowerCase(),value:String(authorization.value),
      validAfter:String(authorization.validAfter),validBefore:String(authorization.validBefore),nonce:String(authorization.nonce).toLowerCase()};
    if(outer.x402Version!==2||accepted.scheme!=='exact'||accepted.network!==NETWORK||String(accepted.asset).toLowerCase()!==ASSET.toLowerCase()||
      accepted.amount!==AMOUNT||String(accepted.payTo).toLowerCase()!==quote.terms.pay_to||values.from!==quote.terms.expected_payer||values.to!==quote.terms.pay_to||
      values.value!==AMOUNT||!ADDRESS.test(values.from)||!ADDRESS.test(values.to)||!UINT.test(values.validAfter)||!UINT.test(values.validBefore)||!HASH.test(values.nonce)||
      typeof body.signature!=='string'||!/^0x[0-9a-f]{130}$/.test(body.signature))throw new PublicError('PAYMENT_REJECTED',409);
    const now=Math.floor(this.now().getTime()/1000); const before=Number(values.validBefore); const after=Number(values.validAfter);
    if(!Number.isSafeInteger(before)||!Number.isSafeInteger(after)||after>now||before<=now||before-now>600)throw new PublicError('PAYMENT_REJECTED',409);
    const signatureCommitment=createHash('sha256').update(body.signature).digest('hex');
    const correlation={...values,signature_commitment:signatureCommitment,network:NETWORK,asset:ASSET.toLowerCase(),asset_transfer_method:'eip3009',quote_id:quote.id,report_id:quote.report_id,report_sha256:quote.report_sha256};
    const identity=createHash('sha256').update(canonical(correlation)).digest('hex');
    return {identity,version:this.version,payer:values.from,valid_until:new Date(before*1000).toISOString(),correlation};
  }
  async bindsTransfer(attempt: Attempt,transactionValue: unknown,logValue: unknown): Promise<boolean> {
    if(attempt.identity_version!==this.version||attempt.correlation.network!==NETWORK||attempt.correlation.asset!==ASSET.toLowerCase()||attempt.correlation.value!==AMOUNT)return false;
    const transaction=object(transactionValue); const log=object(logValue); const input=transaction.input;
    if(transaction.hash!==attempt.tx_hash||log.transactionHash!==attempt.tx_hash||String(transaction.to).toLowerCase()!==ASSET.toLowerCase()||
      typeof input!=='string'||!/^0xe3ee160e[0-9a-f]{576}$/.test(input))return false;
    const words=Array.from({length:9},(_,index)=>input.slice(10+index*64,10+(index+1)*64));
    const addressWord=(value:string)=>value.slice(2).padStart(64,'0');
    const uintWord=(value:string)=>BigInt(value).toString(16).padStart(64,'0');
    const signature=`0x${words[7]!}${words[8]!}${words[6]!.slice(62)}`;
    return words[0]===addressWord(attempt.correlation.from!)&&words[1]===addressWord(attempt.correlation.to!)&&
      words[2]===uintWord(attempt.correlation.value!)&&words[3]===uintWord(attempt.correlation.validAfter!)&&
      words[4]===uintWord(attempt.correlation.validBefore!)&&words[5]===attempt.correlation.nonce!.slice(2)&&
      createHash('sha256').update(signature).digest('hex')===attempt.correlation.signature_commitment;
  }
}

export class MezoFinalityPolicy implements FinalityPolicy {
  readonly reviewed=true;
  readonly version: string;
  constructor(private readonly confirmations=12){ if(!Number.isSafeInteger(confirmations)||confirmations<1)throw new Error('FINALITY_POLICY_INVALID'); this.version=`mezo-testnet-canonical-${confirmations}/v1`; }
  async isFinal(receiptValue: unknown,blockValue: unknown,rpc: ReadonlyRpc): Promise<boolean> {
    try {
      const receipt=object(receiptValue),block=object(blockValue);
      if(typeof receipt.blockNumber!=='string'||typeof receipt.blockHash!=='string'||block.hash!==receipt.blockHash||block.number!==receipt.blockNumber)return false;
      const height=BigInt(receipt.blockNumber); const latest=object(await rpc.call('eth_getBlockByNumber',['latest',false]));
      if(typeof latest.number!=='string'||BigInt(latest.number)<height+BigInt(this.confirmations-1))return false;
      const canonicalBlock=object(await rpc.call('eth_getBlockByNumber',[receipt.blockNumber,false]));
      return canonicalBlock.hash===receipt.blockHash&&canonicalBlock.number===receipt.blockNumber;
    } catch { return false; }
  }
}
