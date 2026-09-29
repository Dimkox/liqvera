import { readFile, open, lstat } from 'node:fs/promises';
import { constants } from 'node:fs';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { lookup } from 'node:dns/promises';
import { isIP } from 'node:net';
import { Pool } from 'pg';
import { Ledger } from './adapters/postgres.js';
import { MezoReceiptReader, MezoReadonlyRpc } from './adapters/mezo-rpc.js';
import { OfficialX402 } from './adapters/x402.js';
import { MezoAuthorizationPolicy, MezoFinalityPolicy } from './security/payment-policy.js';
import { LivePaymentGrant } from './security/live-grant.js';
import type { Attempt } from './domain/model.js';

const migrations=new Map([
  ['001_ledger.sql','bc127e55c876961112f33ca2abdfac01827769d6156ddba2f42856d070c75b3b'],
  ['002_fix_immutable_ledger_identity.sql','981f48215e64fdd0fb72be5a6df78238cf8050de722adb454b4e28b1940ccbcb'],
  ['003_live_grant_consumption.sql','bbedff6137a648166b77233c56a466e46247480b404b8829b64f29123109bcf0'],
  ['004_receipt_confirmation_provenance.sql','96bba00d344d81670a4c0f8741186004910e959f374ecd77ce78268d52fd465a'],
  ['005_receipt_confirmation_count.sql','e99e5cffab60c08dfb1cd73d13caf2915f31aec542c26c87b016d0e125a23b11'],
]);
const fields=['schema','quote_id','scope_hash','report_id','payment_signature','buyer','pay_to'];
const planDigest='5582f45572493c1b1f0daba2ac6b8046e2fa87ae63da99e17ac3d040e0cac671';
function fail(message:string):never{throw new Error(message);}
function exactObject(value:unknown):Record<string,unknown>{if(!value||typeof value!=='object'||Array.isArray(value))fail('P3_INPUT_INVALID');return value as Record<string,unknown>}
function arg(name:string):string {const at=process.argv.indexOf(name);if(at<0||!process.argv[at+1])fail(`missing ${name}`);return process.argv[at+1]!}
function safeUrl(value:string):URL {const url=new URL(value);if(url.protocol!=='https:'||url.username||url.password||url.search||url.hash)fail('P3_URL_INVALID');return url}
async function bytes(path:string,max=65536):Promise<Uint8Array>{
  const before=await lstat(path);if(!before.isFile()||before.nlink!==1||(before.mode&0o077)!==0||before.size<1||before.size>max)fail('P3_INPUT_UNSAFE');
  const handle=await open(path,constants.O_RDONLY|constants.O_NOFOLLOW);
  try {const opened=await handle.stat();if(opened.dev!==before.dev||opened.ino!==before.ino||opened.size!==before.size)fail('P3_INPUT_UNSAFE');const value=await handle.readFile();if(!value.length||value.length>max)fail('P3_INPUT_INVALID');return value;}
  finally {await handle.close();}
}
type Resolver=(hostname:string)=>Promise<{address:string}[]>;
const systemResolver:Resolver=async hostname=>await lookup(hostname,{all:true,verbatim:true});
function loopback(value:string):boolean {const normalized=value.toLowerCase();return normalized==='127.0.0.1'||normalized==='::1';}
export async function databaseIdentity(value:string,resolver:Resolver=systemResolver):Promise<string> {
  const url=new URL(value);const host=url.hostname.replace(/^\[|\]$/g,'').toLowerCase();
  if(!/^postgres(?:ql)?:$/.test(url.protocol)||!host||!url.pathname.slice(1)||url.search||url.hash)fail('P3_DATABASE_CONFIG_INVALID');
  if(isIP(host)){if(!loopback(host))fail('P3_DATABASE_HOST_NOT_LOOPBACK');}
  else if(host==='localhost') {const resolved=await resolver(host);if(!resolved.length||resolved.some(item=>!loopback(item.address)))fail('P3_DATABASE_HOST_NOT_LOOPBACK');}
  else fail('P3_DATABASE_HOST_NOT_LOOPBACK');
  const endpoint=`${url.protocol}//${host}:${url.port||'5432'}${url.pathname}`;return createHash('sha256').update(endpoint).digest('hex');
}
async function checkMigrations(pool:Pool):Promise<void>{
  const rows=(await pool.query<{name:string;sha256:string}>('SELECT name,sha256 FROM gateway_migrations ORDER BY name')).rows;
  if(rows.length!==migrations.size||rows.some(row=>migrations.get(row.name)!==row.sha256))fail('P3_MIGRATION_MISMATCH');
}
function output(value:unknown):void{process.stdout.write(`${JSON.stringify(value)}\n`)}

