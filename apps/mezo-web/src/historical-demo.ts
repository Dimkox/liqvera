export const HISTORICAL_DEMO = Object.freeze({
  reportId: "be727ceb-3e34-4963-963d-ee2fb98fb4f9", sourceAt: "2026-10-23T15:26:44.055Z",
  reportSha256: "d58728bd3df4b79c43bb2e742225e5b8f879eb0ec292213ffd3941f0f8778753",
  bundleSha256: "0c20f41f845bd39c88286b52a64d1dad53713fd215507f611fab51d29896f51f",
  reportUrl: "/demo/snapshots/d58728bd3df4b79c43bb2e742225e5b8f879eb0ec292213ffd3941f0f8778753/report.json", bundleUrl: "/demo/snapshots/d58728bd3df4b79c43bb2e742225e5b8f879eb0ec292213ffd3941f0f8778753/evidence.zip",
});
export function validateHistoricalReport(value:unknown):Record<string,any> {
  const report=value as Record<string,any>;
  if (!report || typeof report !== "object" || report.schema !== "liqvera-evidence-report/v1" ||
      report.report_id !== HISTORICAL_DEMO.reportId || report.source?.source_mode !== "live-public" ||
      report.source?.source_at !== HISTORICAL_DEMO.sourceAt || report.identity?.instrument_id !== "hyperliquid:BTC:perpetual" ||
      report.quality?.snapshot_status !== "VALID_FOR_SNAPSHOT_CALCULATION" || report.boundaries?.execution_authority !== "NONE" ||
      report.boundaries?.execution_promise !== false) throw new Error("Historical live report failed validation.");
  return report;
}
export function formatHistoricalDate(value:string):string {
  const date=new Date(value);
  return Number.isFinite(date.getTime())?`${date.toLocaleString(undefined,{dateStyle:"medium",timeStyle:"medium",timeZone:"UTC"})} UTC`:value;
}
async function sha256(bytes:Uint8Array,subtle:SubtleCrypto):Promise<string> {
  const digest=await subtle.digest("SHA-256",bytes as BufferSource);
  return Array.from(new Uint8Array(digest),byte=>byte.toString(16).padStart(2,"0")).join("");
}
export async function verifyHistoricalAssets(reportBytes:Uint8Array,bundleBytes:Uint8Array,
  subtle:SubtleCrypto=crypto.subtle):Promise<Record<string,any>> {
  if(await sha256(reportBytes,subtle)!==HISTORICAL_DEMO.reportSha256)throw new Error("Historical report digest mismatch.");
  if(await sha256(bundleBytes,subtle)!==HISTORICAL_DEMO.bundleSha256)throw new Error("Historical bundle digest mismatch.");
  let value:unknown;
  try { value=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(reportBytes)); }
  catch { throw new Error("Historical report encoding is invalid."); }
  return validateHistoricalReport(value);
}
