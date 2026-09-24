# Claw Host Inventory Evidence Design

## Goal

Produce a sanitized, read-only, GitHub-run-bound inventory of the current
`claw-engine-runner` host before any Story 1.2A host mutation. The inventory
supplies the missing hash in the owner approval tuple; it grants no authority.

## Boundaries

- The workflow runs only from the trusted default branch on
  `[self-hosted, claw, claw-engine-runner]` and only through
  owner-authenticated `repository_dispatch`. GitHub binds that event to the
  default-branch ref/SHA; the job also rejects any non-branch or non-default
  identity before checkout.
- Collection uses no `sudo`, package mutation, service mutation, Podman
  pull/load/run, recursive credential-tree enumeration, or app-stack write.
- It reads closed projections only: OS, cgroup v2, UID/GID and subordinate ID
  occupancy, exact engine/app systemd properties, allowlisted executable-path
  hashes (never raw `ExecStart` argv), selected directory metadata,
  package-state facts, runner identity, controller SHA/tree and GitHub run ID.
- Output is one closed JSON document with `authority=NONE`,
  `status=HOST_INVENTORY_OBSERVED`, `not_host_receipt=true`, and an embedded
  canonical payload digest. Raw command output and environment data are not
  uploaded.
- The verifier rejects duplicate or extra keys, placeholders, unexpected paths,
  missing app/engine canaries, secret-like fields, controller/run mismatch, and
  a payload-digest mismatch.
- Policy incompatibilities that are still safe to report (existing target
  subids, proposed-range overlaps, closure packages already installed, or an
  existing Podman baseline) do not suppress the observation. They are emitted
  as a sorted closed `preflight_blockers` list. Any non-empty list forbids host
  apply until policy/evidence is corrected and re-observed.

## Components and flow

1. `collect_claw_host_inventory.py` invokes a fixed argv allowlist and creates
   the canonical observation in `$RUNNER_TEMP`.
2. `verify_claw_host_inventory.py` independently validates schema and semantic
   invariants against explicit expected controller/run inputs.
3. `observe-claw-host-inventory.yml` checks out the GitHub-authenticated
   default-branch SHA, runs collector and verifier, writes the verified JSON
   SHA-256 plus its exact base64 bytes to the authenticated run log, and removes
   the mutable local file before a final `always()` cleanup fallback. It uploads
   no artifact that could be replaced after verification.
4. Release and graph tests bind the workflow, scripts and schema to HOST-001 and
   prove the absence of mutation verbs and credential outputs.

## Failure and approval semantics

Every missing command, unreadable exact unit/path, unexpected identity, or
schema mismatch fails before the log envelope is emitted. A successful envelope
is still a non-authoritative observation. Before it enters an approval tuple, an
independent reader must fetch the authenticated run log, decode the exact base64
bytes, match the logged SHA-256, and re-run the verifier. The owner must then
separately approve the exact
tuple `(source SHA/tree, policy hash, package closure hash, OCI archive hash,
host inventory observation hash)` before the transactional bootstrap may run.
The tuple is ineligible while `preflight_blockers` is non-empty; the host
transaction independently rechecks the underlying conditions rather than
trusting the diagnostic list as authority.
