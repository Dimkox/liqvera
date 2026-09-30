import assert from "node:assert/strict";
import test from "node:test";
import { readFile } from "node:fs/promises";
import { HISTORICAL_DEMO, validateHistoricalReport } from "../src/historical-demo.ts";

test("historical live report validates exact immutable identity", async () => {
  const report=JSON.parse(await readFile(new URL("../public/demo/latest-live/report.json",import.meta.url),"utf8"));
  assert.equal(validateHistoricalReport(report).report_id,HISTORICAL_DEMO.reportId);
  assert.throws(()=>validateHistoricalReport({...report,report_id:crypto.randomUUID()}),/failed validation/);
});

test("historical preview UI exposes loading error and accessible mobile-safe controls", async () => {
  const source=await readFile(new URL("../src/main.ts",import.meta.url),"utf8");
  assert.match(source,/Show latest live report/);
  assert.match(source,/Loading sealed historical report/);
  assert.match(source,/Historical preview could not be loaded/);
  assert.match(source,/No payment transaction exists for this public preview/);
  assert.match(source,/download="liqvera-historical-live-evidence\.zip"/);
  assert.match(source,/https:\/\/github\.com\/Dimkox\/liqvera/);
  assert.match(source,/href="https:\/\/github\.com\/Dimkox\/liqvera\/releases"/);
  assert.doesNotMatch(source,/releases\/tag\//);
  assert.match(source,/rel="noopener noreferrer"/);
});
