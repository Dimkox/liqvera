# Seven-Day Shadow Economics Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a public-data-only Shadow Economics Analyzer that replays immutable Hyperliquid and Lighter evidence, reconstructs BTC/ETH/SOL books, evaluates frozen price/basis and funding scenarios, and emits a deterministic `GO`, `NO_GO`, `INSUFFICIENT_EVIDENCE`, or `INVALID_DATASET` verdict.

**Architecture:** A2 remains the immutable public evidence producer. A separate analyzer reads either read-only PostgreSQL evidence or a frozen package through one `EvidenceReader` protocol, reconstructs venue books, applies strict quality and economic mappings, simulates the frozen scenario matrix, and produces hash-bound reports. Final verdicts come only from two byte-identical fresh-process replays of a frozen package.

**Tech Stack:** Python 3.12, standard-library dataclasses/enums/Decimal/Fraction/hashlib/gzip/json, psycopg for read-only PostgreSQL access, existing `multi_exchange_engine.a2` raw-evidence contracts, existing `multi_exchange_engine.shadow` exact-arithmetic and canonical-serialization primitives, unittest/pytest-compatible tests, PostgreSQL 16/17 integration gates, existing A2 Docker/Claw boundary.

## Global Constraints

- Safety boundary: public data, shadow analysis, no exchange credentials, no accounts, no signers, no orders, no cancels, no transfers, no withdrawals.
- Do not add economics, normalized books, opportunities, VWAP, P&L, or verdict logic to `multi_exchange_engine.a2`.
- Implement the seven-day analyzer under `multi_exchange_engine/shadow_economics/`, beside the proven root `a2` and `shadow` packages. Do not expand the parallel `src/multi_exchange_engine` skeleton in this sprint.
- Venues: exact `HYPERLIQUID` and `LIGHTER` only.
- Assets: exact `BTC`, `ETH`, and `SOL` only.
- Products: reviewed linear perpetual mappings only; ticker equality is never equivalence evidence.
- Notional ladder: `100`, `500`, `1000`, `5000`, `10000` USD. Primary verdict sizes: `1000` and `5000` USD.
- Entry thresholds: `0`, `2`, `5`, `10`, `20` bps. Primary verdict thresholds: `5` and `10` bps.
- Price exits: fixed `1`, `5`, `15`, `60` minutes; relative convergence `50%`, `75%`, `90%`; absolute remaining spread `1`, `2`, `5` bps. Primary exit: `75%` convergence or `60` minutes.
- Funding holds: rolling `1`, `4`, `8`, `24` hours; settlement-aware `1` and `2` realized settlements with a `24` hour maximum.
- Delay scenarios: symmetric `100/100`, `300/300`, `500/500`, `1000/1000` ms; asymmetric `100/500`, `500/100`, `300/1000`, `1000/300` ms.
- Primary execution model: parallel taker/taker using independently delayed books. Maker-first is diagnostic only. Sequential taker is worst-case diagnostic only.
- Strict quality: each book age `<=500 ms`, receive-time skew `<=250 ms`, index divergence `<=10 bps`, residual canonical quantity `<=0.25%`, valid snapshot/continuity, non-crossed full-depth books, verified mapping, required fee evidence.
- Diagnostic quality: each book age `<=1000 ms`, skew `<=500 ms`, index divergence `<=25 bps`; diagnostic results never issue `GO`.
- Independent episode cooldown: `60` continuous seconds outside the signal.
- Evidence gate: at least `5` complete UTC data days and at least `95%` strict healthy minutes for BTC/ETH/SOL on both venues.
- Primary portfolio: `20000` USD total, `50/50` venue allocation, `2x` leverage, at least `50%` free-margin reserve. Sensitivities: capital `5000/10000/20000/50000`, allocation `50/50`, `60/40`, `40/60`, leverage `1x/2x/3x`.
- Primary `GO` gate: at least `20` independent episodes; total and median net P&L positive; positive at `300/300` and `500/500` ms; `1000` USD positive; `5000` USD non-negative; operator and conservative product fee cases pass; no single trade contributes more than `25%` of total P&L; funding also requires positive ex-post realized funding P&L.
- Operator fees are manual versioned evidence. Missing operator evidence yields `INSUFFICIENT_INPUT` and blocks overall `GO`; no private API is permitted.
- Final replay is offline, bounded by one raw batch at a time, starts from empty state, performs no network access, and must be byte-identical across two fresh processes.
- Use exact Decimal/Fraction arithmetic. Reject floats, non-finite values, implicit ticker/multiplier inference, top-of-book fallback, and ambient Decimal-context dependence.
- Every significant completed task updates `handoff.md` in the same coherent commit and preserves the shadow-only gate.

---

## File Map

### New production package

```text
multi_exchange_engine/shadow_economics/
    __init__.py              public read-only exports only
    model.py                 immutable identities, events, scenarios, results, verdict enums
    config.py                frozen scenario matrix and versioned fee/config loading
    evidence.py              EvidenceReader protocol and common evidence records
    frozen_package.py        canonical package writer/reader/hash verification
    postgres_reader.py       read-only A2 PostgreSQL implementation
    reconstruction/
        __init__.py
        common.py            immutable L2 book and reconstructor protocol
        hyperliquid.py       Hyperliquid snapshot reconstruction
        lighter.py           Lighter snapshot/delta/nonce reconstruction
    mapping.py               evidence-bound economic mappings and canonical sizing
    quality.py               strict/diagnostic admission decisions
    vwap.py                  exact full-depth sweeps and delayed book lookup
    fees.py                  operator/product fee evidence and cost waterfall
    funding.py               forecast/settlement evidence and signed cashflows
    episodes.py              threshold crossing, cooldown, active-position suppression
    price_strategy.py        delayed entry and fixed/convergence exit simulation
    funding_strategy.py      ex-ante/ex-post funding simulations
    portfolio.py             capital allocation, reserve, prioritization, utilization
    verdict.py               frozen gates and overall verdict
    report.py                canonical JSON/NDJSON/gzip artifacts and Markdown projection
    cli.py                   preview, freeze, and final-replay entry points
```

### New configuration and database boundaries

