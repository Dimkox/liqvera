import { AMOUNT, ASSET, CHAIN_ID, NETWORK } from '../domain/model.js';

const OID=/^[0-9a-f]{40}$/; const DIGEST=/^[0-9a-f]{64}$/; const ADDRESS=/^0x[0-9a-f]{40}$/;
const FIELDS=['schema','subject_commit','subject_tree','plan_sha256','network','chain_id','asset','amount_atomic','buyer','pay_to','maximum_settlement_submissions','max_gas_wei','expires_at'];
export class LivePaymentGrant {
  private submissions=0;
  private constructor(private readonly raw:Record<string,unknown>) {}
  static parse(value:unknown,now:Date):LivePaymentGrant {
    if(!value||typeof value!=='object'||Array.isArray(value))throw new Error('LIVE_GRANT_INVALID'); const raw=value as Record<string,unknown>;
    if(Object.keys(raw).sort().join()!==[...FIELDS].sort().join()||raw.schema!=='liqvera-mezo-payment-grant/v1'||!OID.test(String(raw.subject_commit))||!OID.test(String(raw.subject_tree))||!DIGEST.test(String(raw.plan_sha256))||
      raw.network!==NETWORK||raw.chain_id!==CHAIN_ID||String(raw.asset).toLowerCase()!==ASSET.toLowerCase()||raw.amount_atomic!==AMOUNT||raw.maximum_settlement_submissions!==1||raw.max_gas_wei!=='100000000000000'||
      !ADDRESS.test(String(raw.buyer))||!ADDRESS.test(String(raw.pay_to))||String(raw.buyer)===String(raw.pay_to)||/^0x0{40}$/.test(String(raw.pay_to)))throw new Error('LIVE_GRANT_INVALID');
    const expiry=Date.parse(String(raw.expires_at)); if(!Number.isFinite(expiry)||expiry<=now.getTime()||expiry>now.getTime()+15*60_000)throw new Error('LIVE_GRANT_EXPIRED');
    return new LivePaymentGrant(raw);
  }
  authorize(input:{subjectCommit:string;subjectTree:string;planSha256:string;buyer:string;payTo:string;gasEstimateWei:bigint}):void {
    if(input.subjectCommit!==this.raw.subject_commit||input.subjectTree!==this.raw.subject_tree||input.planSha256!==this.raw.plan_sha256||input.buyer!==this.raw.buyer||input.payTo!==this.raw.pay_to||input.gasEstimateWei>100000000000000n)throw new Error('LIVE_GRANT_MISMATCH');
  }
  consume():void { if(this.submissions>=1)throw new Error('SETTLEMENT_BUDGET_EXHAUSTED'); this.submissions+=1; }
}
