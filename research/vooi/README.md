# VOOI client inventory and static reverse engineering

Снимок: **2026-08-10**. Каталог содержит воспроизводимую инвентаризацию
официальных клиентов VOOI, зафиксированные SHA открытых репозиториев,
извлечённую поверхность Perps API и безопасные инструменты статического
анализа.

## Итог инвентаризации

| Клиент | Текущий статус на дату снимка | Зафиксированная версия/ревизия |
|---|---|---|
| VOOI Ultra | основной живой веб-терминал | footer: `Beta v1.0.1` |
| VOOI Pro | живой legacy/pro терминал | `v1.12.0` |
| VOOI Light | торговля остановлена, осталась миграция аккаунта | `v2.5.0` |
| Telegram Mini App | живой Telegram WebApp | `@VooiAppBot` |
| VOOI Perps MCP | удалённый Streamable HTTP MCP | `https://perps-api.vooi.io/mcp` |
| MCP config repo | открытый конфигурационный клиент | `9a5fc1a...` |
| Signals bot example | официальный Python-клиент | `bb81ee0...` |
| Funding bot example | официальный Python-клиент | `c3ceab2...` |
| MM bot example | официальный TypeScript/Node-клиент | `879d15c...` |

Официальный APK, приложение Google Play, приложение App Store или браузерное
расширение подтвердить не удалось. Это означает только отсутствие проверяемой
официальной публикации в исследованном контуре, а не доказательство
несуществования частной или снятой с публикации сборки.

## Что находится в каталоге

- `clients.lock.json` — машиночитаемый реестр клиентов, статусов, лицензий,
  commit SHA и первичных источников.
- `architecture.md` — результаты статического реверс-инжиниринга и выводы для
  архитектуры Multi-Exchange Engine.
- `data/api-surface-*.csv` — 77 наблюдавшихся пар `HTTP method + path` из
  сгенерированного официального TypeScript SDK.
- `SOURCES.md` — журнал первичных источников и ограничений достоверности.
- `scripts/fetch_sources.py` — скачивание точных публичных Git-ревизий и
  публичных same-origin web assets без авторизации и исполнения JavaScript.
- `scripts/extract_observables.py` — статическое извлечение URL, API paths и
  имён переменных окружения с редактированием secret-like параметров.
- `scripts/verify_inventory.py` — полностью офлайн-проверка реестра и CSV.

## Офлайн-проверка

Из корня репозитория:

```bash
python -B research/vooi/scripts/verify_inventory.py
python -m py_compile research/vooi/scripts/*.py
PYTHONPATH=research/vooi python -B -m unittest discover -s research/vooi/tests -v
```

Ожидаемый результат первой команды:

```json
{"api_rows": 77, "ok": true, "programmatic_clients": 4, "snapshot_at": "2026-08-10T08:02:00Z", "web_clients": 6}
```

## Получение открытых клиентов

Скрипт не запускает скачанный код и не отправляет токены:

```bash
# Все четыре официальных открытых клиента на точных SHA
python research/vooi/scripts/fetch_sources.py repos

# Только один клиент
python research/vooi/scripts/fetch_sources.py repos \
  --include vooi-mm-bot-example

# Публичный HTML и same-origin JS/CSS/manifest для web surfaces
python research/vooi/scripts/fetch_sources.py web \
  --include vooi-ultra,vooi-pro,vooi-light
```

Результаты пишутся в `research/vooi/artifacts/`, который исключён из Git.
Каждый объект получает SHA-256 и запись в `capture.json`.

После загрузки:

```bash
python research/vooi/scripts/extract_observables.py \
  research/vooi/artifacts/repositories \
  research/vooi/artifacts/web \
  -o research/vooi/observables.local.json
```

## Границы анализа

Выполнен статический анализ публичного кода, публичных страниц и официальной
документации. Не выполнялись:

- вход в аккаунт, подключение кошелька или создание API token;
- перехват чужого трафика, обход Cloudflare Access, DRM или иных ограничений;
- вызовы order, leverage, margin, transfer, deposit или withdraw endpoints;
- извлечение private keys, bearer tokens, cookies, wallet signatures или
  пользовательских данных;
- публикация закрытых web bundles в Git.

## Важная граница для Multi-Exchange Engine

Сгенерированный VOOI SDK содержит не только market-data, но и создание/отмену
ордеров, широкую отмену всех ордеров, изменение leverage/margin mode,
межбиржевые переводы и withdrawal. Поэтому его нельзя подключать к текущему
shadow-only runtime целиком.

Для будущего read-only адаптера допустим только отдельный вручную описанный
контракт после review. Любой private/account/trading/funds path в
`data/api-surface-*.csv` помечен как `forbidden` или `strictly_forbidden`.