```text
config/shadow-economics-scenarios.json
config/shadow-economics-fees.example.json
config/shadow-economics-mappings.json
migrations/000003_shadow_economics_views.up.sql
migrations/000003_shadow_economics_views.down.sql
scripts/export-shadow-economics-dataset.py
scripts/run-shadow-economics.py
scripts/check-shadow-economics-boundary.py
```

### New tests

```text
tests/shadow_economics/
    __init__.py
    fixtures.py
    test_model.py
    test_config.py
    test_evidence.py
    test_frozen_package.py
    test_postgres_reader.py
    test_reconstruction_common.py
    test_reconstruction_hyperliquid.py
    test_reconstruction_lighter.py
    test_mapping.py
    test_quality.py
    test_vwap.py
    test_fees.py
    test_funding.py
    test_episodes.py
    test_price_strategy.py
    test_funding_strategy.py
    test_portfolio.py
    test_verdict.py
    test_report.py
    test_cli.py
    test_boundary.py
    integration/test_postgres_reader.py
    integration/test_frozen_replay.py
    integration/test_deterministic_process_replay.py
```

---

### Task 1: Freeze analyzer models, identifiers, and scenario configuration

**Files:**
- Create: `multi_exchange_engine/shadow_economics/__init__.py`
- Create: `multi_exchange_engine/shadow_economics/model.py`
- Create: `multi_exchange_engine/shadow_economics/config.py`
- Create: `config/shadow-economics-scenarios.json`
- Create: `config/shadow-economics-fees.example.json`
- Create: `tests/shadow_economics/__init__.py`
- Create: `tests/shadow_economics/test_model.py`
- Create: `tests/shadow_economics/test_config.py`
- Modify: `handoff.md`

**Interfaces:**
- Produces: `Asset`, `StrategyKind`, `QualityMode`, `ExecutionModel`, `FeeCaseKind`, `Verdict`, `DelayScenario`, `ScenarioMatrix`, `AnalyzerConfig`, `load_analyzer_config(path: Path) -> AnalyzerConfig`.
- Consumes: existing canonical Decimal helpers from `multi_exchange_engine.shadow.tape_codec`; no A2 repository access yet.

- [ ] **Step 1: Write failing enum and configuration tests**

```python
from decimal import Decimal
from pathlib import Path

from mee_contracts.shadow_economics.config import load_analyzer_config
from mee_contracts.shadow_economics.model import Asset, Verdict


def test_frozen_scenario_matrix_matches_approved_design() -> None:
    config = load_analyzer_config(Path("config/shadow-economics-scenarios.json"))
    assert config.assets == (Asset.BTC, Asset.ETH, Asset.SOL)
    assert config.notionals_usd == tuple(map(Decimal, ("100", "500", "1000", "5000", "10000")))
    assert config.entry_thresholds_bps == tuple(map(Decimal, ("0", "2", "5", "10", "20")))
    assert config.primary_thresholds_bps == (Decimal("5"), Decimal("10"))
    assert config.strict_book_age_ms == 500
    assert config.strict_receive_skew_ms == 250
    assert config.strict_index_divergence_bps == Decimal("10")
    assert config.episode_cooldown_seconds == 60


def test_verdict_values_are_stable() -> None:
    assert tuple(item.value for item in Verdict) == (
        "GO",
        "NO_GO",
        "INSUFFICIENT_EVIDENCE",
        "INVALID_DATASET",
    )
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
python -m unittest tests.shadow_economics.test_model tests.shadow_economics.test_config -v
```

Expected: import failure because `shadow_economics` does not exist.

- [ ] **Step 3: Implement immutable model/config contracts**

```python
class Asset(StrEnum):
    BTC = "BTC"
    ETH = "ETH"
    SOL = "SOL"


class Verdict(StrEnum):
    GO = "GO"
    NO_GO = "NO_GO"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    INVALID_DATASET = "INVALID_DATASET"


@dataclass(frozen=True, slots=True)
class DelayScenario:
    hyperliquid_ms: int
    lighter_ms: int


@dataclass(frozen=True, slots=True)
class AnalyzerConfig:
    schema: str
    assets: tuple[Asset, ...]
    notionals_usd: tuple[Decimal, ...]
    entry_thresholds_bps: tuple[Decimal, ...]
    primary_thresholds_bps: tuple[Decimal, ...]
    symmetric_delays: tuple[DelayScenario, ...]
    asymmetric_delays: tuple[DelayScenario, ...]
    strict_book_age_ms: int
    strict_receive_skew_ms: int
    strict_index_divergence_bps: Decimal
    diagnostic_book_age_ms: int
    diagnostic_receive_skew_ms: int
    diagnostic_index_divergence_bps: Decimal
    residual_limit_fraction: Decimal
    episode_cooldown_seconds: int
    minimum_complete_days: int
    minimum_healthy_fraction: Decimal
```

The loader must use duplicate-key-aware JSON parsing, require exact keys, decode all financial values from strings into finite `Decimal`, reject booleans as integers, and reject any value not exactly equal to the approved matrix.

- [ ] **Step 4: Add the exact committed scenario JSON**

The committed configuration must include all frozen notional, threshold, exit, funding, delay, capital, leverage, allocation, fee-case, quality, and verdict values from Global Constraints. It must contain no secret or account field.

- [ ] **Step 5: Run focused tests and static checks**

```bash
python -m unittest tests.shadow_economics.test_model tests.shadow_economics.test_config -v
python -m compileall -q multi_exchange_engine/shadow_economics tests/shadow_economics
python scripts/check-a2-boundary.py
```

Expected: all focused tests pass; A2 boundary remains green.

- [ ] **Step 6: Update handoff and commit**

```bash
git add multi_exchange_engine/shadow_economics config/shadow-economics-scenarios.json config/shadow-economics-fees.example.json tests/shadow_economics handoff.md
git commit -m "feat: freeze shadow economics contracts"
```

---

### Task 2: Define the common evidence contract and an in-memory reference reader

**Files:**
- Create: `multi_exchange_engine/shadow_economics/evidence.py`
- Create: `tests/shadow_economics/fixtures.py`
- Create: `tests/shadow_economics/test_evidence.py`
- Modify: `multi_exchange_engine/shadow_economics/__init__.py`
- Modify: `handoff.md`

