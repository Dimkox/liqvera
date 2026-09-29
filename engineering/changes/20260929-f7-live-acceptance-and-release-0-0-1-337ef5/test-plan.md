# Test plan — F7 live acceptance and release 0.0.1

## Risk-based scenarios

| Priority | Scenario | Evidence |
| --- | --- | --- |
| P0 | Runner semantics, evidence immutability, final identity | duplicate/missing/mutated cases; forged claims; stale/reused/symlink/path evidence; dirty/moved Git; partial writes |
| P0 | Verdict and linkage mutations | all PASS/FAIL/INCOMPLETE mutations; A14 requires exact passing A13 and settle count one |
| P1 | Local acceptance | fresh out-of-tree run; local A30; explicit honest omissions; A26/A28 only with real prerequisites |
| P2 | Public-read boundary | exact hosts/methods, no redirect/proxy, chain/token/decimals, malformed/oversize/rate-limit stops |
| P3 | Production payment boundary | identity/replay/finality/reorg/browser cancel/wrong-chain/unknown/no-retry; one exact testnet envelope |
| P4 | Release artifacts | two builds where reproducibility claimed; archive safety; checksum missing/extra/corrupt; secret canaries |
| P5 | Publication | old/new main OIDs, tag object/target, draft assets, download re-hash, anonymous source/tree comparison |

## Automated checks

- Unit: semantic validators, assertion dispatcher, evidence writer, identity and
  finality policies, release manifest/checksum tooling.
- Local security: exact commit/tree/plan/case/request grant binding, 15-minute
  expiry, HTTPS-only allowlist, public stable DNS resolution, exact EIP-3009
  identity, twelve canonical confirmations, one submission and 0.0001 test-BTC
  gas ceiling. These tests use fakes and perform no network or wallet action.
- Integration: local PostgreSQL/container/browser only after P0; no ambient or
  shared service. Exact public/testnet integration only under P2/P3 grants.
- Contract: schemas, frozen A01–A30 inventory, official pinned x402 types,
  release manifest and product/component version split.
- E2E: local first; one controlled testnet payment maximum; publication only
  after exact reviewed artifacts and grants.
- Static analysis: exact-lock builds, full history/current/artifact secret scans,
  dependency/image scans, pinned PR verifier, five independent review kinds.

## Manual checks

- Human verifies exact wallet chain/token/amount/recipient/expiry and numeric
  gas cap immediately before signature.
- Human verifies rendered release notes, tag target, asset names/hashes, and
  limitations immediately before draft publication.
