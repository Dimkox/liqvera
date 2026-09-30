import {createHash} from 'node:crypto';

export type MigrationIdentity={name:string;sha256:string};
export type LockClient={query:(sql:string,params?:unknown[])=>Promise<{rows:Array<Record<string,unknown>>}>};

export const APPROVED_MIGRATIONS:MigrationIdentity[]=[
  {name:'001_ledger.sql',sha256:'bc127e55c876961112f33ca2abdfac01827769d6156ddba2f42856d070c75b3b'},
  {name:'002_fix_immutable_ledger_identity.sql',sha256:'981f48215e64fdd0fb72be5a6df78238cf8050de722adb454b4e28b1940ccbcb'},
  {name:'003_live_grant_consumption.sql',sha256:'bbedff6137a648166b77233c56a466e46247480b404b8829b64f29123109bcf0'},
  {name:'004_receipt_confirmation_provenance.sql',sha256:'96bba00d344d81670a4c0f8741186004910e959f374ecd77ce78268d52fd465a'},
  {name:'005_receipt_confirmation_count.sql',sha256:'e99e5cffab60c08dfb1cd73d13caf2915f31aec542c26c87b016d0e125a23b11'},
];

export function validateMigrationAuthority(authority:MigrationIdentity[]):void{
  if(authority.length!==APPROVED_MIGRATIONS.length)throw new Error('MIGRATION_MISMATCH');
  for(let index=0;index<authority.length;index++){
    if(authority[index]?.name!==APPROVED_MIGRATIONS[index]?.name||authority[index]?.sha256!==APPROVED_MIGRATIONS[index]?.sha256)
      throw new Error('MIGRATION_MISMATCH');
  }
}

export function verifyMigrationInventory(authority:MigrationIdentity[],sqlByName:Map<string,Buffer>):MigrationIdentity[]{
  if(sqlByName.size!==authority.length)throw new Error('MIGRATION_MISMATCH');
  for(const migration of authority){
    const sql=sqlByName.get(migration.name);
    if(!sql||createHash('sha256').update(sql).digest('hex')!==migration.sha256)throw new Error('MIGRATION_MISMATCH');
  }
  return authority;
}

export function pendingMigrations(expected:MigrationIdentity[],applied:MigrationIdentity[]):MigrationIdentity[]{
  if(new Set(applied.map(row=>row.name)).size!==applied.length||applied.length>expected.length)
    throw new Error('MIGRATION_MISMATCH');
  for(let index=0;index<applied.length;index++){
    if(applied[index]?.name!==expected[index]?.name||applied[index]?.sha256!==expected[index]?.sha256)
      throw new Error('MIGRATION_MISMATCH');
  }
  return expected.slice(applied.length);
}

export async function acquireMigrationLock(
  client:LockClient,timeoutMs=15_000,now:()=>number=Date.now,
  pause:(milliseconds:number)=>Promise<void>=(milliseconds)=>new Promise(resolve=>setTimeout(resolve,milliseconds)),
  destroy:()=>void=()=>{},
):Promise<void>{
  const deadline=now()+timeoutMs;
  while(now()<deadline){
    const remaining=Math.max(1,deadline-now());
    let timer:ReturnType<typeof setTimeout>|undefined;
    const timeout=new Promise<never>((_,reject)=>{timer=setTimeout(()=>{destroy();reject(new Error('MIGRATION_LOCK_TIMEOUT'));},remaining);});
    let result:{rows:Array<Record<string,unknown>>};
    try{result=await Promise.race([client.query('SELECT pg_try_advisory_lock(31611,1) AS acquired'),timeout]);}
    finally{if(timer!==undefined)clearTimeout(timer);}
    if(now()>=deadline){destroy();throw new Error('MIGRATION_LOCK_TIMEOUT');}
    if(result.rows[0]?.acquired===true)return;
    await pause(Math.min(250,Math.max(0,deadline-now())));
  }
  throw new Error('MIGRATION_LOCK_TIMEOUT');
}
