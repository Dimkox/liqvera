# Documentation and provenance analysis — repository boundary cleanup

Route: `7f0f98e3cdda`

Base commit: `0c2cb97f8048f7da8bd193634f4502f24b0e541e`

Role: `docs_researcher` (read-only except this report)

Date: 2026-09-28

## Ruling

Current-state documentation must say that the inherited Go Stage-0 implementation
was removed from the active tree and that Grok/BMad are externally managed,
integrity-pinned contributor tooling. Historical plans and evidence should remain
truthful to the state they recorded; they should not be rewritten as if Go or the
vendored factory had never existed.

`provenance/import-manifest.json` must remain an immutable description of the
initial 815-file import. It is not a generated current-tree manifest and must not
be pruned when imported files are later deleted. The exact current-tree authority
is `architecture/architecture.yaml`, whose repository inventory must be updated
for every deletion and every new thin-integration file.

The word **factory** is overloaded in this repository. The cleanup concerns the
vendored Grok/BMad implementation. It does not, by itself, require removing the
Liqvera build targets or `scripts/build-liqvera-python-distributions.py`. Those are
product build surfaces. Renaming their graph node from `runtime:liqvera-factory`
to a less ambiguous build-oriented name is optional clarity work, not evidence
that the product factory should be deleted.

## Measured baseline

- Go Stage-0 is 24 tracked source/module files: `cmd/engine/main.go`, `go.mod`,
  and 22 files under `internal/` (2,938 lines; 91,315 bytes). There is no tracked
  `go.sum`. The root `Dockerfile` is a 25th Go-owned artifact because it builds
  `./cmd/engine`; it should retire with the Go implementation.
- The four vendored prefixes contain 383 tracked files and 1,940,075 bytes:
  `.agents/` 253, `.grok/` 75, `.grok-stack/` 40, and `_bmad/` 15.
- The architecture inventory classifies another 20 exact paths as
  `VENDORED_TOOLING`: 17 root/`scripts/grok_*` shims plus `.coveragerc`,
  `bandit.yaml`, and `ruff.toml`. This makes 403 currently declared vendored
  paths and 1,957,753 bytes. The three general-purpose quality configurations
  should be judged individually; they need not be deleted merely because the
  old graph grouped them with the factory.
- The imported Adaptive Grok package declares `2.0.11`; the BMad manifest
  declares `6.10.0`. Neither declaration supplies an immutable Adaptive Grok
  upstream repository/release coordinate plus artifact digest. BMad says
  `source: built-in` with no repository URL or package coordinate. The existing
  version strings and the x.ai documentation URL are therefore not a
  reproducible external pin.

## Current/canonical documents that must be rewritten

