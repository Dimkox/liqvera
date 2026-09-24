# M4 Evidence Runs and Frozen Data Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the PostgreSQL and Python M4 evidence authority for immutable capture, frozen-package, analysis, and retention roots with deterministic read and replay contracts.

**Architecture:** PostgreSQL owns run state, global logical-key admission, typed graph edges, writer serialization, terminal hashes, and privileges. Public Capture writes only through constrained security-definer functions; Read-Only Analyzer reads deterministic views or a hash-verified frozen package and writes only its separate `AnalysisRun`. Frozen package receipts and retention actions are independent immutable roots, so sealing, analysis, and retention never reopen or mutate capture evidence.

**Tech Stack:** PostgreSQL 16.11 and 17.7 (digest pinned), Python 3.12, psycopg 3, unittest, canonical JSON, SHA-256, Claw self-hosted validation.

## Global Constraints

- Implement requirements `DATA-001` through `DATA-025`; where M4 consumes exact arithmetic, reconstruction, mapping, VWAP, or strategy contracts owned by another milestone, preserve their typed provenance interfaces and fail closed rather than implement those algorithms here.
- PostgreSQL is the durable evidence authority; final analyzer replay authority is a verified frozen package recorded only under an `AnalysisRun`.
- Canonical semantic hashes include effective evidence time and exclude audit/insertion time.
- Runtime roles have no direct table DML, sequence privilege, ownership, inheritance, schema creation, or alternate mutation path.
- Capture admission and capture sealing lock the same unpartitioned `CaptureRun` row; no admission may commit across the seal.
- Logical-key uniqueness is enforced by one unpartitioned PostgreSQL authority, never a day partition or application pre-check.
- PostgreSQL 16.11 image is `postgres:16.11-alpine@sha256:4327b9fd295502f326f44153a1045a7170ddbfffed1c3829798328556cfd09e2`.
- PostgreSQL 17.7 image is `postgres:17.7-alpine@sha256:bb377b7239d2774ac8cc76f481596ce96c5a6b5e9d141f6d0a0ee371a6e7c0f2`.
- All RED and GREEN acceptance runs execute on `[self-hosted, claw]` against an exact checked-out SHA in a disposable per-run sandbox with isolated databases, credentials, networks, files, and evidence directories.
- The M6 Task 1 trusted exact-SHA disposable controller is a prerequisite to
  M4 Task 1 and supplies the sandbox/PR-identity receipt used by every M4 Claw
  run. M4 never bootstraps or weakens that controller.
- No M4 workflow may deploy, promote, mutate a registry, access private venue APIs, arm trading, use n8n, mount the host Docker socket inside test execution, or touch `/home/operator/app-stack`.
- Every task updates `handoff.md` in the same coherent commit after its checks pass; never commit credentials or generated test evidence.
- M6 release, promotion, app-stack, and deployment work is out of scope. Only
  the already completed M6 Task 1 validation controller is consumed. M4
  produces immutable schema, migration, test, frozen-package, `AnalysisRun`,
  and data-contract receipt interfaces for later M6 Tasks 2-5.

---

## File Structure

- `migrations/000003_evidence_roots_and_graph.up.sql`: unpartitioned roots, registries, global logical-key authority, typed graph contracts, and append-only guards.
- `migrations/000003_evidence_roots_and_graph.down.sql`: test/pre-release rollback that refuses after sealed roots exist.
- `migrations/000004_evidence_writers_and_readers.up.sql`: roles, constrained writers, seal functions, deterministic views, frozen receipt admission, and retention authority.
- `migrations/000004_evidence_writers_and_readers.down.sql`: test/pre-release rollback with sealed-evidence refusal.
- `packages/contracts/src/mee_contracts/evidence_graph.py`: immutable identifiers, node/edge kinds, run states, and canonical receipt types.
- `packages/contracts/src/mee_contracts/evidence.py`: sole deterministic PostgreSQL/frozen reader protocol created in M1 and extended only by compatible record types.
- `packages/contracts/src/mee_contracts/frozen_package.py`: frozen manifest/envelope schema and canonical hashing.
- `packages/public-capture/src/mee_public_capture/storage.py`: capture writer API backed only by approved SQL functions.
- `packages/public-capture/src/mee_public_capture/freeze.py`: pre-seal integrity validation and frozen package export.
- `packages/readonly-analyzer/src/mee_readonly_analyzer/readers/postgres.py`: deterministic read-only PostgreSQL reader.
- `packages/readonly-analyzer/src/mee_readonly_analyzer/readers/frozen.py`: semantic frozen-package reader with no network or host-clock dependency.
- `packages/readonly-analyzer/src/mee_readonly_analyzer/run_store.py`: separate AnalysisRun writer and seal API.
- `scripts/run-m4-postgres-tests.py`: clean-migration and zero-skip M4 test entry point.
- `scripts/run-deterministic-analysis.py`: fresh-process frozen replay command producing canonical bytes and an analysis terminal hash.
- `tests/m4/`: unit contract, canonical hash, frozen validation, and deterministic process tests.
- `tests/m4/integration/`: PostgreSQL schema, roles, writer, race, view, receipt, and retention tests.
- `.github/workflows/verify-m4-on-claw.yml`: exact-SHA disposable Claw PG16/17 matrix; no build, promotion, or deployment.

### Task 1: Define immutable evidence contracts

**Requirements:** `DATA-001..010`, `DATA-020`, `DATA-025`.

**Files:**
- Create: `packages/contracts/src/mee_contracts/evidence_graph.py`
- Modify: `packages/contracts/src/mee_contracts/evidence.py`
- Create: `packages/contracts/src/mee_contracts/frozen_package.py`
- Create: `tests/m4/test_contracts.py`
- Create: `tests/m4/test_canonical_hashes.py`
- Modify: `handoff.md`

