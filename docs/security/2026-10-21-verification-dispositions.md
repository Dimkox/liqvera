# Exact verification dispositions — 2026-10-21

This optional audit policy classifies three existing findings. It does not affect Liqvera builds, runtime, payment authority, or repository instructions. Every raw finding and original detector severity must remain in the successor report. The earlier negative audit remains unchanged.

## Public MUSD contract occurrences

The two generic-secret matches are public Testnet MUSD contract identifiers, not credentials. Both name the 20-byte contract `0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503` on chain 31611. The canonical network definition is `packages/mezo-protocol/src/index.ts`, SHA-256 `28a5c0a9143a803bbd836ab59b3aad31cd225bb6459eb97778a256aada88489b`. The finance regression uses it to test read-only balance/quote behavior. The sealed funding DOM smoke uses the same public identifier in an emulated browser test. Neither literal authorizes a wallet operation.

The policy binds each exact occurrence by normalized path, complete raw-file hash, decoded-text line/column, and exact-match hash. It does not permit other generic assignments, private keys, AWS credentials, or other occurrences in the same file. Changed bytes require renewed review.

## Immutable historical Markdown

`docs/security/2026-10-21-wave1-deployment.md` ends with a blank line at line 51. The full original Wave 1 comparison from `f1d3bffc46fa1459908fdff865fcfbfc831b7f7f` reports exactly `new blank line at EOF.`. Its SHA-256 is `2fc820a62bd6c8d453256d856f923ee2bdf812875c24fab684265883022335ba`. It is published historical deployment evidence; preserving these bytes is a user requirement. This exception covers only that exact non-executable Markdown file, diagnostic and line. No other whitespace or Git error is accepted.

## Verification boundary

`engineering/verification-dispositions.json` binds this explanation by its raw-file SHA-256. The successor Getzilla implementation must reject invalid, stale, duplicate or unsupported entries and preserve the complete comparison scope. The independent successor security review and the final frozen-candidate gate must validate the classification before a passing receipt is recorded. This explanation alone is not a passing review or an external approval.

The policy is intended for the reviewed successor of Getzilla PR #115. The unmodified PR #115 verifier still returns its original failures. Production TLS/image acceptance remains bound to the separate TLS deployment record; this policy creates no new deployment, payment, grant or database write authority.
