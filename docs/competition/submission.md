# Liqvera — submission draft

Prepared 2026-10-13. Existing project; pre-event baseline `607fa0d`. The owner confirms that the Liqvera entry has already been submitted to AKINDO. This session has not accessed the account or verified which attachment versions were submitted. These files remain supporting preparation materials; do not submit a duplicate.

## Ready-to-paste project fields

**Project name:** Liqvera

**Category:** MUSD payments for market reports

**TL;DR:** Spend test MUSD on BTC market-depth reports you can download and independently verify.

**How it works:** Market screenshots and headline prices hide the depth behind a hypothetical order. Liqvera captures public Hyperliquid BTC perpetual order-book snapshots and calculates filled quantity, notional, VWAP, worst price and price impact using exact arithmetic. Each canonical report includes source metadata, input hashes and a downloadable evidence bundle. An offline verifier checks integrity and recomputes the results. The gateway's x402 integration is configured for MUSD on Mezo Testnet to bind access to exact report and bundle hashes. Historical testnet paid delivery has been demonstrated. A wallet-free historical preview is available; Testnet wallet checkout is enabled at 0.01 test MUSD per report. Reports do not execute trades or include fees, funding or net P&L.

**Target group:** The initial audience hypothesis is analysts, developers and technically experienced users who want reproducible BTC market-depth evidence. The desktop-first browser and offline verifier support inspection and sharing. There is no validated customer-demand or regional-adoption claim. Track 2 fit: make MUSD useful for access to independently inspectable digital information.

**Tech stack:** TypeScript, Vite, Node.js/Express, PostgreSQL, Python, Docker Compose, Caddy, x402, and Mezo Testnet. Public Hyperliquid data; no exchange trading credentials.

**Track:** Track 2 — Access and Distribution for MUSD/MEZO.

**Chain configured:** Mezo Testnet, chain ID 31611. Public gateway and browser are deployed; merchant checkout is enabled; a new paid-delivery acceptance on this deployment has not yet been recorded.

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
- Current preview source: [f5de466](https://github.com/Dimkox/liqvera/commit/f5de466). All seven production containers now use audited images; the public preview is a new October 12 live-public Liqvera report verified offline.
- Deck: [presentation.pdf](presentation.pdf), seven slides; editable source: [presentation.html](presentation.html).
- Video: [two-minute captioned preparation cut](pitch.mp4), [public download](https://raw.githubusercontent.com/Dimkox/liqvera/main/docs/competition/pitch.mp4), [editable frames](pitch.html), and [script](pitch-script.md). Silent English captions; real interface captures; no new paid transaction is depicted. Replace the pending-payment segment and add in-event progress before the final competition upload.
- Architecture and boundaries: [specification](../specification.md).
- Local validation: [remediation report](../security/2026-10-12-remediation.md). Current deployed image IDs, advisory scans and functional evidence: [Testnet audit](../security/2026-10-12-testnet.md).
- Merchant verification: 71 gateway tests against disposable PostgreSQL and 31 browser tests at source `5f87329`. [October 13 browser evidence](2026-10-13-browser-results.json) confirms a fresh unsigned quote; [download verification](2026-10-13-verification.json) reproduces the preview ZIP. See the [entry checklist](entry-checklist.md).

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
