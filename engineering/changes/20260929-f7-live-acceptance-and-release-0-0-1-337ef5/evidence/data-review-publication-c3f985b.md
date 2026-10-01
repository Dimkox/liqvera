# Final publication-fingerprint data review

Status: **PASS**
Reviewed commit: `c3f985bd8df743d6c2c0a186dcf99c69329f6b13`
Reviewed tree: `709a56736807b06424bb5450b893687e9d23eacf`
Prior data review: `data-review-paywall-live-r5.md`

## Verdict

No data implementation changed after the prior passing review. `DATA-002`
remains closed, migration 006 retains its exact pinned identity, and the new
publication evidence is consistent with the durable reservation model. No
blocking data finding remains.

## Exact-delta assessment

The delta from `95d438bad1e6bb56a74498c609585546c314cb38` to this commit is
limited to README, handoff, architecture inventory, release/change-package
documents, and review/acceptance evidence. There is no delta under gateway
application code or migrations, installer, build/verification scripts, deploy
configuration, or tests.

Migration 006 remains at SHA-256
`92e346b3fa49699b20d9edca9814d17bde4fb96046e71071c68b0c47326ef18a`
and remains pinned by the live gateway migration policy. The published v0.0.2
installer remains frozen to migrations 001–005.

## Live evidence consistency

- The acceptance record states that migration 006 was applied exactly once
  after a validated PostgreSQL custom-format backup while existing ledger and
  artifact volumes were preserved. It does not claim a destructive rebuild or
  down migration.
- The recorded signed authority is explicitly bounded by a 23-hour validity
  period, 20 submissions, total atomic amount `200000000000000000`, and one
  reservation per payer. Those values fit the reviewed migration-006 database
  constraints and signed-v2 authority model.
- Exactly one new settlement is recorded. Its initial uncertain response was
  recovered through read-only reconciliation of the existing transaction; no
  resubmission is claimed. This is consistent with permanently spent
  reservations and `UNKNOWN` confirm-only recovery.
- The acceptance record identifies the transaction, receipt block,
  confirmations, report digest, and ZIP digest. Paid JSON and ZIP delivery reuse
  the same entitlement and do not debit another reservation.
- Rollback documentation still preserves migration-006 authority rows,
  reservations, ordinals, count/amount debits, per-payer records, and UNKNOWN
  reservations. Publication does not authorize their deletion or reset.

## Read-only checks

```text
git diff --quiet 95d438b..c3f985b -- apps/mezo-gateway installer scripts deploy tests
```

Result: **PASS** (no product/test delta).

```text
sha256sum apps/mezo-gateway/migrations/006_signed_live_grant_authority.sql
```

Result: exact pinned digest above.

```text
git diff --check 95d438b..c3f985b
```

Result: **PASS**.

No database, network, payment, deployment, or publication mutation was
performed by this review.

## Decision

Data review passes for commit
`c3f985bd8df743d6c2c0a186dcf99c69329f6b13` / tree
`709a56736807b06424bb5450b893687e9d23eacf`. Record a passing route receipt
only while this exact repository/spec binding remains current.
