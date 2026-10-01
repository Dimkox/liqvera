# Independent code review — public browser hotfix

- Reviewer role: `code_reviewer` (read-only application review)
- Reviewed commit: `cba005b1c07aafadb4dd15743b7184143143dcf5`
- Reviewed tree: `75151ba8b154b72fd77d3df844beb4d3eca89dac`
- Parent: `63312c3`
- Scope: historical-preview date repair, connect-time EIP-6963 discovery, public labels/version presentation, and surrounding wallet lifecycle
- Outcome: **CHANGES_REQUIRED**

## Strengths

- The historical timestamp formatter removes the invalid `dateStyle`/`timeStyle` plus `timeZoneName` combination while retaining an explicit UTC presentation and invalid-date fallback.
- Connect-time discovery emits a fresh standard `eip6963:requestProvider` event and waits for announcements before selecting from the store. It does not introduce payment or settlement retry behavior.
- The immutable historical report identity checks, wallet switch/add policy, quote payer validation, and pre-submit payment revalidation remain intact.
- The focused web test suite passes all 25 tests at the reviewed tree.

## Critical

None.

## Important

### I-1 — A provider discovered at connect time never receives account/chain listeners

`boot()` binds `bindWalletStateListeners(provider, ...)` once, using the provider known during initial module startup. The hotfix then allows `connectWallet()` to replace `provider` with a newly announced EIP-6963 provider, but it neither disposes the old listeners nor binds listeners to the selected provider. This is the principal late-wallet path introduced by this commit, so it commonly starts with listeners bound to `null` or to a different legacy provider.

After connection, `accountsChanged` and `chainChanged` from the actual wallet do not update `account`/`onChain`. The UI can consequently leave report creation enabled with stale payer/network state and create a quote for the old account; the later pre-submit validation still prevents an incorrect payment, but the browser flow becomes stranded until recovery/reset instead of promptly disabling the stale wallet state. A selected EIP-6963 provider must own the active listener subscription for its full lifetime.

Keep one disposer, call it whenever provider selection changes, bind the new provider immediately, and add an executable regression that starts with no boot provider, discovers one at click time, then emits both account and chain changes and observes the state-only sink/UI update without payment I/O.

Evidence: `apps/mezo-web/src/main.ts` (`connectWallet`, `refreshWallet`, and the one-time listener binding in `boot`); `apps/mezo-web/src/wallet-events.ts` already returns the required disposer.

## Minor

### M-1 — New `STEP 1` / `STEP 2` text is placed in the old fixed 35×35 number badge

The markup changes the two-character numeric content to six-character labels, but `.step` remains a fixed 35px square with normal whitespace and no overflow accommodation. At the configured 12px bold font the label can wrap at the space or overflow, especially under font substitution, undermining the public UI repair. Adjust the badge layout/width or separate the word and number, and cover the rendered geometry in a browser-level check rather than a source-regex assertion.

Evidence: `apps/mezo-web/src/main.ts` panel headings; `apps/mezo-web/src/style.css` `.step{width:35px;height:35px...}`.

## Verification observed

- `npm --prefix apps/mezo-web test` — **25 passed, 0 failed**.
- `npm --prefix apps/mezo-web run build` — could not execute in this shared worktree because `apps/mezo-web/node_modules/.vite-temp` is not writable (`EACCES`). TypeScript/Vite did not report a source failure before that filesystem error; this review does not relabel the build as passing.

## Declined to judge

- No deployment, wallet prompt, testnet payment, external provider, or public-site mutation was performed.
- The deployed site's current bytes were not used as authority; review is bound only to the exact commit/tree above.
- Release publication and the worktree ownership problem are release/tooling concerns outside this application-code review.

## Readiness

**Not ready for a passing code-review receipt.** The preview formatter repair is sound, but the late-provider lifecycle remains incomplete in the exact path this hotfix claims to repair. Rebind wallet listeners on provider replacement and re-review the final exact tree.