async function main():Promise<void>{
  const grantPath=arg('--grant'); const paymentPath=arg('--payment');
  const expectedGrantDigest=arg('--grant-sha256'); const expectedPaymentDigest=arg('--payment-sha256');
  const subjectCommit=arg('--subject-commit'); const subjectTree=arg('--subject-tree'); const planSha256=arg('--plan-sha256');
  const rawGrantBytes=await bytes(grantPath);const rawPaymentBytes=await bytes(paymentPath,16384);
  if(createHash('sha256').update(rawGrantBytes).digest('hex')!==expectedGrantDigest||createHash('sha256').update(rawPaymentBytes).digest('hex')!==expectedPaymentDigest)fail('P3_SNAPSHOT_DIGEST_MISMATCH');
  const rawBundle=exactObject(JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(rawGrantBytes)));
  if(Object.keys(rawBundle).sort().join()!==['cases','expires_at','plan_sha256','schema','subject_commit','subject_tree'].sort().join()||
    rawBundle.schema!=='liqvera-p3-payment-grants/v1'||rawBundle.subject_commit!==subjectCommit||rawBundle.subject_tree!==subjectTree||rawBundle.plan_sha256!==planSha256||planSha256!==planDigest)fail('LIVE_GRANT_MISMATCH');
  const cases=exactObject(rawBundle.cases); const grantRaw=exactObject(cases.A13);
  if(Object.keys(cases).sort().join()!=='A13,A14')fail('LIVE_GRANT_INVALID');
  if(JSON.stringify(cases.A13)!==JSON.stringify(cases.A14))fail('LIVE_PAYMENT_LINK_MISMATCH');
  const grantBytes=new TextEncoder().encode(JSON.stringify(grantRaw,Object.keys(grantRaw).sort()));
  const grant=LivePaymentGrant.parseBytes(grantBytes,new Date());
  const payment=exactObject(JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(rawPaymentBytes)));
  if(Object.keys(payment).sort().join()!==[...fields].sort().join()||payment.schema!=='liqvera-p3-signed-payment/v1'||payment.buyer!==grant.raw.buyer||payment.pay_to!==grant.raw.pay_to)fail('P3_PAYMENT_INPUT_INVALID');
  grant.authorize({subjectCommit,subjectTree,planSha256,buyer:String(payment.buyer),payTo:String(payment.pay_to),now:new Date()});
  const root=resolve(dirname(fileURLToPath(import.meta.url)),'../../..');
  const git=(...args:string[])=>execFileSync('git',['-C',root,...args],{encoding:'utf8'}).trim();
  if(git('rev-parse','HEAD')!==subjectCommit||git('rev-parse','HEAD^{tree}')!==subjectTree||git('status','--porcelain','--untracked-files=all'))fail('P3_SUBJECT_MISMATCH');
  if(process.argv.includes('--preflight')){
    output({schema:'liqvera-p3-preflight/v1',subject_commit:subjectCommit,subject_tree:subjectTree,plan_sha256:planSha256,
      grant_id:grant.raw.grant_id,grant_digest:grant.digest,buyer:payment.buyer,pay_to:payment.pay_to,network:grant.raw.network,
      asset:grant.raw.asset,amount_atomic:grant.raw.amount_atomic,maximum_settlement_submissions:1,max_buyer_native_gas_wei:grant.raw.max_buyer_native_gas_wei,
      required_migrations:Object.fromEntries(migrations),external_calls:0,database_writes:0});return;
  }
  const databaseUrl=process.env.DATABASE_URL_FILE?new TextDecoder('utf-8',{fatal:true}).decode(await bytes(process.env.DATABASE_URL_FILE,4096)).trim():process.env.DATABASE_URL;
  if(!databaseUrl||!/^postgres(?:ql)?:\/\//.test(databaseUrl)||Boolean(process.env.DATABASE_URL_FILE)===Boolean(process.env.DATABASE_URL))fail('P3_DATABASE_CONFIG_INVALID');
  const facilitator=safeUrl(arg('--facilitator-url')); const rpcUrl=safeUrl(arg('--rpc-url'));
  if(facilitator.href!==grant.raw.facilitator_url||rpcUrl.href!==grant.raw.rpc_url||await databaseIdentity(databaseUrl)!==grant.raw.database_identity)fail('P3_EXTERNAL_IDENTITY_MISMATCH');
  const pool=new Pool({connectionString:databaseUrl,max:2,connectionTimeoutMillis:5000});
  try {
    await checkMigrations(pool); // No facilitator/RPC call is possible before this point.
    const ledger=new Ledger(pool); const quote=await ledger.quote(String(payment.scope_hash),String(payment.quote_id));
    if(quote.report_id!==payment.report_id||quote.terms.expected_payer!==payment.buyer||quote.terms.pay_to!==payment.pay_to)fail('P3_PAYMENT_INPUT_MISMATCH');
    const identity=new MezoAuthorizationPolicy(); const finality=new MezoFinalityPolicy(12);
    const reader=new MezoReceiptReader(new MezoReadonlyRpc(rpcUrl),identity,finality);
    const port=new OfficialX402(identity,finality,reader,new URL('https://liqvera.invalid'),grant,
      {subjectCommit,subjectTree,planSha256,buyer:String(payment.buyer),payTo:String(payment.pay_to)},()=>new Date(),facilitator);
    const consumed=(await pool.query<{payment_attempt_id:string}>(`SELECT payment_attempt_id FROM live_grant_consumptions WHERE grant_digest=$1`,[grant.digest])).rows[0];
    let attempt:Attempt;
    if(consumed){attempt=(await pool.query<Attempt>('SELECT * FROM payment_attempts WHERE id=$1',[consumed.payment_attempt_id])).rows[0]??fail('P3_ATTEMPT_MISSING');}
    else {
      await port.initialize(); const verified=await port.verify(String(payment.payment_signature),quote);
      attempt=await ledger.beginAttempt(quote,verified.identity);
      if(!await ledger.markSubmitting(attempt))fail('P3_GRANT_ALREADY_CONSUMED');
      let tx:string|null=null;
      try {tx=(await port.settle(verified.payload,verified.requirements)).tx_hash;} finally {await ledger.unknown(attempt,tx);}
      attempt={...attempt,state:'UNKNOWN',tx_hash:tx};
    }
    if(attempt.state==='CONFIRMED'){
      const retained=await ledger.confirmation(quote);if(!retained)fail('P3_RECEIPT_MISSING');
      output({...retained.confirmation.receipt,schema:'liqvera-p3-payment-observation/v1',status:'CONFIRMED',grant_id:grant.raw.grant_id,grant_digest:grant.digest,settlement_count:1,retry_allowed:false});return;
    }
    const confirmation=await port.confirm(quote,attempt);
    if(!confirmation){output({schema:'liqvera-p3-payment-observation/v1',status:'UNKNOWN',grant_id:grant.raw.grant_id,grant_digest:grant.digest,tx_hash:attempt.tx_hash,settlement_count:1,retry_allowed:false});return;}
    await ledger.confirm(quote,attempt,confirmation);
    output({...confirmation.receipt,schema:'liqvera-p3-payment-observation/v1',status:'CONFIRMED',grant_id:grant.raw.grant_id,grant_digest:grant.digest,settlement_count:1,retry_allowed:false});
  } finally {await pool.end();}
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url))
  main().catch(error=>{process.stderr.write(`${error instanceof Error?error.message:'P3_OPERATOR_FAILED'}\n`);process.exitCode=1});
