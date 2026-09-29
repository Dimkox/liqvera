# F7 live acceptance and release data/security analysis

Route: `337ef5ec16a0`
Role: `data_architect`
Observed subject: HEAD `fe99c7d6a081ef503ddb8b98e22b2167ac8db38c`
Disposition: local runner and release-integrity repairs are bounded and appropriate. Live payment and publication are **not currently executable** and must remain behind their named human gates.

## Critical pre-live ruling

The current tree cannot safely perform A13/A14 even if wallet, RPC, facilitator, and test MUSD become available:

- production startup wires `unresolvedIdentity` and `unresolvedFinality` into both the receipt reader and `OfficialX402` (`apps/mezo-gateway/src/main.ts:8,20-24`);
- those policies have `reviewed:false`; identity throws and finality always returns false (`apps/mezo-gateway/src/adapters/x402.ts:10-18`);
- the browser contains only an interface/test seam and no registered production payment adapter (`apps/mezo-web/src/x402.ts:5-39`);
- gateway readiness is intentionally false while these blockers remain.

Therefore the route must be phased. Runner repair, deterministic local cases, version/release planning, and artifact construction may proceed locally. A live testnet transfer requires a separately reviewed concrete authorization-identity policy, finality policy, browser adapter, full local/fake fault coverage, current security review, and an exact short-lived approval naming network, token, payee, buyer, amount, maximum number of submissions, and evidence destination. Availability of ambient credentials is not approval. This analysis did not inspect any secret or external system.

## Runner semantic and immutability repairs

The preceding local analysis reproduced two schema defects: the published schema accepts `overall_status: PASS` with thirty duplicate `A01/NOT_RUN` rows, and accepts `FAIL` without execution evidence or an omission. Existing focused tests pass but do not cover these semantics.

The implementation owner should add one semantic validator used by both producer and consumer:

1. require exactly one row for every A01–A30 in canonical order;
2. derive, never trust, overall status: any `FAIL` means `FAIL`; all thirty `PASS` means `PASS`; otherwise `INCOMPLETE`;
3. `PASS` requires an executed command, zero exit, start/end, stdout/stderr hashes, at least one retained evidence object, and no omissions;
4. `FAIL` requires an attempted command plus stable failure/timeout information; setup failure is runner exit 2, not a fabricated case row;
5. `NOT_RUN` means no assertion was invoked; `BLOCKED_EXTERNAL` names a specific policy/availability blocker and does not imply a failed external probe;
6. validate the final document against JSON Schema and semantic rules before atomic publication.

Repository identity is currently checked only before assertion commands. Before sealing, recalculate and require the same origin, HEAD, tree, and clean worktree. Any assertion-created tracked/untracked path, moved HEAD, or dirty submodule aborts publication.

Evidence files are presently hashed when admitted but not re-hashed after all cases. Require a unique evidence path per passing case, reject the final output path and runner temporary namespace as evidence, and perform a final size/hash/regular-file/no-symlink pass immediately before result publication. Bind each evidence document to case ID, assertion, exact subject commit, and exact subject tree.

## Out-of-tree result boundary and final-commit binding

Acceptance execution must use a fresh `0700` directory outside the repository. The plan, assertion outputs, sanitized evidence, result JSON, manifest, and checksum sidecars belong there. This avoids the circular condition where writing a result inside Git makes the supposedly clean subject tree dirty.

The acceptance result is evidence **about** its recorded subject commit/tree. If a copy is later committed, that later report-bearing commit does not retroactively become the tested subject. For release, use this sequence:

1. produce and commit all code, version, README, and release metadata;
2. verify/review that clean candidate commit;
3. run acceptance out-of-tree against that exact unchanged commit;
4. final-recheck commit/tree/clean status and seal result/evidence manifest;
5. tag exactly that subject commit;
6. build artifacts from a clean archive/worktree of that same commit;
7. checksum artifacts and compare reconstructed source tree to the tag commit;
8. only then, under explicit publish approval, push the commit/tag and create the release.

