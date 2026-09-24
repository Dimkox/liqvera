# Stage A Operator Revenue Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a credential-free, model-only 10 bps operator-revenue contract,
fixed-point evaluator, GET-only Stage A API slice, and minimal falsifier
command without activating n8n or claiming runtime readiness.

**Architecture:** A strict versioned JSON contract feeds a pure revenue domain.
The domain exposes immutable reports through a read-only interface consumed by
a separate Stage A HTTP server. A minimal `cmd/falsifier` assembles only that
slice; collectors, PostgreSQL, lifecycle processing, deployment, and live
execution remain absent.

**Tech Stack:** Go 1.26.5, `internal/fixed`, `net/http`, JSON string decimals,
PowerShell n8n validators, Bash dependency checks, GitHub Actions, pinned
Docker verifier.

## Global Constraints

- Owner fee is exactly `10` basis points, represented as rate fraction
  `"0.001"`.
- Turnover is every evidenced simulated entry and exit fill across both legs.
- Stage A is `modeled_only`; it does not collect money.
- Unfilled or rejected volume is not charged; evidenced filled volume is not
  refunded in the model.
- Venue-program revenue is exactly zero unless cash evidence is observed.
- Infrastructure cost is actual allocated USD evidence and is never silently
  assumed to be zero.
- The operator gate is at least `"0.5"` USD net revenue per `"1000"` USD
  evidenced turnover.
- All money, rate, turnover, cost, and threshold values use
  `fixed.Value` scaled by `1e8`; JSON decimals are strings and unknown
  evidence is `null`.
- `/v1/*` responses declare `mode:"public_data_falsification"`,
  `execution_available:false`, and `recommendation:false`.
- The partial falsifier always returns `503` from `/readyz`.
- No private endpoints, credentials, accounts, balances, keys, signing,
  trading SDK, order, cancel, transfer, withdrawal, RFQ acceptance, Telegram,
  referral, or wallet code may enter `cmd/falsifier`'s dependency closure.
- n8n stays `active=false`; this checkpoint is not deployed to Claw.
- Hyperliquid and Lighter lifecycle admission remains blocked by provisional
  mappings and empty evidence hashes.
- Each task follows RED, GREEN, REFACTOR, receives independent review, updates
  the progress ledger, and ends in coherent commits.

---

### Task 1: Strict versioned operator-revenue contract

**Files:**

- Create: `config/stage-a-operator-revenue.json`
- Create: `internal/stagea/revenue/contract.go`
- Create: `internal/stagea/revenue/contract_test.go`
- Modify: `internal/stagea/config/config.go`
- Modify: `internal/stagea/config/config_test.go`
- Modify: `internal/stagea/model/reasons.go`

**Interfaces:**

```go
package revenue

type Contract struct {
    ContractVersion                  string      `json:"contract_version"`
    Source                           string      `json:"source"`
    Rate                             fixed.Value `json:"rate"`
    RateBPS                          fixed.Value `json:"rate_bps"`
    TurnoverBasis                    string      `json:"turnover_basis"`
    Payer                            string      `json:"payer"`
    ChargeMoment                     string      `json:"charge_moment"`
    PayoutTerms                      string      `json:"payout_terms"`
    CollectionMechanism              string      `json:"collection_mechanism"`
    RefundOrRebateRules              string      `json:"refund_or_rebate_rules"`
    PayoutCurrency                   string      `json:"payout_currency"`
    InfrastructureCost               string      `json:"infrastructure_cost"`
    MinimumNetRevenuePer1000USD      fixed.Value `json:"minimum_net_revenue_per_1000_usd"`
    VenueProgramRevenueTreatment     string      `json:"venue_program_revenue_treatment"`
}

type ContractValidation struct {
    Complete bool
    Codes    []model.ReasonCode
}

func LoadContract(path string) (Contract, error)
func (c Contract) Validate() ContractValidation
```

Add these stable reason codes:

