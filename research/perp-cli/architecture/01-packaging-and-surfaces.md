# 01 — Packaging and public surfaces

## Authoritative source

Primary source is `hypurrquant/perp-cli`, pinned for this snapshot to:

```text
ed94cfd46259ff9186bf4f2489252a4f8f773e31
package.json version: 0.13.0
license: MIT
```

The repository is a normal TypeScript/Node project, not an opaque application
bundle. The source tree includes `src/`, `skills/perp-cli`, tests, scripts,
documentation and package metadata.

## Published executable entry points

`package.json` exposes three binaries:

| binary | target | role |
|---|---|---|
| `perp` | `dist/index.js` | user/agent CLI |
| `perp-mcp` | `dist/mcp-server.js` | MCP server/advisor surface |
| `perp-guardrail` | `dist/guardrail/perp-guardrail.js` | guardrail/safety entry point |

The npm package publishes only `dist` and `skills`, so the npm tarball is a
compiled/distribution surface while GitHub is the authoritative readable source.

## Agent skill

`skills/perp-cli` is bundled with the npm package. Upstream documents manual or
agent-manager installation for Claude Code, Cursor, Codex and similar tools.
This skill is part of the product surface because it defines how autonomous
agents are expected to call the CLI, including dry-run/confirmation behavior.

## Third-party republishing

A separate `iflow-mcp/hypurrquant-perp-cli` repository and scoped npm package
exist at observed version `0.9.8`. They are older than upstream `0.13.0` and
must be treated as a fork/mirror/republication, not current truth.

Glama, ClaudePluginHub, Unyly and mcp.so index the project/MCP surface. These
indexes are useful for discovery but may cache older README/tool counts.

## Name collision

`@perp/cli@0.2.6` is unrelated: it is the historical Perpetual Protocol CLI.
Search pipelines should explicitly exclude it when inventorying HypurrQuant's
`perp-cli`.