**Interfaces:**
- Consumes: `Asset`, `AnalyzerConfig` from Task 1; immutable A2 types from `multi_exchange_engine.a2.model`, `a2.batch`, and `a2.universe`.
- Produces: `DatasetManifest`, `ControlEvidenceRecord`, `RawBatchRecord`, `QualityMinuteRecord`, `MappingSnapshot`, `FeeConfigBundle`, `EvidenceReader` protocol, `InMemoryEvidenceReader`.

- [ ] **Step 1: Write failing protocol/reader tests**

```python
from mee_contracts.shadow_economics.evidence import InMemoryEvidenceReader
from tests.shadow_economics.fixtures import make_minimal_evidence_bundle


def test_in_memory_reader_preserves_canonical_order() -> None:
    bundle = make_minimal_evidence_bundle()
    reader = InMemoryEvidenceReader(bundle)
    assert reader.read_manifest() == bundle.manifest
    assert tuple(item.batch_sequence for item in reader.iter_raw_batches()) == (0, 1)
    assert tuple(reader.iter_quality_minutes()) == bundle.quality_minutes
```

- [ ] **Step 2: Verify RED**

```bash
python -m unittest tests.shadow_economics.test_evidence -v
```

Expected: missing `evidence` module.

- [ ] **Step 3: Implement exact immutable evidence records**

```python
class EvidenceReader(Protocol):
    def read_manifest(self) -> DatasetManifest: ...
    def iter_control_evidence(self) -> Iterator[ControlEvidenceRecord]: ...
    def iter_raw_batches(self) -> Iterator[RawBatchRecord]: ...
    def iter_quality_minutes(self) -> Iterator[QualityMinuteRecord]: ...
    def read_mapping_snapshot(self) -> MappingSnapshot: ...
    def read_fee_configs(self) -> FeeConfigBundle: ...
```

Every record validates exact built-in types, UUIDs, lowercase SHA-256 digests, contiguous non-negative indexes, UTC nanosecond bounds, and immutable tuple contents. `RawBatchRecord` carries the stored compressed bytes plus both stored hashes; it does not decode eagerly.

- [ ] **Step 4: Implement test fixtures and reference reader**

`make_minimal_evidence_bundle()` must create two contiguous batches, one control record per venue, six mapping entries, deterministic quality minutes, and both fee cases without network or filesystem access.

- [ ] **Step 5: Run focused and regression tests**

```bash
python -m unittest tests.shadow_economics.test_evidence -v
python -m unittest tests.a2.test_model tests.a2.test_batch -v
python -m compileall -q multi_exchange_engine/shadow_economics tests/shadow_economics
```

- [ ] **Step 6: Update handoff and commit**

```bash
git add multi_exchange_engine/shadow_economics/evidence.py multi_exchange_engine/shadow_economics/__init__.py tests/shadow_economics handoff.md
git commit -m "feat: add shadow evidence reader contract"
```

---

### Task 3: Implement the immutable frozen-package format and tamper verification

**Files:**
- Create: `multi_exchange_engine/shadow_economics/frozen_package.py`
- Create: `tests/shadow_economics/test_frozen_package.py`
- Create: `tests/shadow_economics/integration/__init__.py`
- Create: `tests/shadow_economics/integration/test_frozen_replay.py`
- Modify: `handoff.md`

**Interfaces:**
- Consumes: `EvidenceReader` and evidence records from Task 2; canonical JSON/Decimal helpers from `multi_exchange_engine.shadow.tape_codec`; deterministic gzip profile from `multi_exchange_engine.a2.batch`.
- Produces: `write_frozen_package(reader, destination, analyzer_commit_sha, configuration_hash) -> FrozenPackageIdentity`; `FrozenPackageEvidenceReader`; `FrozenPackageError` with stable reason codes.

- [ ] **Step 1: Write failing round-trip and mutation tests**

```python
from pathlib import Path

from mee_contracts.shadow_economics.frozen_package import (
    FrozenPackageEvidenceReader,
    FrozenPackageError,
    write_frozen_package,
)


def test_frozen_package_round_trip_is_byte_stable(tmp_path: Path) -> None:
    reader = make_minimal_reader()
    first = write_frozen_package(reader, tmp_path / "a", "a" * 40, "b" * 64)
    second = write_frozen_package(reader, tmp_path / "b", "a" * 40, "b" * 64)
    assert first.manifest_sha256 == second.manifest_sha256
    assert (tmp_path / "a" / "manifest.json").read_bytes() == (tmp_path / "b" / "manifest.json").read_bytes()
    assert FrozenPackageEvidenceReader(tmp_path / "a").read_manifest() == reader.read_manifest()


def test_tampered_member_fails_before_iteration(tmp_path: Path) -> None:
    write_frozen_package(make_minimal_reader(), tmp_path / "pkg", "a" * 40, "b" * 64)
    member = next((tmp_path / "pkg" / "raw_batches").iterdir())
    member.write_bytes(member.read_bytes() + b"x")
    with self.assertRaisesRegex(FrozenPackageError, "MEMBER_HASH_MISMATCH"):
        FrozenPackageEvidenceReader(tmp_path / "pkg")
```

- [ ] **Step 2: Verify RED**

```bash
python -m unittest tests.shadow_economics.test_frozen_package -v
```

- [ ] **Step 3: Implement canonical package publication**

Required layout:

```text
manifest.json
raw_batches/
control_evidence/
quality_minutes/
mapping_snapshot.json
fee_configs/
funding_evidence/
checksums.sha256
```

Publication uses a sibling staging directory, canonical sorted paths, file fsync, directory fsync, and atomic final rename. Existing destination fails closed. Manifest hash excludes only its own `manifest_sha256` field and binds every member path, length, SHA-256, schema/version, run/time boundary, counts, collector/analyzer SHA, and configuration hash.

- [ ] **Step 4: Implement validating package reader**

The constructor validates the complete member set and hashes before exposing data. Iteration is bounded to one raw batch. Unknown files, symlinks, duplicate paths, path traversal, uppercase hashes, malformed gzip, unsupported versions, or inconsistent counts raise a typed `FrozenPackageError`.

- [ ] **Step 5: Run focused and integration tests**

```bash
python -m unittest tests.shadow_economics.test_frozen_package tests.shadow_economics.integration.test_frozen_replay -v
python -m compileall -q multi_exchange_engine/shadow_economics tests/shadow_economics
```

