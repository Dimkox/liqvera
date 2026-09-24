# ТЗ для фабрики: MEE Evidence × Mezo

**Версия:** 1.0 · **Дата:** 24 сентября 2026 года  
**Продукт:** проверяемый рыночный отчёт → HTTP API → оплата тестовыми MUSD → выдача результата.  
**Заказчик / GitHub:** Dimkox. Регистрация в AKINDO выполнена по сообщению заказчика; повторная регистрация не нужна. Адрес электронной почты участника в публичные файлы не включать.  
**Назначение:** отдельная конкурсная версия существующего Multi-Exchange Engine. Это ТЗ на реализацию, а не утверждение о готовности сервиса.

[README](../../README.md) · [Индекс документации](../README.md) · [Handoff](../../handoff.md) · [Security](../../SECURITY.md) · [Исходная дорожная карта](../ROADMAP.md)

## 0. Задание и текущий статус

Создать самостоятельный публичный репозиторий `Dimkox/mee-mezo-evidence` из проверенного технического снимка `Dimkox/multi-exchange-engine`. Довести ровно один вертикальный сценарий до воспроизводимой демонстрации. Исходный репозиторий оставить приватным, его `main`, историю, незавершённые ветки и существующий Stage A не изменять при переносе.

На момент составления ТЗ проверен `main` исходника на коммите `4f6583f8590ea091d8a465de0c607e59bfe611a5` от 21 августа 2026 года. Дата проверки — 24 сентября 2026 года. Это зафиксированный baseline, а не утверждение, что все остальные ветки слиты.

**Публикация пока не выполнена.** Доступное подключение GitHub позволяет читать и записывать файлы/ветки, но не предоставляет операцию создания репозитория. Проверка через браузер завершилась требованием входа в GitHub. Публичный репозиторий и полный клон не созданы; full-history secret scan, запуск приложения, `make verify` и on-chain оплата в ходе подготовки ТЗ не выполнялись. Этот документ передаётся через отдельную документационную ветку приватного исходника. Этап F0 ниже обязателен для фабрики с авторизованным GitHub CLI/API.

Согласованный scope разрешает подготовку публичной копии и разработку testnet-сценария. Он не разрешает mainnet, пользовательский капитал, торговые операции, покупку облачных услуг, смену лицензии или раскрытие секретов.

## 1. Результат для пользователя и Mezo

Разработчик торгового сервиса или аналитик выбирает BUY/SELL и количество BTC. Сервис получает публичный снимок BTC-perpetual на Hyperliquid, проверяет входные данные и формирует неизменяемый отчёт. До оплаты показываются предмет отчёта, время снимка, статус проверок, ограничение доступной глубины и точная цена доступа. После подтверждённого перевода тестовых MUSD пользователь получает JSON, человекочитаемое представление и пакет для независимого пересчёта.

Пользователь покупает доступ к аналитическому артефакту, а не биткоин, сделку, торговый сигнал или доходность. MUSD применяется для платежа за API. MEZO не нужен для этого MVP.

Ценность демонстрации: от исходных байтов до воспроизводимого расчёта и подтверждённого платежа, без доступа к биржевому счёту. Testnet-платежи подтверждают техническую интеграцию, но не выручку, willingness to pay или PMF.

## 2. Проверенная основа и реальные недоделки

| Компонент baseline | Установленный факт | Требование к реализации |
|---|---|---|
| `packages/contracts` | Активный пакет `mee-contracts` | Сохранить точные числа, типы и ограничения |
| `packages/public-capture` | `source=public` запрашивает только Hyperliquid `l2Book` для BTC | Использовать один live-источник; не выдавать Lighter fixture за live |
| `packages/readonly-analyzer` | Есть reader sealed package, реконструкция, identity binding и `sweep_depth` | Переиспользовать, не переписывать вычислительное ядро на JavaScript |
| `vwap.py` | BUY потребляет asks, SELL — bids; расчёт через `Fraction`; нехватка глубины отклоняется | Сохранить математическую семантику и полный отказ при недостаточной глубине |
| Identity mapping | `REVIEWED_BTC` содержит `evidence_sha256 = "a" * 64`, ссылку `reviewed/v1` и статические параметры | Для live-отчёта заменить формальное происхождение реальными, сохранёнными evidence; не называть заглушку проверкой |
| Capture timing | Runtime передаёт `terminated_at_ms = started + 1` | Не использовать это значение как измеренную задержку; отдельно фиксировать реальное получение данных |
| `verdict.py` | Экономика читается из optional `economics.json`; VWAP не связан с verdict | Новый snapshot-report не должен менять старый verdict или подделывать экономику |
| Stage A | Семейство решений про качество/достаточность длительного наблюдения, а не разрешение торговли | Сохранить `INSUFFICIENT_EVIDENCE` там, где он правильный; не создавать `GO` |
| Платежи / API / UI | В прочитанном baseline выбранный end-to-end сценарий не подтверждён | Реализовать и предъявить доказательства отдельно |

Два разных понятия не смешивать: **снимка достаточно для арифметики по доступным уровням** и **наблюдений достаточно для вывода о стратегии**. Первое может быть истинно, второе — оставаться `INSUFFICIENT_EVIDENCE`.

Официальный Hyperliquid `l2Book` возвращает максимум 20 уровней на сторону [S3]. В UI писать «расчёт по доступной глубине снимка», а не «полный стакан биржи» или «гарантированное исполнение».

## 3. Границы MVP

Включить один инструмент — Hyperliquid BTC linear perpetual, одну сеть платежей — Mezo Testnet, BUY/SELL, объём в BTC, JSON API, браузерный сценарий оплаты, evidence bundle и offline verifier. Название инструмента должно явно содержать `perpetual`, а не создавать впечатление spot-покупки BTC.

