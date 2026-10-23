import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import test from 'node:test';
import {Contracts} from '../src/adapters/contracts.js';
import {capabilitiesResource} from '../src/application/presenters.js';
const borrower='0xDA04759E54728B6636Fe48F7c9795c7B609bAaAa';
const preview={product_id:'trove_risk',borrower,trove_status:'ACTIVE',snapshot_at:'2026-10-23T18:02:00Z',
 snapshot_status:'VALID_FOR_SNAPSHOT_CALCULATION',limitations:['Testnet, read only.'],price_musd:'0.01',expires_at:'2026-10-23T18:04:00Z'};

test('contracts accept closed Trove preview and reject mixed legacy fields',async()=>{
 const contracts=await Contracts.load(new URL('../../dist/contracts/',import.meta.url));
 contracts.assert('preview',preview);
 assert.throws(()=>contracts.assert('preview',{...preview,side:'BUY'}));
 assert.throws(()=>contracts.assert('preview',{...preview,borrower:'invalid'}));
});
test('generic report contract recognizes the independently reproducible Trove schema',async()=>{
 const contracts=await Contracts.load(new URL('../../dist/contracts/',import.meta.url));
 const report=JSON.parse(await readFile(new URL('../../../../evidence/mezo-testnet/2026-10-23-trove-risk-preview/report.json',import.meta.url),'utf8'));
 contracts.assert('report',report);
 assert.throws(()=>contracts.assert('report',{...report,extra:true}));
});
test('capabilities advertise Trove only when enabled without changing legacy capability shape',async()=>{
 const contracts=await Contracts.load(new URL('../../dist/contracts/',import.meta.url));
 const legacy=capabilitiesResource('123e4567-e89b-42d3-a456-426614174050','live-public',[]);
 const enabled=capabilitiesResource('123e4567-e89b-42d3-a456-426614174050','live-public',[],true);
 assert.equal('products' in legacy,false);
 assert.deepEqual(enabled.products,['market_depth','trove_risk']);
 contracts.assert('capabilities',legacy);contracts.assert('capabilities',enabled);
});
