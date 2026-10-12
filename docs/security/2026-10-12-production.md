# Production deployment and security audit — 2026-10-12

Six exact runtime images were scanned again before rollout: capture, report, edge and PostgreSQL from the audited `76b63ec` build, gateway rebuilt from `28f9a1c` (also used by the gateway network proxy), and web rebuilt from `f5de466` with the new verified Liqvera preview evidence. The final web image was rescanned after its preview refresh; the other five image IDs remain unchanged. All twelve Trivy/Grype scans completed successfully. There are **no new or untriaged findings**. All seven running containers were checked after rollout against these exact scanned image IDs; all are healthy with zero restarts.

Database refresh succeeded. The providers returned Trivy's database updated `2026-10-12T13:18:23.1639207Z` and Grype schema `v6.1.10`, built `2026-10-12T06:45:22Z`. These are the same current database builds returned earlier today; no newer database was available.

| Image | Trivy raw matches | Grype raw matches |
| --- | ---: | ---: |
| Capture | 0 | 5 |
| Report | 0 | 5 |
| Web | 0 | 3 |
| Edge | 1 | 3 |
| PostgreSQL | 0 | 3 |
| Gateway | 0 | 4 |

The unsuppressed matches have the previously reviewed dispositions:

- `CVE-2025-60876`: BusyBox URL guard backport; three package-name matches per image. Original package versions are retained, so version-based matching remains visible.
- `CVE-2025-15367` and `CVE-2026-12345`: upstream CPython backports in capture/report, with passing non-root regressions in the original exact-image audit.
- `CVE-2024-9410`: Ada.cx service advisory mismatched to the unrelated `ada-url` C++ parser in the gateway.
- `GO-2026-5932`: containing-module match for OpenPGP code absent from the edge binary. The unchanged exact binary was already checked with govulncheck: zero affected symbols and zero affected imported packages.

Fresh package audits also passed: both npm lockfiles report zero vulnerabilities; Python PyPI and OSV each report zero vulnerabilities in 53 environment dependencies; Getzilla's OSV query reports zero findings across 231 pinned dependencies. Those dependency locks are unchanged from the previous audited source. The refreshed CISA KEV catalog (`2026.10.08`, 1,739 entries) contains none of the four remaining raw CVE identifiers. This narrow KEV comparison is not a claim that every possible vulnerability database has been checked or that raw scanner output is literally empty.

[Security details](2026-10-12-production.json) records full exact image IDs, finding details, database metadata, lock hashes and scanner status. The twelve `*-trivy.json`/`*-grype.json` files retain original scanner output without ignore filters. Existing reviewed backport and non-applicability evidence is in `docs/security/2026-10-12-remediation.md` in the repository. The replacement gateway and final web `/bin/busybox` checksums match the reviewed patched binary (`4261945c0287000d3e73548d381a5afa4279eb07ed6e223ee6c5c51ba39f1642`). [Image-bound VEX](2026-10-12-production-vex.json) binds the reviewed dispositions to all six exact deployed image IDs.

## Deployment and functional verification

[Deployment identity](2026-10-12-production-deployment.json) records the seven containers and six exact images. Component sources are `76b63ec` for capture/report/edge/PostgreSQL, `28f9a1c` for gateway and its network proxy, and `f5de466` for the refreshed web preview. The report's embedded engine commit correctly remains `76b63ec`. No SQL migration, volume recreation, grant renewal or payment submission occurred. Post-rollout aggregates confirm six migration records and the one historical MANUAL_REVIEW payment remain present.

The deployed capture/report services generated a new live-public Hyperliquid BTC report. Gateway artifact reads validated its JSON and ZIP digests. The [build result](2026-10-12-production-live-report.json) and [offline verification](2026-10-12-production-offline-verification.json) record `INTEGRITY_REPRODUCED`, with networking disabled and a trusted report digest. An initial verifier invocation could not read the host-exported file as its non-root UID; making this public test artifact readable corrected the invocation. The public preview publishes this new report, without rewriting earlier sealed evidence. All 27 web tests and the production browser build passed; independent review found no preview blocker.

[Public HTTPS checks](2026-10-12-production-public-checks.json) record successful endpoint status and exact downloaded hashes. Headless Chrome rendered the new preview with no runtime exceptions. Direct audit-host egress stalled on larger responses; the configured HTTPS proxy completed all checks. New payments remain unavailable; `/readyz` reports their blockers. This is a Mezo Testnet deployment, chain 31611, and does not claim mainnet or fresh paid acceptance.

## Recovery

The private operations manifest is `/home/pall/.local/share/liqvera/deploy/compose.json`, mode 0600. It references existing external volumes and networks and the exact deployed image tags. Coherent pre-rollout backups are in `/home/pall/.local/state/liqvera/recovery/2026-10-12-production/`; their contents are not committed. Previous containers are stopped and retained except the web rollback container, which Compose removed during the preview refresh. Its previous image remains available for restoration using the current web configuration. Older images contain known vulnerabilities. Preserve ledger and artifacts together; never recreate their volumes during rollback.

## Raw evidence

[Raw scanner archive](2026-10-12-production-raw.tar.gz): 46 members, SHA-256 `1ae7baec0677184cc0c0d3f9edace1159d929d6c0a32ab1d3d9518209239a967`. The archive manifest and all member hashes were verified. It preserves unsuppressed outputs; the VEX covers all 24 scanner occurrences, rather than hiding version matches.
