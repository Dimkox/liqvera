# Publication go/no-go — v0.0.4

Reviewed commit: `c3f985bd8df743d6c2c0a186dcf99c69329f6b13`

Reviewed tree: `709a56736807b06424bb5450b893687e9d23eacf`

Decision: **FAIL / NO-GO for publication**

## Release blocker

### No immutable v0.0.4 publication asset set exists for the exact release commit

Root VERSION is `0.0.4`, no `v0.0.4` tag exists, and documentation correctly says push/tag/GitHub Release remain pending. However, neither the change package nor the retained release-artifact directories contain a v0.0.4 source archive, release notes, release manifest, `SHA256SUMS`, detached checksum, exact sizes/hashes, extraction/install validation, or anonymous-readback plan bound to this publication commit/tree.

The available retained asset sets are historical v0.0.1, v0.0.2, and v0.0.3 material. `evidence/acceptance-v0.0.4.md` contains live report and evidence-ZIP hashes, but that paid evidence bundle is not the GitHub Release source/artifact set for commit `c3f985b` and must not be relabelled as one.

The release plan itself requires an exact clean commit, complete manifest/checksums, artifact extraction/install validation, scans, and all five reviews. Those publication inputs have not yet been produced for v0.0.4.

Required before publication:

1. Build the closed v0.0.4 release asset set from exact clean commit `c3f985bd8df743d6c2c0a186dcf99c69329f6b13` (or freeze a new explicitly reviewed publication commit if release evidence changes the tree).
2. Record exact asset names, byte sizes, SHA-256 values, source commit/tree, VERSION, submodule identity, and truthful limitations in a v0.0.4 manifest and release notes.
3. Rebuild reproducibly where required, scan, extract, and validate the archive in a clean location without treating the historical installer v0.0.2 as a v0.0.4 installer.
4. Run fingerprint-bound verification and all independent reviews against the final publication fingerprint.
5. Only after the applicable publication gate, create a draft release, upload the allowlisted assets, redownload/re-hash them, verify tag/remote identities, and then publish. Do not reuse or mutate historical release assets.

## Passing release properties

- Deployment distinction is truthful: signed-v2 paid acceptance is bound to deployed parent `dcdc7ae6086007d1ccaab8bc563c137c0e099feb`; publication candidate `c3f985b` is a documentation child and is not falsely claimed as the deployed payment subject.
- The acceptance record names the exact deployed tree, migration-006 application, authority count/amount/per-payer bounds, transaction, report/bundle digests, confirmations, one submission, reconciliation, and offline verification.
- README and handoff consistently report six retained 0.01 test-MUSD settlements, no mainnet/exchange/custody action, and pending publication.
- Root VERSION is consistently `0.0.4`; published v0.0.1–v0.0.3 and installable v0.0.2 remain historical identities rather than being overwritten.
- Rollback remains fail-closed and explicitly preserves migration-006 authority/reservation/spent-budget state, UNKNOWN reservations, immutable artifacts, and ledger data.
- Release documentation keeps tag, push, and GitHub Release pending and does not claim that operational acceptance itself performed publication.

## Verification performed

- Exact commit/tree and clean product state confirmed before report creation.
- `git diff --check 95d438b..c3f985b` — PASS.
- Repository tag inventory contains no `v0.0.4` tag.
- Change-package and retained release-artifact inventory contains no v0.0.4 publication asset set.
- No external call, secret read, build mutation, deployment, payment, push, tag, or GitHub Release action was performed.

## Decision boundary

The deployed-parent distinction, live acceptance evidence, version state, and rollback are acceptable. Publication remains NO-GO solely because immutable, provenance-bound v0.0.4 release artifacts and their verification evidence do not yet exist. This review does not authorize asset creation or external publication.