```go
OperatorRevenueContractIncomplete ReasonCode =
    "OPERATOR_REVENUE_CONTRACT_INCOMPLETE"
OperatorRevenueInputInvalid ReasonCode =
    "OPERATOR_REVENUE_INPUT_INVALID"
InsufficientRevenueEvidence ReasonCode =
    "INSUFFICIENT_REVENUE_EVIDENCE"
OperatorRevenueBelowFloor ReasonCode =
    "OPERATOR_REVENUE_BELOW_FLOOR"
OperatorRevenueArithmeticError ReasonCode =
    "OPERATOR_REVENUE_ARITHMETIC_ERROR"
```

Extend Stage A config:

```go
type Config struct {
    // Existing fields remain unchanged.
    OperatorRevenueContract string
}
```

Allowed environment variable:

```text
STAGE_A_OPERATOR_REVENUE_CONTRACT
```

Default:

```text
config/stage-a-operator-revenue.json
```

- [ ] **Step 1: Write contract and configuration tests first**

Tests must assert:

```go
func TestFrozenOperatorRevenueContractLoadsComplete(t *testing.T)
func TestContractRejectsUnknownJSONField(t *testing.T)
func TestContractRejectsNumericJSONDecimal(t *testing.T)
func TestContractRejectsTrailingJSONValue(t *testing.T)
func TestEachRequiredFieldCanMakeContractIncomplete(t *testing.T)
func TestFrozenContractRejectsAnyRateOtherThanTenBPS(t *testing.T)
func TestContractRejectsNegativeRevenueFloor(t *testing.T)
func TestStageAConfigExposesOperatorRevenueContractPath(t *testing.T)
func TestUnknownRevenueEnvironmentAliasFailsClosed(t *testing.T)
```

The completeness table clears each string field in turn and separately checks:

```go
c.Rate = fixed.Zero()
c.RateBPS = fixed.Zero()
c.MinimumNetRevenuePer1000USD = fixed.Zero()
```

Expected incomplete result:

```go
ContractValidation{
    Complete: false,
    Codes: []model.ReasonCode{
        model.OperatorRevenueContractIncomplete,
    },
}
```

- [ ] **Step 2: Run RED and record the expected failure**

Run through the existing verifier:

```bash
docker build --target verify \
  -t multi-exchange-engine:operator-revenue-contract-red .
```

Expected: compilation fails because `internal/stagea/revenue`, the contract
reason codes, and the config field do not exist. Commit only the failing tests:

```bash
git add internal/stagea/revenue/contract_test.go \
  internal/stagea/config/config_test.go
git commit -m "test: define Stage A revenue contract"
```

- [ ] **Step 3: Add the frozen JSON contract**

Create `config/stage-a-operator-revenue.json` with exactly:

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

- [ ] **Step 4: Implement strict loading and completeness**

`LoadContract` must:

1. open the exact path;
2. decode with `DisallowUnknownFields`;
3. attempt a second decode and require `io.EOF`;
4. return syntax/type errors without replacing values;
5. leave semantic completeness to `Validate`.

`Validate` requires the exact frozen enum strings and exact fixed values:

```go
const (
    frozenVersion        = "stage-a-v1"
    frozenSource         = "owner_turnover_fee"
    frozenTurnoverBasis  = "filled_entry_exit_notional_both_legs"
    frozenMechanism      = "modeled_only"
)

var (
    frozenRate  = fixed.MustParse("0.001")
    frozenBPS   = fixed.MustParse("10")
    frozenFloor = fixed.MustParse("0.5")
)
```

Any mismatch returns the single stable incomplete-contract reason code.

- [ ] **Step 5: Extend the Stage A public config allowlist**

Add the exact env name and default path. Tests must prove that aliases such as
`STAGE_A_REVENUE_RATE_BPS` remain unknown and fail closed.

- [ ] **Step 6: Run GREEN, refactor, and commit**

Run:

```bash
gofmt -w internal/stagea/revenue internal/stagea/config \
  internal/stagea/model
go test ./internal/stagea/revenue ./internal/stagea/config
go vet ./internal/stagea/revenue ./internal/stagea/config
```

Expected: all focused tests pass. Then:

```bash
git add config/stage-a-operator-revenue.json \
  internal/stagea/revenue internal/stagea/config \
  internal/stagea/model/reasons.go
git commit -m "feat: add strict Stage A revenue contract"
```

---

### Task 2: Fixed-point operator-revenue evaluator

**Files:**

