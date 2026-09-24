# perp-cli inventory and static reverse engineering

Снимок: **2026-08-10**. Каталог повторяет подход `research/vooi`: фиксирует
публичные дистрибутивы, точные ревизии, наблюдаемые поверхности, архитектурный
разбор и воспроизводимые инструменты получения исходных артефактов без запуска
скачанного кода.

## Ключевой вывод

В отличие от закрытого web/mobile клиента, `hypurrquant/perp-cli` уже опубликован
как исходный TypeScript-проект под MIT. Поэтому «обратный инжиниринг до
исходников» здесь не требует декомпиляции: authoritative source — публичный
репозиторий, зафиксированный на commit
`ed94cfd46259ff9186bf4f2489252a4f8f773e31`. Текущий `package.json` — `perp-cli@0.13.0`.

## Инвентаризация

| Поверхность | Статус | Зафиксировано |
|---|---|---|
| `hypurrquant/perp-cli` | официальный source repo | `0.13.0`, `ed94cfd462...` |
| npm `perp-cli` | официальный пакет | `0.13.0` |
| `perp` | основной CLI entry point | `dist/index.js` |
| `perp-mcp` | MCP/agent entry point | `dist/mcp-server.js` |
| `perp-guardrail` | safety/guardrail entry point | `dist/guardrail/perp-guardrail.js` |
| `skills/perp-cli` | bundled AI-agent skill | входит в npm package |
| `iflow-mcp/hypurrquant-perp-cli` | сторонний fork/mirror | `0.9.8`, `cae9101d18...` |
| npm `@iflow-mcp/hypurrquant-perp-cli` | сторонняя републикация | `0.9.8` |
| Glama / ClaudePluginHub / Unyly / mcp.so | сторонние каталоги | index/listing only |
| npm `@perp/cli` | **не относится** к этому проекту | historical Perpetual Protocol CLI `0.2.6` |

Официальные Android/iOS приложения, browser extension или отдельный native
desktop app подтвердить не удалось. Это qualified negative finding, а не
доказательство отсутствия любых частных сборок.

## Что находится в каталоге

- `clients.lock.json` — машиночитаемый реестр source/package/entry points,
  third-party mirrors и name collisions.
- `architecture.md` — индекс статического разбора.
- `architecture/01-packaging-and-surfaces.md` — packaging, npm, bin, skill, mirrors.
- `architecture/02-runtime-and-adapters.md` — CLI runtime, adapter abstraction,
  public API endpoints и exchange model.
- `architecture/03-auth-mcp-and-risk.md` — keys/signers, MCP boundary, mutation
  paths и ограничения интеграции.
- `data/surface-map.csv` — surface-level классификация read/mutate/funds risk.
- `data/exchange-adapters.csv` — 4 встроенных DEX adapter registrations.
- `SOURCES.md` — первичные и вторичные источники, версии и ограничения.
- `scripts/fetch_sources.py` — безопасное получение закреплённых публичных Git
  revisions без выполнения скачанного project code.
- `scripts/extract_observables.py` — URL/env/bin/command-like observables из
  скачанного source и локально добавленных npm tarballs.
- `scripts/verify_inventory.py` — офлайн-проверка inventory + CSV.
- `tests/test_verify_inventory.py` — минимальный regression contract для inventory.

`artifacts/` намеренно исключён из Git: туда попадают точные копии upstream
source и любые локально скачанные npm tarballs/capture metadata.

## Офлайн-проверка

Из корня `multi-exchange-engine`:

```bash
python -B research/perp-cli/scripts/verify_inventory.py
python -m py_compile research/perp-cli/scripts/*.py
PYTHONPATH=research/perp-cli python -B -m unittest discover -s research/perp-cli/tests -v
```

Ожидаемая структура результата первой команды:

```json
{"ok": true, "official_components": 6, "supported_exchanges": 4, "third_party_surfaces": 6, "snapshot_at": "2026-08-10T11:44:00Z"}
```

## Получение исходников

Fetcher ограничен публичными `github.com` HTTPS repositories, перечисленными в
`clients.lock.json`, и проверяет итоговый commit SHA. Он не импортирует и не
запускает загруженный JavaScript/TypeScript:

```bash
python research/perp-cli/scripts/fetch_sources.py repos
```

Точные npm package versions и registry metadata URLs закреплены в
`clients.lock.json`. Npm tarballs намеренно не vendor-ятся в Git; при локальном
снятии пакета его следует сохранять в `research/perp-cli/artifacts/npm/` и
фиксировать SHA-256 рядом с capture metadata.

После загрузки:

```bash
python research/perp-cli/scripts/extract_observables.py \
  research/perp-cli/artifacts \
  -o research/perp-cli/observables.local.json
```

## Что показал статический разбор

`perp-cli` строится вокруг общего `ExchangeAdapter`, который объединяет
market-data, account reads, trading mutations и risk operations. Встроенный
registry фиксирует Pacifica, Hyperliquid, Lighter и Aster. CLI дополнительно
содержит funds/bridge/rebalance, strategies/background jobs, wallet/agent
signing и Hyperliquid HIP-4 outcome markets.

`mcp-server.ts` в текущем source прямо описывает MCP как advisor/read-oriented
surface и не должен считаться прямым trade executor. При этом основной CLI
умеет размещать/редактировать/отменять ордера, менять leverage, перемещать
средства и запускать долгоживущие стратегии. Поэтому для Multi-Exchange Engine
нельзя импортировать весь CLI как «read-only adapter» — нужен отдельный
allowlist public/read path.

## Границы анализа

Не выполнялись:

- импорт, запуск или postinstall/prepublish скачанных npm packages;
- подключение реальных wallet/private keys;
- trade/withdraw/bridge/deposit/rebalance;
- перехват пользовательского или authenticated traffic;
- извлечение private keys, API keys, cookies, bearer tokens или wallet signatures;
- exploit testing на реальных биржах/средствах.

Для интеграции в Multi-Exchange Engine рекомендуемый первый этап — только
публичные market-data readers и типы/normalization. Trading, funds и signer
слои должны оставаться за отдельной boundary с явным consent и policy review.
