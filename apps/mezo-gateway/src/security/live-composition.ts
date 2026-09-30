import { OfficialX402, type LivePaymentContext } from '../adapters/x402.js';
import type { MezoReceiptReader } from '../adapters/mezo-rpc.js';
import type { AuthorizationPolicy, FinalityPolicy } from '../ports/index.js';
import { LivePaymentGrant } from './live-grant.js';
import { constants } from 'node:fs';
import { lstat, open } from 'node:fs/promises';

export interface LiveCompositionInput { grantBytes:Uint8Array; context:LivePaymentContext; observedAt:Date; now?:()=>Date }

export async function readPrivateGrantFile(path:string):Promise<Uint8Array> {
  const before=await lstat(path);
  if(!before.isFile()||before.isSymbolicLink()||before.nlink!==1||(before.mode&0o077)!==0||before.size<1||before.size>16_384)throw new Error('LIVE_GRANT_FILE_UNSAFE');
  const handle=await open(path,constants.O_RDONLY|constants.O_NOFOLLOW);
  try {
    const bytes=await handle.readFile();const after=await handle.stat();
    if(after.dev!==before.dev||after.ino!==before.ino||after.size!==before.size)throw new Error('LIVE_GRANT_FILE_REPLACED');
    return bytes;
  } finally { await handle.close(); }
}

/** Explicit harness seam: ordinary production startup passes null and cannot initialize payment. */
export function composeOfficialX402(identity:AuthorizationPolicy,finality:FinalityPolicy,reader:MezoReceiptReader,
  publicBase:URL,input:LiveCompositionInput|null):OfficialX402 {
  if(!input)return new OfficialX402(identity,finality,reader,publicBase,null,null);
  const grant=LivePaymentGrant.parseBytes(input.grantBytes,input.observedAt);
  grant.authorize({...input.context,now:input.observedAt});
  return new OfficialX402(identity,finality,reader,publicBase,grant,input.context,input.now);
}