Не включать Lighter live, cross-venue сравнение, арбитраж, сделки, биржевые API-ключи, funding/net P&L, займы, плечо, маршрутизацию обменов, мосты, MEZO trading, собственные смарт-контракты, custody, mainnet, Telegram/Kakao, регистрацию по email, CRM, платные AI-сервисы и подписки. Не переписывать сохранённый Go-код; это не активный runtime. Не создавать GitHub Actions и не включать унаследованные workflow автоматически.

Две среды обязательны: `fixture` для детерминированных проверок без сети и `live-public + mezo-testnet` для финальной демонстрации. Fixture-результаты помечаются `SIMULATED`; опубликованная платная demo-конфигурация не должна продавать fixture как live.

## 4. F0 — безопасная публичная копия

Это самостоятельный репозиторий, не GitHub fork приватного репозитория: visibility обычного fork связана с upstream [S4]. Не менять visibility исходника и не делать mirror push его истории.

Фабрика должна:

1. Проверить identity авторизованного GitHub-подключения и возможность создавать репозитории у Dimkox. Токены и пароли не выводить и не просить вставлять в чат. Использовать доступный ей авторизованный CLI/API.
2. Зафиксировать `git status --short`, отдельно `git diff --stat`, staged/untracked состояние и текущие refs локального исходника. Не сбрасывать и не включать пользовательские незавершённые изменения в публикацию. Создать отдельную рабочую директорию; старые worktree не переиспользовать вслепую.
3. Получить полную доступную историю исходника в приватную временную область и выполнить redacted secret scan всей истории и текущего дерева по `SECURITY.md`. Сканер работает локально; значения находок не попадают в LLM, чат или публичные отчёты. Найденные действующие секреты требуют ротации владельцем; их удаление из snapshot само по себе не закрывает инцидент.
4. Проверить также персональные контакты, приватные инфраструктурные адреса, дампы, логи, `.env`, sessions, приватные ключи, `.gitmodules`, LFS-объекты, симлинки, сторонние лицензии и сгенерированные архивы. Безопасность всей истории по одному README не подтверждать.
5. Экспортировать технический snapshot зафиксированного baseline в новую историю с собственным root commit. Перенести исходный код, тесты, необходимые документы, build-конфигурацию и применимые notices. Это должна быть копия технической основы, а не пустой scaffold. Не переносить `.git`, старые refs, issues, PR-обсуждения, workflow runs, secrets и приватные runtime-артефакты.
6. Подготовить `PROVENANCE.md`: upstream, baseline SHA, дата импорта, инвентарь файлов/хешей, исключения и причины, сохранённая атрибуция. Полный приватный scan report хранить вне публичного репозитория; публиковать только обезличенное резюме.
7. Сохранить существующие license/NOTICE. GitHub API не распознал лицензию исходника при проверке. Не добавлять MIT/Apache по умолчанию и не объявлять проект open source только на основании public visibility. Если конкурс требует определённую лицензию, зафиксировать отдельное решение владельца.
8. Создать `Dimkox/mee-mezo-evidence`; до первого push отключить выполнение GitHub Actions на destination, если workflow присутствуют в snapshot. Не переносить secrets/environments. Если имя занято, проверить владельца и provenance; не перезаписывать чужой или неожиданный репозиторий.
9. После сканирования опубликовать чистый snapshot, затем это ТЗ и документационные указатели. Разделить импорт и новые конкурсные изменения на понятные коммиты. В README не утверждать, что платежи уже реализованы.
10. Проверить metadata `private=false`, анонимный доступ и чистый clone без авторизации. Сопоставить файлы с инвентарём. Отдельно убедиться, что upstream остался private и его `main` не изменён этой операцией.

При блокере F0 оставить локальный пакет и точный статус `PUBLICATION_BLOCKED`. Не имитировать завершение созданием ссылки на несуществующий репозиторий. Независимую разработку можно продолжить в изолированной приватной рабочей копии; публичный release запрещён до закрытия F0.

## 5. Архитектура и изоляция

Сохранить Python как ядро аналитики. Добавить TypeScript/Express gateway для официального x402 EVM SDK, а не переписывать криптографию платежей. Зафиксировать это решение отдельным ADR в конкурсном репозитории: JavaScript здесь обслуживает платежную границу, не заменяет активный Python runtime.

Физические роли demo-стека:

| Роль | Назначение | Доступ |
|---|---|---|
| Gateway / UI | Публичный API, quote, x402, выдача оплаченного отчёта, reconciliation | Facilitator, testnet RPC, PostgreSQL; read-only доступ к готовым артефактам |
| Public capture service | Получение публичных HL данных и метаданных, сохранение raw package | Только разрешённые публичные HL endpoint; запись raw volume; без платежного окружения |
| Read-only report service | Верификация sealed input, identity binding, VWAP, запись нового report artifact | Raw volume read-only, output volume write; внутренний HTTP, без выхода в интернет |
| PostgreSQL | Quote/payment/entitlement, идемпотентность, durable recovery | Только gateway; отдельная БД и migrations |

Не добавлять Redis, Kafka, внешний object storage, Kubernetes или собственный facilitator. Сохранять evidence на выделенных persistent volumes с атомарной публикацией файлов. Раздельные внутренние сети и bind-порты должны исключать публичный доступ к capture, analyzer и БД. Роль analyzer не подключать к сети с внешним egress. Исходный `compose.stage-a.yml` и его fixture-режим оставить самостоятельными.

