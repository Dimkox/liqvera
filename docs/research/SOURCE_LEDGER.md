# Research Source Ledger

Snapshot: **2026-08-18**

[Research index](README.md) · [Canonical market demand and JTBD](user-needs/README.md) · [Master research](MASTER_RESEARCH.md) · [Kakao/Korea launch gate](MASTER_RESEARCH.md#kakaotalk-south-korea-launch-gate-2026-08-18) · [Competitive code intelligence](COMPETITIVE_CODE_INTELLIGENCE.md) · [Repository README](../../README.md)

## Purpose

This ledger records the sources behind strategic and competitive claims. It separates primary technical evidence from product marketing and third-party reporting. It is not a vendored copy of external material and does not convert external claims into implemented repository capabilities.

## Confidence policy

### Tier A — primary technical evidence

Use for exact API, code, architecture, signing, repository activity and bug claims:

- official documentation;
- official SDK/repository;
- source code;
- commit history;
- release artifacts;
- issue trackers with reproducible logs;
- repository-local pinned inventories.

### Tier B — primary product/business evidence

Use for product availability, pricing, fees, partner programs and published user-facing behavior:

- official product pages;
- official help centers;
- official announcements;
- app-store listings;
- official terms.

### Tier C — independent secondary evidence

Use for adoption, financing, market context and corroboration:

- reputable reporting;
- analytics providers;
- investor announcements;
- independent technical reviews.

### Tier D — discovery-only evidence

Do not treat as settled fact without corroboration:

- YouTube demos;
- anonymous social posts;
- Reddit/forum claims without reproducible artifacts;
- unverified repository descriptions;
- SEO articles;
- unsourced user claims.

## Venue and protocol sources

### Hyperliquid

| Source | Tier | Used for |
|---|---:|---|
| https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api | A | Official API surface |
| https://hyperliquid.gitbook.io/hyperliquid-docs/trading/builder-codes | A/B | Builder-code mechanics |
| https://hyperliquid.gitbook.io/hyperliquid-docs/referrals | A/B | Referral mechanics |
| https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees | A/B | Fee model |
| https://github.com/hyperliquid-dex | A | Official code and SDK organization |

Repository-local status: Hyperliquid runtime capability must be verified from current adapters/tests. External API availability does not imply safe order lifecycle support.

### Lighter

| Source | Tier | Used for |
|---|---:|---|
| https://apidocs.lighter.xyz/docs/api-keys | A | API-key indices and account model |
| https://apidocs.lighter.xyz/docs/websocket-reference | A | WebSocket channels and sequencing |
| https://apidocs.lighter.xyz/docs/trading | A | Signing, order lifecycle and transaction behavior |
| https://apidocs.lighter.xyz/docs/account-types | A/B | Standard/Premium account behavior and latency model |
| https://apidocs.lighter.xyz/docs/rate-limits | A | Limits |
| https://apidocs.lighter.xyz/docs/partner-integration | A/B | Partner attribution and fee fields |
| https://lighter.xyz/ | B | Official product surface |

Repository-local status: public-data and authenticated capability must be tracked separately. Standard-account published latency is a planning input until measured by repository evidence.

### Variational

| Source | Tier | Used for |
|---|---:|---|
| https://github.com/variational-research/variational-sdk-python | A | Official SDK existence, releases and client surface |
| https://docs.variational.io/technical-documentation/api | A | Public API and access status |
| https://docs.variational.io/variational-protocol/key-concepts/trading-via-rfq | A | RFQ model |
| https://docs.variational.io/ | A/B | Product and protocol overview |
| https://docs.variational.io/legal/terms-of-use | A/B | Automation and use constraints |

Repository-local status: no production Variational execution is authorized without official credentials and reviewed terms.

### Extended

| Source | Tier | Used for |
|---|---:|---|
| https://github.com/x10xchange/python_sdk | A | Official Python examples, markets and order flow |
| https://github.com/x10xchange/rust-crypto-lib-base | A | Stark/Poseidon hash construction and test vectors |
| https://github.com/x10xchange/stark-crypto-wrapper-js | A | JS/WASM signing path |

Research conclusion: technically well understood, but not current first execution priority.

### Reya

| Source | Tier | Used for |
|---|---:|---|
| https://github.com/Reya-Labs/reya-python-sdk | A | EIP-712 signing, configuration and order structures |

Research conclusion: migration/config churn makes it a later integration.

### Ostium

| Source | Tier | Used for |
|---|---:|---|
| Official Ostium documentation and SDK package references recorded in historical research | A/B | Contract/API behavior and RWA product scope |

Follow-up: pin exact official repository and docs URLs before any adapter work.

## Direct and infrastructure competitors

### VOOI

| Source | Tier | Used for |
|---|---:|---|
| https://github.com/vooi-app | A | Organization inventory |
| https://github.com/vooi-app/vooi-funding-bot-example | A | Funding-bot architecture, reconciliation and live-fix evidence |
| https://github.com/vooi-app/vooi-signals-bot-example | A | Telegram-signal ingestion and execution example |

Repository-local reproducible inventory and pinned evidence should take precedence over memory or marketing summaries.

### hypurrquant/perp-cli

| Source | Tier | Used for |
|---|---:|---|
| https://github.com/hypurrquant/perp-cli | A | Multi-DEX CLI/MCP architecture, adapters, risk, rebalance and tests |
| Repository-local `perp-cli` research package | A | Pinned source inventory, surface map, auth/risk and packaging analysis |

### Hummingbot

| Source | Tier | Used for |
|---|---:|---|
| https://github.com/hummingbot/hummingbot | A | Connector/strategy framework |
| https://github.com/hummingbot/hummingbot/issues/7295 | A | Failure/fill ordering and duplicate-close risk evidence |

### PD AIO SDK

| Source | Tier | Used for |
|---|---:|---|
| https://github.com/0xarkstar/PD-AIO-SDK | A/D pending audit | Claimed unified perp-DEX SDK coverage |

Policy: do not rely on claimed venue count until adapter depth, tests, maintenance and signing correctness are audited.

### CCXT and Freqtrade

| Source | Tier | Used for |
|---|---:|---|
| https://github.com/ccxt/ccxt | A | Generic exchange adapter commoditization |
| https://github.com/freqtrade/freqtrade | A | Bot framework and Telegram/control-plane benchmark |

### goodcryptoX

| Source | Tier | Used for |
|---|---:|---|
| https://docs.goodcrypto.app/ | B | Product capabilities and platform mechanics |
| Repository-local dated GOOD mechanics package | A/B | Official-source token/revenue-share mechanics and accounting boundaries |

The closed execution engine is not publicly verified. Product claims and token economics must not be mistaken for code evidence.

### Liquid

| Source | Tier | Used for |
|---|---:|---|
| Official Liquid product surfaces | B | Multi-perp mobile product scope |
| Independent financing/product reporting recorded in competitive research | C | Funding and market context |

Follow-up: pin official site/app URLs and current venue list before future claims.

### Wallet in Telegram + Lighter

| Source | Tier | Used for |
|---|---:|---|
| https://wallet.tg/news | B | Telegram Wallet product announcements |
| Official Lighter and Wallet announcement pages recorded in PMF research | B | Lighter-perp availability inside Telegram |

### Dexari and Hyperliquid clients

| Source | Tier | Used for |
|---|---:|---|
| https://www.dexari.com/ | B | Dexari product surface |
| Official app-store listings | B | Mobile availability and declared features |

## 2026-08-18 market-demand and JTBD evidence set

The maintained synthesis is [`user-needs/README.md`](user-needs/README.md). The source set below was selected for reproducible failure sequences, current connector/API drift, or explicit budget evidence. Access/check date: **2026-08-18**.

### Order-state convergence, retries and duplicate execution

| Source | Tier | Claim supported |
|---|---:|---|
| https://github.com/hummingbot/hummingbot/issues/7294 | A | Hyperliquid order can emit failure and then a real fill, causing retry/duplicate risk |
| https://github.com/hummingbot/hummingbot/issues/7295 | A | Funding-arbitrage close can execute twice after a reported failure |
| https://github.com/hummingbot/hummingbot/issues/7032 | A | Ghost orders and exchange/local position divergence persist without authoritative correction |
| https://github.com/hummingbot/hummingbot/issues/8075 | A | Shutdown race can cancel and then create new orders, leaving live venue state |
| https://github.com/hummingbot/hummingbot/issues/8264 | A | Duplicate order-created events can break persistence and monitoring |

Interpretation: these issues support explicit `UNKNOWN`, idempotency, authoritative reconciliation, exact ownership and restart/shutdown convergence requirements. They do not prove a recurring SaaS price.

### Partial fills, cancel/fill races and residual exposure

| Source | Tier | Claim supported |
|---|---:|---|
| https://github.com/hummingbot/hummingbot/issues/7139 | A | Maker fill during cancellation can leave no taker hedge |
| https://github.com/hummingbot/hummingbot/issues/7129 | A | Partial market close can be treated as complete while strategy waits indefinitely for the remainder |
| https://github.com/hummingbot/hummingbot/issues/5984 | A | Residual hedge below venue minimum can stop a cross-exchange strategy |
| https://github.com/hummingbot/hummingbot/issues/6831 | A | Close semantics can produce wrong position behavior on a connector |
| https://github.com/hummingbot/hummingbot/issues/8132 | A | Partial-fill detection can be inconsistent for venue-specific transaction semantics |

Interpretation: these issues support cumulative-fill accounting, cancel/fill race handling, minimum-size policy, residual exposure states and emergency/manual intervention. They do not establish atomic cross-venue execution.

### Live-but-stalled streams, reconnect and stale state

| Source | Tier | Claim supported |
|---|---:|---|
| https://github.com/hummingbot/hummingbot/issues/8250 | A | Hyperliquid reconnect can log successful subscriptions while the strategy remains stalled |
| https://github.com/hummingbot/hummingbot/issues/7230 | A | Controllers can lose state and stop after network loss/recovery |
| https://github.com/hummingbot/hummingbot/issues/8308 | A | Lighter private stream can fail authentication despite basic authenticated access |
| https://github.com/hummingbot/hummingbot/issues/8309 | A | Lighter perpetual private WebSocket and polling can enter repeated 429 retry loops |
| https://github.com/hummingbot/hummingbot/issues/7730 | A | MEXC private stream can repeatedly disconnect during normal use |
| https://github.com/hummingbot/hummingbot/issues/7482 | A | Connector can omit expected trade updates |
| https://github.com/hummingbot/hummingbot/issues/7827 | A | Venue event semantics can leave local available-balance state stale for roughly two minutes |

Interpretation: connection state alone is insufficient. Health needs freshness, sequence, heartbeat, source/receive time, snapshot/recovery and REST/WS divergence evidence.

### API drift and connector maintenance

| Source | Tier | Claim supported |
|---|---:|---|
| https://github.com/hummingbot/hummingbot/issues/8035 | A | Binance private-stream endpoint deprecation can break a connector |
| https://github.com/hummingbot/hummingbot/issues/8256 | A | KuCoin API changes alter execution routes, payloads and stream handling |
| https://github.com/hummingbot/hummingbot/issues/8224 | A | Successful startup does not prove correct margin-mode order semantics |
| https://github.com/hummingbot/hummingbot/issues/7994 | A | Empty or changed funding fields can block connector readiness |
| https://github.com/hummingbot/hummingbot/issues/8307 | A | Venue-specific market metadata can break generic symbol/pair assumptions |

Interpretation: syntax normalization is commodity; semantic conformance, regression and production failure behavior remain operational work.

### Explicit connector-development budget proxies

| Source | Tier | Claim supported |
|---|---:|---|
| https://github.com/hummingbot/hummingbot/issues/7810 | B/A | EVEDEX connector bounty names a 3,000 USDC developer portion and acceptance scope |
| https://github.com/hummingbot/hummingbot/issues/8046 | B/A | GRVT perpetual connector bounty names a 3,000 USDC developer portion |
| https://github.com/hummingbot/hummingbot/issues/7919 | B/A | Architect perpetual connector bounty names a 3,000 USDC developer portion |
| https://github.com/hummingbot/hummingbot/issues/8028 | B/A | Decibel perpetual connector bounty names a 4,000 USDC developer portion |
| https://github.com/hummingbot/hummingbot/issues/7899 | B/A | Backpack spot/perpetual connector bounty names a 3,000 USDC developer portion |
| https://github.com/hummingbot/hummingbot/issues/7894 | B/A | Aevo perpetual connector bounty names a 3,000 USDC developer portion |

Interpretation: connector delivery has explicit budget evidence. Bounties are not proof that traders will buy a recurring MEE subscription; they support testing a standardized connector-conformance and regression offer.

### Evidence-strength boundary

- The GitHub issue set is primary technical evidence for specific reproduced failure modes, not a population-frequency estimate.
- Public forum and Reddit discussions remain discovery-only unless linked to reproducible artifacts or corroborated through interviews.
- Pricing ranges in the synthesis are hypotheses. Only deposits, paid pilots, procurement or renewals count as willingness-to-pay evidence.
- Product names (`MEE Evidence`, `MEE Observer`, `MEE Integrity`) are packaging hypotheses, not implemented runtime nodes.

## Market and South Korea sources

Use Korean primary/regulatory sources wherever possible. Product-market claims require current verification because app-store policy, venue restrictions and product availability can change quickly.

Pinned categories:

- Google Play crypto-app policy;
- Korean Financial Intelligence Unit/VASP requirements;
- Korean reporting on foreign-exchange app availability;
- mobile-audience measurements;
- Telegram/Kakao usage measurements;
- venue terms and geo restrictions.

Policy:

1. A store removal is not equivalent to a network-level ban.
2. A working website is not proof that a venue permits the user or an integrating frontend.
3. Telegram or Kakao distribution is not a legal exemption.
4. Marketing claims about “restoring blocked access” are excluded from the product thesis.
5. Missing exact entity, platform or legal evidence is a blocking unknown, not implied permission.

### Kakao platform and policy evidence — checked 2026-08-18

| Source | Tier | Claim supported | Time sensitivity |
|---|---:|---|---:|
| https://developers.kakao.com/terms/en/site-policies-20250304 | A/B | Kakao Developers prohibits virtual-asset services providing transactions, storage or deposits; Korean text controls conflicts | High |
| https://talksafety.kakao.com/en/policy/commercial/investmentadvising | A/B | KakaoTalk restrictions on investment-leading activity, unregistered exchange promotion and impermissible virtual-asset futures promotion | High |
| https://developers.kakao.com/docs/en/app-setting/app | A | Overseas Biz App uses D-U-N-S; individual Biz App cannot connect to Business Channel; app/admin-key configuration | Medium |
| https://developers.kakao.com/docs/en/kakaotalk-channel/common | A | App/channel connection requires same operator and matching business information; Business Channel review estimate | Medium |
| https://developers.kakao.com/docs/en/kakaologin/prerequisite | A | Redirect URI, client secret and optional OIDC prerequisites | Medium |
| https://developers.kakao.com/docs/en/getting-started/security-guideline | A | State/nonce and firewall/security guidance | Medium |
| https://developers.kakao.com/docs/en/kakaologin/callback | A | Unlink webhook verification, privacy follow-up and 3-second response | Medium |
| https://developers.kakao.com/docs/en/kakaotalk-message/common | A | Messages are user-to-user within the same service; permission review and Biz App prerequisites | Medium |
| https://developers.kakao.com/docs/en/getting-started/quota | A/B | Current quotas and paid Kakao Talk Share pricing | High |
| https://developers.kakao.com/docs/en/app-setting/paid-api | A/B | Biz Wallet pays Kakao API charges; it is not evidence of merchant checkout eligibility | High |
| https://kakaobusiness.gitbook.io/main/tool/chatbot/start/overview | A/B | KakaoTalk Channel chatbot product surface | Medium |
| https://kakaobusiness.gitbook.io/main/tool/chatbot/skill_guide/ai_chatbot_callback_guide | A | 5-second skill timeout, one-minute one-use callback and callback review estimate | Medium |

Interpretation:

- The official product catalog supports channel/chatbot/login/share/message integrations, not a documented general Telegram-style mini-app runtime.
- Technical availability does not override Kakao's prohibited-category policy.
- Public documentation does not settle eligibility of this overseas crypto-adjacent service for a Business Channel or merchant payment product. Written Kakao classification is required.

### Korean virtual-asset and AML evidence — checked 2026-08-18

| Source | Tier | Claim supported | Time sensitivity |
|---|---:|---|---:|
| https://www.kofiu.go.kr/kor/notification/notice.do | A/B | Current registry publication; 2026-06-30 snapshot and official warning context | Critical |
| https://www.fsc.go.kr/eng/pr010101/75563 | A | VASP scope and registration/AML duty | High |
| https://www.fsc.go.kr/eng/pr010101/78319 | A/B | Korean-language site, Korean promotions and payment method used as foreign-targeting evidence; enforcement consequences | High |
| https://www.fsc.go.kr/eng/pr010101/77580 | A | Travel rule threshold, information types and five-year retention under the then-current rule | Critical |
| https://www.fsc.go.kr/eng/pr010101/82683 | A/B | Virtual Asset User Protection Act effective date and high-level protections/sanctions | Medium |
| https://www.fsc.go.kr/eng/pr010101/82534 | A | Deposit segregation, custody and more-than-80% cold-storage rule details | Medium |
| https://www.fsc.go.kr/eng/pr010101/86597 | A/B | Proposed 2026 registration/AML/travel-rule changes intended for 2026-08-20 effectiveness | Critical |
| https://www.law.go.kr/lsInfoP.do?lsiSeq=283365&viewCls=lsRvsDocInfoR | A | Enacted Special Financial Transactions Act amendment record | Critical |

Interpretation:

- The exact legal entities behind Hyperliquid and Lighter were not matched to the current KoFIU spreadsheet in this pass.
- No Korean-facing venue link, signup, referral, builder fee, account connection or trading route is permitted until exact current entity and legal eligibility are proven.
- The 2026-08-20 rules must be re-checked after effectiveness; a proposal summary is not a substitute for the final text.

### Korean privacy evidence — checked 2026-08-18

| Source | Tier | Claim supported | Time sensitivity |
|---|---:|---|---:|
| https://www.law.go.kr/LSW/lsLinkCommonInfo.do?chrClsCd=010202&lsJoLnkSeq=1029334869 | A | PIPA Article 28-8 cross-border transfer framework | High |
| https://law.go.kr/LSW/lsLinkCommonInfo.do?chrClsCd=010202&lspttninfSeq=182203 | A | Overseas-transfer security, complaint/dispute and contractual protection measures | High |
| https://www.law.go.kr/LSW/lsLinkCommonInfo.do?chrClsCd=010202&lsJoLnkSeq=1029335609 | A | Domestic representative requirement framework | High |
| https://law.go.kr/LSW/lsLinkCommonInfo.do?chrClsCd=010202&lspttninfSeq=182211 | A | Current domestic-representative thresholds and management duties | High |
| https://www.law.go.kr/LSW/lsInfoP.do?lsiSeq=283839&viewCls=lsRvsDocInfoR | A | PIPA amendment effective 2026-09-11 | Critical |

Interpretation:

- The recommended discovery MVP minimizes personal data and avoids Kakao identity, venue accounts and financial data.
- Legal basis, disclosures, processors, contractual measures, retention, deletion and domestic-representative analysis must be completed before production.

## Research-only long-tail repositories

The following are discovery or follow-up audit targets, not endorsed dependencies:

- https://github.com/rhwhdgks/funding-arb-engine
- https://github.com/Nicolas-Formenton/delta-hedge
- https://github.com/aferist777/spwa-v1
- https://github.com/pa111111/funding-scout-oss
- https://github.com/NikitaPirate/fundingpulse
- https://github.com/mkzung/drift-funding-monitor
- https://github.com/buddies2705/awesome-perp-dex
- https://github.com/your-quantguy/perp-dex-tools

Each requires license, maintenance, test and security review before reuse.

## Claim discipline

Every new research claim should record:

- source URL;
- access/check date;
- source tier;
- exact claim supported;
- whether it is static or time-sensitive;
- whether it affects runtime configuration;
- confidence and unresolved conflict.

For time-sensitive facts, create a dated snapshot instead of silently updating a timeless document.

## Known evidence gaps

- direct Reddit/forum links with durable, independently reproducible evidence rather than anecdotal discussion;
- paid willingness to use `MEE Evidence` or a read-only `MEE Observer`;
- exact current adoption and retained-user data for closed competitors;
- willingness to pay by Korean users;
- real user acquisition cost;
- production quality of PD AIO SDK adapters;
- exact current Liquid backend and venue coverage;
- Variational commercial/API-access terms;
- measured Lighter latency for the repository's account class and deployment region;
- `kSHIB` authoritative economic multiplier/equivalence;
- realized cross-venue returns after full exits and capital rebalance;
- written Kakao classification of the exact public-only service and content;
- foreign Business Channel eligibility for the operating entity and category;
- exact KoFIU/legal-entity status of every venue that might be named;
- feature-level Korean VASP, investment-advice, derivatives-promotion, privacy, age, tax and consumer-law opinions;
- final post-effective interpretation of the 2026-08-20 AML rules and 2026-09-11 PIPA changes.

These gaps are validation tasks, not blanks to be filled by optimistic assumptions.