- [ ] **Step 6: Update handoff and commit**

```bash
git add multi_exchange_engine/shadow_economics/frozen_package.py tests/shadow_economics handoff.md
git commit -m "feat: add immutable shadow dataset package"
```

---

### Task 4: Add read-only PostgreSQL views, reader, and export CLI

**Files:**
- Create: `migrations/000003_shadow_economics_views.up.sql`
- Create: `migrations/000003_shadow_economics_views.down.sql`
- Create: `multi_exchange_engine/shadow_economics/postgres_reader.py`
- Create: `scripts/export-shadow-economics-dataset.py`
- Create: `tests/shadow_economics/test_postgres_reader.py`
- Create: `tests/shadow_economics/integration/test_postgres_reader.py`
- Modify: `handoff.md`

**Interfaces:**
- Consumes: current immutable A2 PostgreSQL schema/repository; Task 2 evidence records; Task 3 writer.
- Produces: `PostgresEvidenceReader.connect(dsn, run_id)`, exact read-only SQL views, export script producing a Task 3 package.

- [ ] **Step 1: Write failing static SQL and reader tests**

Tests must require:

- only `SELECT` grants for a new `shadow_economics_reader` `NOLOGIN` role;
- no `INSERT`, `UPDATE`, `DELETE`, `TRUNCATE`, function execution, or ownership;
- deterministic `ORDER BY` for batches, decoder evidence, quality minutes, controls, mappings, and lifecycle rows;
- `SET TRANSACTION READ ONLY` and repeatable-read snapshot in the Python reader;
- DSN redaction from `repr` and errors.

- [ ] **Step 2: Verify RED**

```bash
python -m unittest tests.shadow_economics.test_postgres_reader -v
```

- [ ] **Step 3: Implement views and role boundary**

Create views that expose only fields required by `EvidenceReader`. Do not add normalized books or economic columns to A2. The down migration revokes grants and drops only the views/role grants owned by this migration.

- [ ] **Step 4: Implement bounded reader and exporter**

```python
with PostgresEvidenceReader.connect(dsn, run_id) as reader:
    identity = write_frozen_package(
        reader,
        destination,
        analyzer_commit_sha=args.analyzer_commit_sha,
        configuration_hash=args.configuration_hash,
    )
```

The script accepts the DSN only through an existing bounded secret-file argument, never a command-line DSN value. It prints one canonical credential-free JSON result.

- [ ] **Step 5: Run PostgreSQL gates**

```bash
python -m unittest tests.shadow_economics.test_postgres_reader -v
A2_TEST_DATABASE_URL="$A2_TEST_DATABASE_URL" python -m unittest tests.shadow_economics.integration.test_postgres_reader -v
python scripts/check-a2-boundary.py
```

Expected: no skips in the binding PostgreSQL environment.

- [ ] **Step 6: Update handoff and commit**

```bash
git add migrations/000003_shadow_economics_views.* multi_exchange_engine/shadow_economics/postgres_reader.py scripts/export-shadow-economics-dataset.py tests/shadow_economics handoff.md
git commit -m "feat: expose read-only shadow evidence"
```

---

### Task 5: Define immutable reconstructed books and implement Hyperliquid reconstruction

**Files:**
- Create: `multi_exchange_engine/shadow_economics/reconstruction/__init__.py`
- Create: `multi_exchange_engine/shadow_economics/reconstruction/common.py`
- Create: `multi_exchange_engine/shadow_economics/reconstruction/hyperliquid.py`
- Create: `tests/shadow_economics/test_reconstruction_common.py`
- Create: `tests/shadow_economics/test_reconstruction_hyperliquid.py`
- Modify: `handoff.md`

**Interfaces:**
- Consumes: Task 2 `RawBatchRecord`/decoded frame evidence; existing `a2.hyperliquid_semantics` classification and raw provenance.
- Produces: `BookLevel`, `BookProvenance`, `ReconstructedBook`, `BookUpdateResult`, `HyperliquidBookReconstructor.apply(frame) -> BookUpdateResult`.

- [ ] **Step 1: Write failing book invariant tests**

```python
from decimal import Decimal


def test_reconstructed_book_rejects_crossed_levels() -> None:
    with self.assertRaisesRegex(ValueError, "crossed book"):
        ReconstructedBook(
            venue=Venue.HYPERLIQUID,
            market_id="BTC",
            bids=(BookLevel(Decimal("101"), Decimal("1")),),
            asks=(BookLevel(Decimal("100"), Decimal("1")),),
            source_time_ns=1,
            receive_time_ns=2,
            provenance=make_provenance(),
        )
```

- [ ] **Step 2: Write Hyperliquid fixture tests**

Cover snapshot publication, complete replacement semantics, level validation, source-time regression, reconnect epoch reset, unknown channel rejection, duplicate prices, non-finite strings, and raw batch/frame provenance.

- [ ] **Step 3: Verify RED**

```bash
python -m unittest tests.shadow_economics.test_reconstruction_common tests.shadow_economics.test_reconstruction_hyperliquid -v
```

- [ ] **Step 4: Implement immutable book types and Hyperliquid reconstructor**

Hyperliquid `l2Book` is treated as an authoritative complete snapshot. Every valid message replaces the current book for that market/connection epoch. Invalid or regressing source time closes publication until a later valid authoritative snapshot. Levels aggregate exact duplicate prices by summing exact quantities, then sort bids descending and asks ascending.

- [ ] **Step 5: Run focused and A2 semantic regressions**

```bash
python -m unittest tests.shadow_economics.test_reconstruction_common tests.shadow_economics.test_reconstruction_hyperliquid tests.a2.test_hyperliquid_semantics -v
python -m compileall -q multi_exchange_engine/shadow_economics tests/shadow_economics
```

- [ ] **Step 6: Update handoff and commit**

```bash
git add multi_exchange_engine/shadow_economics/reconstruction tests/shadow_economics handoff.md
git commit -m "feat: reconstruct Hyperliquid books"
```

---

### Task 6: Implement Lighter snapshot/delta reconstruction and gap recovery

**Files:**
- Create: `multi_exchange_engine/shadow_economics/reconstruction/lighter.py`
- Create: `tests/shadow_economics/test_reconstruction_lighter.py`
- Modify: `handoff.md`

