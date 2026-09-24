# Multi-Exchange Engine — полный handoff

## Update 2026-08-09: A2 verify image includes actionlint config

- PR CI run `31316449932` passed the PostgreSQL 16.11/17.7, A2 unit,
  replay, fault, and public-boundary gates, then both matrix jobs failed only
  while building the verify image. Its 215-test in-image suite had one failure:
  `/src/.github/actionlint.yaml` was absent.
- Regression coverage now requires the actionlint config in both the exact
  `.dockerignore` build context and the `Dockerfile.a2` verify-stage copies.
  The focused test failed on the missing `COPY` before the implementation.
- `.dockerignore` now re-includes `.github/actionlint.yaml`, and only the
  verify stage copies it. The production image boundary is unchanged.
- Local GREEN evidence: deployment contract 8/8; full A2 suite 215 tests with
  19 expected PostgreSQL-only skips; boundary scan, compileall, and pip check
  passed. Local Docker and actionlint executables were unavailable, so the
  fresh PR run remains the binding in-image and actionlint evidence.
- The Dockerfile validator repeated its documented temporary-pip bootstrap
  failure; fallback static checks found no latest tag, secret assignment, or
  root runtime user and confirmed the urllib healthcheck.
- No Claw workflow was dispatched and no Claw, app-stack, n8n, trading,
  credential, image-tag, or runtime state was changed.

## Update 2026-08-09: controlled A2 candidate promotion producer

- Manual Claw build no longer tags `mee-a2:candidate` inside each PostgreSQL
  matrix leg. The matrix now owns only PostgreSQL 16.11/17.7, unit, replay,
  fault, and boundary gates.
- One `needs: verify-a2-candidate` job builds the exact GitHub SHA once, runs
  pinned Syft/Trivy, uploads the reports, verifies the OCI revision and image
  ID, and runs the present/missing/tampered registry-mount smoke against the
  exact-SHA image before promotion.
- Global non-cancelling workflow concurrency serializes the shared local tag
  and host staging boundary across refs.
- `scripts/promote-a2-candidate.sh` revalidates the source SHA, image revision,
  image ID, and committed registry hash. It tags the candidate, then atomically
  stages a root-owned `0644` reviewed registry, checksum, and receipt under
  `/home/operator/app-stack/secrets`; the receipt is moved last as the deploy commit
  marker and binds source revision, both image IDs, registry hash, and run ID.
- Deployment contract coverage first failed on the old matrix promotion and
  missing staging script, then passed 8 tests. The A2 suite passed 215 tests
  with 19 expected PostgreSQL-only skips; the two CI reference tape modules
  passed 32 tests. Boundary scan, compileall, Bash parse, actionlint, and diff
  checks passed. A broader non-CI discovery attempt reached 431 tests but had
  nine legacy `pytest` import errors because this Windows interpreter does not
  have pytest. Actionlint configuration now records the custom `claw` runner
  label. No workflow was dispatched, no image was built or tagged on Claw, and
  app-stack/Compose/runtime state was not mutated.
- Binding validation still requires an available `[self-hosted, claw]` runner
  with reviewed passwordless authority for the script's `sudo -n` staging
  commands. Absent authority fails closed; it is not proven by Windows checks.

## Update 2026-08-09: A2 frozen-universe status and warm-up quality recovery

- `/v1/a2/soak-status` no longer relies on never-published in-memory coverage
  counters. At runtime freeze it reloads the current run's immutable quality
  minutes, verifies their hashes and exact frozen `(venue, market, channel)`
  membership, and aggregates only those rows; mixed historic runs and foreign
  streams cannot affect the report. `reporting_streams` is the distinct count
  of validated persisted stream keys, so empty and partial evidence now report
  zero and the actual partial count instead of the frozen-universe target 20.
- The runtime now owns a deterministic warm-up minute aggregator. A closed
  healthy UTC minute writes twenty quality records (one L2 stream per frozen
  venue/market) and immediately refreshes the status projection. Feed open and
  close events supply epoch health; a local subscription send no longer counts
  as acknowledgement. A routed venue-native L2 semantic observation is required
  before a stream's later quiet seconds can be healthy, while continuity and
  persistence failures remain invalidating predicates.
- This checkpoint intentionally produces quality only while `WARMING`; it
  does not claim to create five-day `MEASURING` evidence. That producer and
  the terminal soak decision remain separate work.
- Local verification: focused RED regressions failed with empty quality
  reporting 20 streams and no-data health reporting a valid minute. The focused
  status/warm-up/feed/runtime suite then passed 19 tests. Full A2 discovery ran
  211 tests successfully with 19 PostgreSQL-only skips because no local
  `A2_TEST_DATABASE_URL` was configured.

## Update 2026-07-28: A2 package-owned fixture runtime boundary

- The complete committed fixture corpus (seven JSON payloads plus its
  manifest) is package-owned at `multi_exchange_engine/a2/fixtures`; it was
  moved without byte changes and is no longer duplicated under `tests/`.
- `RuntimeDependencies.fixture_root` now defaults to the canonical package
  path, and fixture mode passes that path directly to `FixtureFeed`. Runtime
  source no longer derives a fixture location from a project root or a test
  directory, so the production `/app/multi_exchange_engine` Docker copy
  carries the exact fixture corpus while the production stage still excludes
  tests.
- Unit and integration tests use the same canonical root. The runtime test
  validates every manifest entry's byte length and SHA-256 before accepting
  the default package corpus.
- Verification: the targeted A2 runtime/semantic/replay/deployment suite
  passed 34 tests, fixture-path integration tests passed 3 tests with 2
  expected PostgreSQL-only skips, and the full suite passed 405 tests with 19
  expected PostgreSQL-only skips. `check-a2-boundary.py`, `compileall`, and
  `git diff --check` passed; no Docker build was run.
- This is a source-only packaging repair. It does not build or run Docker,
  start an A2 collector, contact any venue, or alter the shadow-only gate.

## Update 2026-07-28: A2 Task 13 adversarial RC gates complete

- Final reviewed branch commit:
  `2593ec088684c05709bc8c8293e48e400b68a242`; local and
  `origin/feature/a2-boundary-scan` matched after push.
- The whole-branch review first rejected the candidate because production
  lacked the reviewed-registry runtime input and the Docker contract could
  miss an extra `FROM`. Both were fixed. A second review found and mutation-
  confirmed a resume bypass around registry validation; commit `57bee57`
  moved byte/hash verification before database ownership and bound resume to
  the persisted PLAN manifest. Final reviews reported no Critical, Important,
  or Minor findings.
- Local final suite: 404 tests passed with 19 expected PostgreSQL-only skips;
  compileall, public-only boundary, and diff checks passed.
- Claw exact-commit validation was retained at
  `/home/operator/codex-validation/mee-a2-task13-2593ec0-QE2EDegv`.
  The verify and production images built successfully. The real production
  registry smoke accepted the read-only reviewed file and rejected missing
  and byte-tampered mounts while using `--network=none`, read-only rootfs,
  dropped capabilities, and UID/GID `10001:10001`.
- Pinned PostgreSQL 16.11 and 17.7 gates each passed all 22 integration tests
  with no skips, including migration down/up recovery, crash/outage,
  deterministic fresh-process replay, partition, retention, and authority
  checks.
- Pinned Syft produced a 311332-byte CycloneDX SBOM. Pinned Trivy 0.72.0
  produced a 109824-byte report with zero HIGH/CRITICAL findings. The final
  image is 26459830 bytes and `mee-a2:candidate` carries the exact final
  revision label.
- No public collector, measured run, n8n workflow, venue API, or trading path
  was started. Task 14 still owns isolated app-stack Compose and inactive
  read-only n8n integration; the existing unrelated `glider.conf` dirty state
  in `/home/operator/app-stack` was not modified.

## Update 2026-07-28: A2 reviewed-registry runtime boundary and Docker stage parsing

- Production A2 configuration now requires the exact Linux registry mount path
  and its expected SHA-256. Runtime reads that explicit input before any
  database claim, rejects missing or altered bytes, and writes the accepted
  hash to the PLAN manifest. Resume compares the current hash with the
  persisted manifest before it can append a `RESTART` event; valid-but-different
  registry bytes fail closed too.
- `Dockerfile.a2` provides a root-owned `/app/config` mount point but still
  does not copy the registry into production. Task 14 Compose must bind the
  reviewed host file to
  `/app/config/a2-reviewed-perpetual-mappings.json:ro` and set its reviewed
  SHA-256 environment value; the engine plan now makes this mandatory.
- `scripts/smoke-a2-registry-mount.py --image mee-a2:candidate` is the
  production-image mount gate: present input must pass; missing and tampered
  inputs must fail while the image remains read-only and runs as `10001:10001`.
- The deployment contract enumerates every physical `FROM` instruction,
  including optional `--platform` syntax, and requires exactly the three
  approved pinned stages. A mutation adding `FROM busybox:1.36` is rejected.
- This source-only checkpoint does not start A2, run Docker/Compose, change
  `/home/operator/app-stack`, validate the future app-stack repository, or permit
  public warm-up, measured capture, or live trading.

## Update 2026-07-28: A2 selector and proxy-path hardening

- Selector assignments through constant-key subscripts, for example
  `payload["method"]`, now receive the same AST private-capability check as
  named and attribute selectors.
- Lowercase action compounds such as `ordercreate` are rejected at explicit
  capability/action boundaries; arbitrary interior fragments such as `border`
  are not raw-substring matches.
- `channel` is a structured selector. Private `account` is rejected, while
  the explicit public `order_book`, `trade`, and `market_stats` channel pattern
  remains accepted.
- The internal proxy exception requires the exact root A2 path
  `a2/transport.py`; a nested file named `transport.py` cannot inherit it.
- This remains a static source boundary only, not evidence of public data
  quality, reconstruction, opportunity, profitability, warm-up, or live use.

## Update 2026-07-28: A2 boundary scanner review fixes

- Scanner now resolves relative imports against the logical
  `multi_exchange_engine.a2` package and rejects a relative escape to
  `domain.execution`; legitimate A2-local relative imports remain allowed.
- Private capability literals are checked in AST message-selector dict fields,
  selector-like assignments and keyword arguments. Delimited/camel-case tokens
  such as `order.cancel` and `orderCancel` are rejected without substring
  scanning comments, prose, or public channel names.
- Forbidden normalized-book symbols are checked as AST names, attributes,
  import aliases, class names and function names.
- The public URL allowlist contains only the four venue URLs. The internal
  proxy is a separate exception for exactly one module-level
  `transport.py: PROXY_URL` assignment; copies or duplicates fail closed.
- New copied-package mutations cover every reviewed escape. This static gate
  still does not establish data quality, reconstruction, edge, profitability,
  public warm-up, or live-trading authority.

## Update 2026-07-28: A2 public-only boundary regression

- Добавлен fail-closed AST scanner `scripts/check-a2-boundary.py`. Он проверяет
  только production A2 source: import boundary, third-party allowlist,
  credential-free public URL literals, structured outbound message types и
  запрещённые normalized-book symbols.
- `tests/a2/test_dependency_boundary.py` копирует A2 package во временную
  директорию и mutation-tests отклоняют execution import, неразрешённый domain
  import, private outbound `order` и private URL literal. Comments и harmless
  public `order_book` names не считаются private capability evidence.
- Scanner success означает только отсутствие запрещённых capabilities в
  статически проверяемом A2 source. Он не доказывает data quality,
  reconstructability, arbitrage edge, profitability или readiness for live
  trading.
- После GREEN этого checkpoint public warm-up и five-day measured run всё ещё
  требуют следующих packaging/deployment gates; venue/private APIs, signers,
  account data и торговые методы не запускались.

## Update 2026-07-27: A2 Task 10 replay and fault gate complete

### Результат

- Реализован deterministic PostgreSQL replay по одному raw batch за раз:
  compressed/uncompressed hashes, strict envelopes, contiguous batch/ingest
  indexes, frame indexes по `(venue, boot_id, connection_epoch)` и повторная
  venue-native semantic classification.
- Replay сравнивает raw-envelope semantics со stored decoder evidence и
  fail-closed выдаёт только typed A2 reason codes. Order book не строится.
- `scripts/replay-a2-run.py` печатает один credential-free canonical JSON
  report. Ошибка configuration получает exit `2`; integrity/runtime failure —
  exit `1`; traceback и DSN наружу не выходят.
- Два свежих Python процесса против одного PostgreSQL snapshot обязаны
  выдавать побайтно одинаковый stdout. Это доказано integration test.
- Decoder schema/version drift, hash corruption, gzip truncation/append,
  duplicate/missing index, epoch merge и semantic mismatch имеют negative
  replay coverage.

### Fault matrix

- Queue saturation завершает ingress с `QUEUE_SATURATED`.
- WebSocket EOF сохраняется как `WEBSOCKET_DISCONNECTED`.
- Lighter nonce gap открывает `GAP_OPEN`; большой `offset` при правильной
  nonce chain остаётся valid и не используется как continuity key.
- Hyperliquid source-time regression сохраняется как
  `SOURCE_TIME_REGRESSION`/`INVALID_SOURCE_TIME`.
- Stored future decoder version даёт `DECODER_VERSION_MISMATCH`.
- Existing binding PostgreSQL harness реально убивает child до и после commit,
  доказывая atomic/idempotent recovery, и отдельно закрывает connection перед
  pending retry, доказывая outage/reclaim path.

### Файлы и Git

- Core replay checkpoint: `b3d9a79`.
- Canonical CLI/PostgreSQL/fault checkpoint: `e699e31`, pushed в
  `origin/feature/a2-raw-wire-capture`.
- Изменены/добавлены:
  `multi_exchange_engine/a2/model.py`,
  `multi_exchange_engine/a2/repository.py`,
  `multi_exchange_engine/a2/replay.py`,
  `scripts/replay-a2-run.py`,
  `tests/a2/test_replay.py`,
  `tests/a2/test_repository_unit.py`,
  `tests/a2/integration/test_replay_postgres.py`,
  `tests/a2/integration/test_fault_matrix.py`.

### Проверка на Claw

- Source archive exact commit: `e699e31`; SHA-256
  `3946e196fdcd0f4222c786b36aba066612bec3b7eaff385ea1be077442b93aec`.
- Pinned Linux wheelhouse: 13 wheels; archive SHA-256
  `4edce479619007a533831b968d793b5d26ca90f6b9852364b5a4c8a53ff6a759`.
