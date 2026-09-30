# Observability and alerting

## Installed Linux stack

Use the stable wrapper; it emits one closed JSON result and uses exit 0 only
for a completed command:

```bash
root="${XDG_DATA_HOME:-$HOME/.local/share}/liqvera"
"$root/liqvera.sh" --install-root "$root" status --json
"$root/liqvera.sh" --install-root "$root" logs gateway --tail 200 --since 15m
```

Status contains schema, phase, product version, archive release digest,
commit/tree, Compose project, service-manager mode, and blockers. Healthy
shadow operation still reports `EXTERNAL_GRANT_REQUIRED` and
`SIMULATED_SOURCE`; it never proves payment, live-market, or overall release
acceptance. Logs accept only postgres, migrate, capture, report, gateway, web,
or edge; tail is 1–1000 and duration is a positive bounded `s`, `m`, `h`, or
`d` value. Output is capped and redacts authorization, password, token,
signature, and credential-bearing URL forms.

| Installer error | Non-destructive action |
| --- | --- |
| `UNSUPPORTED_LINUX` | Use a listed Linux release and architecture. |
| `DEPENDENCY_MISSING` | Install the documented floors, or explicitly approve the printed dependency command. |
| `UNSAFE_INSTALL_ROOT` | Choose a private local, non-symlinked root. |
| `PORT_OCCUPIED` | Stop the conflicting local service; the candidate is stopped automatically. |
| `RELEASE_DIGEST_MISMATCH` / `ARCHIVE_INVALID` | Delete only the failed download/materialization and reacquire reviewed assets. |
| `CONFIG_INVALID` / `SECRET_REFERENCE_INVALID` | Correct the closed config or owner-only secret-file reference. |
| `MIGRATION_MISMATCH` | Stop; preserve the database and reconcile exact migrations 001–005. |
| `HEALTH_TIMEOUT` | Inspect bounded service logs and readiness blockers; do not switch current manually. |
| `ROLLBACK_RESTORE_REQUIRED` | Preserve state and use reviewed forward recovery or coherent backup restore. |
| `PURGE_CONFIRMATION_REQUIRED` | Re-run preview and inspect every target before supplying its exact token. |

The lifecycle journal, installed state, release manifest, full inventory
digest, migration checksums, config, and current pointer provide local recovery
signals. Secrets remain referenced files and never belong in evidence.

The edge exposes only public `/healthz`, `/readyz`, and documented `/v1/*`
routes. Probe liveness and readiness separately from outside the host. The
gateway must return readiness false for missing recipient, wrong chain/token,
unverified facilitator or finality, unavailable storage, or other payment
gates. Container healthchecks establish process liveness; they cannot prove
settlement or report integrity.

Prometheus text is served at `GET /metrics` on port 9090 bound to the
gateway's `gateway-metrics` address on the internal `operations` network.
Compose publishes no metrics port and Caddy has no `/metrics` route. An
authorized operator may collect it only from an explicitly attached internal
collector or bounded one-off probe. Do not add a host port or edge route. F6
validates this topology statically and does not start a collector or container.

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
