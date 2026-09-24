# Gate0 Public Shadow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove or falsify a paired Hyperliquid/Lighter public-data opportunity after executable costs, deterministic replay, and five complete UTC measurement days.

**Architecture:** Python A2 remains the evidence and research contour. It captures immutable public venue frames, persists raw and processed evidence in PostgreSQL, replays it deterministically, and exposes GET-only status. Claw runs the pinned image through the existing app-stack proxy/network. Binance, if enabled, is an explicitly separate benchmark and never contributes to the primary HL/Lighter decision.

**Tech Stack:** Python 3.12, PostgreSQL 16/17, Docker, GitHub Actions, existing Claw app-stack network, n8n inactive GET-only monitor.

## Global Constraints

- `mode=public_data_falsification` and `execution_available=false` for every Stage A endpoint.
- Primary venues are Hyperliquid and Lighter; no private/account/order/signing methods.
- Terminal decisions are exactly `KILL` or `EXTEND`; Stage A never emits `GO`.
- Raw payload bytes, provenance, monotonic receive time, wall time, epoch, and SHA-256 are persisted before processing claims.
- Hyperliquid requires complete snapshots; Lighter requires snapshot plus nonce-linked deltas; gaps invalidate the epoch until a fresh snapshot.
- Unknown withdrawal, rebalance, settlement, or oracle-basis costs remain null and cannot be treated as zero.
- PostgreSQL is authoritative; pgvector is offline-only and is not on the decision path.
- The collector uses the existing app-stack proxy/network on Claw, non-root read-only execution, bounded resources, and no host ports.
- n8n remains `active=false` until every Gate0 prerequisite and human deployment approval is recorded.

## Gate0 acceptance contract

The run is eligible for `EXTEND` only when every condition below is true:

1. A 60-minute warmup completes with healthy `/health` and `/ready` responses.
2. Exactly five complete UTC measurement days are present after warmup.
3. At least 99.5% of expected L2 slots are present; silent drops are zero.
4. At least 100 closed shadow lifecycles exist, with at least 30 per reviewed mapping.
5. No single day contributes more than 35% of accepted lifecycles; no instrument contributes more than 50%; the top ten opportunities contribute no more than 25%.
6. Calm, normal, and stressed regimes are represented.
7. Every lifecycle uses complete executable depth on both venues, delayed causal legs, exact fixed-point VWAP, venue fees, measured slippage, funding when applicable, and non-zero known reserves.
8. The 95% block-bootstrap lower bound and median net capture are positive under Standard fee assumptions, measured delay, and the 5-second stress model.
9. Raw replay is byte-deterministic across two fresh processes; restart, outage, idempotency, retention, and hash-bound registry checks pass.
10. A named human reviewer records `KILL` or `EXTEND`; no automated result authorizes live trading.

Any failed hard condition produces `KILL` for the run. Missing evidence is a failure, not a pass.

### Task 1: Freeze the reviewed mappings and run identity

**Files:**
- Modify: `config/a2-reviewed-perpetual-mappings.json`
- Test: `tests/a2/test_mapping_registry.py`
- Test: `tests/a2/test_universe.py`
- Evidence: `docs/a2-mapping-review.md`

**Interfaces:**
- Consumes: authoritative venue contract evidence and reviewed mapping registry.
- Produces: immutable mapping IDs, contract/equivalence hashes, and a run-specific registry hash used by the A2 PLAN manifest.

- [ ] **Step 1: Add a failing test for empty evidence hashes.**

```python
def test_primary_mapping_requires_contract_and_equivalence_hashes(self) -> None:
    registry = load_registry()
    for mapping in registry.primary_mappings():
        self.assertRegex(mapping.contract_evidence_hash, r"^[0-9a-f]{64}$")
        self.assertRegex(mapping.equivalence_evidence_hash, r"^[0-9a-f]{64}$")
```

- [ ] **Step 2: Run the focused test and confirm it fails on the current provisional registry.**

Run: `python -B -m unittest tests.a2.test_mapping_registry -v`

Expected: failure identifying missing evidence hashes.

- [ ] **Step 3: Replace provisional mappings only with evidence-backed values.**

Every primary mapping must include venue market IDs, linear/inverse type, multiplier, units, oracle/index, collateral, funding interval, tick, lot, minimum quote, validity interval, and SHA-256 evidence references. If any field is unavailable, keep the mapping unapproved and do not start the measurement run.

- [ ] **Step 4: Re-run the registry and universe suites.**

Run: `python -B -m unittest tests.a2.test_mapping_registry tests.a2.test_universe -v`

Expected: all tests pass and the registry hash is stable across two reads.

- [ ] **Step 5: Commit the mapping gate.**

```bash
git add config/a2-reviewed-perpetual-mappings.json docs/a2-mapping-review.md tests/a2/test_mapping_registry.py tests/a2/test_universe.py
git commit -m "gate(a2): require evidence-backed instrument mappings"
```

### Task 2: Add the executable after-cost shadow gate

**Files:**
- Modify: `multi_exchange_engine/a2/soak_gate.py`
- Modify: `multi_exchange_engine/a2/model.py`
- Test: `tests/a2/test_soak_gate.py`
- Test: `tests/a2/test_model.py`

**Interfaces:**
- Consumes: closed lifecycle records, normalized depth, fee schedules, delay telemetry, and capital profiles.
- Produces: canonical JSON report with `decision`, `hard_failures`, `coverage`, `cost_breakdown`, `bootstrap_lower_bound`, and `median_net_capture`.