- Runtime: `python:3.12-slim-bookworm`, `postgres:16-alpine`, network
  `app-stack_airgap_net`, ephemeral random database password, read-only source
  mount и tmpfs для venv/bytecode.
- Focused Task 10 + binding crash/outage gate: 8/8.
- Полный PostgreSQL integration gate: 22/22, skips запрещены.
- Полный suite на Python 3.12: 377/377.
- `pip check` и `compileall` прошли.
- `/home/operator/app-stack` остался на
  `5109675c17c1b3d8975c208c83d054bbc4e5b550`; HEAD и dirty-state hash до/после
  совпали. Временные containers/source/archive удалены.
- Evidence:
  `outputs/mee-a2-task10-e699e31-claw.log` и
  `outputs/mee-a2-task10-e699e31-claw.status`.

### Что пробовали и что не сработало

- Первый runner делал `pip install` через `proxy-gateway`; intermittent TLS
  record corruption оборвал download до тестов. n8n имеет тот же proxy origin,
  но обычный Node `fetch` сам по себе environment proxy не применяет.
- Повтор заменён на offline delivery pinned Linux wheelhouse. В test container
  нет dependency egress и нет обходного direct-WAN route.
- Следующий runner не передал `PYTHONPATH=/workspace`; explicit script видел
  `scripts/`, но не package `tests`. Path зафиксирован явно.
- Затем `compileall` корректно отказался писать `__pycache__` в read-only
  source mount. Bytecode output перенесён в `/tmp/pycache`; source mount не
  ослаблялся.

### Claim boundary и следующий шаг

- Task 10 доказывает replay integrity и fault handling сохранённых public
  application messages. Он не доказывает reconstructability, arbitrage edge,
  прибыльность или готовность live trading.
- Venue/private APIs, signer, account data и торговые методы не вызывались.
- Следующий шаг: Task 11 forbidden-capability scan и claim-boundary regression.
  До его GREEN и следующих packaging/deployment gates public warm-up и
  пятидневный measured run не запускать.

## Update 2026-07-27: A2 Task 10 bounded replay core checkpoint

- Добавлен batch-bounded deterministic replay. В памяти одновременно
  находится не больше одного raw batch и его bounded decoder evidence range.
- Replay проверяет оба stored hashes, fixed gzip profile, canonical NDJSON,
  contiguous batch/ingest indexes и epoch-local frame indexes.
- Observer state разделён по `(venue, boot_id, connection_epoch)`: одинаковый
  номер epoch нового boot не сливается со старым.
- Reproduced observation сравнивается с combined persisted evidence:
  semantic/source fields из immutable raw envelope плюс decoder version,
  class/continuity/error из `raw_decoder_observations`.
- Terminal report имеет canonical SHA-256, exact `VERIFIED|FAILED` и только
  типизированные A2 reason codes. Replay не строит order book.
- PostgreSQL reader загружает decoder rows только для диапазона текущего
  batch и fail-closed отклоняет missing, duplicate или non-contiguous rows.
- TDD RED: отсутствовал `multi_exchange_engine.a2.replay`, затем отсутствовал
  typed bounded decoder reader. Focused GREEN: 8/8 tests; `compileall` и
  `git diff --check` прошли.
- Один первоначальный corruption test ничего не менял: последний gzip byte
  уже был `0x00`. Fixture исправлена на гарантированный XOR; production code
  для этого не менялся.
- Следующий шаг Task 10: canonical CLI, PostgreSQL replay integration и fault
  matrix. Claw gate и public warm-up на этом checkpoint не запускались.

## Update 2026-07-27: A2 Task 9 runtime composition complete

### Результат

- Собран concrete A2 service runtime для `public|fixture`: strict config,
  PostgreSQL run lease, clock qualification, discovery/frozen universe,
  append-only lifecycle, durable batch writer, оба public raw feeds и exact
  GET-only status surface.
- Startup зафиксирован как lease/database → clock/discovery/freeze → writer →
  Hyperliquid → Lighter → status. Shutdown идёт через единый boundary:
  stop admission → close feed epochs → durable batch flush → lifecycle
  persistence → lease release → status stop.
- `python -m multi_exchange_engine.a2` не печатает DSN или произвольный текст
  исключения. Configuration, terminal и generic failures имеют bounded
  operator-facing сообщения.

### Persistence и restart

- Public discovery получает только fixed credential-free endpoints через
  `proxy-gateway`. Exact raw Hyperliquid/Lighter control payloads и processed
  frozen universe сохраняются атомарно после hash/provenance/registry
  validation.
- Restart восстанавливает exact lifecycle events и frozen universe из
  PostgreSQL. Уже замороженный run не делает повторный discovery и не меняет
  ранжирование.
- Status persistence cursor обновляется после каждого подтверждённого DB
  commit, а не только при shutdown. Callback получает следующий
  `batch_sequence` и `ingest_index` только после успешного `persist`.
- Lifecycle/connection control writes вынесены из asyncio event loop через
  bounded thread calls; batch persistence уже использует тот же подход.

### Fixture boundary

- Fixture mode не создаёт public HTTP/WebSocket session. Он строит
  deterministic synthetic discovery из committed reviewed registry,
  замораживает 10 mappings и пропускает через настоящий ingress/writer семь
  exact committed application payloads: три Hyperliquid и четыре Lighter.
- Fixture readiness доказывает только wiring, raw-byte admission, durability,
  startup/shutdown и отсутствие venue network. Она не доказывает полноту
  semantic routing, public subscription acknowledgement, качество данных,
  reconstructability или arbitrage expectancy.
- Public collector readiness означает: WebSocket открыт и все fixed
  subscription requests отправлены. Качество acknowledged subscription и
  каждого one-second slot остаётся binding обязанностью warm-up/gate.

### Файлы Task 9

- `multi_exchange_engine/a2/config.py`
- `multi_exchange_engine/a2/status_api.py`
- `multi_exchange_engine/a2/app.py`
- `multi_exchange_engine/a2/runtime.py`
- `multi_exchange_engine/a2/fixture_runtime.py`
- `multi_exchange_engine/a2/__main__.py`
- `multi_exchange_engine/a2/feed.py`
- `multi_exchange_engine/a2/hyperliquid_feed.py`
- `multi_exchange_engine/a2/lighter_feed.py`
- `multi_exchange_engine/a2/pipeline.py`
- `multi_exchange_engine/a2/repository.py`
- `tests/a2/test_config.py`
- `tests/a2/test_status_api.py`
- `tests/a2/test_app.py`
- `tests/a2/test_runtime.py`
- связанные feed/pipeline/repository unit и PostgreSQL integration tests.

### Что пробовали и что не сработало

- Первый Claw runner ожидал отсутствующий cached
  `python:3.12-alpine`; выбран имеющийся `python:3.12-slim-bookworm`.
- Первый container run передал explicit unittest modules без
  `PYTHONPATH=/workspace`, поэтому Python видел `scripts/`, но не package
  `tests`. Финальный runner фиксирует top-level path.
- Попытка использовать host Python подтвердила `Python 3.12.3`, но system
  environment не содержит `aiohttp/psycopg`. Временный venv сначала получил
  склеенные IP всех сетей `proxy-gateway`, затем host-to-container DB path
  завис. Этот смешанный маршрут отброшен.
- Финальный gate повторяет рабочий n8n network pattern: Python runner и
  ephemeral PostgreSQL находятся в `app-stack_airgap_net`; outbound dependency
  fetch идёт только через `http://proxy-gateway:1080`, DB — по container DNS.
- Чтение полного `docker logs` через Bitvise зависло после terminal
  `EXIT=0`; отдельная bounded cleanup-проверка подтвердила отсутствие
  контейнеров, archive и temp tree.

### Проверка и Git

- Финальный локальный suite: 362 tests, 345 passed, 17 ожидаемых PostgreSQL
  skips без локального DSN.
- Claw binding PostgreSQL gate: 17/17, runner `EXIT=0`; gate отдельно падает
  при любом skip.
- `compileall`, `pip check` и `git diff --check` прошли.
- Runtime checkpoints pushed:
  `6730b85`, `c472926`, `da17eef`, `0c2024d`.
- `/home/operator/app-stack` не изменялся. Временные Claw containers, source tree
  и archive удалены.
- Public warm-up, пятидневный measured run, replay и торговые операции не
  запускались.

### Следующий шаг

- Task 10: deterministic bounded PostgreSQL replay и fault matrix. Без
  byte-identical двойного replay и crash/outage evidence запуск public
  warm-up преждевременен.

## Update 2026-07-27: A2 Task 9 GET-only status checkpoint

- Добавлен exact GET-only aiohttp surface: `/health`, `/ready`,
  `/v1/a2/soak-status`. Автоматический `HEAD` отключён; известные пути дают
  `405` для `HEAD/POST/PUT/PATCH/DELETE`, mutating routes отсутствуют.
- Status публикует только типизированный `A2StatusSnapshot`: lifecycle,
  immutable window, warm-up, aggregate coverage, typed failure counts и
  batch/index/hash progress. Произвольный config/secret payload не принимается.
- Readiness равна `true` только при одновременно held ownership, ready
  database, frozen universe и ready Hyperliquid/Lighter collectors.
- `A2Application` фиксирует startup order
  database/ownership → discovery/freeze → writer → Hyperliquid → Lighter →
  status. Shutdown order:
  stop admission → close both epochs → flush boundary → persist lifecycle →
  release ownership → stop status.
- Ownership conflict останавливает startup до discovery/writer/feeds/status и
  публикуется как typed failure. SIGINT/SIGTERM только выставляют stop event;
  shutdown выполняет один и тот же boundary-controller.
- TDD: ожидаемый RED — отсутствовали `a2.status_api` и `a2.app`. Один тест
  ошибочно использовал quality label `MISSING_SLOT` как terminal enum; посылка
  исправлена на `COVERAGE_BELOW_THRESHOLD`. Focused suite прошёл 6/6.
- Полный локальный suite: 356 total, 340 passed, 16 ожидаемых PostgreSQL
  skips. `compileall`, `pip check`, 88-column scan и `git diff --check`
  прошли.
- Следующий шаг внутри Task 9: concrete runtime assembly и `__main__.py`.
  Public/fixture run не запускался.

## Update 2026-07-27: A2 Task 9 safe-config checkpoint

- Добавлен строгий `A2Config`: canonical run UUID, только `public|fixture`,
  fixed app-stack proxy, IPv4 status bind, bounded port и allowlisted log
  level.
- `A2_DATABASE_URL` и неизвестные `A2_*` переменные отклоняются без вывода
  значений. PostgreSQL DSN читается только из bounded regular non-symlink
  файла; на Linux group/other permissions запрещены.
- DSN исключён из `repr` и ошибок. Secret file проверяется до и после
  открытия, ограничен 4096 bytes и не допускает пустой, multiline, NUL или
  whitespace-mutated value.
- TDD: ожидаемый RED — отсутствовал `a2.config`; первый GREEN обнаружил
  неверный exact-type check для Windows `WindowsPath`, после исправления
  focused config suite прошёл 5/5.
- Полный локальный suite: 350 total, 334 passed, 16 ожидаемых PostgreSQL
  skips. `compileall`, `pip check`, 88-column scan и `git diff --check`
  прошли.
- Следующий шаг: status/application RED, GET-only API и boundary-ordered
  application composition. Public или fixture run ещё не запускался.

## Update 2026-07-27: A2 Task 8 quality, lifecycle and five-day gate

### Цель и результат

- Реализован credential-free Task 8: fixed-slot quality evidence,
  60-минутный contiguous warm-up, одно immutable measured window и
  deterministic `PASS|FAIL` gate.
- Исправлена критическая несогласованность: отдельные A2 design/plan всё ещё
  задавали 24 часа, хотя binding Stage A spec и явная команда пользователя
  требуют пять полных data days. Единый контракт теперь равен ровно
  432000 секундам после warm-up, half-open
  `[measured_start, measured_end)`.
- Торговых/private/account/signer/order/transaction методов нет. Task 8 не
  строит книги и не заявляет прибыльность.

### Что изменено

- Каждый из 20 frozen venue-market L2 streams получает 60 expected
  one-second slots на UTC minute. Slot valid только при acknowledged
  subscription, active epoch, valid recorder clock, ready persistence и
  отсутствии continuity gap. Quiet healthy second valid; отсутствующий slot
  синтезируется как `MISSING_SLOT`.
- Source-time age и latest cross-venue receive skew считаются exact
  `Decimal` из integer nanoseconds. Пороги 750/200/250 ms сохраняются как
  hash-bound evidence для A3 и сами не уменьшают A2 coverage. Future source
  time получает отдельный reason count.
- Warm-up требует 60 contiguous complete minutes. Invalid minute, временной
  скачок или restart сбрасывает progress append-only событием `WARMUP_RESET`.
  После 60-й минуты bounds фиксируются один раз; restart во время measurement
  не меняет и не продлевает окно.
- `SoakGate` проверяет ровно 10 mappings, 20 L2 streams и 7200 quality
  minutes на stream. На каждом stream 432000 expected slots; ровно 429840
  valid slots (99,5%) ещё проходят, 429839 уже дают
  `COVERAGE_BELOW_THRESHOLD`.
- `PASS` требует valid replay shape и terminal evidence hash. Missing stream,
  bad quality hash, bad replay anchor, silent drop, wrong duration или
  неполный window дают immutable `FAIL`; ручного override, `GO` или `EXTEND`
  в A2 нет.
- Python `RunEvent` и PostgreSQL authoritative trigger теперь независимо
  запрещают `MEASURING/PASS` без exact 432000-second bounds, окно в
  `PLANNED/WARMING`, неправильную длительность и изменение bounds terminal
  событием. `PASS` decision row также обязан иметь пятидневное окно.

### Файлы Task 8

- `multi_exchange_engine/a2/quality.py`
- `multi_exchange_engine/a2/lifecycle.py`
- `multi_exchange_engine/a2/soak_gate.py`
- `multi_exchange_engine/a2/model.py`
- `multi_exchange_engine/a2/repository.py`
- `migrations/000002_a2_raw_capture.up.sql`
- `tests/a2/test_quality.py`
- `tests/a2/test_lifecycle.py`
- `tests/a2/test_repository_unit.py`
- `tests/a2/integration/test_pipeline_postgres.py`
- `tests/a2/integration/test_repository_postgres.py`
- A2 design, plan и этот `handoff.md`.

