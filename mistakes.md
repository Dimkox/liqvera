# Mistakes

Root causes, not symptoms. Record only mistakes that caused a real problem.

## 2026-08-18 — Treated research completion as Git publication

**Symptom:** The Kakao/Korea research session was presented as delivered even though no repository file, branch, commit or PR existed.
**Root cause:** Completion was inferred from the research tool output instead of verifying the target repository, canonical path, inbound links and remote SHA. Publication work is complete only after the file is readable from the intended Git ref and the commit/PR state is verified.

## 2026-08-17 — Treated the plan's `go test` step as executable policy

**Symptom:** Go 1.26.5 was installed and five Go analysis agents were launched, then killed.
**Root cause:** The M0-M3 task file was read as the run contract. Owner policy (hypotheses only in Python) was not applied before spawning agents or fetching a toolchain.

## 2026-08-17 — Dropped a non-graph YAML into architecture/

**Symptom:** `GraphLoadError: repository manifest set is invalid (unexpected: conformance.yaml)`.
**Root cause:** Assumed `architecture/` is a folder for any schema document. The loader's authority set is the closed `_REPOSITORY_MANIFESTS` list of top-level `*.yaml` names.

## 2026-08-17 — Put new graph nodes in data-contracts.yaml

**Symptom:** `grok_verify` `contract-structure` failed: missing `openapi:` / `asyncapi:`.
**Root cause:** Chose a path because its *graph kind* is Contract. The quality profile keys off the filename token `contract`, not `kind: Contract`.

## 2026-08-17 — Edited the Claw PR workflow to attach a local pytest gate

**Symptom:** `secret-scan` failed on `.github/workflows/verify-a2-pr-on-claw.yml`.
**Root cause:** Verification scans the whole changed file. The pre-existing `password="$(...)"` assignment already matches `generic-secret`; touching the file for an unrelated step reopened that match.

## 2026-08-17 — Quoted the workflow password assignment in decisions.md

**Symptom:** `grok_verify` `secret-scan` failed on `decisions.md` after the memory files were committed.
**Root cause:** The log copied the exact `password=` quoted assignment that the scanner matches. Memory files are scanned like product files; describe the pattern, do not paste the matching text.

## 2026-08-17 — Used a hyphenated script path as an importable module

**Symptom:** `tests/conformance/test_stage_a_excludes_go.py` could not import the artifact scanner.
**Root cause:** Inspection logic lived only in `scripts/check-stage-a-artifacts.py`. A hyphenated CLI name is not a Python module; shared logic belongs under `tools/`.

## 2026-09-24 — Inferred project language from the conversation

**Symptom:** Newly published Liqvera documentation used Russian even though the owner requires English throughout the project.
**Root cause:** The artifact language was inferred from the chat instead of being treated as a separate project requirement. Use English by default and preserve that decision in `AGENTS.md`.

## 2026-09-24 — Assumed /dev/null could isolate npm configuration and cache

The first F1 compatibility probe failed locally at npm because the implementation used `/dev/null` as both config paths and a directory-backed cache. Use distinct temporary config paths and an isolated temporary cache, test cleanup on success and failure, and rerun before classifying a failure as external.

## 2026-09-24 — Large pytest parameter generated an unbounded failure label

A 2 MiB synthetic response fixture became its own default pytest parameter ID and inflated RED output. Give large or sensitive-shaped fixtures short explicit IDs so diagnostic output stays bounded.

## 2026-09-24 — Fixed initial URLs did not constrain the full transport

The initial compatibility implementation treated fixed urllib URLs and npm registry argv as proof of endpoint isolation, while urllib inherited ambient proxy credentials and npm followed redirects. The injected IncompleteRead test also missed that real bounded HTTP reads can silently return fewer bytes than Content-Length. Test actual transport behavior and dependency defaults, including proxy selection, redirect follow-up requests, and real HTTPResponse framing, before claiming a fail-closed boundary.

