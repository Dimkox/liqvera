# Wave 1 browser deployment — 2026-10-21

Application source `9ca9ceda79fbce07b9b9bfb1dcc174d4c300b863` from [PR #14](https://github.com/Dimkox/liqvera/pull/14) is deployed at https://liqvera.site on claw. Browser image: `sha256:de0e5216443ac6a51c5e0c63e5ee45b416f57ced9590943161f8addcbc7ecbcd`. Entry asset: `index-Dd1iIief.js`. Only the browser container was replaced; all seven service containers are healthy. The gateway remains Testnet 31611, live-public, payment-ready, at 0.01 test MUSD.

## Verification

- Complete `make verify PYTHON=.venv/bin/python`: 951 passed, 85 subtests passed, including the four Docker Compose cases unavailable in the original implementation environment.
- Web: 102 tests pass; Testnet and Mainnet production builds pass.
- Gateway: all 71 tests pass, including 13 cases against a new disposable PostgreSQL database. Production databases were not test targets.
- Exact browser Docker build, artifact checks and documentation links pass.
- Five recovery fault-injection cases and a real Docker replacement/rollback rehearsal pass.
- The coherent PostgreSQL dump was restored into a disposable database; aggregate payment states and migration hashes match.

Initial Python verification encountered an A07 nested build timeout under host load. Its focused rerun passed; a second full attempt was interrupted after reproducing the timeout. The subsequent complete run passed in 421.78 seconds without application changes. Earlier logs remain in the evidence archive and are not represented as passes.

Published-origin Chrome at a mobile viewport confirms the funding panel is present and guarded before a wallet/quote, historical preview rendering, AppKit wallet selection and QR generation, and WalletConnect relay HTTP 101. No browser exception or CSP violation was observed. Public-origin responses were fetched through the environment HTTPS proxy; SDK connections were direct. The check made no POST requests to Liqvera and created no quotes or payment submissions. Physical mobile pairing, live wallet balance observation, external borrowing and a new paid purchase remain outside this acceptance.

The unchanged public evidence ZIP reproduces offline with `INTEGRITY_REPRODUCED` and `VALID_FOR_SNAPSHOT_CALCULATION`. Report SHA-256: `0ebf36b89bda183b99767cd7fedc3c956405ef4a3f195d9d73b911d2c146ccf2`; ZIP SHA-256: `3255a42c210c6fe6ad0020c34113988da3f1659c566a73b7729606ad65d083b0`. Reproduction does not authenticate the exchange or confer execution authority.

## Security scope

Both npm audits report zero. Fresh exact-browser Trivy reports zero; Grype reports nine unsuppressed package matches. Its isolated database checksum is valid. All nine have reviewed dispositions, retained in [the machine-readable record](2026-10-21-wave1-deployment.json):

| Matches | Disposition and limit |
| --- | --- |
| Five nginx matches, including three Critical | Configuration-bound non-applicability: constant paths without affected map/alias/rewrite expressions; no SSI/AIO, nginx HTTP/3 proxy, or nginx TLS/session-ticket configuration. Caddy terminates TLS. |
| One curl High match | The affected HTTP/2 upload code is not called by nginx, entrypoints or health checks; nginx has no libcurl linkage. |
| Three BusyBox matches | The exact binary matches the reviewed backport SHA; all eight non-root regressions pass. |

nginx 1.30.5-r1 and curl 8.22.0-r0 are version-affected packages, not newly patched packages. Reassess applicability if configuration, linkage, entrypoints or network placement changes. Independent read-only review found no remaining blocker. The [official nginx advisories](https://nginx.org/en/security_advisories.html) and [curl advisory](https://curl.se/docs/CVE-2026-92392.html) were consulted. Unchanged runtime services retain their earlier image audits; this record is not a fresh whole-stack scan.

## Preserved state and recovery

WalletConnect configuration remains at `/home/pall/.local/share/liqvera/deploy/walletconnect.env`, variable `LIQVERA_WALLETCONNECT_PROJECT_ID`; its bytes are unchanged and the exact browser contains the owner configuration. The edge retains its source-bound Caddy policy. Active Testnet volume `liqvera-live_postgres_data`, retained Mainnet volume `liqvera-live_mainnet_postgres_data_6ee3bbe_final`, capture/artifact volumes and TLS state are preserved.

The ledger before and after rollout has three CONFIRMED attempts, one MANUAL_REVIEW attempt, four receipts and four entitlements. Migrations 001–008 retain their hashes. The gateway was gracefully drained, then report/capture writers frozen for the coherent backup; the same containers resumed. This backup interruption took 38.41 seconds. No migration, grant renewal or payment submission was performed.

Private recovery files are under `/home/pall/.local/state/liqvera/recovery/2026-10-21-wave1-9ca9ced/` (mode 0700). They include the prior manifest, retained public build configuration, PostgreSQL dump and artifact/capture archives. None are in this repository. The previous stopped browser is `liqvera-live-web-live-1-before-wave1-9ca9ced`, image `sha256:e4a2aeb5f71bcb74d747b746b9a83571e3d8ddf93d2e9ccbc26868aa597ee3f9`.

Run the retained reviewed recovery command only when rollback is intended:

```bash
python3 /home/pall/.local/state/liqvera/recovery/2026-10-21-wave1-9ca9ced/rollout.py rollback
```

It restores the prior browser and manifest without restoring a database or applying migrations. The actual live deployment did not need rollback. Disposable validation containers were removed; retained live rollback containers and images remain.

## Evidence

[Summary and archive hashes](2026-10-21-wave1-deployment.json) bind the [raw archive](2026-10-21-wave1-deployment-raw.tar.gz) to this source and image. It contains selected tests, unsuppressed scans, sanitized browser results, build binding, recovery/review records and public operations scripts. Private configuration, dumps, browser profiles, pairing values and vulnerability database caches are excluded. Original implementation evidence and earlier deployment records remain immutable.