| Document | Current problem | Required treatment |
| --- | --- | --- |
| `README.md` | Says retained Go is the historical executable specification, describes the checkout as factory-bound, and reports Grok-specific verification as if the implementation remains local. | Replace present-tense Go/factory claims with the retired-source boundary and the exact external-tooling setup/pin. Preserve `IMPLEMENTED_UNVERIFIED`, `NOT_RUN`, payment blockers, and shadow-only status. Keep the stack graph complete as required by `AGENTS.md`. |
| `handoff.md` | Present-tense current handoff says the factory is integrated, names local `.grok-stack` state and `scripts/grok_verify.py`, and repeatedly treats absence of a factory receipt as the current condition. | Add the cleanup decision, final tree/fingerprint evidence, external-tool prerequisite, rollback reference, and next action. Historical verification paragraphs may remain explicitly historical, but the opening/current-state section must not imply vendored tooling or Go remains active. |
| `docs/architecture.md` | Its stated purpose is preservation of the **Go Stage-0 foundation** and it says existing Go remains `TEST_ONLY_EXECUTABLE_SPEC`. | Retitle/reframe it around the surviving Liqvera safety invariants. State that the source is retired from the active tree and recoverable at the immutable import commit. Keep the invariant list; remove current-runtime implications. |
| `docs/README.md` | Lists `architecture.md` as retained Go-foundation truth and says `.agents/`, `_bmad/`, and related files are repository-local contributor tooling. | Describe the retired historical source and the thin external integration. Link the pinned lock/bootstrap/contributor instructions once their final paths are known. |
| `PROVENANCE.md` | Correctly records the initial import, but “No baseline file is omitted” and the `_bmad` scan explanation can be misread as claims about the present checkout. | Keep source SHAs, counts, hashes, and scan facts unchanged; qualify them as import-time facts. Add a dated post-import retirement note pointing to base commit `0c2cb97...` (and the cleanup commit once known) as recovery locations. Explicitly say the import manifest is not a current-tree bill of materials. |
| `docs/planning/LIQVERA_FACTORY_TZ.md` | The canonical spec says “Do not rewrite the retained Go code” and directly requires `.grok-stack/runtime/active-route.json`. Its title/instructions conflate product specification with one tool implementation. | Preserve F0-F7 product requirements, but supersede the retained-Go and local-factory execution instructions. Prefer a product/delivery-spec title in the document. The filename may remain as a compatibility path unless a separate rename updates all links/tests. |
| `docs/planning/MEE_MEZO_EVIDENCE_FACTORY_TZ.md` | Compatibility pointer says it exists for factory links. | Keep as a compatibility pointer, but describe the old filename/tooling terminology as historical and point only to the canonical Liqvera spec. |
| `AGENTS.md` | The safety contract invokes local route files, hooks, `scripts/grok_*`, vendored skills, receipts, and deployment flow. Deleting their implementation without changing this document creates impossible instructions. | Preserve project-owned continuity, commit/handoff, secret, shadow-only, market-research, release-authority, and one-write-owner rules. Replace implementation-specific commands with the final thin launcher/bootstrap interface and deterministic “tooling unavailable” behavior. Do not weaken product `make verify`. |
| `docs/a2-deployment.md` | Says the root `Dockerfile` still packages the Go reference engine. | Remove that present-tense paragraph and state that Stage A product images remain wheel-only; historical Dockerfile evidence belongs in Git history/dated validation records. |
| `docs/adr/0001-python-universal-arbitrage-core.md` | The accepted ADR says removal is a future separate reviewed commit. | Do not rewrite the 2026-07-26 context/decision. Add a dated outcome/addendum recording that this cleanup completed the already-approved migration boundary and naming the recovery commit. |
| `docs/research/TECHNICAL_STRATEGY.md` | Says existing Go remains until parity/removal. | Update the scope note to say retirement completed; retain the surviving correctness thesis. |
| `docs/research/REPOSITORY_CONNECTIVITY_AUDIT.md` | Classifies Go as a transitional active-tree reference and the four vendored prefixes as current tooling. | Add a superseding dated note or refresh the relevant classification sections. Do not silently present the 2026-08-18 snapshot as current. |
| `decisions.md` | Contains historically correct decisions that Go stays active until review and that factory links/build targets were preserved. | Keep old entries intact. Append one concise superseding decision: why history plus conformance tests is sufficient, why the import manifest stays immutable, and why external tooling needs an integrity pin. |

`docs/ROADMAP.md` references the compatibility filename
`LIQVERA_FACTORY_TZ.md` but does not depend on vendored factory code. It only
needs a link change if the canonical file is actually renamed. Its “F1 is next”
sentence is independently stale relative to the current handoff and should be
corrected if current-state docs are refreshed in this change.

## Historical documents that should not be modernized

These files are evidence of what existed or was proposed at a specific time.
Their Go/Grok/BMad details remain useful provenance and should not be globally
replaced:

- `docs/validation.md` (dated Stage-0 validation record);
- `docs/agent-handoff.md` (dated 2026-07-28 handoff);
- `docs/deployment.md` (old Claw host/runtime observations);
- `docs/planning/epics.md` and
  `docs/planning/implementation-readiness-report-2026-08-11.md`;
- `docs/planning/research/technical-go-vs-rust-production-runtime-research-2026-07-26.md`;
- the Go-era plans/specs under `docs/superpowers/`, especially
  `2026-07-21-five-day-stage-a`, `2026-07-25-stage-a-operator-revenue`,
  `2026-08-11-m0-m3-canonical-distributions-and-graph`, and
  `2026-08-11-unified-graph-migration-program`;