## 2026-09-24 — Decoded-body and socket-operation limits were incomplete

The reviewed transport bounded decoded JSON and individual socket operations, leaving HTTP chunk trailers and total elapsed request time insufficiently bounded. Test real wire framing and slow-drip responses, budget framing separately from payload, and use one total deadline that covers every transport phase.

## 2026-09-24 — Used a credentials-shaped literal in a security regression test

**Symptom:** GitGuardian flagged a synthetic proxy URI as a Basic Auth secret even though the values were non-secret test markers.
**Root cause:** The test embedded the complete `scheme://user:marker@host` shape as one literal. Preserve the behavioral test while assembling synthetic user-info from separate non-secret components so repository-history scanners do not treat fixtures as credentials.

## 2026-09-24 — F2 plan validated local pieces without their shared boundaries

Initial review found that a full-match test helper would enforce stronger string constraints than the published JSON Schema, while separate state tables omitted joint delivery and retention/replay predicates. The root cause was checking each contract in isolation instead of testing interoperability and cross-machine invariants against adverse traces. The planning repair specifies standard regex/URI behavior, discriminated status payloads, joint confirmation eligibility, retention floors and concrete future vectors; independent re-review remains pending.

## 2026-09-24 — Test-helper assumptions masked portable schema defects

Task 1 review exposed Python-specific number equality/bounds and JSON exponent overflow; Task 3 review exposed reliance on the helper's HTTPS-only URI format. The root cause was treating helper behavior as proof that published JSON Schema had the same semantics in other validators. Numeric regressions and an explicit HTTPS pattern with a format-independent test now cover those repaired boundaries.

## 2026-09-24 — Task 6 exploratory verification raced dependency arrival

An exploratory full test run overlapped incoming task cherry-picks and produced transient missing-interface failures. The root cause was verifying a changing dependency tree; later stable checks superseded that result, and integration verification runs only after the selected artifact commits and repairs are present.

## 2026-09-24 — F2 node instructions omitted required graph context

The first integration graph check rejected two orphan nodes and an unscoped validation edge despite all exact file bindings being present. The root cause was following the plan's node/edge sketch without accounting for the existing reverse-requirement and proof-scope checks. Context-only DATA-005 linkage and the existing non-proof marker resolve the missing graph metadata without asserting runtime acceptance.

## 2026-09-24 — State schema was inspected without validating its own document

Integration found that the symbol pattern rejected the existing `report_sha256` uniqueness field. The root cause was testing schema structure and graph semantics separately while the parallel task lacked the shared checker. A failing complete-document regression now validates the actual state file; allowing ASCII digits after the first letter repairs the schema while unsafe names remain rejected.

## 2026-09-24 — Reconstructed vector envelopes hid invalid root fields

Task 6 initially extracted the vector array and rebuilt a known-valid envelope before schema validation. The root cause was validating transformed test data instead of the original loaded document, allowing a wrong/missing schema version or extra root field to escape detection. The loading-path repair validates the original document first and rejects each corruption through real file-loading regressions.

## 2026-09-24 — F2 local consistency checks missed shared safety predicates

Whole-branch review found evidence recovery statuses absent from OpenAPI, expired quotes classified before expiry handling, and valid fixtures/previews/readiness fields not constrained by sale eligibility. The root cause was treating independently valid shapes and model branches as proof of cross-contract agreement. Endpoint/vector comparisons and direct eligibility/readiness mutations now reproduce and cover those shared boundaries; reencoded identity remains explicitly unresolved with no charge or attempt.

## 2026-09-24 — Host-language representations replaced contract semantics

The bounded checker used Python int identity for JSON Schema integer membership, and recovery tests ordered UTC strings lexically. The root cause was conflating implementation representation with mathematical JSON values and temporal instants. Integral float/Decimal regressions, exact numeric precision-boundary checks and mixed/sub-microsecond timestamp regressions now preserve the contract semantics.

