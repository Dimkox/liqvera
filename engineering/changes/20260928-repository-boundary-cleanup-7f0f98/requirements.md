# Requirements — Repository boundary cleanup

## Acceptance criteria

- [x] No tracked Go source, module, root Go image, or Stage-0-only migration
  remains, while the historical source is reachable by immutable commit.
- [x] The five carried safety invariants remain covered by Python conformance
  tests with no deleted-path references.
- [x] No generated BMad payload remains tracked; its optional external identity
  is exact, integrity pinned, and unrelated to product verification.
- [x] Adaptive automation uses a tested fail-closed launcher over the exact
  `v2.0.19` gitlink; no copied kernel or dirty/floating source is accepted.
- [x] Current graph inventory is exact and product container scanning remains
  explicit after root Dockerfile removal.
- [x] Protected migrations, schemas, vectors, fixtures, product source, and the
  import manifest are unchanged.
- [x] F3-F7, vector, payment, acceptance, deployment, and release status claims
  remain unchanged.

## Failure and edge cases

- Missing/offline/corrupt optional tool artifact.
- Dirty or wrong-version local tool cache.
- Dangling Go path or obsolete vendor-count assertion.
- Product checks silently losing Trivy coverage.
- Cleanup diff touching a protected schema, migration, vector, or fixture.

## Non-functional requirements

- Security: no silent download/execute path; integrity mismatch fails closed;
  no secret or production access.
- Reliability: ordinary product checks work without agent tooling or network.
- Performance: the selected v2.0.19 verifier uses bounded pytest-xdist workers.
- Observability: verification and independent review evidence names the exact
  final commit and reports inherited failures without waiver.
