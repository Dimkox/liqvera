import { readFile } from 'node:fs/promises';
import { address, PublicError } from './domain/model.js';
import { fixedInternalUrl } from './adapters/http.js';
export async function databaseUrl(env:NodeJS.ProcessEnv):Promise<string> {
  if(env.DATABASE_URL&&env.DATABASE_URL_FILE)throw new PublicError('INVALID_INPUT');
  const value=env.DATABASE_URL_FILE?(await readFile(env.DATABASE_URL_FILE,'utf8')).trim():env.DATABASE_URL;
  if(!value||!/^postgres(?:ql)?:\/\//.test(value))throw new PublicError('STORAGE_UNAVAILABLE');return value;
}
export async function loadConfig(env:NodeJS.ProcessEnv=process.env) {
  const sourceMode=env.SOURCE_MODE??'fixture';if(sourceMode!=='fixture'&&sourceMode!=='live-public')throw new PublicError('INVALID_INPUT');
  const publicBase=new URL(env.PUBLIC_BASE_URL??'http://localhost:8080');
  if(publicBase.username||publicBase.password||publicBase.search||publicBase.hash||publicBase.pathname!=='/'||
    (publicBase.protocol!=='https:'&&!(publicBase.protocol==='http:'&&['localhost','127.0.0.1'].includes(publicBase.hostname))))throw new PublicError('INVALID_INPUT');
  const origins=new Set((env.CORS_ORIGINS??publicBase.origin).split(',').map(value=>value.trim()));
  for(const value of origins) {
    const url=new URL(value);if(url.origin!==value||url.username||url.password||!['http:','https:'].includes(url.protocol))throw new PublicError('INVALID_INPUT');
  }
  const port=Number(env.PORT??'8080');if(!Number.isInteger(port)||port<1||port>65535)throw new PublicError('INVALID_INPUT');
  const reportToken=env.REPORT_SERVICE_TOKEN_FILE?(await readFile(env.REPORT_SERVICE_TOKEN_FILE,'utf8')).trim():null;
  if(reportToken!==null&&(!/^[A-Za-z0-9_-]{32,256}$/.test(reportToken)))throw new PublicError('INVALID_INPUT');
  return {databaseUrl:await databaseUrl(env),sourceMode,payTo:env.PAY_TO?address(env.PAY_TO):null,publicBase,origins,port,
    host:env.HOST??'0.0.0.0',artifactRoot:env.ARTIFACT_ROOT??'/data/artifacts',reportToken,
    reportUrl:fixedInternalUrl(env.REPORT_SERVICE_URL??'http://report:8082')};
}
