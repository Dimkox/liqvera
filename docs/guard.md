# LiqveraGuard: автоматическая защита Trove (дизайн A2)

Статус: только Mezo Testnet (chain 31611). Контракт не задеплоен. Аудита нет.
Этот документ написан в стиле ASD-STE100: короткие предложения, одно действие в шаге.

## 1. Назначение

LiqveraGuard защищает Trove от ликвидации. Пользователь заранее подписывает одну операцию Mezo.
Когда ICR падает до порога, keeper вызывает `protect()`. Guard выполняет подписанную операцию.

Модель взята из DeFi Saver Liquity Repay и Summer.fi Stop-Loss: триггер по коэффициенту, исполняет бот.
Функция `checker()` повторяет интерфейс Gelato/Chainlink. Код написан с нуля. Код из этих проектов не копировали.

## 2. Как это работает

1. Пользователь вносит MUSD (`depositMUSD`) или BTC (`depositBTC`) в эскроу Guard.
2. Пользователь подписывает EIP-712 сообщение Mezo `RepayMUSD` или `AddColl`.
   - Домен: `BorrowerOperationsSignatures`, версия `1`, chainId 31611, контракт `0xD757e3646AF370b15f32EB557F0F8380Df7D639e`.
   - Подпись связывает `amount`, `borrower`, `nonce`, `deadline`.
3. Пользователь вызывает `arm(action, triggerICR, amount, keeperReward, deadline, signature)`.
   - Guard проверяет подпись on-chain по `getNonce(msg.sender)`.
   - Guard проверяет: триггер в диапазоне (MCR, 1000%], срок подписи не больше 30 дней, Trove активен, эскроу хватает, для repay остаётся `minNetDebt`.
4. Keeper опрашивает `checker(borrower)` каждые 30 секунд.
5. Когда `canExec == true`, keeper вызывает `protect(borrower, upperHint, lowerHint)`.
6. Guard удаляет политику, списывает эскроу, вызывает Mezo, проверяет рост ICR, платит награду keeper.

Одна подпись даёт одно исполнение. После `protect()` пользователь должен снова вызвать `arm()`.

## 3. Ответы на открытые вопросы Q1–Q5

Все ответы проверены fork-тестом `contracts/guard/test/fork/GuardFork.t.sol` на RPC `https://rpc.test.mezo.org`.

| Вопрос | Ответ | Тест |
|---|---|---|
| Q1. Как читать nonce? | Маппинг `nonces` приватный. `nonces(address)` откатывается. Используйте `getNonce(address)`. Nonce последовательный, начинается с 0. | `test_Q1_NonceGetter` |
| Q2. Нужен ли approve MUSD? | Нет. BorrowerOperations сжигает MUSD у `_caller` (Guard) напрямую. Allowance остаётся 0. | `test_Q2_RepayPath_NoApproveNeeded` |
| Q3. Какой код задеплоен? | Прокси `0xD757…` — TransparentUpgradeableProxy. Реализация `0xEec635aB00463A4a803DE38C9d858A0FE3bdc235` верифицирована в Blockscout. Исходник совпадает с `BorrowerOperationsSignatures.sol` коммита `da7888a`. `BorrowerOperations.borrowerOperationsSignaturesAddress()` возвращает этот прокси. Codehash реализации: `0x9714ca105dccb830037cd8821974832a5e2a1e7822b2369654849617c6e73900`. | `test_Q3_DeployedImplementationAndDomain` |
| Q4. Есть ли Gelato или Chainlink Automation на Mezo? | Нет. Gelato Web3 Functions закрыты 31.03.2026, Mezo не поддерживали. Chainlink Automation не поддерживает Mezo. Нужен свой keeper. | — |
| Q5. Порядок полей `getEntireDebtAndColl`? | `(coll, principal, interest, pendingCollateral, pendingPrincipal, pendingInterest)`. | `test_Q5_GetEntireDebtAndCollOrder` |

## 4. Риски и меры

| Риск | Мера |
|---|---|
| Устаревший nonce. Любая другая подписанная операция пользователя увеличивает nonce. | `checker()` возвращает `StaleNonce`. `protect()` не выполняется. Пользователь должен снова вызвать `arm()`. Эскроу не меняется. Тест `test_FrontRun_StaleNonce`. |
| Front-running подписи. Подпись видна в calldata `arm()`. | Mezo проверяет `msg.sender`-независимую подпись, но списывает MUSD/BTC у вызывающего. Чужой вызов только погасит долг пользователя за свой счёт и сделает nonce устаревшим. Средства эскроу не теряются. |
| `minNetDebt` = 1800 MUSD. | `arm()` и `checker()` проверяют: `(debt − 200 газовой компенсации) − amount ≥ 1800`. Иначе статус `BelowMinNetDebt`. Тест `test_MinNetDebt_Enforced`. |
| Recovery Mode. | В Recovery Mode Mezo запрещает только вывод залога и рост долга. Repay и addColl разрешены. Ликвидация в Mezo только ниже MCR в обоих режимах. Тест `test_RecoveryMode_RepayStillWorks`. |
| MCR 110%. | Триггер должен быть выше MCR. `checker()` возвращает `StillBelowMCR`, если ICR после операции останется ниже MCR (Mezo откатит такой repay в Normal Mode). |
| Только EOA. | Подпись проверяется через `ecrecover`. Смарт-кошельки (EIP-1271) не поддерживаются. |
| Прокси Mezo обновляемый. | Mezo может изменить реализацию. Перед деплоем и периодически проверяйте codehash реализации (см. Q3). |
| Оракул в fork-тестах. | PriceFeed читает прекомпайл `0x7b7c…0015`. Локальный fork его не исполняет. Fork-тест берёт цену через `eth_call` к узлу и фиксирует её `vm.mockCall`. |
| Нет аудита. | Только testnet. Перед mainnet нужен аудит и Slither. |

## 5. Отклонение от плана

План предполагал одну валюту награды. Реализация платит награду keeper в валюте операции: MUSD для `RepayMUSD`, BTC для `AddColl`. Причина: эскроу пользователя может содержать только один актив.

## 6. Keeper

Код: `services/guard-keeper`.

1. Читает события `Armed`, `Disarmed`, `Protected` и строит множество активных политик.
2. Каждые 30 секунд вызывает `status(borrower)`.
3. Для статуса `Ready` считает hints: `HintHelpers.getApproxHint` и `SortedTroves.findInsertPosition` по NICR после операции (`coll·1e20/principal`).
4. Симулирует `protect()`. Отправляет транзакцию только после успешной симуляции.
5. Пишет одну JSON-строку на событие.

Keeper хранит только свой ключ (`KEEPER_PRIVATE_KEY` из env). Ключи пользователей keeper не хранит. Режим `DRY_RUN=1` не отправляет транзакции.

## 7. Тесты

```sh
cd contracts/guard
forge test                                              # unit, fuzz, invariant
MEZO_TESTNET_RPC=https://rpc.test.mezo.org forge test   # плюс fork-тесты
cd ../../services/guard-keeper && npm ci && npm test
```

## 8. Что сделать до деплоя в testnet

1. Получить одобрение владельца на деплой.
2. Запустить Slither. Исправить находки.
3. Выполнить `script/Deploy.s.sol` с `--broadcast --verify`. Проверить контракт в Blockscout.
4. Создать и пополнить отдельный кошелёк keeper.
5. Добавить панель Guard во frontend (deposit, подпись, arm, disarm, статус).
6. Выполнить минимум 3 реальных `protect()` в testnet и записать их в журнал транзакций.