### Что пробовали и что не сработало

- Первый Claw runner поставил только `psycopg`; импорт repository требует
  pinned public transport dependency `aiohttp`, поэтому tests остановились до
  миграции. Runner переведён на полный `requirements-a2.txt`.
- Первый полный PostgreSQL run дал 15 pass и одну rejected fixture: старый
  owner-immutability test вставлял фиктивный `PASS` с bounds `1..2`. Fixture
  заменена на `FAIL`, поскольку тест проверяет только owner-level запрет
  `UPDATE/DELETE`, а не успешный soak.
- Root test container создал временный `__pycache__`, который не мог удалить
  host user. Повторный runner запретил bytecode; старый temp tree удалён через
  точечно смонтированный `/tmp`. Финальная cleanup-проверка прошла.
- При финальном разделении reducer и gate focused-тест поймал забытый
  `SoakDecision` import в `LifecycleEvent.finalize`. Импорт восстановлен,
  повторный focused и полный suite прошли.

### Проверка и среда

- Focused Task 8: 11/11 passed.
- Локальный полный suite: 345 total, 329 passed, 16 PostgreSQL tests
  ожидаемо skipped без DSN.
- `compileall`, repository contract suite 23/23 и `git diff --check` прошли.
- На Claw: ephemeral `postgres:16-alpine` и Python 3.12 container в
  `app-stack_airgap_net`; binding PostgreSQL gate 16/16, skips 0.
- Временные archive, runner, test tree и PostgreSQL container удалены.
  `/home/operator/app-stack` не изменялся; production deployment и пятидневный
  сбор не запускались.

### Следующий шаг

- Task 9: safe configuration, application composition и GET-only status API.
- До Task 9/10 нельзя запускать warm-up или пятидневный сбор: Task 8 доказал
  reducer/gate и DB constraints, но runtime orchestration, status surface и
  deterministic database replay ещё отсутствуют.

## Update 2026-07-27: A2 Task 7 public discovery and raw feeds

### Цель и результат

- Task 7 реализует только credential-free public discovery и raw capture для
  Hyperliquid/Lighter. Торговых, private, signer, account, order, transaction,
  transfer или withdrawal методов нет.
- Контракт инструмента: одинаковый base asset, linear perpetual, `1x`
  displayed base units, USD valuation, USDC settlement и обязательный
  `EXPLICIT_ORACLE_STABLECOIN_BASIS/v1`. Это не доказательство нулевого basis
  risk или прибыльности.
- Коммитный manual registry содержит 12 текущих reviewed кандидатов; runtime
  ранжирует их только после semantic membership review и замораживает top 10
  по минимуму положительного venue-reported 24h quote volume.

### Что изменено

- Добавлены fixed public transports:
  `https://api.hyperliquid.xyz/info`,
  `wss://api.hyperliquid.xyz/ws`,
  Lighter `orderBooks` и
  `wss://mainnet.zklighter.elliot.ai/stream?readonly=true`.
  Все venue-соединения идут через `http://proxy-gateway:1080`; TLS verification
  включена, redirect policy fail closed, WebSocket heartbeat равен 30 секундам,
  frame limit равен 8 MiB.
- JSON discovery разбирается строго: числа с дробной частью становятся
  `Decimal`, duplicate keys и non-finite constants отклоняются. Semantic value
  каждый раз восстанавливается из exact hash-bound raw bytes и не может
  разойтись с payload после внешней мутации.
- Discovery обрабатывается до записи. Затем одна PostgreSQL transaction
  сохраняет:
  1. exact raw Hyperliquid `metaAndAssetCtxs`;
  2. exact raw Lighter active `orderBooks`;
  3. exact raw Lighter read-only `market_stats/all`;
  4. processed hash-bound frozen mappings.
  Missing, duplicate, wrong-run, wrong-provenance или hash-unbound evidence
  отклоняется до transaction. Lighter catalog дополнительно обязан реально
  разрешать каждый frozen market ID/base asset; raw-only и processed-only
  успешная запись запрещена.
- Добавлена append-only таблица `a2.raw_control_evidence` с фиксированными
  venue/kind/transport/source URI constraints, raw `bytea`, SHA-256, 8 MiB
  limit и owner-level immutable trigger.
- Добавлены по одному multiplexed public WebSocket collector на venue. Exact
  text UTF-8/binary application bytes допускаются в ingress до semantic
  observer. Reconnect создаёт новый epoch и observer. Queue saturation и
  oversized frame закрывают epoch без бесконечного reconnect. OPEN/CLOSE
  evidence хранит фактические extensions и точную версию `aiohttp`.
- Добавлены deterministic mapping-review generator, committed registry,
  критический review-документ и credential-free live smoke.

### Файлы Task 7

- `multi_exchange_engine/a2/transport.py`
- `multi_exchange_engine/a2/feed.py`
- `multi_exchange_engine/a2/hyperliquid_feed.py`
- `multi_exchange_engine/a2/lighter_feed.py`
- `multi_exchange_engine/a2/universe.py`
- `multi_exchange_engine/a2/repository.py`
- `migrations/000002_a2_raw_capture.up.sql`
- `config/a2-reviewed-perpetual-mappings.json`
- `docs/a2-mapping-review.md`
- `scripts/build-a2-mapping-review.py`
- `scripts/smoke-a2-public-discovery.py`
- `tests/a2/test_transport.py`
- `tests/a2/test_mapping_registry.py`
- `tests/a2/test_hyperliquid_feed.py`
- `tests/a2/test_lighter_feed.py`
- `tests/a2/test_repository_unit.py`
- `tests/a2/integration/test_repository_postgres.py`
- A2 design, plan и этот `handoff.md`.

### Что пробовали и что не сработало

- `aiohttp 3.14.3` не принимает `max_redirects` в `ws_connect`; это обнаружил
  первый Claw live smoke. Защита заменена на session middleware, которое
  отклоняет любой 3xx до follow-up request, плюс проверку exact final WS URL и
  empty response history.
- Первый финальный Claw gate оборвался на transient
  `SSL record layer failure` при `pip` через proxy-gateway. Cleanup удалил
  временную БД и файлы. Добавлен bounded dependency-install retry.
- Следующий PostgreSQL gate выявил только ошибку нового теста:
  отсутствовал локальный `import psycopg` перед zero-row assertion. После
  исправления весь binding gate прошёл.

### Проверка и среда

- Локально: suite выполнил 334 теста — 318 passed и 16 PostgreSQL tests
  ожидаемо skipped без DSN; focused Task 7/repository — 46 passed;
  `compileall`, `pip check`, line-length scan и `git diff --check` прошли.
- На Claw: ephemeral PostgreSQL 16 в `app-stack_airgap_net`, 16/16 binding
  integration tests без skips. Доказаны raw+processed round-trip,
  pre-transaction rejection с нулём строк и immutable восьми evidence tables.
- Live smoke через реальный `proxy-gateway`: 12 current accepted mappings,
  10 frozen mappings, 3 raw control documents, 313786 raw bytes, один
  Hyperliquid application WebSocket frame, `public_only=true`.
- `/home/operator/app-stack` не изменялся. Временный PostgreSQL container, archive,
  test directory и runner удалены после проверки.

### Следующий шаг

- Task 8: warm-up lifecycle, fixed measured window и soak gate.
- До Task 8 нельзя заявлять готовность пятидневного сбора: collectors и
  persistence primitives готовы, но orchestration, 60 contiguous warm-up
  minutes, 5-day window, coverage decision и production deployment ещё не
  реализованы.

## Update 2026-07-27: A2 compatibility contract corrected before Task 7

- Dmitry selected the explicit basis-risk model after official contract review
  showed that ticker equality cannot prove identical quote conventions.
- A reviewed pair now requires the same base asset, USD-valued price, USDC
  settlement, linear payoff, one base-asset displayed-size unit, and exact
  `1x` multipliers. `quote_currency` was replaced by
  `valuation_currency`.
- Hyperliquid and Lighter quote/oracle references are stored separately. Every
  admitted mapping must carry
  `EXPLICIT_ORACLE_STABLECOIN_BASIS/v1`; downstream economics may not assume
  the recorded oracle/stablecoin basis is zero.
- Venue-reported positive USD-valued 24-hour notionals remain usable for
  discovery ranking without FX conversion. Their raw payload hashes, separate
  quote references, and the basis-risk policy are bound into the frozen
  manifest and canonical PostgreSQL mapping document.
- Focused TDD produced the expected missing-field RED and then passed 18
  universe/repository tests. Full local discovery passes 309 tests with 15
  explicit PostgreSQL skips; `compileall` and `git diff --check` pass. This is
  a binding design correction, not a profitability or
  executable-equivalence claim. Next action remains A2 Task 7 public
  transport, reviewed registry, and raw public feeds.

## Update 2026-07-27: A2 Task 6 durable restart and outage recovery

- A leased repository now derives the next `batch_sequence` and
  `ingest_index` from the complete committed batch tail. It rejects gaps,
  overlaps, malformed indexes, a foreign/closed lease, and any divergent
  restart cursor instead of guessing from process memory.
- `BatchWriter` accepts that durable cursor, so a new process may use a new
  `boot_id` and connection epoch while continuing the immutable run indexes.
  The existing `MEASURING` event retains the original fixed measurement
  window.
- `RepositoryBatchSink` owns the PostgreSQL run lease, retains the exact
  pending batch and decoder observations across a connection outage, verifies
  readiness by reconnecting and reclaiming ownership, and accepts only the
  pre-commit or identical-post-commit cursor before replay.
- Availability failure and evidence conflict are now separate. A database
  outage stops admission, emits `PERSISTENCE_UNAVAILABLE` once, and retries
  only after readiness. `IntegrityConflict` is terminal and never enters the
  readiness loop.
- The binding PostgreSQL gate ran on Claw against an ephemeral PostgreSQL 16
  container on `app-stack_airgap_net`. All three Task 6 scenarios passed:
  process death before commit left zero rows; death after commit replayed
  idempotently; and a forced connection loss stopped admission, reclaimed the
  lease, and committed the retained batch. No persistent database or
  credential was created.
- Focused terminal/repository coverage passes 23 tests. Full local discovery
  passes 308 tests with 15 explicit PostgreSQL skips; the binding Claw gate
  supplies the three Task 6 PostgreSQL results. `compileall` and
  `git diff --check` pass. Next action is A2 Task 7: fixed public transports,
  deterministic mapping-review evidence, and read-only Hyperliquid/Lighter
  feeds.

## Update 2026-07-27: A2 Task 5 final UTC and role-boundary remediation

- Both security-definer helpers now compute exactly one explicit UTC date from
  `(CURRENT_TIMESTAMP AT TIME ZONE 'UTC')::date`. Partition authorization,
  the current/yesterday window, retention argument validation, and the
  seven-complete-UTC-day cutoff no longer depend on caller or session
  `TimeZone`; production migration SQL contains no `CURRENT_DATE`.
- `a2_writer` and `a2_maintainer` are created with explicit `NOLOGIN`,
  `NOSUPERUSER`, `NOCREATEDB`, `NOCREATEROLE`, `NOINHERIT`,
  `NOREPLICATION`, and `NOBYPASSRLS`. Every up migration revalidates all
  attributes and rejects any role that is a member of another role with
  SQLSTATE `55000`. External principals may still be granted membership in
  these A2 roles.
- PostgreSQL coverage now asserts exact catalog attributes and zero inherited
  memberships, changes the session timezone to `+14:00` and `-12:00` while
  proving UTC partition/retention decisions and no early boundary drop, and
  exercises an unsafe pre-existing `LOGIN` maintainer rejection followed by
  safe restoration and idempotent migration recovery.
- TDD RED produced exactly three expected failures: missing role hardening,
  session-local partition authorization, and session-local retention. Focused
  GREEN passes 22 tests. Full local discovery passes 304 tests with 12 explicit
  PostgreSQL skips; `compileall` and `git diff --check` pass.
- `A2_TEST_DATABASE_URL` remains unavailable. The expanded PostgreSQL migration,
  catalog, timezone, and unsafe-role runtime paths were compiled and discovered
  but not executed; the zero-skip Task 12 CI/Claw gate remains mandatory.

## Update 2026-07-27: A2 Task 5 adversarial-review remediation

- Logical batch identity is serialized across UTC partitions with a stable
  transaction-scoped advisory lock taken before the global lookup and insert.
  Replay now reads and validates every stored batch column, rejects duplicate
  logical sequences, verifies lengths, hashes, compression profile, UTC day,
  and full `RawWireBatch` integrity, and maps corruption to
  `IntegrityConflict`.
- Frozen universe persistence now stores a complete canonical versioned
  document in `identity_json`: run and manifest identity plus every
  `FrozenMapping` field, including exact exponent-form decimals and discovery
  evidence.
- Partition creation is restricted to the server's current/yesterday window
  and serialized before DDL. Retention accepts only `CURRENT_DATE`, derives its
  cutoff server-side, locks each candidate child `ACCESS EXCLUSIVE`, rechecks
  nonterminal runs in that same transaction, and is granted only to a separate
  `a2_maintainer` role.
- Down migration revokes A2 grants and drops only the A2 schema. Cluster roles
  intentionally survive rollback. Writer permissions remain limited to
  `SELECT`, `INSERT`, and current-window partition creation; production
  repository SQL still contains no `UPDATE` or `DELETE`.
- Adversarial RED tests exposed the missing canonical mapping document, missing
  logical-write lock, incomplete replay verification, unsafe retention order,
  overbroad retention authority, and runner-discovery weakness. Focused
  repository/migration/runner coverage now passes 21 tests.
- Final local verification passes: `compileall`, `pip check`,
  `git diff --check`, and full discovery (301 tests, 10 explicit PostgreSQL
  skips). The binding runner still exits `2` with the exact
  `A2_TEST_DATABASE_URL is required` diagnostic because no PostgreSQL DSN is
  available. PostgreSQL runtime/catalog/concurrency validation remains an
  explicit Task 12 CI/Claw gate; it is not claimed here.

## Update 2026-07-27: A2 Task 5 append-only PostgreSQL evidence repository

- Added PostgreSQL-16-compatible `a2` evidence tables, UTC-day partitions,
  immutable owner-visible mutation triggers, serialized lifecycle transition
  placeholders, one-terminal-event uniqueness, and A2-scoped down migration.