- `docs/archive/**`;
- `engineering/changes/2026-09-24-mezo-evidence/**`, including bound F1/F2
  evidence and state; and
- existing historical entries in `decisions.md` and `mistakes.md`.

For non-archive historical files that remain easy to reach from current indexes,
add a short standard banner: “Historical record; paths and tool commands reflect
the repository on <date>; current authority is README/handoff/ADR.” A banner is
especially useful for `docs/agent-handoff.md`, `docs/deployment.md`, and the two
2026-08-11 planning documents because their titles can look current.

Do **not** edit fingerprint-bound evidence reports merely to add such a banner.
The directory and evidence heading already provide historical context, and
modifying them would damage their value as exact records. Archive files are also
acceptable unchanged when they are reachable only through the explicit archive
pointer in `docs/README.md`, consistent with the connectivity-audit rule.

The F1/F2 plans' old `grok_verify` commands may remain historical. Current
contributor instructions must not route readers to those plans as setup
documentation.

## Provenance and import-manifest constraints

1. `provenance/import-manifest.json` has schema `mee-source-import/v1`, source
   commit `4f6583f8590ea091d8a465de0c607e59bfe611a5`, and 815 file records. It
   describes the initial import, not today’s checkout.
2. The manifest includes all 24 Go/module paths, the four vendored prefixes,
   root shims, and the original root Dockerfile. Those entries must remain even
   after deletion; removing them would make the manifest's claim about the
   initial import false.
3. Do not regenerate source/import SHA-256 fields against the cleanup tree and
   do not repurpose the manifest as an allowlist. If a current source inventory
   is desired, use a new schema/file; the architecture inventory already serves
   that role.
4. `PROVENANCE.md` should identify both immutable recovery points:
   import commit `8734907d489168a8a6567b93bc85920001fefd85` for original bytes and
   base commit `0c2cb97f8048f7da8bd193634f4502f24b0e541e` for the last pre-cleanup
   integrated tree. Record the final cleanup commit only after it exists.
5. The `_bmad/_config/files-manifest.csv` digest finding remains a truthful
   import-time scan result even when that path no longer exists at HEAD. Phrase
   it historically; do not delete the scan disclosure.
6. No test currently validates every import-manifest hash against HEAD, which is
   correct because 22 files were transformed at import and many files changed
   afterward. Graph tests only require that the manifest file itself has
   documentation authority.

## Machine-readable architecture and generated-inventory impact

The following are current authority, not historical documentation, and must be
updated atomically with the deletions:

- `architecture/architecture.yaml` binds every tracked path exactly once. It
  contains Go bindings, the root-Dockerfile binding, 20 exact vendored
  exclusions, and four prefix exclusions. Stale bindings fail with
  `REPOSITORY_ARTIFACT_NOT_TRACKED`; an unbound new lock/bootstrap/config fails
  with `REPOSITORY_ARTIFACT_UNDECLARED`.
- `architecture/runtime.yaml` declares active `runtime:go-reference` and
  inactive `artifact:vendored-agent-tooling`. Retire or remove the Go owner and
  replace the vendor artifact with truthful thin-integration authority.
- `architecture/requirements.yaml` and `architecture/architecture.yaml`
  contain the `ARCH-GO-001..005` requirements and their proof lanes. Preserve
  historical intent, but do not leave active proof edges pointing at a deleted
  runtime. A retired node plus immutable source reference is clearer than a
  phantom implemented runtime.
- `architecture/conformance/manifest.yaml` has five dangling-prone
  `reference_source: internal/...` values and `retirement_state: BLOCKED`.
  Replace each with a structured or unambiguous immutable historical reference
  plus the existing current Python contract/test. The cleanup's independent
  review is the retirement evidence; `stage_a_packaging_allowed` must remain
  false.
