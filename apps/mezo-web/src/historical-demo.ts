export const HISTORICAL_DEMO = Object.freeze({
  reportId: "3c02f1e7-e197-487b-bac7-bf8b73823a38", sourceAt: "2026-10-12T22:38:07.729Z",
  reportSha256: "0ebf36b89bda183b99767cd7fedc3c956405ef4a3f195d9d73b911d2c146ccf2",
  bundleSha256: "3255a42c210c6fe6ad0020c34113988da3f1659c566a73b7729606ad65d083b0",
  reportUrl: "/demo/latest-live/report.json", bundleUrl: "/demo/latest-live/evidence.zip",
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
  return Number.isFinite(date.getTime())?date.toLocaleString(undefined,{dateStyle:"medium",timeStyle:"medium",timeZone:"UTC"}):value;
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
