## 7. Confidence and limitations

### High confidence

- existence and current labels of live web surfaces;
- shutdown VOOI Light;
- official Telegram bot identity;
- pinned commits and contents of public repositories;
- method/path from the generated SDK;
- Bearer MCP setup;
- SSE usage in official clients.

### Medium confidence

- the generated SDK closely matches the live server surface;
- the market list and response semantics have not changed since 2026-06-12;
- absence of native clients in public distribution.

### Unverified

- internal server topology;
- exact production rate limits;
- idempotency of order/transfer requests;
- guarantees for event ordering and the SSE replay window;
- compatibility of the generated SDK with the current live API;
- existence of private/delisted APKs;
- production implementation MCP tools.

As of 2026-08-10, `https://perps-api.vooi.io/docs` redirected to Cloudflare
Access login. The generated SDK from the official repository is therefore
the most complete publicly verifiable schema snapshot, but must not be treated as
a permanent contract.

## 8. Risks for Multi-Exchange Engine

| Risk | Why it matters | Required protection |
|---|---|---|
| Broad generated client | One import exposes orders, transfer, and withdraw | Do not vendor the SDK; write a narrow read-only transport |
| `cancel-all` | Can affect other people's/manual orders | Never enable it; exact ownership registry |
| Stale market mapping | `baseSymbol`, `id`, and HIP-3 prefixes change | Snapshot/version/hash, fail closed |
| Shared margin account | Logical venues may share a Hyperliquid account | Account identity separate from venue alias |
| SSE gap/reconnect | Lost events create false state | Sequence/epoch evidence and authoritative REST reconciliation |
| Unknown POST outcome | An HTTP timeout does not prove an order is absent | Unknown state freeze, lookup before retry |
| Token leakage | One Bearer exposes a broad surface | Separate scoped token, redacted logs, no token in query/history |
| Signature confusion | prepare/execute payload venue-specific | Domain separation, exact payload hash, user confirmation |
| Transfer/withdraw exposure | A configuration error becomes a loss of funds | Separate process/capability; absent from the current build |
| API edge dependency | VOOI becomes a shared point of failure | Raw evidence, health status, venue-direct fallback only after review |

## 9. Recommended integration path

### Step R0 — fixture research only

1. Record the `GET /exchange/markets` response as a non-executable fixture.
2. Preserve raw bytes, headers, timestamp, and SHA-256.
3. Specify schema drift tests.
4. Do not add credentials or a network runtime.

### Step R1 — public read-only collector

After a separate review:

1. allow only the allowlisted HTTPS host;
2. allow only `GET /exchange/markets`,
   `/exchange/top-volume-symbols-quotes`, `/funding-strategies*`, and `/time`,
   if live probing confirms that authentication is not required;
3. forbid redirects outside the host;
4. forbid POST/PUT/PATCH/DELETE at the transport level;
5. preserve raw evidence before normalization;
6. keep the engine in `shadow`.

### Step R2 — authenticated read-only boundary

Only through a separate process and a separate decision:

- a scoped read-only token, if VOOI supports scopes;
- account reads are separated from the public collector;
- the token never enters the main engine, logs, or fixtures;
- the SSE private stream is not mixed with the public market stream;
- no signing, orders, leverage, transfers, or withdrawals.

### Step R3 — mutations

Outside this research package. Separate contracts, chaos
tests, ownership registry, unknown-state reconciliation, human-reviewed
release gate, and explicit removal of the shadow-only restriction will be required.

## 10. Practical conclusion

For new code, the reference is **Ultra + Perps API**, rather than Light. Pro is useful as
a historical UX/venue reference. Official examples provide enough
material to build an independent narrow read-only adapter, but connecting the
entire generated VOOI SDK is dangerous: its surface combines market data,
private account state, trading, broker approval, funds transfer, and withdrawal.
