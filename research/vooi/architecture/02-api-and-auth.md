## 3. Восстановленная схема взаимодействия

Высокодостоверная часть:

```text
Web terminal / Bot / MCP client
            |
            | HTTPS + Bearer token
            v
    perps-api.vooi.io
            |
            +-- /exchange/*
            +-- /funding-strategies/*
            +-- /transfer/*
            +-- /withdraw/*
            +-- /user-exchange/*
            +-- /mcp
```

Следующая часть является архитектурным выводом из API shape и официального
описания unified execution layer:

```text
perps-api.vooi.io
        |
        +-- common routing and account layer
        |
        +-- venue-specific adapters / signing workflows
              Hyperliquid
              Lighter
              Aster
              Extended
              Binance
              HIP-3 builders on Hyperliquid
```

Публичного server repository, подтверждающего внутренние class/module names,
нет. Поэтому слова `router` и `adapter` здесь описывают наблюдаемую роль, а не
утверждают конкретную серверную реализацию.

## 4. API surface

`data/api-surface-*.csv` содержит 77 точных пар method/path, извлечённых из
сгенерированного SDK в pinned MM-bot commit. Основные группы:

### Market and strategy reads

```text
GET /exchange/markets
GET /exchange/top-volume-symbols-quotes
GET /exchange/quotes
GET /exchange/estimate-slippage
GET /funding-strategies
GET /funding-strategies/funding-rate-history
GET /funding-strategies/spread-chart
GET /time
```

`GET /exchange/markets` в official examples назван authoritative list для
доступных exchange/market combinations. `quotes` и `estimate-slippage` требуют
Bearer в generated schema и не являются эквивалентом полностью публичного
market-data endpoint.

### Streaming

```text
GET  /exchange/updates-orderbook
POST /exchange/updates-token
GET  /exchange/updates
```

Generated client описывает SSE. Разделение на public-looking orderbook stream и
one-time-token updates указывает, что market stream и private account/order
stream нельзя смешивать в одном доверительном контуре.

### Trading and account mutation

```text
POST   /exchange/orders
DELETE /exchange/orders
POST   /exchange/batch-orders
DELETE /exchange/batch-orders
DELETE /exchange/all-orders
POST   /exchange/leverage
POST   /exchange/margin-mode
```

`DELETE /exchange/all-orders` описан как Lighter-only broad cancel. Он прямо
несовместим с инвариантом Multi-Exchange Engine «отменять только собственные
точно зарегистрированные ордера».

### Onboarding and wallet signatures

```text
POST /exchange/broker/prepare
POST /exchange/broker/execute
GET  /exchange/broker/approved

POST /user-exchange/{exchange}/register/prepare
POST /user-exchange/{exchange}/register/execute
GET  /user-exchange/{exchange}/register/status
```

Наблюдается prepare/sign/execute pattern: API строит exchange-specific payload,
пользователь подписывает его кошельком, затем signed data отправляется на
execute endpoint. Это сильная граница полномочий; исследование не выполняло ни
одного signing flow.

### Funds movement

```text
GET  /deposit
POST /transfer/prepare
POST /transfer/execute
POST /transfer/arbitrum
POST /withdraw/prepare
POST /withdraw/execute
POST /withdraw/extended/quote
POST /withdraw/extended/execute
```

Эти endpoints не имеют места в текущем shadow-only или public-data runtime.
Даже «prepare» может создавать подпись/transaction intent и должен считаться
funds-moving capability.

### MCP

```text
GET    /mcp
POST   /mcp
DELETE /mcp
```

Generated OpenAPI schema не помечает security одинаково во всех местах, но
официальный MCP README и Ultra setup требуют Bearer token. Документация
продукта имеет приоритет над отсутствующей annotation в generated client.

## 5. Venue abstraction и утечки venue-specific семантики

VOOI даёт общий `/exchange/*` namespace, но abstraction не полностью стирает
различия venue:

- exchange передаётся строкой и может расширяться без regeneration клиента;
- market identity включает `baseSymbol` и `id`;
- Kinetiq и trade.xyz представлены как HIP-3 builder deployments внутри
  Hyperliquid;
- их symbols имеют prefixes, например `km:` и `xyz:`;
- official MM bot сопоставляет «virtual venue» с
  `{exchange: "hyperliquid", prefix}`;
- для Aster order/leverage `asset` использует market `id` вроде `BTCUSDT`,
  тогда как другие paths используют `baseSymbol`;
- две логические legs могут разделять один физический margin account.

Следствие: ключ состояния только по `exchange` недостаточен. Минимальный ключ
должен включать venue/exchange, canonical market identity, symbol namespace и
роль leg. Нельзя предполагать, что одинаковый ticker означает одинаковый
contract.

## 6. Authentication и secret boundary

Наблюдаемая модель:

- VOOI API token создаётся в Ultra console;
- clients передают Bearer header;
- server-side broker identity/fee policy связывается с API key;
- отдельные exchange actions требуют wallet signature;
- Telegram/LLM/database credentials в examples передаются через environment.

Исследовательские инструменты этого каталога:

- не читают `.env`;
- не принимают Bearer token;
- не отправляют cookies;
- не подключают wallet;
- удаляют secret-like query values из observables;
- не выполняют скачанный код.