Рекомендуемые новые области: `apps/mezo-gateway/`, `packages/evidence-report/`, `services/evidence-capture/`, `services/evidence-report/`, `contracts/mezo-evidence/`, `deploy/mezo-evidence/`, `tests/mezo-evidence/`. Это целевые области, не заявление об их наличии. Фабрика уточняет минимальные файлы после чтения существующих interfaces; не создаёт пустые слои ради структуры.

Capture и analyzer не должны получать весь `process.env` gateway: в исходнике действуют проверки credential-like имён. Не ослаблять их ради `TOKEN`, `PASSWORD`, wallet или database переменных. Gateway хранит адрес получателя, но не его private key; пользователь подписывает в своём кошельке.

## 6. Данные инструмента и временные границы

Для каждого live-отчёта сохранять неизменённые байты ответа `l2Book`, тело публичного запроса, проверенный origin, реальное UTC-время начала/получения, exchange timestamp, HTTP status, SHA-256 payload и связанные metadata evidence. Не сохранять пользовательские HTTP-заголовки, cookies или секреты.

Параметры `product_kind`, base/quote/settlement asset, единица объёма и multiplier должны иметь проверяемое происхождение: официальный ответ метаданных и/или версионированный reviewed mapping с настоящим source reference и хешем. Не считать строку `APPROVED` доказательством и не наследовать фиктивный хеш. Автоматическое чтение документов не выдавать за человеческий review. Если API не содержит нужного свойства, оно закрывается отдельно reviewed evidence либо отчёт остаётся `IDENTITY_UNVERIFIED`.

Текущий `sweep_depth` допускает только bound identity, `displayed_size_unit=coin` и multiplier=1. Эти проверки сохраняются. Не пересчитывать размеры через произвольный multiplier. Quantity должен быть положительной десятичной строкой, представимой в существующем exact type; неподдерживаемую точность отклонять, не округлять тайно. Для гипотетического snapshot sweep не объявлять соблюдение всех реальных order constraints биржи.

Стартовая политика продукта, а не свойства протоколов: максимум 5 000 ms между source timestamp и receive timestamp; отклонение source timestamp в будущем более 1 000 ms — `CLOCK_SKEW`; metadata evidence не старше 24 часов и в своём интервале валидности. Все пределы версионируются и тестируются на границах. Quote живёт 120 секунд после готовности отчёта. Свежесть проверяется при его создании; по мере оплаты отчёт становится историческим снимком, что явно показывается пользователю.

Проверять корректный JSON, конечные и положительные цены, неотрицательные размеры, порядок уровней, идентичность инструмента, отсутствие crossed/locked book и достаточную глубину. Дубликаты/некорректный порядок не исправлять незаметно. Любая нормализация допустима только по существующему проверенному контракту и с доказательствами. User-supplied URLs, пути файлов, market mappings или HTTP payload для upstream не принимать.

## 7. Состав и точность отчёта

Новая схема: `mee-evidence-report/v1`. Закрытый набор `snapshot_status`: `VALID_FOR_SNAPSHOT_CALCULATION`, `REJECTED`, `SIMULATED`. Только первый допускает live chargeable quote; это не оценка прибыльности. Не переименовывать `mee-stage-a-decision/v1` и не изменять его смысл. Новый отчёт может содержать исходный Stage A verdict как независимое поле с разъяснением, почему длительных наблюдений недостаточно.

Обязательные поля:

| Группа | Содержание |
|---|---|
| Identity | `report_id`, schema version, venue, instrument id, product kind, base/quote/settlement asset, mapping version и evidence references |
| Запрос | side, `quantity_base` как decimal string, единица BTC |
| Время / источник | created/observed/source timestamps, build-time age, `source_mode`, payload и package hashes, реально доступные уровни с каждой стороны |
| Расчёт | requested/filled quantity, notional, VWAP, worst consumed price, consumed levels, price impact относительно лучшего уровня соответствующей стороны |
| Качество | `snapshot_status`, стабильные reason codes, выполненные проверки и ограничения, отдельный Stage A verdict |
| Воспроизводимость | engine commit, версии пакетов, digest lockfiles, calculation/policy version, перечень входных файлов и их хешей |
| Границы вывода | `execution_authority=NONE`, fees/funding/net P&L не рассчитаны, отсутствие обещания исполнения |

Внутреннее имя `ExecutableFill` не превращать в утверждение о реальном fill. В публичном представлении использовать «гипотетический sweep по снимку». Сетевую комиссию за оплату отчёта не смешивать с комиссиями гипотетической биржевой сделки.

BUY: пройти asks по возрастанию; SELL: bids по убыванию. Notional — сумма price × consumed quantity; VWAP — notional / requested quantity. При недостаточной глубине отклонить полный запрос, не продать частичный результат как полный. BUY impact = (VWAP / best ask − 1) × 10 000 bps; SELL impact = (1 − VWAP / best bid) × 10 000 bps.

Цена, количество и денежные величины не проходят через JavaScript `Number` или Python `float`. Для неделимых дробей хранить точные numerator/denominator строками; представление decimal округлять `ROUND_HALF_EVEN` до явно заданной display precision. Канонический расчёт сверяется по дробям, а не по округлённой строке. Payment amount хранить integer atomic units независимо от биржевых exact types.

Контрольный пример: asks 100000 × 0.10 BTC и 100100 × 0.10 BTC; BUY 0.15 BTC. Notional = 15005; VWAP = 300100/3; worst price = 100100; consumed levels = 2; impact = 10/3 bps. BUY 0.21 BTC должен дать `DEPTH_INSUFFICIENT`, без оплаты. Это синтетический test vector, не рыночная котировка.