- Partition and retention helpers are security-definer functions with a fixed
  safe search path, validated generated identifiers, revoked public execution,
  and narrow `a2_writer` grants. Retention only removes closed raw-wire child
  partitions older than seven complete UTC days and refuses nonterminal runs.
- Added strict frozen repository records, stable UUID advisory-lock ownership,
  integer-nanosecond UTC day derivation, canonical JSON without a float path,
  DSN-redacted connection failures, transactional batch/observation persistence,
  exact immutable retry comparison, replay iteration, and typed conflicts.
- PostgreSQL integration coverage applies up/down/up and exercises owner
  immutability, lease contention, identical/conflicting retry, UTC partition
  creation, seven-day retention boundaries/refusal, rollback, and restart.
- TDD evidence: the initial RED was the expected missing repository import; the
  runner contract then RED-failed while its script was absent. Focused
  unit/static tests pass 15 tests. `compileall`, full Python discovery (293
  tests, 8 explicit PostgreSQL skips), `pip check`, and `git diff --check`
  pass. `A2_TEST_DATABASE_URL` is absent: the binding runner exits `2` with
  `A2_TEST_DATABASE_URL is required`; no PostgreSQL integration result is
  claimed. That gate remains pending for Task 12 CI/Claw.

## Update 2026-07-27: A2 Task 4 final durability remediation

- An ingress terminal condition now retains an immutable first
  `A2ReasonCode`, stops admission, wakes the writer, and invokes its callback
  once. The writer drains/persists every already accepted frame (including any
  retry batch) before raising the typed terminal reason; an empty terminal
  ingress fails promptly.
- A run-identity mismatch no longer strands a valid partial batch: the writer
  seals and durably persists its existing same-run lines, observations, and
  tickets, then fails closed with the mismatched head still queued and unpopped.
- Regression coverage includes two completed frames queued before writer start,
  requiring the first durable batch before the retained mismatch terminal, and
  running-writer oversize/saturation terminal drains with first-reason/callback
  uniqueness.
- TDD evidence: RED lacked the typed terminal failure export; after the new
  terminal contracts, focused Task 4 passed 16 tests. `compileall`, full Python
  suite (270 tests), and `git diff --check` passed.

## Update 2026-07-27: A2 Task 4 review remediation

- `BatchWriter` is now a continuous event-driven consumer: private ingress wake
  signals cover admission, observation completion, and shutdown, so it waits
  without polling while queues are empty or the earliest ticket is incomplete.
- Decoder outcomes are immutable `DecoderObservation` data. Typed decoder
  failures remain a normal raw-frame record with `error_code/error_detail` and
  are persisted rather than terminating the epoch.
- `stop_at_boundary()` stops ingress and waits until all accepted queue heads,
  partial data, and any retained retry batch are committed; it does not return
  while a durable ticket is pending. Persistence readiness is mandatory and an
  outage reports once per episode before retrying the exact same objects.
- Destructive queue operations are private writer-only methods. Candidate run
  identity and observation completion are validated before dequeue; a mismatch
  fails closed with the candidate retained.
- Clock evidence now maps malformed Decimal text, including `InvalidOperation`,
  to typed `CLOCK_EVIDENCE_INVALID`.
- TDD evidence: remediation RED exposed missing event liveness, public dequeue,
  run-ID retention, and invalid-decimal typing. Focused Task 4 suite passed 14
  tests; `compileall`, full Python suite (268 tests), and `git diff --check`
  passed.

## Update 2026-07-27: A2 Task 4 bounded capture ingress and durable batches

- Added fail-closed clock readiness: exact built-in/nonnegative clock readings,
  `25 ms` error and `50 ms` wall/monotonic divergence boundaries, plus immutable
  decisions that retain observed evidence and never use wall time for ordering.
- Added a read-only JSON host-clock evidence provider. It accepts only the
  exact evidence shape and `Normal` leap status, derives the conservative
  millisecond bound from exact Decimal strings, and maps missing, stale, or
  malformed evidence to `CLOCK_EVIDENCE_INVALID` without host command execution.
- `CaptureIngress` now copies raw bytes into separate bounded FIFO queues per
  venue, uses monotonically increasing arrival tickets, accounts queue bytes on
  pop, and fails closed on count/byte saturation or frames above `8 MiB` with no
  eviction.
- `BatchWriter` consumes the lowest queue-head ticket only after its one-shot
  decoder observation completes. It emits contiguous canonical envelopes and
  deterministic raw batches, closes at wall-second or size limits, and marks
  immutable durable tickets only after sink persistence returns.
- A persistence outage stops both ingress streams, reports
  `PERSISTENCE_UNAVAILABLE`, retains the exact pending batch/observations for
  explicit readiness-probe retry, and does not re-encode or reindex it. Boundary
  stop waits for that durable batch boundary.
- TDD evidence: focused RED failed from the expected absent `clock` and
  `pipeline` modules. Focused Task 4 suite passed 10 tests; `compileall`, full
  Python suite (264 tests), and `git diff --check` passed. Scope remains public,
  read-only, shadow-only, and without exchange/private/trading capability.

## Update 2026-07-27: A2 Task 3 review fixes

- `subscribed/order_book` now requires only the snapshot `nonce`; a missing
  delta-only `begin_nonce` is retained as `None`. Such a valid snapshot opens
  or restores `VALID`, including after a detected gap.
- The Hyperliquid watermark regression now proves that valid `100`, invalid
  `99`, and invalid `95` leave the valid watermark unchanged until valid `101`.
- Lighter tests now cover both a mismatched `begin_nonce` and an equal
  `begin_nonce` with non-increasing new nonce; both open a gap and later deltas
  remain blocked pending a snapshot.
- Both observers now have explicit no-escape, exact-reason coverage for
  malformed JSON, duplicate keys, non-object top levels, missing fields, type
  mismatches, unknown messages, and unroutable markets. Fixtures and their
  previously pinned byte lengths/SHA-256 values remain unchanged.
- TDD evidence: focused RED failed as expected because a no-`begin_nonce`
  snapshot was classified invalid and a missing Lighter `trades` field was
  misclassified. Focused Task 3 suite then passed 14 tests; `compileall`, full
  Python suite (254 tests), and `git diff --check` passed.

## Update 2026-07-27: A2 Task 3 venue-native semantic observers

- Added pure, per-connection-epoch Hyperliquid and Lighter public-wire
  observers. Their constructor accepts only a copied, non-empty exact-string
  venue-market-to-canonical-identity map; neither observer imports a book
  reducer, shadow evaluator, or exchange adapter.
- Hyperliquid classifies `l2Book`, `trades`, and `activeAssetCtx`, validates
  finite `ctx.funding` without widening the bounded observation/envelope
  schema, and rejects only per-market `l2Book` source-time regressions without
  advancing its valid watermark.
- Lighter classifies public snapshots, deltas, trades, and market stats;
  validates nonce continuity only for `order_book:<market-id>` and treats the
  source `offset` as retained evidence rather than a continuity comparator.
  A gap blocks later deltas until a fresh snapshot, while non-book channels do
  not mutate L2 continuity state.
- Seven credential-free, representative public-format fixtures are pinned by
  exact byte length and lowercase SHA-256. Their manifest records official
  documentation URLs fetched on 2026-07-27 and explicitly identifies every
  fixture as documentation-shape-derived rather than a claimed live message.
- TDD evidence: exact focused RED failed from the two absent semantic modules;
  focused Task 3 suite then passed 12 tests. `compileall`, full Python suite
  (252 tests), and `git diff --check` passed. Scope remains public, read-only,
  and without account, transaction, order, signer, credential, reconstruction,
  economics, or trading behavior.

## Update 2026-07-27: A2 Task 2 review fixes

- The reviewed-universe gate now rejects duplicate Hyperliquid market IDs and
  duplicate Lighter market IDs across distinct mapping IDs before discovery
  evidence or selection. A frozen set of ten mappings therefore represents ten
  distinct reviewed venue markets on each venue.
- Regression coverage now independently rejects unknown discovery mapping IDs,
  mismatched venue market IDs, malformed lowercase SHA-256 values, invalid
  timestamps, duplicate reviewed mapping IDs, and duplicate per-venue evidence.
- The manifest test varies every independently changeable valid source field,
  run ID, both venue records, and score-driven rank/order. The singleton
  `LINEAR_PERPETUAL` identity component remains guarded by its exact rejection
  test because it has no second valid value.
- TDD evidence: duplicate-venue-market RED produced two expected focused test
  failures; focused Task 2 suite then passed 16 tests. Full verification follows
  before the review-fix commit.

## Update 2026-07-27: A2 Task 2 reviewed discovery universe frozen

- Added immutable reviewed-mapping, venue-discovery, frozen-mapping, and
  frozen-universe contracts. A reviewed identity must use the exact canonical
  `LINEAR_PERPETUAL` product kind, match the reviewed quote, settlement, and
  payoff fields, and have identical positive finite `Decimal` multipliers.
- Freezing accepts exactly one positive finite `Decimal` 24-hour quote-volume
  record from Hyperliquid and Lighter for each admitted reviewed mapping. It
  rejects duplicate mapping/evidence IDs, mismatched venue market IDs, invalid
  evidence hashes/timestamps, and insufficient candidates; missing valid venue
  evidence contributes only to the insufficient-candidates outcome.
- The selected universe contains exactly ten mappings, ranked by the lower
  cross-venue volume and then UTF-8 mapping-ID bytes. The SHA-256 manifest
  deterministically binds run ID, rank, every reviewed/frozen field, both
  evidence payload hashes, timestamps, and exact Decimal strings without
  float conversion.
- TDD evidence: expected missing-module RED; a focused product-kind RED after
  contract clarification; focused universe suite passed 11 tests. Next action:
  A2 Task 3 approved reviewed-mapping registry and discovery transport.

## Update 2026-07-27: A2 Task 1 deterministic gzip rereview fix

- `RawWireBatch` now rejects a direct construction unless its gzip payload is
  byte-for-byte equal to the required fixed raw-DEFLATE-level-6 profile over
  its NDJSON, in addition to validating both hashes and decompression.
- A regression test uses valid gzip with nonzero `mtime` and a recomputed
  SHA-256 to prove fail-closed rejection. The payload-SHA test now supplies a
  different valid lowercase 64-character digest, reaching the integrity check.
- TDD evidence: the nonprofile-gzip focused RED failed because direct
  construction was accepted; focused A2 suite then passed 17 tests. `pip
  check`, `compileall`, full Python suite (224 passed), and `git diff --check`
  passed.

## Update 2026-07-27: A2 Task 1 review fixes

- The raw envelope schema is now exactly `mee-a2-envelope/v1`; the immutable
  capture profile accepts only `websocket-application-message-post-decompression/v1`,
  `mee-a2-envelope/v1`, `mee-a2-ndjson/v1`, and
  `gzip-raw-deflate-6-mtime0-os255/v1` as exact built-in strings.
- Decoding produces a persisted-only `RawFrameEnvelope`. It never manufactures
  the transient `ReceivedFrame.arrival_ticket` from durable `ingest_index`, and
  its encoded keys remain exactly the approved binding envelope schema.
- `RawWireBatch` now validates all bytes, hashes, gzip content, frame metadata,
  order, and timestamps in its constructor, so direct inconsistent construction
  fails closed before a caller can trust the object.
- TDD review-fix evidence: initial focused RED showed missing profile constants,
  absent persisted envelope fields, and a bypassable direct batch constructor;
  a second RED showed profile string subclasses were accepted. Focused A2 suite
  then passed 16 tests; `pip check`, `compileall`, full Python suite (223
  passed), and `git diff --check` passed.

## Update 2026-07-27: A2 Task 1 raw evidence codec complete

- Added immutable credential-free A2 capture-boundary models for public
  Hyperliquid/Lighter text or binary application-message evidence.
- Canonical raw envelopes preserve payload bytes through base64, enforce exact
  schema fields, duplicate-key rejection, integrity length/SHA-256 checks, and
  deterministic UTF-8 JSON without raw payload excerpts in decoder detail.
- Raw batches retain contiguous ingest order as terminal-LF NDJSON and emit
  byte-stable manual gzip (fixed header, raw DEFLATE level 6, CRC32, OS 255)
  plus both SHA-256 digests. Batch verification fails closed on framing,
  metadata, compression, hash, ordering, or payload conflicts.
- Added `requirements-a2.txt` with reviewed pinned collector dependencies.
- TDD evidence: expected missing-A2-module RED; focused A2 suite 12 passed;
  dependency installation and `pip check`, `compileall`, full Python suite
  (219 passed), and `git diff --check` passed.
- Scope remains public, read-only, credential-free, and without account,
  signer, order, cancellation, transaction, RFQ, withdrawal, private channel,
  book reconstruction, or economics capability.
- Next action: A2 Task 2 reviewed discovery evidence and frozen universe.

## Update 2026-07-27: A2 implementation plan ready

- Dmitry approved the A2 raw-wire capture design.
- The executable TDD plan is
  `docs/superpowers/plans/2026-07-27-a2-raw-wire-capture.md`.
- It contains 15 separately reviewable tasks from immutable raw codec through
  public discovery/feeds, PostgreSQL, replay, CI/image validation, app-stack
  integration, fixture deployment, warm-up, and the fixed five-day soak.
- Collector source/image ownership remains in
  `Dimkox/multi-exchange-engine`. The canonical `/home/operator/app-stack`
  Compose/n8n/deploy source is
  `https://github.com/Dimkox/openclaw-airgap-farm`.
- The app-stack remote `main` was
  `5109675c17c1b3d8975c208c83d054bbc4e5b550` during planning. The existing
  Windows clone is ahead one and behind eight, so implementation must use a
  fresh isolated worktree from refreshed `origin/main`.
- A2 uses its own Compose project on external
  `app-stack_airgap_net`. This prevents the main app-stack deployment's
  `docker compose up --remove-orphans` from deleting an active A2 soak.
- Engine CI tests PostgreSQL 16.11 and 17.7. Claw retains its existing
  PostgreSQL 16 service; A2 migrations must remain PostgreSQL-16 compatible.
- Public venue mapping is not ticker inference. The plan generates a current
  candidate report, commits a reviewed mapping registry with evidence hashes,
  and refuses warm-up unless at least ten current accepted candidates exist.
- Recorder clock error comes from a fresh host `chronyc -c tracking` evidence
  file. Missing, stale, malformed, or unsynchronized evidence blocks
  readiness; the collector does not substitute an unqualified clock source.
