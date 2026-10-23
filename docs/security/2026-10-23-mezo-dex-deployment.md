# Mezo DEX deployment — 2026-10-23

Source `e80474ea5121532cde2c470a4db399d4e1427baf` is deployed at https://liqvera.site. All seven services are healthy. The wallet-free preview renders Mezo DEX vs Hyperliquid at block **16321216**; its published JSON/ZIP digests match the source pins and the downloaded ZIP reproduces in the deployed report image with networking disabled.

## Source and runtime

| Service | Exact current image |
| --- | --- |
| web | `sha256:b4156c28fa5abb10c846869d3819105bc382a7da703b00653ad6c3afe03e1cc8` |
| edge | `sha256:aa8f036c87fd1f83aec1618205864fac968ac645882c493c74bcb07d5f7a601c` |
| gateway | `sha256:5248627d05a881606e27f9dca701ecbb794badcf9723025f36de0a5fe73c0b0c` |
| gateway-net | `sha256:a341fae9c0c8a1feade5b11493b58dbeb1a4f22cad5e5b79ef4602dd5b7db901` |
| postgres | `sha256:ac94c2b07e35f5f12172a07ba198a7bcd221a90d149122bc9900771d467733ec` |
| report | `sha256:02839715795594d45af915ee9b19ea8263bad0936967f6c0738f75dcd3140339` |
| evidence-capture | `sha256:45c2f9324c090db3c206d16e5fe586492af234b3fdec19866eb20a9181982d15` |

Only capture, report, gateway and web were replaced. PostgreSQL, edge and the namespace carrier retain their identities. The active Testnet database, retained Mainnet data, capture/evidence volumes, merchant configuration and public WalletConnect bytes are preserved. Ledger aggregates remain three CONFIRMED attempts, one MANUAL_REVIEW, four receipts and four entitlements; migration 001–008 hashes are unchanged. No migration, database restore, new payment or grant renewal occurred.

## Verification scope

- [Exact-head CI](https://github.com/Dimkox/liqvera/actions/runs/39986859564) passed: 1021 Python tests and 85 subtests, with two live tests deselected; 107 browser tests. Gateway passed 74 locally against a disposable PostgreSQL; hosted CI passed 61 and explicitly skipped 13 database cases.
- Published Chrome checks at 320 and 1280 pixels show the DEX panel, pinned pool/router/block links, no horizontal overflow and no runtime exceptions. [Screenshots and measurements](../competition/2026-10-23-mezo-dex/published-browser.json) are current published checks, without wallet pairing or signing.
- Fresh image-bound Trivy scans have zero findings. Grype retains 18 raw occurrences, all explicitly dispositioned: CPython/BusyBox backports, unrelated Ada.cx versus ada-url metadata, and inactive curl in the static nginx runtime. The curl High finding is a configuration disposition, not a patch or zero-raw claim. The musl and nginx package findings were corrected before rollout.
- Capture/report/gateway filesystems and runtime configurations equal the preceding tested candidates apart from source labels. Their prior runtime regressions are retained as inherited evidence. Web binary, entrypoint and nginx configuration hashes also match; static preview files changed. This is an incremental four-image verification, not a new full-fleet audit.

## Mixed CDN assets: failed first attempt and correction

The first rollout failed its public ZIP digest check. Cloudflare served the new JSON but the exact old ZIP from its four-hour cache. Saved origin responses match the new pair. The reviewed compatible recovery retained new gateway/report readers, disabled DEX capture, restored the preceding capture/web and preserved all data. A direct external ZIP diagnostic timed out with a partial file; it is retained as a failure.

The successful retry serves both assets from `/demo/snapshots/d58728bd3df4b79c43bb2e742225e5b8f879eb0ec292213ffd3941f0f8778753/`. The source retains the mutable alias and the previous report byte-for-byte. Both snapshot files were checked publicly after rollout, then the downloaded ZIP reproduced offline.

Historical payments remain the payment evidence for this update at the owner’s request. No fresh signed-payment acceptance, overall A01–A32 pass, Trove API/UI deployment or registry contract is claimed.

## Recovery and evidence

A fresh coherent PostgreSQL/artifact/capture backup was validated before each attempt; private backups and all original/candidate containers remain retained. Recovery never restores a database dump. After possible public exposure it preserves new readers, disables DEX capture and restores compatible capture/web so new paid entitlements remain readable.

Current reviewed recovery command:

```sh
python3 /home/pall/.local/state/liqvera/recovery/2026-10-23-mezo-dex-e80474e/rollout.py rollback
```

[Machine-readable record](2026-10-23-mezo-dex-deployment.json) and [raw evidence](2026-10-23-mezo-dex-deployment-raw.tar.gz) retain the failed diagnostic, exact image/scanner bindings, independent reviews, recovery scripts and published checks. Archive SHA-256: `1a55f2290f8d8ab80afeaa1905db8d498d68463fe409d83d70198e1fc32d1df3`. All 40 payload member digests were verified. Private manifests, credentials, browser profiles, database dumps and scanner caches are excluded.