**Interfaces:**
- Produces: `RunNamespace`, `RunState`, `NodeRef`, `LogicalKey`, `EvidenceEdge`, `CaptureTerminal`, `FrozenPackageReceipt`, `AnalysisTerminal`, and `RetentionReceipt` frozen dataclasses.
- Consumes without redefining: the sole `mee_contracts.evidence.EvidenceReader` from M1 with `read_capture_manifest`, `capture_terminal`, `iter_control_evidence`, `iter_raw_batches`, `iter_raw_envelopes`, `iter_quality_minutes`, and `read_mapping_snapshot`.
- Produces: immutable record types used by both concrete readers; PostgreSQL and frozen implementations must satisfy the same protocol and canonical ordering.
- Produces: `canonical_json_bytes(value: object) -> bytes` and `sha256_hex(value: bytes) -> str`.
- Consumes: no application, adapter, database driver, network, clock, or workflow implementation.

- [ ] **Step 1: Write the failing immutable-contract tests**

```python
def test_canonical_hash_ignores_audit_time_but_binds_effective_time() -> None:
    first = EvidenceEnvelope(RUN_ID, NODE_ID, "RAW_WIRE_BATCH", 10, 100, b"{}")
    second = replace(first, audit_time_ns=999)
    changed = replace(first, effective_time_ns=11)
    assert first.semantic_sha256 == second.semantic_sha256
    assert first.semantic_sha256 != changed.semantic_sha256

def test_contract_package_has_no_runtime_dependencies() -> None:
    forbidden = {"psycopg", "aiohttp", "requests", "websockets"}
    imported = set(importlib.metadata.requires("mee-contracts") or ())
    assert not any(name in requirement for name in forbidden for requirement in imported)
```

- [ ] **Step 2: Run the focused tests and confirm RED**

Run on Claw: `python -B -m unittest tests.m4.test_contracts tests.m4.test_canonical_hashes -v`

Expected: `ERROR` importing `mee_contracts.evidence_graph` or missing named types; no test is skipped.

- [ ] **Step 3: Implement the immutable types and canonical hash boundary**

```python
class RunNamespace(StrEnum):
    CAPTURE = "CAPTURE"
    PACKAGE = "PACKAGE"
    ANALYSIS = "ANALYSIS"
    RETENTION = "RETENTION"

@dataclass(frozen=True, slots=True)
class EvidenceEnvelope:
    capture_run_id: UUID
    node_id: UUID
    node_type: str
    effective_time_ns: int
    audit_time_ns: int
    payload: bytes

    @property
    def semantic_sha256(self) -> str:
        document = {
            "capture_run_id": str(self.capture_run_id),
            "effective_time_ns": self.effective_time_ns,
            "node_id": str(self.node_id),
            "node_type": self.node_type,
            "payload_sha256": hashlib.sha256(self.payload).hexdigest(),
            "schema_version": "mee-evidence-envelope/v1",
        }
        return hashlib.sha256(canonical_json_bytes(document)).hexdigest()
```

- [ ] **Step 4: Run GREEN checks**

Run: `python -B -m unittest tests.m4.test_contracts tests.m4.test_canonical_hashes -v`

Expected: all tests pass, zero skips.

- [ ] **Step 5: Update handoff and commit the contract boundary**

```bash
git add packages/contracts/src/mee_contracts tests/m4/test_contracts.py tests/m4/test_canonical_hashes.py handoff.md
git commit -m "feat(contracts): define immutable evidence graph types"
```

### Task 2: Add unpartitioned roots, registries, global keys, and typed edges

**Requirements:** `DATA-011..013`, `DATA-018`, `DATA-020`, `DATA-023..025`.

**Files:**
- Create: `migrations/000003_evidence_roots_and_graph.up.sql`
- Create: `migrations/000003_evidence_roots_and_graph.down.sql`
- Create: `tests/m4/integration/test_schema_postgres.py`
- Create: `tests/m4/integration/test_graph_constraints_postgres.py`
- Modify: `handoff.md`

**Interfaces:**
- Produces unpartitioned tables `evidence.capture_runs`, `frozen_package_receipts`, `analysis_runs`, `retention_actions`, `node_registry`, `logical_key_authority`, `edge_kind_contract`, and `evidence_edges`.
- Produces composite registry identity `(namespace, root_id, node_id, node_type)` for typed foreign keys.
- Produces globally authoritative logical-key identity `(scope_version, namespace, root_id, logical_key_sha256)`.

- [ ] **Step 1: Write schema tests for all roots and global authorities**

```python
def test_roots_and_authorities_are_unpartitioned(self) -> None:
    rows = self.connection.execute("""
        SELECT c.relname, c.relkind, pg_get_partkeydef(c.oid)
        FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname='evidence' AND c.relname = ANY(%s)
        ORDER BY c.relname
    """, (["capture_runs", "analysis_runs", "retention_actions",
            "node_registry", "logical_key_authority"],)).fetchall()
    self.assertEqual(len(rows), 5)
    self.assertTrue(all(row[1] == "r" and row[2] is None for row in rows))

def test_same_logical_key_cannot_cross_day_partitions(self) -> None:
    admit_raw(day="2026-08-10", key=KEY)
    with self.assertRaises(psycopg.errors.UniqueViolation):
        admit_raw(day="2026-08-11", key=KEY)
```

- [ ] **Step 2: Run the clean migration test and confirm RED**

Run: `A2_TEST_DATABASE_URL="$TEST_DATABASE_URL" python -B -m unittest tests.m4.integration.test_schema_postgres tests.m4.integration.test_graph_constraints_postgres -v`

Expected: failure because migration `000003` and schema `evidence` do not exist.

- [ ] **Step 3: Create root and registry tables**