- Runtime exchange egress is explicit through `proxy-gateway:1080`; venue
  URLs are fixed, TLS verification cannot be disabled, Lighter stays
  `readonly=true`, and account/trading methods remain forbidden.
- PostgreSQL authentication uses only the dedicated app-stack secret file.
  Venue, wallet, signer, account, and private-endpoint credentials are absent.
- The plan self-review passed: 1,956 lines, 15 tasks, 113 checkboxes, balanced
  Markdown fences, maximum line length 88, required contract coverage,
  forbidden-placeholder scan, and `git diff --check`.
- Next action: Dmitry selects execution mode `1` for subagent-driven task
  execution or `2` for inline task execution. Do not implement before that
  choice.

## Update 2026-07-27: A2 raw-wire capture design approved

- Dmitry approved
  `docs/superpowers/specs/2026-07-27-a2-raw-wire-capture-design.md`.
- The A2 branch is `feature/a2-raw-wire-capture`; the approved design commit is
  `c3e2b9f`.
- A2 freezes ten formally equivalent common linear perpetuals by the lower
  Hyperliquid/Lighter 24-hour quote volume, warms up for 60 contiguous minutes,
  and then records one fixed half-open five-day measurement window.
- The collector retains exact WebSocket application-message bytes before JSON
  parsing, venue-native continuity evidence, deterministic one-second gzip
  NDJSON batches, and append-only UTC-partitioned PostgreSQL evidence.
- A2 is public and read-only. It has no exchange credentials, signing, private
  endpoints, order methods, reconstruction, arbitrage evaluation, or trading.
- Deployment is a Python collector under `/home/operator/app-stack`, with exchange
  traffic restricted to the existing proxy/airgap network contract.
- PostgreSQL authentication is the sole runtime credential exception. It must
  come from the existing `/app-stack` secret/config boundary and must never be
  logged or persisted in raw evidence.
- A2 passes only with deterministic replay and hashes, zero silent drops, typed
  restart/failure evidence, and at least 99.5 percent one-second L2 slot
  coverage for every one of the 20 frozen venue-market streams.
- The approved design accidentally prohibited every credential-bearing
  runtime input, which made database authentication impossible. The wording is
  corrected without authorizing any venue or wallet secret.
- Next action: write and review the A2 TDD implementation plan. Do not start
  implementation before Dmitry selects the execution mode.

## Update 2026-07-27: A1 Task 7 bounded replay and golden corpus

- Added a bounded LF-only binary reader and deterministic replay for canonical
  A1 NDJSON. It validates schema, consecutive indexes, input identity, and the
  hash chain before returning; evaluates with `1..8` workers, holds at most
  `workers * 2` pending cases, and compares outputs in record-index order.
  Internal chain validity returns only `SELF_CONSISTENT`; only a matching
  caller anchor returns `VERIFIED`.
- The committed 36-case corpus is `shadow-pair-domain-golden-v1`, format
  `mee-a1-ndjson/v1`, domain `pair-domain/v1`, evaluator
  `pair-evaluator/v1`, arithmetic
  `exact-rational-render28-half-even/v1`, reasons `pair-reasons/v2`, hash
  `sha256-domain-separated/v1`, canonical JSON `mee-canonical-json/v1`,
  selection `synthetic-conformance/v1`, and costs
  `displayed-taker-entry-cost/v1`.
- Its manifest pins reference commit
  `515143b026e084e8fefbecc76f691a960f9cfd19`. The terminal anchor is
  `2b458cc42f6332bbef4def3708da552b175bd2fb1270588f7ec637f987db8d99`
  at `tests/fixtures/shadow-golden-v1.terminal.sha256`; the complete tape is
  `tests/fixtures/shadow-golden-v1.ndjson`.
- Adversarial tests cover physical encoding and limits, protected bytes,
  duplicate/unknown keys, Decimal/float failures, structural mutations,
  identities/hashes/counts, truncation/appending, hostile Decimal context,
  fresh process replay, forced shuffled completion, worker failure typing,
  external-anchor mismatch, and forbidden imports across every `tape_*.py`
  module plus the generator. Final focused tests: 80 passed. Full Python suite:
  207 passed.
- CI extracts the committed manifest reference, regenerates both files into
  `RUNNER_TEMP`, and requires byte equality without secrets or caches.
  The claim boundary is **pair-domain parity** over normalized immutable
  `PairInput` and projected `evaluate_pair` output only. It is not raw-wire,
  collector, reconstructed-book, expectancy, signing, execution, order,
  cancellation, database, or deployment evidence.
- Next action: implement Go pair-domain conformance against this immutable
  Python corpus. A2 raw-wire capture and A3 stateful book reconstruction remain
  separate, non-authorized plans.

### Final whole-branch review fix

- Pair mapping validation now rejects equal buy/sell `mapping_id` values before
  quantity or economics as `MARKET_MAPPING_REJECTED`.
- Additional entry costs accept only the frozen immutable pairs `GAS` with
  `documented-entry-cost/v1` and `ENTRY_STRESS` with
  `synthetic-entry-stress/v1`; all other pairs yield
  `COST_MODEL_INCOMPLETE`.
- Replay threads the exact caller `TapeLimits` through case parsing, domain
  reconstruction, and worker evaluation. Before surfacing a synchronous error,
  it resolves only pending lower record indexes in order, so first-error
  identity is independent of worker count while normal pending bounds remain
  unchanged.
- Two fresh 36-case generations matched the committed fixture and sidecar byte
  for byte. Reference commit, terminal hash, pair-domain claim boundary, and
  the single-writer one-directory publication contract remain unchanged.

### Review fix: replay trust boundary and two-target publication

- Caller anchors are validated before stream access as exact built-in `str`
  values containing 64 lowercase hexadecimal characters. Terminal comparison
  uses `hmac.compare_digest`; subclasses, equality spoofing, uppercase, bad
  length, nonhex, and non-string values fail `EXTERNAL_ANCHOR_MISMATCH`.
- Recognized records complete strict schema validation before index errors.
  Failure of the post-trailer `read(1)` is fail-closed and typed
  `TRAILER_NOT_FINAL`, because immediate EOF could not be proved.
- Fixture generation now stages and fsyncs both files beside their targets,
  snapshots prior bytes into hashed backups, and durably publishes a journal
  before either target replacement. Any pre-commit failure restores both old
  targets. A deterministic startup recovery handles an interrupted journal;
  successful publication removes the journal and all transaction artifacts.
- The fixture and terminal targets must resolve to one parent directory.
  Different parents fail with a deterministic `ValueError` before recovery,
  stage, backup, journal, fixture build, or target mutation.
- Corpus conformance freezes exactly 36 unique tick IDs and exact equality with
  the normative tick set. The committed fixture and terminal hash are unchanged.

## Update 2026-07-27: A1 Task 6 deterministic hash chain

- Added pure `shadow.tape_chain` builders for manifest, case, and trailer
  records. They derive the case identity solely from canonical input bytes and
  record hashes solely from the complete record mapping without `record_hash`.
- Hash domains are fixed as `MEE-A1-INPUT-v1\0` and `MEE-A1-RECORD-v1\0`;
  all digests are canonical lowercase SHA-256 hexadecimal. Case metadata,
  expected output, index, and predecessor affect the record hash, while only
  input affects `case_id`.
- Chain verification revalidates strict records, IDs, hashes, predecessor
  links, consecutive indexes, uniqueness, manifest binding, and trailer count.
  Its returned terminal hash is only `SELF_CONSISTENT`; it is not externally
  verified and no external anchor, reader, replay, I/O, network, credential,
  persistence, collector, execution, order, cancellation, or deployment path
  was added.
- TDD evidence: expected missing-module RED; focused chain suite 10 passed;
  full Python suite 168 passed; `compileall`, changed-file 88-column scan, and
  diff check passed. Next: physical canonical NDJSON reader and replay remain
  separate tasks.

## Update 2026-07-26: A1 Task 5 strict tape schema and projection

- Added frozen manifest, case metadata, case, and trailer records with exact
  recursive field allowlists, safe integer checks, lowercase hash/reference
  validation, and exact frozen A1 constants. Version mismatches retain the
  stable Task 4 error families.
- Added explicit `PairInput` and `PairEvaluation` projections without
  `dataclasses.asdict`. Financial values use the canonical Task 4 Decimal
  codec, raw book provenance is named `source_payload_sha256`, levels and
  additional costs reconstruct as tuples, and thresholds remain immutable.
- Reasons persist as ordered `{family, code}` objects. `entry_eligible` is
  scoped only as `DISPLAYED_TAKER_ENTRY_ONLY`; early rejections have no
  quantity/depth/economics, while `NON_POSITIVE_AFTER_COSTS` retains all
  economics. Missing mappings alone round-trip as `None`.
- Case direction is derived exactly as `buy_market.venue->sell_market.venue`;
  no case normalization or venue aliasing is accepted.
- TDD evidence: expected missing-module RED; 20 focused and 150 full Python
  tests passed. This task adds no tape reader, hash chain, replay, collector,
  network, credential, database, execution, order, cancel, or deployment path.

## Update 2026-07-26: A1 Task 4 canonical Decimal and JSON codec

- Added the evaluator-independent `shadow.tape_codec` boundary. Decimal values
  use bounded coefficient/exponent strings produced from `Decimal.as_tuple()`;
  negative zero, nonfinite values, noncanonical spellings, more than 128
  digits, and canonical exponents outside `-1000..1000` fail closed.
- Restricted JSON uses duplicate-aware parsing, compact ASCII key order, exact
  decode/re-encode byte comparison, safe integers, printable ASCII strings,
  and trusted frozen A1 limits including eight replay workers. It rejects BOM,
  invalid UTF-8, CR/LF payloads, floats/constants, unknown Python types,
  oversized strings/lines, excessive depth, and parser recursion breaches.
- `decode_canonical_json_line` consumes payload bytes after a physical LF has
  been required and stripped by the future Task 7 reader. This task adds no
  schema semantics, hash chain, evaluator import, network, credential,
  persistence, collector, execution, order, cancellation, or deployment path.
- TDD evidence: expected missing-module RED; focused codec suite 19 passed;
  full Python suite 130 passed. `compileall`, 88-column scan, and diff checks
  are required at the commit gate. Next: strict tape schema and projection.

## Update 2026-07-26: A1 Task 3 versioned entry-cost evidence

- `displayed-taker-entry-cost/v1` replaces opaque pair fee and extra-cost
  scalars with immutable per-leg `FeeEvidence` and typed `CostComponent`
  provenance. It accepts only exact `TAKER` and `EXACT_QUOTE` evidence for the
  evaluated buy/sell venues, current schedule/component timestamps, lowercase
  SHA-256 evidence, and the pair quote currency; no conversion path exists.
- Pair outputs now attribute buy fee, sell fee, total fee, and additional cost
  separately while retaining exact Fraction comparisons for gross and net.
  Incomplete, invalid, future, unsupported, or cross-currency evidence rejects
  after quantity/depth/notional gates with `COST_MODEL_INCOMPLETE` and no
  economics. Documented Decimal zero remains valid; `None` is unknown.
- Stage A now names the reference arithmetic profile
  `exact-rational-render28-half-even/v1`; only display rendering rounds.
- Verification: focused provenance/pair suite 25 passed; full Python suite 111
  passed; `compileall`, changed-Python 88-column scan, and `git diff --check`
  passed. No network, credential, database, collector, execution, order,
  cancellation, or deployment behavior changed.

## Update 2026-07-26: A1 Task 2 reviewed market mappings and payoff boundary

- Added immutable `MarketMappingEvidence` with exact reviewed market-field,
  identity, SHA-256, validity-window, Decimal, and printable-ASCII validation.
  Missing or invalid mappings reject normalized pairs with
  `MARKET_MAPPING_REJECTED` before quantity, depth, or economics.
- `VenueMarket.displayed_size_unit` is required and explicit in both public
  discovery mapping contracts and every repository constructor. Pair evaluation
  admits only exact `PERPETUAL` plus `LINEAR` contracts; all other payoff or
  product kinds reject with `UNSUPPORTED_PAYOFF`.
- Verification: focused provenance/pair suite 20 passed; full Python suite 105
  passed. No network, credential, database, collector, execution, order,
  cancellation, or deployment behavior changed. Next: versioned entry-cost
  evidence.

### Review fix: active market Decimal boundary

- `VenueMarket` now rejects bool, int, and non-finite values for contract
  multiplier, quantity step, and minimum notional before positivity or mapping
  comparison. This closes a malformed active-market path that could compare
  equal to reviewed Decimal evidence.
- Verification: domain/provenance/pair covering suite 27 passed; `compileall`,
  changed-file 88-column scan, and diff check passed.

## Update 2026-07-26: A1 Task 1 stable reasons and receive-time causality

- Added the versioned normalized-pair `ShadowRejectCode` order in
  `shadow.reasons`; `shadow.quantity` re-exports it for backwards-compatible
  imports, while pair and VWAP import the canonical module directly.
- `evaluate_book_pair` now accumulates
  `BOOK_RECEIVED_AFTER_EVALUATION` when either immutable snapshot receive time
  is after the evaluation tick. It does not infer an exchange-to-receive clock
  offset; the existing future exchange timestamp recorder-clock rejection stays.
- Verification: focused reasons/quality suite 21 passed; full Python suite 95
  passed; `compileall`, 88-column scan, and `git diff --check` passed.
- No network, credential, database, collector, execution, or deployment path
  changed. Next task: reviewed linear market mappings and payoff boundary.

## Update 2026-07-26: A1 implementation plan approved

- Dmitry approved the written A1 pair-domain design.
- The executable TDD plan is
  `docs/superpowers/plans/2026-07-26-a1-pair-domain-parity-tape.md`.
  It has seven independently committable tasks: stable reasons/receive-time
  causality, reviewed linear market mappings, versioned entry-cost evidence,
  canonical Decimal/JSON, strict tape schema/projection, domain-separated hash
  chain, and bounded replay/golden corpus/CI.
- The plan was checked for placeholder instructions, required binding profile
  names, line length, whitespace, and separate commit boundaries.
- Independent architecture review closed pre-code contract gaps: missing
  mappings are explicit evaluator inputs, active markets carry a required size
  unit, A1 costs are quote-currency-only, all frozen IDs are in the manifest,
  replay workers are bounded, and CI regenerates with the manifest-pinned
  evaluator commit before byte-comparing the corpus.