Минимальные reason codes: `INVALID_INPUT`, `INVALID_DATASET`, `SOURCE_UNAVAILABLE`, `STALE_SOURCE`, `CLOCK_SKEW`, `IDENTITY_UNVERIFIED`, `IDENTITY_MISMATCH`, `CROSSED_BOOK`, `DEPTH_INSUFFICIENT`, `UNSUPPORTED_INSTRUMENT`, `SIMULATED_SOURCE`. Не маскировать конкретную причину общим «ошибка сервера».

## 8. Evidence bundle и offline verification

Bundle содержит исходный sealed input package, `report.json`, отдельный manifest с SHA-256 файлов, source/mapping evidence и сведения о версии алгоритма. Существующий sealed package не изменять добавлением отчёта внутрь: хранить его самостоятельным вложенным артефактом, чтобы не ломать member-set validation.

`report_sha256` считать по окончательным каноническим UTF-8 bytes `report.json`; собственный digest не включать в хешируемое тело. Сериализацию версионировать, закрепить сортировку ключей, формат строк и финальный newline. Receipt ссылается на report digest; отдельные строки состояния UI не должны менять report bytes.

CLI verifier работает без кошелька, интернета и БД. Он проверяет schema, допустимые имена/размеры файлов, manifest, raw payload hashes, reconstruction/identity и пересчитывает значения точной арифметикой. Успешная проверка возвращает exit code 0; повреждение любого значимого поля — ненулевой code и reason. ZIP path traversal, symlinks и decompression bombs отклоняются до распаковки.

Честная граница: хеши и пересчёт подтверждают целостность относительно полученного manifest и воспроизводимость. Они сами по себе не доказывают, что биржа подписала данные, что оператор не сфабриковал исходный снимок или что сделку можно исполнить сейчас. Blockchain receipt подтверждает платёж, а не достоверность рыночного прогноза. On-chain anchoring отчёта и собственные подписи данных не входят в MVP.

## 9. Контракт внешнего API

До кода зафиксировать OpenAPI и JSON Schema, версии ошибок и test vectors. Свободных полей не принимать. Безопасный `request_id` присутствует в ответах и логах, без wallet secrets и payment signature.

| Метод / путь | Поведение |
|---|---|
| `GET /healthz` | Liveness без приватных данных; никаких платежей |
| `GET /readyz` | Готовность storage, конфигурации и интеграции; failure закрывает новые платежи, не выдаёт фиктивный PASS |
| `GET /v1/capabilities` | Инструмент, testnet, цена, режим данных и ограничения; без секретов |
| `POST /v1/report-quotes` | Валидирует запрос, готовит и сохраняет отчёт; только затем выдаёт quote |
| `GET /v1/report-quotes/{quote_id}` | Авторизованное получение статуса, preview, expiry и recovery state; не раскрывает платный body |
| `GET /v1/reports/{report_id}` | 402 с x402 requirements до оплаты; 200 с report и receipt после подтверждения |
| `GET /v1/reports/{report_id}/evidence` | Bundle в рамках уже оплаченного entitlement; не второй платёж |

Create request: instrument id, BUY/SELL, `quantity_base`, expected payer EVM address. Source/price/payTo выбирает сервер. `Idempotency-Key` обязателен при создании quote. Один ключ плюс одинаковое нормализованное тело и тот же access scope возвращают тот же объект; изменённое тело — 409. Конкурентный повтор ещё выполняющегося build может получить 202 с адресом статуса.

Доступ к quote/report защищается независимой capability: клиент до первого запроса генерирует случайный секрет не менее 256 бит и передаёт его как Bearer. Браузер хранит его в sessionStorage для восстановления после reload; API-клиент хранит у себя. Сервер сохраняет только hash и связывает объекты с ним. Это не wallet private key и не торговый API key. Секрет, quote id и idempotency key имеют разные назначения. ID, адрес кошелька, публичный tx hash и report hash не являются авторизацией.

Payment payer должен совпадать с ожидаемым адресом quote; подлинность payer устанавливается валидной платежной подписью, а не полем запроса. Другой access scope не получает quote/status/report даже при знании ID или tx hash. Capability не передавать в URL, access logs и analytics. Для unauthenticated/чужого ресурса возвращать согласованную 401/404 политику без утечки существования объекта.

Preview содержит только instrument/side/quantity, время снимка, уровень качества, ограничения, цену и expiry. Полный расчёт, raw bundle и internal paths до оплаты недоступны. Для reject показывать бесплатную причину и не создавать chargeable quote.

Коды: 201 — готовый quote; 200 — ресурс; 202 — build или неопределённый settlement ещё проверяется; 402 — требуется платежная авторизация; 409 — конфликт/неподходящее состояние; 410 — истёкший quote или документированное окончание retention; 422 — неправильные параметры или непригодные данные; 429 — лимит; 503 — недоступный upstream/storage/payment service. В 402 не добавлять второй несовместимый формат оплаты: следовать pinned x402 SDK.

## 10. Mezo/x402: конфигурация и предварительная проверка

По официальной документации Mezo на дату проверки [S1, S2]:

| Параметр | Значение для MVP |
|---|---|
| Network | Mezo Testnet, chain ID `31611`, CAIP-2 `eip155:31611` |
| RPC | `https://rpc.test.mezo.org` |
| Explorer | `https://explorer.test.mezo.org` |
| MUSD | `0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503` |
| Decimals | 18 |
| Facilitator | `https://facilitator.vativ.io` |
| Protocol | x402 v2, EVM `exact`; официальная поддержка MUSD/Permit2/EIP-2612 |
| Headers | `PAYMENT-REQUIRED`, `PAYMENT-SIGNATURE`, `PAYMENT-RESPONSE` |
| Demo price | **0.01 test MUSD = 10000000000000000 atomic units**; продуктовая настройка, не рыночная оценка |