```sql
CREATE SCHEMA evidence;
CREATE TYPE evidence.run_state AS ENUM ('OPEN','SEALING','SEALED','INVALID');
CREATE TABLE evidence.capture_runs (
  capture_run_id uuid PRIMARY KEY,
  collector_sha text NOT NULL CHECK (collector_sha ~ '^[0-9a-f]{40}$'),
  config_sha256 text NOT NULL CHECK (config_sha256 ~ '^[0-9a-f]{64}$'),
  state evidence.run_state NOT NULL DEFAULT 'OPEN',
  expected_counts jsonb, observed_counts jsonb, terminal_indices jsonb,
  terminal_epochs jsonb, canonical_start_ns bigint, canonical_end_ns bigint,
  graph_root_sha256 text, terminal_sha256 text UNIQUE,
  sealed_at_audit timestamptz,
  CHECK ((state='SEALED') = (terminal_sha256 IS NOT NULL))
);
CREATE TABLE evidence.node_registry (
  namespace text NOT NULL CHECK (namespace IN ('CAPTURE','PACKAGE','ANALYSIS','RETENTION')),
  root_id uuid NOT NULL,
  node_id uuid NOT NULL,
  node_type text NOT NULL,
  schema_version text NOT NULL,
  semantic_sha256 text NOT NULL CHECK (semantic_sha256 ~ '^[0-9a-f]{64}$'),
  effective_time_ns bigint NOT NULL,
  audit_time timestamptz NOT NULL DEFAULT statement_timestamp(),
  PRIMARY KEY(namespace, root_id, node_id),
  UNIQUE(namespace, root_id, node_id, node_type)
);
CREATE TABLE evidence.logical_key_authority (
  scope_version text NOT NULL,
  namespace text NOT NULL,
  root_id uuid NOT NULL,
  logical_key_sha256 text NOT NULL CHECK (logical_key_sha256 ~ '^[0-9a-f]{64}$'),
  node_id uuid NOT NULL,
  PRIMARY KEY(scope_version, namespace, root_id, logical_key_sha256),
  UNIQUE(namespace, root_id, node_id),
  FOREIGN KEY(namespace, root_id, node_id)
    REFERENCES evidence.node_registry(namespace, root_id, node_id)
);
```

- [ ] **Step 4: Add typed-edge and DAG constraints**

```sql
CREATE TABLE evidence.edge_kind_contract (
  edge_kind text NOT NULL, contract_version integer NOT NULL,
  source_namespace text NOT NULL, source_type text NOT NULL,
  target_namespace text NOT NULL, target_type text NOT NULL,
  allows_cross_root boolean NOT NULL,
  PRIMARY KEY(edge_kind, contract_version, source_namespace, source_type,
              target_namespace, target_type)
);
CREATE TABLE evidence.evidence_edges (
  edge_id uuid PRIMARY KEY, edge_kind text NOT NULL, contract_version integer NOT NULL,
  source_namespace text NOT NULL, source_root_id uuid NOT NULL,
  source_node_id uuid NOT NULL, source_type text NOT NULL,
  target_namespace text NOT NULL, target_root_id uuid NOT NULL,
  target_node_id uuid NOT NULL, target_type text NOT NULL,
  FOREIGN KEY(source_namespace,source_root_id,source_node_id,source_type)
    REFERENCES evidence.node_registry(namespace,root_id,node_id,node_type),
  FOREIGN KEY(target_namespace,target_root_id,target_node_id,target_type)
    REFERENCES evidence.node_registry(namespace,root_id,node_id,node_type),
  FOREIGN KEY(edge_kind,contract_version,source_namespace,source_type,
              target_namespace,target_type)
    REFERENCES evidence.edge_kind_contract(edge_kind,contract_version,
              source_namespace,source_type,target_namespace,target_type)
);
CREATE UNIQUE INDEX evidence_one_superseding_successor
ON evidence.evidence_edges(target_namespace,target_root_id,target_node_id)
WHERE edge_kind='supersedes';
```

Add a deferred constraint trigger that rejects undeclared cross-root edges and recursively rejects a `derived_from` or `supersedes` insertion when the target already reaches the source.

- [ ] **Step 5: Run GREEN schema and graph checks**

Run: `A2_TEST_DATABASE_URL="$TEST_DATABASE_URL" python -B -m unittest tests.m4.integration.test_schema_postgres tests.m4.integration.test_graph_constraints_postgres -v`

Expected: roots are unpartitioned; dangling/type-incompatible/cyclic/competing-successor edges and cross-partition duplicate keys are rejected; zero skips.

- [ ] **Step 6: Update handoff and commit schema authority**

```bash
git add migrations/000003_evidence_roots_and_graph.* tests/m4/integration/test_schema_postgres.py tests/m4/integration/test_graph_constraints_postgres.py handoff.md
git commit -m "feat(db): add global evidence graph authority"
```

### Task 3: Implement the sole capture writer and terminal race

**Requirements:** `DATA-001`, `DATA-011..016`, `DATA-019`.

**Files:**
- Create: `migrations/000004_evidence_writers_and_readers.up.sql`
- Create: `migrations/000004_evidence_writers_and_readers.down.sql`
- Create: `packages/public-capture/src/mee_public_capture/storage.py`
- Create: `tests/m4/integration/test_capture_writer_postgres.py`
- Create: `tests/m4/integration/test_capture_terminal_race_postgres.py`
- Modify: `handoff.md`

**Interfaces:**
- Produces SQL functions `evidence.admit_capture_node(...)` and `evidence.seal_capture_run(...)`.
- Produces Python `CaptureStore.admit(envelope, logical_key, edges) -> NodeRef` and `CaptureStore.seal(request: CaptureSealRequest) -> CaptureTerminal`.
- Consumes the pre-seal replay-integrity, lifecycle, soak, decoder-observation, and connection node types from Task 2 registry.

- [ ] **Step 1: Write direct-DML, atomicity, and post-seal failing tests**

