# Credential-Free Public Adapter Boundaries Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provide dedicated Hyperliquid and Lighter public market-data adapters
that need no account, key, signer, nonce, or trading transport and expose no
private execution methods.

**Architecture:** Extract discovery, public wire parsing, and order-book state
into dependency-isolated `public_hyperliquid.py` and `public_lighter.py`
modules. Keep the existing execution adapters backward compatible by importing
and subclassing those public adapters, then adding only private dependencies
and methods. Add the existing Python suite as a required GitHub Actions gate.
This checkpoint changes no wire schema and adds no live network client.

**Tech Stack:** Python 3.12+, `asyncio`, structural runtime protocols,
`unittest`, exact `Decimal`.

## Global Constraints

- Public adapters accept only public read transports, reviewed mapping
  providers, and receive clocks.
- Public adapters expose `list_markets` and `order_book`; Lighter additionally
  exposes its public order-book message reducer.
- Public adapters must satisfy `PublicMarketDataAdapter` and must not satisfy
  `ExecutionAdapter`.
- Importing either public adapter module must not import
  `multi_exchange_engine.domain.execution` or any signer, nonce, send, account,
  order, fill, or cancellation type.
- Existing `HyperliquidAdapter` and `LighterAdapter` constructor behavior and
  all existing execution tests remain compatible.
- No credential values, account identifiers, signer, nonce coordinator,
  client-order index provider, send transport, or private method may be added
  to a public adapter.
- No HTTP/WebSocket client, exchange mutation, live order, or deployment is
  part of this checkpoint.
- All price and quantity values remain exact `Decimal`; no float boundary.
- Production lines remain at most 88 characters and the full Python suite,
  `compileall`, and `git diff --check` must pass.

---

### Task 1: Split Public and Private Venue Capabilities

**Files:**

- Create: `tests/exchange/test_public_adapter_boundaries.py`
- Create: `multi_exchange_engine/exchange/public_hyperliquid.py`
- Create: `multi_exchange_engine/exchange/public_lighter.py`
- Modify: `multi_exchange_engine/exchange/hyperliquid.py`
- Modify: `multi_exchange_engine/exchange/lighter.py`
- Modify: `multi_exchange_engine/exchange/lighter_normalize.py`
- Modify: `.github/workflows/ci.yml`
- Modify: `handoff.md`
- Modify: `docs/agent-handoff.md`

**Interfaces:**

- Produces:
  `HyperliquidPublicAdapter(*, info_transport, mapping_provider,
  received_timestamp_ms)`.
- Produces:
  `LighterPublicAdapter(*, read_transport, mapping_provider,
  received_timestamp_ms)`.
- Preserves:
  `HyperliquidAdapter(*, account_address, info_transport,
  exchange_transport, mapping_provider, received_timestamp_ms)`.
- Preserves:
  `LighterAdapter(*, account_index, read_transport, sign_transport,
  send_transport, nonce_coordinator, mapping_provider,
  client_index_provider, received_timestamp_ms)`.

- [ ] **Step 1: Write the failing public-boundary tests**

Create `tests/exchange/test_public_adapter_boundaries.py` with self-contained
fixture transports and mapping providers. The tests must:

```python
import unittest
from decimal import Decimal

from mee_contracts.domain.market import InstrumentIdentity
from mee_contracts.exchange import hyperliquid, lighter
from mee_contracts.exchange.contracts import (
    ExecutionAdapter,
    PublicMarketDataAdapter,
)


class QueueTransport:
    def __init__(self, responses):
        self.responses = list(responses)

    async def __call__(self, *request):
        del request
        return self.responses.pop(0)


class HyperliquidMappings:
    def mapping_for(self, symbol, metadata):
        del metadata
        if symbol != "ASSET":
            return None
        return hyperliquid.HyperliquidInstrumentMapping(
            identity=InstrumentIdentity(
                "ASSET", "USDC", "PERPETUAL", "USDC", "LINEAR"
            ),
            contract_multiplier=Decimal("1"),
            min_notional=Decimal("10"),
            equivalence_evidence="reviewed:asset-v1",
        )


class LighterMappings:
    def mapping_for(self, symbol, detail):
        del detail
        if symbol != "ASSET":
            return None
        return lighter.LighterInstrumentMapping(
            identity=InstrumentIdentity(
                "ASSET", "USDC", "PERPETUAL", "USDC", "LINEAR"
            ),
            contract_multiplier=Decimal("1"),
            equivalence_evidence="reviewed:asset-v1",
        )
```

The Hyperliquid test instantiates `HyperliquidPublicAdapter` without an account
or exchange transport, asserts it satisfies `PublicMarketDataAdapter`, asserts
it does not satisfy `ExecutionAdapter`, discovers `ASSET`, and maps one valid
official `l2Book` snapshot.

The Lighter test instantiates `LighterPublicAdapter` without account, signer,
send transport, nonce coordinator, or client index provider, asserts the same
protocol boundary, discovers `ASSET`, applies one
`subscribed/order_book` snapshot on `order_book:45`, and returns the exact
book through `order_book`.

Add an import-isolation test that starts a fresh Python subprocess, imports
only both public modules, and asserts
`"multi_exchange_engine.domain.execution" not in sys.modules`.