Официальный quickstart показывает комплект `@x402/*` 2.16.0 [S2]. Это исходная reference-конфигурация, не безусловный приказ использовать старую версию. В F1 проверить существование/совместимость пакетов, доступность сети и facilitator; сохранить точные проверенные версии и lockfile. Не устанавливать `latest` в runtime, не смешивать major versions и не копировать USDC six-decimal форматирование.

Перед открытием платёжного маршрута проверить фактический `eth_chainId`, bytecode token, `decimals`, поддержку сети/схемы через facilitator capabilities и соответствие registry SDK ожидаемому MUSD. Документация не заменяет эту runtime-проверку. Не подменять отсутствующую поддержку testnet фиктивным success, самодельным ERC-20 или mainnet.

`PAY_TO` обязателен, валидируется, принадлежит выделенному merchant test wallet. Не использовать адрес получателя из примера Mezo, zero address или неявный default. Buyer и merchant в demo разные. Merchant private key не нужен gateway. При отсутствии заданного адреса payment readiness=false; разработки аналитики это не блокирует.

Для тестовых MUSD документация описывает получение test BTC и выпуск MUSD через testnet borrow [S2]. Не обещать прямой MUSD faucet. Получение средств выполняет оператор в отдельном тестовом кошельке; отсутствие баланса — именованный blocker, не повод трогать реальные средства. Не отправлять платежи чужому demo-сервису в качестве скрытого acceptance test.

Mainnet chain `31612` и любая другая сеть должны отклоняться проверками конфигурации и запросов. Переход на mainnet нельзя реализовать одним переключателем среды: он вне этого release.

## 11. Платёжный протокол и recovery

Основной поток:

1. Gateway создаёт durable запись запроса и инициирует capture/report. Quote появляется только после сохранения и контрольного чтения report и bundle. Ошибка данных или storage не должна приводить к подписи платежа.
2. Quote неизменно связывает report id/digest, buyer, access scope, chain, asset, atomic amount, payTo, version и expiry. Каждая подписываемая цена должна совпадать с показанной.
3. Неоплаченный GET отчёта с корректной capability возвращает 402 и стандартные требования. UI показывает адрес получателя, 0.01 test MUSD, сеть и время исходного снимка. Пользователь явно подтверждает платеж в своём кошельке.
4. Клиент повторяет GET с `PAYMENT-SIGNATURE`. Сервер проверяет signature, payer, chain, token, amount, receiver, deadlines, nonce и соответствие закреплённым условиям. Одно `verify=true` ещё не означает оплату.
5. До `/settle` сохранить уникальный payment attempt и association authorization→quote. Выходящий network call выполняется после durable commit. Одна quote одновременно имеет не более одной активной settlement-попытки.
6. После положительного settlement проверить chain transaction receipt, success status, canonical block и MUSD Transfer конкретного token от buyer к merchant на нужную сумму. Связать event с конкретной authorization, а не просто найти похожий перевод. Подтверждённое правило финальности зафиксировать в F1; простого принятия транзакции mempool недостаточно.
7. В одной DB transaction сохранить settled payment, immutable receipt и entitlement к конкретному report digest. Только после этого вернуть платный body и `PAYMENT-RESPONSE`. Не стримить body до settlement.
8. Повторный запрос владельца entitlement получает тот же артефакт и тот же receipt без новой подписи и `/settle`. Разрыв соединения после списания, перезапуск и несколько вкладок не должны требовать второй оплаты.

Состояния quote/report: `PREPARING → READY → PAYMENT_PENDING → PAID`; отдельные ветви `BUILD_FAILED`, `REJECTED`, `EXPIRED` и `PAYMENT_UNCERTAIN`. Состояния payment attempt: `RECEIVED → VERIFIED → SUBMITTING → CONFIRMED`, либо `REJECTED` / `UNKNOWN`. Доставку фиксировать отдельно: server response не доказывает, что клиент его получил. State transitions атомарны и проверяются по допустимому графу.

При timeout `/settle` или падении после broadcast ставить `UNKNOWN` / `PAYMENT_UNCERTAIN`, а не «не оплачено». Не создавать новую authorization/nonce и не делать слепой повтор списания. Восстановление сначала проверяет сохранённый tx hash и состояние authorization на цепи. Если tx hash не получен, использовать только реально поддержанные способы поиска и correlation по nonce/transaction evidence; не выдумывать facilitator `/status` endpoint. Совпадения payer/amount/time недостаточно при нескольких одинаковых платежах. Неоднозначный случай остаётся заблокированным с операторским recovery, без второго списания и без утверждения о settlement.

Идемпотентность обеспечивается БД, блокировкой состояния и идентичностью on-chain authorization. Один hash сырого payload недостаточен: иное кодирование/подпись той же authorization не должны обходить deduplication. Зафиксировать canonical identity, nonce semantics и replay-domain для фактически выбранного SDK. Не предполагать, что x402 автоматически криптографически подписывает report id или URL: связь с ресурсом проверяется по действительной схеме и серверному ledger; одна authorization не обслуживает два quote.

Quote expiry запрещает начинать новую оплату, но не отменяет уже начатую/подтверждённую. Если broadcast произошёл до expiry и платеж подтвердился позже, выдать первоначальный отчёт. Уже оплаченный исторический отчёт нельзя заблокировать как stale или заново пересчитать на свежем рынке. После входа в `SUBMITTING` очистка артефактов запрещена до reconciliation.

Без receipt finality, с wrong asset/amount/payer/receiver/network, reverted transaction, reused authorization или failed verification body не выдаётся. Реорганизация/несогласованность RPC переводит попытку в проверку, не инициирует новый перевод. Система не обещает распределённую «магическую exactly once»: доказать требуется at-most-once charge на подтверждённую authorization, durable entitlement и безопасное поведение при неизвестном исходе.

