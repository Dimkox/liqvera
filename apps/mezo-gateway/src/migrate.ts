import { createHash } from 'node:crypto';
import { readdir, readFile } from 'node:fs/promises';
import { Pool } from 'pg';
import { databaseUrl } from './config.js';
import { logEvent } from './security/observability.js';
async function migrate():Promise<void> {
  const pool=new Pool({connectionString:await databaseUrl(process.env),max:1,connectionTimeoutMillis:5000});
  const client=await pool.connect();
  try {
    await client.query('SELECT pg_advisory_lock(31611,1)');
    await client.query('CREATE TABLE IF NOT EXISTS gateway_migrations(name text PRIMARY KEY,sha256 text NOT NULL,applied_at timestamptz NOT NULL DEFAULT now())');
    const root=new URL('./migrations/',import.meta.url);
    for(const name of (await readdir(root)).filter(file=>/^\d{3}_[a-z_]+\.sql$/.test(file)).sort()) {
      const sql=await readFile(new URL(name,root),'utf8');const sha=createHash('sha256').update(sql).digest('hex');
      const existing=(await client.query('SELECT sha256 FROM gateway_migrations WHERE name=$1',[name])).rows[0];
      if(existing) {if(existing.sha256!==sha)throw new Error('Migration checksum mismatch');continue;}
      await client.query('BEGIN');
      try {
        await client.query("SET LOCAL lock_timeout='5s'");await client.query(sql);
        await client.query('INSERT INTO gateway_migrations(name,sha256) VALUES($1,$2)',[name,sha]);await client.query('COMMIT');
      }catch(error){await client.query('ROLLBACK');throw error;}
      logEvent({event:'MIGRATION_APPLIED',component:name});
    }
  }finally{await client.query('SELECT pg_advisory_unlock(31611,1)');client.release();await pool.end();}
}
migrate().catch(()=>{logEvent({event:'MIGRATION_FAILED'});process.exitCode=1;});