- Create: `internal/stagea/revenue/evaluate.go`
- Create: `internal/stagea/revenue/evaluate_test.go`

**Interfaces:**

```go
type Evidence struct {
    EvidencedTurnoverUSD          *fixed.Value
    ObservedVenueCashRevenueUSD   *fixed.Value
    InfrastructureCostUSD         *fixed.Value
}

type Report struct {
    Contract                       Contract
    ContractComplete               bool
    GatePassed                     bool
    VenueCashObserved              bool
    EvidencedTurnoverUSD           *fixed.Value
    OwnerFeeUSD                    *fixed.Value
    ObservedVenueCashRevenueUSD    *fixed.Value
    GrossOperatorRevenueUSD        *fixed.Value
    InfrastructureCostUSD          *fixed.Value
    NetOperatorRevenueUSD          *fixed.Value
    NetRevenuePer1000USD           *fixed.Value
    Codes                          []model.ReasonCode
}

func Evaluate(contract Contract, evidence Evidence) Report
```

The report preserves the configured contract even when evidence is invalid.
Unknown evidence and derived values are `nil`, so HTTP encodes them as `null`.

- [ ] **Step 1: Write evaluator boundary tests**

Tests must use real `fixed.Value` inputs:

```go
func TestEvaluatePassesExactlyAtFiftyCentsPerThousand(t *testing.T)
func TestEvaluateFailsOneFixedUnitBelowFloor(t *testing.T)
func TestEvaluateZeroTurnoverIsInsufficientEvidence(t *testing.T)
func TestEvaluateAbsentVenueCashCountsZeroButRemainsUnobserved(t *testing.T)
func TestEvaluateMissingInfrastructureCostIsInsufficient(t *testing.T)
func TestEvaluateNegativeInputsFailClosed(t *testing.T)
func TestEvaluateArithmeticOverflowFailsClosed(t *testing.T)
func TestEvaluateIncompleteContractCannotPass(t *testing.T)
```

Exact passing evidence:

```go
turnover := fixed.MustParse("1000")
venueCash := fixed.MustParse("0")
cost := fixed.MustParse("0.5")
report := Evaluate(contract, Evidence{
    EvidencedTurnoverUSD:        &turnover,
    ObservedVenueCashRevenueUSD: &venueCash,
    InfrastructureCostUSD:       &cost,
})
```

Expected:

```text
owner_fee_usd                 = "1"
gross_operator_revenue_usd    = "1"
net_operator_revenue_usd      = "0.5"
net_revenue_per_1000_usd      = "0.5"
gate_passed                   = true
```

One-unit-below evidence uses infrastructure cost `"0.50000001"` and expects
net and normalized net `"0.49999999"` with
`OPERATOR_REVENUE_BELOW_FLOOR`.

- [ ] **Step 2: Run RED**

```bash
go test ./internal/stagea/revenue \
  -run 'TestEvaluate' -count=1
```

Expected: compilation fails because `Evidence`, `Report`, and `Evaluate` do
not exist.

- [ ] **Step 3: Implement fail-closed evaluation**

Implement in this order:

1. copy contract and completeness into the report;
2. reject incomplete contract;
3. require non-nil turnover and infrastructure cost;
4. treat nil venue cash as numeric zero while setting
   `VenueCashObserved=false`;
5. reject negative inputs;
6. reject zero turnover with `INSUFFICIENT_REVENUE_EVIDENCE`;
7. calculate with `fixed.Mul`, `Add`, `Sub`, and `Div`;
8. convert any arithmetic error to
   `OPERATOR_REVENUE_ARITHMETIC_ERROR`;
9. compare normalized net to the configured floor;
10. set `GatePassed=true` only at or above the floor.

Do not use `float64`, integer bps shortcuts, or implicit infrastructure zero.

- [ ] **Step 4: Run GREEN and commit**

```bash
gofmt -w internal/stagea/revenue
go test ./internal/stagea/revenue -count=1
go vet ./internal/stagea/revenue
```

Expected: all contract and evaluator tests pass.

```bash
git add internal/stagea/revenue/evaluate.go \
  internal/stagea/revenue/evaluate_test.go
git commit -m "feat: evaluate Stage A operator revenue"
```

