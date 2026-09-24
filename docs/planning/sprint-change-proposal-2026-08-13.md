# Sprint Change Proposal — Story 1.2A installed OCI approval path

Date: 2026-08-13

Mode: BMAD Correct Course, batch synchronization

Decision: approved by the owner's explicit request to synchronize BMAD and Superpowers

Authority: `NONE`

## 1. Issue summary

D0 installed the reviewed host-deployment controller, but the first separately
authorized D1 `begin` stopped at `STAGED_INPUT_VERIFY`. The installed policy
stores the logical source identity `ci/claw/oci-evidence-approval.json`, while
the installed controller necessarily passes the physical root-owned path
`/usr/local/libexec/mee-claw-host-deploy-lib/oci-evidence-approval.json` to the
verifier. The verifier compares those two different path domains directly.

The failure occurred before nonce consumption, begin intent, host WAL, package,
user, subid, Podman, service or app-stack mutation. D1 `finalize` was not run.
The expired approval comment is not reusable.

## 2. Impact analysis

- Epic 1 remains the active epic; no epic rollback or re-baselining is needed.
- Story 1.2 remains `in-progress` and cannot advance to Phase B while the host
  transition prerequisite is incomplete.
- Story 1.2A becomes an explicit BMAD story and the immediate blocking work.
- Story 1.3 and all later release/deployment work remain blocked.
- No PRD or UX change is required. The 2026-08-11 readiness report remains a
  historical baseline and is superseded for this incident by this proposal.
- Epics 2-4 are unaffected.

## 3. Recommended course correction

Use a direct, bounded source correction:

1. Keep `--approval` as the physical file used for byte loading and hashing.
2. Add required `--approval-policy-path` as the logical source-relative policy
   identity.
3. Require that logical value to be exactly
   `ci/claw/oci-evidence-approval.json`; reject absolute paths, backslashes,
   dot-segments, omissions and mismatches.
4. Make the installed controller pass both identities explicitly.
5. Prove the change by TDD, direct Claw tests, manifest/hash closure and two
   independent security and graph reviews.

This is a moderate course correction: implementation is localized, but the
installed-artifact manifest, approval path set and deployment sequencing must
remain exact.

## 4. Artifact changes

| Artifact | Old state | Synchronized state |
|---|---|---|
| Story 1.2 | nonstandard `phase-a-review` | `in-progress`; D0 installed, D1 prerequisite blocked |
| Story 1.2A | file existed but was absent from epics/ledger and said `DESIGN / RED` | explicit Epic 1 story, `in-progress`, D0 complete and D1 fail-closed checkpoint recorded |
| Sprint ledger | generated 2026-08-11, last updated 2026-08-12 | current timestamp, standard status vocabulary, Story 1.2A tracked |
| Superpowers design | correction architecture selected | preserved as the approved contract |
| Superpowers plan | no dedicated execution plan | TDD plan `2026-08-13-claw-installed-approval-path.md` |

## 5. Acceptance and approval points

- Source tests must demonstrate current RED, then physical/logical-path GREEN
  and all negative path-domain cases.
- Direct Claw Python 3.14 tests, graph precommit, manifest hashes, syntax and
  diff checks must pass on the exact source SHA.
- Independent security and graph reviewers must both return YES before source
  merge.
- Source merge grants no host authority.
- A later D0 update requires a separate owner approval bound to the landed
  source/tree/manifest.
- A later D1 retry requires fresh authenticated inventory and a new exact owner
  approval. `finalize` remains a separate approval point.

## 6. Handoff

- Developer: implement only the Superpowers plan with strict TDD.
- Security reviewer: verify path-domain separation, installed-byte binding and
  fail-closed recovery.
- Graph reviewer: verify inventory, proof lanes, exact approval path set and no
  Story 1.3 authority.
- Owner: separately approve source merge, D0 update, D1 begin and D1 finalize.

## 7. Correct-course checklist

- [x] Trigger and failure evidence recorded.
- [x] Epic/story impact assessed.
- [x] Direct-adjustment approach selected.
- [x] BMAD epics, stories and sprint ledger synchronized.
- [x] Superpowers design preserved and execution plan created.
- [x] Authority and rollback/recovery boundaries retained.
- [x] Source implementation completed with RED/GREEN evidence.
- [ ] Independent reviews completed on exact source SHA.
- [ ] Separate owner checkpoints completed as applicable.
