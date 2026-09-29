# Tasks — F7 live acceptance and release 0.0.1

- [x] Synthesize four analyses and freeze P0–P5 scope, gates, stop conditions,
  rollback, version decision, and exact authority boundaries.
- [x] Record `scope_and_design_approval` for the current scope digest.
- [x] P0 RED-first runner semantic/evidence/final-binding/A30 implementation.
- [ ] Complete P0 independent reviews after final verifier.
- [x] P1 immutable out-of-tree local acceptance and omission review: five
  configured local assertions pass, four external cases are blocked, and 21
  deliberately unconfigured cases remain not run; no case fails.
- [ ] Obtain exact short-lived P2 public-read grant; execute allowlisted reads.
- [ ] P3 implement/review identity, finality, and browser x402 wiring.
- [ ] Obtain exact short-lived P3 testnet-write grant including buyer/payee,
  amount, one-submit budget, and numeric BTC gas cap; human confirms wallet.
- [ ] P4 set root product `VERSION=0.0.1`, preserve component `0.1.0`, build and
  verify manifest, artifacts, checksums, notes, scans, verifier, and reviews.
- [ ] Obtain exact P5 publication grant; fast-forward main, tag `v0.0.1`, create
  draft release/assets, re-hash, obtain final confirmation, and publish.
- [ ] Bind final receipts/evidence to exact release commit and artifacts.
