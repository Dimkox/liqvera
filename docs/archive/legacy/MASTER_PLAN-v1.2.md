# Master Project TODO & Research
## Multi-Exchange Execution OS + Private Solana Intelligence Terminal

**Версия:** 1.2  
**Дата:** 6 августа 2026  
**Предыдущая версия:** 1.1 (6 августа 2026)  
**Статус:** живой мастер-документ  
**Назначение:** единая точка правды по проекту, исследованиям, архитектуре, конкурентам и задачам

---

# Changelog 1.1 → 1.2 (6 августа 2026)

- **Совмещены два контура в одном продукте / репозитории:**
  1. Cross-exchange perpetual execution & risk engine (HL, Lighter, Variational, CEX) — уже bootstrapped.
  2. Private Solana Intelligence & Execution Terminal (Observe→Shadow→Paper→Live, Wallet DNA, Copy Score, Anti-Copy) — полный backlog в `docs/SOLANA_TERMINAL_TODO.md`.
- Product charter Solana: `docs/solana-product-charter.md`.
- ADR-0001 Solana scope & non-goals: `docs/adr/0001-solana-scope-and-non-goals.md`.
- Solana — **Wave A–E** (core intelligence + gated copy/execution); cross-venue perps — **Wave F** / XVN-* после G7 Solana *или* параллельно на уже готовых HL/Lighter adapters.
- Non-goals Solana зафиксированы жёстко (нет wash volume, holder farming, custody чужих средств, SaaS).
- Signer isolation обязателен для любого Live (Solana и perps).

# Changelog 1.0 → 1.1 (6 августа 2026)

- Верифицирована стратегическая гипотеза (продукт = execution OS, а не frontend).
- Подтверждена интеграция Lighter в Wallet in Telegram (апрель 2026).
- Зафиксированы официальные latency/fee tiers Lighter Standard / Premium / Plus.
- Проведён архитектурный аудит VOOI funding-bot-example и perp-cli.
- Подтверждено существование kSHIB на Hyperliquid; **multiplier подтверждён live meta (1 unit = 1000 SHIB, szDecimals=0)**.
- Уточнён статус Variational (SDK есть, full trading API gated).
- Обновлены секции 5, 6, 12, 13, 16, 20.
- Добавлен Decision D-009.
- Отмечены выполненные research-пункты.

---

# 0. Краткий вывод

Проект — **единый Multi-Exchange Execution OS** с двумя операционными контурами в одном репозитории:

### Контур A — Solana Intelligence & Gated Execution (Wave A–E)

Приватный аналитико-торговый терминал:

- near-real-time ingest Solana mainnet;
- decode Pump.fun / Raydium / Meteora / Orca / Jupiter / SPL;
- Wallet DNA, Token Risk, strategy classification, **Copy Score**, hard **NON_COPYABLE**;
- режимы **Observe → Shadow → Paper → Live** без пропусков;
- isolated signer; Jupiter V2 primary;
- private Web UI (VPN).

Полный backlog: [`docs/SOLANA_TERMINAL_TODO.md`](docs/SOLANA_TERMINAL_TODO.md).  
Charter: [`docs/solana-product-charter.md`](docs/solana-product-charter.md).  
ADR: [`docs/adr/0001-solana-scope-and-non-goals.md`](docs/adr/0001-solana-scope-and-non-goals.md).

### Контур B — Cross-exchange Perp Execution (уже в коде + Wave F)

> **Execution and risk engine для дельта-нейтральной торговли между DEX и CEX.**

Площадки:

- Hyperliquid — adapter + market data + trading (dry-run/live path) **готовы**;
- Lighter — market data + trading adapter **готовы**; shadow scanner HL↔Lighter **готов**;
- Variational — после official API;
- Bybit / MEXC / HTX — CEX hedge legs;
- Extended — later DEX.

Moat **не** в количестве коннекторов (commoditized), а в:

- двухногом исполнении + reconciliation + partial fill + residual hedge;
- нормализации инструментов (kSHIB = 1000 SHIB);
- net P&L после всех fees/latency;
- для Solana — в отказе копировать некопируемое и в честном follower PnL.

**Статус (6 авг 2026):** гипотеза execution-OS подтверждена; HL/Lighter bootstrap в repo; Solana backlog вписан в тот же MASTER_PLAN как primary product surface для intelligence + copy.

---

# 1. Предыстория проекта

## 1.1. Исходная идея

Первоначальная идея:

- мобильный доступ к perp DEX без официальных приложений;
- Telegram Mini App вместо Kotlin/Android;
- worldwide distribution;
- приоритет tier-2/3 GEO;
- монетизация через builder fees и referrals;
- первоначальные площадки: Extended, Reya, Ostium.

Причины выбора Telegram Mini App:

- дешевле native-разработки;
- не нужен Google Play review;
- быстрые обновления;
- прямая воронка из Telegram;
- удобные push-уведомления через бота;
- меньше зависимости от блокировок магазинов приложений.

## 1.2. Исходная техническая база

