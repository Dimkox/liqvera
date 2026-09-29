import { createHash } from 'node:crypto';
import { AMOUNT, ASSET, CHAIN_ID, NETWORK } from '../domain/model.js';

const OID=/^[0-9a-f]{40}$/; const DIGEST=/^[0-9a-f]{64}$/; const ADDRESS=/^0x[0-9a-f]{40}$/;
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
const FIELDS=['schema','grant_id','subject_commit','subject_tree','plan_sha256','scheme','settlement_broadcaster','network','chain_id','asset','amount_atomic','buyer','pay_to','maximum_settlement_submissions','max_buyer_native_gas_wei','expires_at'];
export class LivePaymentGrant {
  private _digest:string;
  get digest():string{return this._digest;}
  private constructor(readonly raw:Readonly<Record<string,unknown>>) { this._digest=createHash('sha256').update(JSON.stringify(raw,Object.keys(raw).sort())).digest('hex'); }
  static parse(value:unknown,now:Date):LivePaymentGrant {
    if(!value||typeof value!=='object'||Array.isArray(value))throw new Error('LIVE_GRANT_INVALID'); const raw=value as Record<string,unknown>;
    if(Object.keys(raw).sort().join()!==[...FIELDS].sort().join()||raw.schema!=='liqvera-mezo-payment-grant/v1'||!UUID.test(String(raw.grant_id))||!OID.test(String(raw.subject_commit))||!OID.test(String(raw.subject_tree))||!DIGEST.test(String(raw.plan_sha256))||
      raw.scheme!=='exact'||raw.settlement_broadcaster!=='facilitator'||raw.network!==NETWORK||raw.chain_id!==CHAIN_ID||String(raw.asset).toLowerCase()!==ASSET.toLowerCase()||raw.amount_atomic!==AMOUNT||raw.maximum_settlement_submissions!==1||raw.max_buyer_native_gas_wei!=='100000000000000'||
      !ADDRESS.test(String(raw.buyer))||!ADDRESS.test(String(raw.pay_to))||String(raw.buyer)===String(raw.pay_to)||/^0x0{40}$/.test(String(raw.pay_to)))throw new Error('LIVE_GRANT_INVALID');
    const expiry=Date.parse(String(raw.expires_at)); if(!Number.isFinite(expiry)||expiry<=now.getTime()||expiry>now.getTime()+15*60_000)throw new Error('LIVE_GRANT_EXPIRED');
    return new LivePaymentGrant(Object.freeze({...raw}));
  }
  static parseBytes(bytes:Uint8Array,now:Date):LivePaymentGrant {
    if(bytes.byteLength===0||bytes.byteLength>16_384)throw new Error('LIVE_GRANT_INVALID');
    let value:unknown;
    try { value=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes)); }
    catch { throw new Error('LIVE_GRANT_INVALID'); }
    const parsed=LivePaymentGrant.parse(value,now);
    parsed._digest=createHash('sha256').update(bytes).digest('hex');
    return parsed;
  }
  authorize(input:{subjectCommit:string;subjectTree:string;planSha256:string;buyer:string;payTo:string;now:Date}):void {
    if(input.now.getTime()>=Date.parse(String(this.raw.expires_at)))throw new Error('LIVE_GRANT_EXPIRED');
    if(input.subjectCommit!==this.raw.subject_commit||input.subjectTree!==this.raw.subject_tree||input.planSha256!==this.raw.plan_sha256||input.buyer!==this.raw.buyer||input.payTo!==this.raw.pay_to)throw new Error('LIVE_GRANT_MISMATCH');
  }
}
