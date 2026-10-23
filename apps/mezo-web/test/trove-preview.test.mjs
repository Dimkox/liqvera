import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import test from 'node:test';
import {TROVE_PREVIEW,verifyTrovePreview} from '../src/trove-preview.ts';
const report=await readFile(new URL('../public'+TROVE_PREVIEW.reportUrl,import.meta.url));
const bundle=await readFile(new URL('../public'+TROVE_PREVIEW.bundleUrl,import.meta.url));
test('public Trove preview pins the actual native report and bundle before rendering',async()=>{
 const value=await verifyTrovePreview(report,bundle);assert.equal(value.trove_risk.block_number,'16323457');
 assert.ok(TROVE_PREVIEW.reportUrl.includes(TROVE_PREVIEW.reportSha256));
 assert.ok(TROVE_PREVIEW.bundleUrl.includes(TROVE_PREVIEW.reportSha256));
});
for(const member of ['report','bundle'])test(`Trove preview rejects changed ${member} bytes`,async()=>{
 const bad=Buffer.from(member==='report'?report:bundle);bad[bad.length-1]^=1;
 await assert.rejects(verifyTrovePreview(member==='report'?bad:report,member==='bundle'?bad:bundle));
});
