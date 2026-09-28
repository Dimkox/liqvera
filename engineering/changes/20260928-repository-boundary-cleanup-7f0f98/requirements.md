# Requirements — Repository boundary cleanup

## Acceptance criteria

- [ ] No tracked Go source, module, root Go image, or Stage-0-only migration
  remains, while the historical source is reachable by immutable commit.
- [ ] The five carried safety invariants remain covered by Python conformance
  tests with no deleted-path references.
- [ ] No generated BMad payload remains tracked; any optional install is exact,
  integrity checked, explicit, ignored, and unrelated to product verification.
- [ ] Adaptive automation is either honestly retired or reduced to a tested
  minimal kernel; no fictitious external pin or silent fail-open completion.
- [ ] Current graph inventory is exact and product container scanning remains
  explicit after root Dockerfile removal.
- [ ] Protected migrations, schemas, vectors, fixtures, product source, and the
  import manifest are unchanged.
- [ ] F3-F7, vector, payment, acceptance, deployment, and release status claims
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
- Performance: tracked file and byte reductions are measured before/after.
- Observability: verification and independent review evidence names the exact
  final commit and reports inherited failures without waiver.
