# Liqvera — submission draft

October 23 deployed update: the Mezo DEX extension adds captured reserves and fees, Pool/Router quote agreement, exact comparison with Hyperliquid, and offline-reproducible ZIP evidence. The comparison is deployed with immutable JSON/ZIP URLs and verified in published Chrome checks. Historical payments are retained as payment evidence; the owner deferred a fresh signed purchase. [Deployment record](../security/2026-10-23-mezo-dex-deployment.md). [Implementation and verification instructions](../mezo-integration.md). The [rechecked official deadline](2026-10-23-event-facts.json) is October 26 at **15:00 UTC**; internal target 11:00 UTC, code freeze 08:00 UTC.


Prepared 2026-10-13. Existing project; pre-event baseline `607fa0d`. The owner confirms that the Liqvera entry has already been submitted to AKINDO. This session has not accessed the account or verified which attachment versions were submitted. These files remain supporting preparation materials; do not submit a duplicate.

## October 21 Wave 1 source extension

The [MUSD funding extension](wave1-musd-funding.md) adds block-bound wallet balance checks, exact report budgets, JSON observations and an assisted official Borrow handoff inside the existing checkout. October 13 preparation is explicitly identified as reused. This source update has not been deployed or applied to AKINDO in this session; no new paid acceptance is claimed. See [prepared AKINDO updates](wave1-akindo-update.md) and the [verification record](2026-10-21-funding/verification.json). The historical October 13 fields below retain their dated scope.

## Ready-to-paste project fields

**Project name:** Liqvera

**Category:** MUSD market data payments

**TL;DR:** Spend test MUSD on BTC market-depth reports you can download and independently verify.

**How it works:** Liqvera compares a hypothetical BTC order against a public Hyperliquid perpetual order book and the Mezo Testnet MUSD/BTC spot pool. Mezo token identity, reserves, decimals, actual fee and Pool/Router quotes are read at one fixed block. Exact arithmetic and raw calls travel with the downloadable evidence ZIP; its verifier rebuilds the report offline. x402 binds 0.01 test-MUSD access to exact report and bundle hashes. The current wallet-free preview and offline verification are deployed. Historical MUSD transfers are linked; the owner deferred a new signed-payment acceptance run. Spot MUSD and perpetual USD differ, and gas, Hyperliquid fees and funding are excluded.

**Target group:** The initial audience hypothesis is analysts, developers and technically experienced users who want reproducible BTC market-depth evidence. Browser-extension and mobile WalletConnect sessions support report access, while the offline verifier supports inspection and sharing. There is no validated customer-demand or regional-adoption claim. Track 2 fit: make MUSD useful for access to independently inspectable digital information.

**Tech stack:** TypeScript, Vite, Node.js/Express, PostgreSQL, Python, Docker Compose, Caddy, x402, Reown AppKit / WalletConnect, and Mezo Testnet. Public Hyperliquid data; no exchange trading credentials.

**Track:** Track 2 — Access and Distribution for MUSD/MEZO.

**Chain configured:** Mezo Testnet, chain ID 31611. Public gateway and browser are deployed; merchant checkout is enabled; a new paid-delivery acceptance on this deployment has not yet been recorded.

**Wallet access:** The published demo uses standard Reown AppKit with browser extensions, WalletConnect QR/mobile pairing, account management and session restoration. It supports multiple EVM wallets. Report preparation works before network selection; payment requires Mezo Testnet. Browser tests cover network selection, cancellation and session recovery. Physical mobile pairing and a fresh signed purchase remain outside the latest verification.

**Project status:** Existing project. The published baseline predates the buildathon. Describe and link the actual features added during the competition after they exist; do not count this preparation as work completed during Wave 1.

**Project readiness:** Testnet gateway and browser are deployed with merchant checkout enabled at 0.01 test MUSD. Public landing, health, readiness, capabilities and preview downloads pass; a fresh live report reached READY and returned the correct Testnet payment challenge. The buyer must confirm each purchase in their wallet. Historical confirmed paid delivery was on Testnet; a new paid-delivery acceptance on this deployment has not yet been recorded. The historical acceptance aggregate remains 9 PASS and 21 NOT_RUN, not an overall acceptance pass.

**Future milestones — proposals, not completed commitments:**