## 12. Persistence и retention

PostgreSQL — source of truth для платежного состояния; versioned migrations обязательны. Gateway — единственный writer ledger. Не подключать capture/analyzer к существующей производственной БД фабрики.

Минимальные сущности: access scopes, report requests, reports/artifact manifests, quotes, payment attempts, entitlements и append-only audit events. Нужны foreign keys и уникальности: `(access_scope, idempotency_key)`; canonical authorization identity; `(chain_id, tx_hash, log_index)`; entitlement на quote/report. Один tx может содержать несколько логов — tx hash без log index не достаточен. Сохранять chain/asset/amount/payTo/payer, report digest, состояние, times, error/recovery code и version, а не произвольные JSON вместо всех ограничений.

Каждый capture получает собственный новый каталог по внутреннему run/report id. Текущий package writer очищает переданный root: запрещено использовать один общий каталог для конкурентных отчётов или направлять writer в пользовательский путь. Не вызывать `make prod` из API: baseline-команда очищает свой Stage A volume.

Публикация артефакта: temporary directory → запись и flush → проверка hash → atomic rename → статус READY. Обнаружение незавершённой записи после restart не должно превращать её в готовый отчёт. Immutable report никогда не переписывается под тем же id. Перед settlement контрольное чтение должно подтвердить наличие exact bytes.

Стартовые пределы: платные отчёты и bundle доступны минимум 7 суток с подтверждения платежа; unpaid artifacts удаляются не раньше 15 минут после expiry и только при отсутствии pending/unknown payment. UNKNOWN сохраняется до решения. Ledger, access-scope binding и dedup records сохраняются не менее 30 суток и никогда не меньше срока действительности authorization. Удаление ledger не должно открывать replay. Реальные сроки показываются до оплаты.

Потеря подтверждённого артефакта закрывает новые продажи и запускает восстановление из сохранённого sealed input; повторная генерация допустима только при совпадении прежнего report digest. Не требовать доплату за восстановление. Автоматические refunds и merchant signing key в MVP не добавлять; невосстановимый случай фиксировать как инцидент и тестировать его обнаружение.

## 13. UI и demo

Одна страница, английский интерфейс для жюри; русская операторская документация допустима. В шапке постоянно видны `TESTNET ONLY`, `READ-ONLY ANALYTICS` и режим данных. Никаких buy/sell execution buttons: BUY/SELL относятся к расчёту, рядом это объясняется.

Порядок: выбрать side/quantity → подключить EVM wallet и проверить сеть → получить quote/preview → подтвердить цену → подписать платёж → увидеть report/receipt → скачать bundle → повторно открыть без доплаты. Переключение кошелька после выдачи quote требует сверки payer, а не оплаты старых условий другим аккаунтом.

Показывать время и возраст снимка, sampled depth, VWAP/worst price, количество потреблённых уровней, ограничения расчёта и ссылку на testnet transaction. Не превращать `READY` в зелёный «можно торговать». На stale/identity/depth rejection — бесплатная понятная причина. На settlement timeout — «проверяем уже отправленную оплату», не кнопка «оплатить ещё раз».

Нет регистрации, email-форм, seed/private-key input, пользовательских API-ключей, незаметных автосписаний и unlimited approvals. Если используемая SDK-схема фактически требует approval, это отдельная явно отображаемая ограниченная testnet операция после ADR review, а не скрытая подпись.

## 14. Нефункциональные требования

Для MVP достаточно одного gateway replica и небольшого worker pool; корректность платежей не должна зависеть от этой конфигурации. Нужны transaction-safe concurrent tests минимум на 20 параллельных повторах одного запроса.

Стартовые продуктовые лимиты: JSON body ≤16 KiB, decoded payment payload ≤16 KiB, bundle ≤10 MiB, максимум 4 параллельные сборки, 5 новых quote в минуту на access scope с дополнительным IP/global budget. Публичные ID/статусы и paid reads имеют отдельный rate limit. Пределы конфигурируются, документируются и не обходятся новым клиентским заголовком.

Общий build deadline — 15 секунд; не больше двух upstream попыток в этом бюджете. Settlement timeout ограничивает ожидание HTTP, не определяет неуспех платежа. Reconciliation имеет bounded attempts/backoff и явный `MANUAL_REVIEW`, не бесконечный цикл. Готовый paid artifact при исправном локальном storage должен отдаваться с p95 <1 секунды на документированном demo-host; upstream/block latency измерять отдельно, не включать в обещание.

TLS, точный CORS allowlist, CSP, ограничения egress, non-root containers, read-only mounts и минимальные зависимости обязательны. Bundle не хранить под публичным static path. `Cache-Control: private, no-store` для quote/payment/report responses; CDN caching платных тел запрещён. Исключить payment/capability headers из reverse-proxy, APM и application logs. No arbitrary redirects для RPC/facilitator/upstream.

Метрики без high-cardinality wallet labels: build duration/rejections, readiness, 402 responses, verified/settled/unknown, reconciliation duration, duplicate attempts blocked, delivery failures и artifact integrity failures. Логировать request/quote/payment correlation IDs и стабильные error codes. В demo/release logs не включать подписи, bearer tokens, DB credentials и электронную почту участника.

## 15. Тесты и критерии приёмки

Исходные `make verify` и релевантные conformance/installed tests должны проходить до и после изменения. Существующий `INSUFFICIENT_EVIDENCE` не исправлять под ожидаемый коммерческий ответ. Go tests не являются доказательством Stage A.

