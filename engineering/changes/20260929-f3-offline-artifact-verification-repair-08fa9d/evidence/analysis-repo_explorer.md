# Repository exploration — F3 offline artifact verification repair

Route: `08fa9d84745d`
Observed HEAD: `bed18457b084f9c9f15dd8bee24c31a74323e639`
Role: route-selected read-only repository exploration; only this report was added

## Result

The narrow offline F3 vertical is present and works from source: a deterministic
fixture capture can be strictly inspected, converted into an exact report,
published as exactly `report.json` plus `evidence.zip`, read back, and
recalculated by the archive-first verifier. A local temporary-directory probe
completed without network or persistent-store access and produced report SHA-256
`d8069708ccb53321003690ce0a51684f3214c3c374c5188b51926aa235b480d1` and
bundle SHA-256
`7105958df469e3acc36c0b93dc8d019593d1902b57febe23be4c4bb166be131a`.
This is characterization only, not acceptance evidence or installed-wheel proof.

One deterministic contract defect is confirmed. `tools/mezo_acceptance/runner.py`
records `git rev-parse HEAD` and `HEAD^{tree}`, which are 40-character Git object
IDs in this repository. `schemas/mezo-evidence/v1/acceptance-result.schema.json`
defines both fields with its 64-character `sha256` definition. Validating a
runner-shaped offline result therefore produces two errors at
`repository/commit` and `repository/tree`. The repair should give these fields
an explicit Git-object-ID definition matching the repository identity contract,
not disguise Git identities as content SHA-256 values.

The canonical implementation has no checked-in direct tests. Existing
`tests/evidence_report/` and
`tests/installed/test_f3_mvp_demo_contract.py` cover the older MVP
`builder.py`/`bundle.py` path and static Makefile/README strings. A repository
search found no tests importing `evidence_bundle`, `build_inspected_report`, or
`capture_package`, and no test validating an acceptance result emitted by the
runner. This is the main reason the contract mismatch and the canonical
publication behavior survived integration.

## Relevant surfaces

- Fixture capture and atomic sealing:
  `packages/public-capture/src/mee_public_capture/evidence_capture.py` and
  `evidence_package.py`.
- Strict retained-input inspection:
  `packages/evidence-report/src/mee_evidence_report/sealed_input.py`.
- Exact report/reproducibility document:
  `packages/evidence-report/src/mee_evidence_report/report.py`.
- Deterministic ZIP, archive-first verification, atomic publication and
  immutable readback:
  `packages/evidence-report/src/mee_evidence_report/evidence_bundle.py`.
- Installed commands:
  `mee-evidence-build` and `mee-evidence-verify` in
  `packages/evidence-report/pyproject.toml`.
- Result identity producer/consumer:
  `tools/mezo_acceptance/runner.py` and
  `schemas/mezo-evidence/v1/acceptance-result.schema.json`.

The evidence-report wheel force-includes the complete Mezo evidence schema
directory, the local demo migration, demo web assets, and the demo server.
Canonical algorithm and dependency resources live below the packaged Python
package. Installed-wheel verification still needs to prove those declarations
against the built artifact rather than infer them from `pyproject.toml`.

## Required regression matrix

The smallest coherent test slice should exercise the canonical modules, not the
legacy MVP aliases:

1. Build/install the four local Liqvera wheels into an isolated environment and
   invoke the installed capture/build/verify boundaries using only a fixture and
   temporary directories.
2. Assert byte-identical repeated bundle construction, the exact two published
   files, matching report/bundle digests, `SIMULATED`, non-chargeable output,
   false exchange-authenticity claim, and `execution_authority=NONE`.
3. Mutate a report member, manifest digest/length/path, sealed-input member, ZIP
   metadata/order, or trusted expected report digest and require fail-closed
   `INVALID_DATASET` rejection.
4. Reuse an already published report ID and require rejection without changing
   either existing artifact byte. Pre-create a partial target directory and
   require both publication refusal and immutable-reader integrity rejection.
5. Inject failures before rename and at readback verification; assert no target
   report directory becomes visible and no staging directory remains. The stable
   lock-file behavior should be asserted separately rather than mistaken for a
   partial artifact.
6. Construct a complete 30-case offline acceptance result from the runner's
   repository identity and validate it against the schema. Assert malformed Git
   OIDs remain rejected.

`publish_artifact` already follows write/fsync/verify/rename/fsync ordering and
`read_published` requires exactly the report and bundle. The negative tests
should first characterize these guarantees; implementation changes should be
limited to an actually failing case.

## Factory and environment constraints

The full `liqvera-python` target cannot be honestly called an offline build in
its current form: `scripts/build-liqvera-python-distributions.py` unconditionally
runs `pip download` for `jsonschema==4.23.0` and `referencing==0.35.1`. It also
requires an exactly clean HEAD, while this routed worktree currently contains
the active change package and the cancellation records for the superseded
route. Do not bypass either guard. For this tranche, use an already provisioned
local environment for source characterization, and run the exact factory only
after the implementation/evidence files are committed and either an approved
offline wheelhouse/no-index path exists or dependency download is explicitly
outside the no-network acceptance claim.

No migration is needed. No gateway ledger, SQLite demo database, service
listener, live capture, facilitator/RPC/wallet/payment path, Compose start,
deployment, release, or external write belongs in this change.

## Recommended implementation order

1. Add the acceptance identity schema regression and correct the Git OID
   contract.
2. Add source-level canonical F3 happy-path and negative publication/verifier
   tests; repair only reproduced failures.
3. Add the installed-wheel fixture vertical, explicitly proving packaged
   resources and console entry points.
4. Run focused tests, then the route's full verifier and independent code/test/
   data reviews on one final fingerprint.

The earlier broad-route repository report remains valid only as background.
Graph orphans, gateway/web dependency installation, F4 recovery behavior, live
acceptance, and F5-F7 work are deliberately outside route `08fa9d84745d`.