Было проведено глубокое техническое исследование:

### Extended

- Starknet;
- SNIP-12;
- Poseidon;
- Stark curve;
- builder fee;
- referral program;
- официальный Python SDK;
- Rust crypto library;
- JS WASM wrapper;
- тест-векторы;
- квантование;
- expiration;
- signed i64 conversion;
- builder fee в order hash.

### Reya

- EIP-712;
- ABI-encoded order inputs;
- packed nonce;
- separate cancellation signature;
- remote config из-за Evolution migration.

### Ostium

- Arbitrum contracts;
- Python SDK;
- RWA perps;
- отдельные особенности limit/stop.

## 1.3. Существующий Hyperliquid-бот

Позже выяснилось, что уже существует работающий бот:

- подключён к Hyperliquid;
- является адаптированным клоном HTX futures grid-бота;
- совершил более $10 000 собственного объёма;
- видит динамические рынки;
- видит `DOGE-USDC`;
- видит `kSHIB`;
- частично умеет торговать.

Это изменило приоритеты.

Hyperliquid стал не новой интеграцией, а:

- исходным адаптером;
- тестовой площадкой;
- источником реального order lifecycle;
- полигоном для refactor;
- первой ногой будущего арбитража.

---

# 2. Почему мы изменили стратегию

## 2.1. Мобильный клиент перестал быть уникальным

За время исследования появились или были обнаружены:

- официальные mobile apps;
- Hyperliquid clients;
- Lighter mobile;
- Wallet in Telegram с Lighter;
- Liquid;
- goodcryptoX;
- Dexari;
- Apex Mini App;
- другие специализированные клиенты.

Следовательно, оффер «DEX в телефоне» недостаточен.

## 2.2. Lighter уже встроен в Telegram

Критический конкурентный факт (подтверждён 6 авг 2026):

- Lighter доступен внутри Wallet in Telegram с 2 апреля 2026;
- 50+ рынков, до 50x leverage, native experience;
- сам факт «Lighter in Telegram» уже не является преимуществом.

Следовательно, Lighter должен быть execution venue, а не центром маркетинга.

## 2.3. Multi-DEX aggregation уже существует

Обнаружены и аудированы продукты:

- Liquid (Paradigm-backed);
- goodcryptoX;
- VOOI (unified API + open-source funding bot);
- perp-cli (hypurrquant);
- Hummingbot;
- PD AIO SDK;
- другие frameworks.

Следовательно, оффер «один интерфейс для нескольких perp DEX» тоже недостаточен.

## 2.4. Funding scanner уже commoditized

На GitHub существует большое количество:

- funding scanners;
- Telegram alerts;
- arbitrage dashboards;
- exchange adapters;
- basic bots.

Следовательно, scanner — функция, но не moat.

## 2.5. Главная сложность — execution correctness

Исследование Hummingbot и других проектов показало реальный failure mode:

```text
close order sent
→ failure event
→ fill event
→ retry
→ duplicate close
→ reversed exposure
```