| ID | Проверка | Обязательный результат |
|---|---|---|
| A01 | Чистый baseline и изменённое дерево | Отдельные сохранённые результаты проверок; старые падения не скрыты |
| A02 | BUY test vector из §7 | Exact notional/VWAP/worst price/levels совпадают |
| A03 | SELL, один уровень, ровно вся глубина, дробь с бесконечным decimal | Верные стороны и точные рациональные значения |
| A04 | Недостаточная глубина, zero/negative, float, NaN, unsupported precision | Отказ; нет quote для оплаты и нет settlement |
| A05 | Stale/future timestamp, crossed book, wrong instrument, metadata gap | Конкретный reason code; нет продажи неправильного отчёта |
| A06 | Mapping с фиктивным source hash или неверной единицей/multiplier | `IDENTITY_UNVERIFIED`/отказ; не формальный PASS |
| A07 | Live без доступа к HL | `SOURCE_UNAVAILABLE`; никакого fallback на скрытый fixture |
| A08 | Повреждение raw/mapping/report/manifest и ZIP traversal/bomb | Offline verifier отказывает |
| A09 | Пересчёт bundle на чистой машине без сети | Тот же exact результат и digest |
| A10 | Неоплаченный authorized GET | 402, верные x402 headers; платного body нет |
| A11 | Wrong signature/network/token/amount/receiver/payer, expired/reused authorization | Ни entitlement, ни платного body |
| A12 | 18 decimals / 0.01 test MUSD | Ровно 10000000000000000 units во всех слоях |
| A13 | Happy path testnet, buyer ≠ merchant | Один подтверждённый MUSD Transfer и один entitlement |
| A14 | Повтор GET и скачивание bundle после оплаты | Тот же report/receipt, ноль дополнительных settlement |
| A15 | 20 конкурентных retries quote/payment | Один logical quote и не более одного списания |
| A16 | Тот же idempotency key с другим телом | 409 без нового действия |
| A17 | Crash до submit, после broadcast, после chain success до DB commit | Корректное recovery; неизвестный исход не считается отказом |
| A18 | Потеря ответа клиенту после settlement | Восстановление доступа без новой подписи/платежа |
| A19 | Timeout без tx hash и несколько похожих Transfer | Нет ложного CONFIRMED и нет повторного списания |
| A20 | Expiry во время settlement | Подтверждённый платёж открывает прежний отчёт |
| A21 | Чужая capability, угаданный ID или публичный tx hash | Доступ не получен |
| A22 | Report file исчез до оплаты / повреждён после оплаты | До — списания нет; после — recovery/incident, не доплата |
| A23 | Подмена RPC chain ID, registry token, mainnet config | Payment readiness=false / отказ |
| A24 | Facilitator verify success, settle failure/unknown | Paid body не выдан до подтверждения |
| A25 | Raw signatures/keys/capabilities в логах и browser bundle | Не обнаружены; redaction проверена тестовыми canary values |
| A26 | Network/container boundaries | Analyzer не выходит наружу; capture не видит payment/DB env |
| A27 | Старый Stage A verdict и fixture suite | Не изменены ради новой упаковки; `GO` невозможен |
| A28 | Чистая установка по README | Сборка и offline demo воспроизводятся по lockfiles |
| A29 | Public clone и provenance | Анонимно читается; snapshot сопоставлен; upstream private сохранён |
| A30 | Wallet cancel, wallet switch, reload, wrong chain | Нет неявного платежа; UI показывает корректный recovery |

Разделить уровни: unit/contract/fault tests с mocks; integration с настоящим PostgreSQL; offline end-to-end; отдельно live-public/testnet end-to-end. Mocked settlement не заменяет A13. Внешняя недоступность даёт `BLOCKED_EXTERNAL`, а не PASS или бесшумный skip.

Для A13 оператор использует выделенный тестовый buyer, явно подтверждает ограниченную сумму и сохраняет tx hash/block/log index. В рамках самого написания ТЗ никакие средства не переводятся.

## 16. Декомпозиция для фабрики

| Этап | Работа | Зависимости | Exit artifact |
|---|---|---|---|
| F0 | Безопасный snapshot, scan и публичный destination | Авторизованный GitHub create/push | Public URL, anonymous clone proof, provenance, redacted scan summary |
| F1 | Проверить baseline, live metadata, SDK/Mezo/receiver/finality; принять narrow ADR | Чтение исходника; публикация может ещё быть заблокирована | Baseline results, ADR, compatibility lock, named blockers |
| F2 | OpenAPI/JSON schemas, quote/payment state graph, exact test vectors | F1 | Machine-readable contracts, invariants, failing tests |
| F3 | Настоящий provenance и capture timing; report builder и verifier | F2 | Воспроизводимый offline bundle и live-source validation |
| F4 | Gateway, PostgreSQL migrations, quote/capability, protected delivery без real settlement | F2–F3 | API tests; 402 и корректный отказ без оплаты |
| F5 | x402 adapter, durable settlement, entitlement/reconciliation | F1, F4 | Replay/concurrency/crash tests, затем controlled testnet payment |
| F6 | Минимальный UI, isolated Compose, rate limits, runbook | F4–F5 | Browser flow и чистая установка |
| F7 | Независимый review, fault suite, live-public/testnet demo | F0–F6 | Acceptance report, release candidate, конкурсные материалы |

Распараллеливать независимые исследование, тест-анализ, документацию и review. Единственный write-agent владеет application-code изменениями. Не запускать F5 до устойчивых quote/report contracts; не строить UI поверх плавающего JSON. Не объявлять F7 закрытым, если хотя бы F0 или testnet payment blocked.

Каждый существенный этап оставляет coherent commit, обновлённый `handoff.md` и factual evidence с exact commit SHA. Пользовательские изменения не терять. Никаких force push, массового удаления, поддельных CI checks, обхода branch protection и автоматического merge в исходный `main`.

