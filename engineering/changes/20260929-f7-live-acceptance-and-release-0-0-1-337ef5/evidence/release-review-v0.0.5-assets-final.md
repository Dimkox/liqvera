# Release review: Liqvera v0.0.5 asset-bound candidate

Date: 2026-10-01 UTC
Reviewer: `release_reviewer`
Decision: **GO for the separately gated v0.0.5 publication sequence**

This decision is bound to source commit `19284fb07fedd4909672c7e9a641cb066efbb7cc`, tree `744503327469d38be1c18f7af2413d452557bc92`, and the candidate directory `/home/pall/grok-projects/liqvera-release-0.0.5-19284fb`. It is not authorization for an external write and does not supersede the route's human gates or other required reviews.

## Findings

No release-blocking finding remains in the reviewed scope.

- The reviewed worktree was clean and matched the requested commit and tree exactly.
- Root and archived `VERSION` are `0.0.5`. The release notes and manifest distinguish the publication source commit from the already deployed browser-hotfix runtime commit `f34464521e85a2798a51a00c2d33cba60e809fbf` (tree `39bddd9cdf4ab3ab8de8cf5c7be58c30cb9b49f3`). They do not claim that the reviewed publication commit itself is deployed.
- The source archive is a reproducible `git archive` of the reviewed commit with prefix `liqvera-0.0.5/`. A fresh archive compared byte-for-byte equal and produced the same SHA-256.
- `unzip -t` passed, all 1,067 entries remain below the expected prefix, and the only archived symlink, `.agents/skills -> ../tooling/adaptive-grok-build-pro/.agents/skills`, resolves within the extracted release root.
- Installer content is unchanged from tag `v0.0.2`. Documentation and metadata truthfully retain installer version `0.0.2` and do not claim a v0.0.5 installer.
- The exact-head verification receipt is PASS. It includes a zero-result secret scan and a Trivy configuration scan with zero MEDIUM/HIGH/CRITICAL failures.
- `release.md`, `handoff.md`, release notes, and manifest consistently describe v0.0.5 as a source hotfix candidate; payment was not submitted, F7 remains incomplete, and testnet/product limitations remain explicit.
- Tag `v0.0.5` and GitHub Release `v0.0.5` were absent at review time, as required before publication. No premature publication was found.
- The hotfix is web-only. Existing rollback guidance remains applicable and preserves gateway/database state, including migration 006/UNKNOWN semantics.

## Exact candidate inventory

| File | Bytes | SHA-256 |
|---|---:|---|
| `liqvera-0.0.5-source.zip` | 2,651,686 | `36e04e8c15403f65ea8aae60e4ba11fe370e51c4d419714aba5fcdb7e627ffc2` |
| `RELEASE_NOTES.md` | 1,901 | `170becaccc16510c8fbebdf856caf84d4a304f2c7cacc1c0492c39245436ad2b` |
| `release-manifest.json` | 2,300 | `26bd334787d236d28f10f073fe3f2fd4f025e60be8dc3b7cbf06599dea8c8697` |
| `SHA256SUMS` | 360 | `212ce15145c4462ffb38613df602ed80481ea5420c7c446dcd9f1872e1a051c3` |
| `liqvera-0.0.5-source.zip.sha256` | 91 | `1dba5bd2140c8b45ae6665f6d363981f1799a86ee8f24876005949441ada4aeb` |

Both aggregate and detached checksum verification passed against these exact files.

## Publication and rollback conditions

The reviewed asset set is ready for the repository's separately authorized publication procedure, provided the operator:

1. rechecks that remote `main` and the local source identity still satisfy the documented publication precondition;
2. creates annotated tag `v0.0.5` at exactly `19284fb07fedd4909672c7e9a641cb066efbb7cc`;
3. publishes only the reviewed allowlisted assets, then downloads and re-hashes them against `SHA256SUMS`;
4. records the final tag, release, and asset identities without converting NOT_RUN or no-payment evidence into success claims; and
5. follows the documented rollback procedure if the deployed web hotfix regresses, without rolling back or mutating the gateway database.

Human-gate state and the remaining route receipts must be evaluated immediately before the external write. This review alone grants no publication, payment, deployment, or exchange-mutation authority.
