# Data architecture analysis — offline F3 artifact loop

Route: `08fa9d84745d`
Scope reviewed: installed canonical F3 fixture input, deterministic bundle, immutable local publication, and offline verification.

## Decision: no migration and no persistent-store work

This tranche must not change or execute any SQL migration, database schema, ledger row, service state, or external store. In particular, `packages/evidence-report/migrations/001_local_demo.sql` and `apps/mezo-gateway/migrations/001_ledger.sql` are outside scope and must remain byte-for-byte unchanged.

The only state owned by this change is disposable local fixture/artifact state under test temporary directories. The canonical data flow is:

1. `inspect_package()` reads an exact, bounded local fixture tree into an in-memory `dict[str, bytes]` through no-follow descriptors.
2. `build_report()` derives canonical report, algorithm, dependency-lock, and sealed-input bytes from that snapshot.
3. `publish_artifact()` writes `report.json` plus `evidence.zip` into a same-filesystem staging directory, fsyncs files/directories, verifies the ZIP, then atomically renames the staging directory to `<root>/<report_id>`.
4. `verify_bundle()` opens one local regular file without following symlinks, validates exact ZIP structure and member digests, then rebuilds the report and bundle byte-for-byte without network or database access.

Therefore schema-before and schema-after are identical, data volume/backfill/query-plan/index/lock/downtime impact is **none**, and rollback is deletion of test-temporary output or code reversion. No production cleanup or destructive SQL is authorized.

## Integrity invariants to characterize

- Fixture membership is exact: only `BASE_MEMBERS` plus fixture mapping evidence are accepted; missing, extra, duplicate, unsafe, symlinked, non-regular, oversized, or hash/length-mismatched members fail closed.
- The captured byte snapshot, not later filesystem contents, is the sole input to report and ZIP construction.
- The bundle manifest binds every non-manifest member, while the report binds sealed input, algorithm, runtime dependency lock, engine commit, request, and report UUID.
- A published report ID is immutable. Reusing an existing UUID must fail before replacing or merging any bytes, including when the new payload is otherwise valid.
- Publication is all-or-nothing at the visible target: only a directory containing exactly `report.json` and `evidence.zip` is readable. A failed build/verification/rename must not expose a target directory.
- `read_published()` must require equality between the standalone report and the verified report embedded in the bundle. Tampering either copy must fail closed.
- Offline verification is intentionally repeatable; “replay rejection” in this tranche should mean duplicate **publication** for the same report UUID, not rejection of repeated read-only verification of an unchanged bundle.
- A successful verifier result establishes relative integrity and exact recalculation only. It must continue to report `exchange_authenticity_verified=false` and `execution_authority=NONE`.

## Fixture/state risks and required probes

1. **Installed-resource drift.** Canonical code loads schemas and `runtime-dependencies.txt` from wheel resources. Source-tree tests can pass while an installed wheel omits or changes resources. Build/install the actual wheel in an isolated local environment and exercise the same fixture-to-publish-to-verify path.
2. **Split-brain report copies.** Publication deliberately stores the report twice (standalone and in ZIP). Mutate each independently and assert `read_published()`/verification rejects rather than serving mismatched state.
3. **Duplicate-ID overwrite.** Publish once, attempt a second publish with the same UUID (both identical and changed report inputs), and assert original file bytes and digests remain unchanged.
4. **Partial publication/recovery residue.** Inject failures after the first staging file, after both files, and during verification/rename. Assert no visible `<report_id>` target, no readable partial artifact, and no mutation of an existing target. Hidden staging residue after process death may be an operational cleanup concern but must never be interpreted as a published report.
5. **Member tamper and structural ambiguity.** Flip bytes in report, algorithm, dependency lock, sealed input, and manifest; remove/add/duplicate/reorder members; alter ZIP metadata; assert stable `INVALID_DATASET` rejection and no derived output.
6. **Fixture tree races.** Mutate or replace a fixture file while it is read and assert rejection or a self-consistent captured snapshot—never a mixed report/bundle. The current per-file checks cover inode/size/mtime around each read, but cross-file atomicity is not guaranteed by the source directory itself; manifest bindings and final strict inspection are the required fail-closed boundary.
7. **Artifact-root hazards.** Exercise symlink/non-directory roots and symlink/non-regular published members. They must reject without traversing or deleting outside the test root.
8. **Bound enforcement.** Test member count, individual size, aggregate size, nesting depth, and ZIP central/local-header constraints at their boundaries to prevent resource amplification.

## Source of truth and recovery

For this offline tranche, the sealed fixture bytes and their manifest are the immutable calculation input; the published deterministic bundle is the portable verification artifact. The standalone report is a convenience copy and is accepted only when equal to the report recovered from the bundle. There is no database projection to reconcile and no backfill/replay job to design.

Forward recovery is bounded: discard an unpublished staging directory and rebuild from the unchanged fixture, or publish a new UUID. Never repair bytes in place under an existing report UUID. Any future ledger/API integration is a separate change requiring its own migration, reconciliation, and retention analysis.

## Data-review acceptance boundary

Data review should pass only if focused tests demonstrate the invariants above against the installed package and the diff contains no migration, database, network, payment, deployment, or external-write changes. Any need to alter persistent schema or execute a store write is scope expansion and must stop this route.
