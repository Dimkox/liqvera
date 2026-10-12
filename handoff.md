# Liqvera handoff

## 2026-10-12 — complete product migrated; final independent image audit in progress

Baseline: origin/main `97484401d50fa3fb28ebd813cc8320e7e51c72f5`, after published v0.0.5. The earlier cleanup branch started from stale F1 and its whole-product conclusions are withdrawn. Full web, gateway, payments, reports and installer remain present. No live deployment, payment, database or grant change has been made.

The [baseline CVE/runtime report](docs/security/2026-10-12-baseline.md) binds fresh OSV/npm/Trivy findings to source and exact running images. Public landing and historical report returned 200; gateway health/readiness returned 502 and its container logged STARTUP_FAILED. The sanitized log does not establish a root cause.

Current changes remove obsolete delivery tooling, private-host automation and inherited research. Four Python packages/imports/CLIs and active schema/configuration names migrate to Liqvera 0.2.0. Immutable preview assets, SQL migrations, published installer image lock and third-party attribution retain original bytes. Existing persisted state needs its matching version or a separately reviewed migration.

Verification: full Python suite 1167 passed plus 85 subtests; gateway 51 local tests and 7 additional disposable-PostgreSQL tests passed; browser 27 tests and production build passed. Installer/operations checks passed (203 tests). Ten focused source-identity, fresh-wheel and namespace tests passed after build-helper fixes. Documentation links and lint passed. Six isolated fixture services started; the canonical report was generated and its bundle reproduced offline. Real headless Chrome rendered the hash-verified historical preview without runtime exceptions and kept fresh requests disabled without a wallet. Fixture payment readiness correctly remains false. Historical acceptance remains 9 PASS and 21 NOT_RUN; no overall acceptance PASS.

Dependency fixes: npm audits and Python audits against both PyPI and OSV report no vulnerabilities. Five rebuilt application/database images have zero Trivy findings. The standard Caddy build now uses Go 1.27.2, x/net 0.61.0 and x/crypto 0.58.0; its 18 CVE findings are gone. Raw Trivy and Getzilla OSV retain GO-2026-5932, an unmaintained OpenPGP package advisory without a fixed release. Source-level govulncheck finds only a module match, no imported vulnerable package or reachable symbol; binary confirmation and independent Grype image scans are pending. No ignore rule has been added. Caddy configuration, all 135 standard modules, non-root fixture startup and browser smoke passed after replacement.

Independent read-only review found no remaining Critical/Important issue after restoring byte-identical historical SQL and fixing build isolation/download handling. Go edge build and govulncheck were added to CI in response to its coverage observation. Next: build clean-commit artifacts and the two standalone Python images, finish independent image/binary scans, persist exact image IDs and final results, then remove only audit-owned test resources. Public deployment remains unchanged and its observed gateway failure is not fixed by these source changes.

Reference plan: [current cleanup](docs/superpowers/plans/2026-10-12-standalone-current.md). Prior release evidence is retained in Git at v0.0.5 and the published assets.
