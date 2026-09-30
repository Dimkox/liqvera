import assert from 'node:assert/strict';
import test from 'node:test';
import {acquireMigrationLock,pendingMigrations,type MigrationIdentity} from '../src/migration-policy.js';

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
