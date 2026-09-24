# VOOI: индекс результатов статического реверс-инжиниринга

Дата снимка: **2026-08-10**. Анализ ограничен официальными публичными поверхностями, документацией и закреплёнными ревизиями репозиториев `vooi-app`; авторизация, подключение кошелька, торговые и денежные операции не выполнялись.

## Состав отчёта

1. [`architecture/01-client-surfaces-and-clients.md`](architecture/01-client-surfaces-and-clients.md) — Ultra, Pro, Light, Telegram Mini App, MCP и четыре официальных программных клиента.
2. [`architecture/02-api-and-auth.md`](architecture/02-api-and-auth.md) — восстановленная схема взаимодействия, API surface, SSE, onboarding/signing, transfer/withdraw и venue abstraction.
3. [`architecture/03-risks-and-integration.md`](architecture/03-risks-and-integration.md) — границы достоверности, риски и безопасный путь интеграции в Multi-Exchange Engine.

## Главный вывод

VOOI предоставляет единый API-first execution layer поверх нескольких perp-venue, но его сгенерированный SDK объединяет публичные market-data чтения, приватное состояние, торговлю, изменение параметров счёта, broker approval, transfers и withdrawals. Поэтому потенциальный адаптер Multi-Exchange Engine должен начинаться только с отдельного read-only shadow-контура и явного allowlist маршрутов. Все mutation/funds-moving пути в текущем исследовательском пакете помечены `forbidden` или `strictly_forbidden`.

Полная машинно-читаемая карта находится в `data/api-surface-*.csv`; инвентарь клиентов и закреплённые SHA — в `clients.lock.json`.
