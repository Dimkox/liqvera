import assert from 'node:assert/strict';
import { createServer, type IncomingMessage, type ServerResponse } from 'node:http';
import { once } from 'node:events';
import test from 'node:test';
import { HttpReportService } from '../src/adapters/report-service.js';

const REPORT_ID = '11111111-1111-4111-8111-111111111111';

async function withServer(
  responder: (request: IncomingMessage, response: ServerResponse) => void,
  run: (base: URL) => Promise<void>,
): Promise<void> {
  const server = createServer(responder);
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
  const address = server.address();
  assert(address && typeof address === 'object');
  try {
    await run(new URL(`http://127.0.0.1:${address.port}`));
  } finally {
    server.close();
    await once(server, 'close');
  }
}

test('cleanup accepts both exact HTTP 200 absence outcomes', async () => {
  for (const deleted of [true, false]) {
    await withServer((request, response) => {
      assert.equal(request.method, 'DELETE');
      assert.equal(request.url, `/internal/v1/reports/${REPORT_ID}`);
      assert.equal(request.headers.authorization, 'Bearer test_cleanup_token_1234567890');
      response.writeHead(200, { 'content-type': 'application/json' });
      response.end(JSON.stringify({ report_id: REPORT_ID, deleted }));
    }, async base => {
      const service = new HttpReportService(base, 'test_cleanup_token_1234567890');
      assert.equal(await service.cleanup(REPORT_ID, AbortSignal.timeout(1000)), true);
    });
  }
});

test('cleanup rejects structurally invalid or mismatched HTTP 200 bodies', async () => {
  const bodies: unknown[] = [
    { report_id: '22222222-2222-4222-8222-222222222222', deleted: true },
    { report_id: REPORT_ID, deleted: 'true' },
    { report_id: REPORT_ID },
    { report_id: REPORT_ID, deleted: true, extra: true },
  ];
  for (const body of bodies) {
    await withServer((_request, response) => {
      response.writeHead(200, { 'content-type': 'application/json' });
      response.end(JSON.stringify(body));
    }, async base => {
      const service = new HttpReportService(base, 'test_cleanup_token_1234567890');
      assert.equal(await service.cleanup(REPORT_ID, AbortSignal.timeout(1000)), false);
    });
  }
});

test('cleanup rejects malformed JSON and non-200 responses', async () => {
  await withServer((_request, response) => {
    response.writeHead(200, { 'content-type': 'application/json' });
    response.end('{');
  }, async base => {
    const service = new HttpReportService(base, 'test_cleanup_token_1234567890');
    await assert.rejects(service.cleanup(REPORT_ID, AbortSignal.timeout(1000)));
  });

  await withServer((_request, response) => {
    response.writeHead(503, { 'content-type': 'application/json' });
    response.end(JSON.stringify({ report_id: REPORT_ID, deleted: false }));
  }, async base => {
    const service = new HttpReportService(base, 'test_cleanup_token_1234567890');
    await assert.rejects(service.cleanup(REPORT_ID, AbortSignal.timeout(1000)));
  });
});
