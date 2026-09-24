## 3. Reconstructed interaction model

High-confidence portion:

```text
Web terminal / Bot / MCP client
            |
            | HTTPS + Bearer token
            v
    perps-api.vooi.io
            |
            +-- /exchange/*
            +-- /funding-strategies/*
            +-- /transfer/*
            +-- /withdraw/*
            +-- /user-exchange/*
            +-- /mcp
```

The following portion is an architectural inference from the API shape and the official
description of the unified execution layer:

```text
perps-api.vooi.io
        |
        +-- common routing and account layer
        |
        +-- venue-specific adapters / signing workflows
              Hyperliquid
              Lighter
              Aster
              Extended
              Binance
              HIP-3 builders on Hyperliquid
```

There is no public server repository confirming internal class/module names.
The terms `router` and `adapter` therefore describe the observed role here, rather than
asserting a specific server implementation.

## 4. API surface

`data/api-surface-*.csv` contains 77 exact method/path pairs extracted from
the generated SDK at the pinned MM-bot commit. Main groups:

### Market and strategy reads

```text
GET /exchange/markets
GET /exchange/top-volume-symbols-quotes
GET /exchange/quotes
GET /exchange/estimate-slippage
GET /funding-strategies
GET /funding-strategies/funding-rate-history
GET /funding-strategies/spread-chart
GET /time
```

Official examples describe `GET /exchange/markets` as the authoritative list of
available exchange/market combinations. `quotes` and `estimate-slippage` require
Bearer in the generated schema and are not equivalent to a fully public
market-data endpoint.

### Streaming

```text
GET  /exchange/updates-orderbook
POST /exchange/updates-token
GET  /exchange/updates
```

The generated client describes SSE. The separation into a public-looking orderbook stream and
one-time-token updates indicates that the market stream and private account/order
stream must not be mixed within one trust boundary.

### Trading and account mutation

```text
POST   /exchange/orders
DELETE /exchange/orders
POST   /exchange/batch-orders
DELETE /exchange/batch-orders
DELETE /exchange/all-orders
POST   /exchange/leverage
POST   /exchange/margin-mode
```

`DELETE /exchange/all-orders` is described as a Lighter-only broad cancel. It is directly
incompatible with the Multi-Exchange Engine invariant to "cancel only owned,
exactly registered orders."

### Onboarding and wallet signatures

```text
POST /exchange/broker/prepare
POST /exchange/broker/execute
GET  /exchange/broker/approved

POST /user-exchange/{exchange}/register/prepare
POST /user-exchange/{exchange}/register/execute
GET  /user-exchange/{exchange}/register/status
```

A prepare/sign/execute pattern is observed: the API constructs an exchange-specific payload,
the user signs it with a wallet, and the signed data is then sent to the
execute endpoint. This is a strong authority boundary; the research performed no
signing flows.

### Funds movement

```text
GET  /deposit
POST /transfer/prepare
POST /transfer/execute
POST /transfer/arbitrum
POST /withdraw/prepare
POST /withdraw/execute
POST /withdraw/extended/quote
POST /withdraw/extended/execute
```

These endpoints have no place in the current shadow-only or public-data runtime.
Even "prepare" may create a signature/transaction intent and must be treated as a
funds-moving capability.

### MCP

```text
GET    /mcp
POST   /mcp
DELETE /mcp
```

The generated OpenAPI schema does not annotate security consistently everywhere, but
the official MCP README and Ultra setup require a Bearer token. Product documentation
takes precedence over a missing annotation in the generated client.

## 5. Venue abstraction and leaks of venue-specific semantics

VOOI provides a common `/exchange/*` namespace, but the abstraction does not fully erase
venue differences:

- exchange is passed as a string and can be extended without regenerating the client;
- market identity includes `baseSymbol` and `id`;
- Kinetiq and trade.xyz are represented as HIP-3 builder deployments within
  Hyperliquid;
- their symbols have prefixes, such as `km:` and `xyz:`;
- the official MM bot maps a "virtual venue" to
  `{exchange: "hyperliquid", prefix}`;
- for Aster order/leverage, `asset` uses a market `id` such as `BTCUSDT`,
  while other paths use `baseSymbol`;
- two logical legs may share one physical margin account.

Consequence: a state key based only on `exchange` is insufficient. The minimum key
must include venue/exchange, canonical market identity, symbol namespace, and
leg role. An identical ticker must not be assumed to mean an identical
contract.

## 6. Authentication and secret boundary

Observed model:

- the VOOI API token is created in the Ultra console;
- clients send a Bearer header;
- server-side broker identity/fee policy is bound to the API key;
- individual exchange actions require a wallet signature;
- Telegram/LLM/database credentials in the examples are passed through the environment.

The research tools in this directory:

- do not read `.env`;
- do not accept a Bearer token;
- do not send cookies;
- do not connect a wallet;
- remove secret-like query values from observables;
- do not execute downloaded code.

