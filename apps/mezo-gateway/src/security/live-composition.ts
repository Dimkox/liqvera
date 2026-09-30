import { OfficialX402, type LivePaymentContext } from '../adapters/x402.js';
import type { MezoReceiptReader } from '../adapters/mezo-rpc.js';
import type { AuthorizationPolicy, FinalityPolicy } from '../ports/index.js';
import { LivePaymentGrant } from './live-grant.js';
import { constants } from 'node:fs';
import { lstat, open } from 'node:fs/promises';

export interface LiveCompositionInput { grantBytes:Uint8Array; context:LivePaymentContext&{databaseIdentity:string}; observedAt:Date; now?:()=>Date }
export interface GrantReadHooks { afterOpen?:()=>Promise<void>; afterRead?:()=>Promise<void> }

function safe(stat:{isFile():boolean;nlink:number|bigint;mode:number|bigint;size:number|bigint}):boolean {
  return stat.isFile()&&Number(stat.nlink)===1&&(Number(stat.mode)&0o077)===0&&Number(stat.size)>=1&&Number(stat.size)<=16_384;
}
export async function readPrivateGrantFile(path:string,hooks:GrantReadHooks={}):Promise<Uint8Array> {
  const before=await lstat(path,{bigint:true});
  if(!safe(before))throw new Error('LIVE_GRANT_FILE_UNSAFE');
  const handle=await open(path,constants.O_RDONLY|constants.O_NOFOLLOW);
  try {
    const opened=await handle.stat({bigint:true});
    if(!safe(opened)||opened.dev!==before.dev||opened.ino!==before.ino||opened.size!==before.size)throw new Error('LIVE_GRANT_FILE_CHANGED');
    await hooks.afterOpen?.();
    const buffer=Buffer.alloc(Number(opened.size));let offset=0;
    while(offset<buffer.length) { const {bytesRead}=await handle.read(buffer,offset,buffer.length-offset,offset);if(!bytesRead)break;offset+=bytesRead; }
    const extra=Buffer.alloc(1);const overflow=(await handle.read(extra,0,1,offset)).bytesRead;
    await hooks.afterRead?.();
    const after=await handle.stat({bigint:true});
    if(offset!==buffer.length||overflow!==0||!safe(after)||after.dev!==opened.dev||after.ino!==opened.ino||after.size!==opened.size||
      after.mode!==opened.mode||after.nlink!==opened.nlink||after.mtimeNs!==opened.mtimeNs||after.ctimeNs!==opened.ctimeNs)throw new Error('LIVE_GRANT_FILE_CHANGED');
    return buffer;
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
