# Claw Host Inventory Evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a read-only Claw inventory observation that closes the pre-mutation owner tuple without granting host authority.

**Architecture:** A stdlib Python collector emits a canonical closed JSON observation from fixed read-only commands. A separate verifier checks schema and runtime bindings; a repository-dispatch workflow executes only at GitHub's authenticated default-branch identity, emits exact verified bytes through the run log, and always removes local evidence.

**Tech Stack:** Python 3 stdlib, GitHub Actions, Bash, JSON Schema, pytest, architecture graph.

## Global Constraints

- No `sudo`, package/service mutation, container mutation, app-stack write, credential enumeration, environment dump, or secret output.
- `authority=NONE`, `status=HOST_INVENTORY_OBSERVED`, and `not_host_receipt=true` are immutable.
- Safe policy mismatches are evidence, not schema errors: emit a sorted closed
  `preflight_blockers` list and forbid host apply while it is non-empty.
- Third-party actions use the repository's existing exact commit pins.
- Every new tracked path is graph-inventoried and HOST-001 scoped.

---

### Task 1: Closed observation contract

**Files:**
- Create: `schemas/claw-host-inventory-observation-v1.schema.json`
- Create: `scripts/collect_claw_host_inventory.py`
- Create: `scripts/verify_claw_host_inventory.py`
- Test: `tests/release/test_claw_host_inventory.py`

**Interfaces:**
- Collector: `python -m scripts.collect_claw_host_inventory --policy PATH --output PATH` plus explicit GitHub controller/run arguments.
- Verifier: `python -m scripts.verify_claw_host_inventory --observation PATH` plus the same expected identity arguments.

- [x] Write tests for closed fields, duplicate/extra rejection, payload digest,
      exact engine/app projections, fixed paths, subid overlap and secret-field
      rejection.
- [x] Run `python -B -m pytest tests/release/test_claw_host_inventory.py -q`
      and confirm collection fails because modules/schema do not exist.
- [x] Implement the minimal collector, verifier and schema using fixed argv and
      canonical JSON.
- [x] Re-run the focused test and require all cases to pass.

### Task 2: Trusted read-only workflow

**Files:**
- Create: `.github/workflows/observe-claw-host-inventory.yml`
- Modify: `tests/release/test_claw_source_controller_policy.py`
- Modify: `tests/graph/test_workflow_policy.py`

**Interfaces:**
- Trigger: owner-only `repository_dispatch` type
  `observe-claw-host-inventory`, with exact default-branch ref/SHA binding.
- Evidence handoff: authenticated run-log lines
  `HOST_INVENTORY_OBSERVATION_SHA256=<hex>` and
  `HOST_INVENTORY_OBSERVATION_B64=<base64>`; no mutable artifact upload.

- [x] Add RED assertions for exact runner labels, pinned checkout,
      repository-dispatch/default-branch binding, collector-before-verifier
      ordering, mutation-token absence, log-envelope handoff and always cleanup.
- [x] Run focused workflow tests and confirm missing workflow failure.
- [x] Add the minimal workflow with `contents: read`, a fifteen-minute timeout,
      no untrusted inputs, no artifact upload, and exact local cleanup.
- [x] Re-run focused workflow tests and parse the YAML.

### Task 3: Graph and handoff closure

**Files:**
- Modify: `architecture/architecture.yaml`
- Modify: `docs/implementation/1-2a-claw-engine-runner-host-transition.md`
- Modify: `handoff.md`
- Modify: graph/release inventory tests as required by exact tracked count.

**Interfaces:**
- All new paths bind to HOST-001 contract/test/gate/evidence-plan lanes without
  creating a realized graph Receipt.

- [x] Add RED graph assertions for every new path and HOST-001 scope.
- [x] Add exact inventory bindings and update Story/handoff with the observation
      boundary and next owner checkpoint.
- [x] Run focused release, full graph, architecture precommit, syntax and diff
      checks.
- [ ] Commit one coherent source-only change and request independent security
      and graph reviews before push/landing.

### Runtime correction: observable blockers

- [x] RED: reproduce run `31632766796` failing with `SUBID_OVERLAP` before an
      authenticated observation could be emitted.
- [x] GREEN: accept bounded, closed subid/package/Podman facts and derive exact
      blocker codes; retain fail-closed structure, digest and authority rules.
- [ ] Re-run source reviews and land the correction before another dispatch.
