import assert from "node:assert/strict";
import test from "node:test";
import { readFile } from "node:fs/promises";
import { HISTORICAL_DEMO, formatHistoricalDate, validateHistoricalReport, verifyHistoricalAssets } from "../src/historical-demo.ts";

test("historical live report validates exact immutable identity", async () => {
  const reportBytes=await readFile(new URL("../public/demo/latest-live/report.json",import.meta.url));
  const report=JSON.parse(reportBytes.toString("utf8"));
  assert.equal(validateHistoricalReport(report).report_id,HISTORICAL_DEMO.reportId);
  assert.throws(()=>validateHistoricalReport({...report,report_id:crypto.randomUUID()}),/failed validation/);
  assert.match(formatHistoricalDate(HISTORICAL_DEMO.sourceAt),/2026/);
  const bundle=await readFile(new URL("../public/demo/latest-live/evidence.zip",import.meta.url));
  assert.equal((await verifyHistoricalAssets(reportBytes,bundle)).report_id,HISTORICAL_DEMO.reportId);
  const changed=Uint8Array.from(reportBytes);changed[changed.length-1]^=1;
  await assert.rejects(()=>verifyHistoricalAssets(changed,bundle),/digest/i);
  const changedBundle=Uint8Array.from(bundle);changedBundle[changedBundle.length-1]^=1;
  await assert.rejects(()=>verifyHistoricalAssets(reportBytes,changedBundle),/digest/i);
});

test("historical preview UI exposes loading error and accessible mobile-safe controls", async () => {
  const source=await readFile(new URL("../src/main.ts",import.meta.url),"utf8");
  const style=await readFile(new URL("../src/style.css",import.meta.url),"utf8");
  assert.match(source,/Show latest live report/);
  assert.match(source,/Loading sealed historical report/);
  assert.match(source,/Historical preview could not be loaded/);
  assert.match(source,/No payment transaction exists for this public preview/);
  assert.match(source,/download="liqvera-historical-live-evidence\.zip"/);
  assert.match(source,/https:\/\/github\.com\/Dimkox\/liqvera/);
  assert.match(source,/href="https:\/\/github\.com\/Dimkox\/liqvera\/releases"/);
  assert.doesNotMatch(source,/releases\/tag\//);
  assert.match(source,/Liqvera v0\.0\.4/);
  assert.match(source,/<span class="step">STEP 1<\/span>/);
  assert.match(source,/<span class="step">STEP 2<\/span>/);
  assert.doesNotMatch(source,/<span class="step">0[12]<\/span>/);
  assert.match(style,/\.step\{[^}]*min-width:72px[^}]*width:auto[^}]*white-space:nowrap/);
  assert.match(source,/rel="noopener noreferrer"/);
});

test("fresh quote render uses the standards-safe shared UTC formatter", async () => {
  const source=await readFile(new URL("../src/main.ts",import.meta.url),"utf8");
  assert.doesNotThrow(()=>formatHistoricalDate("2026-10-01T01:37:22.535Z"));
  assert.match(formatHistoricalDate("2026-10-01T01:37:22.535Z"),/2026/);
  assert.doesNotMatch(source,/function dateTime\(/);
  assert.doesNotMatch(source,/dateStyle[\s\S]{0,160}timeStyle[\s\S]{0,160}timeZoneName/);
  assert.match(source,/"Snapshot time", formatHistoricalDate\(q\.preview\.snapshot_at\)/);
  assert.match(source,/"Quote expires", formatHistoricalDate\(q\.terms\.expires_at\)/);
});
