# Test review — fresh-quote Intl hotfix at 6df3c60

## Reviewed state

- Commit: `6df3c60a4a58a7a2022ab21c57556c7e36f8c96a`
- Tree: `5546b8945fe40ae6367bb3386e588e548453d70d`
- Behavior commit: `f34464521e85a2798a51a00c2d33cba60e809fbf`
- Scope: regression coverage, web verification, and recorded public Chrome smoke for fresh-quote date rendering.

## Decision

**PASS.** The regression exercises the real JavaScript `Intl` implementation through the shared UTC formatter, rejects reintroduction of the invalid option combination, and pins the two fresh-quote render call sites that failed in Chrome. The complete web test suite, TypeScript check, and a fresh production Vite build pass at the reviewed tree. The handoff records a bounded public Chrome smoke with stable request/quote identities and an explicit stop before payment.

## Coverage assessment

The previous formatter combined `dateStyle`, `timeStyle`, and `timeZoneName`. An independent Node exercise of that exact expression throws `TypeError`, reproducing the runtime class reported by Chromium. The new regression calls the exported `formatHistoricalDate` with a representative live timestamp, so the green assertion uses the platform `Intl` implementation rather than a stub.

The test additionally checks that:

- the removed `dateTime` helper is absent;
- the forbidden option combination is absent from `main.ts`;
- quote `snapshot_at` is routed through `formatHistoricalDate`;
- quote `expires_at` is routed through `formatHistoricalDate`.

The production diff also routes delivered-report `source_at` and receipt `confirmed_at` through the same formatter. Those two mappings are not individually source-pinned by the new test, but they share the same formatter and compile/build path; this is not a blocker for the reported fresh-quote regression.

## Verification executed

- `npm test` in `apps/mezo-web` — PASS: 27 tests, 27 passed, zero failed/skipped.
- `npm run typecheck` in `apps/mezo-web` — PASS.
- `npm exec vite build -- --configLoader runner --outDir <fresh-temp-dir>` — PASS: 476 modules transformed and production assets emitted.
- Direct Node reproduction of the removed `toLocaleString` option set — PASS: expected `TypeError` observed.
- Search of `apps/mezo-web/src` — PASS: no production `timeZoneName` use remains; the shared formatter uses valid `dateStyle`, `timeStyle`, and `timeZone: "UTC"` options.

## Public Chrome evidence

`handoff.md` records a real headless Chrome smoke against the public deployment using a synthetic EIP-6963 provider on Mezo chain 31611. It identifies request `dc776db0-ecd9-4d46-8852-0d1fffde0f03` and quote `a9c8de9b-9cb9-4a63-b2ae-c41e1ca0f799`, reports both `Snapshot time` and `Quote expires` rendered, status reached “Evidence is ready,” and no console/runtime exception occurred. The smoke explicitly stopped before the payment button, with no signature, settlement submission, or retry.

This review inspected that durable record but did not independently repeat the public browser flow. No standalone browser transcript or screenshot is present in the reviewed delta; the fingerprint-bound handoff record is therefore the evidence source for the deployed Chrome result.

## Findings

### Blocking

None.

### Non-blocking

- The regression source-pins the two quote timestamps but not the two paid-delivery timestamps changed in the same patch. Adding those assertions would improve completeness if the source-contract style remains in use.
- Public Chrome evidence is narrative rather than a retained machine log or screenshot. Future public smoke runs would be stronger with an artifact containing URL, browser result, console output, and timestamp.

## Receipt boundary

This decision is bound to commit `6df3c60a4a58a7a2022ab21c57556c7e36f8c96a` and tree `5546b8945fe40ae6367bb3386e588e548453d70d`. Repository changes after this report require a fresh receipt.