- [ ] **Step 2: Run tests and verify the expected RED**

Run:

```powershell
python -m unittest tests.exchange.test_public_adapter_boundaries -v
```

Expected: both tests fail because `HyperliquidPublicAdapter` and
`LighterPublicAdapter` do not exist.

- [ ] **Step 3: Extract the dependency-isolated Hyperliquid public capability**

Create `multi_exchange_engine/exchange/public_hyperliquid.py`. It imports only
standard-library types plus `domain.book` and `domain.market`. Move the
existing public request type, `InfoTransport`, instrument mapping/provider,
known-market record, public parsing helpers, constructor state,
`list_markets`, `order_book`, and `_require_market` into:

```python
class HyperliquidPublicAdapter:
    venue = "HYPERLIQUID"

    def __init__(
        self,
        *,
        info_transport: InfoTransport,
        mapping_provider: HyperliquidMappingProvider,
        received_timestamp_ms: Callable[[], int],
    ) -> None:
        self._info_transport = info_transport
        self._mapping_provider = mapping_provider
        self._received_timestamp_ms = received_timestamp_ms
        self._known_markets: dict[str, _KnownMarket] = {}
```

Keep the current discovery, validation, and snapshot behavior unchanged. In
`multi_exchange_engine/exchange/hyperliquid.py`, import and re-export the
public types required by existing callers, import the shared parsing helpers,
and change the private adapter declaration to:

```python
class HyperliquidAdapter(HyperliquidPublicAdapter):
```

Its constructor must call `super().__init__` with only public dependencies,
then validate/store `account_address`, `exchange_transport`, and owned-order
state. Keep `_require_intent` and every account/order/fill method only on the
private subclass. The public module must not import `domain.execution`.

- [ ] **Step 4: Extract the dependency-isolated Lighter public capability**

Create `multi_exchange_engine/exchange/public_lighter.py`. It imports only
standard-library types plus `domain.book` and `domain.market`. Move the
existing `ReadTransport`, instrument mapping/provider, known-market record,
book reducer, public wire helpers, constructor state, `list_markets`,
`order_book`, `apply_order_book_message`, and `_require_market` into:

```python
class LighterPublicAdapter:
    venue = "LIGHTER"

    def __init__(
        self,
        *,
        read_transport: ReadTransport,
        mapping_provider: LighterMappingProvider,
        received_timestamp_ms: Callable[[], int],
    ) -> None:
        self._read_transport = read_transport
        self._mapping_provider = mapping_provider
        self._received_timestamp_ms = received_timestamp_ms
        self._known: dict[str, _KnownMarket] = {}
        self._books: dict[str, LighterBookReducer] = {}
```

Make `LighterBookReducer.snapshot` use the public venue constant. In
`lighter_normalize.py`, import the shared public parsing helpers and keep only
private account/order/fill normalization. In `lighter.py`, import and re-export
the public types required by existing callers and change the private adapter
declaration to:

```python
class LighterAdapter(LighterPublicAdapter):
```

Its constructor calls `super().__init__` with public dependencies, then
validates/stores account, signing, sending, nonce, client-index, ownership, and
transaction state. Keep `_require_intent`, `_symbol_for`, and every
account/order/fill method only on the private subclass.

- [ ] **Step 5: Add the Python suite to GitHub Actions**

Add a separate `python` job to `.github/workflows/ci.yml` using:

```yaml
  python:
    name: Verify Python reference engine
    runs-on: ubuntu-24.04
    timeout-minutes: 10
    steps:
      - name: Checkout source
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd
        with:
          fetch-depth: 1

      - name: Set up Python
        uses: actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405
        with:
          python-version: "3.12"
          cache: false

      - name: Unit tests
        run: python -B -m unittest discover -s tests -t . -v

      - name: Compile bytecode
        run: python -m compileall -q multi_exchange_engine tests
```

- [ ] **Step 6: Run focused and full verification**

Run:

```powershell
python -m unittest tests.exchange.test_public_adapter_boundaries -v
python -m unittest discover -s tests -v
python -m compileall -q multi_exchange_engine tests
```

Expected: the focused tests pass, then all tests pass without warnings or
errors.

- [ ] **Step 7: Update continuity documents**

Add a dated checkpoint to `handoff.md` and `docs/agent-handoff.md` recording:

- the new credential-free public classes;
- dependency isolation and the Python CI job;
- private adapters remain separate and backward compatible;
- exact test counts and verification commands;
- no network client, key use, trading call, or deployment;
- next action: exact shadow VWAP and data-quality domain.

- [ ] **Step 8: Run repository checks and commit**

Run:

```powershell
$long = Get-ChildItem multi_exchange_engine,tests -Recurse -Filter *.py |
    ForEach-Object {
        $path = $_.FullName
        $line = 0
        Get-Content -LiteralPath $path | ForEach-Object {
            $line++
            if ($_.Length -gt 88) { "$path`:$line" }
        }
    }
if ($long) { $long; exit 1 }
git diff --check
git status --short
```

Stage only the files listed in this task. Commit:

```powershell
git commit -m "refactor: split credential-free public adapters"
```