---

### Task 3: GET-only Stage A HTTP slice

**Files:**

- Create: `internal/stagea/httpapi/server.go`
- Create: `internal/stagea/httpapi/server_test.go`

**Interfaces:**

```go
package httpapi

type BuildInfo struct {
    Version string `json:"version"`
    Commit  string `json:"commit"`
}

type OperatorRevenueReader interface {
    OperatorRevenue() revenue.Report
}

type Clock func() time.Time

type Server struct {
    handler http.Handler
}

func New(
    info BuildInfo,
    reader OperatorRevenueReader,
    clock Clock,
) *Server

func (s *Server) Handler() http.Handler
```

The only routes in this checkpoint are:

```text
GET /healthz
GET /readyz
GET /v1/meta
GET /v1/business/operator-revenue
```

- [ ] **Step 1: Write exact route and envelope tests**

Required tests:

```go
func TestOperatorRevenueEnvelopeIsReadOnlyAndFailClosed(t *testing.T)
func TestCompleteContractExposesEveryN8NRequiredField(t *testing.T)
func TestIncompleteContractRemainsVisibleAndCannotPass(t *testing.T)
func TestStageAPartialRuntimeIsNeverReady(t *testing.T)
func TestStageARoutesRejectMutatingMethods(t *testing.T)
func TestStageAResponsesUseSecurityAndNoStoreHeaders(t *testing.T)
func TestGeneratedAtIsUTCRFC3339Nano(t *testing.T)
```

Use a fixed clock:

```go
now := time.Date(2026, 7, 25, 12, 0, 0, 123, time.UTC)
clock := func() time.Time { return now }
```

Assert the top-level envelope:

```json
{
  "mode": "public_data_falsification",
  "execution_available": false,
  "recommendation": false,
  "generated_at": "2026-07-25T12:00:00.000000123Z"
}
```

Assert nonempty n8n fields under `data.operator_revenue`:

```text
source
rate
turnover_basis
payout_terms
collection_mechanism
infrastructure_cost
```

For no-turnover evidence assert:

```text
contract_complete = true
gate_passed = false
reason_codes = ["INSUFFICIENT_REVENUE_EVIDENCE"]
```

Every POST, PUT, PATCH, and DELETE request to every registered route must
return `404` or `405` and never invoke the reader.

- [ ] **Step 2: Run RED**

```bash
go test ./internal/stagea/httpapi -count=1
```

Expected: package or exported server interfaces are missing.

- [ ] **Step 3: Implement typed envelopes and handlers**

Use typed response structs. Do not build the revenue payload with
`map[string]any`.

Required operator-revenue JSON fields:

```go
type operatorRevenueData struct {
    ContractComplete            bool               `json:"contract_complete"`
    Source                      string             `json:"source"`
    Rate                        fixed.Value        `json:"rate"`
    RateBPS                     fixed.Value        `json:"rate_bps"`
    TurnoverBasis               string             `json:"turnover_basis"`
    PayoutTerms                 string             `json:"payout_terms"`
    CollectionMechanism         string             `json:"collection_mechanism"`
    InfrastructureCost         string             `json:"infrastructure_cost"`
    GatePassed                  bool               `json:"gate_passed"`
    EvidencedTurnoverUSD        *fixed.Value       `json:"evidenced_turnover_usd"`
    OwnerFeeUSD                 *fixed.Value       `json:"owner_fee_usd"`
    ObservedVenueCashRevenueUSD *fixed.Value       `json:"observed_venue_cash_revenue_usd"`
    GrossOperatorRevenueUSD     *fixed.Value       `json:"gross_operator_revenue_usd"`
    InfrastructureCostUSD       *fixed.Value       `json:"infrastructure_cost_usd"`
    NetOperatorRevenueUSD       *fixed.Value       `json:"net_operator_revenue_usd"`
    NetRevenuePer1000USD        *fixed.Value       `json:"net_revenue_per_1000_usd"`
    VenueCashObserved           bool               `json:"venue_cash_observed"`
    ReasonCodes                 []model.ReasonCode `json:"reason_codes"`
}
```

`/readyz` always returns:

