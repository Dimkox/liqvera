# VOOI: результаты статического реверс-инжиниринга

Дата снимка: **2026-08-10**
Метод: анализ официальных web surfaces, документации и открытых репозиториев
организации `vooi-app`; без авторизованных запросов и без исполнения торгового
кода.

## 1. Карта клиентских поверхностей

### VOOI Ultra

`https://ultra.vooi.io/` — текущий основной продукт. На момент проверки live
footer показывал `VOOI Ultra Beta v1.0.1`. Интерфейс содержит:

- одиночную позицию long/short;
- hedge placement;
- позиции, ордера, историю ордеров и сделок;
- отдельные arbitrage positions/history;
- API-token console и MCP onboarding;
- публичные market pages и Arbitrage Desk.

Публичный changelog фиксирует `Arbitrage Desk v1.0.0` от 2026-07-23, тогда как
live terminal уже показывал `v1.0.1`. Это обычный признак того, что footer и
changelog обновляются независимо.

### VOOI Pro

`https://pro.vooi.io/` продолжает работать и показывает `VOOI Pro v1.12.0`.
Терминал имеет market/limit/stop-limit form, chart/orderbook, позиции, ордера и
history. Официальные release notes датируют v1.12.0 2025-12-18. Продукт выглядит
как предыдущая профессиональная ветка, но не как основной новый API-first
surface.

### VOOI Light

`https://app.vooi.io/` показывает `VOOI Light v2.5.0`, но прямо сообщает, что
VOOI Light shut down. Остались migration/sign-in, staking, send и claim
surfaces. Для новой интеграции Light следует считать историческим источником,
а не активной торговой целью.

### Telegram Mini App

Официальная точка входа: `https://t.me/VooiAppBot/vooi`. Это Telegram WebApp,
а не APK. Release notes сообщают о запуске mini-app версии торгового терминала
2024-10-01. Публично проверяемого отдельного source repository для Mini App не
найдено.

### VOOI Perps MCP

Удалённый Streamable HTTP endpoint:

```text
https://perps-api.vooi.io/mcp
```

Официальный `vooi-app/mcp` содержит только конфигурационные примеры и MIT
license. Серверная реализация MCP в этом repository отсутствует. Onboarding
через Ultra требует Bearer token и предлагает конфиги для Claude, Codex,
Cursor и других MCP clients.

## 2. Официальные открытые программные клиенты

### `vooi-app/vooi-signals-bot-example`

Pinned commit:

```text
bb81ee0d5e48246f63b25f39a552622cc23af97d
```

Архитектура:

1. Telegram ingestion.
2. Разбор сообщений и LLM-assisted signal parsing.
3. Нормализация/resolve market.
4. VOOI REST calls через async `httpx.AsyncClient`.
5. SSE listener.
6. PostgreSQL/Alembic persistence.
7. Order lifecycle, reconciliation, TP/SL and safety watchers.
8. Audit/alerting.

Наблюдавшиеся свойства клиента:

- base URL по умолчанию `https://perps-api.vooi.io`;
- `Authorization: Bearer ...`;
- JSON request/response boundary;
- retry для 429 и выбранных 5xx;
- `Retry-After` плюс exponential backoff;
- correlation identifiers;
- редактирование Authorization в логах;
- отдельная конфигурация risk/circuit-breaker параметров.

Это наиболее показательный Python reference для transaction lifecycle, но он
умеет ставить реальные ордера и не должен импортироваться в shadow-only
runtime.

### `vooi-app/vooi-funding-bot-example`

Pinned commit:

```text
c3ceab29e80bb26fd6bde128280cb5da5428f3f1
```

Python-клиент для delta-neutral funding arbitrage. В repository присутствуют:

- большой MVP coordinator;
- SSE module;
- strategy, risk, position, reporting and execution boundaries;
- read-only `probe` package;
- Docker packaging and tests;
- dry-run configuration.

License — MIT с дополнительным trading disclaimer. Сам repository предупреждает,
что бот может размещать реальные ордера, и рекомендует сначала
`BOT_DRY_RUN=true`.

### `vooi-app/vooi-mm-bot-example`

Pinned commit:

```text
879d15c677e9840dfe4164e3e700bf54c72d5082
```

TypeScript/Node.js >=18 market-making client:

- generated SDK от `@hey-api/openapi-ts`;
- explicit Bearer Authorization header;
- market resolver;
- SSE reconnect/backoff;
- two-sided maker quotes на primary leg;
- hedge leg;
- margin preflight;
- shutdown cleanup;
- read-only `check` and `markets` commands.

Pinned revision отказался от Bun и перешёл на Node/`tsx`: commit message
сообщает, что VOOI API edge отклонял запросы Bun HTTP stack, тогда как Node
работал. Это наблюдение конкретной версии, а не универсальное утверждение о
всех будущих Bun releases.

### `vooi-app/mcp`

Pinned commit:

```text
9a5fc1aba5411a0c6e29822628b5ea834889caa7
```

README/config repository. Он документирует remote MCP URL и Bearer header, но
не содержит server code, tool handlers или exchange adapters.