```python
def test_runtime_role_cannot_bypass_writer(self) -> None:
    with self.connection.transaction(), self.connection.cursor() as cursor:
        cursor.execute("SET LOCAL ROLE mee_capture_runtime")
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            cursor.execute("""
                INSERT INTO evidence.node_registry
                  (namespace,root_id,node_id,node_type,schema_version,
                   semantic_sha256,effective_time_ns)
                VALUES ('CAPTURE',%s,%s,'RAW_WIRE_BATCH','v1',%s,1)
            """, (RUN_ID, NODE_ID, "0" * 64))

def test_failed_payload_admission_leaves_no_authority_rows(self) -> None:
    with self.assertRaises(psycopg.Error):
        self.call_admit(payload_sha256="0" * 64)
    self.assertEqual(self.count_registry_key_payload_edges(), (0, 0, 0, 0))
```

- [ ] **Step 2: Run writer tests and confirm RED**

Run: `A2_TEST_DATABASE_URL="$TEST_DATABASE_URL" python -B -m unittest tests.m4.integration.test_capture_writer_postgres tests.m4.integration.test_capture_terminal_race_postgres -v`

Expected: missing roles/functions and at least one direct-DML bypass on the old schema.

- [ ] **Step 3: Add least-privilege roles and sole-writer function**

```sql
CREATE ROLE mee_evidence_function_owner NOLOGIN NOINHERIT;
CREATE ROLE mee_capture_runtime NOLOGIN NOINHERIT;
REVOKE ALL ON ALL TABLES IN SCHEMA evidence FROM PUBLIC, mee_capture_runtime;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA evidence FROM PUBLIC, mee_capture_runtime;
GRANT USAGE ON SCHEMA evidence TO mee_capture_runtime;

CREATE FUNCTION evidence.admit_capture_node(
  p_capture_run_id uuid, p_node_id uuid, p_node_type text,
  p_schema_version text, p_logical_scope_version text,
  p_logical_key_sha256 text, p_semantic_sha256 text,
  p_effective_time_ns bigint, p_payload jsonb, p_edges jsonb
) RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog,evidence AS $$
DECLARE current_state evidence.run_state;
BEGIN
  SELECT state INTO STRICT current_state FROM evidence.capture_runs
    WHERE capture_run_id=p_capture_run_id FOR UPDATE;
  IF current_state <> 'OPEN' THEN
    RAISE EXCEPTION 'capture run is not open' USING ERRCODE='55000';
  END IF;
  INSERT INTO evidence.node_registry VALUES
    ('CAPTURE',p_capture_run_id,p_node_id,p_node_type,p_schema_version,
     p_semantic_sha256,p_effective_time_ns,statement_timestamp());
  INSERT INTO evidence.logical_key_authority VALUES
    (p_logical_scope_version,'CAPTURE',p_capture_run_id,p_logical_key_sha256,p_node_id);
  INSERT INTO evidence.capture_payloads
    (capture_run_id,node_id,payload,semantic_sha256)
    VALUES (p_capture_run_id,p_node_id,p_payload,p_semantic_sha256);
  PERFORM evidence.admit_declared_edges('CAPTURE',p_capture_run_id,p_node_id,p_edges);
  RETURN p_node_id;
END $$;
ALTER FUNCTION evidence.admit_capture_node(uuid,uuid,text,text,text,text,text,bigint,jsonb,jsonb)
  OWNER TO mee_evidence_function_owner;
REVOKE ALL ON FUNCTION evidence.admit_capture_node(uuid,uuid,text,text,text,text,text,bigint,jsonb,jsonb) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION evidence.admit_capture_node(uuid,uuid,text,text,text,text,text,bigint,jsonb,jsonb) TO mee_capture_runtime;
```

- [ ] **Step 4: Add capture seal closure and terminal hash**

`seal_capture_run` must lock the same `capture_runs` row `FOR UPDATE`, require state `OPEN`, verify required node types and expected/observed counts, calculate the canonical node-set and graph-root hashes inside the transaction, set `SEALING`, reject any missing closure, then set `SEALED` and persist the terminal hash. A retry with identical inputs returns the same terminal; altered inputs fail SQLSTATE `23514`.

- [ ] **Step 5: Add deterministic two-session race cases**

Use two psycopg connections and barriers for both schedules: admission holds the root lock before seal, and seal holds it before admission. Assert admission-first is included by the seal; seal-first makes admission fail `55000`; neither schedule leaves partial registry/key/payload/edge rows.

- [ ] **Step 6: Run GREEN writer and race checks**

Run: `A2_TEST_DATABASE_URL="$TEST_DATABASE_URL" python -B -m unittest tests.m4.integration.test_capture_writer_postgres tests.m4.integration.test_capture_terminal_race_postgres -v`

Expected: direct DML denied, atomic rollback proven, both race schedules pass, every post-seal capture write rejected, zero skips.

- [ ] **Step 7: Update handoff and commit writer authority**

```bash
git add migrations/000004_evidence_writers_and_readers.* packages/public-capture/src/mee_public_capture/storage.py tests/m4/integration/test_capture_writer_postgres.py tests/m4/integration/test_capture_terminal_race_postgres.py handoff.md
git commit -m "feat(db): serialize capture writes and terminalization"
```

### Task 4: Export and semantically verify frozen packages

**Requirements:** `DATA-003/004`, `DATA-015..017`, `DATA-020`.

**Files:**
- Create: `packages/public-capture/src/mee_public_capture/freeze.py`
- Create: `packages/readonly-analyzer/src/mee_readonly_analyzer/readers/frozen.py`
- Create: `tests/m4/test_frozen_package.py`
- Create: `tests/m4/test_frozen_semantic_validation.py`
- Create: `tests/m4/integration/test_frozen_receipt_postgres.py`
- Modify: `handoff.md`