- This checkpoint changes documentation only. No runtime, network, credential,
  PostgreSQL, collector, order, or deployment behavior changed.
- Next action: execute Task 1 through a fresh implementation agent using TDD,
  followed by independent spec and code-quality review before Task 2.

## Update 2026-07-26: A1 pair-domain parity tape design

- Dmitry selected self-contained canonical NDJSON and the normalized-domain A1
  boundary. Raw venue bytes remain a later A2/A3 collector and reconstruction
  corpus.
- Architect and trading-domain reviews returned `CONDITIONAL GO` and blocked
  freezing the original sketch. The approved conceptual revision adds a Task 0
  causality guard, reviewed mapping/multiplier evidence, linear-payoff boundary,
  typed fee/cost provenance, and one rational/render28 arithmetic profile.
- The written design is
  `docs/superpowers/specs/2026-07-26-a1-pair-domain-parity-tape-design.md`.
  It defines bounded canonical JSON/Decimal encoding, domain-separated record
  and input hashes, an externally anchored terminal hash, strict version
  separation, typed reason families, fail-closed replay, and the adversarial
  corpus matrix.
- Dmitry approved this design before implementation planning. No runtime,
  network, credential, PostgreSQL, collector, or trading behavior changed at
  this checkpoint.

## Update 2026-07-26: Task 2 isolated Decimal rendering context

- `shadow.exact` now renders non-terminating fractions inside one fresh explicit
  `Context`: precision 28, `ROUND_HALF_EVEN`, `MIN_EMIN`/`MAX_EMAX`, clamp 0,
  and explicit invalid-operation, division-by-zero, and overflow traps. Each
  render receives a local copy rather than the caller's ambient Decimal context.
- A hostile ambient context (precision 3, round-down, `Emin=-9`, `Emax=9`,
  clamp 1, every trap enabled) cannot underflow, trap, or zero the positive
  five-thirds times `10^-100` VWAP rendering.
- Verification: quantity 9 passed, VWAP 10 passed, pair 10 passed, full Python
  suite 92 passed; `compileall`, 88-column scan, and `git diff --check` passed.

## Update 2026-07-26: Task 2 exact VWAP and pair economics remediation

- Added `multi_exchange_engine/shadow/exact.py` as the shared exact arithmetic
  boundary. It converts finite Decimals to integer-backed Fractions without the
  ambient Decimal context and returns terminating decimals exactly.
- Non-terminating output ratios use an explicit 28-significant-digit
  `ROUND_HALF_EVEN` contract under a locally fixed context; regression covers
  five thirds and a nonzero five-thirds times `10^-100` VWAP.
- VWAP sweep, actual notional, and VWAP use Fractions end-to-end. Pair target/
  overshoot checks, gross capture, entry fees, net capture, and divergence also
  use Fractions before deterministic output conversion.
- Precision-28 regressions retain exact
  `10000000000000000000000000001` quantity/notional and do not mislabel the
  equal-notional pair as `TARGET_OVERSHOOT`.

## Update 2026-07-26: Task 2 adversarial arithmetic remediation

- Replaced Task 2 common-quantity arithmetic with exact integer-backed
  `Fraction` operations. Decimal coefficient/exponent conversion, rational LCM,
  ceiling units, native quantities, and target/overshoot comparisons no longer
  use ambient Decimal context precision. Only terminating fractions convert back
  to `Decimal`; unsupported native quantities reject fail closed.
- Quantity now rechecks both rounded top-price notionals against target and
  target-plus-overshoot. Regression uses target
  `10000000000000000000000000001` under precision 28.
- Depth validates every immutable displayed level before consuming any level, so
  an invalid unconsumed tail rejects rather than being hidden by early fill.
- Next action remains golden-tape serialization and deterministic replay.

## Update 2026-07-26: exact paired shadow-entry evaluation

- Added credential-free Task 2 shadow domain contracts for canonical common
  quantity, authoritative displayed-depth VWAP, and paired entry economics.
  All monetary/quantity arithmetic is exact finite `Decimal`; no network,
  credential, account, signing, order, cancellation, or deployment path was
  introduced.
- Canonical quantity is the ceiling of the maximum target/minimum requirement
  on the decimal LCM of `quantity_step * contract_multiplier` for both venues.
  It rechecks native step alignment, venue minimum quantity/notional, and
  per-leg `target * (1 + overshoot_bps / 10_000)` before returning a quote.
- Depth consumes immutable asks/bids strictly in supplied authoritative order,
  never extrapolates beyond visible levels, and uses
  `taken_native * price * contract_multiplier`; VWAP is actual notional divided
  by requested canonical quantity.
- Pair evaluation calls the quality gate before all quantity/depth/economics,
  maps only typed quantity/depth rejections, verifies book-market venue/symbol
  and reviewed identity, then computes gross capture, explicit entry fees,
  extra cost, raw VWAP divergence, and positive-net eligibility. Actual swept
  leg notionals outside the target/overshoot bounds fail closed.
- Verification at this checkpoint: quantity 9 passed, VWAP 9 passed, pair 10
  passed, full Python suite 91 passed; `compileall`, 88-column scan, and
  `git diff --check` passed.
- Limitations: this is entry-only indicative shadow math, not lifecycle PnL,
  fill certainty, funding, latency/stress, exit economics, execution, or alpha
  evidence. Next action: golden-tape serialization and deterministic replay.

## Update 2026-07-26: deterministic public book quality gate

- Added immutable public `BookEvidence`, explicit immutable `QualityThresholds`,
  and `BookPairQuality` under `multi_exchange_engine/shadow/quality.py`.
- The gate evaluates all blockers before any quantity, VWAP, fee, or economics:
  boot epoch, continuity, active connection, venue-specific age, source and
  receive skew, recorder clock error, and wall/monotonic drift.
- Default limits remain external configuration: Hyperliquid 750 ms, Lighter
  200 ms, source/receive skew 250 ms, recorder clock error 25 ms, and drift
  50 ms. Malformed IDs, clocks, hashes, threshold mappings, and unknown venue
  limits fail closed.
- P1 regression hardening rejects mutable/non-`OrderBookSnapshot` inputs and
  every book level whose price or quantity is not a finite positive `Decimal`.
- Verification: focused quality suite 18 passed; full Python suite 63 passed;
  `compileall`, 88-column production-line scan, and `git diff --check` passed.
- This is credential-free, public shadow evaluation only; no network client,
  account, signer, order, cancellation, execution, or deployment was added.
  Next action: exact displayed-depth VWAP and paired shadow economics, gated
  exclusively by this quality result.

## Update 2026-07-26: credential-free public adapter split

- Added `HyperliquidPublicAdapter` and `LighterPublicAdapter` in dependency-
  isolated public modules. They require only injected public read transports,
  mapping providers, and receive-time functions; no account, key, signer,
  nonce, send transport, or trading method is present.
- The public modules import no execution domain. Existing `HyperliquidAdapter`
  and `LighterAdapter` now subclass their corresponding public adapters and
  retain the private account/order/fill behavior unchanged.
- GitHub Actions now has a separate pinned Python 3.12 reference-engine job.
- Verification: `python -m unittest tests.exchange.test_public_adapter_boundaries
  -v` (3 passed); `python -m unittest discover -s tests -v` (45 passed);
  `python -m compileall -q multi_exchange_engine tests` passed.
- No network client, key use, trading call, or deployment was added.
- Next action: exact shadow VWAP and data-quality domain.

## Update 2026-07-26: scope correction and Python migration

- Active branch: `feature/python-arbitrage-engine`.
- The owner clarified the product as cross-exchange arbitrage for any verified
  common asset.
- Hyperliquid and Lighter are the first venue adapters; later DEX/CEX venues
  must use the same capability-specific contracts.
- Go is not the target runtime. The accepted migration decision is
  `docs/adr/0001-python-universal-arbitrage-core.md`.
- Python Step 1 is implemented: venue-neutral economic instrument identity,
  venue market constraints, evidence-gated dynamic common-market discovery.
- Python Step 2 was committed as `151aab7`.
- Python Step 3 was committed as `572aba7`.
- The market contract now supports both fixed ticks and venue rules expressed
  as decimal places plus significant digits, required by Hyperliquid.
- Python Step 4 adds `multi_exchange_engine/exchange/hyperliquid.py`: an
  injected-transport adapter with no live HTTP client, signing, secrets, or
  network calls in tests.
- Hyperliquid discovery reads official `metaAndAssetCtxs`, rejects malformed
  metadata/context alignment, derives quantity step from `szDecimals`, and
  carries the `6 - szDecimals` decimal plus five-significant-digit price rule.
  Contract multiplier, economic identity, and equivalence evidence are supplied
  only by a data-driven mapping provider; they are never inferred from a ticker.
- Official `l2Book`, `clearinghouseState`, `frontendOpenOrders`/`orderStatus`,
  and `userFillsByTime` payloads map through exact Decimal-only contracts. L2
  snapshots use `sequence=None`, because this endpoint provides no sequence.
- Submit/cancel responses distinguish accepted, filled, rejected, and unknown;
  a cancel emits official `cancelByCloid` for the exact owned CLOID only.
  Unknown/malformed paths remain non-terminal, including `unknownOid`.
  Terminal cancel/reject variants are normalized, invalid CLOID/size/price are
  rejected before transport, full fill pages fail closed, and fill identity is
  the exchange `hash` plus `tid`.
- Current verification: 30 Python tests pass, `compileall`, line-length, and
  `git diff --check` pass.
- Python Step 5 adds `LighterAdapter` and strict normalization helpers, pinned
  to official `lighter-python` v1.1.2 commit
  `6957dd8a1b36894ca9580be0d51de30aeea3bd4a`. The injected boundary holds no
  HTTP client, signer, secret, or network call.
- Active perp discovery uses `order_book_details(filter="perp")`; reviewed
  mappings supply identity/equivalence while metadata supplies Decimal ticks,
  minimum base, and minimum quote. No asset, market ID, leverage, slippage, or
  multiplier is embedded in the adapter.
- Independent review found seven P1 defects in the first Lighter version. The
  hardened reducer now accepts the official `subscribed/order_book` snapshot,
  verifies `order_book:{market_id}`, uses the outer millisecond timestamp, and
  refreshes receive time on each event. An update must have
  `begin_nonce == previous nonce`; gaps make the book unavailable and `offset`
  remains non-authoritative.
- Nonces no longer start at zero inside the adapter. An injected one-writer
  coordinator supplies an API-key-bound authoritative nonce and is told whether
  the send was accepted, rejected before sequencer admission, or remains
  unknown. A separate injected signer returns tx type/info/hash; exact
  ownership and signed hash are retained before `sendTx`.
- `sendTx code=200` remains API acceptance only. Official tx lookup uses
  `by=hash,value=...`; cancellation can use only the exact owned client index,
  even after a different venue order index is reconciled.
- Fills now retain official client and venue IDs, calculate maker/taker fee from
  Lighter fee ticks, normalize timestamps to milliseconds, and derive order
  VWAP from filled quote/base. Partial fills are explicit. A filled reducing
  order that closes the position to flat is valid; reconciliation instead
  checks exact order/trade quantity consistency.
- Current verification: 42 Python tests pass, `compileall`, line-length, and
  `git diff --check` pass. No live order, credential use, authorization, or
  deployment was added.
- Claw runtime was checked: Python 3.12.3, Docker 29.6.2, and Compose 5.3.1.
  Branch-level Linux/Docker verification is the next deployment check.
- No live market-data process, actual order, credential use, authorization, or
  deployment was added. Next action: verify this boundary on Claw, then build
  the credential-free two-venue shadow selector and lifecycle before any live
  SDK transport is considered.

Обновлено: 2026-07-25
Рабочая ветка: `stage-a-falsifier`
HEAD до создания этого документа: `e2e9fa2`
Статус: **Stage A не запущен; live execution не разрешён**

## 1. Коротко: где проект находится на самом деле

Это пока не торговый MVP и не готовый пятидневный эксперимент.

Фактически готовы:

- safety-first фундамент Stage 0;
- зафиксированная спецификация пятидневного Stage A;
- детальный план из 10 задач;
- Task 1: публичная конфигурация, модель инструментов и capital gate;
- неактивный GET-only workflow n8n для будущего контроля Stage A;
- валидаторы, запрещающие превратить этот workflow в торговый контур.

Фактически отсутствуют:

- сборщики публичного L2 Hyperliquid и Lighter;
- реконструкция книг и контроль sequence gaps;
- PostgreSQL-схема evidence для Stage A;
- расчёт общего количества, executable VWAP и economics;
- delayed/stress lifecycle и статистика;
- Variational observer;
- Stage A runtime и четыре из пяти внутренних GET API;
- `/v1/business/operator-revenue`;
- детерминированный итоговый отчёт;
- warm-up и пятидневный clock gate;
- любое подтверждение положительной доходности или операторской выручки.

Текущий честный verdict: **исследовательская гипотеза не доказана, операторская
экономика не определена, переход к live запрещён**.

## 2. Цель проекта

Проверить на реальных публичных данных, существует ли между Hyperliquid и
Lighter воспроизводимое расхождение цен, которое:

1. сохраняется после executable depth, округлений, venue minimums, entry и
   exit costs;
2. переживает измеренную задержку и консервативный stress;
3. укладывается в заданный капитал;
4. не зависит от stale/misaligned books, maker fills, forecast funding или
   выдуманной ликвидности;
5. может дать измеримую операторскую выручку, а не только красивую trader-side
   метрику.

Stage A — это пятидневный credential-free falsification experiment. После
60-минутного warm-up должны пройти пять полных UTC data days. Допустимы только
два итоговых решения:

- `KILL` — гипотеза или экономика провалена;
- `EXTEND` — данных недостаточно, но заранее заданные критерии продления
  выполнены.

Stage A **никогда не выдаёт `GO`**, не разрешает live trading и не является
релизом Telegram Mini App.

## 3. Зафиксированный scope

### Основные площадки

- Hyperliquid — основной публичный L2.
- Lighter — основной публичный L2.
- Variational — только редкий read-only reference witness:
  раз в 60 секунд, с максимальной допустимой свежестью 600 секунд.

Variational не является третьей исполняемой ногой. Его данные запрещено
включать в executable VWAP, fill simulation или PnL.

### Инструменты

В allowlist находятся только:

- `PUMP` — кандидат с микроценой;
- `DOGE` — legacy control из старого Hyperliquid-бота.

