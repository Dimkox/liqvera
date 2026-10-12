# Liqvera security remediation — 2026-10-12

The complete application at source commit `76b63ecaa5782614435850b1cfbda80ac02684eb` was rebuilt and checked locally. All identified applicable findings in the audited dependency and image scope have been remediated. Raw scanners still report version-based matches for backported fixes and two unrelated or absent components; this is not a claim that every vulnerability database returns zero.

The baseline is the complete post-v0.0.5 application at `97484401d50fa3fb28ebd813cc8320e7e51c72f5`, not the earlier F1 cleanup branch. The [baseline report](2026-10-12-baseline.md) records the original findings and public runtime observations. No deployment, live database change, grant renewal or new payment was performed. The observed public gateway 502 remains outside this completed local remediation.

## Evidence and scope

- [Machine-readable results](2026-10-12-remediation.json): exact image IDs, versions, findings, functional results and evidence hashes.
- [Image-bound VEX dispositions](2026-10-12-remediation-vex.json): fixed and not-affected findings, without scanner ignore rules.
- [Raw evidence archive](2026-10-12-remediation-raw.tar.gz): unsuppressed scans, regression results, test logs and local functional evidence. SHA-256: `44bb03181bb3189c96bc61b5fc71edb1af619f27a6ef8bfb07c447713c3e318b`.
- [Independent review](2026-10-12-review.md): findings and subsequent fixes.

Eight locally built `linux/amd64` runtime images were scanned, including the standalone capture/analyzer, PostgreSQL and edge proxy. This evidence does not apply to older published installer images or unchanged production containers. Dependency databases are time-bound and cannot prove the absence of unknown vulnerabilities.

| Check | Database or version | Result |
| --- | --- | --- |
| External Getzilla / OSV | Getzilla `540c12f`, online OSV | 231 pinned dependencies, zero findings |
| Python pip-audit | PyPI and OSV, separately | Zero findings in the installed dependency closure |
| npm audit | Both current application lockfiles | Zero findings |
| Trivy | 0.74.0; DB updated 2026-10-12 13:18 UTC | Seven images zero; edge has one module-only advisory |
| Grype | 0.120.1; DB v6.1.10 built 2026-10-12 06:45 UTC | 33 raw package/advisory matches, all explained below |
| govulncheck | 1.9.0, final Caddy binary | Zero affected symbols or imported packages; one containing-module match |
| CISA KEV | Catalog 2026.10.08, 1,739 entries | No match among the four CVE IDs remaining in raw image results |

CISA comparison is limited to those remaining IDs. Grype's NVD matching is independent of Trivy's Alpine advisory feed; it exposed additional real issues that were then fixed.

## Remaining raw matches

| Image | Trivy matches | Grype matches |
| --- | ---: | ---: |
| Capture service | 0 | 5 |
| Report service | 0 | 5 |
| Gateway | 0 | 4 |
| Web | 0 | 3 |
| PostgreSQL | 0 | 3 |
| Edge | 1 | 3 |
| Standalone capture | 0 | 5 |
| Standalone analyzer | 0 | 5 |

