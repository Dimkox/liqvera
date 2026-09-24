# Observability and alerting

The edge exposes only public `/healthz`, `/readyz`, and documented `/v1/*`
routes. Probe liveness and readiness separately from outside the host. The
gateway must return readiness false for missing recipient, wrong chain/token,
unverified facilitator or finality, unavailable storage, or other payment
gates. Container healthchecks establish process liveness; they cannot prove
settlement or report integrity.

Collect bounded metrics without wallet addresses as labels:

| Signal | Watch for |
| --- | --- |
| Report build duration and rejection reason | Slow builds, stale/crossed/invalid source, `SOURCE_UNAVAILABLE` |
| Storage and artifact integrity failures | Missing/corrupt bundle, failed atomic publication, digest mismatch |
| Quote creation and 402 counts | Unexpected chargeability or a fixture quote |
| Payment verify, submit, confirm, unknown counts | Any unknown or duplicate authorization attempt |
| Reconciliation age and manual-review backlog | Stalled unknown outcomes |
| Paid delivery latency and failures | Missing entitlement, delayed or repeated delivery |
| PostgreSQL and volume capacity | Disk exhaustion before it affects payment state |
| Readiness vector and container restarts | External dependency, configuration, or process failure |

Alert immediately on a fixture-origin chargeable quote, mainnet chain or
wrong token detection, an attempted second settlement for one authorization,
paid delivery before finality, raw/artifact digest mismatch, or lost durable
payment state. Keep a separate alert for readiness remaining false; that may
be the correct fail-closed state during development but blocks a paid demo.

Structured logs should carry stable error codes, UTC timestamps, safe
request/quote/report/attempt correlation IDs, source mode, and image/source
version. Do not log bearer capabilities, cookies, `PAYMENT-SIGNATURE`, raw
authorization payloads, database URLs/passwords, internal report-service
tokens, private keys, or participant email. Sanitize any transaction evidence
before attaching it to acceptance or incident reports. Limit log retention
and access independently from the
paid artifact retention policy.
