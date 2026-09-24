# VOOI client inventory and static reverse engineering

Snapshot: **2026-08-10**. This directory contains a reproducible inventory of
official VOOI clients, pinned SHAs of public repositories,
the extracted Perps API surface, and safe static-analysis
tools.

## Inventory summary

| Client | Current status as of the snapshot date | Recorded version/revision |
|---|---|---|
| VOOI Ultra | primary live web terminal | footer: `Beta v1.0.1` |
| VOOI Pro | live legacy/pro terminal | `v1.12.0` |
| VOOI Light | trading stopped; account migration remains | `v2.5.0` |
| Telegram Mini App | live Telegram WebApp | `@VooiAppBot` |
| VOOI Perps MCP | remote Streamable HTTP MCP | `https://perps-api.vooi.io/mcp` |
| MCP config repo | public configuration client | `9a5fc1a...` |
| Signals bot example | official Python client | `bb81ee0...` |
| Funding bot example | official Python client | `c3ceab2...` |
| MM bot example | official TypeScript/Node client | `879d15c...` |

No official APK, Google Play app, App Store app, or browser
extension could be verified. This means only that no verifiable
official publication was found within the research scope, rather than proving
that a private or delisted build does not exist.

## Directory contents

- `clients.lock.json` — machine-readable registry of clients, statuses, licenses,
  commit SHAs, and primary sources.
- `architecture.md` — static reverse-engineering findings and implications for
  Multi-Exchange Engine architecture.
- `data/api-surface-*.csv` — 77 observed `HTTP method + path` pairs from
  the generated official TypeScript SDK.
- `SOURCES.md` — log of primary sources and confidence limitations.
- `scripts/fetch_sources.py` — downloads exact public Git revisions and
  public same-origin web assets without authentication or JavaScript execution.
- `scripts/extract_observables.py` — statically extracts URLs, API paths, and
  environment variable names while redacting secret-like parameters.
- `scripts/verify_inventory.py` — fully offline verification of the registry and CSV.

## Offline verification

From the repository root:

```bash
python -B research/vooi/scripts/verify_inventory.py
python -m py_compile research/vooi/scripts/*.py
PYTHONPATH=research/vooi python -B -m unittest discover -s research/vooi/tests -v
```

Expected result of the first command:

```json
{"api_rows": 77, "ok": true, "programmatic_clients": 4, "snapshot_at": "2026-08-10T08:02:00Z", "web_clients": 6}
```

## Fetching public clients

The script does not execute downloaded code or send tokens:

```bash
# All four official public clients at exact SHAs
python research/vooi/scripts/fetch_sources.py repos

# Only one client
python research/vooi/scripts/fetch_sources.py repos \
  --include vooi-mm-bot-example

# Public HTML and same-origin JS/CSS/manifest for web surfaces
python research/vooi/scripts/fetch_sources.py web \
  --include vooi-ultra,vooi-pro,vooi-light
```

Results are written to `research/vooi/artifacts/`, which is excluded from Git.
Each object receives a SHA-256 and an entry in `capture.json`.

After downloading:

```bash
python research/vooi/scripts/extract_observables.py \
  research/vooi/artifacts/repositories \
  research/vooi/artifacts/web \
  -o research/vooi/observables.local.json
```

## Analysis boundaries

Static analysis covered public code, public pages, and official
documentation. The following were not performed:

- account login, wallet connection, or API token creation;
- interception of other people's traffic or bypass of Cloudflare Access, DRM, or other restrictions;
- calls to order, leverage, margin, transfer, deposit, or withdraw endpoints;
- extraction of private keys, bearer tokens, cookies, wallet signatures, or
  user data;
- publication of nonpublic web bundles in Git.

## Important boundary for Multi-Exchange Engine

The generated VOOI SDK includes market data as well as order creation/cancellation,
broad cancellation of all orders, leverage/margin mode changes,
cross-exchange transfers, and withdrawals. It therefore cannot be connected in full to the current
shadow-only runtime.

A future read-only adapter may use only a separate manually specified
contract after review. Every private/account/trading/funds path in
`data/api-surface-*.csv` is marked `forbidden` or `strictly_forbidden`.
