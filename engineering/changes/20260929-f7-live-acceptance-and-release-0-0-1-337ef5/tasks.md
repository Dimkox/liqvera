# Tasks — F7 live acceptance and release 0.0.1

- [x] Synthesize four analyses and freeze P0–P5 scope, gates, stop conditions,
  rollback, version decision, and exact authority boundaries.
- [x] Record `scope_and_design_approval` for the current scope digest.
- [x] P0 RED-first runner semantic/evidence/final-binding/A30 implementation.
- [ ] Complete P0 independent reviews after final verifier.
- [x] P1 immutable out-of-tree local acceptance and omission review: five
  configured local assertions pass, four external cases are blocked, and 21
  deliberately unconfigured cases remain not run; no case fails.
- [x] Implement local-only P2 public-read grant/allowlist/DNS boundary; no grant
  was issued and no public read was executed.
- [x] Wire the operator live CLI to the real bounded A07 executor and keep A29
  explicitly blocked when its network-byte ceiling cannot be proven.
- [x] Replace the transport-only P2 evidence with canonical semantics: A07 runs
  the real gateway report adapter against a controlled 503 and proves no
  fixture/artifact. A29 has tested hard process/disk/output envelopes but cannot
  PASS without a reviewer-verifiable preemptive network-byte cap. The durable
  UUID journal is independent of output roots and bound into every P2 grant.
- [x] Add executable browser transport timeout, redirect, credential and byte-
  cap tests plus transactional fake restart/concurrency consumption coverage.
- [x] Implement local P3 identity, twelve-confirmation finality, one-submit live
  grant, and pinned browser x402 wiring. Independent review remains pending.
- [x] Replace the incorrect facilitator-gas blocker with exact EIP-3009 buyer
  authority: the facilitator broadcasts, the buyer signs only, buyer native-gas
  spend must be zero, and transaction/Transfer/balance/finality evidence is
  checked through the approved read-only RPC seam.
- [x] Add migration 004 for immutable confirmation provenance and a separate
  `--p3-live-grants` operator path. Without the human wallet signature/output
  seam it seals A13/A14 as blocked before facilitator or RPC I/O.
- [x] Add opt-in disposable-PostgreSQL coverage for 20-pool atomic grant
  consumption, restart rejection, rollback preservation and append-only rows.
- [x] Record the approved isolated PostgreSQL 001–004 migration/idempotency and
  20-pool evidence without credentials; add the bounded signed-payload-only P3
  operator, zero-I/O preflight and linked A13/A14 acceptance evidence seam.
- [x] Apply forward-only migration 005 to the approved retained isolated DB,
  prove idempotency/schema/zero receipts, and pass all six PostgreSQL behaviors
  on a separately approved fresh disposable DB.
- [ ] Obtain exact short-lived P2 public-read grant; execute allowlisted reads.
- [ ] Obtain exact short-lived P3 testnet-write grant including buyer/payee,
  amount, one-submit budget, and buyer native-gas cap; human confirms wallet.
  Migrations 001–004 are proven only on the approved isolated disposable DB;
  exact grant/wallet/RPC/facilitator inputs remain absent, so no live payment is
  authorized or executed.
- [ ] P4 set root product `VERSION=0.0.1`, preserve component `0.1.0`, build and
  verify manifest, artifacts, checksums, notes, scans, verifier, and reviews.
- [ ] Obtain exact P5 publication grant; fast-forward main, tag `v0.0.1`, create
  draft release/assets, re-hash, obtain final confirmation, and publish.
- [ ] Bind final receipts/evidence to exact release commit and artifacts.
