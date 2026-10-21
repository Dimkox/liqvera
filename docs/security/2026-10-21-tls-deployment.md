# TLS remediation and deployment — 2026-10-21

Application source `1c020995adaa1a80fc8a97888aa838041d8e01d5` is deployed on claw at https://liqvera.site. All seven services are healthy with zero restarts. Six application containers were replaced; the existing PostgreSQL container was retained. The browser still serves `index-Cnfn94HM.js`, including the repaired funding layout, prerequisite guidance and Getzilla footer link.

The four inherited TLS blockers from the [initial negative audit](2026-10-21-getzilla-initial.md) are closed. Independent security review of the frozen successor passes. This does not turn the historical negative report into a passing report, and it does not mean every scanner returns zero. The complete external Getzilla gate still exits 1 for the two non-security categories explained below.

## Security correction and exact images

The [source remediation](2026-10-21-tls-remediation.md) pins certifi 2026.10.19, pip 26.2.2, CA packages 20261020-r0 and the Go 1.27.3 Caddy builder. Node explicitly selects corrected OpenSSL trust, inherited by its gateway child. Python and Node regressions inspect effective CA paths, including additional or lazily loaded stores. CI bootstraps the checksum-bound pip wheel offline before dependency access and constrains both CA lookup paths. Existing BusyBox and CPython backports remain present.

| Service | Exact image |
| --- | --- |
| Capture | `sha256:3edb015ec3aea7235b621303d1a1821eaa7c52b44f8ceb03b50fe51c4c97d5c1` |
| Report/verifier | `sha256:f938d4f3483af7453944ad98de648f9b7a1f6ac4ad3399434069194245d58901` |
| Gateway and namespace carrier | `sha256:a341fae9c0c8a1feade5b11493b58dbeb1a4f22cad5e5b79ef4602dd5b7db901` |
| Caddy edge | `sha256:aa8f036c87fd1f83aec1618205864fac968ac645882c493c74bcb07d5f7a601c` |
| Web | `sha256:6b26f78a2856e7f2f5a07884249d2b45351a08b3160732ef50a5d04967e07a06` |
| PostgreSQL, retained live image | `sha256:ac94c2b07e35f5f12172a07ba198a7bcd221a90d149122bc9900771d467733ec` |
| PostgreSQL, corrected build tested only | `sha256:98e5cab850b96ff1acfaca92834c8590274e62ba9f64b6d882d27ec7f6e090d8` |

The six newly built images carry the exact application source label. The gateway, edge, web and PostgreSQL final root filesystems equal the independently tested candidate filesystems; rebuilt Python images had all runtime regressions repeated. Docker/Trivy index identifiers and Grype OCI configuration identifiers were cross-checked against their manifests and root filesystems. The live database is internal-only and has none of the four reported outbound TLS paths; its updated recipe was built and tested without replacing production PostgreSQL.

Fresh Trivy and Grype scans retain 30 raw occurrences across the six candidate images: 5 capture, 5 report, 4 gateway, 4 edge, 9 web and 3 PostgreSQL. All have reviewed dispositions; zero remain untriaged. BusyBox and CPython matches are covered by the retained backports and exact-binary regressions. The Ada.cx advisory is unrelated to the ada-url parser package. Caddy has no affected OpenPGP symbols; binary govulncheck reports zero affected symbols/packages. The unchanged nginx configuration lacks the features required by its five matches, including the TLS session-ticket finding: nginx has no TLS listener and Caddy terminates TLS. curl is inactive in this web runtime. These configuration dispositions are not claims that nginx/curl packages were patched. Full findings and independent reasoning are retained in the raw archive.

## Verification and external Getzilla result

- Complete Python suite: 955 tests and 85 subtests pass, including Docker configuration checks. The final gate's Python run took 428.79 seconds.
- Web: 104 tests pass; Testnet and Mainnet builds pass. Both web and gateway npm audits report zero advisories.
- Gateway: all 71 tests pass, including 13 real PostgreSQL cases, with zero skips. The database was disposable and isolated; it was removed after validation.
- Six Docker builds, Python/Node effective-trust checks, CPython/BusyBox regressions, Caddy validation, artifact guard and clean wheel builds pass. The historical public evidence ZIP reproduces in the exact final report image with execution authority `NONE`.
- Fresh supplemental OSV/PyPI queries cover 65 Python lock entries / 52 unique versions with zero advisories. The previous certifi version remains a positive control. Getzilla's normal filename discovery omits these `.lock` files, so the supplement is required.
- Four complete analysis reports and five independent read-only review reports are preserved byte-for-byte. Code, tests, security, data and release reviews found no blocking issue in the frozen candidate. Two additional mutation/negative-test coverage opportunities are disclosed in the full reports; independent probes cover the actual trust behavior.

