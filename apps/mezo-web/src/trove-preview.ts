import {validateTroveReport} from './trove-report.ts';
import type {TroveReport} from './contracts.ts';
const prefix='/demo/troves/22dfc0db8355bc126f89af07914aa2601b42fd84eafc923e319b84bc2b7b60f1';
export const TROVE_PREVIEW=Object.freeze({
 reportSha256:'22dfc0db8355bc126f89af07914aa2601b42fd84eafc923e319b84bc2b7b60f1',
 bundleSha256:'94c0a93520eb91382c45f4690f176e655ccc372e67b9594653ef651cfd419b10',
 reportUrl:`${prefix}/report.json`,bundleUrl:`${prefix}/evidence.zip`,
});
export async function verifyTrovePreview(reportBytes:Uint8Array,bundleBytes:Uint8Array):Promise<TroveReport> {
 for(const [bytes,expected] of [[reportBytes,TROVE_PREVIEW.reportSha256],[bundleBytes,TROVE_PREVIEW.bundleSha256]] as const) {
  const digest=await crypto.subtle.digest('SHA-256',bytes as BufferSource);
  const actual=Array.from(new Uint8Array(digest),b=>b.toString(16).padStart(2,'0')).join('');
  if(actual!==expected)throw new Error('Trove preview digest mismatch.');
 }
 return validateTroveReport(JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(reportBytes)));
}
