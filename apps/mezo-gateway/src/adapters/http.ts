import { PublicError } from '../domain/model.js';
export async function boundedJson(url: URL, init: RequestInit, maxBytes = 1048576, timeoutMs = 12000, acceptedErrorStatuses:number[]=[]): Promise<unknown> {
  const timeout = AbortSignal.timeout(timeoutMs);
  const signal = init.signal ? AbortSignal.any([init.signal,timeout]) : timeout;
  const response = await fetch(url, { ...init, signal, redirect:'error', headers:{'content-type':'application/json',...init.headers} });
  if ((!response.ok&&!acceptedErrorStatuses.includes(response.status)) || !response.body) throw new PublicError('SOURCE_UNAVAILABLE');
  const reader = response.body.getReader();
  const chunks: Uint8Array[] = []; let total=0;
  try {
    while (true) {
      const { done,value } = await reader.read(); if (done) break;
      total += value.length; if (total>maxBytes) throw new PublicError('SOURCE_UNAVAILABLE'); chunks.push(value);
    }
  } finally { await reader.cancel(); }
  return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(Buffer.concat(chunks)));
}
export function fixedInternalUrl(raw: string): URL {
  const url=new URL(raw);
  if (!['http:','https:'].includes(url.protocol) || url.username || url.password || url.search || url.hash || url.pathname !== '/')
    throw new PublicError('INVALID_INPUT');
  return url;
}