## 2026-09-24 — One-way predicates and a hidden conversion limit left edge gaps

Scoped review showed that scenario flags and readiness declarations were constrained in only one direction, while exact timestamp conversion still passed its entire fractional string through Python's limited int parser. The root cause was testing representative positive/negative cases without complete truth tables or an input beyond the host conversion limit. Bidirectional scenario binding, exhaustive readiness combinations and exact Decimal-to-Fraction tests with 4,301 digits now cover those gaps without weakening the timestamp schema.

## 2026-09-24 — A complete truth table retained an incomplete expectation

The readiness truth table covered every boolean combination but incorrectly allowed false payment readiness without blockers, preserving the schema omission. The root cause was applying the complete-explanation rule only to capabilities instead of both resource projections. A focused /readyz regression and corrected truth-table expectation now require a blocker whenever payment readiness is false.

## 2026-09-28 — Artifact search stopped before the owner's local repository

The initial analysis concluded that Adaptive Grok had no trustworthy external
identity because it compared only Liqvera's copied labels and public package
metadata. The authoritative local repository contains annotated `v2.0.19`;
future boundary analysis must inspect owner-provided source repositories before
declaring an artifact unavailable.

## 2026-09-28 — Optional-tool fallbacks crossed a safety boundary

The initial externalization retained shell fallbacks that converted pin
validation failures into successful empty or allow hook responses, while
ordinary tests also imported the optional checkout. Safety hooks must propagate
validation failure; static clone tests and initialized-tooling integration
tests are separate contracts.

## 2026-09-28 — Treated clean Git status as content integrity

The first validator trusted `git status`, which honors `assume-unchanged` and
`skip-worktree` hints and therefore accepted hidden verifier byte/mode changes.
External executable/instruction inputs require direct HEAD blob/mode comparison
plus rejection of index hints and ignored importable files. That comparison
must follow an explicit bounded trust closure rather than rereading historical
packages and release evidence on every hook.

## 2026-09-28 — Retained a coverage floor after changing its ownership set

The cleanup first replaced vendored Grok/scripts coverage with a cherry-picked
set of Liqvera packages/tools, producing an invalid 59.18% denominator that
still omitted owned scripts, standalone tools, and project-owned tooling. The
complete tracked inventory measures 36.16%; coverage ownership and its blocking
floor must be derived together and guarded by an inventory comparison.

## 2026-09-29 — Typed evidence referenced directories instead of contracts

The first F3 full verifier completed its checks but could not record a receipt
because the change spec named test directories and one nonexistent schema file.
The root cause was copying human-readable suite labels into typed evidence
instead of validating every entry as the required regular file path.

## 2026-09-29 — Unpinned verifier interpreter looked like parallel races

The full verifier was invoked with system `python3`, then missing project
packages and Hatchling were misclassified as seven xdist build/import
collisions. The root cause was not binding the command to the repository's
pinned `.venv`; reproducing the exact slice under both interpreters showed the
22-worker path is green and has no shared mutable-state failure.

## 2026-09-29 — Static trigger review missed cross-table record evaluation

The initial F4 analyses declared the schema unchanged without executing the
artifact state transition on PostgreSQL. The shared trigger's guarded
`OLD.tx_hash` reference still evaluated for `artifacts`; future data-boundary
analysis must run each approved mutation on both fresh and upgraded schemas.

## 2026-09-29 — Immediate Docker absence check raced asynchronous removal

The first green database suite was followed by an immediate `docker inspect`
after stopping an auto-remove container, producing a false cleanup failure.
Poll the exact validated container identity until absent before claiming local
cleanup, while retaining the exit trap.

## 2026-09-29 — F5 acceptance evidence used a prose-only field

The first F5 verifier finished its checks but could not record the receipt
because acceptance entries used `verification` instead of the schema's typed
`evidence` array. The root cause was authoring from the Markdown test plan
without first copying the established v2 acceptance shape from a validated
change package.
