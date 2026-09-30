import { readdir, readFile } from 'node:fs/promises';
import { Pool } from 'pg';
import { databaseUrl } from './config.js';
import { logEvent } from './security/observability.js';
import { APPROVED_MIGRATIONS,acquireMigrationLock,pendingMigrations,validateMigrationAuthority,verifyMigrationInventory,type MigrationIdentity } from './migration-policy.js';
async function migrate():Promise<void> {
  const pool=new Pool({connectionString:await databaseUrl(process.env),max:1,connectionTimeoutMillis:5000});
  const client=await pool.connect();
  let locked=false;let destroyed=false;
  try {
    await acquireMigrationLock(client,15_000,Date.now,undefined,()=>{destroyed=true;client.release(true);});locked=true;
    await client.query('CREATE TABLE IF NOT EXISTS gateway_migrations(name text PRIMARY KEY,sha256 text NOT NULL,applied_at timestamptz NOT NULL DEFAULT now())');
    const root=process.env.MIGRATION_SQL_ROOT??new URL('./migrations/',import.meta.url);
    const names=(await readdir(root)).filter(file=>/^\d{3}_[a-z_]+\.sql$/.test(file)).sort();
    const sqlByName=new Map<string,Buffer>();
    for(const name of names){sqlByName.set(name,await readFile(typeof root==='string'?`${root}/${name}`:new URL(name,root)));}
    let authority=APPROVED_MIGRATIONS;
    if(process.env.MIGRATION_MANIFEST_FILE){
      const manifest=JSON.parse(await readFile(process.env.MIGRATION_MANIFEST_FILE,'utf8')) as {migrations?:MigrationIdentity[]};
      if(!Array.isArray(manifest.migrations))throw new Error('MIGRATION_MISMATCH');
      authority=manifest.migrations;
    }
    validateMigrationAuthority(authority);
    const expected=verifyMigrationInventory(authority,sqlByName);
    const applied=(await client.query('SELECT name,sha256 FROM gateway_migrations ORDER BY name')).rows as MigrationIdentity[];
    for(const migration of pendingMigrations(expected,applied)) {
      const {name,sha256:sha}=migration;const bytes=sqlByName.get(name);if(bytes===undefined)throw new Error('MIGRATION_MISMATCH');const sql=bytes.toString('utf8');
      await client.query('BEGIN');
      try {
        await client.query("SET LOCAL lock_timeout='5s'");await client.query(sql);
        await client.query('INSERT INTO gateway_migrations(name,sha256) VALUES($1,$2)',[name,sha]);await client.query('COMMIT');
      }catch(error){await client.query('ROLLBACK');throw error;}
      logEvent({event:'MIGRATION_APPLIED',component:name});
    }
  }finally{if(locked)await client.query('SELECT pg_advisory_unlock(31611,1)');if(!destroyed)client.release();await pool.end();}
}
migrate().catch(()=>{logEvent({event:'MIGRATION_FAILED'});process.exitCode=1;});
