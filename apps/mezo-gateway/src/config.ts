import { readFile } from 'node:fs/promises';
import { address, PublicError } from './domain/model.js';
import { fixedInternalUrl } from './adapters/http.js';
import type { GatewayConfig } from './application/gateway.js';
export interface RuntimeConfig extends GatewayConfig {
  databaseUrl: string;
  publicBase: URL;
  origins: Set<string>;
  port: number;
  host: string;
  artifactRoot: string;
  reportToken: string | null;
  reportUrl: URL;
  metricsHost: string;
  metricsPort: number;
  liveGrantFile: string|null;
  testnetDemoAnyPayer: boolean;
  liveContext: {subjectCommit:string;subjectTree:string;planSha256:string;buyer:string;payTo:string}|null;
}
export async function databaseUrl(env:NodeJS.ProcessEnv):Promise<string> {
  if(env.DATABASE_URL&&env.DATABASE_URL_FILE)throw new PublicError('INVALID_INPUT');
  const value=env.DATABASE_URL_FILE?(await readFile(env.DATABASE_URL_FILE,'utf8')).trim():env.DATABASE_URL;
  if(!value||!/^postgres(?:ql)?:\/\//.test(value))throw new PublicError('STORAGE_UNAVAILABLE');return value;
}
export async function loadConfig(env:NodeJS.ProcessEnv=process.env):Promise<RuntimeConfig> {
  const sourceMode=env.SOURCE_MODE??'fixture';if(sourceMode!=='fixture'&&sourceMode!=='live-public')throw new PublicError('INVALID_INPUT');
  const publicBase=new URL(env.PUBLIC_BASE_URL??'http://localhost:8080');
  if(publicBase.username||publicBase.password||publicBase.search||publicBase.hash||publicBase.pathname!=='/'||
    (publicBase.protocol!=='https:'&&!(publicBase.protocol==='http:'&&['localhost','127.0.0.1'].includes(publicBase.hostname))))throw new PublicError('INVALID_INPUT');
  const origins=new Set((env.CORS_ORIGINS??publicBase.origin).split(',').map(value=>value.trim()));
  for(const value of origins) {
    const url=new URL(value);if(url.origin!==value||url.username||url.password||!['http:','https:'].includes(url.protocol))throw new PublicError('INVALID_INPUT');
  }
  const port=Number(env.PORT??'8080');if(!Number.isInteger(port)||port<1||port>65535)throw new PublicError('INVALID_INPUT');
  const metricsHost=env.METRICS_HOST??'127.0.0.1';
  if(!['127.0.0.1','gateway-metrics'].includes(metricsHost))throw new PublicError('INVALID_INPUT');
  const metricsPort=Number(env.METRICS_PORT??'9090');
  if(!Number.isInteger(metricsPort)||metricsPort<1||metricsPort>65535||metricsPort===port)throw new PublicError('INVALID_INPUT');
  const reportToken=env.REPORT_SERVICE_TOKEN_FILE?(await readFile(env.REPORT_SERVICE_TOKEN_FILE,'utf8')).trim():null;
  if(reportToken!==null&&(!/^[A-Za-z0-9_-]{32,256}$/.test(reportToken)))throw new PublicError('INVALID_INPUT');
  const payTo=env.PAY_TO?address(env.PAY_TO):null;
  const liveGrantFile=env.LIQVERA_LIVE_GRANT_FILE??null;
  let liveContext:RuntimeConfig['liveContext']=null;
  if(liveGrantFile) {
    if(sourceMode!=='live-public'||!payTo||!env.LIQVERA_SUBJECT_COMMIT||!env.LIQVERA_SUBJECT_TREE||!env.LIQVERA_PLAN_SHA256||!env.LIQVERA_LIVE_BUYER)throw new PublicError('INVALID_INPUT');
    if(!/^[0-9a-f]{40}$/.test(env.LIQVERA_SUBJECT_COMMIT)||!/^[0-9a-f]{40}$/.test(env.LIQVERA_SUBJECT_TREE)||!/^[0-9a-f]{64}$/.test(env.LIQVERA_PLAN_SHA256))throw new PublicError('INVALID_INPUT');
    liveContext={subjectCommit:env.LIQVERA_SUBJECT_COMMIT,subjectTree:env.LIQVERA_SUBJECT_TREE,planSha256:env.LIQVERA_PLAN_SHA256,buyer:address(env.LIQVERA_LIVE_BUYER),payTo};
  }
  const testnetDemoAnyPayer=env.LIQVERA_TESTNET_DEMO_ANY_PAYER==='1';
  if(env.LIQVERA_TESTNET_DEMO_ANY_PAYER!==undefined&&!['0','1'].includes(env.LIQVERA_TESTNET_DEMO_ANY_PAYER))throw new PublicError('INVALID_INPUT');
  if(testnetDemoAnyPayer&&(!liveGrantFile||sourceMode!=='live-public'))throw new PublicError('INVALID_INPUT');
  return {databaseUrl:await databaseUrl(env),sourceMode,payTo,publicBase,origins,port,liveGrantFile,liveContext,testnetDemoAnyPayer,
    host:env.HOST??'0.0.0.0',artifactRoot:env.ARTIFACT_ROOT??'/data/artifacts',reportToken,metricsHost,metricsPort,
    reportUrl:fixedInternalUrl(env.REPORT_SERVICE_URL??'http://report:8082')};
}
