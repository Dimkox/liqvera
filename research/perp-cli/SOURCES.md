# Source log

Snapshot date: **2026-08-10**.

## Primary / authoritative sources

| Source | Pinned/observed state | Use |
|---|---|---|
| https://github.com/hypurrquant/perp-cli | main `ed94cfd46259ff9186bf4f2489252a4f8f773e31` | authoritative TypeScript source |
| https://github.com/hypurrquant/perp-cli/blob/main/package.json | `perp-cli` `0.13.0` | package/bin/dependency surface |
| https://github.com/hypurrquant/perp-cli/blob/main/CHANGELOG.md | `0.13.0` release + later hardening on main | release history / HIP-4 additions |
| https://github.com/hypurrquant/perp-cli/blob/main/LICENSE | MIT | redistribution/source-use boundary |
| https://github.com/hypurrquant/perp-cli/blob/main/src/index.ts | current main | CLI wiring, key resolution, adapter creation |
| https://github.com/hypurrquant/perp-cli/blob/main/src/exchanges/interface.ts | current main | common ExchangeAdapter contract |
| https://github.com/hypurrquant/perp-cli/blob/main/src/exchanges/registry.ts | current main | built-in exchange registrations |
| https://github.com/hypurrquant/perp-cli/blob/main/src/api/public/urls.ts | current main | public API endpoint constants |
| https://github.com/hypurrquant/perp-cli/blob/main/src/mcp-server.ts | current main | MCP behavior and public-read fallbacks |
| https://github.com/hypurrquant/perp-cli/blob/main/SECURITY.md | latest only supported | project security boundary |
| https://www.npmjs.com/package/perp-cli | package distribution | official npm surface |
| https://registry.npmjs.org/perp-cli/0.13.0 | exact registry metadata | reproducible npm tarball discovery |

## Third-party surfaces

| Source | Observation |
|---|---|
| https://github.com/iflow-mcp/hypurrquant-perp-cli | older fork/mirror; main `cae9101d182407d684d6c557db8d4b1947d90ffa`; package metadata `0.9.8` |
| https://www.npmjs.com/package/@iflow-mcp/hypurrquant-perp-cli | scoped third-party package `0.9.8` |
| https://glama.ai/mcp/servers/hypurrquant/perp-cli | MCP directory/index |
| https://www.claudepluginhub.com/plugins/hypurrquant-perp-cli | agent/plugin index; can lag/reshape upstream docs |
| https://unyly.org/mcp/hypurrquant-perp-cli | MCP directory/index |
| https://chat.mcp.so/server/perp-cli/hypurrquant | MCP directory/index |

These are discovery/republishing surfaces, not authoritative source for current
behavior. Any tool-count/version discrepancy is resolved in favor of the pinned
upstream source.

## Explicit name collision excluded

`https://www.npmjs.com/package/@perp/cli` is a different historical package:
Perpetual Protocol CLI `0.2.6`. It is preserved in `clients.lock.json` so search
results do not accidentally merge two unrelated codebases.

## Version / provenance caveat

The upstream repository's current `main` commit is newer than the `0.13.0`
release entry. `package.json` still reports `0.13.0`, so this research snapshot
describes **main at `ed94cfd46259ff9186bf4f2489252a4f8f773e31` with package version field `0.13.0`**,
not necessarily the byte-for-byte npm tarball source tree.

Use both acquisition modes when reproducibility matters:

1. Git source pinned by commit SHA.
2. npm tarball pinned by exact package version and recorded SHA-256.

## Search boundary / negative findings

Search and first-party surfaces were checked for Android/APK, iOS/App Store,
native desktop and browser-extension distributions. None were verified as
official `hypurrquant/perp-cli` distributions in the observed public surface.
