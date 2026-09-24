# Liqvera — handoff

Дата: 2026-09-24. Репозиторий: `Dimkox/liqvera`.

## Бренд и конкурс

**Market reports you can verify.**

Рыночные отчёты, которые можно проверить.

Создано для [MEZO ₿](https://mezo.org/) — [The Mezo Buildathon](https://app.akindo.io/wave-hacks/OVOO0gdrVU8379D10).

Название Liqvera и слоган утверждены владельцем. Канонический репозиторий: [Dimkox/liqvera](https://github.com/Dimkox/liqvera). Актуальное ТЗ — `docs/planning/LIQVERA_FACTORY_TZ.md`; прежний путь оставлен как совместимый указатель для ссылок из фабрики. Технические имена пакетов `mee-*` и форматы данных сохранены.

## Что подготовлено

Ветка `main` содержит самостоятельный технический snapshot upstream `4f6583f8590ea091d8a465de0c607e59bfe611a5` с новой Git-историей. Отдельный документационный коммит перенёс ТЗ из `97f4c7c3b9e1783f4a898412b538a4d6310b902a` (upstream PR №55) и актуализировал точки входа. Секреты, environments, старые refs и история исходника не перенесены.

Состав и контрольные суммы импорта: [PROVENANCE.md](PROVENANCE.md) и [manifest](provenance/import-manifest.json). Контактные данные автора и приватные инфраструктурные адреса из публикации удалены. Унаследованные workflow сохранены как часть технического снимка, но выполнение GitHub Actions на новом репозитории отключено.

## Следующее действие

Локальная разработка начата в ветке `feat/mezo-evidence-f1`. Написан проект
дизайна `docs/superpowers/specs/2026-09-24-mezo-evidence-design.md` и создан
design-only change package `engineering/changes/2026-09-24-mezo-evidence/`.
Активный route фабрики отсутствует, поэтому route ID и receipts не заявляются.

Письменный дизайн одобрен. Детальный F1 implementation plan находится в
`docs/superpowers/plans/2026-09-24-mezo-evidence-f1.md`; change package переведён
в `scoped`. Следующее действие — review плана и выбор режима исполнения, затем
последовательная реализация пяти F1-задач с TDD и отдельными коммитами.

После F1 отдельным планом реализовать F2, затем F3–F7: контракты → проверяемый
отчёт → API/хранение → тестовая MUSD-оплата → интерфейс → приёмка.

Сохранить существующий Stage A verdict. Формальное provenance метаданных, синтетический capture timing и отсутствие готового платёжного сценария остаются задачами реализации. Mainnet, торговля и пользовательский капитал не разрешены.

## Граница проверки этого переноса

Проверены происхождение файлов, новая история и локальные сканы. Финальный Gitleaks-скан дал ровно два срабатывания на хеши: одно подтверждено способом вычисления в коде, второе — совпадением с SHA-256 соответствующего файла. Неразобранных срабатываний не осталось. Публикация проверяется по публичной metadata, анонимному clone и совпадению дерева. Это проверка переноса; полный `make verify`, Docker и on-chain оплата не выполнялись.

Исторические документы исходника сохранены как контекст. При расхождении статуса нового репозитория руководствоваться этим handoff, README и PROVENANCE. Отсутствует локальный `.grok-stack/runtime/active-route.json`; receipts фабрики не создавались и не заявляются.

## Baseline F1 — 2026-09-24

Исходный коммит `d7a60169985e3a697d7eb5cf29b19b00cb8c0f7a` проверен до
изменений. `make artifacts` прошёл. `make verify` остановился на неполном
architecture inventory публикационных файлов; отдельный Python-suite дал 504
passed, 5 связанных graph failures и 6 wheel-build errors из-за отсутствующего
`hatchling`. `make salvage` зависит от объекта приватной истории, которого нет
в публичном clone. Эти результаты сохранены в change package и не выдаются за
зелёный baseline.

Read-only probes подтвердили доступность Hyperliquid BTC public metadata/book,
Mezo Testnet chain ID 31611, bytecode и 18 decimals заданного MUSD, а также
поддержку facilitator для x402 v2 exact. Реальная оплата не выполнялась;
`PAY_TO`, funded buyer и testnet receipt остаются внешними блокерами.

## F1 Task 1 — публикационный inventory

В ветке `feat/mezo-evidence-f1-impl` четыре файла F0-публикации получили
явные bindings к активному `document:graph-authority-handoff`:
`PROVENANCE.md`, оба ТЗ в `docs/planning/` и
`provenance/import-manifest.json`. Классификатор относит `provenance/` к
`DOCUMENTATION`. Регрессионные тесты (22 passed) и precommit graph check
прошли; graph check вывел только ожидаемые declared conflicts. Проблемы
публично воспроизводимого `make salvage` и полного development toolchain
остаются открытыми для следующих задач F1; полный F1 baseline пока не
объявляется зелёным.

Дополнительный полный pytest дал 516 passed и 6 wheel-build errors из-за
отсутствующего `hatchling`, без новых graph failures. `grok_verify --mode pr`
также остаётся красным: pytest упирается в тот же toolchain, а Trivy сообщает
по одному LOW `DS-0026` для двух Stage A Dockerfile.

## F1 Task 2 — проверка salvage в публичном clone

Манифест PR №21 фиксирует SHA-256 четырёх строк импортированных целевых файлов
(два правила указывают на один `reader.py`). `make salvage` проверяет наличие и
байты этих файлов без приватной Git-истории: `items=4 targets=verified
source_objects=unavailable`. Это проверка целевых байтов по манифесту, а не
доказательство происхождения из приватного исходника. Режим
`--require-source-objects` требует исходный commit и сверяет его blob SHA;
при отсутствии объектов он завершается ошибкой.

TDD-проверка зафиксировала исходный RED (4 failed), затем 5 focused tests,
прямой вызов verifier и `make salvage` прошли. Полный pytest: 519 passed и 6
wheel-build errors из-за отсутствующего `hatchling`. `grok_verify --mode pr`
остаётся красным по pytest и Trivy; остальные профили прошли. Следующее
действие F1 — Task 3: завершить документированный development toolchain.

Review Task 2 выявил две ошибки первой реализации: проверка commit не читала
blob payload, а текстовый parser мог принять неверные YAML metadata. Исправление
читает байты каждого исходного blob до статуса `source_objects=verified` и
проверяет YAML по закрытой схеме; отсутствие payload в strict-режиме завершается
ошибкой. Регрессионный тест использует только синтетический локальный Git fixture,
не приватные объекты. Публичный результат выше остаётся проверкой целевых
байтов, а не подтверждением происхождения из исходного репозитория.

## F1 Task 3 — воспроизводимая среда разработки

Корневой `dev` extra теперь содержит тот же `hatchling==1.32.4`, что и
`build-system.requires`; `.venv/` исключён из Git, а тест синхронизации
привязан к `test:runtime-boundaries`. Чистая установка `-e '.[dev]'` сначала
обнаружила несовместимые исходные pins: `eth-account==0.14.0` и
`hyperliquid-python-sdk==0.24.0`, который требует `eth-account<0.14.0`.
Корневой pin исправлен на точный `eth-account==0.13.7`, совместимость пары
проверена resolver и регрессионным тестом. `pip check` не выявил нарушенных
зависимостей; установленный Hatchling имеет версию 1.32.4.

`PATH="$PWD/.venv/bin:$PATH" make verify` прошёл: 534 tests passed, 85 subtests
passed, без прежних wheel-build errors и предупреждений pytest о неизвестных
настройках. Graph check по-прежнему печатает известные declared conflicts;
`make salvage` подтверждает target bytes и сообщает
`source_objects=unavailable`. Следующее действие F1 — Task 4: sanitized Mezo
compatibility lock и read-only probe.

Дополнительный `grok_verify.py --mode pr` прошёл по pytest, Ruff, Bandit,
secret scan и остальным применимым профилям, но общий результат остаётся
`FAIL`: Trivy требует HEALTHCHECK в двух прежних Stage A Dockerfile (по одному
LOW `DS-0026`). Эти файлы не входят в Task 3 и не изменялись.