Do not amend the subject commit after acceptance. Any code, version, README, build script, or release-metadata change makes the result stale and requires the full final cycle again.

## Testnet receipt identity and no-duplicate-settlement proof

A13 PASS needs sanitized public evidence for exactly one canonical MUSD `Transfer`: Mezo Testnet `eip155:31611`, pinned MUSD address, amount `10000000000000000`, buyer distinct from merchant, transaction hash, canonical block hash/number, and log index. The receipt must also bind quote ID, report ID, report SHA-256, payment-attempt ID, payer/payee, authorization identity/version, finality-policy version, and observed confirmation time. A matching Transfer alone is insufficient; `MezoReceiptReader` already acknowledges this (`mezo-rpc.ts:48-56`).

Before live eligibility, the concrete identity policy must demonstrate scheme-specific canonical identity, nonce/replay domain, quote association, chain correlation, validity horizon, and exact transfer binding. The concrete finality policy must define its block/canonicality threshold and reorg response. Neither may be toggled by environment alone.

Exactly-once charging is a behavioral claim, not just a database uniqueness claim. The bounded live run must enforce an operator-side submission budget of one and retain:

- pre-run quote/attempt state and zero-settlement counter;
- one durable `SUBMITTING` boundary before the sole settle call;
- facilitator result as a transaction hint, not confirmation;
- canonical receipt plus entitlement commit;
- repeat report and bundle reads using the same receipt with settlement counter still one;
- duplicate signature/idempotency/reload attempts rejected or recovered without another settle;
- post-run reconciliation showing no eligible second attempt.

If submission outcome is unknown, tx hash is absent, receipt binding is ambiguous, or logs conflict, stop. Preserve `UNKNOWN`/`MANUAL_REVIEW`, perform confirm-only reconciliation, and do not submit again. Such a run is `FAIL` or `INCOMPLETE` for A13/A14, never retried into a convenient PASS.

The current persistent uniqueness and transaction design supports these goals, but production `MANUAL_REVIEW -> CONFIRMED/PAID` recovery remained a documented F5 residual. Resolve or explicitly block the live run; do not discover it with funds.

## Logs, redaction, and evidence handling

Gateway logging uses an allowlist projection and excludes bodies, URLs, wallet data, capabilities, authorization identity, and payment values (`security/observability.ts:28-36`). HTTP middleware logs request ID/status/duration only (`security/middleware.ts:13-23`). This is a good baseline, not complete live proof.

Before a live gate, deterministic canary tests must cover gateway stdout/stderr, reverse proxy access/error logs, browser console/network export, assertion subprocess output, acceptance JSON/evidence, and release artifacts. Prohibit raw:

- Authorization/capability and `PAYMENT-SIGNATURE` headers;
- decoded x402 payloads and signatures;
- private keys, seed phrases, wallet session exports, database/report tokens;
- cookies, participant email, and RPC/facilitator credentials;
- environment values and command-line secret arguments.

Acceptance result may retain environment **names**, never values. Public tx/block hashes, log index, public buyer/payee addresses, amount, and network may be retained only in sanitized A13/A14 evidence. Do not persist facilitator request/response bodies merely to prove the call. Assertions should emit structured observations and hashes; raw secret-bearing streams must be discarded securely after redaction verification.

Evidence output must be created exclusively, not overwritten; use deterministic per-case filenames and a manifest with path, size, SHA-256, case ID, subject commit/tree, and media type. After sealing, make the local set read-only and verify it again before attaching any public subset.

## Release 0.0.1 version and artifact integrity

There is currently no tag. However, existing metadata is root `0.1.0.dev0` and component `0.1.0`; changing metadata to `0.0.1` is a semantic version **downgrade**, not a normal release promotion. Internal Python dependencies also pin sibling packages at `==0.1.0`, and npm lockfiles repeat `0.1.0`. Before editing, the scope/design gate must explicitly choose one coherent interpretation:

