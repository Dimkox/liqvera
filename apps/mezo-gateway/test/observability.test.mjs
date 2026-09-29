import assert from "node:assert/strict";
import test from "node:test";

import { metrics, telemetryHandler } from "../src/security/observability.ts";

function response() {
  return {
    status: null,
    headers: null,
    body: "",
    writeHead(status, headers) { this.status = status; this.headers = headers; },
    end(body = "") { this.body = body; },
  };
}

test("telemetry exposes only GET /metrics and never health/readiness routes", () => {
  for (const [method, url] of [["POST", "/metrics"], ["GET", "/"], ["GET", "/healthz"], ["GET", "/readyz"]]) {
    const res = response();
    telemetryHandler({ method, url }, res);
    assert.equal(res.status, 404);
    assert.equal(res.body, "");
  }
  const res = response();
  telemetryHandler({ method: "GET", url: "/metrics" }, res);
  assert.equal(res.status, 200);
  assert.equal(res.headers["Cache-Control"], "no-store");
});

test("metrics have the exact bounded label-free grammar", () => {
  metrics.readiness(false);
  const blocked = response();
  telemetryHandler({ method: "GET", url: "/metrics" }, blocked);
  const samples = blocked.body.split("\n").filter(line => line.startsWith("liqvera_"));
  const names = samples.map(line => line.split(/[ _]/).slice(0, -1).join("_"));
  const allowedCounters = [
    "http_request", "http_error", "payment_required", "payment_verified", "payment_settled", "payment_unknown",
    "authorization_duplicate", "delivery_failure", "artifact_integrity_failure", "build_complete", "build_rejected",
    "worker_failure", "reconciliation_complete",
  ].map(name => `liqvera_${name}_total`);
  assert.deepEqual(samples.slice(0, allowedCounters.length).map(line => line.split(" ")[0]), allowedCounters);
  assert.equal(samples.at(-1), "liqvera_payment_ready 0");
  assert.ok(samples.every(line => /^liqvera_[a-z_]+ (?:0|[1-9][0-9]*)(?:\.[0-9]+)?$/.test(line)));
  assert.ok(samples.every(line => !line.includes("{") && !line.includes("report_id") && !line.includes("payer")));
  assert.ok(names.length >= allowedCounters.length);

  metrics.readiness(true);
  const ready = response();
  telemetryHandler({ method: "GET", url: "/metrics" }, ready);
  assert.match(ready.body, /liqvera_payment_ready 1\n$/);
});
