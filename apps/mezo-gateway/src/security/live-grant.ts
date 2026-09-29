import { createHash } from 'node:crypto';
import { AMOUNT, ASSET, CHAIN_ID, NETWORK } from '../domain/model.js';
import { X402_PERMIT2 } from '@liqvera/mezo-protocol';

const OID=/^[0-9a-f]{40}$/; const DIGEST=/^[0-9a-f]{64}$/; const ADDRESS=/^0x[0-9a-f]{40}$/;
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
const FIELDS=['schema','grant_id','subject_commit','subject_tree','plan_sha256','scheme','settlement_broadcaster','network','chain_id','asset','amount_atomic','buyer','pay_to','maximum_settlement_submissions','max_buyer_native_gas_wei','asset_transfer_method','permit2_address','permit2_proxy','approval_mode','required_extension','authorization_identity_version','facilitator_url','rpc_url','database_identity_kind','database_host_policy','database_identity','expires_at'];
export class LivePaymentGrant {
  private _digest:string;
  get digest():string{return this._digest;}
  private constructor(readonly raw:Readonly<Record<string,unknown>>) { this._digest=createHash('sha256').update(JSON.stringify(raw,Object.keys(raw).sort())).digest('hex'); }
  static parse(value:unknown,now:Date):LivePaymentGrant {
    return LivePaymentGrant.parseValue(value,now,true);
  }
  private static parseValue(value:unknown,now:Date,enforceExpiry:boolean):LivePaymentGrant {
    if(!value||typeof value!=='object'||Array.isArray(value))throw new Error('LIVE_GRANT_INVALID'); const raw=value as Record<string,unknown>;
    if(Object.keys(raw).sort().join()!==[...FIELDS].sort().join()||raw.schema!=='liqvera-mezo-payment-grant/v1'||!UUID.test(String(raw.grant_id))||!OID.test(String(raw.subject_commit))||!OID.test(String(raw.subject_tree))||!DIGEST.test(String(raw.plan_sha256))||
      raw.scheme!=='exact'||raw.settlement_broadcaster!=='facilitator'||raw.network!==NETWORK||raw.chain_id!==CHAIN_ID||String(raw.asset).toLowerCase()!==ASSET.toLowerCase()||raw.amount_atomic!==AMOUNT||raw.maximum_settlement_submissions!==1||raw.max_buyer_native_gas_wei!=='100000000000000'||
      raw.asset_transfer_method!==X402_PERMIT2.assetTransferMethod||raw.permit2_address!==X402_PERMIT2.permit2Address||raw.permit2_proxy!==X402_PERMIT2.exactProxyAddress||raw.approval_mode!==X402_PERMIT2.approvalMode||raw.required_extension!==X402_PERMIT2.requiredExtension||raw.authorization_identity_version!==X402_PERMIT2.authorizationIdentityVersion||
      raw.facilitator_url!=='https://facilitator.vativ.io/'||raw.rpc_url!=='https://rpc.test.mezo.org/'||raw.database_identity_kind!=='sha256-credential-free-postgresql-endpoint/v1'||raw.database_host_policy!=='loopback-only/v1'||!DIGEST.test(String(raw.database_identity))||
      !ADDRESS.test(String(raw.buyer))||!ADDRESS.test(String(raw.pay_to))||String(raw.buyer)===String(raw.pay_to)||/^0x0{40}$/.test(String(raw.pay_to)))throw new Error('LIVE_GRANT_INVALID');
    const expiry=Date.parse(String(raw.expires_at)); if(!Number.isFinite(expiry)||(enforceExpiry&&(expiry<=now.getTime()||expiry>now.getTime()+15*60_000)))throw new Error('LIVE_GRANT_EXPIRED');
    return new LivePaymentGrant(Object.freeze({...raw}));
  }
  static parseBytes(bytes:Uint8Array,now:Date):LivePaymentGrant {
    return LivePaymentGrant.parseByteValue(bytes,now,true);
  }
  static parseBytesForReconciliation(bytes:Uint8Array,now:Date):LivePaymentGrant {
    return LivePaymentGrant.parseByteValue(bytes,now,false);
  }
  private static parseByteValue(bytes:Uint8Array,now:Date,enforceExpiry:boolean):LivePaymentGrant {
    if(bytes.byteLength===0||bytes.byteLength>16_384)throw new Error('LIVE_GRANT_INVALID');
    let value:unknown;
    try { value=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes)); }
    catch { throw new Error('LIVE_GRANT_INVALID'); }
    const parsed=LivePaymentGrant.parseValue(value,now,enforceExpiry);
    parsed._digest=createHash('sha256').update(bytes).digest('hex');
    return parsed;
  }
  assertContext(input:{subjectCommit:string;subjectTree:string;planSha256:string;buyer:string;payTo:string}):void {
    if(input.subjectCommit!==this.raw.subject_commit||input.subjectTree!==this.raw.subject_tree||input.planSha256!==this.raw.plan_sha256||input.buyer!==this.raw.buyer||input.payTo!==this.raw.pay_to)throw new Error('LIVE_GRANT_MISMATCH');
  }
  authorize(input:{subjectCommit:string;subjectTree:string;planSha256:string;buyer:string;payTo:string;now:Date}):void {
    this.assertContext(input);
    const expiry=Date.parse(String(this.raw.expires_at));
    if(expiry<=input.now.getTime()||expiry>input.now.getTime()+15*60_000)throw new Error('LIVE_GRANT_EXPIRED');
  }
}
