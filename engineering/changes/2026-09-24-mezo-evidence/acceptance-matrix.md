# Acceptance matrix

Status values are `NOT_RUN`, `PASS`, `FAIL`, or `BLOCKED_EXTERNAL`. The F1
observations below are bound to implementation commit
`68dafdba76ee5aaf9dc2d5c28719f26f849bf1f6` in
[F1 evidence](evidence/f1-verification.md). F7 must repeat acceptance against
the final implementation; no F1 result is final-product acceptance.

| IDs | Area | Planned stage | Current status |
| --- | --- | --- | --- |
| A01 | Baseline before/after | F1/F7 | PASS for F1 evidence capture: initial failures and current results recorded separately; make verify passes, grok_verify remains FAIL with BLOCKED_TRIVY_HEALTHCHECK_POLICY |
| A02–A06 | Exact calculation, validation, identity | F2–F3 | NOT_RUN |
| A07 | Live source outage | F3 | NOT_RUN |
| A08–A09 | Bundle tamper/offline replay | F3 | NOT_RUN |
| A10–A12 | 402, invalid payments, atomic units | F4–F5 | NOT_RUN |
| A13–A14 | Real testnet payment and repeat access | F5/F7 | BLOCKED_EXTERNAL — PAY_TO_MISSING, FINALITY_RULE_UNVERIFIED, funded buyer absent; no payment or repeat-access run |
| A15–A20 | Concurrency, idempotency, crash, expiry | F4–F5 | NOT_RUN |
| A21–A25 | Authorization, artifact loss, RPC/facilitator, redaction | F4–F5 | NOT_RUN |
| A26 | Container/network isolation | F6 | NOT_RUN |
| A27 | Stage A verdict and fixture suite | F1/F7 | PASS for F1: 623 tests and 85 subtests pass; verdict/CLI tests preserve INSUFFICIENT_EVIDENCE and exclude GO |
| A28 | Clean README install, build, offline demo | F1/F7 | NOT_RUN as a full acceptance scenario; Task 3 installed the pinned environment and F1 verifies installed wheels, but no fresh clean-machine README/demo run is claimed |
| A29 | Anonymous public clone and provenance | F1/F7 | NOT_RUN against F1: F0 publication evidence is retained in PROVENANCE.md; F1 public salvage verifies target bytes only, source_objects=unavailable; no new anonymous publication check |
| A30 | Wallet/browser recovery | F6–F7 | NOT_RUN |

Compatibility success does not satisfy A10–A25 or A30. All payment behavior
remains blocked or not run, and readiness is false. The unresolved Trivy
policy issue is a local verification failure, not an external-service outage.