**Interfaces:**
- Consumes: Task 5 common book types; existing `a2.lighter_semantics` observations and raw payloads.
- Produces: `LighterBookReconstructor.apply(frame) -> BookUpdateResult` with explicit `AWAITING_SNAPSHOT`, `VALID`, and `GAP_OPEN` state.

- [ ] **Step 1: Write failing snapshot/delta tests**

Cover:

- delta before snapshot publishes no book;
- snapshot with nonce establishes state;
- delta with matching `begin_nonce` applies updates and advances nonce;
- mismatch opens a gap and blocks later deltas;
- fresh snapshot recovers;
- zero quantity deletes a level;
- duplicate/out-of-order nonce fails closed;
- reconnect requires a new snapshot;
- malformed and crossed results publish no book.

- [ ] **Step 2: Verify RED**

```bash
python -m unittest tests.shadow_economics.test_reconstruction_lighter -v
```

- [ ] **Step 3: Implement deterministic delta semantics**

Maintain exact price-to-quantity maps only inside one `(boot_id, connection_epoch, market_id)`. Validate the entire update before mutating state. Apply zero-size deletion, aggregate no duplicate keys, sort only when publishing, and include the exact snapshot-plus-delta provenance range.

- [ ] **Step 4: Run focused and semantic regression tests**

```bash
python -m unittest tests.shadow_economics.test_reconstruction_lighter tests.a2.test_lighter_semantics -v
python -m compileall -q multi_exchange_engine/shadow_economics tests/shadow_economics
```

- [ ] **Step 5: Update handoff and commit**

```bash
git add multi_exchange_engine/shadow_economics/reconstruction/lighter.py tests/shadow_economics/test_reconstruction_lighter.py handoff.md
git commit -m "feat: reconstruct Lighter books"
```

---

### Task 7: Add evidence-bound mappings, index divergence, and canonical sizing

**Files:**
- Create: `multi_exchange_engine/shadow_economics/mapping.py`
- Create: `config/shadow-economics-mappings.json`
- Create: `tests/shadow_economics/test_mapping.py`
- Modify: `handoff.md`

**Interfaces:**
- Consumes: current reviewed A2 mapping registry/control evidence; Task 1 assets/config; Task 5 books.
- Produces: `EconomicMapping`, `MappingRegistry`, `IndexObservation`, `CanonicalSizing`, `load_mapping_registry(path, evidence)`, `calculate_canonical_sizing(...)`.

- [ ] **Step 1: Write failing mapping validation tests**

```python

def test_ticker_equality_without_reviewed_evidence_is_rejected() -> None:
    registry = MappingRegistry(())
    with self.assertRaisesRegex(MappingError, "MAPPING_NOT_REVIEWED"):
        registry.require_pair(Asset.BTC)


def test_canonical_sizing_rounds_down_and_limits_residual() -> None:
    sizing = calculate_canonical_sizing(
        target_usd=Decimal("1000"),
        reference_index=Decimal("100"),
        hyperliquid_step=Decimal("0.01"),
        lighter_step=Decimal("0.001"),
        hyperliquid_multiplier=Decimal("1"),
        lighter_multiplier=Decimal("1"),
    )
    assert sizing.target_base == Decimal("10")
    assert sizing.residual_fraction <= Decimal("0.0025")
```

- [ ] **Step 2: Verify RED**

```bash
python -m unittest tests.shadow_economics.test_mapping -v
```

- [ ] **Step 3: Implement exact mapping and sizing**

Each committed BTC/ETH/SOL entry includes venue symbol/ID, linear payoff, exact multiplier, displayed-size unit, quote/settlement assets, index/mark references, funding sign/schedule, tick/step/minimums, source evidence hashes, validity bounds, and review ID. Unknown or expired evidence fails closed.

Reference index is the deterministic midpoint of the two valid venue indexes at signal time. If either index is missing or divergence exceeds the selected gate, sizing is unavailable. Convert target USD to canonical base quantity, derive venue-native quantities, round toward lower exposure, calculate actual base/notional and residual-neutralization estimate, and reject residual above `0.0025`.

- [ ] **Step 4: Commit reviewed BTC/ETH/SOL mapping file**

The file must bind current official control-evidence hashes. Do not infer `kSHIB` or any other asset; the file contains exactly six venue-market records for BTC/ETH/SOL.

- [ ] **Step 5: Run focused and existing mapping tests**

```bash
python -m unittest tests.shadow_economics.test_mapping tests.a2.test_mapping_registry tests.a2.test_universe -v
```

- [ ] **Step 6: Update handoff and commit**

```bash
git add multi_exchange_engine/shadow_economics/mapping.py config/shadow-economics-mappings.json tests/shadow_economics/test_mapping.py handoff.md
git commit -m "feat: add shadow economic mappings"
```

---

### Task 8: Implement strict/diagnostic quality, delayed book lookup, and full-depth VWAP

**Files:**
- Create: `multi_exchange_engine/shadow_economics/quality.py`
- Create: `multi_exchange_engine/shadow_economics/vwap.py`
- Create: `tests/shadow_economics/test_quality.py`
- Create: `tests/shadow_economics/test_vwap.py`
- Modify: `handoff.md`

**Interfaces:**
- Consumes: Task 5/6 `ReconstructedBook`; Task 7 mapping/sizing; Task 1 config.
- Produces: `QualityReason`, `QualityDecision`, `evaluate_pair_quality(...)`, `DelayedBookIndex`, `SweepResult`, `sweep_vwap(...)`.

- [ ] **Step 1: Write failing boundary tests**

Test exact strict boundaries at `500 ms`, `250 ms`, `10 bps`, and `0.25%`; one unit above each fails strict. Test diagnostic boundaries at `1000 ms`, `500 ms`, and `25 bps`. Test missing depth returns `INSUFFICIENT_DEPTH` and never top-of-book fallback.

- [ ] **Step 2: Verify RED**

```bash
python -m unittest tests.shadow_economics.test_quality tests.shadow_economics.test_vwap -v
```

- [ ] **Step 3: Implement typed quality accumulation**

Evaluate all blockers and return a stable ordered tuple of reasons. Strict and diagnostic decisions are distinct values; no automatic downgrade may turn diagnostic into strict. Source-time age is evaluated only for mappings with verified timestamp semantics; receive-time age and skew are always retained.