**Interfaces:**
- Produces canonical `manifest.json`, `envelopes.ndjson`, `nodes.ndjson`, `edges.ndjson`, and `terminal.json` with a lexicographically sorted file digest table.
- Produces `verify_frozen_package(path: Path) -> VerifiedFrozenPackage`.
- Produces SQL `evidence.admit_frozen_package_receipt(...)` requiring the exact sealed capture terminal hash and complete node-set hash.

- [ ] **Step 1: Write tamper and closure RED tests**

```python
for mutation in (tamper_payload, tamper_mapping_hash, tamper_quality_hash,
                 duplicate_logical_key, change_epoch, change_index,
                 change_effective_time, remove_replay_integrity,
                 add_analysis_node_to_capture):
    with self.subTest(mutation=mutation.__name__):
        with self.assertRaises(FrozenPackageInvalid):
            verify_frozen_package(mutation(copy_fixture()))
```

- [ ] **Step 2: Run frozen tests and confirm RED**

Run: `python -B -m unittest tests.m4.test_frozen_package tests.m4.test_frozen_semantic_validation -v`

Expected: import/missing-validator errors; no mutation is accepted or skipped.

- [ ] **Step 3: Implement canonical export**

```python
def write_canonical_ndjson(path: Path, rows: Iterable[Mapping[str, object]]) -> str:
    digest = hashlib.sha256()
    with path.open("xb") as stream:
        for row in rows:
            encoded = canonical_json_bytes(row) + b"\n"
            stream.write(encoded)
            digest.update(encoded)
    return digest.hexdigest()
```

Export only after loading a sealed terminal and verifying required capture closure. Write into a new temporary directory, fsync files and directory, rename once, and refuse overwrite.

- [ ] **Step 4: Implement complete semantic verification**

Parse every raw envelope; recompute payload, mapping, quality, manifest, file, node-set, graph-root, and package hashes; validate run, venue, epoch, batch/index/sequence, source/effective/receive time, counts, logical-key uniqueness, lifecycle, soak, decoder, connection, and pre-seal replay-integrity closure. Reject unknown schemas, noncanonical JSON, an analysis-owned node, or any missing/extra node/edge.

- [ ] **Step 5: Bind receipt admission to exact sealed capture state**

```sql
CREATE FUNCTION evidence.admit_frozen_package_receipt(
 p_receipt_id uuid, p_capture_run_id uuid, p_capture_terminal_sha256 text,
 p_manifest_sha256 text, p_package_sha256 text, p_node_set_sha256 text,
 p_object_uri text, p_verifier_identity text
) RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,evidence AS $$
BEGIN
  PERFORM 1 FROM evidence.capture_runs
   WHERE capture_run_id=p_capture_run_id AND state='SEALED'
     AND terminal_sha256=p_capture_terminal_sha256 FOR SHARE;
  IF NOT FOUND THEN RAISE EXCEPTION 'capture terminal mismatch' USING ERRCODE='23503'; END IF;
  INSERT INTO evidence.frozen_package_receipts
    (receipt_id,capture_run_id,capture_terminal_sha256,manifest_sha256,
     package_sha256,node_set_sha256,object_uri,verifier_identity,status)
  VALUES (p_receipt_id,p_capture_run_id,p_capture_terminal_sha256,p_manifest_sha256,
          p_package_sha256,p_node_set_sha256,p_object_uri,p_verifier_identity,'VERIFIED');
  RETURN p_receipt_id;
END $$;
```

- [ ] **Step 6: Run GREEN frozen and receipt checks**

Run: `A2_TEST_DATABASE_URL="$TEST_DATABASE_URL" python -B -m unittest tests.m4.test_frozen_package tests.m4.test_frozen_semantic_validation tests.m4.integration.test_frozen_receipt_postgres -v`

Expected: pristine package passes; every mutation and terminal/node-set mismatch fails closed; zero skips.

- [ ] **Step 7: Update handoff and commit frozen authority**

```bash
git add packages/public-capture/src/mee_public_capture/freeze.py packages/readonly-analyzer/src/mee_readonly_analyzer/readers/frozen.py tests/m4/test_frozen_package.py tests/m4/test_frozen_semantic_validation.py tests/m4/integration/test_frozen_receipt_postgres.py handoff.md
git commit -m "feat(data): verify frozen capture packages"
```

### Task 5: Add deterministic views and prove the Analyzer role is read-only

**Requirements:** `DATA-003`, `DATA-021/022`, `SEC-002`.

**Files:**
- Modify: `migrations/000004_evidence_writers_and_readers.up.sql`
- Create: `packages/readonly-analyzer/src/mee_readonly_analyzer/readers/postgres.py`
- Create: `tests/m4/integration/test_deterministic_view_postgres.py`
- Create: `tests/m4/integration/test_analyzer_grants_postgres.py`
- Modify: `handoff.md`

**Interfaces:**
- Produces `evidence.capture_reader_v1`, ordered only by canonical fields.
- Analyzer receives only database `CONNECT`, schema `USAGE`, and named-view `SELECT`.
- Produces `PostgresEvidenceReader(connection).iter_raw_envelopes(run_id)` matching `FrozenPackageEvidenceReader.iter_raw_envelopes(run_id)` bytes and ordering under the sole contracts protocol.

- [ ] **Step 1: Write catalog and mutation denial tests**

