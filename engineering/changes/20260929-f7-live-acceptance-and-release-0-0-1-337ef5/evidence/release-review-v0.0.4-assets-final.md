# Final publication review — v0.0.4 asset-bound candidate

Reviewed commit: `b4461ea3e3385f8bbeaa94194db57e89f3a97a23`

Reviewed tree: `6eefbde46ca5f00ef04600665fd885f1df27f547`

Staged asset root: `/home/pall/grok-projects/liqvera-release-0.0.4-b4461ea`

Decision: **PASS / GO for the separately gated publication step**

No release-blocking finding remains.

## Asset identity and reproducibility

The staged set contains exactly the expected publication inputs:

| Asset | Bytes | SHA-256 |
| --- | ---: | --- |
| `liqvera-0.0.4-source.zip` | 2,636,383 | `13346632a2b0160aeb4d3442fea9e890085d893c48df8dd698bc2a9fcaf55b80` |
| `RELEASE_NOTES.md` | 2,164 | `a8652db1faa8283b07e90dc1097baed295e61e2425765f1d08e26f6395ed9101` |
| `release-manifest.json` | 2,479 | `dddd644cf9f5f60626d8bc08ceba6b62178171cbedd68e0798dca1c7b28d7021` |
| `liqvera-0.0.4-source.zip.sha256` | 91 | `60c0dc4afc9c4dcd842eefd7378290b96cb0d54a9422a9a859ad49beb179f3c3` |
| `SHA256SUMS` | 360 | `7e83d4b53addb05e62e6c4edeb068f9bb6ba9ab61f90106529c33974fa77afe8` |

`SHA256SUMS` validates all four published payload assets, and the detached checksum independently validates the source ZIP. The ZIP passes full decompression validation, contains exactly 1,061 entries under the single `liqvera-0.0.4/` prefix, and contains root VERSION `0.0.4`.

A fresh local command equivalent to:

```text
git archive --format=zip --prefix=liqvera-0.0.4/ b4461ea3e3385f8bbeaa94194db57e89f3a97a23
```

matched the staged ZIP byte-for-byte and produced the same `133466…` digest. The manifest binds the same exact source commit/tree, archive prefix, entry count, root/component versions, deployed runtime parent, acceptance identities, asset sizes/digests, pending publication state, and truthful limitations.

## Release truth and boundaries

- Publication source is exact docs/review commit `b4461ea3…`; deployed and paid runtime remains exact parent lineage candidate `dcdc7ae6…` / tree `2459af5d…`. The manifest and notes keep those identities separate.
- Release notes correctly describe a source/evidence release, not a v0.0.4 installer.
- The independently published installer remains v0.0.2. Installer/build/verifier path bytes at `b4461ea` are identical to tag `v0.0.2`.
- Overall F7 remains `INCOMPLETE`; no NOT_RUN case is promoted to PASS.
- Payment evidence is Mezo Testnet only. No mainnet, trading, exchange mutation, custody, withdrawal, or private-venue claim is made.
- Rollback remains fail-closed and preserves migrations 003/004/006, immutable artifacts, ledger state, UNKNOWN reservations, and signed-authority budget evidence.
- The top handoff publication-review entry records the immediately preceding NO-GO checkpoint and asset-building next action; this final report is the evidence that the external ignored staging step subsequently completed without changing the bound source commit.

## Publication-state checks

- Local repository contains no `v0.0.4` tag.
- Read-only remote tag lookup returned no `refs/tags/v0.0.4`.
- Read-only GitHub release lookup returned `release not found` for `v0.0.4`.
- Manifest publication fields remain `NOT_RUN`, so no pre-publication action is falsely recorded as complete.

## Verification performed

- Exact HEAD/tree and clean product state confirmed before report creation.
- `sha256sum --check SHA256SUMS` — PASS.
- `sha256sum --check liqvera-0.0.4-source.zip.sha256` — PASS.
- `unzip -t liqvera-0.0.4-source.zip` — PASS.
- Archive prefix, entry count, and embedded VERSION checks — PASS.
- Fresh exact-commit `git archive` byte comparison — PASS.
- `git diff --check c3f985b..b4461ea` — PASS.
- Installer v0.0.2 path inventory and bytes comparison — PASS, no diff.
- Remote tag/release absence checks — PASS.

No asset byte, repository product file, deployment, payment, push, tag, or release was mutated by this review.

## Go/no-go boundary

The prior sole asset-set blocker is closed. Release review is GO for the human/route-controlled publication step using only the exact allowlisted staged assets above. Publication must still preserve the exact remote-main precondition, create annotated `v0.0.4` at `b4461ea3e3385f8bbeaa94194db57e89f3a97a23`, upload only the reviewed assets, redownload and re-hash them, and record the resulting remote/tag/release identities. This PASS is evidence, not permission to bypass the applicable publication gate.
