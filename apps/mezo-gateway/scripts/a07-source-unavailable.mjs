import { HttpReportService } from '../dist/adapters/report-service.js';

const originalFetch = globalThis.fetch;
let requests = 0;
globalThis.fetch = async () => {
  requests += 1;
  return new Response(JSON.stringify({ code: 'SOURCE_UNAVAILABLE' }), {
    status: 503,
    headers: { 'content-type': 'application/json' },
  });
};

let reason = null;
let artifactEmitted = false;
try {
  const service = new HttpReportService(new URL('https://source.invalid/'));
  await service.build(
    '00000000-0000-4000-8000-000000000007',
    { side: 'BUY', quantity_base: '0.15', expected_payer: '0x1111111111111111111111111111111111111111' },
    AbortSignal.timeout(1000),
  );
  artifactEmitted = true;
} catch (error) {
  reason = error && typeof error === 'object' && 'code' in error ? error.code : null;
} finally {
  globalThis.fetch = originalFetch;
}

process.stdout.write(`${JSON.stringify({
  schema: 'liqvera-a07-source-unavailable/v1',
  adapter: 'HttpReportService.build',
  request_count: requests,
  reason,
  source_mode: 'live-public',
  fixture_fallback_used: false,
  artifact_emitted: artifactEmitted,
})}\n`);
if (reason !== 'SOURCE_UNAVAILABLE' || artifactEmitted || requests !== 1) process.exitCode = 1;