```python
def test_analyzer_has_only_declared_privileges(self) -> None:
    self.assertEqual(actual_privileges("mee_analysis_runtime"), {
        ("DATABASE", self.database_name, "CONNECT"),
        ("SCHEMA", "evidence", "USAGE"),
        ("VIEW", "evidence.capture_reader_v1", "SELECT"),
    })

for statement in ("INSERT INTO evidence.node_registry(namespace,root_id,node_id,node_type,schema_version,semantic_sha256,effective_time_ns) VALUES ('CAPTURE','00000000-0000-0000-0000-000000000001','00000000-0000-0000-0000-000000000002','RAW_WIRE_BATCH','v1',repeat('0',64),1)",
                  "SELECT evidence.admit_capture_node('00000000-0000-0000-0000-000000000001','00000000-0000-0000-0000-000000000002','RAW_WIRE_BATCH','v1','capture/v1',repeat('0',64),repeat('1',64),1,'{}'::jsonb,'[]'::jsonb)",
                  "SELECT nextval('evidence.any_sequence')",
                  "CREATE TABLE evidence.bypass(id int)",
                  "SET ROLE mee_capture_runtime"):
    with self.assertRaises(psycopg.Error):
        execute_as_analyzer(statement)
```

- [ ] **Step 2: Run view/role tests and confirm RED**

Run: `A2_TEST_DATABASE_URL="$TEST_DATABASE_URL" python -B -m unittest tests.m4.integration.test_deterministic_view_postgres tests.m4.integration.test_analyzer_grants_postgres -v`

Expected: missing view/role and privilege-set mismatch.

- [ ] **Step 3: Create the deterministic security-barrier view**

```sql
CREATE VIEW evidence.capture_reader_v1 WITH (security_barrier=true) AS
SELECT r.capture_run_id,n.node_id,n.node_type,n.schema_version,
       n.effective_time_ns,n.semantic_sha256,p.payload
FROM evidence.capture_runs r
JOIN evidence.node_registry n
  ON n.namespace='CAPTURE' AND n.root_id=r.capture_run_id
JOIN evidence.capture_payloads p
  ON p.capture_run_id=r.capture_run_id AND p.node_id=n.node_id
WHERE r.state='SEALED';
```

The Python reader issues an explicit `ORDER BY effective_time_ns,node_type,node_id`; audit timestamps are never an ordering or hash input.

- [ ] **Step 4: Apply exact Analyzer grants and default revocations**

```sql
CREATE ROLE mee_analysis_runtime NOLOGIN NOINHERIT;
REVOKE ALL ON SCHEMA evidence FROM PUBLIC,mee_analysis_runtime;
REVOKE ALL ON ALL TABLES IN SCHEMA evidence FROM PUBLIC,mee_analysis_runtime;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA evidence FROM PUBLIC,mee_analysis_runtime;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA evidence FROM PUBLIC,mee_analysis_runtime;
DO $grant$
BEGIN
  EXECUTE format('GRANT CONNECT ON DATABASE %I TO mee_analysis_runtime',
                 current_database());
END $grant$;
GRANT USAGE ON SCHEMA evidence TO mee_analysis_runtime;
GRANT SELECT ON evidence.capture_reader_v1 TO mee_analysis_runtime;
ALTER DEFAULT PRIVILEGES FOR ROLE mee_evidence_function_owner IN SCHEMA evidence
  REVOKE ALL ON TABLES FROM PUBLIC;
ALTER DEFAULT PRIVILEGES FOR ROLE mee_evidence_function_owner IN SCHEMA evidence
  REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;
```

- [ ] **Step 5: Run GREEN view, byte-parity, and denial checks**

Run: `A2_TEST_DATABASE_URL="$TEST_DATABASE_URL" python -B -m unittest tests.m4.integration.test_deterministic_view_postgres tests.m4.integration.test_analyzer_grants_postgres -v`

Expected: exact privilege set matches; all mutation/bypass attempts fail; PostgreSQL and frozen readers return identical canonical envelopes; zero skips.

- [ ] **Step 6: Update handoff and commit read boundary**

```bash
git add migrations/000004_evidence_writers_and_readers.up.sql packages/readonly-analyzer/src/mee_readonly_analyzer/readers/postgres.py tests/m4/integration/test_deterministic_view_postgres.py tests/m4/integration/test_analyzer_grants_postgres.py handoff.md
git commit -m "feat(db): expose deterministic read-only evidence view"
```

### Task 6: Create and deterministically seal separate AnalysisRuns

**Requirements:** `DATA-004/005/010`, `DATA-016`, `DATA-019/020`, `DATA-023/025`.

**Files:**
- Modify: `migrations/000004_evidence_writers_and_readers.up.sql`
- Create: `packages/readonly-analyzer/src/mee_readonly_analyzer/run_store.py`
- Create: `scripts/run-deterministic-analysis.py`
- Create: `tests/m4/integration/test_analysis_run_postgres.py`
- Create: `tests/m4/test_deterministic_analysis_process.py`
- Modify: `handoff.md`

**Interfaces:**
- Produces `create_analysis_run(capture_run_id, receipt_id, artifact_digest, code_sha, config_sha256) -> UUID`.
- Produces analysis-only writer and `seal_analysis_run(...) -> AnalysisTerminal`.
- Produces `analysis-replay-receipt/v1` containing frozen package digest, capture terminal, analyzer artifact/code/config identities, output digest, graph root, terminal hash, process receipt hashes, and outcome.

- [ ] **Step 1: Write isolation and fresh-process RED tests**

```python
def test_analysis_never_adds_capture_nodes(self) -> None:
    before = capture_node_count(RUN_ID)
    analyze_verified_package(PACKAGE)
    self.assertEqual(capture_node_count(RUN_ID), before)

def test_two_fresh_processes_are_byte_identical(self) -> None:
    first = run_process(PACKAGE, env={"NO_NETWORK": "1", "HOST_CLOCK": "deny"})
    second = run_process(PACKAGE, env={"NO_NETWORK": "1", "HOST_CLOCK": "deny"})
    self.assertEqual(first.stdout, second.stdout)
    self.assertEqual(receipt(first).analysis_terminal_sha256,
                     receipt(second).analysis_terminal_sha256)
```

- [ ] **Step 2: Run analysis tests and confirm RED**

Run: `A2_TEST_DATABASE_URL="$TEST_DATABASE_URL" python -B -m unittest tests.m4.integration.test_analysis_run_postgres tests.m4.test_deterministic_analysis_process -v`

