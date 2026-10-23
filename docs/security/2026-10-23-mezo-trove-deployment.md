# Mezo Trove product deployed — October 23, 2026

The existing Testnet product at [liqvera.site](https://liqvera.site) now supports
borrower Trove risk alongside the deployed DEX comparison. Source
`d63860d7af70b5ad12145b039131ac11f0d4e729` is included in main
`7a5ccbfbb22804fee87c2a63eddb3a97afb0a00c`. All seven services are healthy. PostgreSQL,
edge and the gateway network carrier were retained; no migrations or database
restore ran. Existing confirmed and manual-review payment states, receipts and
entitlements match the pre-deployment aggregate ledger.

The [machine-readable record](2026-10-23-mezo-trove-deployment.json) and
[allowlisted raw evidence](2026-10-23-mezo-trove-deployment-raw.tar.gz) bind image IDs,
source, CI, scanner results, recovery tests and public checks. Archive SHA-256:
`2efaf79d68401394bbf9482069c3c7cd1a1d5b3d852c1c64eb61a6a798e4c783`. Its manifest verifies 62 public-data
payload files. Private configs, secrets, grants, database dumps, sealed-volume
backups and browser profiles are excluded.

## Public verification

- The new browser asset is `index-CH7o6gkm.js`. Published Chrome
  checks at 320 and 1280 pixels show the Trove example, four pinned explorer links,
  no horizontal overflow and no runtime exceptions. The sealed example is explicitly
  historical: block 16323457, not current borrower advice.
- A public native request became READY in 9426 ms in one
  observed run, including polling. It captured block 16324977.
  This timing is a local observation, not a general service guarantee.
- Exact replay returned the same quote (201); a changed borrower with the same key
  returned 409, invalid checksum 400, another scope 404, and unpaid report delivery
  402 with the existing 0.01 test MUSD terms. No signature, settlement or entitlement
  was created. The public borrower was used as a test expected-payer address; wallet
  ownership was not asserted.
- Only that smoke request's own public-data artifact was exported through operator
  access. Its report digest is `233c90cf148ddc299665a10ebe32c9374e35bc8fb8119fcfc32a724d3a58d497` and ZIP digest is
  `44818adbc64b039eddc6a09a4fe8fd8dc54520615c7b1ef3021ea48bed4a8291`. The exact installed report image reproduced it with
  networking disabled. This operator verification does not claim the public paywall
  returned an unpaid report.
- Both immutable DEX and Trove preview pairs, plus the preserved older archive, match
  their source bytes. Historical verified MUSD transfers remain the owner's selected
  payment proof; no fresh signed-purchase acceptance is claimed.

## Source and image checks

[PR CI](https://github.com/Dimkox/liqvera/actions/runs/40009751538) and
[main CI](https://github.com/Dimkox/liqvera/actions/runs/40010846187) passed.
The shared offline gate completed 1101 Python tests and 85 subtests, all 98 gateway
tests with disposable PostgreSQL, and 130 browser tests. Two native RPC tests remain
explicit opt-ins. Builds, typechecks, root Ruff and docs checks passed; README totals
are enforced from actual output.

Four exact images received fresh Trivy and Grype scans. Trivy reported zero findings;
all 18 raw Grype occurrences have source-bound dispositions: verified backports,
an unrelated-product match, or the retained inactive curl configuration exception.
The curl package is **not** claimed patched. New Python behavior/TLS checks ran on
the actual images. Inherited gateway/web runtime facts are identified separately and
supported by matching critical binary/configuration hashes. No blanket zero-CVE
claim is made.

An installed-image HTTP test, without a source checkout mount, also built and
reproduced a native Trove report at block 16324628. Two harness export failures are
retained: Docker archive copying could not export tmpfs, then an unrelated host UID
could not read the original 0640 artifact. Bounded tar export and a byte-identical
public 0644 copy passed; original artifact permissions were not changed.

## Recovery and observed limits

Independent read-only review verified the exact rollout/binding hashes, images,
scans, CI and offline reproduction. Eleven isolated recovery tests cover lost replies,
repeated recovery, public-check failure, pinned assets and retained-reader restart
policies. Before exposure the retained originals are recoverable. After exposure,
recovery retains the **new gateway, report and browser**, disables new Trove creation
in both services, keeps DEX enabled and restores only the prior capture image.
Existing report delivery and payment recovery stay readable. Database restoration
is not part of rollback.

The first public probe lost a polling response; its one request had reached READY.
Four database statement timeouts were recorded in that initial window. A second
native probe passed, and no later worker failures were observed in the retained
follow-up window. The evidence records this incident without asserting an unknown
infrastructure cause was permanently eliminated. No payment was involved.