## 17. Конкурсная упаковка и даты

Направление: **Access and distribution**, развитие существующего продукта. MUSD используется непосредственно в рабочем API; декорация логотипом не считается интеграцией. В submission разделить imported baseline и новые commits, приложить архитектуру, публичный код, инструкции, видео и подтверждённый testnet transfer. Не представлять старый код как написанный во время конкурса.

По предоставленному организаторскому письму: Wave 1 — 16–26 октября, Wave 2 — 2–15 ноября, демонстрации/объявление — 23 ноября. Планирование ведётся для 2026 года, но точные submission cutoff и timezone фабрика/владелец сверяют в AKINDO. Страницы события не удалось независимо прочитать при составлении этого ТЗ; даты не выдаются за повторно подтверждённые правила.

Внутренние контрольные даты: candidate Wave 1 — 25 октября 2026 года, candidate Wave 2 — 14 ноября 2026 года. Это предлагаемые проектные буферы, не дедлайны, назначенные организатором. Не откладывать технический baseline до открытия Wave 1; допустимость конкурсных изменений, сделанных ранее, отдельно проверить по правилам и раскрыть честно.

Wave 1: один рабочий сценарий, offline verifier, реальная testnet оплата и базовая отказоустойчивость. Wave 2: закрыть обратную связь, усилить recovery/tests/UX. Расширение числа бирж и mainnet не становятся обязательными даже во второй волне.

## 18. Definition of Done и передача

Работа завершена только когда одновременно существуют: публичный анонимно клонируемый технический репозиторий с provenance; несломанный исходный Stage A; подтверждённые metadata/timing; воспроизводимый отчёт; unpaid 402; successful test MUSD payment; повторное получение без повторной оплаты; verifier на чистой машине; fault/security tests; инструкции запуска и восстановления; testnet-only UI; сохранённые доказательства приёмки.

Итоговые материалы в destination: README с реальным статусом, это ТЗ и его индекс, узкий ADR, OpenAPI/JSON schemas, исходники/тесты/migrations, lockfiles, isolated Compose, безопасные `.env.example` без значений секретов, `PROVENANCE.md`, testnet runbook, recovery runbook, acceptance report, короткий demo script и конкурсное описание на английском. Docker/lockfiles не должны требовать приватного GitHub-доступа для публичной сборки.

В acceptance report перечислить команду, окружение, время, code SHA, exit code, результаты и пропуски каждой группы; для payment — testnet transaction evidence без ключей/подписей. Ссылки на видео/hosting добавляются только после их реального создания. Платное облако, production deploy и mainnet не покупать/не включать автоматически.

Технический kill criterion: недостоверные metadata, невозможность безопасно связать оплату с entitlement, повторные списания, утечка paid artifact или сломанный Stage A блокируют release. Небольшой визуальный дефект не оправдывает ослабление этих критериев.

## 19. Команда-поручение фабрике

Прочитай этот файл, `AGENTS.md`, `README.md`, `handoff.md`, `SECURITY.md`, `docs/ROADMAP.md` и существующие точные контракты. Применяй фактический маршрут фабрики из `.grok-stack/runtime/active-route.json`, если он создан в рабочем окружении; отсутствие маршрута не заменяй выдуманными receipts. Создай change package `engineering/changes/2026-09-24-mezo-evidence/` с задачами F0–F7, source baseline, ADR, acceptance matrix и blockers. Начни с безопасной публичной копии и baseline verification. Сохрани существующие изменения. Реализуй только утверждённый testnet сценарий. Не спрашивай повторно выбор продукта или регистрацию. При отсутствии полномочий/merchant address/test MUSD зафиксируй конкретный blocker и продолжай независимые задачи; не подставляй чужие credentials или fictitious success. В конце предъяви проверяемые артефакты, а не только текст «готово».

## 20. Источники и границы проверки

Дата обращения к техническим источникам — 24 сентября 2026 года. Внешние параметры перепроверяются в F1, ссылки не являются pin зависимости.

- **[S1] Mezo, x402 overview:** https://mezo.org/docs/developers/getting-started/musd-payments-x402/ — network/asset, протокол, facilitator и заголовки.
- **[S2] Mezo, x402 quickstart:** https://mezo.org/docs/developers/getting-started/musd-payments-x402/x402-quickstart/ — SDK reference, buyer/merchant, test MUSD acquisition, предупреждение о default PAY_TO. Overview и quickstart расходятся по описанию mainnet; для этого testnet-only ТЗ mainnet не используется.
- **[S3] Hyperliquid, Info endpoint:** https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint — `l2Book`, публичный запрос и предел уровней.
- **[S4] GitHub, Forks:** https://docs.github.com/en/pull-requests/reference/forks — ограничения visibility fork.
- **[S5] Исходный код:** https://github.com/Dimkox/multi-exchange-engine/tree/4f6583f8590ea091d8a465de0c607e59bfe611a5 — прочитаны README, AGENTS, SECURITY, handoff, roadmap, architecture, research index, runtime.py, package.py, vwap.py и фрагмент verdict.py. Это статическое изучение, не полный аудит или выполненный test run.
- **[S6] Организаторское письмо, предоставленное заказчиком:** AKINDO / Mezo Buildathon; https://app.akindo.io/wave-hacks/OVOO0gdrVU8379D10 и https://luma.com/mezo-buildathon — scope и даты требуют сверки перед submission; регистрацию подтверждает заказчик.

Все policy thresholds, demo price, внутренние даты, архитектурные роли, endpoints и состояния в этом документе — проектные решения/требования, а не цитаты организатора или утверждения об уже реализованном продукте.
