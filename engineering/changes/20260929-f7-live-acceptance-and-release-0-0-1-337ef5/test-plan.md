# Test plan — F7 live acceptance and release 0.0.1

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
| P4 | Release artifacts | two builds where reproducibility claimed; archive safety; checksum missing/extra/corrupt; secret canaries |
| P5 | Publication | old/new main OIDs, tag object/target, draft assets, download re-hash, anonymous source/tree comparison |

## Automated checks

- Unit: semantic validators, assertion dispatcher, evidence writer, identity and
  finality policies, release manifest/checksum tooling.
- Local security: exact commit/tree/plan/case/request grant binding, 15-minute
  expiry, HTTPS-only allowlist, public stable DNS resolution, exact EIP-3009
  identity, twelve canonical confirmations, one submission and 0.0001 test-BTC
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
  `TEST_DATABASE_DISPOSABLE=1`, migrate fresh 001→004 twice, verify checksums,
  race 20 separate pools through `markSubmitting`, retry after restart, inject
  an in-transaction failure, and reject update/delete of consumption rows.
- Contract: schemas, frozen A01–A30 inventory, official pinned x402 types,
  release manifest and product/component version split.
- E2E: local first; one controlled testnet payment maximum; publication only
  after exact reviewed artifacts and grants.
- Static analysis: exact-lock builds, full history/current/artifact secret scans,
  dependency/image scans, pinned PR verifier, five independent review kinds.

## Manual checks

- Human verifies exact wallet scheme/chain/token/amount/recipient/expiry and the
  buyer native-gas cap immediately before signature. Exact EIP-3009 requires a
  zero buyer native-balance delta; facilitator gas is not buyer authority.
- Human verifies rendered release notes, tag target, asset names/hashes, and
  limitations immediately before draft publication.
