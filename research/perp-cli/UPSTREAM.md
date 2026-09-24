# Upstream source pin

Authoritative source snapshot:

- repository: `hypurrquant/perp-cli`
- branch observed: `main`
- commit: `ed94cfd46259ff9186bf4f2489252a4f8f773e31`
- package version field: `0.13.0`
- license: MIT

The upstream TypeScript source is already public. It is intentionally not
vendored into this repository; `scripts/fetch_sources.py repos` reproduces the
exact public Git checkouts under ignored `artifacts/repositories/`.

Third-party mirror pin:

- repository: `iflow-mcp/hypurrquant-perp-cli`
- commit: `cae9101d182407d684d6c557db8d4b1947d90ffa`
- observed package version field: `0.9.8`

This mirror is preserved for provenance comparison only and is not treated as
a source of truth for current behavior.
