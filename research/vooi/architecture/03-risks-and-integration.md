## 7. Достоверность и ограничения

### Высокая уверенность

- существование и текущие labels live web surfaces;
- shutdown VOOI Light;
- official Telegram bot identity;
- pinned commits и содержимое открытых repositories;
- method/path из generated SDK;
- Bearer MCP setup;
- SSE usage в official clients.

### Средняя уверенность

- generated SDK близок к live server surface;
- market list и response semantics не изменились после 2026-06-12;
- отсутствие native clients в публичной дистрибуции.

### Не подтверждено

- внутренняя серверная топология;
- точные production rate limits;
- идемпотентность order/transfer requests;
- гарантия event ordering и replay window SSE;
- compatibility generated SDK с текущей live API;
- наличие private/delisted APK;
- production implementation MCP tools.

На 2026-08-10 `https://perps-api.vooi.io/docs` перенаправлял на Cloudflare
Access login. Поэтому generated SDK из official repository является
наиболее полным публично проверяемым schema snapshot, но не должен считаться
вечным контрактом.

## 8. Риски для Multi-Exchange Engine

| Риск | Почему релевантен | Требуемая защита |
|---|---|---|
| Broad generated client | Один импорт открывает orders, transfer и withdraw | Не vendor SDK; написать узкий read-only transport |
| `cancel-all` | Может затронуть чужие/ручные ордера | Никогда не включать; exact ownership registry |
| Stale market mapping | `baseSymbol`, `id`, HIP-3 prefixes меняются | Snapshot/version/hash, fail closed |
| Shared margin account | Логические venues могут делить Hyperliquid account | Account identity отдельно от venue alias |
| SSE gap/reconnect | Потеря событий создаёт ложное состояние | Sequence/epoch evidence и authoritative REST reconciliation |
| Unknown POST outcome | HTTP timeout не доказывает отсутствие ордера | Unknown state freeze, lookup before retry |
| Token leakage | Один Bearer открывает широкую поверхность | Separate scoped token, redacted logs, no token in query/history |
| Signature confusion | prepare/execute payload venue-specific | Domain separation, exact payload hash, user confirmation |
| Transfer/withdraw exposure | Ошибка конфигурации становится потерей средств | Отдельный process/capability; отсутствует в current build |
| API edge dependency | VOOI становится общей точкой отказа | Raw evidence, health status, venue-direct fallback only after review |

## 9. Рекомендуемый путь интеграции

### Шаг R0 — только fixture research

1. Зафиксировать `GET /exchange/markets` response как неисполняемый fixture.
2. Сохранить raw bytes, headers, timestamp и SHA-256.
3. Описать schema drift tests.
4. Не добавлять credentials и network runtime.

### Шаг R1 — public read-only collector

После отдельного review:

1. разрешить только allowlisted HTTPS host;
2. разрешить только `GET /exchange/markets`,
   `/exchange/top-volume-symbols-quotes`, `/funding-strategies*` и `/time`,
   если live probing подтвердит отсутствие auth;
3. запретить redirects за пределы host;
4. запретить POST/PUT/PATCH/DELETE на transport level;
5. сохранять raw evidence до нормализации;
6. оставить engine в `shadow`.

### Шаг R2 — authenticated read-only boundary

Только отдельный процесс и отдельное решение:

- scoped read-only token, если VOOI поддерживает scope;
- account reads отделены от public collector;
- token никогда не попадает в main engine, logs или fixtures;
- SSE private stream не смешивается с public market stream;
- никаких signing, orders, leverage, transfers или withdrawals.

### Шаг R3 — mutations

Не входит в этот research package. Потребуются отдельные contracts, chaos
tests, ownership registry, unknown-state reconciliation, human-reviewed
release gate и явное снятие shadow-only ограничения.

## 10. Практический вывод

Для нового кода ориентир — **Ultra + Perps API**, а не Light. Pro полезен как
исторический UX/venue reference. Официальные examples дают достаточно
материала, чтобы построить независимый узкий read-only adapter, но целиком
подключать generated VOOI SDK опасно: его surface объединяет market data,
private account state, trading, broker approval, funds transfer и withdrawal.