Expected: missing AnalysisRun functions/command or differing/unavailable terminal receipt.

- [ ] **Step 3: Implement analysis root creation and writer isolation**

Require an exact sealed capture plus verified receipt pair before inserting `analysis_runs`. The analysis writer accepts only `ANALYSIS` node kinds and only declared cross-root input edges; its security-definer owner and grants are distinct from Capture. No function updates `capture_runs`, capture registry rows, or frozen receipts.

- [ ] **Step 4: Implement canonical analysis sealing and process receipt**

```python
terminal_document = {
    "analysis_run_id": str(run_id),
    "analyzer_artifact_digest": artifact_digest,
    "analyzer_code_sha": code_sha,
    "capture_terminal_sha256": capture_terminal_sha256,
    "config_sha256": config_sha256,
    "frozen_package_sha256": package_sha256,
    "graph_root_sha256": graph_root_sha256,
    "observed_counts": observed_counts,
    "output_sha256": hashlib.sha256(output_bytes).hexdigest(),
    "schema_version": "analysis-terminal/v1",
}
analysis_terminal_sha256 = sha256_hex(canonical_json_bytes(terminal_document))
```

The command accepts all identity/time inputs explicitly, disables socket creation through the test harness, rejects calls to system time, emits canonical bytes to stdout, and writes the receipt to a caller-selected new path.

- [ ] **Step 5: Run GREEN analysis isolation and determinism checks**

Run twice in separate disposable processes: `python -B scripts/run-deterministic-analysis.py --package "$PACKAGE" --analysis-run-id "$RUN_ID" --artifact-digest "$ARTIFACT_DIGEST" --code-sha "$TARGET_SHA" --config-sha256 "$CONFIG_SHA256" --receipt "$RECEIPT"`

Expected: both runs exit 0; `cmp` of canonical outputs succeeds; terminal hashes match; CaptureRun row/node counts and hashes are unchanged.

- [ ] **Step 6: Update handoff and commit AnalysisRun authority**

```bash
git add migrations/000004_evidence_writers_and_readers.up.sql packages/readonly-analyzer/src/mee_readonly_analyzer/run_store.py scripts/run-deterministic-analysis.py tests/m4/integration/test_analysis_run_postgres.py tests/m4/test_deterministic_analysis_process.py handoff.md
git commit -m "feat(analyzer): seal isolated deterministic analysis runs"
```

### Task 7: Gate retention through a verified receipt and separate RetentionAction

**Requirements:** `DATA-017`, `DATA-024/025`.

**Files:**
- Modify: `migrations/000004_evidence_writers_and_readers.up.sql`
- Create: `tests/m4/integration/test_retention_action_postgres.py`
- Modify: `handoff.md`

**Interfaces:**
- Produces `evidence.plan_retention_action(...)` and `evidence.apply_retention_action(...)` under `mee_retention_runtime`.
- Produces `retention-receipt/v1` with capture terminal, frozen receipt/package hashes, authorization identity, exact affected objects, result, and evidence hash.
- Replaces direct eligibility of `a2.drop_expired_raw_partitions`; no raw object becomes unavailable without the new authority.

- [ ] **Step 1: Write retention refusal and immutability tests**

```python
for missing in ("sealed_capture", "verified_receipt", "retrievable_object",
                "independent_closure_check", "authorization"):
    with self.subTest(missing=missing), self.assertRaises(psycopg.Error):
        apply_retention_fixture(without=missing)
self.assertEqual(capture_snapshot_after(), capture_snapshot_before())
self.assertEqual(analysis_snapshot_after(), analysis_snapshot_before())
```

- [ ] **Step 2: Run retention tests and confirm RED**

Run: `A2_TEST_DATABASE_URL="$TEST_DATABASE_URL" python -B -m unittest tests.m4.integration.test_retention_action_postgres -v`

Expected: old partition-drop path succeeds without a frozen receipt or no RetentionAction API exists.

- [ ] **Step 3: Implement retention plan/apply functions**

`plan_retention_action` inserts immutable intent after locking and validating the sealed capture/verified receipt pair. `apply_retention_action` requires `PLANNED`, verifies retrievability and independent closure evidence supplied by immutable hashes, records the sorted exact partition/object list, performs only those mutations, and atomically seals the action as `APPLIED` with `retention_evidence_sha256`; failure records no partial drop or false success.

- [ ] **Step 4: Revoke the legacy bypass**

Revoke `a2_maintainer` execution of `a2.drop_expired_raw_partitions`, remove it from runtime reachability, and add a migration assertion that no runtime role can execute a raw drop/detach/truncate function except `evidence.apply_retention_action`.

- [ ] **Step 5: Run GREEN retention checks**

Run: `A2_TEST_DATABASE_URL="$TEST_DATABASE_URL" python -B -m unittest tests.m4.integration.test_retention_action_postgres -v`

Expected: every missing prerequisite fails without mutation; authorized exact objects are affected once; retry is idempotent; capture/analysis roots remain byte-for-byte unchanged; zero skips.

- [ ] **Step 6: Update handoff and commit retention authority**

```bash
git add migrations/000004_evidence_writers_and_readers.up.sql tests/m4/integration/test_retention_action_postgres.py handoff.md
git commit -m "feat(db): authorize retention through frozen receipts"
```

### Task 8: Bind clean PostgreSQL 16/17 and exact-SHA Claw acceptance

**Requirements:** `DATA-021` and verification of all M4-applicable `DATA-001..025`.

**Files:**
- Create: `scripts/run-m4-postgres-tests.py`
- Create: `.github/workflows/verify-m4-on-claw.yml`
- Create: `tests/m4/test_claw_workflow_contract.py`
- Create: `tests/m4/test_m4_receipt.py`
- Modify: `handoff.md`

