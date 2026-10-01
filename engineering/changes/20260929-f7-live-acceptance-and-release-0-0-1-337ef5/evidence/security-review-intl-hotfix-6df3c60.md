# Security review — fresh-quote Intl hotfix

## Review binding

- Commit: `6df3c60a4a58a7a2022ab21c57556c7e36f8c96a`
- Tree: `5546b8945fe40ae6367bb3386e588e548453d70d`
- Runtime hotfix commit: `f34464521e85a2798a51a00c2d33cba60e809fbf`
- Route: `337ef5ec16a0`
- Scope: Intl/UI change, payment and wallet regression, rendering safety, and secret exposure.
- Constraints observed: read-only product review; no secret reads, external calls, wallet actions, payment, deployment, or publication mutation.

## Verdict

**PASS — no blocking security findings.** The executable hotfix is UI-only and does not alter payment, wallet, authorization, CSP, issuer, grant, ledger, or deployment behavior.

## Change analysis

The runtime change removes the local `dateTime()` helper whose `Intl.DateTimeFormat` options combined `dateStyle`, `timeStyle`, and `timeZoneName`. Four display-only call sites now use the existing `formatHistoricalDate()` helper:

- quote snapshot time;
- quote expiry;
- delivered report snapshot time;
- receipt confirmation time.

The shared helper parses the supplied value, formats valid dates with `dateStyle`, `timeStyle`, and fixed `timeZone: "UTC"`, and returns the original string for an invalid date. All results continue through `appendField()` into nodes created with `textContent`; neither valid nor fallback values gain an HTML interpretation or injection sink.

The implementation commit changes only `apps/mezo-web/src/main.ts` and its regression test. The exact reviewed HEAD additionally records publication/hotfix documentation and evidence. No payment adapter, payment guard, quote binding, wallet provider selection, account/chain revalidation, event ownership, recovery state machine, API transport, CSP, dependency, gateway, issuer pin, grant, database, or Compose file changed.

## Security regression checks

- Payment remains reachable only through the existing guarded `submitPayment()` path. Formatting happens during rendering and neither submits nor retries a payment.
- Wallet discovery, selected-provider listener ownership, exact payer comparison, and immediate account/Mezo-chain revalidation are unchanged.
- Quote subject/identity preservation, ambiguous-outcome lock, GET-only recovery, one guarded payment invocation, and evidence ZIP digest verification are unchanged.
- Dynamic date values remain text-only. No new `innerHTML`, URL construction, external origin, credential mode, or event handler was added.
- The delta contains no private key, mnemonic, grant bytes, payment signature, bearer token, database credential, report token, or credential-bearing URL. Secret-related matches in added review prose are negative assertions, not values.

## Verification evidence

- `apps/mezo-web: npm test`: **27 passed, 0 failed**. This includes payment/recovery non-resettlement, wallet revalidation and event-boundary tests, transport guards, and the new standards-safe fresh-quote formatter regression.
- `apps/mezo-web: npm run build`: **PASS** (`tsc --noEmit` and Vite production build).
- `git diff --check f344645^..6df3c60`: **PASS**.
- Targeted added-line secret/capability scan: no credential or reusable payment capability found.

The documentation records a smoke that stopped before the payment button; it claims no wallet signature, settlement submission, or retry and does not expand the authority of this review.
