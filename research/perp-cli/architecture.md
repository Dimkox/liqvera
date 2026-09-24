# perp-cli: индекс результатов статического реверс-инжиниринга

Дата снимка: **2026-08-10**. Поскольку authoritative implementation уже
опубликован как TypeScript source, анализ ориентирован не на декомпиляцию, а
на происхождение дистрибутивов, runtime wiring, signing boundary и separation
read-only/mutation/funds.

## Состав отчёта

1. [`architecture/01-packaging-and-surfaces.md`](architecture/01-packaging-and-surfaces.md) — source repo, npm, bin entry points, agent skill, mirrors/indexes.
2. [`architecture/02-runtime-and-adapters.md`](architecture/02-runtime-and-adapters.md) — CLI runtime, `ExchangeAdapter`, 4 DEX, public endpoints and outcome surface.
3. [`architecture/03-auth-mcp-and-risk.md`](architecture/03-auth-mcp-and-risk.md) — private-key/OWS/agent resolution, MCP role, trade/funds mutations and integration boundaries.

## Главный вывод

`perp-cli` — удобный unified execution layer, но его core adapter contract
объединяет public market reads, account state, order mutation и leverage/risk
operations. Поверх него CLI добавляет bridge/rebalance/funds и long-running
strategies. Для Multi-Exchange Engine безопасная reuse-граница — типы,
normalization и отдельный read-only market-data layer. Полный adapter/CLI
нельзя подключать к shadow-only runtime без явного policy split.
