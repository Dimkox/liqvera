# Requirements — F7 live acceptance and release 0.0.1

> Typed authority: [`change-spec.yaml`](change-spec.yaml). This Markdown explains context and cannot override typed IDs, risk, acceptance criteria, forbidden outcomes, or approval scopes.

## Acceptance criteria

- [ ] AC-001/P0: exactly A01–A30 in canonical order are semantically validated;
  overall status is derived; PASS cannot be self-certified by echoed text; case
  evidence is unique/create-only/rehashed and final output is atomically bound
  to unchanged clean commit/tree, plan, runner, assertion, command, and evidence.
- [ ] AC-002/P1: locally eligible cases execute in a fresh mode-0700 out-of-tree
  root on the reviewed commit; missing container/PostgreSQL/clean-machine/live
  prerequisites remain explicit `NOT_RUN`/`BLOCKED_EXTERNAL`; local A30 names
  only the fake-provider production-browser criterion.
- [ ] AC-003/P2: after an exact short-lived read grant, only allowlisted public
  destinations/methods run within frozen attempt/timeout/size limits, with no
  redirects/proxies/private methods or mutations.
- [ ] AC-004/P3: reviewed production identity/finality/x402 browser wiring is
  green before a separately approved exact envelope is shown to a human-held
  wallet; at most one submission transfers exactly `10000000000000000` atomic
  test MUSD on chain 31611 to the approved distinct merchant, under a numeric
  test-BTC gas cap. UNKNOWN is confirm-only and never retried.
- [ ] AC-005/P4: Liqvera product version `0.0.1` is machine-readable while all
  component versions stay `0.1.0`; reproducible assets and `SHA256SUMS` bind
  the release commit, acceptance result/manifest, exact names, sizes, and hashes.
- [ ] AC-006/P5: after a separate exact production grant, canonical remote main
  fast-forwards from the approved old OID to the approved release OID, annotated
  `v0.0.1` targets it, and a GitHub Release with allowlisted re-hashed assets and
  truthful limitations is published and anonymously verified.

## Failure and edge cases

- Any tracked/untracked worktree change, changed HEAD/tree/plan/target/grant,
  duplicate/missing case, dishonest status algebra, mutable/stale/symlinked
  evidence, secret canary, or failing required case stops progression.
- P2 stops on DNS/TLS/redirect/proxy/chain/token/code/decimals/scheme mismatch,
  rate limiting, malformed/oversized data, stale market data, or credentials.
- P3 stops before signing on wrong/expired envelope, unreviewed policy, balance
  or gas-cap failure, ambiguous identity, or any unexpected approval/tx. After
  possible broadcast, state is UNKNOWN; preserve evidence and reconcile only.
- P5 stops if remote main moved, tag/release exists, actor/repository differs,
  branch rules differ, or any downloaded asset hash differs.

## Governance context

Canonical governance JSON under `governance/` remains separately reviewed authority. Any rule, example, debt, or digest named here is non-authoritative context until the verifier rederives current governance evidence.

- Applicable rule IDs:
- Canonical-example deviations and evidence:
- Intentional debt created, repaid, or accepted:

## Non-functional requirements

- Security: secret names only; no `.env`, key store, browser profile, credential
  helper, private dump, raw signature/header, or ambient authority inspection.
- Reliability: immutable out-of-tree results; no self-referential commit; no
  payment retry; publication recovery is additive and never rewrites history.
- Performance: all commands, probes, evidence, and artifacts have explicit
  bounds and stop conditions.
- Observability: exact commit/tree/grant digests, public tx/block/log identity,
  settlement count, case/evidence hashes, artifact hashes, and remote read-back.
