# Evidence

Store human-readable review reports here. Machine receipts live under `.grok-stack/runtime/receipts/` and are bound to the current repository fingerprint.

## Implementation checkpoint — 2026-09-28

- Adaptive Grok source: local annotated tag `v2.0.19`, gitlink commit
  `cb9af4073ba6c3d515145164d771c75ebdfa3224`, release-sidecar SHA-256
  `4176a872acdca873e840855d0b2c9e379cf8f796c9de69e5560b3e2bf85634b9`.
- BMad source: external `bmad-method@6.10.0` package with its exact npm SRI
  recorded in `tooling/tooling-lock.json`; no package source is tracked.
- TDD red: the initial boundary suite produced seven expected failures for
  retained Go, copied framework source, missing pins, and missing launcher.
- Focused green: `python3 tooling/run-adaptive-grok.py --check` accepted the
  exact clean pin; `python3 -m pytest tests/conformance tests/graph -q`
  reported `257 passed, 3 warnings`.
- Preserved files were compared to the base: A2 raw-capture migrations,
  gateway ledger migration, SQLite demo migration, import manifest, schemas,
  vectors, and fixtures remain outside the approved removal set.
- The graph diagnostic contains only the inherited 26 implementation orphans
  and six still-active declared conflicts; no cleanup inventory, dangling-Go,
  or repository-boundary diagnostic remains.

The v2.0.19 PR verifier starts `pytest-xdist workers=22` with
`--dist=worksteal`. Diff, change-spec, secret, contract, SQL, Ruff, Bandit, and
source-stability checks pass; Python and coverage remain red because two wheel
fixtures cannot import the declared `hatchling` dev dependency from
`/usr/bin/python3`, and a pre-existing installed-demo test expects the already
absent `## F3 MVP prototype` README heading. A direct diagnostic reached
`1001 passed`, `85 subtests passed`, and the two environment errors plus that
one stale assertion before xdist stopped the run.

Trivy scanned all seven tracked product Dockerfiles explicitly. Each produced
only the inherited LOW `DS-0026` missing-`HEALTHCHECK` finding (26 of 27 checks
passed per file); none produced a medium, high, or critical finding.

Route receipts and independent reviews are still pending. A v2.0.19 state
transition reached `scoped` and then failed closed because the pre-existing
active route does not contain the gate declaration required by this newer
kernel; no approval or receipt was fabricated.