- [ ] **Step 4: Implement delayed book lookup and exact sweeps**

```python
book = index.first_valid_at_or_after(
    venue=Venue.HYPERLIQUID,
    asset=Asset.BTC,
    target_receive_ns=signal_receive_ns + delay_ms * 1_000_000,
    mode=QualityMode.STRICT,
)
```

`sweep_vwap` validates every visible level before consuming any, consumes full requested canonical quantity, returns actual quantity/notional/VWAP/worst level/source checkpoint, and rejects insufficient depth.

- [ ] **Step 5: Run focused and legacy shadow regressions**

```bash
python -m unittest tests.shadow_economics.test_quality tests.shadow_economics.test_vwap tests.shadow.test_quality tests.shadow.test_vwap -v
```

- [ ] **Step 6: Update handoff and commit**

```bash
git add multi_exchange_engine/shadow_economics/quality.py multi_exchange_engine/shadow_economics/vwap.py tests/shadow_economics handoff.md
git commit -m "feat: add strict shadow VWAP gates"
```

---

### Task 9: Implement fee evidence and full failure-cost attribution

**Files:**
- Create: `multi_exchange_engine/shadow_economics/fees.py`
- Create: `tests/shadow_economics/test_fees.py`
- Modify: `multi_exchange_engine/shadow_economics/config.py`
- Modify: `handoff.md`

**Interfaces:**
- Consumes: Task 1 fee bundle/config; Task 8 sweep results.
- Produces: `VenueFeeSchedule`, `CostComponent`, `CostBreakdown`, `calculate_entry_costs`, `calculate_exit_costs`, `calculate_failure_costs`, `calculate_residual_cost`.

- [ ] **Step 1: Write failing provenance and cost tests**

Require exact venue, maker/taker role, rate, source URL/reference, verification/effective timestamps, scope, and lowercase evidence hash. Test operator absence yields `INSUFFICIENT_INPUT`; product case remains available. Test builder/partner fees are separate components and not silently merged into venue fees.

- [ ] **Step 2: Verify RED**

```bash
python -m unittest tests.shadow_economics.test_fees -v
```

- [ ] **Step 3: Implement versioned fee schedules and cost waterfall**

All rates are Decimal fractions. Cost calculation uses actual per-leg notional from the sweep, not target notional. Failure/rejection cost is zero only when evidence explicitly states no paid cost; unknown remains unknown and blocks strict verdict. Diagnostic infrastructure allocation is reported separately and never silently deducted from venue cash P&L.

- [ ] **Step 4: Run focused tests**

```bash
python -m unittest tests.shadow_economics.test_fees tests.shadow.test_provenance -v
```

- [ ] **Step 5: Update handoff and commit**

```bash
git add multi_exchange_engine/shadow_economics/fees.py multi_exchange_engine/shadow_economics/config.py tests/shadow_economics/test_fees.py handoff.md
git commit -m "feat: attribute shadow execution costs"
```

---

### Task 10: Implement independent episodes and price/basis simulation

**Files:**
- Create: `multi_exchange_engine/shadow_economics/episodes.py`
- Create: `multi_exchange_engine/shadow_economics/price_strategy.py`
- Create: `tests/shadow_economics/test_episodes.py`
- Create: `tests/shadow_economics/test_price_strategy.py`
- Modify: `handoff.md`

**Interfaces:**
- Consumes: Task 8 delayed books/VWAP/quality; Task 9 fees; Task 7 sizing; Task 1 scenario matrix.
- Produces: `OpportunityObservation`, `Episode`, `EpisodeTracker`, `PriceTradeSimulation`, `simulate_price_episode(...)`.

- [ ] **Step 1: Write failing episode tests**

Cover upward crossing, continuous episode, quality-invalid close, 60-second outside-signal cooldown, one active position per `asset × strategy × direction × size`, and signals during an open position counted only as observations.

- [ ] **Step 2: Write failing delayed entry/exit tests**

Create fixtures where signal-time spread is positive but the `300/300 ms` books erase it. Assert no scalar bps haircut is used. Cover fixed exits `1/5/15/60` minutes, relative convergence `50/75/90%`, absolute `1/2/5 bps`, primary `75% or 60 minutes`, full exit VWAP, and locked capital.

- [ ] **Step 3: Verify RED**

```bash
python -m unittest tests.shadow_economics.test_episodes tests.shadow_economics.test_price_strategy -v
```

- [ ] **Step 4: Implement deterministic episode tracker**

Episode IDs are domain-separated hashes of asset, strategy, direction, threshold, size, fee case, execution model, delay scenario, and first qualifying evidence identity. Iteration order is fixed and independent of dictionary insertion order.

- [ ] **Step 5: Implement price simulator**

For each counterfactual, fetch independent delayed entry books, sweep both legs, lock scenario capital, scan subsequent valid books for every exit family, sweep both exits, apply cost waterfall, and emit immutable gross/basis/cost/net records. Counterfactuals are never summed.

- [ ] **Step 6: Run focused tests**

```bash
python -m unittest tests.shadow_economics.test_episodes tests.shadow_economics.test_price_strategy -v
```

- [ ] **Step 7: Update handoff and commit**

```bash
git add multi_exchange_engine/shadow_economics/episodes.py multi_exchange_engine/shadow_economics/price_strategy.py tests/shadow_economics handoff.md
git commit -m "feat: simulate shadow basis episodes"
```

---

### Task 11: Implement funding evidence, realized cashflows, and funding simulations

**Files:**
- Create: `multi_exchange_engine/shadow_economics/funding.py`
- Create: `multi_exchange_engine/shadow_economics/funding_strategy.py`
- Create: `tests/shadow_economics/test_funding.py`
- Create: `tests/shadow_economics/test_funding_strategy.py`
- Modify: `handoff.md`

**Interfaces:**
- Consumes: raw market-stat/funding evidence through Task 2; mapping funding sign/schedule; Task 8/9 entry/exit economics.
- Produces: `FundingForecast`, `FundingSettlement`, `FundingCashflow`, `FundingEvidenceIndex`, `FundingTradeSimulation`.

- [ ] **Step 1: Write failing funding sign and settlement tests**

