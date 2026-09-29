# Liqvera v0.0.1 — draft release notes

Liqvera produces market reports whose source data and deterministic analysis
can be verified offline. This release candidate adds the fail-closed Mezo
Testnet payment boundary and hardened A01–A30 acceptance evidence workflow.

## Verified in retained evidence

- A13 paid access and A14 replay passed on Mezo Testnet with one settlement of
  0.01 test MUSD, one shared transaction, 50 observed confirmations, and zero
  buyer native-gas spend.
- The corrected offline candidate passed A01, A08, A09, A27, and A30 with no
  FAIL rows. Its overall status remains **INCOMPLETE**: 4 cases are
  `BLOCKED_EXTERNAL` and 21 are `NOT_RUN`.
- Product release identity is `0.0.1`; inherited `mee-*` identifiers and
  component versions remain `0.1.0` (root workspace metadata remains
  `0.1.0.dev0`).

## Explicit limitations

- The full live result is not an overall PASS: its A08/A09 used the wrong
  interpreter and failed. Only its sealed A13/A14 evidence is cited.
- A29 anonymous public-clone verification, final release-commit acceptance,
  final artifact build/checksums, independent reviews, tag, push, and GitHub
  Release are still not run.
- No mainnet, custody, exchange mutation, private venue access, or promise of
  investment performance is included.

The final notes must replace pending commit/tree, artifact hashes, verifier
fingerprint, review receipts, and public download verification before release.
