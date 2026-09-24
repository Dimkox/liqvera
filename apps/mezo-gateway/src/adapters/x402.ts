import { x402ResourceServer } from '@x402/core/server';
import { decodePaymentSignatureHeader, encodePaymentRequiredHeader, encodePaymentResponseHeader } from '@x402/core/http';
import { ExactEvmScheme } from '@x402/evm/exact/server';
import type { PaymentPayload, PaymentRequirements, VerifyResponse, SettleResponse, SupportedResponse } from '@x402/core/types';
import type { AuthorizationPolicy, FinalityPolicy, PaymentPort } from '../ports/index.js';
import { AMOUNT, ASSET, NETWORK, PublicError, type Attempt, type Quote, type Receipt, type Reason } from '../domain/model.js';
import { paymentHeader } from '../security/input.js';
import { boundedJson } from './http.js';
import { MezoReceiptReader } from './mezo-rpc.js';
// Policy implementations require reviewed scheme-specific identity, nonce,
// replay-domain, chain correlation and finality evidence. Configuration cannot
// flip these defaults into an approval.
export const unresolvedIdentity: AuthorizationPolicy = {
  reviewed:false,version:'UNRESOLVED_F5',
  identify(){throw new PublicError('AUTHORIZATION_IDENTITY_UNVERIFIED');},
  async bindsTransfer(){return false;}
};
export const unresolvedFinality: FinalityPolicy = { reviewed:false,version:'FINALITY_RULE_UNVERIFIED',async isFinal(){return false;} };
const facilitator=new URL('https://facilitator.vativ.io');
// No retries, redirects or custom status endpoint. The SDK controls protocol
// payload construction; this transport supplies bounded I/O only.
const transport={
  async verify(paymentPayload: PaymentPayload,paymentRequirements: PaymentRequirements): Promise<VerifyResponse> {
    return await boundedJson(new URL('/verify',facilitator),{method:'POST',body:JSON.stringify({x402Version:2,paymentPayload,paymentRequirements})},65536) as VerifyResponse;
  },
  async settle(paymentPayload: PaymentPayload,paymentRequirements: PaymentRequirements): Promise<SettleResponse> {
    return await boundedJson(new URL('/settle',facilitator),{method:'POST',body:JSON.stringify({x402Version:2,paymentPayload,paymentRequirements})},65536) as SettleResponse;
  },
  async getSupported(): Promise<SupportedResponse> {
    return await boundedJson(new URL('/supported',facilitator),{method:'GET'},65536) as SupportedResponse;
  }
};
export class OfficialX402 implements PaymentPort {
  private readonly server=new x402ResourceServer(transport).register(NETWORK,new ExactEvmScheme());
  private initialized=false;
  constructor(private readonly identity: AuthorizationPolicy,private readonly finality: FinalityPolicy,private readonly reader: MezoReceiptReader,private readonly publicBase: URL) {}
  async initialize(): Promise<void> {
    if(!this.identity.reviewed||!this.finality.reviewed)return;
    await this.server.initialize();
    this.initialized=!!this.server.getSupportedKind(2,NETWORK,'exact');
  }
  blockers(): Reason[] {
    const reasons: Reason[]=[];
    if(!this.identity.reviewed)reasons.push('AUTHORIZATION_IDENTITY_UNVERIFIED');
    if(!this.finality.reviewed)reasons.push('FINALITY_RULE_UNVERIFIED');
    if(!this.initialized)reasons.push('PAYMENT_SERVICE_UNAVAILABLE');
    return reasons;
  }
  private ready(): void { if(this.blockers().length)throw new PublicError('PAYMENT_NOT_READY'); }
  async requirements(quote: Quote) {
    this.ready();
    const values=await this.server.buildPaymentRequirements({scheme:'exact',network:NETWORK,payTo:quote.terms.pay_to,
      price:{asset:ASSET,amount:AMOUNT},maxTimeoutSeconds:120});
    if(values.length!==1)throw new PublicError('PAYMENT_NOT_READY');
    const value=values[0]!;
    if(value.scheme!=='exact'||value.network!==NETWORK||value.asset.toLowerCase()!==ASSET.toLowerCase()||value.amount!==AMOUNT||value.payTo.toLowerCase()!==quote.terms.pay_to)throw new PublicError('PAYMENT_NOT_READY');
    const required=await this.server.createPaymentRequiredResponse(values,{url:new URL(`/v1/reports/${quote.report_id}`,this.publicBase).href,description:'Liqvera immutable BTC perpetual snapshot report',mimeType:'application/json'});
    return {value,header:encodePaymentRequiredHeader(required)};
  }
  async verify(header: string,quote: Quote) {
    this.ready();
    const payload=decodePaymentSignatureHeader(paymentHeader(header));
    const {value:requirements}=await this.requirements(quote);
    if(payload.x402Version!==2 || payload.accepted?.scheme!=='exact'||payload.accepted.network!==NETWORK||
      payload.accepted.asset?.toLowerCase()!==ASSET.toLowerCase()||payload.accepted.amount!==AMOUNT||payload.accepted.payTo?.toLowerCase()!==quote.terms.pay_to)
      throw new PublicError('PAYMENT_REJECTED',409);
    const result=await this.server.verifyPayment(payload,requirements);
    if(result.isValid!==true||result.payer?.toLowerCase()!==quote.terms.expected_payer)throw new PublicError('PAYMENT_REJECTED',409);
    const identity=this.identity.identify(payload,quote);
    if(identity.payer!==quote.terms.expected_payer||!identity.identity||identity.identity.length>512||identity.version!==this.identity.version||
      !Number.isFinite(Date.parse(identity.valid_until))||Date.parse(identity.valid_until)<=Date.now())throw new PublicError('PAYMENT_REJECTED',409);
    return {payload,requirements,identity};
  }
  async settle(payload: PaymentPayload,requirements: PaymentRequirements) {
    this.ready();
    const result=await this.server.settlePayment(payload,requirements);
    // Even success is only a transaction hint, not finality or entitlement.
    const tx=typeof result.transaction==='string'&&/^0x[0-9a-fA-F]{64}$/.test(result.transaction)?result.transaction.toLowerCase():null;
    return {tx_hash:tx};
  }
  async confirm(quote: Quote,attempt: Attempt) {
    const receipt=await this.reader.confirmation(quote,attempt); if(!receipt)return null;
    return {receipt,response_header:encodePaymentResponseHeader({success:true,transaction:receipt.tx_hash,network:NETWORK,payer:receipt.payer})};
  }
  async revalidate(quote: Quote,attempt: Attempt,receipt: Receipt): Promise<boolean> {
    const current=await this.reader.confirmation(quote,attempt);
    return !!current && current.tx_hash===receipt.tx_hash && current.block_hash===receipt.block_hash &&
      current.block_number===receipt.block_number && current.log_index===receipt.log_index && current.finality_policy_version===receipt.finality_policy_version;
  }
}