Cover long pays/receives and short receives/pays according to each venue's reviewed convention, unmatched forecast and settlement, duplicate settlement, ambiguous timestamp, notional at settlement, hourly/8h/annualized display-only conversion, and exact realized cashflow.

- [ ] **Step 2: Write failing rolling and settlement-aware simulation tests**

Cover `1/4/8/24h`, `1/2` realized settlements, `24h` maximum, forecast-known-at-entry filtering, forecast error, executable delayed exits, basis P&L, round-trip fees, and exclusion from strict verdict when settlement evidence is ambiguous.

- [ ] **Step 3: Verify RED**

```bash
python -m unittest tests.shadow_economics.test_funding tests.shadow_economics.test_funding_strategy -v
```

- [ ] **Step 4: Implement funding evidence index and cash accounting**

Forecast and realized records are different immutable types. Annualized values are projections only. Cashflow uses actual signed position notional at each venue settlement. No missing settlement is synthesized.

- [ ] **Step 5: Implement funding simulator**

Use ex-ante expected net carry for entry threshold and ex-post realized settlements for outcome. Price/basis P&L remains separate from funding cashflow in the output waterfall.

- [ ] **Step 6: Run focused tests**

```bash
python -m unittest tests.shadow_economics.test_funding tests.shadow_economics.test_funding_strategy -v
```

- [ ] **Step 7: Update handoff and commit**

```bash
git add multi_exchange_engine/shadow_economics/funding.py multi_exchange_engine/shadow_economics/funding_strategy.py tests/shadow_economics handoff.md
git commit -m "feat: simulate realized funding carry"
```

---

### Task 12: Implement constrained virtual portfolios and deterministic prioritization

**Files:**
- Create: `multi_exchange_engine/shadow_economics/portfolio.py`
- Create: `tests/shadow_economics/test_portfolio.py`
- Modify: `handoff.md`

**Interfaces:**
- Consumes: price and funding candidate simulations from Tasks 10/11; Task 1 capital matrix.
- Produces: `PortfolioConfig`, `VenueLedger`, `PortfolioState`, `BlockedOpportunity`, `PortfolioDiagnostic`, `rank_opportunities`, `simulate_portfolio`.

- [ ] **Step 1: Write failing capital and ranking tests**

Cover primary `20000`, `50/50`, `2x`, `50%` reserve; `5000/10000/50000` sensitivities; `60/40` and `40/60`; `1x/3x`; no instantaneous transfer; P&L retained on venue; margin insufficiency blocks entry; capital lock until exit; price/funding separate portfolios.

- [ ] **Step 2: Test deterministic ranking**

Ranking keys must be:

1. strict only;
2. higher expected net bps;
3. higher executable capacity;
4. lower data age/skew;
5. lower expected holding time;
6. `BTC`, `ETH`, `SOL`;
7. stable strategy/direction/config ID bytes.

Shuffle input repeatedly and require identical accepted/blocked output.

- [ ] **Step 3: Verify RED**

```bash
python -m unittest tests.shadow_economics.test_portfolio -v
```

- [ ] **Step 4: Implement venue ledgers and portfolio simulation**

Use exact balances, margin reservations, equity, realized/unrealized P&L, capital-hours, idle capital, utilization, blocked reasons, and optional non-binding rebalance events. A `3x`-only positive result is marked diagnostic.

- [ ] **Step 5: Run focused tests**

```bash
python -m unittest tests.shadow_economics.test_portfolio -v
```

- [ ] **Step 6: Update handoff and commit**

```bash
git add multi_exchange_engine/shadow_economics/portfolio.py tests/shadow_economics/test_portfolio.py handoff.md
git commit -m "feat: add shadow portfolio diagnostics"
```

---

### Task 13: Implement verdict gates, canonical artifacts, CLI, and fresh-process replay

**Files:**
- Create: `multi_exchange_engine/shadow_economics/verdict.py`
- Create: `multi_exchange_engine/shadow_economics/report.py`
- Create: `multi_exchange_engine/shadow_economics/cli.py`
- Create: `scripts/run-shadow-economics.py`
- Create: `tests/shadow_economics/test_verdict.py`
- Create: `tests/shadow_economics/test_report.py`
- Create: `tests/shadow_economics/test_cli.py`
- Create: `tests/shadow_economics/integration/test_deterministic_process_replay.py`
- Modify: `handoff.md`

**Interfaces:**
- Consumes: all prior simulation/portfolio outputs and frozen package identity.
- Produces: `StrategyVerdict`, `OverallVerdict`, `evaluate_strategy_verdict`, `evaluate_overall_verdict`, `write_report_artifacts`, CLI subcommands `preview`, `final-replay`, and `compare-replays`.

- [ ] **Step 1: Write failing verdict truth-table tests**

Cover:

- insufficient days/coverage -> `INSUFFICIENT_EVIDENCE`;
- package/config integrity failure -> `INVALID_DATASET`;
- sufficient evidence but failed primary gates -> `NO_GO`;
- exact `GO` conditions;
- operator fee missing blocks overall `GO`;
- maker-only or diagnostic-only positive output cannot issue `GO`;
- funding requires positive realized funding;
- single-trade concentration above `25%` fails;
- overall precedence exactly matches the design.

- [ ] **Step 2: Write failing canonical report tests**

Require exact output tree:

```text
dataset-manifest.json
analyzer-config.json
mapping-snapshot.json
coverage.json
quality-rejections.json
reconstructed-checkpoints.ndjson.gz
price-episodes.ndjson.gz
funding-episodes.ndjson.gz
price-matrix.json
funding-matrix.json
portfolio-diagnostics.json
latency-diagnostics.json
fee-and-failure-costs.json
verdict.json
report.md
checksums.sha256
```

Canonical JSON has sorted keys, exact Decimal strings, no floats, no timestamps from the host clock, and stable iteration. Markdown is a projection and cannot alter verdict data.

- [ ] **Step 3: Verify RED**

```bash
python -m unittest tests.shadow_economics.test_verdict tests.shadow_economics.test_report tests.shadow_economics.test_cli -v
```

- [ ] **Step 4: Implement verdict engine and canonical writer**

Every failed gate is emitted as an ordered typed reason. The report distinguishes `market_data_age`, `public_network_rtt`, and `execution_delay_assumption`; it never labels the first two order-to-fill latency.

- [ ] **Step 5: Implement CLI boundaries**

