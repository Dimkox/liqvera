import { OfficialX402, type LivePaymentContext } from '../adapters/x402.js';
import type { MezoReceiptReader } from '../adapters/mezo-rpc.js';
import type { AuthorizationPolicy, FinalityPolicy } from '../ports/index.js';
import { LivePaymentGrant } from './live-grant.js';

export interface LiveCompositionInput { grantBytes:Uint8Array; context:LivePaymentContext; observedAt:Date }

/** Explicit harness seam: ordinary production startup passes null and cannot initialize payment. */
export function composeOfficialX402(identity:AuthorizationPolicy,finality:FinalityPolicy,reader:MezoReceiptReader,
  publicBase:URL,input:LiveCompositionInput|null):OfficialX402 {
  if(!input)return new OfficialX402(identity,finality,reader,publicBase,null,null);
  const grant=LivePaymentGrant.parseBytes(input.grantBytes,input.observedAt);
  grant.authorize({...input.context,now:input.observedAt});
  return new OfficialX402(identity,finality,reader,publicBase,grant,input.context);
}
