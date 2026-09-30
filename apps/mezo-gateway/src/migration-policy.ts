export type MigrationIdentity={name:string;sha256:string};
export type LockClient={query:(sql:string,params?:unknown[])=>Promise<{rows:Array<Record<string,unknown>>}>};

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
):Promise<void>{
  const deadline=now()+timeoutMs;
  while(now()<deadline){
    const result=await client.query('SELECT pg_try_advisory_lock(31611,1) AS acquired');
    if(result.rows[0]?.acquired===true)return;
    await pause(Math.min(250,Math.max(0,deadline-now())));
  }
  throw new Error('MIGRATION_LOCK_TIMEOUT');
}
