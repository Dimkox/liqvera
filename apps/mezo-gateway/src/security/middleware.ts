import { randomUUID } from 'node:crypto';
import type { RequestHandler } from 'express';
import { PublicError } from '../domain/model.js';
import { logEvent, metrics } from './observability.js';
export function securityHeaders(origins:ReadonlySet<string>):RequestHandler {
  return (request,response,next)=>{
    response.locals.requestId=randomUUID();response.setHeader('X-Request-ID',response.locals.requestId);
    response.setHeader('Cache-Control','private, no-store');response.setHeader('Pragma','no-cache');
    response.setHeader('Content-Security-Policy',"default-src 'none'; frame-ancestors 'none'; base-uri 'none'");
    response.setHeader('X-Content-Type-Options','nosniff');response.setHeader('X-Frame-Options','DENY');
    response.setHeader('Referrer-Policy','no-referrer');response.setHeader('Permissions-Policy','camera=(), microphone=(), geolocation=()');
    response.setHeader('Vary','Origin');
    const started=performance.now();
    response.once('finish',()=>{
      metrics.increment('http_request');if(response.statusCode>=400)metrics.increment('http_error');
      logEvent({event:'HTTP_RESPONSE',request_id:response.locals.requestId,status:response.statusCode,duration_ms:Math.round(performance.now()-started)});
    });
    const seen=new Set<string>();
    for(let index=0;index<request.rawHeaders.length;index+=2) {
      const header=request.rawHeaders[index]!.toLowerCase();
      if(['authorization','payment-signature','idempotency-key','origin','content-type'].includes(header)) {
        if(seen.has(header))return next(new PublicError('INVALID_INPUT',422));seen.add(header);
      }
    }
    const origin=request.get('origin');
    if(origin) {
      if(!origins.has(origin))return next(new PublicError('UNAUTHORIZED',401));
      response.setHeader('Access-Control-Allow-Origin',origin);
      response.setHeader('Access-Control-Allow-Methods','GET, POST, OPTIONS');
      response.setHeader('Access-Control-Allow-Headers','Authorization, Content-Type, Idempotency-Key, PAYMENT-SIGNATURE');
      response.setHeader('Access-Control-Expose-Headers','X-Request-ID, Location, Retry-After, PAYMENT-REQUIRED, PAYMENT-RESPONSE');
    }
    if(request.method==='OPTIONS'){response.status(204).end();return;}
    next();
  };
}
