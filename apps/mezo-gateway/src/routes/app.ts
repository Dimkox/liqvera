import express, { type ErrorRequestHandler, type Request, type RequestHandler, type Response } from 'express';
import { Gateway, type ApiResult } from '../application/gateway.js';
import { errorResource } from '../application/presenters.js';
import { PublicError, uuidPattern } from '../domain/model.js';
import { capability, decodeQuoteBody, idempotencyKey } from '../security/input.js';
import { securityHeaders } from '../security/middleware.js';
import { metrics } from '../security/observability.js';
export function createApp(gateway:Gateway,origins:ReadonlySet<string>) {
  const app=express();app.disable('x-powered-by');app.disable('etag');app.set('trust proxy',false);
  app.use(securityHeaders(origins));
  app.use((request,_response,next)=>{
    // Express otherwise routes HEAD through GET, which could submit payment.
    if(!['GET','POST'].includes(request.method)){next(new PublicError('NOT_FOUND',404));return;}next();
  });
  function send(response:Response,result:ApiResult):void {
    if(result.shape)gateway.contracts.assert(result.shape,result.body);
    response.status(result.status);
    for(const [name,value] of Object.entries(result.headers??{}))response.setHeader(name,value);
    if(result.bytes)response.end(result.bytes);else response.json(result.body);
  }
  const route=(handler:(request:Request,response:Response)=>Promise<ApiResult>):RequestHandler=>
    (request,response,next)=>{void handler(request,response).then(result=>send(response,result)).catch(next);};
  const readBudget:RequestHandler=(request,_response,next)=>{
    // Forwarded headers are never a client-controlled budget reset. Reverse
    // proxies share their socket IP budget; deployment may set larger ceilings.
    void gateway.ledger.rateLimit(`read-ip:${request.socket.remoteAddress??'unknown'}`,300).then(()=>next()).catch(next);
  };
  const scoped:RequestHandler=(request,response,next)=>{
    try {response.locals.scope=capability(request.get('authorization'));next();}catch(error){next(error);}
  };
  const id=(request:Request,name:string):string=>{
    const value=request.params[name];if(typeof value!=='string'||value.length!==36||!uuidPattern.test(value))throw new PublicError('NOT_FOUND',404);return value;
  };
  app.get('/healthz',route(async(_request,response)=>({status:200,shape:'health',body:{schema:'mee-evidence-health/v1',request_id:response.locals.requestId,status:'alive'}})));
  app.get('/readyz',route(async(_request,response)=>gateway.readiness(response.locals.requestId)));
  app.get('/v1/capabilities',readBudget,route(async(_request,response)=>gateway.capabilities(response.locals.requestId)));
  app.post('/v1/report-quotes',scoped,readBudget,express.raw({type:'application/json',limit:16384,inflate:false}),route(async(request,response)=>{
    if(!Buffer.isBuffer(request.body))throw new PublicError('INVALID_INPUT',422);
    let body;
    try{body=decodeQuoteBody(request.body);}catch(error){throw error instanceof PublicError?error:new PublicError('INVALID_INPUT',422);}
    await gateway.ledger.rateLimit('quote-global',60);
    await gateway.ledger.rateLimit(`quote-ip:${request.socket.remoteAddress??'unknown'}`,20);
    return gateway.create(response.locals.scope,idempotencyKey(request.get('idempotency-key')),body,response.locals.requestId);
  }));
  app.get('/v1/report-requests/:report_request_id',scoped,readBudget,route(async(request,response)=>gateway.status(response.locals.scope,id(request,'report_request_id'),response.locals.requestId)));
  app.get('/v1/report-quotes/:quote_id',scoped,readBudget,route(async(request,response)=>gateway.quote(response.locals.scope,id(request,'quote_id'),response.locals.requestId)));
  app.get('/v1/reports/:report_id',scoped,readBudget,route(async(request,response)=>gateway.read(response.locals.scope,id(request,'report_id'),'report',request.get('payment-signature'),response.locals.requestId)));
  app.get('/v1/reports/:report_id/evidence',scoped,readBudget,route(async(request,response)=>gateway.read(response.locals.scope,id(request,'report_id'),'bundle',undefined,response.locals.requestId)));
  app.use((_request,_response,next)=>next(new PublicError('NOT_FOUND',404)));
  const errors:ErrorRequestHandler=(error,_request,response,_next)=>{
    if(response.headersSent){response.destroy();return;}
    const failure=error instanceof PublicError?error: new PublicError(
      error?.type==='entity.too.large'||error?.type==='encoding.unsupported'?'INVALID_INPUT':'STORAGE_UNAVAILABLE',
      error?.type==='entity.too.large'||error?.type==='encoding.unsupported'?422:503);
    if(failure.code==='RATE_LIMITED')response.setHeader('Retry-After','60');
    if(failure.code==='ARTIFACT_INTEGRITY_FAILURE')metrics.increment('artifact_integrity_failure');
    if(failure.code==='AUTHORIZATION_REUSED')metrics.increment('authorization_duplicate');
    if(failure.code==='PAYMENT_UNCERTAIN')metrics.increment('payment_unknown');
    response.status(failure.status).json(errorResource(failure.code,response.locals.requestId));
  };
  app.use(errors);return app;
}
