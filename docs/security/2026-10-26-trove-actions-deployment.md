# Guarded Trove actions deployed — October 26, 2026

## Source and checks

[PR #39](https://github.com/Dimkox/liqvera/pull/39) merged as
`9615fb3d946fb44755799a2f9687fa0c35e9ea90`. Its tree
`62a4bcbba1bc475192c757dcadb3d88a65c81678` exactly matches reviewed source
`b6b77d13eecad06caf4e89f6167082159e545ddf` and the candidate image build input.
The [PR verification run](https://github.com/Dimkox/liqvera/actions/runs/40406667172)
passed every job, including the full product gate, runtime security regressions,
TLS trust and dependency audits.

The final local `make test` passed 1116 Python tests, 85 subtests, all 104 gateway
tests against its own disposable PostgreSQL ledger, and all 177 browser tests.
The two opt-in live Python tests were deselected. Protocol TypeScript compilation,
web production build, Ruff, artifact checks and documentation checks passed.
The completed local gate log SHA-256 is
`0df2d2ce77b65b3accaaf8b817c15b0df67bd0c20db6f97117ec62522aa31196`.
An earlier gate passed its constituent suites but failed the README count check
because review regressions had increased the browser count during that run; the
final gate used the fixed source and matching documented counts.

Independent read-only review of the actual diff found and reproduced protocol
capacity/exemption, cross-tab persistence and preview ordering bugs. Each was
corrected with a failing-then-passing regression. Final independent review found no
remaining delivery blockers and passed 34 focused tests. The design incorporates
BMAD adversarial and edge-case review amendments.

## User-visible behavior

The paid active-Trove report now includes rescue-to-target calculations,
collateral deposits, bounded repayment, collapsed guarded borrowing, before/after
risk previews, a second signing click and a downloadable action log. Borrowing
checks both system and borrower ratios, per-Trove capacity and fee exemption.
Every action reads live parameters and hints at its simulation block. Unknown or
pending outcomes retain a borrower-wide signing guard; recovery checks receipts
without sending another transaction. Action receipts bind the original delivery
report digest. Prepared predictions and observed post-confirmation state are
separate. The original report, sealed ZIP and x402 flow remain unchanged.

Actual local Chrome with an in-memory provider exercised rescue fill, gas-reserved
Max, preview and review with zero wallet submissions. At 320 and 1280 pixels there
was no horizontal overflow or runtime exception. These are browser checks, not
live signed-action acceptance.

## Native read-only preparation

Public RPC preparation and simulation succeeded for borrower
`0xF63F28B90f7075a640BC0911467Fa3FDbc436bf6`:

| Action | Prepared block | Amount | Estimated gas limit with margin |
| --- | --- | --- | --- |
| addColl | `0xfa1371` | 0.0005 BTC | `0x6f55c` |
| repayMUSD | `0xfa1372` | 0.5 MUSD | `0x6f44a` |

Both calls used the borrower as sender and fresh post-action insertion hints.
The read-only provider explicitly rejected signing/submission methods. Preparation
read a non-exempt borrower and a total borrowing capacity of roughly 2933.77 MUSD;
the repayment ceiling was roughly 0.958 MUSD at the observation. These are
block-specific observations, not current-price promises or transaction receipts.
The preparation summary log SHA-256 is
`0198a1e3b02519c96e90db5a3efea0d1f5444d703074681c4e5c57505d8a74c8`.

## Rollout and recovery

Built `liqvera-web-candidate:trove-b6b77d1` as image
`sha256:8988073cadbf48c803d472ac073efa4692e1e9f66a4d5d814fe3ae5278808ec7`.
Its revision label identifies `b6b77d1`. The build used the existing
`LIQVERA_WALLETCONNECT_PROJECT_ID` configuration from
`/home/pall/.local/share/liqvera/deploy/walletconnect.env`; its value is not recorded.
A disposable candidate passed Nginx configuration and HTTP/Chrome checks.

After merge and exact-tree comparison, recreated only `web-live` with the retained
operational Compose manifest and an image-only stdin override, `--no-deps`,
`--no-build`, `--pull never` and `--force-recreate`. All seven services are healthy.
The prior image remains available as `liqvera-web-candidate:bf3309b`,
`sha256:045466a49d1a3c8dc6351e98c3e560422096ad261c943b4537844da9371749d2`.
The same image-only override procedure can restore that image without changing
other services or durable volumes. No deployment manifest was rewritten.

Fresh scans of both the prior and new images report Trivy 0 findings and Grype 3
Medium matches for the retained BusyBox backport (`CVE-2025-60876`, busybox,
busybox-binsh and ssl_client). No new match or High/Critical finding appeared.
The image contains none of curl, libcurl or brotli-libs; Nginx config validation
passes. Existing backport provenance and regression checks remain in the repository.

The public index serves `/assets/index-C8aE9WEU.js`. Its SHA-256 is
`3db5aad7222a3fdc4279ed9322f6a126fd37540af2934167f89c8442498ea487`, matching the
candidate bundle. The public API remains Mezo Testnet `eip155:31611`, price 0.01
MUSD, with `payment_ready=true` and both report products available.

[Post-merge CI](https://github.com/Dimkox/liqvera/actions/runs/40407922640) was
started automatically for the identical merge tree; its final result is tracked
on that run separately from the passed PR gate.

## Wallet acceptance boundary

The owner authorized Testnet demo transactions. This agent session has no usable
MetaMask control or connected borrower signer. No wallet transaction or new report
payment was sent. No new addColl/repay transaction hash is claimed or fabricated.
Existing historical transaction evidence is preserved. Live signature, inclusion
and downloaded action receipts still need a connected borrower wallet.

No database, migration, unknown payment state, grant, sealed bundle, release asset
or Akindo page was changed by this rollout.