```json
{
  "status": "not_ready",
  "missing": [
    "storage",
    "migrations",
    "feed_read_models",
    "experiment_state"
  ]
}
```

with status `503`.

- [ ] **Step 4: Add headers and method-negative behavior**

Match the existing server:

```text
Content-Security-Policy: default-src 'none'
X-Content-Type-Options: nosniff
Cache-Control: no-store
Content-Type: application/json
```

Register routes with Go method patterns such as
`mux.HandleFunc("GET /v1/business/operator-revenue", handler)`.

- [ ] **Step 5: Run GREEN and commit**

```bash
gofmt -w internal/stagea/httpapi
go test ./internal/stagea/httpapi ./internal/stagea/revenue -count=1
go vet ./internal/stagea/httpapi
```

```bash
git add internal/stagea/httpapi
git commit -m "feat: expose read-only Stage A revenue API"
```

---

### Task 4: Minimal falsifier assembly and read-only CI gate

**Files:**

- Create: `cmd/falsifier/main.go`
- Create: `cmd/falsifier/main_test.go`
- Create: `scripts/verify-stage-a-read-only.sh`
- Modify: `.github/workflows/ci.yml`
- Modify: `deploy/n8n/stage-a-orchestrator.workflow.json`
- Modify: `scripts/validate-stage-a-n8n.ps1`
- Modify: `scripts/test-validate-stage-a-n8n-mutations.ps1`
- Modify: `README.md`
- Modify: `docs/five-day-stage-a-spec.md`
- Modify: `docs/superpowers/plans/2026-07-21-five-day-stage-a.md`
- Modify: `handoff.md`
- Update locally: `.superpowers/sdd/progress.md` (ignored recovery ledger)

**Interfaces:**

```go
type staticRevenueReader struct {
    report revenue.Report
}

func (r staticRevenueReader) OperatorRevenue() revenue.Report

func buildAPI(
    cfg stageconfig.Config,
    info stagehttp.BuildInfo,
    clock stagehttp.Clock,
) (*stagehttp.Server, error)
```

`buildAPI` loads the configured contract and evaluates it with:

```go
turnover := fixed.Zero()

revenue.Evidence{
    EvidencedTurnoverUSD:        &turnover,
    ObservedVenueCashRevenueUSD: nil,
    InfrastructureCostUSD:       nil,
}
```

The resulting report is contract-complete but gate-failed with insufficient
evidence.

- [ ] **Step 1: Write assembly tests first**

Required tests:

```go
func TestBuildAPILoadsFrozenContractAndStaysNotReady(t *testing.T)
func TestBuildAPIFailsForUnreadableContract(t *testing.T)
func TestBuildAPIFailsForMalformedContract(t *testing.T)
func TestFalsifierDependencyClosureIsReadOnly(t *testing.T)
```

The assembly test writes a complete contract to `t.TempDir`, points
`Config.OperatorRevenueContract` at it, invokes `buildAPI`, and checks:

```text
GET /v1/business/operator-revenue = 200
contract_complete = true
gate_passed = false
GET /readyz = 503
```

- [ ] **Step 2: Run RED**

```bash
go test ./cmd/falsifier -count=1
```

Expected: `cmd/falsifier` and `buildAPI` do not exist.

- [ ] **Step 3: Implement minimal process assembly**

`main` must:

1. use JSON `slog`;
2. call the existing credential-rejecting Stage A config loader;
3. call `buildAPI`;
4. exit `2` on configuration or contract errors;
5. start `http.Server` with the existing timeout values;
6. handle SIGINT/SIGTERM;
7. perform a 10-second graceful shutdown;
8. log `mode=public_data_falsification` and
   `live_execution=false`.

It must not import Stage 0 `internal/httpapi`, exchange contracts, execution,
ownership, risk, reconcile, Telegram, wallet, or signing code.

- [ ] **Step 4: Add the dependency safety script**

`scripts/verify-stage-a-read-only.sh` must expose a testable
`check_dependencies` function and execute it when run directly:

```bash
#!/usr/bin/env bash
set -euo pipefail

check_dependencies() {
  local deps="$1"

  for forbidden in \
    github.com/Dimkox/multi-exchange-engine/internal/execution \
    github.com/Dimkox/multi-exchange-engine/internal/ownership \
    github.com/Dimkox/multi-exchange-engine/internal/risk \
    github.com/Dimkox/multi-exchange-engine/internal/reconcile
  do
    if grep -Fxq "$forbidden" <<<"$deps"; then
      echo "forbidden dependency: $forbidden" >&2
      return 1
    fi
  done

  if grep -Eiq '(wallet|signing|telegram|hyperliquid.*sdk|lighter.*sdk)' \
    <<<"$deps"
  then
    echo "forbidden Stage A dependency category" >&2
    return 1
  fi

  return 0
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  check_dependencies "$(go list -deps ./cmd/falsifier)"
  echo "Stage A falsifier dependency closure is read-only."
fi
```

The Go dependency test executes the script directly and requires exit zero. It
also sources the script and calls `check_dependencies` with a literal forbidden
package line, requiring nonzero exit; do not accept a test that checks only the
happy path.

- [ ] **Step 5: Extend GitHub Actions**

After unit/race tests, add:

```yaml
      - name: Verify Stage A read-only dependency closure
        run: bash scripts/verify-stage-a-read-only.sh

      - name: Validate inactive Stage A n8n workflow
        shell: pwsh
        run: |
          ./scripts/validate-stage-a-n8n.ps1
          ./scripts/test-validate-stage-a-n8n-mutations.ps1

      - name: Build binaries
        run: |
          go build -trimpath ./cmd/engine
          go build -trimpath ./cmd/falsifier
```

Replace the existing single-engine build step rather than adding a duplicate.

- [ ] **Step 6: Make the source n8n revenue gate economically fail closed**

Update the Code node to reject unless:

```javascript
if (operatorRevenue.contract_complete !== true) {
  throw new Error('operator revenue contract is incomplete');
}
if (operatorRevenue.gate_passed !== true) {
  throw new Error('operator revenue gate has not passed');
}
```

Extend the validator's exact expected Code body and add a mutation that removes
the `gate_passed` check while leaving `contract_complete:true`. The validator
must reject that mutation. Keep the workflow `active=false`, at exactly nine
allowlisted nodes, with zero credentials and the same five internal GET routes.
Do not import this revision into Claw in this checkpoint.

- [ ] **Step 7: Update operator documentation**

README, the binding five-day spec, the original Stage A plan, and `handoff.md`
must state:

- the revenue slice is model-only;
- the endpoint is implemented;
- the source n8n gate now requires `gate_passed:true`;
- the currently imported Claw workflow remains the older inactive revision;
- `/readyz` is intentionally `503`;
- n8n remains inactive;
- there is no Claw deployment;
- Task 2 remains next after this checkpoint;
- the current GitHub repository and draft PR are recorded.

The original Task 9 plan must identify this checkpoint as a prerequisite
already implemented, without marking the rest of Task 9 complete. Update the
ignored ledger with the final reviewed commit range only after independent
review is clean.

- [ ] **Step 8: Run full verification**

Run fresh:

```bash
gofmt -w cmd/falsifier internal/stagea
test -z "$(gofmt -l .)"
go vet ./...
go test -race -cover ./...
bash scripts/verify-stage-a-read-only.sh
pwsh -File scripts/validate-stage-a-n8n.ps1
pwsh -File scripts/test-validate-stage-a-n8n-mutations.ps1
go build -trimpath ./cmd/engine
go build -trimpath ./cmd/falsifier
docker build --target verify -t multi-exchange-engine:verify .
```

GitHub Actions must pass on the pushed branch. Claw Docker verification, when
used, runs without direct container Internet egress and must not modify
`/home/operator/app-stack`.

- [ ] **Step 9: Independent review and final commit**

The reviewer must provide both:

- spec compliance verdict;
- code-quality verdict.

Critical and Important findings return to the implementer and require
re-review.

After clean review:

```bash
git add cmd/falsifier internal/stagea config deploy/n8n \
  scripts .github/workflows/ci.yml README.md docs handoff.md
git commit -m "feat: add Stage A operator revenue slice"
git push origin stage-a-falsifier
```

Do not activate n8n, deploy the falsifier, merge the draft PR, or start Task 2
inside this commit.