1. By October 26: demonstrate a clearly scoped MUSD-access improvement against the pre-event baseline, with a working supported-network flow and recorded evidence. Each payment requires the buyer’s wallet confirmation.
2. By November 15: act on Wave 1 feedback, improve report discovery and recovery usability, and show meaningful additional progress with repeatable validation.
3. Within 30 days after the event: run a small pilot with prospective report users, validate repeat usage and willingness to pay, and publish a prioritized roadmap based on evidence.

**Team info:** Dimkox — project owner. Public GitHub: https://github.com/Dimkox. This public attribution is owner-confirmed. No other member, personal name, X or LinkedIn profile is asserted; the public GitHub profile supplies none.

## Links and evidence

- Project: <https://liqvera.site>
- Public source: <https://github.com/Dimkox/liqvera>
- Current deployed source: [e80474e](https://github.com/Dimkox/liqvera/commit/e80474ea5121532cde2c470a4db399d4e1427baf). The October 23 preview contains Mezo block 16321216 and a coupled immutable JSON/ZIP pair; downloaded evidence reproduces offline. [Published browser checks](2026-10-23-mezo-dex/published-browser.json).
- Deck: [presentation.pdf](presentation.pdf), seven slides; editable source: [presentation.html](presentation.html).
- Video: [two-minute captioned preparation cut](pitch.mp4), [public download](https://raw.githubusercontent.com/Dimkox/liqvera/main/docs/competition/pitch.mp4), [editable frames](pitch.html), and [script](pitch-script.md). Silent English captions; real interface captures; no new paid transaction is depicted. This dated preparation cut does not show the October 23 DEX update; current screenshots and the updated deck are linked separately. No fresh signed-payment acceptance is claimed.
- Architecture and boundaries: [specification](../specification.md).
- Local validation: [remediation report](../security/2026-10-12-remediation.md). Current deployed image IDs, scoped scans and published checks: [October 23 deployment](../security/2026-10-23-mezo-dex-deployment.md). The [October 13 WalletConnect audit](../security/2026-10-13-walletconnect.md) remains historical evidence.
- Merchant verification: 71 gateway tests against disposable PostgreSQL and 31 browser tests at source `5f87329`. [October 13 browser evidence](2026-10-13-browser-results.json) confirms a fresh unsigned quote; [download verification](2026-10-13-verification.json) reproduces the preview ZIP. Latest wallet integration: 49 browser tests; published QR/relay and Android handoff checks pass within their documented scope. See the [entry checklist](entry-checklist.md).

## Official requirements and dates

Checked 2026-10-13 against the [AKINDO event](https://app.akindo.io/wave-hacks/OVOO0gdrVU8379D10) and its [public event API](https://api.akindo.io/public/wave-hacks/OVOO0gdrVU8379D10).

| Item | Confirmed requirement or date |
| --- | --- |
| Registration | Open; each participant needs an AKINDO account and completed entry questions. Join [Mezo Discord](https://discord.mezo.org) and request the participant Developer role. |
| Workshop | [October 13, 13:00 UTC](https://luma.com/mezo-buildathon). |
| Wave 1 | API start October 15, 15:00 UTC; submission deadline October 26, 15:00 UTC. The overview labels this October 16–26, consistent with the start in JST. |
| Wave 2 | November 2–15; confirm the platform's exact deadline and timezone when the wave opens. |
| Results | November 23, online. |
| Eligibility of product | Working supported-network deployment integrating MUSD and/or MEZO; Mezo Testnet accepted. Existing products need new integration or features during the event. |
| Required materials | Live project link, public GitHub, product deck, two-minute pitch video. Submit through AKINDO before the wave deadline. |
| Scoring | Mezo integration 30%; product/business viability 30%; technical implementation 20%; UX 10%; materials 10%. |

For a subsequent update, document actual in-event progress and recheck links. A fresh signed payment is a recommended post-update regression check, not a separately stated competition eligibility requirement. Use the owner-confirmed public attribution above; do not copy private registration details into this repository. A historical preview alone does not establish the complete current payment flow.

Registration asks for full name, email, Telegram, Discord, GitHub, experience, focus, existing-product status, country and continuation intent. The owner must review the displayed eligibility and terms; recipients must complete KYB for prizes. The official event description and required registration checkbox currently link different terms documents. Inspect the actual registration terms before accepting; this draft accepts neither.
