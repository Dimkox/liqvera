# Test plan — F7 live acceptance and release 0.0.1

## Installer Task 5

- Exercise idempotent start/stop/status, the nonblocking lifecycle lock, bounded
  redacted logs and fixed Docker argv with no volume deletion.
- Inject crashes after intent, backup, candidate start, health, migration commit
  and pointer switch; only non-irreversible phases resume automatically.
- Prove health-before-pointer update, prior preservation on failure, exact-ledger
  rollback compatibility, default data preservation and exact purge-token scope.
- Keep real Docker, database, systemd, package and host mutations NOT_RUN in PR
  tests; production update remains fail-closed without coherent backup proof.

## Installer Task 4

- Assert the seven-role Compose topology, digest-only inputs, fixture mapping,
  exact private-file secrets, internal networks, loopback edge-only publish,
  production-compatible healthchecks, users, resource bounds, aliases and
  report commit/origin configuration.
- Cover migration empty/prefix/complete retry and reject unknown, duplicate, gap,
  reorder, checksum drift, missing/extra/changed SQL against the verified
  manifest; exercise contention and a stalled query under the total lock budget.
- Exercise both mandatory honest blockers, malformed/duplicate reasons,
  post-observation and monotonic-clock timeout, partial-up/port-race candidate
  shutdown, and systemd path/escaping/restore/fallback through injected effects.
- Run gateway build/typecheck and focused migration policy tests. Real PostgreSQL
  remains NOT_RUN unless the explicit disposable test URL gate is provisioned.

## Risk-based scenarios

| Priority | Scenario | Evidence |
| --- | --- | --- |
| P0 | Runner semantics, evidence immutability, final identity | duplicate/missing/mutated cases; forged claims; stale/reused/symlink/path evidence; dirty/moved Git; partial writes |
| P0 | Verdict and linkage mutations | all PASS/FAIL/INCOMPLETE mutations; A14 requires exact passing A13 and settle count one |
| P1 | Local acceptance | fresh out-of-tree run; local A30; explicit honest omissions; A26/A28 only with real prerequisites |
| P2 | Public-read boundary | exact hosts/methods, no redirect/proxy, chain/token/decimals, malformed/oversize/rate-limit stops |
| P3 | Production payment boundary | identity/replay/finality/reorg/browser cancel/wrong-chain/unknown/no-retry; one exact testnet envelope |

The approved isolated PostgreSQL operation passed all six real database tests,
including twenty-pool single-winner consumption, restart, rollback and
append-only enforcement. Operator fake E2E proves confirmed and pending paths,
one settlement across replay, preflight zero-I/O, closed signed inputs, and
migration mismatch before any external adapter call.
Negative authority coverage changes the facilitator, RPC and database identity,
and rejects permissive, symlinked or hard-linked operator input files.
Validated grant/payment bytes are copied create-exclusive into private snapshots
and digest-bound to Node; deterministic original-path swaps cannot change either
snapshot. Receipt shape tests require the observed confirmation count, and
migration 005 persists it for replay without an RPC re-query.
| P4 | Release artifacts | two builds where reproducibility claimed; archive safety; checksum missing/extra/corrupt; secret canaries |
| P5 | Publication | old/new main OIDs, tag object/target, draft assets, download re-hash, anonymous source/tree comparison |

## Automated checks

- Unit: semantic validators, assertion dispatcher, evidence writer, identity and
  finality policies, release manifest/checksum tooling.
- Local security: exact commit/tree/plan/case/request grant binding, 15-minute
  expiry, HTTPS-only allowlist, public stable DNS resolution, exact Permit2 plus
  EIP-2612 sponsorship identity, twelve canonical confirmations, one submission and 0.0001 test-BTC
  gas ceiling. These tests use fakes and perform no network or wallet action.
- Live runner authority: current commit/tree/canonical plan, four exact case
  grants, stale/body/target/linkage mutants, one shared A13/A14 submission, and
  UNKNOWN confirm-only behavior through injected deterministic executors.
- Operator P2: actual CLI sealing with deterministic transport injection;
  response target, plan, grant, subject and byte-bound mutations fail closed.
- P2 semantics: controlled gateway `SOURCE_UNAVAILABLE` through
  `HttpReportService.build` with no fallback/artifact. A29 process memory,
  wall-time, output, single-file and aggregate-disk caps terminate early in
  tests, but A29 stays blocked because network bytes are not exactly measured.
- Authority: P2 accepts exactly A07/A29 and the approved journal identity; P3
  accepts exactly linked A13/A14. Mixed bundles and a different journal fail
  before case execution.
- Browser transport: executable timeout, redirect, ambient-credential and both
  declared/streamed response-cap tests. Durable consumption: concurrent and
  restarted adapters share one transactional fake store; real PostgreSQL proof
  remains gated on an explicitly disposable local database URL.
- Integration: local PostgreSQL/container/browser only after P0; no ambient or
  shared service. Exact public/testnet integration only under P2/P3 grants.
- Disposable PostgreSQL: with only `TEST_DATABASE_URL` and
  `TEST_DATABASE_DISPOSABLE=1`, migrate fresh 001→005 twice, verify checksums,
  race 20 separate pools through `markSubmitting`, retry after restart, inject
  an in-transaction failure, and reject update/delete of consumption rows.
- Contract: schemas, frozen A01–A30 inventory, official pinned x402 types,
  release manifest and product/component version split.
- E2E: local first; one controlled testnet payment maximum; publication only
  after exact reviewed artifacts and grants.
- Static analysis: exact-lock builds, full history/current/artifact secret scans,
  dependency/image scans, pinned PR verifier, five independent review kinds.

P3 database identity accepts only numeric loopback or fully loopback-resolved
`localhost`; remote DNS, non-loopback addresses, query/socket/TLS overrides and
fragments fail before Pool construction. Migration 005 is bound by checksum
`e99e5cffab60c08dfb1cd73d13caf2915f31aec542c26c87b016d0e125a23b11`.

## Manual checks

- Human verifies exact wallet scheme/chain/token/amount/recipient/expiry and the
  buyer native-gas cap immediately before signature. Exact Permit2 with atomic
  EIP-2612 sponsorship requires a zero buyer native-balance delta and no buyer
  chain approval; facilitator gas is not buyer authority.
- Human verifies rendered release notes, tag target, asset names/hashes, and
  limitations immediately before draft publication.