(Документированный race condition в Hummingbot Hyperliquid perpetual, issue #7295.)

Значит, самая сложная и ценная часть продукта:

- не увидеть spread;
- не отправить REST request;
- а правильно определить состояние после timeout, reject, late fill и restart.

---

# 3. Текущая формулировка продукта

## 3.1. Что строим

> **Execution OS для торговли perp-инструментами между несколькими DEX и CEX.**

Telegram Mini App является:

- панелью управления;
- интерфейсом портфеля;
- экраном opportunities;
- системой уведомлений;
- подтверждением действий.

Backend является настоящим продуктом.

## 3.2. Основные режимы

### Unified portfolio

- балансы;
- позиции;
- funding;
- realized/unrealized P&L;
- margin;
- venue health.

### Funding arbitrage

- long на одной площадке;
- short на другой;
- net funding после fees и exit cost.

### Price/basis arbitrage

- сравнение executable VWAP;
- simultaneous or hedge-first execution;
- закрытие при convergence.

### DEX ↔ CEX hedge

- DEX как источник opportunity;
- CEX как ликвидная hedge leg.

### RFQ arbitrage

После Variational API:

```text
Variational RFQ
→ compare hedge VWAP
→ accept quote
→ immediate hedge
```

---



## 3.0. Единый продукт (v1.2)

Один репозиторий `multi-exchange-engine` обслуживает:

| Контур | Стек (MVP) | Режим Live |
|--------|------------|------------|
| Solana intelligence + copy | Rust modular monolith + isolated signer + TS UI | только после G0–G6 |
| Perp cross-venue (HL/Lighter/…) | Python adapters (уже) → позже unified venue traits | dry-run → Paper → tiny Live |

Общие принципы:

- risk/execution correctness > UI;
- Observe/Shadow/Paper перед Live;
- signer / keys вне analytics и UI;
- instrument registry + precision quantization;
- reconciliation = source of truth по позициям.

Solana non-goals (wash, farming, custody, SaaS) — **жёсткие**.  
Perp non-goals: не строить moat на «ещё одном агрегаторе UI».


# 4. Текущий приоритет площадок

1. Hyperliquid
2. Lighter
3. Bybit
4. Variational
5. MEXC
6. Extended
7. HTX
8. Reya
9. Ostium

### Hyperliquid

Уже есть работающий код и собственный объём.

### Lighter

- документированный API;
- WebSocket;
- API keys (index 0–3 reserved frontend);
- partner attribution;
- Standard / Premium / Plus account model;
- Standard: 0 fees + 200–300 ms latency;
- подходит для funding и не ультракоротких opportunities.

### Bybit

- сильный API;
- хорошая ликвидность;
- удобная hedge leg;
- CEX benchmark.

### Variational

- официальный Python SDK;
- API access gated (Pro not live, waitlist, trading API в roadmap);
- RFQ model;
- важный strategic differentiator.

### MEXC

- много альтов;
- потенциальные price dislocations;
- полезная hedge leg;
- сложнее качество рынков.

### Extended

- builder fee;
- низкая конкуренция;
- Stark integration уже исследована;
- но не первый execution priority.

---

# 5. Что уже проверено

## 5.1. По текущему проекту

- Hyperliquid подключён.
- Бот совершает сделки.
- Наторговано более $10 000 собственного объёма.
- Market discovery работает как минимум частично.
- Видны `DOGE-USDC` и `kSHIB`.
- Существующий код содержит HTX/grid-наследие.
- Требуется refactor до использования с пользовательскими деньгами.

## 5.2. По Lighter (обновлено 6 авг)

- есть официальный API;
- есть WebSocket;
- есть API keys (до 256 на account, index 0–3 reserved);
- есть отдельный nonce на key;
- есть partner attribution;
- есть Standard/Premium/Plus account model;
- **Standard Account (verified):**
  - Fees: 0 / 0
  - Taker latency: 300 ms
  - Maker / Cancel latency: 200 ms
- Premium: fees + staking discounts + lower latency;
- подходит для funding и не ультракоротких opportunities.

## 5.3. По Variational (обновлено 6 авг)

- существует официальный Python SDK (`variational-research/variational-sdk-python`);
- API access требует обращения к команде;
- торговая модель RFQ;
- public API / SDK не равны полноценному trading access;
- Pro not live (waitlist);
- trading API в roadmap 2026;
- reverse engineering private API не должен быть production-путём.

## 5.4. По конкурентам (обновлено 6 авг)

### VOOI

Аудировано:

- unified API;
- Lighter + Hyperliquid (+ Aster);
- production-grade open-source funding bot;
- Telegram signals example;
- REST reconciliation;
- SSE wake-up model;
- half-leg / orphan position detection;
- state snapshot + cooldown;
- margin routing;
- live bug fixes.

Структура fundbot: api / execution / position / risk / strategy / reporting.

### perp-cli (hypurrquant)

Аудировано:

- Hyperliquid + Lighter + Pacifica + Aster;
- dual-leg execution (`arb exec`);
- portfolio / risk / rebalance / bridge;
- client-id deduplication;
- pre-trade validation;
- TWAP / grid / DCA;
- MCP server (18 tools);
- Telegram/Discord alerts;
- большое количество тестов;
- Korean QA след;
- Lighter API key index default = 4.

### Hummingbot

Подтверждено наличие зрелой infrastructure framework и реальных race-condition issues (double fill on close retry).

### Closed-source competitors

- Wallet in Telegram + Lighter (live с апреля 2026);
- Liquid (Paradigm, HL + Lighter + Ostium);
- goodcryptoX (мобильные боты HL + Lighter + CEX);
- Dexari (Hyperliquid mobile).

---

# 6. Что требует проверки

## 6.1. Текущий Hyperliquid-бот

Нужно доказать:

- корректный `clientOrderId`;
- idempotency;
- обработку late fills;
- partial fills;
- reduce-only;
- reconnect;
- restart recovery;
- position reconciliation;
- builder/referral fields;
- multiplier handling;
- fee attribution;
- отсутствие повторного order submission.

## 6.2. `kSHIB` (обновлено 6 авг — live meta)

- [x] Рынок существует на Hyperliquid.
- [x] Contract model = 1 unit of underlying (linear).
- [x] `szDecimals` = **0** (live `meta` 6 авг 2026).
- [x] Canonical: **1 unit kSHIB = 1000 SHIB** (mid ≈ 0.00492 ≈ 1000 × spot SHIB).
- [x] Quantity — только целые числа.
- [ ] Price / quantity normalization в Instrument Registry.
- [ ] Matching с Bybit / MEXC / Lighter instruments (1000SHIB / SHIB1000 и т.п.).

**Статус:** multiplier подтверждён. Рынок можно включать в shadow scanner после mapping-тестов. Для live paired execution — только после полной нормализации и cross-venue verification.

## 6.3. Lighter

Нужно проверить практически:

- [ ] testnet/mainnet onboarding;
- [ ] API key lifecycle;
- [ ] nonce behavior;
- [ ] actual order latency (Standard vs Premium);
- [ ] cancel latency;
- [ ] private event ordering;
- [ ] partner fee;
- [ ] restart behavior;
- [ ] rejected transaction behavior;
- [ ] duplicate event behavior.

Официальные latency цифры уже зафиксированы (см. 5.2).

## 6.4. Variational

Нужно получить:

- [ ] API key;
- [ ] partner contact;
- [ ] sandbox;
- [ ] RFQ endpoint specification;
- [ ] quote expiry;
- [ ] execution confirmation;
- [ ] rate limits;
- [ ] fee model;
- [ ] attribution;
- [ ] GEO rules;
- [ ] commercial terms.

## 6.5. Competitor research

Глубокое исследование ещё не завершено по:

- [ ] APK analysis (lawful static only);
- [ ] web bundle analysis;
- [ ] protobuf/GraphQL extraction;
- [ ] API endpoint mapping;
- [ ] CI/CD artifact analysis;
- [ ] Korean forks;
- [ ] Korean Telegram Mini Apps;
- [ ] closed-source architecture indicators.

---

# 7. Competitive conclusions

## 7.1. Что больше не является moat

- Telegram Mini App;
- Lighter integration;
- Hyperliquid integration;
- funding scanner;
- Telegram alerts;
- basic unified portfolio;
- grid;
- DCA;
- TWAP;
- стандартные CEX adapters.

## 7.2. Потенциальный moat

### Execution correctness

- two-leg state machine;
- idempotency;
- fill reconciliation;
- duplicate protection;
- residual hedge;
- restart recovery.

### Contract normalization

- kSHIB;
- 1000SHIB;
- aliases;
- HIP-3 markets;
- RWA;
- quote differences.

### Real net P&L

- fees;
- slippage;
- funding;
- partner fees;
- builder fees;
- exit;
- rebalance;
- failed hedge cost.

### Variational RFQ

Официальный ранний доступ может дать временное преимущество.

### Korean distribution

- корейский UX;
- terminology;
- acquisition;
- support;
- onboarding;
- content;
- local partner network.

### Proprietary execution dataset

- opportunity lifetime;
- actual slippage;
- fill probability;
- venue latency;
- reject rates;
- effective capacity.

---

# 8. Build vs Buy

## Можно использовать готовое

- public market data clients;
- standard exchange SDK;
- CEX metadata;
- Telegram notifications;
- charts;
- basic funding history;
- generic wallet libraries;
- logging/metrics stack;
- basic REST clients.

## Можно использовать как benchmark

- VOOI examples (funding bot + signals);
- perp-cli;
- Hummingbot;
- PD AIO SDK;
- CCXT;
- Freqtrade.

## Нельзя полностью отдавать наружу

- order state machine;
- reconciliation;
- residual hedge;
- risk reservation;
- normalized instrument registry;
- P&L attribution;
- user-level limits;
- kill switch;
- execution history;
- venue scoring.

## VOOI shortcut

Возможный быстрый MVP:

- использовать VOOI API для Lighter + Hyperliquid;
- поверх сделать Korean UX и strategy layer.

Риски:

- зависимость от конкурента;
- fee;
- lock-in;
- order flow exposure;
- VOOI может сам выйти в Корею;
- слабый moat.

Рекомендация (подтверждена 6 авг):

- benchmark и прототип — да;
- единственная production dependency — нет.

---

# 9. Целевая архитектура

```text
Telegram Mini App / Web
        ↓
API Gateway
        ↓
Portfolio / Strategy / Notifications
        ↓
Opportunity Engine
        ↓
Risk Engine
        ↓
Execution Coordinator
        ↓
Exchange Adapters
        ├── Hyperliquid
        ├── Lighter
        ├── Bybit
        ├── Variational
        ├── MEXC
        ├── Extended
        └── HTX
```

## Core services

### Market Data Service

- public WebSocket;
- snapshot + delta;
- sequence;
- checksum;
- stale detection;
- reconnect.

### Instrument Registry

- canonical asset;
- venue symbol;
- multiplier;
- tick;
- step;
- min quantity;
- quote;
- settlement;
- market status.

### Opportunity Engine

- VWAP;
- funding;
- basis;
- capacity;
- opportunity decay;
- net edge.

### Execution Coordinator

- paired execution;
- maker-first;
- simultaneous;
- RFQ-first;
- partial fill;
- residual hedge;
- close.

### Risk Engine

- max notional;
- net delta;
- margin;
- unhedged timeout;
- daily loss;
- venue health;
- kill switch.

### Reconciliation Service

- private stream;
- REST state;
- open orders;
- fills;
- positions;
- unknown-state resolution.

---

# 10. Execution state machine

```text
CREATED
→ PREFLIGHT
→ RISK_RESERVED
→ LEG_A_SENT
→ LEG_B_SENT
→ PARTIALLY_FILLED
→ HEDGING
→ OPEN
→ CLOSING
→ CLOSED
```

Failure states:

```text
UNKNOWN
DEGRADED
FAILED
MANUAL_INTERVENTION
```

Главное правило:

```text
request uncertain
→ private events
→ open orders
→ fills
→ position delta
→ retry only after reconciliation
```

---

# 11. Master TODO

## 11.0. Solana Terminal (полный backlog)

Исполняемый backlog Solana-контура вынесен в отдельный документ (тот же repo):

- **[`docs/SOLANA_TERMINAL_TODO.md`](docs/SOLANA_TERMINAL_TODO.md)** — фазы 0–13, P0/SOL/DEC/TOK/WAL/…, гейты G0–G9, первые 20 коммитов.
- Charter / ADR: `docs/solana-product-charter.md`, `docs/adr/0001-solana-scope-and-non-goals.md`.

Порядок: **Wave A (данные)** → B (intelligence) → C (Shadow/Paper) → D (execution) → E (ops) → **Wave F (XVN cross-venue, HL/Lighter уже частично готовы)**.

До первых 20 Solana-коммитов (TODO §14) не начинать Live UI и native arb.

Ниже — исходный Master TODO по perp-контуру (Lighter/HL), который остаётся в силе.


## P0 — Repository and audit

- [ ] Создать clean repository.
- [ ] Составить file map текущего HTX/Hyperliquid бота.
- [ ] Выделить HTX-specific assumptions.
- [ ] Выделить grid strategy.
- [ ] Выделить Hyperliquid adapter.
- [ ] Зафиксировать current behavior integration tests.
- [ ] Зафиксировать DOGE market test.
- [ ] Зафиксировать kSHIB discovery test.

## P0 — Numeric correctness

- [ ] Перейти на Decimal/fixed-point.
- [ ] Запретить float для денег.
- [ ] Добавить finite validation.
- [ ] Добавить tick/step rounding tests.
- [ ] Добавить min-notional tests.
- [ ] Добавить multiplier tests.
- [x] Подтвердить kSHIB multiplier (live meta: 1 unit = 1000 SHIB, szDecimals=0).

## P0 — Order lifecycle

- [ ] Реализовать `clientOrderId`.
- [ ] Реализовать idempotency keys.
- [ ] Хранить raw request hash.
- [ ] Хранить venue order ID.
- [ ] Хранить fill IDs.
- [ ] Реализовать late-fill resolution.
- [ ] Реализовать duplicate-fill protection.
- [ ] Реализовать unknown-state workflow.
- [ ] Реализовать restart reconciliation.

## P0 — Risk

- [ ] Max order notional.
- [ ] Max venue exposure.
- [ ] Max net delta.
- [ ] Max unhedged duration.
- [ ] Max slippage.
- [ ] Daily loss limit.
- [ ] Venue health.
- [ ] Global kill switch.

## P0 — Lighter market data

- [x] Market metadata client.
- [x] Instrument mapping.
- [x] Public WS.
- [x] Snapshot.
- [x] Delta.
- [x] Sequence-gap recovery.
- [x] Stale detection.
- [x] Reconnect.
- [x] Funding feed.
- [x] Latency metrics.

## P0 — Lighter trading

- [x] Account onboarding. (lookup_account_index helper)
- [x] API key generation/import. (via official SDK / UI; adapter accepts key)
- [x] API key index handling. (default 4+)
- [x] Nonce manager. (SDK optimistic + explicit api_key_index)
- [x] Place limit.
- [x] Place IOC.
- [x] Place market.
- [x] Cancel.
- [x] Cancel all.
- [ ] Private stream. (structure ready; auth WS next)
- [x] Fill storage. (in-memory hooks)
- [x] Position storage. (in-memory hooks)
- [x] Reconciliation. (resolve_order_state)
- [x] Restart recovery. (local state + resolve)

## P0 — Lighter partner attribution

- [ ] Integrator account.
- [ ] User approval.
- [ ] System fee limits.
- [ ] Maker fee config.
- [ ] Taker fee config.
- [ ] Fee disclosure.
- [ ] Revenue reconciliation.
- [ ] Disable fee where edge is too small.

## P0 — Hyperliquid refactor

- [ ] Dynamic instruments.
- [ ] Separate public/private clients.
- [ ] Order gateway.
- [ ] Position reader.
- [ ] Fill listener.
- [ ] Reconciliation.
- [ ] Builder code config.
- [ ] Referral config.
- [ ] HIP-3 alias handling.
- [ ] DOGE tests.
- [ ] kSHIB tests.
- [ ] Remove grid coupling.
- [ ] Remove HTX symbol assumptions.

## P1 — Shadow scanner

- [ ] BTC.
- [ ] ETH.
- [ ] SOL.
- [ ] DOGE.
- [ ] SHIB after normalization.
- [ ] L1 spread.
- [ ] VWAP $100/$500/$1k/$5k.
- [ ] Entry fees.
- [ ] Exit fees.
- [ ] Partner fees.
- [ ] Builder fees.
- [ ] Funding.
- [ ] Slippage buffer.
- [ ] Latency buffer.
- [ ] Rebalance cost.
- [ ] Edge at 100/300/500 ms and 1/5 sec.
- [ ] Maximum executable size.
- [ ] Simulated fills.
- [ ] Minimum 7 days shadow run.
- [ ] Daily report.

## P1 — Live paired execution

- [ ] Manual confirmation.
- [ ] $50–100 per leg.
- [ ] One user.
- [ ] One execution worker.
- [ ] One strategy.
- [ ] Partial-fill handler.
- [ ] Residual hedge.
- [ ] Emergency close.
- [ ] Daily loss limit.
- [ ] 100 complete paired executions.
- [ ] Zero lost fills.
- [ ] Zero unresolved position mismatch.

## P1 — Bybit

- [ ] Public WS.
- [ ] Private WS.
- [ ] Linear perp markets.
- [ ] Order placement.
- [ ] IOC.
- [ ] Position mode.
- [ ] Reduce-only.
- [ ] Funding.
- [ ] Fee tier.
- [ ] API vault.
- [ ] IP whitelist guide.
- [ ] Withdraw disabled validation.
- [ ] Emergency hedge.

## P1 — Variational access

- [ ] Contact team.
- [ ] Request API key.
- [ ] Request sandbox.
- [ ] Request partner/integrator status.
- [ ] Request RFQ docs.
- [ ] Request rate limits.
- [ ] Request fee model.
- [ ] Request attribution model.
- [ ] Request geo policy.
- [ ] Request allowed automation scope.
- [ ] Review official Python SDK.
- [ ] Build read-only adapter.
- [ ] Build RFQ adapter after approval.

## P2 — MEXC

- [ ] Public market data.
- [ ] Private data.
- [ ] Perp order adapter.
- [ ] Funding.
- [ ] Symbol mapping.
- [ ] Altcoin liquidity filters.
- [ ] Fake-depth protection.
- [ ] Delisting risk.
- [ ] Hedge integration.

## P2 — Telegram Mini App

- [ ] Dashboard.
- [ ] Markets.
- [ ] Funding.
- [ ] Opportunities.
- [ ] Positions.
- [ ] Executions.
- [ ] Strategies.
- [ ] Risk.
- [ ] Accounts.
- [ ] Notifications.
- [ ] Korean UI.
- [ ] Korean terminology.
- [ ] Korean onboarding.
- [ ] Korean risk explanations.
- [ ] Telegram init-data verification.
- [ ] Re-auth for trade.
- [ ] Command nonce.
- [ ] Idempotency.
- [ ] Audit log.

---

# 12. Research TODO

## GitHub audit

- [x] Full file-tree audit VOOI funding bot (структура + reconciliation patterns).
- [ ] Full file-tree audit VOOI signals bot.
- [x] Full file-tree audit perp-cli (features + dual-leg + safety).
- [ ] Extract state machines (детальнее).
- [ ] Extract error taxonomy.
- [ ] Extract adapter interface.
- [ ] Extract reconciliation logic (глубже в код).
- [ ] Extract multiplier handling.
- [ ] Run tests where permitted.
- [ ] Audit PD AIO SDK.
- [ ] Audit Korean `funding-arb-engine`.
- [ ] Review Hummingbot funding arb issues (race condition confirmed).
- [ ] Review Freqtrade Telegram architecture.
- [ ] Review CCXT exchange coverage.

## APK and web analysis

Only lawful static analysis of publicly obtainable client artifacts.

- [ ] goodcryptoX APK.
- [ ] Liquid app/web.
- [ ] Dexari APK.
- [ ] Hyperliquid app.
- [ ] Wallet in Telegram web surfaces.
- [ ] Identify endpoints.
- [ ] Identify WebSocket hosts.
- [ ] Identify feature flags.
- [ ] Identify analytics stack.
- [ ] Identify error monitoring.
- [ ] Identify wallet/key model.
- [ ] Identify backend aggregation.

## Korean market

- [ ] Search Korean GitHub repositories.
- [ ] Search Korean Telegram Mini Apps.
- [ ] Search Naver blogs.
- [ ] Search Korean YouTube.
- [ ] Search X Korean crypto.
- [ ] Search DC Inside.
- [ ] Map Korean perp influencers.
- [ ] Map foreign-exchange app user migration.
- [ ] Determine acquisition costs.
- [ ] Determine legal marketing constraints.

---

# 13. Следующие 30 дней

## Week 1 (прогресс на 6 авг)

- [x] Audit current competitive landscape (hypothesis verified).
- [x] Confirm Lighter in Telegram + latency tiers.
- [x] Clone/review VOOI funding bot + perp-cli.
- [ ] Audit current bot (file map).
- [x] Confirm `kSHIB` multiplier (live meta: 1 unit = 1000 SHIB, szDecimals=0).
- [ ] Contact Variational.
- [ ] Create Lighter account/test setup.

## Week 2

- Implement Lighter metadata.
- Implement Lighter public WS.
- Build normalized order book.
- Add latency metrics.
- Refactor Hyperliquid market data.
- Add DOGE/SHIB mapping tests.

## Week 3

- Implement Lighter signing.
- Implement nonce manager.
- Implement test orders.
- Implement private stream.
- Implement fill storage.
- Implement reconciliation.

## Week 4

- Build Hyperliquid ↔ Lighter shadow scanner.
- Run BTC/ETH/SOL/DOGE.
- Start 7-day dataset.
- Produce daily net-edge reports.
- Decide whether Standard Lighter latency is acceptable.

### 30-day deliverable

```text
Working Hyperliquid adapter
+ working Lighter adapter
+ shadow scanner
+ verified opportunity dataset
+ Variational access status
```

---

# 14. Следующие 90 дней

## Month 2

- Complete shadow mode.
- Implement paired execution.
- Run small canary trades.
- Implement residual hedge.
- Implement kill switch.
- Add Bybit market data and trading.
- Start Korean landing and closed beta.

## Month 3

- Run 100 paired executions.
- Add Bybit as hedge venue.
- Implement funding strategy.
- Add Korean Mini App beta.
- Add Variational read-only or RFQ depending on access.
- Evaluate MEXC.
- Decide production architecture.

### 90-day deliverable

```text
Production-capable two-leg engine
+ Hyperliquid
+ Lighter
+ Bybit hedge
+ Korean closed beta
+ measured execution quality
```

---

# 15. Decision Log

### D-010 (2026-08-06) — Единый репозиторий: Solana Terminal + Perp Execution OS

**Решение:** Solana Intelligence & Execution Terminal **не** отдельный продукт/репо.  
Весь backlog (`docs/SOLANA_TERMINAL_TODO.md`) и charter/ADR вписаны в `multi-exchange-engine`.  
Perp adapters (HL, Lighter) остаются Wave F / XVN и уже частично реализованы.  
Live Solana только после G0–G6; cross-venue Live — G8–G9.

**Причина:** один risk/execution mindset, один operator, избежание split-brain.


## D-001: Telegram Mini App instead of Android-first

**Decision:** Telegram-first, web-compatible backend.  
**Reason:** distribution, updates, Google Play risk.  
**Status:** accepted.

## D-002: Product is execution engine, not frontend

**Decision:** backend execution OS is core.  
**Reason:** mobile and multi-DEX frontends already exist.  
**Status:** accepted (verified 6 авг).

## D-003: Hyperliquid is base adapter

**Decision:** refactor existing bot rather than rewrite immediately.  
**Reason:** working code and live volume.  
**Status:** accepted.

## D-004: Lighter is first new venue

**Decision:** integrate Lighter before Extended/Reya/Ostium.  
**Reason:** API maturity, partner attribution, arbitrage pairing.  
**Status:** accepted.

## D-005: Variational only through official access

**Decision:** no production reverse engineering of private trading endpoints.  
**Reason:** fragility, terms risk, security.  
**Status:** accepted (confirmed still gated).

## D-006: Bybit before MEXC

**Decision:** Bybit first CEX hedge venue.  
**Reason:** API quality and liquidity.  
**Status:** accepted.

## D-007: Shadow mode before live arbitrage

**Decision:** at least 7–14 days.  
**Reason:** visible spread is not executable profit.  
**Status:** accepted.

## D-008: No automatic withdrawals in MVP

**Decision:** withdraw permission prohibited.  
**Reason:** credential and custody risk.  
**Status:** accepted.

## D-009: VOOI / perp-cli as benchmark only (NEW)

**Decision:** использовать как reference и test-case source, не как production dependency.  
**Reason:** lock-in, fee, order-flow exposure, риск конкурентного выхода в Корею.  
**Status:** accepted (6 авг 2026).

---

# 16. Open Questions

## Product

- Кто первый пользователь: retail farmer, semi-pro trader или internal strategy?
- Нужен manual terminal или только strategies?
- Какая модель оплаты: subscription, partner fee, builder fee или profit share?
- Какой minimum deposit?

## Technical

- На каком языке текущий bot?
- Можно ли безопасно refactor без rewrite?
- Каков точный multiplier `kSHIB`? → **1 unit = 1000 SHIB, szDecimals=0** (подтверждено 6 авг).
- Standard Lighter latency (300 ms taker) достаточна для целевых opportunities?
- Нужен ли Premium Lighter?
- Какие venue events могут приходить out of order?
- Какой source of truth для каждого adapter?

## Variational

- Дадут ли API key?
- Есть ли sandbox?
- Разрешён ли multi-venue hedge?
- Можно ли получать executable RFQ?
- Как устроен quote expiry?
- Есть ли partner fee?

## Korea

- Какой legal classification у frontend/execution service?
- Можно ли рекламировать derivatives?
- Какие GEO правила нужны?
- Насколько Telegram достаточен для acquisition?
- Нужен ли Kakao/Naver acquisition layer?
- Есть ли спрос на self-hosted API-key bot?

## Business

- Достаточно ли 1 bps?
- Какой CAC?
- Какой volume retention?
- Каков average capital?
- Сколько стоит support?
- Какой риск platform dependency?

---

# 17. Go / No-Go критерии

## Gate 1: Lighter adapter

Go, если:

- market data стабилен;
- 100 test order lifecycles;
- zero unknown unresolved state;
- restart recovery работает.

## Gate 2: Shadow economics

Go, если:

- opportunities сохраняются после realistic latency (включая 200–300 ms Standard Lighter);
- net edge положительный после всех fees;
- capacity достаточна.

No-Go, если прибыль существует только на last price или при нулевой задержке.

## Gate 3: Live canary

Go, если:

- zero lost fills;
- residual hedge работает;
- slippage соответствует модели;
- daily loss контролируется.

## Gate 4: Korean beta

Go, если:

- onboarding понятен;
- пользователи подключают accounts;
- manual paired trade завершается;
- нет критических security incidents.

## Gate 5: Variational

Полная интеграция только при официальном API access.

---

# 18. Definition of Done MVP

- [ ] Hyperliquid и Lighter реализуют единый adapter interface.
- [ ] DOGE корректно сопоставляется.
- [x] kSHIB multiplier подтверждён (1 unit = 1000 SHIB, szDecimals=0); mapping + cross-venue verification still required.
- [ ] Есть локальные стаканы.
- [ ] Есть funding scanner.
- [ ] Есть executable VWAP.
- [ ] Shadow mode собрал минимум 7 дней.
- [ ] Есть two-leg state machine.
- [ ] Есть partial-fill handling.
- [ ] Есть residual hedge.
- [ ] Есть reconciliation.
- [ ] Есть kill switch.
- [ ] Выполнено 100 малых paired executions.
- [ ] Lost fills = 0.
- [ ] Unresolved position mismatch = 0.
- [ ] Bybit доступен как hedge leg.
- [ ] Telegram Mini App показывает portfolio и opportunities.
- [ ] Korean locale работает.
- [ ] Variational отображается только в доступном режиме.
- [ ] Все fees раскрываются пользователю.
- [ ] Withdrawal permissions не используются.

---

# 19. Source and repository queue

## Primary code sources

- `vooi-app/vooi-funding-bot-example` (audited structure)
- `vooi-app/vooi-signals-bot-example`
- `hypurrquant/perp-cli` (audited features)
- `hummingbot/hummingbot`
- `variational-research/variational-sdk-python`
- `0xarkstar/PD-AIO-SDK`
- `ccxt/ccxt`
- `freqtrade/freqtrade`

## Existing project references

- `x10xchange/python_sdk`
- `x10xchange/rust-crypto-lib-base`
- `x10xchange/stark-crypto-wrapper-js`
- `Reya-Labs/reya-python-sdk`
- `your-quantguy/perp-dex-tools`
- `buddies2705/awesome-perp-dex`

## Follow-up Korean/long-tail audit

- `rhwhdgks/funding-arb-engine`
- `Nicolas-Formenton/delta-hedge`
- `aferist777/spwa-v1`
- `pa111111/funding-scout-oss`
- `NikitaPirate/fundingpulse`
- `mkzung/drift-funding-monitor`

---

# 20. Research status

## Completed

- initial market map;
- Extended/Reya/Ostium technical research;
- Hyperliquid project status discovery;
- Lighter priority decision;
- Variational SDK discovery;
- VOOI discovery + architectural audit (structure, reconciliation, half-leg handling);
- perp-cli discovery + feature audit (dual-leg, safety, MCP);
- Hummingbot failure-mode discovery (race condition confirmed);
- Korean product positioning review;
- **Lighter Standard/Premium latency & fee tiers (official docs)**;
- **Wallet in Telegram + Lighter integration (live since Apr 2026)**;
- **Strategic hypothesis verification (6 авг 2026)**;
- **kSHIB existence on Hyperliquid confirmed**;
- **kSHIB multiplier confirmed (1 unit = 1000 SHIB, szDecimals=0)**.

## In progress

- APK/bundle acquisition;
- static client analysis;
- GitHub/CI deep audit (state machines, error taxonomy);
- API/WS/protobuf mapping;
- architecture comparison;
- code reuse/license review.

## Pending

- final competitor matrix;
- closed-source endpoint map;
- Korean local app repository map;
- production architecture comparison;
- comprehensive license matrix;
- execution state-machine comparison (детальный extract);
- Variational outreach result.

---

# 21. Final strategic statement

Проект не должен конкурировать как:

- ещё один мобильный терминал;
- ещё один Hyperliquid клиент;
- ещё один Lighter Mini App;
- ещё один funding scanner.

Проект должен конкурировать как:

> **Korean-first cross-exchange execution company, которая умеет безопасно открывать, контролировать и закрывать дельта-нейтральные позиции между DEX и CEX.**

Telegram — канал управления.

Lighter, Hyperliquid, Variational, Bybit и MEXC — площадки.

Настоящий продукт:

- state machine;
- risk engine;
- reconciliation;
- normalization;
- execution data;
- distribution.