- tag/release `v0.0.1` while preserving component package metadata and clearly documenting the distinction; or
- approve a coordinated metadata downgrade to `0.0.1`, update every internal exact dependency and lockfile coherently, and prove clean wheel/npm installs.

Do not partially change only README or root metadata. A single machine-readable release manifest should enumerate the selected release version, exact Git commit/tree, every Python wheel/sdist/web/gateway/source artifact, size, SHA-256, build command identity, and acceptance-result/manifest SHA-256. Generate `SHA256SUMS` from final bytes using stable filenames, then verify it from a fresh directory. Do not include private env files, evidence working directories, node_modules, database volumes, browser profiles, wallet material, or unredacted logs.

Minimum artifact checks:

- archive members are relative, normalized, duplicate-free, bounded, and contain no symlink/device/path traversal surprises;
- wheel metadata/version/internal requirements match the approved version decision;
- npm package and lockfile root versions agree;
- web bundle contains no secret canaries, localhost-only debug endpoints presented as production, source maps unless explicitly approved, or wallet/payment test adapters;
- source archive expands to the exact tagged tree under an explicit export policy;
- all checksums are recomputed after upload/download before a release claim;
- GitHub release targets exact `v0.0.1` commit and attaches only manifest-listed bytes.

A release may truthfully carry `INCOMPLETE`, `NOT_RUN`, and `BLOCKED_EXTERNAL` limitations, but it must not call payment working if A13/A14 are not PASS. Publication approval does not waive acceptance or payment gates.

## Gate matrix

| Phase | Permitted now | Required before crossing |
| --- | --- | --- |
| Runner/schema/fault repair | local files and tests only | approved exact scope digest |
| Local A01–A30 eligibility | out-of-tree temp evidence, no network | clean final subject commit and deterministic plan |
| Public read probes | none from this analysis | explicit external-write/read scope, hosts, limits, timeouts, retained evidence |
| Testnet payment | none | reviewed identity/finality/browser adapters, green fault suite, exact buyer/payee/network/asset/amount/submission-budget approval, test funds only |
| Tag/push/GitHub Release | none | green final verifier and all independent reviews on exact commit; checksum manifest; separate explicit publication approval |

Mainnet, custody, exchange mutation, private venues, real/user funds, withdrawals, unrelated repositories, shared environments, and secret inspection remain forbidden.

## Deterministic tests required before approval

- reject duplicate/missing case IDs and inconsistent overall status;
- reject incomplete FAIL rows and dishonest NOT_RUN/BLOCKED transitions;
- abort when a command dirties the tree, moves HEAD, mutates prior evidence, reuses a path, or aliases the result path;
- validate and re-hash the entire out-of-tree evidence set after all cases;
- prove A14 cannot pass without the exact passing A13 tx and settlement count one;
- prove unknown/timeout/reload/duplicate flows never invoke settle twice;
- prove receipt mismatch, multiple Transfers, removed log, wrong block/chain/token/amount/payer/payee, and insufficient finality never entitle;
- inject canaries into every permitted input/log boundary and prove absence from result, bundles, logs, and release artifacts;
- build twice from the same clean commit where reproducibility is claimed, compare hashes, and verify checksum corruption/missing/extra artifact rejection;
- prove release manifest commit/tree/version differs by one bit -> rejection.

All tests use fakes/temp files. No database, migration, container, network, wallet, RPC, facilitator, secret store, or external mutation is needed for this analysis or the pre-gate repair.

## Recommendation

Approve a first phase limited to runner semantics, evidence immutability/final binding, local fault tests, release manifest/checksum tooling, and truthful documentation. Keep live-public, testnet transfer, tag/push, and GitHub Release as separate named gates. The current unresolved payment policies and absent browser adapter are hard blockers, not configuration tasks; release them only through reviewed code and exact evidence, never by bypass or fabricated PASS.
