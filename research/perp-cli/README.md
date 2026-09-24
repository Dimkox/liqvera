# perp-cli inventory and static reverse engineering

Snapshot: **2026-08-10**. This directory follows the `research/vooi` approach: it records
public distributions, exact revisions, observable surfaces, architectural
analysis, and reproducible tools for obtaining source artifacts without executing
the downloaded code.

## Key finding

Unlike a closed web/mobile client, `hypurrquant/perp-cli` is already published
as a TypeScript source project under MIT. Therefore, "reverse engineering to
source code" requires no decompilation here: the authoritative source is the public
repository pinned to commit
`ed94cfd46259ff9186bf4f2489252a4f8f773e31`. Its current `package.json` specifies `perp-cli@0.13.0`.

## Inventory

| Surface | Status | Recorded version |
|---|---|---|
| `hypurrquant/perp-cli` | Official source repo | `0.13.0`, `ed94cfd462...` |
| npm `perp-cli` | Official package | `0.13.0` |
| `perp` | Main CLI entry point | `dist/index.js` |
| `perp-mcp` | MCP/agent entry point | `dist/mcp-server.js` |
| `perp-guardrail` | safety/guardrail entry point | `dist/guardrail/perp-guardrail.js` |
| `skills/perp-cli` | bundled AI-agent skill | Included in the npm package |
| `iflow-mcp/hypurrquant-perp-cli` | Third-party fork/mirror | `0.9.8`, `cae9101d18...` |
| npm `@iflow-mcp/hypurrquant-perp-cli` | Third-party republication | `0.9.8` |
| Glama / ClaudePluginHub / Unyly / mcp.so | Third-party directories | index/listing only |
| npm `@perp/cli` | **Unrelated** to this project | historical Perpetual Protocol CLI `0.2.6` |

Official Android/iOS applications, a browser extension, or a separate native
desktop app could not be confirmed. This is a qualified negative finding, not
proof that no private builds exist.

## Directory contents

- `clients.lock.json` — machine-readable registry of source/package/entry points,
  third-party mirrors, and name collisions.
- `architecture.md` — static analysis index.
- `architecture/01-packaging-and-surfaces.md` — packaging, npm, bin, skill, mirrors.
- `architecture/02-runtime-and-adapters.md` — CLI runtime, adapter abstraction,
  public API endpoints, and exchange model.
- `architecture/03-auth-mcp-and-risk.md` — keys/signers, MCP boundary, mutation
  paths, and integration constraints.
- `data/surface-map.csv` — surface-level classification of read/mutate/funds risk.
- `data/exchange-adapters.csv` — 4 built-in DEX adapter registrations.
- `SOURCES.md` — primary and secondary sources, versions, and limitations.
- `scripts/fetch_sources.py` — safe retrieval of pinned public Git
  revisions without executing downloaded project code.
- `scripts/extract_observables.py` — URL/env/bin/command-like observables from
  downloaded source and locally added npm tarballs.
- `scripts/verify_inventory.py` — offline inventory + CSV verification.
- `tests/test_verify_inventory.py` — minimal regression contract for the inventory.

`artifacts/` is deliberately excluded from Git: it holds exact copies of upstream
source and any locally downloaded npm tarballs/capture metadata.

## Offline verification

From the `multi-exchange-engine` root:

```bash
python -B research/perp-cli/scripts/verify_inventory.py
python -m py_compile research/perp-cli/scripts/*.py
PYTHONPATH=research/perp-cli python -B -m unittest discover -s research/perp-cli/tests -v
```

Expected output structure of the first command:

```json
{"ok": true, "official_components": 6, "supported_exchanges": 4, "third_party_surfaces": 6, "snapshot_at": "2026-08-10T11:44:00Z"}
```

## Fetching source

The fetcher is restricted to public `github.com` HTTPS repositories listed in
`clients.lock.json` and verifies the final commit SHA. It neither imports nor
executes downloaded JavaScript/TypeScript:

```bash
python research/perp-cli/scripts/fetch_sources.py repos
```

Exact npm package versions and registry metadata URLs are pinned in
`clients.lock.json`. Npm tarballs are deliberately not vendored in Git; when capturing
a package locally, save it under `research/perp-cli/artifacts/npm/` and
record its SHA-256 alongside capture metadata.

After downloading:

```bash
python research/perp-cli/scripts/extract_observables.py \
  research/perp-cli/artifacts \
  -o research/perp-cli/observables.local.json
```

## Static analysis findings

`perp-cli` is built around a shared `ExchangeAdapter` that combines
market-data, account reads, trading mutations, and risk operations. The built-in
registry specifies Pacifica, Hyperliquid, Lighter, and Aster. The CLI additionally
includes funds/bridge/rebalance, strategies/background jobs, wallet/agent
signing, and Hyperliquid HIP-4 outcome markets.

`mcp-server.ts` in the current source explicitly describes MCP as an advisor/read-oriented
surface and must not be treated as a direct trade executor. However, the main CLI
can place/edit/cancel orders, change leverage, move
funds, and run long-lived strategies. Therefore, Multi-Exchange Engine
must not import the entire CLI as a "read-only adapter" — it needs a separate
allowlist for the public/read path.

## Analysis boundaries

The following were not performed:

- Importing, running, or postinstall/prepublish of downloaded npm packages;
- Connecting real wallets/private keys;
- Trade/withdraw/bridge/deposit/rebalance;
- Intercepting user or authenticated traffic;
- Extracting private keys, API keys, cookies, bearer tokens, or wallet signatures;
- Exploit testing against real exchanges/funds.

For integration into Multi-Exchange Engine, the recommended first phase is limited to
public market-data readers and types/normalization. Trading, funds, and signer
layers must remain behind a separate boundary with explicit consent and policy review.