Для обоих инструментов заведены provisional mappings на Hyperliquid и Lighter.
Все `evidence_hash` пустые. Поэтому `AdmitLifecycle` обязан отклонять каждый
lifecycle с причинами:

- `INSTRUMENT_MAPPING_UNVERIFIED`;
- `CONTRACT_EQUIVALENCE_UNVERIFIED`.

Совпадение тикера не доказывает совпадение контракта, multiplier, payoff,
oracle, settlement или единиц измерения.

### Капитал и исследовательские профили

- целевой суммарный капитал: `$10`;
- условное распределение: `$5` на каждую основную площадку;
- исследовательские notional: `$10`, `$25`, `$50` на одну ногу;
- leverage в текущей проверке: `2x`, без автоматического повышения.

`$10` на ногу при `$5` collateral и `2x` использует всю venue allocation ещё
до fees и reserve. Это `ZERO_MARGIN_HEADROOM`, а не рабочий профиль.
`$25/$50` при тех же условиях — только stress diagnostics и
`CAPITAL_NOTIONAL_UNSUPPORTED`.

Ранее упомянутые фактические балансы пользователя на биржах не являются
бюджетом проекта, разрешением на торговлю или доказательством исполнимости.

### Жёсткие non-goals Stage A

- private API и account streams;
- API keys, signing, wallets и mnemonics;
- создание, изменение или отмена ордеров;
- live mode;
- Telegram Mini App;
- billing, referrals и deposits;
- multi-tenancy и внешнее onboarding;
- RFQ;
- maker/queue assumptions;
- свечи как замена executable L2 evidence.

## 4. Архитектурная граница

```mermaid
flowchart LR
    HL["Hyperliquid public L2"] --> GO["Детерминированный Go falsifier"]
    LI["Lighter public L2"] --> GO
    VA["Variational read-only observer"] -. "reference only" .-> GO
    GO --> PG["PostgreSQL evidence store"]
    PG --> API["GET-only operator API"]
    API --> N8N["n8n control plane, inactive"]
    N8N --> GATE["Fail-closed status/revenue gate"]
```

Только Go falsifier имеет право:

- собирать и нормализовать market data;
- реконструировать книги;
- формировать immutable evidence;
- считать economics;
- принимать `KILL`/`EXTEND`;
- публиковать внутренний read-only API.

n8n не имеет права:

- читать биржевые WebSocket напрямую;
- реконструировать L2;
- считать economics;
- писать evidence;
- хранить venue credentials;
- вызывать private endpoints;
- подписывать или отправлять ордера.

## 5. Репозиторий и рабочая среда

### Локальные пути

- основной checkout:
  `C:\Users\Dmitry\Documents\Codex\2026-07-20\new-chat\work\multi-exchange-engine`
- изолированный worktree:
  `C:\Users\Dmitry\Documents\Codex\2026-07-20\new-chat\work\multi-exchange-engine\.worktrees\stage-a-falsifier`
- текущая ветка: `stage-a-falsifier`;
- integration branch: `main` на `668ce8a`;
- private GitHub remote:
  `https://github.com/Dimkox/multi-exchange-engine`;
- `main` и `stage-a-falsifier` отслеживают соответствующие ветки `origin`;
- draft PR: `https://github.com/Dimkox/multi-exchange-engine/pull/1`.

### Claw

- hostname: `claw`;
- SSH user: `pall`;
- LAN: `[redacted private IP]`;
- Tailscale IPv4: `100.119.249.65`;
- MagicDNS: `claw.taild9f611.ts.net`;
- live application area: `/home/operator/app-stack`;
- временные Stage A материалы использовались ниже
  `/home/operator/stage-a-falsifier-dev`.

Проверенные ранее версии:

- Docker Engine `29.6.2`;
- Docker Compose `5.3.1`;
- `x86_64`;
- n8n `2.31.3`.

### Сетевой контракт Claw

Контейнеры проекта не должны долбиться в прямой Internet egress.

Они обязаны:

- read-only переиспользовать существующий proxy/network contract из
  `/home/operator/app-stack`;
- fail closed, если этот контракт отсутствует;
- не менять `app-stack`, его контейнеры или dirty `glider.conf`;
- не копировать credentials из `app-stack` в этот репозиторий.

`--network none` применялся для детерминированной сборки и тестов, которым сеть
не нужна. Runtime collectors в будущем должны использовать утверждённый
app-stack proxy contract, а не прямой выход.

## 6. Исторический статус старого Stage A плана

Эта таблица относится к прежней нумерации Stage A и не описывает задачи
актуального A2 raw-capture плана выше.

| Этап | Состояние | Фактический результат |
|---|---|---|
| Stage 0 foundation | Готов | Fixed-point, shadow-only config, safety interfaces, reducer/reconciliation, ownership, risk, HTTP skeleton, migration, Docker/CI |
| Five-day spec | Готов | Scope, gates, persistence, API boundary, `KILL/EXTEND` зафиксированы |
| Implementation plan | Готов | 10 TDD-задач, Task 1–10 |
| Task 1 | Готов | Public config, manifest, lifecycle admission и capital gate |
| Task 2 | Не начат | Нет deterministic book reconstruction и quality gates |
| Task 3 | Не начат | Нет Stage A evidence schema/replay |
| Task 4 | Не начат | Нет Hyperliquid public collector |
| Task 5 | Не начат | Нет Lighter public collector |
| Task 6 | Не начат | Нет common quantity/VWAP/paired evaluation |
| Task 7 | Не начат | Нет delayed lifecycle/stress/statistics |
| Task 8 | Не начат | Нет Variational observer |
| Task 9 | Частично | n8n contract есть; Go runtime и API отсутствуют |
| Task 10 | Не начат | Нет report, warm-up и five-day start gate |
| n8n import | Готов, inactive | Workflow импортирован и экспортом проверен |
| Live execution | Запрещён | Нет реализации и нет авторизации |

## 7. Что было изменено

Stage A changeset от `a173359^` до `e2e9fa2`:

- 16 tracked files;
- 2,650 добавленных строк;
- 9 удалённых строк;
- 14 последовательных коммитов 2026-07-21.

### Спецификация и план

#### `docs/five-day-stage-a-spec.md`

Создана binding specification:

- пятидневное окно и 60-минутный warm-up;
- только `KILL`/`EXTEND`;
- PUMP/DOGE instrument gate;
- public feed semantics;
- clock/data-quality gates;
- common quantity и VWAP rule;
- taker-only lifecycle;
- evidence/statistical gates;
- persistence и API boundary;
- CI proof of no execution;
- future Sybil/bot-farm threat model.

#### `docs/superpowers/plans/2026-07-21-five-day-stage-a.md`

Создан пошаговый TDD-план из 10 задач:

1. config/model/capital;
2. book reconstruction/quality;
3. PostgreSQL evidence/replay;
4. Hyperliquid collector;
5. Lighter collector;
6. common quantity/VWAP;
7. lifecycle/stress/statistics;
8. Variational observer;
9. runtime/GET API/negative CI;
10. report/warm-up/five-day gate.

План остаётся ориентиром, но порядок Task 2+ заблокирован незавершённым
operator-revenue contract.

### Task 1: код и конфигурация

#### `config/stage-a.env.example`

Добавлен публичный конфигурационный контракт:

- public WebSocket/HTTP URLs;
- manifest path;
- raw/evidence retention;
- venue age, skew и clock-error limits.

Credentials в контракт не входят.

#### `config/stage-a-instruments.json`

Добавлены ровно четыре provisional mapping:

- Hyperliquid PUMP, market `200`;
- Lighter PUMP, market `45`;
- Hyperliquid DOGE, market `12`;
- Lighter DOGE, market `3`.

Зафиксированы quote/base units, multiplier, tick/lot sizes и minimums.
`evidence_hash` намеренно пустой, чтобы lifecycle admission оставался закрыт.

#### `internal/stagea/model/reasons.go`

Добавлены стабильные reason codes для:

- contract/mapping failures;
- missing/stale/invalid books;
- skew и sequence gaps;
- depth/quantity/minimum failures;
- capital/headroom failures;
- fee/economics/lifecycle failures.

#### `internal/stagea/model/types.go`

Добавлены структуры Stage A:

- venue/contract/instrument;
- research profile;
- run;
- evaluation sample;
- lifecycle evidence;
- reference sample;
- stage decision;
- admission result.

`AdmitLifecycle` fail closed проверяет verified mapping и непустой evidence
hash.

#### `internal/stagea/config/config.go`

Добавлен строгий loader:

- публичные defaults;
- allowlist `STAGE_A_*`;
- запрет credential-like environment variables;
- positive integer validation;
- JSON manifest с `DisallowUnknownFields`;
- ошибка на пустом manifest.

#### `internal/stagea/config/config_test.go`

Покрыты:

- public contract и defaults;
- запрет credentials;
- запрет любого неизвестного `STAGE_A_*`, включая пустое значение;
- точный набор PUMP/DOGE × Hyperliquid/Lighter;
- блокировка lifecycle при пустом evidence.

#### `internal/stagea/feasibility/capital.go`

Добавлена fixed-point проверка:

- положительных capital/leverage/notional;
- достаточности total capital для двух venue allocations;
- запрета отрицательных fees/reserve;
- required margin;
- fee/stress-adjusted headroom;
- отдельного `ZERO_MARGIN_HEADROOM`;
- `CAPITAL_NOTIONAL_UNSUPPORTED`.

#### `internal/stagea/feasibility/capital_test.go`

Покрыты:

- `$10` без запаса;
- `$25/$50` при `2x`;
- запрет неявного увеличения leverage;
- недостаточный total capital;
- отрицательные costs/reserve.

### n8n control plane

#### `deploy/n8n/stage-a-orchestrator.workflow.json`

Создан и импортирован workflow:

- id: `stageAOrchestrator01`;
- name: `Stage A HL+Lighter - ORCHESTRATOR (NO EXECUTION)`;
- `active=false`;
- 9 allowlisted nodes;
- 0 credentials;
- manual trigger;
- five-minute trigger;
- пять внутренних GET;
- финальный fail-closed Code gate.

Внутренние routes:

- `/healthz`;
- `/readyz`;
- `/v1/experiment/status`;
- `/v1/ops/data-quality`;
- `/v1/business/operator-revenue`.

Последний endpoint ещё не реализован. Поэтому workflow и должен оставаться
неактивным и непроходимым.

#### `scripts/validate-stage-a-n8n.ps1`

Валидатор отклоняет:

- активный workflow;
- credentials;
- любой node type вне allowlist;
- не ровно 9 nodes;
- неверный schedule;
- external URLs;
- HTTP method кроме GET;
- отсутствующие routes/connections;
- execution-related строки;
- неполный fail-closed gate.

#### `scripts/test-validate-stage-a-n8n-mutations.ps1`

Добавлены positive control и mutation tests. Проверяется, что:

- исходный workflow принимается;
- side-effect node отклоняется;
- comment-only fake gate отклоняется;
- seven-minute schedule отклоняется.

#### `docs/n8n-stage-a.md`

Зафиксированы authority boundary, routes, fail-closed contract и команда
валидации.

### Continuity и Git

#### `.gitignore`

Добавлены ignore для isolated worktrees и локальных Serena metadata.

#### `docs/agent-handoff.md`

В процессе работы обновлялся краткий continuity log. После появления этого
файла канонический handoff находится в корне: `handoff.md`.

## 8. Проверки, которые уже проходили

### Stage 0

Зафиксированное evidence:

- `gofmt`, `go vet`, unit tests, coverage, binary build — pass;
- Linux `go test -race ./...` на Claw — pass;
- actionlint — pass;
- Hadolint — pass, 0 findings;
- Checkov Dockerfile — 92 checks, 0 failures;
- Docker verify и production build — pass;
- hardened runtime smoke:
  read-only root, dropped capabilities, no-new-privileges, no network — pass;
- PostgreSQL migration up/down — pass.

### Task 1

TDD выполнялся как RED → GREEN → adversarial review → regression RED/GREEN.

Итоговые команды на Claw в cached verifier с `--network none`:

```text
gofmt -l .
go vet ./...
go test -cover ./...
```

Итог: exit `0`, reviewer не оставил Critical/Important/Minor findings.

### n8n

Проверены:

- статический workflow validator;
- positive control;
- три запрещённые мутации;
- импорт в n8n `2.31.3`;
- обратный export;
- `active=false`;
- 9 nodes;
- 0 credentials.

Старый workflow `Hyperliquid DOGE Grid - LIVE` не изменялся и не
активировался.

## 9. Что пробовали и что не сработало

### 9.1. Локальный Go на Windows

В исходной Windows-среде Go отсутствовал.

Первая попытка скачать portable Go через PowerShell собрала некорректный
слишком длинный URL и получила HTTP `414`. После выбора точного архива
Go `1.26.5` был скачан и использован, но пользователь прямо указал, что
локальный Go здесь не нужен.

Результат:

- portable toolchain удалён из worktree;
- временная копия перемещена в
  `C:\Temp\codex-trash-stage-a-go-20260721`;
- рабочая проверка закреплена за Docker/Claw.

### 9.2. Доступ к Claw

Из проверявшей Windows-машины:

- SSH key auth не сработал;
- MagicDNS не разрешился;
- прямой Tailscale IPv4 timed out;
- LAN `[redacted private IP]` сработал.

Tailscale адреса остаются документированными, но перед следующим использованием
их нужно проверить заново. Пароли в Git, handoff и logs не записывать.

### 9.3. RED build Task 1

Первая Docker-проверка с `--network none` упала из-за отсутствующих
`internal/stagea/config`, `model` и `feasibility`.

Это был ожидаемый RED, а не инфраструктурный сбой. После реализации тесты
стали GREEN.

### 9.4. Первая реализация Task 1 была недостаточно fail-closed

Независимый review нашёл четыре реальные ошибки:

1. нулевой margin headroom считался допустимым;
2. неизвестный пустой `STAGE_A_*` проходил;
3. total capital игнорировался;
4. отрицательные fee/reserve принимались.

Все четыре случая сначала закреплены regression tests, затем исправлены.
Именно поэтому конечный код находится на `eb31b39`, а не на первоначальном
`9e41da3`.

### 9.5. Первая версия n8n validator была слабой

Review обнаружил:

1. произвольные node types могли пройти;
2. fail-closed gate проверялся строками недостаточно строго;
3. schedule не валидировался структурно;
4. отсутствовал positive control.

Исправления:

