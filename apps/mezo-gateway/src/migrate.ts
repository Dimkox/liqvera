import { createHash } from 'node:crypto';
import { readdir, readFile } from 'node:fs/promises';
import { Pool } from 'pg';
import { databaseUrl } from './config.js';
import { logEvent } from './security/observability.js';
import { acquireMigrationLock,pendingMigrations,type MigrationIdentity } from './migration-policy.js';
async function migrate():Promise<void> {
  const pool=new Pool({connectionString:await databaseUrl(process.env),max:1,connectionTimeoutMillis:5000});
  const client=await pool.connect();
  let locked=false;
  try {
    await acquireMigrationLock(client);locked=true;
    await client.query('CREATE TABLE IF NOT EXISTS gateway_migrations(name text PRIMARY KEY,sha256 text NOT NULL,applied_at timestamptz NOT NULL DEFAULT now())');
    const root=new URL('./migrations/',import.meta.url);
    const names=(await readdir(root)).filter(file=>/^\d{3}_[a-z_]+\.sql$/.test(file)).sort();
    const expected:MigrationIdentity[]=[];const sqlByName=new Map<string,string>();
    for(const name of names){const sql=await readFile(new URL(name,root),'utf8');sqlByName.set(name,sql);expected.push({name,sha256:createHash('sha256').update(sql).digest('hex')});}
    const applied=(await client.query('SELECT name,sha256 FROM gateway_migrations ORDER BY name')).rows as MigrationIdentity[];
    for(const migration of pendingMigrations(expected,applied)) {
      const {name,sha256:sha}=migration;const sql=sqlByName.get(name);if(sql===undefined)throw new Error('MIGRATION_MISMATCH');
      await client.query('BEGIN');
      try {
        await client.query("SET LOCAL lock_timeout='5s'");await client.query(sql);
        await client.query('INSERT INTO gateway_migrations(name,sha256) VALUES($1,$2)',[name,sha]);await client.query('COMMIT');
      }catch(error){await client.query('ROLLBACK');throw error;}
      logEvent({event:'MIGRATION_APPLIED',component:name});
    }
  }finally{if(locked)await client.query('SELECT pg_advisory_unlock(31611,1)');client.release();await pool.end();}
}
migrate().catch(()=>{logEvent({event:'MIGRATION_FAILED'});process.exitCode=1;});
