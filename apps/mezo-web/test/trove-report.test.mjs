import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import test from 'node:test';
import {validateTroveReport} from '../src/trove-report.ts';
const report=JSON.parse(await readFile(new URL('../../../evidence/mezo-testnet/2026-10-23-trove-risk-preview/report.json',import.meta.url),'utf8'));
test('native Trove report is recognized without wallet or network access',()=>assert.equal(validateTroveReport(report),report));
for(const [label,mutate] of [
 ['borrower',r=>r.trove_risk.borrower='0x1111111111111111111111111111111111111111'],
 ['block',r=>r.trove_risk.block_number='https://evil.invalid'],
 ['number',r=>r.trove_risk.debt_musd=123],
 ['status',r=>r.trove_risk.status='SAFE FOREVER'],
 ['flags',r=>r.boundaries.execution_promise=true],
])test(`Trove report rejects altered ${label}`,()=>{const value=structuredClone(report);mutate(value);assert.throws(()=>validateTroveReport(value));});