**Interfaces:**
- Consumes the exact successful M6 Task 1 trusted-controller/sandbox receipt;
  missing, mismatched, or non-default-branch controller identity blocks M4.
- Produces one `m4-data-contract-receipt/v1` per PostgreSQL major and one aggregate receipt keyed to exact source SHA.
- Receipt fields: repository, source SHA, migration hashes, PostgreSQL image digest/version, test command, test count, skip count, schema hash, grant hash, frozen fixture/package hash, deterministic replay receipt hash, run/attempt/job identity, start/end UTC audit times, outcome, and cleanup outcome.
- M6 may consume these receipt hashes but cannot alter or synthesize them.

- [ ] **Step 1: Write workflow and receipt contract tests**

```python
def test_workflow_is_claw_only_and_non_deploying() -> None:
    workflow = WORKFLOW.read_text()
    self.assertIn("runs-on: [self-hosted, claw]", workflow)
    for forbidden in ("ubuntu-", "push:", "docker.sock", "app-stack",
                      "registry", "promote", "deploy", "secrets."):
        self.assertNotIn(forbidden, workflow)

def test_receipt_binds_exact_database_and_source() -> None:
    self.assertEqual(receipt["source_sha"], os.environ["TARGET_SHA"])
    self.assertEqual(receipt["skip_count"], 0)
    self.assertRegex(receipt["postgres_image"], r"@sha256:[0-9a-f]{64}$")
```

- [ ] **Step 2: Run the contract test and confirm RED**

Run: `python -B -m unittest tests.m4.test_claw_workflow_contract tests.m4.test_m4_receipt -v`

Expected: missing workflow/runner/receipt implementation.

- [ ] **Step 3: Implement the zero-skip clean-migration runner**

```python
if not database_url or not expected_postgres_major:
    return 2
os.environ["A2_TEST_DATABASE_URL"] = database_url
os.environ["M4_TEST_DATABASE_URL"] = database_url
apply_all_migrations(database_url)
assert server_major(database_url) == expected_postgres_major
result = unittest.TextTestRunner(verbosity=2).run(load_m4_integration_suite())
if result.skipped:
    raise SystemExit(f"M4 gate rejects {len(result.skipped)} skipped tests")
write_canonical_receipt(result, schema_hash(database_url), grants_hash(database_url))
raise SystemExit(0 if result.wasSuccessful() else 1)
```

- [ ] **Step 4: Implement the disposable Claw matrix**

The default-branch-controlled workflow validates same-repository PR metadata and exact 40-hex SHA, checks out with `persist-credentials: false`, asserts `git rev-parse HEAD`, creates a unique sandbox/network/database/evidence directory per run-attempt-major, uses the two Global Constraint image digests, supplies per-run credentials, executes only M4 tests, uploads non-secret receipts, and always removes its database/network/files. The inner test environment has no host Docker socket, production route, release credential, or deployment authority.

- [ ] **Step 5: Run the complete RED gate on exact pre-implementation SHA**

Run on Claw for both matrix entries:

```bash
test "$(git rev-parse HEAD)" = "$TARGET_SHA"
python -B scripts/run-m4-postgres-tests.py \
  --database-url "$M4_TEST_DATABASE_URL" \
  --expected-postgres-major "$POSTGRES_MAJOR" \
  --receipt "$EVIDENCE_DIR/m4-$POSTGRES_MAJOR.json"
```

Expected before Tasks 1–7: nonzero exit due to missing migrations/contracts, never a skipped or unavailable-service pass.

- [ ] **Step 6: Run the complete GREEN gate on the implementation SHA**

Run the same exact commands for PG16 and PG17 after Tasks 1–7.

Expected: both clean databases apply the full migration chain; schema, role/grant, writer, concurrency, terminal-race, deterministic-view, frozen-reader, AnalysisRun, and retention suites pass with zero skips; both receipts bind the same exact source SHA and their respective pinned image digests.

- [ ] **Step 7: Run final non-database M4 verification**

Run: `python -B -m unittest discover -s tests/m4 -t . -v && python -m compileall -q packages scripts tests/m4 && git diff --check`

Expected: all M4 tests pass with only explicitly database-gated tests absent from this non-database invocation, compilation succeeds, and `git diff --check` emits no output.

- [ ] **Step 8: Record independent verification, update handoff, and commit the gate**

Record named data-engineering and security/grant reviews with exact receipt hashes. Then:

```bash
git add scripts/run-m4-postgres-tests.py .github/workflows/verify-m4-on-claw.yml tests/m4/test_claw_workflow_contract.py tests/m4/test_m4_receipt.py handoff.md
git commit -m "ci: bind M4 data contract to Claw PostgreSQL matrix"
```

## Final Handoff Gate

- [ ] Confirm every M4-applicable `DATA-001..025` requirement maps to a named test and immutable receipt field.
- [ ] Confirm no root, registry, logical key, payload, edge, receipt, analysis, or retention object can be mutated after its terminal state.
- [ ] Confirm Capture, Package, Analysis, and Retention have distinct root IDs, logical-key scopes, writer functions, grants, and typed cross-root edges.
- [ ] Confirm two fresh analyzer processes over one verified package emit byte-identical canonical output and matching analysis terminal hashes without network or host clock.
- [ ] Confirm PostgreSQL 16 and 17 receipts both bind the exact implementation SHA, full clean migration chain, zero skips, schema/grant hashes, and deterministic replay receipt.
- [ ] Confirm the only M6-facing outputs are immutable artifact-neutral receipt interfaces; this plan does not build, scan, promote, release, or deploy.
- [ ] Confirm `handoff.md` names the exact completed commit, checks, receipt locations/hashes, independent reviewers, unresolved blockers, and next authorized action.

Implementation is complete only when every checkbox above has real exact-SHA evidence. A green local command, existing workflow file, historical PG run, or placeholder receipt is not completion evidence.
