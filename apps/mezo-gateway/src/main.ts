import { createServer } from 'node:http';
import { Pool } from 'pg';
import { loadConfig } from './config.js';
import { Ledger } from './adapters/postgres.js';
import { Contracts } from './adapters/contracts.js';
import { HttpReportService } from './adapters/report-service.js';
import { ImmutableArtifacts } from './adapters/artifacts.js';
import { OfficialX402, unresolvedIdentity, unresolvedFinality } from './adapters/x402.js';
import { MezoReadonlyRpc, MezoReceiptReader } from './adapters/mezo-rpc.js';
import { Gateway } from './application/gateway.js';
import { createApp } from './routes/app.js';
import { startWorkers } from './workers/scheduler.js';
import { logEvent, metrics } from './security/observability.js';
async function main():Promise<void> {
  const config=await loadConfig();
  const pool=new Pool({connectionString:config.databaseUrl,max:12,connectionTimeoutMillis:3000,idleTimeoutMillis:30000,
    application_name:'mee-mezo-gateway',statement_timeout:5000});
  pool.on('error',()=>logEvent({event:'DATABASE_UNAVAILABLE'}));
  const contracts=await Contracts.load(new URL('./contracts/',import.meta.url));
  const reader=new MezoReceiptReader(new MezoReadonlyRpc(),unresolvedIdentity,unresolvedFinality);
  const payments=new OfficialX402(unresolvedIdentity,unresolvedFinality,reader,config.publicBase);
  // No startup facilitator call or environment-controlled authorization bypass.
  // Reviewed concrete policies and controlled integration verification must be
  // installed here before initialize() can establish payment readiness.
  const gateway=new Gateway(new Ledger(pool),new HttpReportService(config.reportUrl,config.reportToken),new ImmutableArtifacts(config.artifactRoot),payments,contracts,config);
  const server=createServer({maxHeaderSize:32768,requestTimeout:20000,headersTimeout:10000},createApp(gateway,config.origins));
  server.keepAliveTimeout=5000;server.maxRequestsPerSocket=100;
  const stopWorkers=startWorkers(gateway);
  const telemetry=createServer((_req,res)=>{res.writeHead(200,{'Content-Type':'text/plain; version=0.0.4','Cache-Control':'no-store'});res.end(metrics.render());});
  telemetry.listen(9090,'127.0.0.1');
  server.listen(config.port,config.host,()=>logEvent({event:'GATEWAY_STARTED'}));
  let shuttingDown=false;
  const shutdown=async()=>{
    if(shuttingDown)return;shuttingDown=true;
    const deadline=setTimeout(()=>process.exit(1),20000);deadline.unref();
    await Promise.all([stopWorkers(),new Promise<void>(resolve=>server.close(()=>resolve())),new Promise<void>(resolve=>telemetry.close(()=>resolve()))]);
    await pool.end();clearTimeout(deadline);logEvent({event:'GATEWAY_STOPPED'});
  };
  process.once('SIGTERM',()=>void shutdown());process.once('SIGINT',()=>void shutdown());
}
main().catch(()=>{logEvent({event:'STARTUP_FAILED'});process.exitCode=1;});
