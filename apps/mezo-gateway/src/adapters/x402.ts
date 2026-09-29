import { x402ResourceServer } from '@x402/core/server';
import { decodePaymentSignatureHeader, encodePaymentRequiredHeader, encodePaymentResponseHeader } from '@x402/core/http';
import { ExactEvmScheme } from '@x402/evm/exact/server';
import { declareEip2612GasSponsoringExtension } from '@x402/extensions';
import { MUSD_PERMIT, X402_PERMIT2 } from '@liqvera/mezo-protocol';
import type { PaymentPayload, PaymentRequirements, VerifyResponse, SettleResponse, SupportedResponse } from '@x402/core/types';
import type { AuthorizationPolicy, FinalityPolicy, PaymentPort } from '../ports/index.js';
import { AMOUNT, ASSET, NETWORK, PublicError, type Attempt, type Quote, type Receipt, type Reason } from '../domain/model.js';
import { paymentHeader } from '../security/input.js';
import { boundedJson } from './http.js';
import { MezoReceiptReader } from './mezo-rpc.js';
import type { LivePaymentGrant } from '../security/live-grant.js';
export interface LivePaymentContext { subjectCommit:string;subjectTree:string;planSha256:string;buyer:string;payTo:string }
// Policy implementations require reviewed scheme-specific identity, nonce,
// replay-domain, chain correlation and finality evidence. Configuration cannot
// flip these defaults into an approval.
export const unresolvedIdentity: AuthorizationPolicy = {
  reviewed:false,version:'UNRESOLVED_F5',
  identify(){throw new PublicError('AUTHORIZATION_IDENTITY_UNVERIFIED');},
  async bindsTransfer(){return false;}
};
export const unresolvedFinality: FinalityPolicy = { reviewed:false,version:'FINALITY_RULE_UNVERIFIED',async isFinal(){return false;} };
const defaultFacilitator=new URL('https://facilitator.vativ.io');
export function settlementTransaction(result: Pick<SettleResponse,'success'|'errorReason'|'transaction'>):string|null {
  const pending=result.success===false&&result.errorReason==='settlement_pending';
  return (result.success===true||pending)&&typeof result.transaction==='string'&&/^0x[0-9a-fA-F]{64}$/.test(result.transaction)
    ? result.transaction.toLowerCase():null;
}
export function permit2Capability(kind:unknown,extensions:unknown):boolean {
  if(!kind||typeof kind!=='object'||Array.isArray(kind)||!Array.isArray(extensions))return false;
  const value=kind as Record<string,unknown>; const extra=value.extra;
  if(Object.keys(value).sort().join()!==['x402Version','scheme','network','extra'].sort().join()||value.x402Version!==2||value.scheme!=='exact'||value.network!==NETWORK||
    !extra||typeof extra!=='object'||Array.isArray(extra)||Object.keys(extra).join()!=='assets'||extensions.length!==1||extensions[0]!==X402_PERMIT2.requiredExtension)return false;
  const assets=(extra as Record<string,unknown>).assets;
  if(!Array.isArray(assets))return false;
  const matches=assets.filter(item=>item&&typeof item==='object'&&!Array.isArray(item)&&String((item as Record<string,unknown>).address).toLowerCase()===ASSET.toLowerCase());
  if(matches.length!==1)return false;
  const asset=matches[0] as Record<string,unknown>; const eip712=asset.eip712;
  return Object.keys(asset).sort().join()===['address','symbol','decimals','eip712','assetTransferMethod','supportsEip2612'].sort().join()&&
    asset.symbol==='MUSD'&&asset.decimals===18&&asset.assetTransferMethod===X402_PERMIT2.assetTransferMethod&&asset.supportsEip2612===true&&
    !!eip712&&typeof eip712==='object'&&!Array.isArray(eip712)&&Object.keys(eip712).sort().join()==='name,version'&&
    (eip712 as Record<string,unknown>).name===MUSD_PERMIT.domainName&&(eip712 as Record<string,unknown>).version===MUSD_PERMIT.domainVersion;
}
// No retries, redirects or custom status endpoint. The SDK controls protocol
// payload construction; this transport supplies bounded I/O only.
function facilitatorTransport(facilitator:URL) { return {
  async verify(paymentPayload: PaymentPayload,paymentRequirements: PaymentRequirements): Promise<VerifyResponse> {
    return await boundedJson(new URL('/verify',facilitator),{method:'POST',body:JSON.stringify({x402Version:2,paymentPayload,paymentRequirements})},65536) as VerifyResponse;
  },
  async settle(paymentPayload: PaymentPayload,paymentRequirements: PaymentRequirements): Promise<SettleResponse> {
    return await boundedJson(new URL('/settle',facilitator),{method:'POST',body:JSON.stringify({x402Version:2,paymentPayload,paymentRequirements})},65536) as SettleResponse;
  },
  async getSupported(): Promise<SupportedResponse> {
    return await boundedJson(new URL('/supported',facilitator),{method:'GET'},65536) as SupportedResponse;
  }
}; }
export class OfficialX402 implements PaymentPort {
  private readonly server:x402ResourceServer;
  private initialized=false;
  constructor(private readonly identity: AuthorizationPolicy,private readonly finality: FinalityPolicy,private readonly reader: MezoReceiptReader,private readonly publicBase: URL,
    private readonly grant: LivePaymentGrant|null=null,private readonly liveContext:LivePaymentContext|null=null,private readonly now:()=>Date=()=>new Date(),
    facilitator:URL=defaultFacilitator) {
    this.server=new x402ResourceServer(facilitatorTransport(facilitator)).register(NETWORK,new ExactEvmScheme());
  }
  private authorizeGrant():void {
    if(!this.grant||!this.liveContext)throw new PublicError('PAYMENT_NOT_READY');
    this.grant.authorize({...this.liveContext,now:this.now()});
  }
  async initialize(): Promise<void> {
    if(!this.identity.reviewed||!this.finality.reviewed||!this.grant||!this.liveContext)return;
    this.authorizeGrant();
    await this.server.initialize();
    this.initialized=permit2Capability(this.server.getSupportedKind(2,NETWORK,'exact'),this.server.getFacilitatorExtensions(2,NETWORK,'exact'));
  }
  blockers(): Reason[] {
    const reasons: Reason[]=[];
    if(!this.identity.reviewed)reasons.push('AUTHORIZATION_IDENTITY_UNVERIFIED');
    if(!this.finality.reviewed)reasons.push('FINALITY_RULE_UNVERIFIED');
    if(!this.grant||!this.liveContext)reasons.push('EXTERNAL_GRANT_REQUIRED');
    if(!this.initialized)reasons.push('PAYMENT_SERVICE_UNAVAILABLE');
    return reasons;
  }
  private ready(): void { if(this.blockers().length)throw new PublicError('PAYMENT_NOT_READY'); }
  async requirements(quote: Quote) {
    this.ready();
    const values=await this.server.buildPaymentRequirements({scheme:'exact',network:NETWORK,payTo:quote.terms.pay_to,
      price:{asset:ASSET,amount:AMOUNT},maxTimeoutSeconds:120,extra:{assetTransferMethod:X402_PERMIT2.assetTransferMethod,name:MUSD_PERMIT.domainName,version:MUSD_PERMIT.domainVersion}});
    if(values.length!==1)throw new PublicError('PAYMENT_NOT_READY');
    const value=values[0]!;
    if(value.scheme!=='exact'||value.network!==NETWORK||value.asset.toLowerCase()!==ASSET.toLowerCase()||value.amount!==AMOUNT||value.payTo.toLowerCase()!==quote.terms.pay_to||value.extra?.assetTransferMethod!==X402_PERMIT2.assetTransferMethod||value.extra?.name!==MUSD_PERMIT.domainName||value.extra?.version!==MUSD_PERMIT.domainVersion)throw new PublicError('PAYMENT_NOT_READY');
    const required=await this.server.createPaymentRequiredResponse(values,{url:new URL(`/v1/reports/${quote.report_id}`,this.publicBase).href,description:'Liqvera immutable BTC perpetual snapshot report',mimeType:'application/json'},undefined,declareEip2612GasSponsoringExtension());
    return {value,header:encodePaymentRequiredHeader(required)};
  }
  async verify(header: string,quote: Quote) {
    this.ready();
    const payload=decodePaymentSignatureHeader(paymentHeader(header));
    const {value:requirements}=await this.requirements(quote);
    if(payload.x402Version!==2 || payload.accepted?.scheme!=='exact'||payload.accepted.network!==NETWORK||
      payload.accepted.asset?.toLowerCase()!==ASSET.toLowerCase()||payload.accepted.amount!==AMOUNT||payload.accepted.payTo?.toLowerCase()!==quote.terms.pay_to||payload.accepted.extra?.assetTransferMethod!==X402_PERMIT2.assetTransferMethod)
      throw new PublicError('PAYMENT_REJECTED',409);
    const result=await this.server.verifyPayment(payload,requirements);
    if(result.isValid!==true||result.payer?.toLowerCase()!==quote.terms.expected_payer)throw new PublicError('PAYMENT_REJECTED',409);
    const identity=this.identity.identify(payload,quote);
    if(identity.payer!==quote.terms.expected_payer||!identity.identity||identity.identity.length>512||identity.version!==this.identity.version||
      !Number.isFinite(Date.parse(identity.valid_until))||Date.parse(identity.valid_until)<=Date.now())throw new PublicError('PAYMENT_REJECTED',409);
    this.authorizeGrant();
    if(this.liveContext!.buyer!==identity.payer||this.liveContext!.payTo!==quote.terms.pay_to)throw new PublicError('PAYMENT_REJECTED',409);
    const balance=await this.reader.nativeBalanceSnapshot(identity.payer);
    identity.correlation.buyer_native_balance_before=balance.balance;
    identity.correlation.buyer_native_balance_before_block_number=balance.block_number;
    identity.correlation.buyer_native_balance_before_block_hash=balance.block_hash;
    identity.correlation.live_grant_digest=this.grant!.digest;
    identity.correlation.live_grant_id=String(this.grant!.raw.grant_id);
    return {payload,requirements,identity};
  }
  async settle(payload: PaymentPayload,requirements: PaymentRequirements) {
    this.ready();
    this.authorizeGrant();
    const result=await this.server.settlePayment(payload,requirements);
    // A transaction-bearing settlement_pending response is spent and enters
    // confirm-only reconciliation exactly like a successful submission.
    const tx=settlementTransaction(result);
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