The external tool is Getzilla commit `2bb417431f1e4b9494e4af71ebf27adb1d04d898`, containing merged [PR #115](https://github.com/Dimkox/Getzilla/pull/115). It stays outside the Liqvera runtime and repository policy. Route `b54297afc340` compares against actual Liqvera main `f1d3bffc46fa1459908fdff865fcfbfc831b7f7f`. All five reviews evaluated audit commit `bf569ce96039deeec69e025a3c3cdc9653584b0d`, tree `c4205fabda3d9d34d08058990fca33b0b059f81d`. Only their five full report files were then added, producing final audit commit `b030ab142194bd5c50d2edb38238535567d98bda`, tree `d70205ee88e46e1d98280c989a6be758e5f7f591`. Tracked product bytes equal application source `1c02099`.

One qualifying `--mode pr --full-scope --keep-going --json` run started at 12:29:41 UTC and completed in 447.08 seconds. A preceding launcher preflight detected missing Bandit before invoking Getzilla; its failure is retained separately. The qualifying run covered the complete `tests/` target, used fresh OSV access and preserved a clean, unchanged final audit tree. The clone's secondary `pr-target` discovery selected source `1c02099`; the primary route still selected real main. Their range union contains all 77 changed paths, with no selection findings or omitted product changes.

The raw gate exits 1 for exactly these checks:

1. `git-diff-check`: a blank line in immutable preceding Wave 1 evidence, intentional Markdown hard-break spaces in an unedited analysis report, and a final blank line in an unedited release review.
2. `secret-scan`: two generic-pattern matches on public MUSD token-address constants in test/evidence code. These are not credentials; independent review identifies their public meaning.

Known-vulnerability scanning passes across 476 pinned dependencies, and Ruff, Bandit, OpenGrep, SQL safety, full Python tests, source stability and quality admission pass. Optional unconfigured framework components are explicitly skipped, not represented as executed. No findings were suppressed and no passing final receipt was manufactured. The full run is complete, but Getzilla's zero-gap completion condition is not satisfied. The native gate result must remain distinct from the passing TLS security review.

## Preservation, published checks and recovery

The coherent backup stopped the gateway gracefully and briefly paused report/capture writers for 8.04 seconds. The same original containers resumed before replacement. PostgreSQL dump and artifact/capture backups remain private. A fresh dump restore into the corrected PostgreSQL image on a disposable internal network reproduced all aggregate ledger states and migration hashes; the owned test container/network were removed.

The application replacement completed in 96.86 seconds. Post-deployment comparisons confirm the same PostgreSQL identity, mounts, host configuration and environment except the declared Node trust setting and new report-engine source provenance. WalletConnect bytes and Caddy policy are unchanged. The ledger remains three `CONFIRMED`, one `MANUAL_REVIEW`, four receipts and four entitlements; migrations 001–008 retain their hashes. Existing Testnet/Mainnet volumes, unknown outcomes and sealed evidence are preserved. No quote, payment, loan or grant was created. Normal service startup and existing workers remain enabled; this is not a claim that no database statement ever ran.

HTTPS checks with the corrected CA bundle pass for the page, health/readiness, capabilities, historical report and ZIP. Public capabilities remain Mezo Testnet 31611, live-public, payment-ready, 0.01 test MUSD. The historical report SHA-256 remains `0ebf36b89bda183b99767cd7fedc3c956405ef4a3f195d9d73b911d2c146ccf2`; the ZIP remains `3255a42c210c6fe6ad0020c34113988da3f1659c566a73b7729606ad65d083b0`.

Published Chrome checks pass at 320, 390, 768, 1024, 1280 and 1440 pixels: both funding-control gaps are 14 pixels, no horizontal overflow, Getzilla footer present. The checkbox stays disabled until a fresh unpaid-quote shortfall is established, and its prerequisite is now explained. AppKit renders its QR and receives a relay WebSocket 101 response with no observed exception, CSP violation or relay error. Public application requests were GET-only. Physical wallet pairing, borrowing and a new signed paid delivery were not exercised.

Private recovery directory: `/home/pall/.local/state/liqvera/recovery/2026-10-21-tls-1c02099/`. The six stopped previous containers have suffix `-before-tls-1c02099`. Earlier browser/Mainnet recovery generations are retained. Exact current rollback:

```bash
python3 /home/pall/.local/state/liqvera/recovery/2026-10-21-tls-1c02099/rollout.py rollback
```

The reviewed script is SHA-256 `21211975c0679774958b5801e21e19e6e1f888fbad6c0554088bf85119f7dc4f`; its immutable image binding is `e1c966aa44fd760f5baa26d2108f063c043016c7eec76cd6b2a016b1291b7cf3`. Recovery stops candidate writers before restarting the original dependency sequence and restores the previous operational manifest. It never restores a database dump or runs migrations. Identity guards reject use after an unrelated deployment. Sixty-nine fault-model cases and an actual disposable Docker gateway/namespace-pair rehearsal pass; this is not a production full-stack rollback rehearsal. Retained old images still have their old TLS exposure and must not be described as remediated.

## Evidence package

[Machine-readable record](2026-10-21-tls-deployment.json) and [raw archive](2026-10-21-tls-deployment-raw.tar.gz) bind the images, reviews, gate, backup validation and published checks. Archive SHA-256: `625cd5f517b19b80073530f9ffdba2bfab71f0461050d68d0051be57d0dc8b89`. All 354 payload hashes were verified against its manifest. It includes complete unedited reviews, primary-source snapshots, scanner output, public browser screenshots and the frozen audit Git bundle; the bundle requires application commit `1c02099` as its prerequisite. Private configuration, dumps, grants, browser profiles and scanner databases are excluded. Earlier negative, Wave 1 and layout evidence remain byte-for-byte unchanged.