- [ ] **Step 1: Write a failing test for unknown costs.**

```python
def test_unknown_rebalance_cost_cannot_be_zero(self) -> None:
    lifecycle = make_closed_lifecycle(rebalance_cost=None)
    report = evaluate_gate([lifecycle], standard_gate_config())
    self.assertEqual(report.decision, "KILL")
    self.assertIn("UNKNOWN_REBALANCE_COST", report.hard_failures)
```

- [ ] **Step 2: Run the focused test and verify the expected failure.**

Run: `python -B -m unittest tests.a2.test_soak_gate.SoakingGateTests.test_unknown_rebalance_cost_cannot_be_zero -v`

- [ ] **Step 3: Implement the minimal fail-closed evaluator.**

The evaluator must calculate exact entry and exit VWAP at full requested depth, subtract venue fees for both legs, causal delay slippage, measured stress, funding only when the hold crosses settlement, and known inventory costs. Null costs remain null and create a hard failure. It must return only `KILL` or `EXTEND`.

- [ ] **Step 4: Add concentration and regime tests.**

Cover day concentration over 35%, instrument concentration over 50%, top-ten concentration over 25%, missing regimes, fewer than 100 total lifecycles, and fewer than 30 per mapping.

- [ ] **Step 5: Run the complete A2 unit suite.**

Run: `python -B -m unittest discover -s tests/a2 -t . -v`

Expected: zero failures; PostgreSQL-only tests may remain explicitly skipped when PostgreSQL is unavailable.

- [ ] **Step 6: Commit the shadow gate.**

```bash
git add multi_exchange_engine/a2/soak_gate.py multi_exchange_engine/a2/model.py tests/a2/test_soak_gate.py tests/a2/test_model.py
git commit -m "feat(a2): enforce after-cost kill-or-extend gate"
```

### Task 3: Verify CI, image, and Claw fixture deployment

**Files:**
- Modify: `.github/workflows/ci.yml` only when a failing check identifies a concrete contract defect.
- Modify: `.github/workflows/build-a2-on-claw.yml` only when a failing check identifies a concrete contract defect.
- Evidence: `docs/a2-deployment.md`, `handoff.md`

**Interfaces:**
- Consumes: reviewed branch commit and mapping registry hash.
- Produces: pinned image digest, SBOM, vulnerability report, Claw `/health` and `/ready` evidence, and rollback digest.

- [ ] **Step 1: Run local static and Python gates.**

```powershell
python -B -m unittest tests.a2.test_deployment_contract -v
python scripts/check-a2-boundary.py
python -m compileall -q multi_exchange_engine tests scripts
git diff --check
```

- [ ] **Step 2: Dispatch GitHub CI and wait for every matrix job.**

The required jobs are Python reference tests, Go checks, PostgreSQL 16 and 17 integration, deterministic replay, boundary scan, Docker verify/production builds, SBOM generation, and strict HIGH/CRITICAL scan.

- [ ] **Step 3: Build the exact image on Claw.**

Use the manual workflow on `[self-hosted, claw]`; tag the image with the exact commit SHA and `candidate`. Do not start the collector from the build workflow.

- [ ] **Step 4: Run the production mount smoke test.**

The reviewed registry must be mounted read-only, the image must run as UID/GID `10001:10001`, root filesystem read-only, all capabilities dropped, and network access limited to the existing app-stack route.

- [ ] **Step 5: Commit deployment evidence.**

```bash
git add docs/a2-deployment.md handoff.md
git commit -m "docs(a2): record Gate0 deployment evidence"
```

### Task 4: Warmup, five-day shadow run, and decision

**Files:**
- Modify: `docs/five-day-stage-a-spec.md` only if the verified gate changes.
- Evidence: append run reports and canonical hashes to `handoff.md`.

**Interfaces:**
- Consumes: running Claw collector, approved registry, public Hyperliquid/Lighter data, and GET-only status endpoints.
- Produces: immutable five-day report and human-signed `KILL` or `EXTEND` decision.

- [ ] **Step 1: Start a fresh run with a unique run ID.**
- [ ] **Step 2: Observe 60 minutes of warmup.**
- [ ] **Step 3: Verify clock, coverage, gaps, epoch resets, raw hashes, and append-only persistence.**
- [ ] **Step 4: Collect exactly five UTC measurement days.**
- [ ] **Step 5: Run replay twice in fresh processes and compare canonical reports byte-for-byte.**
- [ ] **Step 6: Generate after-cost report and apply every hard gate.**
- [ ] **Step 7: Record human decision `KILL` or `EXTEND`; keep n8n inactive unless separately authorized.**

## Rollback

Stop the collector, preserve the immutable run evidence, and redeploy the previous image digest. A failed gate cannot be repaired by editing stored evidence. A changed mapping requires a new run ID and new registry hash.

## Final verification checklist

- [ ] Mapping evidence hashes present and stable.
- [ ] Gate evaluator has negative tests for every hard failure.
- [ ] CI and Claw image checks are green on the exact commit.
- [ ] Health/readiness and registry mount smoke passed on Claw.
- [ ] Five complete days and all coverage/concentration/regime gates passed.
- [ ] Replay is byte-deterministic.
- [ ] Human reviewer recorded `KILL` or `EXTEND`.
- [ ] No live trading, private adapter, or n8n activation occurred.
