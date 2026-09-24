# Stage A Operator Revenue Design

Date: 2026-07-25
Status: approved for implementation
Scope: one credential-free, model-only Stage A revenue slice

## Decision

Stage A models an owner turnover fee without collecting money.

The frozen contract is:

- owner fee: `10` basis points;
- rate fraction: `0.001`;
- turnover basis: every evidenced simulated fill on entry and exit for both
  legs;
- payer: future end user;
- charge moment: when a simulated fill becomes immutable lifecycle evidence;
- collection mechanism: `modeled_only`;
- payout currency: USD-denominated fixed-point evidence;
- unfilled or rejected volume: not charged;
- evidenced filled volume: not refunded in the model;
- venue-program revenue: counted only when cash evidence exists, otherwise
  exactly `0`;
- infrastructure cost: actual allocated USD cost, never an implicit zero;
- revenue gate: at least `$0.50` net operator revenue per `$1,000` evidenced
  turnover.

This contract is a falsification assumption, not proof that the fee can legally
or technically be collected. Stage A does not bill users and does not authorize
live execution.

## Why this slice exists now

Operator commission is the owner's primary business criterion. The existing
experiment specification defines trader-side evidence but does not implement a
versioned operator-revenue formula or the endpoint required by the inactive n8n
control plane.

The complete Stage A runtime belongs to Task 9. This slice pulls forward only
the revenue domain, its strict public configuration, and one read-only endpoint.
It does not fake feed, storage, lifecycle, or readiness.

## Rejected approaches

### Add the endpoint to the Stage 0 engine

Rejected because it would mix the legacy foundation runtime with the Stage A
falsifier and make an unready experiment appear operational.

### Implement only the formula and wait until Task 9 for HTTP

Rejected because n8n already has a binding contract for
`/v1/business/operator-revenue`. A separately tested Stage A HTTP slice can
establish that boundary now without claiming the rest of Task 9 is complete.

### Pull all of Task 9 forward

Rejected because collectors, evidence persistence, quality summaries, and
lifecycle read models do not exist yet. Building their API projections now
would create placeholders rather than evidence-backed endpoints.

## Components

### Versioned public contract

Create `config/stage-a-operator-revenue.json`.

The file contains no credentials and uses string decimals:

```json
{
  "contract_version": "stage-a-v1",
  "source": "owner_turnover_fee",
  "rate": "0.001",
  "rate_bps": "10",
  "turnover_basis": "filled_entry_exit_notional_both_legs",
  "payer": "future_end_user",
  "charge_moment": "immutable_simulated_fill_evidence",
  "payout_terms": "model_only_stage_a_no_cash_collection",
  "collection_mechanism": "modeled_only",
  "refund_or_rebate_rules": "unfilled_or_rejected_not_charged_filled_not_refunded",
  "payout_currency": "USD",
  "infrastructure_cost": "actual_allocated_usd",
  "minimum_net_revenue_per_1000_usd": "0.5",
  "venue_program_revenue_treatment": "observed_cash_only_otherwise_zero"
}
```

Add `STAGE_A_OPERATOR_REVENUE_CONTRACT` to the existing Stage A public
environment allowlist. Its default is the path above.

JSON decoding rejects unknown fields and numeric JSON decimals. An unreadable
or malformed file prevents process startup. A syntactically valid but
semantically incomplete contract remains representable and produces
`contract_complete:false`.

### Revenue domain

Create `internal/stagea/revenue`.

It owns:

- strict contract loading;
- semantic completeness validation;
- fixed-point revenue evaluation;
- stable reason codes;
- the read model consumed by HTTP.

It imports `internal/fixed` and Stage A model types only. It must not import
HTTP, persistence, collectors, exchange adapters, execution, wallets, or
credentials.

The calculation is:

```text
owner_fee_usd =
    evidenced_turnover_usd * 0.001

gross_operator_revenue_usd =
    owner_fee_usd + observed_venue_cash_revenue_usd

net_operator_revenue_usd =
    gross_operator_revenue_usd - allocated_infrastructure_cost_usd

net_revenue_per_1000_usd =
    net_operator_revenue_usd * 1000 / evidenced_turnover_usd
```

All operations use `fixed.Value`. Overflow, negative turnover, negative
observed venue cash, or negative infrastructure cost fail closed.

`gate_passed` is true only when:

- the contract is complete;
- evidenced turnover is positive;
- every input is valid;
- `net_revenue_per_1000_usd >= 0.5`.

Zero turnover returns `gate_passed:false` and
`INSUFFICIENT_REVENUE_EVIDENCE`; it is not a division error and not a pass.

### Stage A HTTP slice

Create `internal/stagea/httpapi`.

The server receives a revenue read-model interface. It cannot receive a
collector, writable repository, exchange client, execution service, or
credential provider.

The implemented routes are:

```text
GET /healthz
GET /readyz
GET /v1/meta
GET /v1/business/operator-revenue
```

`/readyz` returns `503` because storage, migrations, feed read models, and
experiment state are absent. This is intentional and prevents the inactive n8n
workflow from treating the slice as an operational falsifier.

Every `/v1/*` response contains:

```json
{
  "mode": "public_data_falsification",
  "execution_available": false,
  "recommendation": false,
  "generated_at": "UTC RFC3339Nano",
  "data": {}
}
```

The operator-revenue data preserves the fields already required by n8n:

```json
{
  "operator_revenue": {
    "contract_complete": true,
    "source": "owner_turnover_fee",
    "rate": "0.001",
    "turnover_basis": "filled_entry_exit_notional_both_legs",
    "payout_terms": "model_only_stage_a_no_cash_collection",
    "collection_mechanism": "modeled_only",
    "infrastructure_cost": "actual_allocated_usd",
    "gate_passed": false,
    "reason_codes": ["INSUFFICIENT_REVENUE_EVIDENCE"]
  }
}
```

The response also includes all calculated fixed-point evidence fields.
Unknown evidence values are JSON `null`; they are never coerced to zero.

POST, PUT, PATCH, and DELETE are not registered. Security headers and
`Cache-Control: no-store` match the existing server policy.

The source-controlled n8n gate must require both
`contract_complete:true` and `gate_passed:true`. Contract completeness alone
is not economic evidence. The no-turnover report therefore remains blocked.
The already imported Claw workflow stays inactive and is not re-imported by
this checkpoint.

### Minimal falsifier command

Create `cmd/falsifier`.

It:

1. loads the credential-free Stage A configuration;
2. loads the versioned operator-revenue contract;
3. constructs a no-turnover revenue read model;
4. starts only the Stage A HTTP slice;
5. performs graceful shutdown.

It does not:

- connect to Hyperliquid, Lighter, Variational, or PostgreSQL;
- report readiness;
- expose fake experiment or data-quality routes;
- accept private configuration;
- collect money;
- enter the current production Docker target;
- deploy to Claw.

The command is compiled by repository-wide verification. A dedicated
production image and deployment remain in Task 9.

## Error handling

- Missing/unreadable/malformed contract file: startup error, exit code `2`.
- Syntactically valid incomplete contract: HTTP `200`,
  `contract_complete:false`, `gate_passed:false`, stable reason codes.
- Invalid or missing revenue evidence: HTTP `200`, fail-closed result with
  reason codes.
- Unsupported HTTP method: `405` or `404`, never a mutating handler.
- Internal serialization failure: terminate the response without inventing
  values; tests must make the response types JSON-safe.

Process readiness and economic validity are separate. Economic failure is
reported in the data envelope; absent runtime dependencies keep `/readyz` at
`503`.

## Required tests

### Contract tests

- the frozen JSON contract loads and is complete;
- unknown fields are rejected;
- JSON numeric decimals are rejected;
- every required semantic field can independently make the contract
  incomplete;
- a rate other than `10` bps makes this frozen Stage A contract incomplete;
- negative thresholds are rejected.

### Calculation tests

- `$1,000` turnover, `$0` venue cash, `$0.50` infrastructure cost produces
  `$1.00` owner fee, `$0.50` net, and passes exactly at the boundary;
- infrastructure cost `$0.50000001` produces `$0.49999999` net and fails;
- zero turnover returns `INSUFFICIENT_REVENUE_EVIDENCE`;
- absent venue cash evidence contributes exactly zero but is identified as
  unobserved;
- negative inputs and arithmetic overflow fail closed.

### HTTP tests

- exact envelope and string-decimal encoding;
- `execution_available:false`;
- `recommendation:false`;
- UTC RFC3339Nano `generated_at`;
- required n8n fields are nonempty for the complete contract;
- no-turnover evidence does not pass the revenue gate;
- the n8n validator rejects a gate that checks contract completeness but not
  `gate_passed:true`;
- incomplete contract remains visible and fails closed;
- `/readyz` returns `503`;
- mutating methods cannot reach a handler;
- `Cache-Control: no-store` and security headers are present.

### Dependency and safety tests

Repository-wide checks must prove that `cmd/falsifier` and
`internal/stagea` do not import execution, signing, wallet, Telegram, private
exchange, or trading SDK code. No credential variable enters the Stage A
environment contract.

## TDD and verification

Implementation must follow RED, GREEN, REFACTOR:

1. commit failing domain/config/HTTP tests;
2. run them and record the expected missing-implementation failure;
3. add the minimum implementation;
4. run focused tests;
5. run repository-wide formatting, vet, tests, race tests, n8n validation,
   and Docker verification on Claw;
6. obtain an independent task review;
7. update `handoff.md`;
8. create one coherent implementation commit after the review is clean.

No activation, deployment, credentials, or live trading is part of this
design.
