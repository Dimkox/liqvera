# Funding layout deployment — 2026-10-21

The desktop/mobile funding layout repair and Getzilla footer link from source `57660040b36300de62cd45cb663bd2124167fe45` are published at https://liqvera.site on claw. Image: `sha256:e824dfe58616166fcabbe973b140be27857d7dbb3113fa501296488610527e0f`; entry: `index-Cnfn94HM.js`.

The former inline padded link overlapped its acknowledgment and the following terms link. Explicit grid rows now preserve 14-pixel gaps. Before/after browser measurements reproduce and resolve both overlaps at 320, 390, 768, 1024, 1280 and 1440 px. The published page passes the same checks without overflow or exceptions. The footer links to https://github.com/Dimkox/Getzilla. The acknowledgment remains disabled until a fresh balance observation proves a shortfall for an unpaid quote; guidance now explains the prerequisite. Unknown payment guards are unchanged.

All 104 web tests and the Testnet build pass. Two guidance regressions failed before the fix. Independent read-only review found no remaining UI blocker. Public mobile Chrome confirms historical preview, AppKit QR and WalletConnect relay HTTP 101, with zero CSP violations or browser exceptions. Public-origin requests are GET-only; no live quote, payment or loan was created. Physical wallet pairing and live shortfall interaction were not performed.

Only the web container was replaced; all seven services are healthy. WalletConnect configuration bytes, Caddy policy, volume bindings, migration hashes and historical preview hashes remain unchanged. The ledger remains three CONFIRMED attempts, one MANUAL_REVIEW attempt, four receipts and four entitlements. A fresh coherent PostgreSQL/artifact/capture backup was validated with archive integrity and pg_restore listing; the writer interruption lasted 7.76 seconds. The preceding deployment's separate disposable restore and rollback rehearsal remain historical evidence, not a claim that this new dump was restored again.

Fresh exact-image Trivy reports zero matches. Grype reports the same nine unsuppressed matches as the preceding browser. Runtime BusyBox/nginx/curl binaries, effective nginx configuration and linkage are unchanged; the [preceding reviewed dispositions](2026-10-21-wave1-deployment.md) remain applicable. nginx/curl package versions themselves are not newly patched. The separate full Getzilla audit includes inherited Python/runtime findings and is not certified clean by this web rollout.

Private recovery directory: `/home/pall/.local/state/liqvera/recovery/2026-10-21-layout-5766004/` (0700). Previous stopped container: `liqvera-live-web-live-1-before-layout-5766004`; previous image: `sha256:de0e5216443ac6a51c5e0c63e5ee45b416f57ced9590943161f8addcbc7ecbcd`. The preceding recovery generation remains retained.

```bash
python3 /home/pall/.local/state/liqvera/recovery/2026-10-21-layout-5766004/rollout.py rollback
```

This exact-image guarded command restores the preceding browser and manifest. It never restores a database or applies migrations. Its recovery algorithm is unchanged from the previously reviewed and fault-tested script; only source/image/output/recovery identities and the preceding asset were updated. The live deployment did not require rollback.

[Machine-readable evidence](2026-10-21-layout-deployment.json) binds the [raw archive](2026-10-21-layout-deployment-raw.tar.gz) to source and image. Only selected public operations scripts, sanitized results, tests, scans and non-pairing screenshots are included. Private manifests, backups, configuration contents, browser profiles and pairing values are excluded.