- node allowlist и точное количество nodes;
- точная topology/routes;
- структурная проверка Code gate;
- ровно five-minute schedule;
- positive control;
- mutation tests.

### 9.6. Ошибка в имени mutation script

Сначала была запущена несуществующая команда
`test-validate-stage-a-n8n.ps1`, а последующая команда скрыла её exit status.

Исправлено:

- используется `test-validate-stage-a-n8n-mutations.ps1`;
- exit codes проверяются явно;
- финальный прогон прошёл.

### 9.7. Прямой Internet egress контейнеров

Подход с прямым выходом каждого контейнера в Интернет отвергнут владельцем.
Правильный контракт — существующий `/home/operator/app-stack` proxy/network,
read-only и fail-closed.

Не пытаться «починить сеть» изменением dirty `glider.conf`: это чужая live
зона и отдельный blast radius.

### 9.8. Переиспользование старого Hyperliquid-бота целиком

Старый бот полезен только как источник:

- fill identity/deduplication;
- watermarks;
- causal metadata;
- deterministic client order IDs;
- exact-order ownership;
- unknown-outcome reconciliation;
- restart и cancel/fill race scenarios.

Не переносить:

- Python live monolith;
- DOGE grid strategy/constants;
- embedded SQL;
- `float` на денежных границах;
- broad cancel;
- candle-touch replay;
- n8n/cron как trading или market-data plane.

Старый бот не является доказательством expectancy новой системы.

### 9.9. Поиск «монеты с большим числом нулей»

Низкая номинальная цена не создаёт edge и не уменьшает экономически значимый
minimum notional. `LILPEPE` не был найден как точный общий официальный контракт
на Hyperliquid, Lighter и Variational. PUMP был выбран лишь как provisional
micro-price candidate, DOGE — как control.

До contract/oracle equivalence оба остаются непригодными для lifecycle.

## 10. Главные блокеры и риски

### Blocker 1 — операторская комиссия утверждена, но ещё не реализована

Владелец выбрал одновременно:

1. venue builder/referral cash;
2. собственную turnover fee.

Решение от 2026-07-25:

- `own_fee_bps`: `10`;
- turnover basis: каждый подтверждённый simulated fill на entry и exit обеих
  ног;
- collection mechanism Stage A: `modeled_only`, без списания денег;
- payer: будущий end user;
- unfilled/rejected volume не тарифицируется;
- venue-program revenue учитывается только по cash evidence, иначе `0`;
- infrastructure cost: фактически распределённый USD cost;
- gate: минимум `$0.50` net operator revenue на `$1,000` evidenced turnover.

Утверждённый дизайн:
`docs/superpowers/specs/2026-07-25-stage-a-operator-revenue-design.md`.
Реализация и endpoint пока отсутствуют, поэтому блокер снят на уровне product
decision, но не на уровне кода.

Историческая проверка официальных условий на 2026-07-21 показала:

- Hyperliquid builder fee требует отдельного согласия пользователя;
- perp builder fee ограничен 10 bps;
- builder account требует не менее `$100` account value;
- referral code требовал `$10,000` предыдущего volume;
- Lighter Standard maker/taker fees были нулевыми;
- для Lighter не был найден опубликованный гарантированный cash referral rate;
- points нельзя считать cash revenue.

Эти внешние условия изменчивы и должны быть перепроверены перед реализацией.

Для масштаба: lifecycle с `$10` на одну ногу имеет около `$40` суммарного
entry+exit turnover по двум ногам. Тогда gross owner fee равна:

| Fee | Gross revenue на lifecycle |
|---|---:|
| 1 bp | `$0.004` |
| 5 bps | `$0.020` |
| 10 bps | `$0.040` |

Это до infrastructure, failed lifecycle, refunds, acquisition и abuse. Без
огромного валидного turnover модель почти наверняка не даёт значимой выручки.

### Blocker 2 — operator revenue API отсутствует

`/v1/business/operator-revenue` существует только как n8n contract. В Go его
нет. Пока endpoint отсутствует и `contract_complete` не может быть истинным,
n8n workflow обязан fail closed.

### Blocker 3 — instrument equivalence не доказана

У всех четырёх mappings пустой `evidence_hash`. Нельзя запускать lifecycle,
пока не сохранены authoritative contract/multiplier/oracle/settlement evidence.

### Blocker 4 — основной evidence engine отсутствует

Task 2–8 и большая часть Task 9–10 не реализованы. Сейчас нечему собирать пять
дней данных, считать VWAP, закрывать lifecycle или формировать решение.

### Blocker 5 — `$10` capital profile уже на границе непригодности

При `$5` на venue и `2x` базовый `$10` notional имеет нулевой запас.
Даже минимальные fees, slippage, reserve или price movement делают профиль
неподдерживаемым.

### Risk 6 — Stage A ещё не интегрирован

Private remote и draft PR созданы 2026-07-25. Ветка `stage-a-falsifier`
сохранена на GitHub, но изменения ещё не прошли реализацию operator-revenue
checkpoint, финальный review и merge в `main`.

## 11. Следующий шаг

### Сначала закончить operator-revenue checkpoint

1. Выполнить TDD implementation plan:
   `docs/superpowers/plans/2026-07-25-stage-a-operator-revenue.md`.
2. Реализовать versioned contract, fixed-point revenue domain, отдельный
   Stage A HTTP slice и минимальный `cmd/falsifier`.
3. Проверить exact boundary `$0.50/$1,000`, incomplete contract, zero turnover,
   unknown JSON fields и запрет mutating routes.
4. Обновить source n8n gate: одного `contract_complete:true` недостаточно,
   требуется `gate_passed:true`.
5. Провести независимый review и обновить этот handoff.
6. Оставить Claw n8n `active=false`, не re-import и не деплоить checkpoint.
7. Отдельным следующим коммитом продолжить Task 2:
   deterministic book reconstruction, clock epochs и quality gates.

Не смешивать operator-revenue contract и Task 2 в одном коммите.

## 12. Условия, при которых n8n можно рассматривать для активации

Одного существования workflow недостаточно. До отдельного решения владельца
должны быть истинны все условия:

- Stage A runtime развёрнут;
- все пять GET routes отвечают внутри Docker network;
- `execution_available=false`;
- revenue contract полный и versioned;
- instrument mappings verified;
- collectors и quality gates прошли warm-up;
- workflow validator и mutation tests зелёные;
- экспорт из n8n подтверждает 0 credentials и неизменную topology;
- старый live workflow остаётся выключенным;
- есть отдельная явная авторизация на активацию именно Stage A observer.

Даже после этого активация n8n не разрешает торговлю.

## 13. Команды для продолжения

### Открыть правильный worktree

```powershell
Set-Location 'C:\Users\Dmitry\Documents\Codex\2026-07-20\new-chat\work\multi-exchange-engine\.worktrees\stage-a-falsifier'
git status --short --branch
git log --oneline --decorate -20
Get-Content .\handoff.md
```

### Проверить n8n contract

```powershell
& .\scripts\validate-stage-a-n8n.ps1
& .\scripts\test-validate-stage-a-n8n-mutations.ps1
```

### Полная Go-проверка в подготовленной среде

```text
gofmt -l .
go vet ./...
go test -race -cover ./...
go build -trimpath ./cmd/engine
```

Если локального Go нет, использовать pinned Docker builder/Claw. Не
устанавливать toolchain в репозиторий.

### Docker verification

```text
docker build --target verify -t multi-exchange-engine:verify .
docker build -t multi-exchange-engine:dev .
```

Не передавать secrets как build args. Не запускать private/live adapters:
их не должно существовать в Stage A.

## 14. Secret handling

- В этом worktree `.env` отсутствует.
- `.env` игнорируется Git.
- В других локальных checkout могли ранее находиться venue/Telegram
  credentials; их содержимое не переносить в handoff или commits.
- В документации разрешено указывать только имена переменных и secret
  locations.
- Lighter private keys, read-only token, email, wallet, SSH password и любые
  Telegram/venue tokens считать скомпрометированными, если они когда-либо
  попадали в чат или незашифрованный лог; перед live use их нужно ротировать.
- Stage A не должен читать ни один из этих секретов.

## 15. Карта ключевых коммитов

| Commit | Значение |
|---|---|
| `a173359` | Five-day Stage A specification |
| `cdee1ec` | Implementation plan |
| `668ce8a` | Isolated worktree ignore |
| `6aa7848` | Claw proxy/network invariant |
| `8de7b53` | Task 1 RED tests |
| `9e41da3` | Initial Task 1 implementation |
| `2e895df` | Regression tests после review |
| `eb31b39` | Fail-closed Task 1 fixes |
| `f7a405c` | Task 1/revenue blocker handoff |
| `7169cdd` | Dual revenue model selection |
| `1f07c2c` | Initial n8n workflow/validator/docs |
| `acc6749` | Hardened n8n validation |
| `fc1aee2` | n8n positive control |
| `e2e9fa2` | Verified inactive n8n import |

## 16. Definition of done для следующего checkpoint

Следующий checkpoint считается завершённым только если:

- owner fee contract зафиксирован без неоднозначностей;
- spec и plan согласованы с ним;
- `/v1/business/operator-revenue` реализован fail closed;
- fixed-point unit tests и negative tests проходят;
- n8n validator/mutation suite проходит;
- workflow всё ещё inactive и без credentials;
- `gofmt`, `go vet`, `go test -race -cover ./...` зелёные;
- изменения оформлены одним coherent commit;
- этот handoff обновлён в том же commit.

## 17. Главная передача следующему агенту

Не начинай с написания WebSocket collectors и не активируй n8n.

Сначала добей у владельца точный operator fee contract. Без него проект
оптимизирует trader-side картинку, хотя заявленный бизнес-критерий — комиссия
оператора. Это будет не прогресс, а дорогое избегание главного вопроса.

После фиксации контракта реализуй revenue endpoint отдельным TDD checkpoint,
затем переходи к Task 2. Live trading, private credentials и изменение
`/home/operator/app-stack` не авторизованы.

## 18. Task 12: A2 packaging and CI checkpoint

Task 12 adds `Dockerfile.a2`, without changing the root Go `Dockerfile`. The
new Python image installs only the pinned `requirements-a2.txt` dependency set
to `/install`; its production stage copies only that directory, the
`multi_exchange_engine` package, and migrations, and runs as UID/GID 10001 on
port 8081. It has a urllib `/health` probe and starts in exec form with
`python -m multi_exchange_engine.a2`.

The binding Task 12 security-base decision replaces the retired Bookworm image
in all A2 stages with
`python:3.12.13-alpine3.23@sha256:601d3d3797e90e2534782e69c85fafb7971b43f24c7b1b079b7e48dd435e458d`.
The prior base failed the pinned Trivy HIGH/CRITICAL gate; the exact Alpine
digest had zero HIGH/CRITICAL findings in the same scan. No `--ignore-unfixed`
waiver, registry publication, or production-boundary expansion is authorized.

The `a2` CI matrix uses pinned PostgreSQL 16.11 and 17.7 and runs PostgreSQL,
unit, replay, fault, and boundary gates before verify/production builds, a
pinned Syft CycloneDX SBOM, and a pinned Trivy HIGH/CRITICAL gate. Neither
workflow publishes an image. `build-a2-on-claw.yml` is manual-only on
`[self-hosted, claw]`; it creates the local `mee-a2:${{ github.sha }}` and
`mee-a2:candidate` tags but never runs the A2 image. Its scanner binaries are
copied from stopped pinned scanner containers, avoiding `docker run`.

Windows local Docker was not available during authoring, so no Docker build,
SBOM, or Trivy success is claimed locally. See `docs/a2-deployment.md` for
the Dockerfile validation loop and the exact local verification commands.

### Review follow-up: verify context and production registry blocker

Claw verify builds proved the deployment-contract discovery needs explicit
copies of `Dockerfile.a2`, `.dockerignore`, `requirements-a2.txt`, the two A2
workflow files, and `config/a2-reviewed-perpetual-mappings.json`. They are
verify-only inputs; the production stage remains limited to `/install`,
`multi_exchange_engine`, and migrations.

This leaves a confirmed Task 13/14 runtime packaging blocker: runtime resolves
the reviewed mapping registry beneath its project root, but Task 12 forbids
copying `config/` into production. Do not relax that production boundary. The
deployment integration must supply the immutable reviewed registry as a
read-only runtime input and prove it with a production smoke test before an A2
container can be started.

### Final Task 12 Claw validation

Exact reviewed commit `c5b2b0f71b3169f097b017696fafe595634aa48c` was
validated in isolated path
`/home/operator/codex-validation/mee-a2-task12-c5b2b0f-20260728`; `/home/operator/app-stack`
was untouched and the A2 container was never started. `Dockerfile.a2` verify
and production builds both exited 0. Pinned Syft generated a 311328-byte
CycloneDX report; pinned Trivy 0.72.0 strict HIGH/CRITICAL exited 0 with zero
findings and a 109710-byte JSON report. The image measured 26458760 bytes;
inspection confirmed USER `10001:10001`, correct exec CMD/urllib healthcheck,
and OCI revision `c5b2b0f`. Reports were downloaded under ignored
`.superpowers/sdd/task12-claw-final/`.

Reviewer Minor remains only on FROM-line parsing: retain every pinned FROM on
one physical line. This does not relax the explicit Task 13/14 mapping-registry
read-only-input blocker above.

### Task 12 follow-up: isolate self-hosted Python gates

Merged-main run `31317718016` failed before the A2 gates because the Claw
runner's shared `setup-python` toolcache contained unrelated, incomplete
Paramiko and LangChain installations. The manual Claw workflow now creates a
fresh `${{ github.workspace }}/.venv` in each job and invokes that venv's
Python for dependency checks, PostgreSQL/unit/replay/fault/boundary gates, and
the registry-mount smoke. Every multiline Python gate uses
`set -euo pipefail`; the hosted `ci.yml` is unchanged.

The regression contract was observed RED before the workflow change and GREEN
after it. Local evidence: deployment contract 9/9, A2 suite 216 tests OK with
19 PostgreSQL-dependent skips when `A2_TEST_DATABASE_URL` is absent,
`A2_BOUNDARY_OK`, and actionlint PASS. Local Go and Docker execution were not
available and are not claimed; the self-hosted workflow remains the binding
PostgreSQL/Docker/scanner evidence gate. No image was started or promoted and
no Claw Compose, n8n, trading, or private surface was changed.