- `architecture/schemas/graph-manifest.schema.json`,
  `tools/graph_checker/loader.py`, `checker.py`, `model.py`, and retirement
  logic hard-code `GO_SOURCE`, `go-test-only`, `TEST_ONLY_EXECUTABLE_SPEC`, the
  four vendor prefixes, and Grok shim names. At minimum remove current-instance
  assumptions. Keeping a generic enum is harmless only if tests no longer
  imply the Liqvera tree contains or authorizes that runtime.
- `architecture/strategies.yaml` names
  `document:mezo-evidence-factory-spec`; this denotes the product spec, not the
  vendored factory. It may remain for compatibility or be renamed with all
  three edges updated.

Tests with exact stale expectations include:

- `tests/graph/test_third_final_review_policy.py`: minimum 626 tracked files,
  exact 403 vendored exclusions, vendor-prefix classifier cases, publication
  paths, and exact inventory coverage. Deleting about 400 files will make the
  `>= 626` floor fail even when inventory is correct.
- `tests/graph/test_repository_manifests_cli.py`: expects
  `conflict:go-stage-a-build` and seven declared conflicts.
- `tests/graph/test_second_final_review_policy.py`: asserts the active
  `runtime:go-reference` profile/classification.
- `tests/conformance/test_retirement_policy.py`: explicitly requires the live
  Go owner to remain blocked from retirement without receipt/review.
- `tests/graph/test_contracts_distribution_classifier.py`: expects `.grok`
  and `scripts/grok_verify.py` to classify as vendored tooling.

Negative product-boundary checks should remain:

- `Makefile`/`scripts/check-stage-a-artifacts.py` forbidding `cmd/**`,
  `internal/**`, `go.mod`, `go.sum`, and an `engine` binary;
- `tests/conformance/test_stage_a_excludes_go.py`;
- `tests/artifact/test_wheel_boundaries.py`; and
- installed-package purity checks forbidding `adaptive_grok` imports.

Those checks protect against accidental reintroduction and do not imply that Go
or Adaptive Grok is still shipped.

The root Go `Dockerfile` currently causes external verification to discover a
container target. After it is removed, the verification contract must name the
actual product Dockerfiles/Compose files explicitly; otherwise a cleaner result
could mean reduced scan coverage. The historical Trivy findings must be reported
as historical or still-open only according to a fresh scan of the relevant
product definitions, not silently disappear with the trigger file.

## Minimum documentation contract for the external integration

Before current docs claim the factory is “pinned,” the retained integration must
publish all of the following:

1. canonical upstream repository/package/release coordinate;
2. immutable commit or release artifact identity;
3. archive/package SHA-256 (and signature identity if available);
4. expected Adaptive Grok and BMad compatibility versions;
5. explicit bootstrap command and ignored local cache location;
6. offline/cached operation and deterministic missing-cache failure behavior;
7. commands replacing route, status, change, verify, review, and deploy-plan;
8. proof that ordinary product build/test commands never download or execute
   remote tooling; and
9. rollback instructions to the base commit or a prior lock without restoring
   copied sources into the product tree.

The current repository cannot supply item 1-3 from its own metadata. The write
owner must obtain the authoritative external coordinate; documentation must use
`TOOLING_SOURCE_UNRESOLVED` or equivalent rather than inventing a link or
claiming the version string is a pin.

## Documentation acceptance checks

- A current-doc scan has no present-tense claim that local Go source, `.agents/`,
  `_bmad/`, `.grok/`, or `.grok-stack/adaptive_grok` remains active.
- Historical mentions are either inside explicit archive/evidence paths or have
  a dated historical banner.
- `PROVENANCE.md` and the unchanged import manifest agree on initial count,
  source commit, transformations, and recovery history.
- Every link in README/docs index/canonical spec resolves after any rename.
- The legacy spec pointer still resolves if the canonical filename is retained;
  if renamed, graph bindings and publication tests are updated together.
- README and handoff retain exact product truth: F3-F7
  `IMPLEMENTED_UNVERIFIED`, all 156 vectors `NOT_RUN`, A13-A14
  `BLOCKED_EXTERNAL`, payment readiness false, no live payment/deployment/release,
  and shadow-only safety.
- New lock/bootstrap/config files are bound once in the architecture inventory;
  deleted paths are absent from active bindings/exclusions.
