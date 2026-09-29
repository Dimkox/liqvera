import { createHash } from 'node:crypto';
import type { PaymentPayload } from '@x402/core/types';
import { PERMIT2_ADDRESS, x402ExactPermit2ProxyABI, x402ExactPermit2ProxyAddress } from '@x402/evm';
import { decodeFunctionData, encodeFunctionData } from 'viem';
import { MUSD_PERMIT } from '@liqvera/mezo-protocol';
import { AMOUNT, ASSET, NETWORK, PublicError, type Attempt, type AuthorizationIdentity, type Quote } from '../domain/model.js';
import type { AuthorizationPolicy, FinalityPolicy, ReadonlyRpc } from '../ports/index.js';

const ADDRESS=/^0x[0-9a-f]{40}$/;
const UINT=/^(0|[1-9][0-9]*)$/;
function object(value: unknown): Record<string,unknown> { if(!value||typeof value!=='object'||Array.isArray(value))throw new PublicError('PAYMENT_REJECTED',409); return value as Record<string,unknown>; }
function exactKeys(value: Record<string,unknown>,keys: string[]): void { if(Object.keys(value).sort().join()!==[...keys].sort().join())throw new PublicError('PAYMENT_REJECTED',409); }
function canonical(value: Record<string,string>): string { return Object.keys(value).sort().map(key=>`${key}=${value[key]}`).join('\n'); }