**CVE-2025-60876 — fixed in all eight images.** BusyBox was rebuilt using the pinned Alpine recipe plus the [upstream-reviewed URL guard](https://lists.busybox.net/pipermail/busybox/2025-November/091840.html). The injection was reproduced before patching. All eight targeted regression cases pass; all 304 applets remain. Each final image contains the same patched binary, SHA-256 `4261945c0287000d3e73548d381a5afa4279eb07ed6e223ee6c5c51ba39f1642`, and corresponding source/license. NVD still matches the unchanged versions of `busybox`, `busybox-binsh` and `ssl_client`, producing three matches per image. The original recipe's static utmps/skarnet relink is preserved. This is targeted regression evidence, not a claim that the entire upstream BusyBox suite was run.

**CVE-2025-15367 and CVE-2026-12345 — fixed in all four Python images.** Exact CPython production backports reject POP3 control characters and close the TemporaryDirectory/shutil symlink race: [POP3 upstream commit](https://github.com/python/cpython/commit/b234a2b67539f787e191d2ef19a7cbdce32874e7), [Python 3.14 cleanup-race backport](https://github.com/python/cpython/commit/58ed0259cae509a19138795df302fe60b544dc74). Non-root reproductions fail before patching and pass in each final image. Versions remain 3.14.8, so CPE matching still reports both advisories. Patch and resulting module hashes are checked during builds.

**CVE-2024-9410 — not applicable to the gateway.** The [vendor research](https://www.tenable.com/security/research/tra-2024-41) concerns Ada.cx Sentry configuration. The installed `ada-libs` is the unrelated [ada-url C++ parser](https://github.com/ada-url/ada). The affected product is absent.

**GO-2026-5932 — affected code absent from the edge.** The [Go advisory](https://pkg.go.dev/vuln/GO-2026-5932) concerns `golang.org/x/crypto/openpgp`. Standard Caddy does not import or link that package. Final-binary govulncheck reports zero affected symbols and zero affected imported packages; Trivy matches only the containing module.

No advisory suppression or fabricated package version was used. Backports and their removal criteria are maintained under [deploy/security](../../deploy/security/README.md).

## Other changes

Python runtime images use pinned 3.14.8 Alpine bases, patched OpenSSL 3.5.9 and zlib 1.3.2; runtime pip/ensurepip are removed. Gateway uses Alpine Node 24.18.1 LTS dynamically linked to system OpenSSL 3.5.9. Updating Alpine packages alone did not replace the older OpenSSL embedded in the official Node image. See the [OpenSSL advisory](https://openssl-library.org/news/secadv/20260929.txt).

Unused vulnerable nginx modules, PostgreSQL gosu and edge curl/libcap were removed. npm closures and development dependencies were updated. Upstream Caddy 2.11.7 is built with Go 1.27.2, x/net 0.61.0 and x/crypto 0.58.0. There is no Go application, `.go` source, `go.mod` or `go.sum` in Liqvera; the Go compiler is used only inside the upstream proxy build stage.

## Working-product verification

- Final host `make verify`: **1,167 tests and 85 subtests passed**. Installer and operations checks are included.
- Final Node 24 gateway: **51 local tests plus seven fresh disposable-PostgreSQL tests passed**. Browser: **27 tests and production build passed**.
- Python 3.14 non-root runtime: 786 tests and 85 subtests passed; one system-interpreter case exposed an environment-selection bug, was fixed, and passed separately. The final host suite includes that fix. An earlier root/Alpine full-suite attempt was unsuitable for Ubuntu installer/permission checks and is not presented as passing.
- Clean-commit wheel and standalone image builds passed. Standalone capture/analyzer run successfully; the deliberately short fixture correctly returns `INSUFFICIENT_EVIDENCE`.
- All six isolated fixture services were healthy on the exact audited image IDs. Canonical report creation returned 200; its exported ZIP returned `INTEGRITY_REPRODUCED` with network disabled and read-only verification.
- Headless Chrome displayed the hash-verified historical preview with zero runtime exceptions. Requests remained disabled without a wallet. Fixture `/healthz` returned 200; payment `/readyz` correctly returned 503 with no payment authority.

These checks establish local functionality and preserve payment safeguards. Historical live acceptance remains **9 PASS / 21 NOT_RUN**. They do not establish current production uptime, a new settlement, or full live acceptance.

Audit-owned fixture and database containers, networks, volumes and the temporary loopback relay were removed after verification. Candidate images and build artifacts were retained.

## Recheck

Use the commands in [validation](../validation.md), scan exact built image IDs with refreshed Trivy and Grype databases, and rerun the regression scripts in `deploy/security`. Compare raw matches against the exact image-bound VEX; rebuilding or changing a component requires fresh evidence. The JSON report records all archive member hashes for independent integrity checks.