```text
preview --database-secret-file PATH --run-id UUID --output PATH
final-replay --package PATH --output PATH
compare-replays --first PATH --second PATH
```

`final-replay` performs no network or database access. It prints one canonical JSON terminal line containing status, verdict, terminal hash, output path, and no secret/config values.

- [ ] **Step 6: Prove fresh-process determinism**

The integration test invokes `final-replay` twice with fresh Python processes, different `PYTHONHASHSEED` values, hostile locale/timezone/Decimal environment, and separate output directories. It requires byte identity for every canonical artifact and matching terminal hash.

- [ ] **Step 7: Run focused tests**

```bash
python -m unittest tests.shadow_economics.test_verdict tests.shadow_economics.test_report tests.shadow_economics.test_cli tests.shadow_economics.integration.test_deterministic_process_replay -v
```

- [ ] **Step 8: Update handoff and commit**

```bash
git add multi_exchange_engine/shadow_economics scripts/run-shadow-economics.py tests/shadow_economics handoff.md
git commit -m "feat: produce deterministic shadow verdicts"
```

---

### Task 14: Add boundary, mutation, end-to-end, deployment, and sprint-run gates

**Files:**
- Create: `scripts/check-shadow-economics-boundary.py`
- Create: `tests/shadow_economics/test_boundary.py`
- Create: `tests/shadow_economics/integration/test_end_to_end_fixture.py`
- Modify: `.github/workflows/ci.yml` or the active Python/A2 CI workflow selected by repository inspection
- Modify: `Dockerfile.a2` only if the verify stage needs analyzer tests; production A2 image must not contain analyzer code
- Modify: `docs/validation.md`
- Modify: `docs/ROADMAP.md`
- Modify: `README.md`
- Modify: `handoff.md`

**Interfaces:**
- Consumes: all prior tasks.
- Produces: fail-closed static capability scan, full fixture replay gate, CI job, documented seven-day capture/freeze/replay procedure.

- [ ] **Step 1: Write failing boundary mutation tests**

The scanner must reject copied-package mutations containing:

- signer/private-key imports;
- account/private WebSocket selectors;
- order/cancel/transfer/withdraw methods;
- direct `aiohttp/httpx/websockets/socket` use in final-replay modules;
- A2 `INSERT/UPDATE/DELETE` SQL;
- credential environment names;
- imports from execution/order domains;
- direct mutation of A2 tables.

It must permit read-only psycopg in `postgres_reader.py`, filesystem reads in `frozen_package.py`, and pure use of existing shadow arithmetic.

- [ ] **Step 2: Verify RED**

```bash
python -m unittest tests.shadow_economics.test_boundary -v
```

- [ ] **Step 3: Implement AST/text boundary scanner**

Scan only production analyzer source and migration views. Emit canonical reason codes and paths, never source excerpts containing possible secrets. Success proves only capability absence, not profitability or correctness.

- [ ] **Step 4: Add an end-to-end fixture replay**

The fixture must cover both venues, BTC/ETH/SOL mappings, strict and diagnostic intervals, one gap/recovery, one insufficient-depth scenario, one profitable counterfactual, one losing counterfactual, funding forecast/settlement, capital blocking, and deterministic `NO_GO` or `INSUFFICIENT_EVIDENCE` chosen explicitly by the fixture. It must not require network or PostgreSQL.

- [ ] **Step 5: Add CI gates**

Run:

```bash
python scripts/check-a2-boundary.py
python scripts/check-shadow-economics-boundary.py
python -m unittest discover -s tests -v
python -m compileall -q multi_exchange_engine tests scripts
```

PostgreSQL matrix jobs run Task 4 integration tests against pinned PostgreSQL 16.11 and 17.7 with no skips. Final-replay tests run with network disabled where the CI runner supports it.

- [ ] **Step 6: Run full verification**

```bash
python scripts/check-a2-boundary.py
python scripts/check-shadow-economics-boundary.py
python -m unittest discover -s tests -v
python -m compileall -q multi_exchange_engine tests scripts
git diff --check
```

On Claw, additionally run the pinned PostgreSQL matrix, verify/prod image boundary, and fixture replay. Do not start public capture until these gates are green.

- [ ] **Step 7: Document the seven-day operating procedure**

Document:

1. build exact commit;
2. verify A2 and analyzer boundaries;
3. start/continue A2 public capture;
4. observe live preview without verdict authority;
5. close the available window at Day 7;
6. export frozen package;
7. verify package hashes;
8. run two fresh final replays;
9. compare bytes/hashes;
10. publish `GO`, `NO_GO`, `INSUFFICIENT_EVIDENCE`, or `INVALID_DATASET` with exact gate reasons.

- [ ] **Step 8: Update handoff and commit**

```bash
git add scripts/check-shadow-economics-boundary.py tests/shadow_economics .github Dockerfile.a2 docs README.md handoff.md
git commit -m "test: gate shadow economics sprint"
```

---

## Plan Self-Review Checklist

- [ ] Every approved design section maps to at least one task.
- [ ] No task adds private/trading capability.
- [ ] A2 remains raw evidence only.
- [ ] Root package placement is explicit; the parallel `src/` skeleton is untouched.
- [ ] Every task has a failing-test step, passing-test step, and coherent commit.
- [ ] Frozen parameters appear only in Global Constraints/config and are not tuned after evidence collection.
- [ ] Final verdict depends only on frozen-package replay.
- [ ] Price and funding reports remain separate.
- [ ] Diagnostic maker/3x/relaxed-quality results cannot issue `GO`.
- [ ] Operator fee absence blocks overall `GO` without private API use.
- [ ] Five-day/95% failure yields `INSUFFICIENT_EVIDENCE`, not `NO_GO`.
- [ ] Full-cycle entry/exit/funding/residual/rebalance/failure costs are attributable.
- [ ] Final artifacts are canonical and replayed twice in fresh processes.
- [ ] `handoff.md` is updated in every significant task commit.

## Execution Mode

Use **subagent-driven development** as the default: one fresh implementer per task, followed by task-scoped specification and code-quality review, with an independent final whole-branch review. Work on an isolated branch/worktree; never implement directly on `main`. Start with Task 1 only after pre-flight confirms the plan has no conflicts with the approved design and current repository invariants.
