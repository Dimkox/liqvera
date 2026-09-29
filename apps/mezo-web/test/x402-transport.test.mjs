import assert from "node:assert/strict";
import test from "node:test";

import { boundedFetch, boundedFetchJson, boundedResponseJson } from "../src/x402-transport.mjs";

test("payment fetch enforces timeout and supplies no ambient credentials or redirects", async () => {
  let observed;
  const fetcher = async (_url, init) => {
    observed = init;
    return new Response("{}", { status: 200 });
  };
  await boundedFetch(fetcher, "/paid", { credentials: "include", redirect: "follow" }, 20);
  assert.equal(observed.credentials, "omit");
  assert.equal(observed.redirect, "error");
  assert.equal(observed.cache, "no-store");

  await assert.rejects(
    boundedFetch((_url, init) => new Promise((_resolve, reject) => {
      init.signal.addEventListener("abort", () => reject(init.signal.reason), { once: true });
    }), "/paid", {}, 5),
    /abort|timeout/i,
  );
});

test("payment fetch rejects a redirect even if a transport returns it", async () => {
  await assert.rejects(
    boundedFetch(async () => new Response(null, { status: 302, headers: { location: "https://evil.invalid" } }), "/paid", {}),
    /Redirects are forbidden/,
  );
});

test("payment decoder rejects declared and streamed responses over the cap", async () => {
  await assert.rejects(
    boundedResponseJson(new Response("{}", { headers: { "content-length": "99" } }), 8),
    /exceeds/,
  );
  const stream = new ReadableStream({ start(controller) { controller.enqueue(new Uint8Array(9)); controller.close(); } });
  await assert.rejects(boundedResponseJson(new Response(stream), 8), /exceeds/);
});

test("payment deadline remains active while the response body is stalled", async () => {
  const stalled = new ReadableStream({ start(controller) { controller.enqueue(new Uint8Array([123])); } });
  await assert.rejects(
    boundedFetchJson(async () => new Response(stalled, { status: 200 }), "/paid", {}, 1024, 5),
    /deadline exceeded/,
  );
});
