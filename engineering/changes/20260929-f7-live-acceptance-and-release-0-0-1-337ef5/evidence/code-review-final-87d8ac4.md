# Independent code review — web repairs and signed v2 grant authority

- Reviewer role: `code_reviewer` (read-only application review)
- Reviewed commit: `87d8ac45b11910f871e303cf1115fde5dcda36c6`
- Reviewed tree: `3300e6cfef7c5a70bcd0eb05cfdc23249f167698`
- Prior reviewed commit: `cba005b1c07aafadb4dd15743b7184143143dcf5`
- Scope: closure of the public-browser findings plus signed v2 authority, migration 006, reservation/readiness flow, and affected installer contracts
- Outcome: **FAIL / CHANGES_REQUIRED**

## Prior web-finding closure

- **I-1 CLOSED:** `createWalletListenerOwner` transfers account/chain listener ownership whenever the selected provider changes and disposes the prior binding. The executable regression begins with a prior provider, selects a late provider, and verifies old events are ignored while the late provider updates state.
- **M-1 CLOSED:** `.step` is now auto-width with a 72px minimum, horizontal padding, and `white-space: nowrap`, so `STEP 1` / `STEP 2` no longer occupy the old fixed 35×35 number box.
- Historical preview integrity is stronger than requested: exact report and ZIP SHA-256 values are verified before rendering, and download uses the verified in-memory bytes rather than refetching an unverified URL.

## Strengths

- V2 policy bytes must be duplicate-free canonical JCS, carry an Ed25519 signature, and match the configured raw-key fingerprint. Unknown fields, bad signatures, noncanonical payloads, excessive lifetime, and wrong runtime/payment identities fail closed.
- Migration 006 is additive and its authority/reservation rows are append-only. Reservation, budget checks, and `VERIFIED -> SUBMITTING` remain in one transaction under an authority-row lock; UNKNOWN does not refund authority.
- V1 remains exact-buyer and one-shot in the payment adapter. V2 verification still binds the facilitator result and decoded Permit2 identity to each quote payer.
- Focused unit and contract suites are green at this exact tree.

## Critical

None.

## Important

### I-1 — The published v0.0.2 installer contract is rewritten in place to include migration 006

The change modifies `installer/manifests/v0.0.2.json`, the v0.0.2 release schema, lifecycle validator, archive builder, and standalone verifier from the immutable 001–005 set to 001–006 while retaining `product_version: 0.0.2`, the same archive name/prefix, and the old v0.0.2 image/compose identities. Published v0.0.2 bytes and release evidence are already immutable and explicitly documented as migrations 001–005. The repository can therefore no longer reproduce or validate that published contract from its named v0.0.2 sources, and a newly built artifact with the same version/name would be a different product.

Do not mutate the v0.0.2 contract. Restore every v0.0.2 installer source/verifier/lifecycle boundary to 001–005. If migration 006 belongs in an installable package, introduce a new product/package version with its own schema, manifest, archive identity, compatibility and upgrade evidence; do not silently widen the released version.

Evidence: `installer/manifests/v0.0.2.json`, `installer/schemas/release-manifest.schema.json`, `installer/lib/lifecycle.py`, `scripts/build-liqvera-installer.py`, `scripts/verify-liqvera-installer.py`; conflicting frozen statements remain in `README.md:136`, `docs/architecture.md:34`, `docs/runbooks/observability.md:31`, and the approved installer spec/plan.

### I-2 — The advertised any-payer opt-in flag no longer gates any-payer behavior

Configuration and public/operator documentation still define `LIQVERA_TESTNET_DEMO_ANY_PAYER=1` as the explicit switch that permits arbitrary connected payers. Runtime parsing now derives any-payer behavior solely from a signed v2 grant: `testnetDemoAnyPayer` is validated and returned by `loadConfig`, but is never passed into composition or checked by `OfficialX402`. Consequently, setting the flag to `0` while supplying a valid v2 grant and public key still enables `ANY_VALID_X402_PAYER`. Conversely, `1` with a v1 grant remains buyer-bound. This makes an operator-visible safety control semantically false.

Choose one authoritative contract and make configuration/docs/tests agree. If signed v2 policy intentionally replaces the ambient flag, remove the flag from Compose/config/README/runbooks and make the signed policy the explicit sole authority. If the flag remains the operator opt-in, require it before accepting v2 any-payer policy and prove `flag=0 + valid v2` fails closed. Do not retain a parsed but behaviorally inert safety setting.

Evidence: `apps/mezo-gateway/src/config.ts` (`testnetDemoAnyPayer`), `apps/mezo-gateway/src/main.ts` (not propagated), `apps/mezo-gateway/src/security/live-composition.ts`, `apps/mezo-gateway/src/security/live-grant.ts`, `deploy/mezo-evidence/compose.yaml`, and `README.md:4-6`.

## Minor

None.

## Verification observed

- `npm --prefix apps/mezo-web test` — **26 passed, 0 failed**.
- `npm --prefix apps/mezo-gateway test` — build/typecheck passed; **51 passed, 7 skipped**. The seven skips require an explicitly disposable PostgreSQL URL.
- `.venv/bin/pytest -q tests/contracts/test_signed_grant_authority.py tests/installer/test_contracts.py tests/evidence_report/test_canonical_f3.py` — **14 passed**.

## Declined to judge

- No external wallet, facilitator, RPC, Mezo Testnet payment, deployment, Docker mutation, or release publication was performed.
- Disposable PostgreSQL integration was not provisioned in this review; retained evidence reports seven passing gated database tests, but this review only observed the honest skips above.
- Cryptographic primitive correctness is delegated to Node's Ed25519 implementation; this review assessed framing, canonicalization, key binding, and application usage.

## Readiness

**Not ready for a passing code-review receipt.** The web repair is closed and the signed-v2 reservation design is substantially sound, but the tree mutates an immutable published installer identity and exposes a documented opt-in flag that does not control the corresponding widening. Repair both contracts and rerun exact-tree review.
