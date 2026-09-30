import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import test from 'node:test';
import {APPROVED_MIGRATIONS,acquireMigrationLock,pendingMigrations,validateMigrationAuthority,verifyMigrationInventory,type MigrationIdentity} from '../src/migration-policy.js';

const expected:MigrationIdentity[]=[1,2,3,4,5].map(index=>({name:`00${index}_m.sql`,sha256:String(index).repeat(64)}));

test('migration ledger accepts only exact prefixes and retries forward',()=>{
  for(let length=0;length<=expected.length;length++)assert.deepEqual(pendingMigrations(expected,expected.slice(0,length)),expected.slice(length));
  for(const applied of [[expected[1]!],[{...expected[0]!,sha256:'0'.repeat(64)}],[...expected,{name:'006_x.sql',sha256:'6'.repeat(64)}],[expected[0]!,expected[0]!]])
    assert.throws(()=>pendingMigrations(expected,applied),/MIGRATION_MISMATCH/);
});

test('migration lock is nonblocking and bounded',async()=>{
  let attempts=0;let time=0;
  const client={query:async()=>({rows:[{acquired:++attempts===3}]})};
  await acquireMigrationLock(client,1_000,()=>time,async milliseconds=>{time+=milliseconds;});
  assert.equal(attempts,3);
  time=0;
  await assert.rejects(()=>acquireMigrationLock({query:async()=>({rows:[{acquired:false}]})},10,()=>time,async milliseconds=>{time+=milliseconds;}),/MIGRATION_LOCK_TIMEOUT/);
});

test('migration lock destroys a stalled query at the total deadline',async()=>{
  let destroyed=0;
  await assert.rejects(()=>acquireMigrationLock(
    {query:()=>new Promise(()=>{})},10,Date.now,async()=>{},()=>{destroyed++;}
  ),/MIGRATION_LOCK_TIMEOUT/);
  assert.equal(destroyed,1);
});

test('verified manifest is sole authority for exact embedded migration inventory',()=>{
  const sql=new Map(expected.map(row=>[row.name,Buffer.from(row.name)]));
  const manifest=expected.map(row=>({...row,sha256:createHash('sha256').update(sql.get(row.name)!).digest('hex')}));
  assert.deepEqual(verifyMigrationInventory(manifest,sql),manifest);
  const extra=new Map(sql);extra.set('006_extra.sql',Buffer.from('no'));
  assert.throws(()=>verifyMigrationInventory(manifest,extra),/MIGRATION_MISMATCH/);
  const missing=new Map(sql);missing.delete(expected[0]!.name);
  assert.throws(()=>verifyMigrationInventory(manifest,missing),/MIGRATION_MISMATCH/);
  const changed=new Map(sql);changed.set(expected[0]!.name,Buffer.from('changed'));
  assert.throws(()=>verifyMigrationInventory(manifest,changed),/MIGRATION_MISMATCH/);
  assert.doesNotThrow(()=>validateMigrationAuthority(APPROVED_MIGRATIONS));
  assert.throws(()=>validateMigrationAuthority([...APPROVED_MIGRATIONS,{name:'006_extra.sql',sha256:'0'.repeat(64)}]),/MIGRATION_MISMATCH/);
  assert.throws(()=>validateMigrationAuthority(APPROVED_MIGRATIONS.map((row,index)=>index?row:{...row,sha256:'0'.repeat(64)})),/MIGRATION_MISMATCH/);
});
