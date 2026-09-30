# Security re-review R3 — SEC-03

## Review binding

- Base: `e3df6833e8916d01f55028e63d4db1632a805a75`
- Reviewed head: `ea3098732b369f92d4a8ec7503cfda6153a582ee`
- Scope: prior finding SEC-03 only — live gateway network namespace, loopback database proxy, PostgreSQL isolation, and executable topology tests.
- Constraints observed: no secret reads, external calls, product edits, or scope expansion.

## Verdict

**PASS — SEC-03 is resolved.** This report supports a passing `security_review` receipt for the reviewed head, limited to the stated scope.

## Evidence

### Dedicated gateway network namespace

`gateway-live` now uses `network_mode: service:gateway-net-live`; it no longer shares the PostgreSQL namespace. `gateway-net-live` alone owns the gateway-facing `edge`, `gateway_report`, `operations`, and `payment_egress` attachments plus the internal `gateway_db` attachment.

The namespace service runs as non-root, is read-only, drops all capabilities, enables `no-new-privileges`, and has explicit process, memory, CPU, and temporary-filesystem bounds. It mounts no secrets or volumes.

### Loopback-only database bridge

`db-loopback-proxy.js` listens only on `127.0.0.1:5432`. Because `gateway-live` shares the proxy namespace, its grant-bound database endpoint remains the required credential-free loopback identity. The proxy connects upstream to the `postgres` alias solely over `gateway_db`.

The proxy rejects non-loopback clients defensively, pauses clients until the upstream connection succeeds, limits active clients to 64, applies 30-second idle/error cleanup, and holds neither PostgreSQL credentials nor payment grant material. The gateway retains end-to-end PostgreSQL authentication over the byte-transparent proxy.

### PostgreSQL isolation restored

Rendered live Compose places `postgres-live` only on `gateway_db`. It no longer owns gateway aliases and has no attachment to `edge`, `gateway_report`, `operations`, or external `payment_egress`. The intended migration service and the credential-free proxy remain the only separate containers on its database network.

Thus lower-trust edge/report/operations peers have no network route to PostgreSQL, and compromise of PostgreSQL no longer inherits payment egress. This restores the least-privilege boundary identified in SEC-03 while preserving the database identity required by the one-shot grant.

### Executable topology checks

`tests/operations/test_f6_static.py` renders the real Compose model and asserts:

- `gateway-live` shares only `gateway-net-live`'s namespace;
- `postgres-live` belongs only to `gateway_db`;
- `gateway-net-live` owns the exact required gateway networks;
- the bridge command is the reviewed proxy;
- the bridge has no secrets or volumes;
- the proxy source binds `127.0.0.1` explicitly.

Command executed:

```text
pytest -q tests/operations/test_f6_static.py
5 passed, 0 failed
```

The three reported pytest warnings concern repository-level unknown asyncio configuration options and do not affect these synchronous topology assertions.

## Residual risk

The proxy is intentionally a network member of `gateway_db` and can relay loopback gateway connections to PostgreSQL. It has no database credentials, secret mounts, persistent storage, or general application behavior; this narrow connectivity is the reviewed bridge, not a restoration of the prior cross-network PostgreSQL exposure.