export class MezoAuthorizationPolicy implements AuthorizationPolicy {
  readonly reviewed=true;
  readonly version='liqvera-permit2-eip2612-identity/v1';
  constructor(private readonly now:()=>Date=()=>new Date()) {}
  identify(payment: PaymentPayload,quote: Quote): AuthorizationIdentity {
    const outer=object(payment); const accepted=object(outer.accepted); const body=object(outer.payload);
    const extra=object(accepted.extra); exactKeys(extra,['assetTransferMethod','name','version']);
    exactKeys(body,['permit2Authorization','signature']); const authorization=object(body.permit2Authorization);
    exactKeys(authorization,['from','permitted','spender','nonce','deadline','witness']);
    const permitted=object(authorization.permitted); exactKeys(permitted,['token','amount']);
    const witness=object(authorization.witness); exactKeys(witness,['to','validAfter']);
    const extensions=object(outer.extensions); exactKeys(extensions,['eip2612GasSponsoring']);
    const extension=object(extensions.eip2612GasSponsoring); exactKeys(extension,['info','schema']);
    const permit=object(extension.info); exactKeys(permit,['from','asset','spender','amount','nonce','deadline','signature','version']);
    const values={from:String(authorization.from).toLowerCase(),token:String(permitted.token).toLowerCase(),amount:String(permitted.amount),
      spender:String(authorization.spender).toLowerCase(),nonce:String(authorization.nonce),deadline:String(authorization.deadline),
      to:String(witness.to).toLowerCase(),validAfter:String(witness.validAfter)};
    const approval={from:String(permit.from).toLowerCase(),asset:String(permit.asset).toLowerCase(),spender:String(permit.spender).toLowerCase(),
      amount:String(permit.amount),nonce:String(permit.nonce),deadline:String(permit.deadline),version:String(permit.version)};
    if(outer.x402Version!==2||accepted.scheme!=='exact'||accepted.network!==NETWORK||String(accepted.asset).toLowerCase()!==ASSET.toLowerCase()||
      accepted.amount!==AMOUNT||String(accepted.payTo).toLowerCase()!==quote.terms.pay_to||extra.assetTransferMethod!=='permit2'||extra.name!==MUSD_PERMIT.domainName||extra.version!==MUSD_PERMIT.domainVersion||
      values.from!==quote.terms.expected_payer||values.to!==quote.terms.pay_to||values.token!==ASSET.toLowerCase()||values.amount!==AMOUNT||
      values.spender!==x402ExactPermit2ProxyAddress.toLowerCase()||!ADDRESS.test(values.from)||!ADDRESS.test(values.to)||!UINT.test(values.validAfter)||!UINT.test(values.deadline)||!UINT.test(values.nonce)||
      approval.from!==values.from||approval.asset!==values.token||approval.spender!==PERMIT2_ADDRESS.toLowerCase()||approval.amount!==AMOUNT||approval.version!=='1'||
      !UINT.test(approval.nonce)||!UINT.test(approval.deadline)||typeof body.signature!=='string'||!/^0x[0-9a-fA-F]{130}$/.test(body.signature)||
      typeof permit.signature!=='string'||!/^0x[0-9a-fA-F]{130}$/.test(permit.signature))throw new PublicError('PAYMENT_REJECTED',409);
    const now=Math.floor(this.now().getTime()/1000); const deadline=Number(values.deadline); const after=Number(values.validAfter); const approvalDeadline=Number(approval.deadline);
    if(!Number.isSafeInteger(deadline)||!Number.isSafeInteger(after)||!Number.isSafeInteger(approvalDeadline)||after>now||deadline<=now||deadline-now>600||approvalDeadline<deadline||approvalDeadline-now>600)throw new PublicError('PAYMENT_REJECTED',409);
    const signatureCommitment=createHash('sha256').update(body.signature).digest('hex');
    const approvalSignatureCommitment=createHash('sha256').update(permit.signature).digest('hex');
    const correlation={...values,eip2612_from:approval.from,eip2612_asset:approval.asset,eip2612_spender:approval.spender,eip2612_amount:approval.amount,
      eip2612_nonce:approval.nonce,eip2612_deadline:approval.deadline,eip2612_version:approval.version,signature_commitment:signatureCommitment,
      eip2612_signature_commitment:approvalSignatureCommitment,network:NETWORK,asset:ASSET.toLowerCase(),asset_transfer_method:'permit2',
      approval_mode:'eip2612-gas-sponsoring',required_extension:'eip2612GasSponsoring',permit2_address:PERMIT2_ADDRESS.toLowerCase(),
      permit2_proxy:x402ExactPermit2ProxyAddress.toLowerCase(),quote_id:quote.id,report_id:quote.report_id,report_sha256:quote.report_sha256};
    const identity=createHash('sha256').update(canonical(correlation)).digest('hex');
    return {identity,version:this.version,payer:values.from,valid_until:new Date(Math.min(deadline,approvalDeadline)*1000).toISOString(),correlation};
  }
  async bindsTransfer(attempt: Attempt,transactionValue: unknown,logValue: unknown): Promise<boolean> {
    try {
      if(attempt.identity_version!==this.version||attempt.correlation.network!==NETWORK||attempt.correlation.asset!==ASSET.toLowerCase()||attempt.correlation.amount!==AMOUNT)return false;
      const transaction=object(transactionValue); const log=object(logValue); const input=transaction.input;
      if(transaction.hash!==attempt.tx_hash||log.transactionHash!==attempt.tx_hash||String(transaction.to).toLowerCase()!==x402ExactPermit2ProxyAddress.toLowerCase()||typeof input!=='string')return false;
      const decoded=decodeFunctionData({abi:x402ExactPermit2ProxyABI,data:input as `0x${string}`});
      if(decoded.functionName!=='settleWithPermit'||!decoded.args)return false;
      if(encodeFunctionData({abi:x402ExactPermit2ProxyABI,functionName:'settleWithPermit',args:decoded.args})!==input)return false;
      const [permit2612,permit2,owner,witness,signature]=decoded.args as unknown as [Record<string,unknown>,Record<string,unknown>,string,Record<string,unknown>,string];
      const permitted=object(permit2.permitted);
      const approvalSignature=`0x${String(permit2612.r).slice(2)}${String(permit2612.s).slice(2)}${Number(permit2612.v).toString(16).padStart(2,'0')}`;
      return String(owner).toLowerCase()===attempt.correlation.from&&String(permitted.token).toLowerCase()===attempt.correlation.token&&String(permitted.amount)===attempt.correlation.amount&&
        String(permit2.nonce)===attempt.correlation.nonce&&String(permit2.deadline)===attempt.correlation.deadline&&String(witness.to).toLowerCase()===attempt.correlation.to&&
        String(witness.validAfter)===attempt.correlation.validAfter&&String(permit2612.value)===attempt.correlation.eip2612_amount&&String(permit2612.deadline)===attempt.correlation.eip2612_deadline&&
        createHash('sha256').update(signature).digest('hex')===attempt.correlation.signature_commitment&&createHash('sha256').update(approvalSignature).digest('hex')===attempt.correlation.eip2612_signature_commitment;
    } catch { return false; }
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
