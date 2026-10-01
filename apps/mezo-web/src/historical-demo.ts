export const HISTORICAL_DEMO = Object.freeze({
  reportId: "d84fb495-8b22-49c1-99a3-a2b763afc977", sourceAt: "2026-09-30T23:32:40.858Z",
  reportSha256: "8f8fd199de1674e5b3f154e50609792bd7bdd711e15cd8a8c15cd703bcaac7dd",
  bundleSha256: "a6cc771d3fb8428325d32855fef53417f7da25c893db3a99b49802f482adc4fc",
  reportUrl: "/demo/latest-live/report.json", bundleUrl: "/demo/latest-live/evidence.zip",
});
export function validateHistoricalReport(value:unknown):Record<string,any> {
  const report=value as Record<string,any>;
  if (!report || typeof report !== "object" || report.schema !== "mee-evidence-report/v1" ||
      report.report_id !== HISTORICAL_DEMO.reportId || report.source?.source_mode !== "live-public" ||
      report.source?.source_at !== HISTORICAL_DEMO.sourceAt || report.identity?.instrument_id !== "hyperliquid:BTC:perpetual" ||
      report.quality?.snapshot_status !== "VALID_FOR_SNAPSHOT_CALCULATION" || report.boundaries?.execution_authority !== "NONE" ||
      report.boundaries?.execution_promise !== false) throw new Error("Historical live report failed validation.");
  return report;
}
export function formatHistoricalDate(value:string):string {
  const date=new Date(value);
  return Number.isFinite(date.getTime())?date.toLocaleString(undefined,{dateStyle:"medium",timeStyle:"medium",timeZone:"UTC"}):value;
}
