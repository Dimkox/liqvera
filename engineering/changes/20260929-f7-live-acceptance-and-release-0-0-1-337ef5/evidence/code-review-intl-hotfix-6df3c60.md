# Code review — Intl date rendering hotfix at 6df3c60

## Reviewed state

- Commit: `6df3c60a4a58a7a2022ab21c57556c7e36f8c96a`
- Tree: `5546b8945fe40ae6367bb3386e588e548453d70d`
- Behavior commit: `f34464521e85a2798a51a00c2d33cba60e809fbf`
- Behavior base: `dcd9b6867558354aa8879fe2e4cb261b1381eabf`
- Scope: Chromium/Node `Intl.DateTimeFormat` option failure on fresh quote and paid-delivery rendering.

## Outcome

**PASS.** The repair is minimal, removes the invalid formatter, routes all four affected fresh-flow timestamps through the existing standards-safe UTC formatter, and leaves no production instance of the forbidden `dateStyle` + `timeStyle` + `timeZoneName` combination.

## Review

The removed `dateTime` helper passed `dateStyle`, `timeStyle`, and `timeZoneName` together. ECMA-402 implementations reject that combination, matching the reported Chrome `TypeError: Invalid option : option`.

The hotfix makes no API, payment, persistence, wallet, or orchestration change. It reuses `formatHistoricalDate`, whose options are `dateStyle`, `timeStyle`, and `timeZone: "UTC"`; that is a valid combination and gives the fresh flow the same deterministic timezone policy already used by the historical preview.

All affected calls were replaced:

- quote snapshot time;
- quote expiry;
- delivered report snapshot time;
- payment confirmation time.

A repository-wide production search found only two remaining `toLocaleString` option objects: the shared Mezo web formatter above and a separate legacy formatter using `dateStyle` plus `timeStyle` only. Neither contains `timeZoneName`, and no forbidden permutation remains.

The exact head adds only deployment/smoke documentation after the behavior commit. That documentation reports a fresh valid quote rendering in Chrome without proceeding to payment, consistent with the bounded hotfix.

## Findings

### Critical

None.

### Important

None.

### Minor

None.

## Verification

- `npm --prefix apps/mezo-web test` — PASS: 27 passed, zero failed/skipped.
- `npm --prefix apps/mezo-web run build` — PASS: TypeScript and production Vite build completed.
- `git diff --check f344645^..6df3c60` — PASS.
- Repository search for `dateStyle`, `timeStyle`, `timeZoneName`, and locale formatter calls — no forbidden production combination remains.
- Direct regression exercise confirms the shared formatter accepts the representative live timestamp.

## Declined to judge

- The code review did not submit a payment or mutate the deployed service.
- The already-recorded headless Chrome smoke was inspected as evidence but not independently repeated in this read-only review.
- Locale-specific presentation details vary by browser locale; the UTC instant and absence of the crashing option combination are the reviewed invariants.

## Readiness

The hotfix is ready for the route's `code_review` requirement. This result is bound to commit `6df3c60a4a58a7a2022ab21c57556c7e36f8c96a` / tree `5546b8945fe40ae6367bb3386e588e548453d70d`; any repository change invalidates the receipt.
