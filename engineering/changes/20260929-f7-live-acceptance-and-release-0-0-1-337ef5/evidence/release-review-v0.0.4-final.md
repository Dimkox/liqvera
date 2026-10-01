# Release review — v0.0.4 final candidate

Reviewed commit: `cba005b1c07aafadb4dd15743b7184143143dcf5`

Reviewed tree: `75151ba8b154b72fd77d3df844beb4d3eca89dac`

Decision: **FAIL / NO-GO for publication**

## Blocking finding

### RELEASE-BLOCKER — canonical release plan contradicts current deployment and release state

The top of `engineering/changes/20260929-f7-live-acceptance-and-release-0-0-1-337ef5/release.md` correctly records that candidate `0f3e745d41022c33fbb075c9816b35b1c6a3cabe` was deployed and that v0.0.4 tag/push/GitHub Release remain pending. Its later unqualified `## Deployment` section still says `No hosted deployment`. The same document's `## Follow-up v0.0.2 candidate` section says no v0.0.2 artifact, push, tag, or GitHub Release exists, while README and handoff correctly record published v0.0.2 assets and tag.

These are not harmless omissions in a canonical go/no-go document: an operator or reviewer cannot distinguish historical pre-v0.0.1 statements from current release state. The live evidence itself is precise, but the release plan presents mutually exclusive deployment/publication facts.

Required correction: make historical sections explicitly version- and date-scoped, replace the generic Deployment section with current v0.0.4 facts, and state separately:

- deployed public candidate: `0f3e745d41022c33fbb075c9816b35b1c6a3cabe`;
- reviewed release candidate: `cba005b1c07aafadb4dd15743b7184143143dcf5`;
- the browser hotfix commits after `0f3e745` have test evidence but are not claimed as deployed;
- v0.0.4 push/tag/GitHub Release remain pending;
- v0.0.2 and v0.0.3 are already published historical milestones.

After that documentation-only repair, rerun fingerprint-bound verification and every route-selected review because the commit/tree will change.

## Evidence assessment

- `evidence/acceptance-v0.0.4.md` truthfully binds the deployed candidate to `0f3e745d41022c33fbb075c9816b35b1c6a3cabe`, reports the public origin and exact report/bundle/transaction identities, and explicitly says no push, tag, or GitHub Release occurred.
- Handoff truthfully distinguishes the deployed `0f3e745` candidate from the later browser hotfix at reviewed HEAD. It does not claim that `cba005b` is deployed.
- README truthfully labels root VERSION 0.0.4 as unpublished, identifies the public judge URL, and retains v0.0.2 as the installable operator package.
- The paid E2E evidence records one submission, confirm-only recovery, JSON and ZIP delivery, 22 confirmations, offline bundle verification, and no mainnet/exchange/custody action.
- The checked-in rollback remains exact: `compose.live-disabled.yaml` atomically removes the grant mount and activating context while preserving the fail-closed live service and durable payment/evidence state.
- No release artifact manifest or publication evidence for v0.0.4 was presented; this is consistent with publication still pending.

## Verification sampled

- Exact commit/tree and clean product worktree confirmed.
- `git diff --check e3df683..cba005b` — PASS.
- `.venv/bin/python -m pytest tests/operations/test_f6_static.py -q` — **5 passed**.
- `cd apps/mezo-web && npm test` — **25 passed, 0 failed**.
- No external HTTP/RPC/facilitator call, payment, deployment, tag, push, or release mutation was made by this review.

## Additional closure state

At review time `python3 scripts/grok_status.py` reports the human gates and all independent review receipts stale after repository changes. This release-review receipt records FAIL for the exact reviewed fingerprint; it does not substitute for scope/external-write approval or the remaining review wave.

## Go/no-go matrix

| Area | Result |
| --- | --- |
| Exact commit/tree | PASS |
| Worktree cleanliness | PASS |
| Live acceptance evidence precision | PASS |
| Hotfix test evidence | PASS |
| Rollback/fail-closed operation | PASS |
| README/handoff truthfulness | PASS |
| Canonical release-plan truthfulness | FAIL |
| v0.0.4 artifact/tag/push/release evidence | PENDING / NOT CLAIMED |
| Route evidence closure | NOT READY |

Publication remains NO-GO until the contradictory release-plan sections are repaired and the resulting final fingerprint completes verification, all independent reviews, and required human gates.
