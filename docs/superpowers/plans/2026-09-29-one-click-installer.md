# Liqvera Linux One-Click Installer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a checksum-bound Docker-first Bash installer and lifecycle wrapper for safe self-hosted Liqvera on supported Linux hosts.

**Architecture:** Closed JSON contracts define one install phase/state machine. A thin Bash launcher verifies immutable v0.0.2 package bytes before extraction, generates restricted configuration, and orchestrates digest-pinned Docker Compose services and migrations 001–005 through an injectable process boundary. Optional systemd integration is user-level and explicit; direct Compose lifecycle is the required fallback.

**Tech Stack:** Linux, Bash, Docker Engine, Docker Compose v2, optional systemd user units, JSON Schema Draft 2020-12, Python 3.12 build/test tooling, pytest, ShellCheck.

**Spec:** `docs/superpowers/specs/2026-09-29-one-click-installer-design.md`

## Global Constraints

- Support Linux only. Do not add macOS, Windows, PowerShell, WSL, Docker Desktop, or cross-platform abstraction.
- Product package/version is exactly `0.0.2`; component versions remain `0.1.0`, root workspace metadata `0.1.0.dev0`.
- Defaults are Mezo Testnet chain `31611`, shadow/read-only source mode, payment disabled, and loopback-published ports.
- Mainnet, custody, wallet-key generation/storage, private venues, exchange writes, trading, and automatic payment are forbidden.
- Require an independently supplied outer SHA-256. Never trust a digest obtained only from the same archive URL.
- Reject missing/extra/duplicate archive entries, traversal, absolute paths, symlinks, hardlinks, devices, FIFOs, sockets, and checksum drift before executing extracted content.
- Compose images are immutable digests; mutable tags are invalid.
- Migrations are exactly existing 001–005 with manifest-bound checksums. Never run down migrations or rewrite history.
- Secrets are restricted existing files or restricted interactive-file inputs, never CLI values, logs, state JSON, release files, or Git content.
- `--install-deps` is explicit. Never invoke `sudo`, a package manager, or systemd silently.
- systemd integration, when present, is explicit and user-level only. Direct Compose operation is the fallback.
- Default uninstall preserves config, logs, backups, and volumes. Purge requires an exact confirmation token and narrow validated targets.
- Every task follows RED → minimal GREEN → focused verification → coherent commit and updates graph/handoff when repository truth changes.
- No real dependency installation, container/database mutation, external host mutation, push, tag, or release without separate authority.

## Review Focus

1. Linux path aliases, Unicode normalization, and case-fold collisions must not bypass archive duplicate/traversal/link rejection; Task 2 adds hostile archive tests.
2. A port can become occupied after preflight; Task 4 requires candidate shutdown and unchanged current pointer.
3. Crash recovery between phase intent/completion markers must not duplicate config or migrations; Task 5 tests every boundary.
4. A migration-committed update must refuse false rollback when the prior image is incompatible; Task 5 tests explicit restore-required behavior.
5. Subprocess stderr/config errors containing secret canaries must remain redacted from logs/status; Tasks 1, 3, and 5 test all output channels.

---

## File map and interfaces

- `installer/schemas/{release-manifest,install-state,config}.schema.json`: closed shared contracts.
- `installer/config/{liqvera.env,ports.env}.template`: non-secret safe defaults.
- `installer/lib/common.sh`: validation, state, config, process, Compose, migration, health, and lifecycle functions.
- `installer/install.sh`: preflight/install entrypoint.
- `installer/liqvera.sh`: status/logs/start/stop/update/uninstall/rollback entrypoint.
- `installer/compose.yaml`: security-preserving installer projection of existing services.
- `installer/systemd/liqvera.service.in`: optional user-unit template only.
- `installer/manifests/v0.0.2.json`: package identity/image/migration/compatibility template.
- `scripts/build-liqvera-installer.py`: deterministic builder.
- `scripts/verify-liqvera-installer.py`: independent archive verifier/materializer.
- `tests/installer/`: contracts, archive, Bash, Compose, lifecycle, package, and Linux harness tests.

Stable shell/JSON interfaces:

- `preflight INPUT_JSON -> preflight-result-v1`
- `verify_release ARCHIVE EXPECTED_SHA256 DESTINATION -> verified-release-v1`
- `load_state INSTALL_ROOT -> install-state-v1 | absent`
- `write_state_atomic INSTALL_ROOT STATE_JSON`
- `render_config CONFIG_JSON -> runtime.env`
- `run_compose ARGV_JSON ENV_JSON -> process-result-v1`
- `check_migration_plan -> migration-plan-result-v1`
- `wait_healthy DEADLINE_SECONDS -> health-result-v1`
- `reconcile_install VERIFIED_RELEASE CONFIG PRIOR_STATE -> install-result-v1`
- `run_lifecycle COMMAND OPTIONS STATE -> lifecycle-result-v1`

### Task 1: Freeze contracts and Linux-safe defaults

**Files:**
- Create: `installer/schemas/release-manifest.schema.json`
- Create: `installer/schemas/install-state.schema.json`
- Create: `installer/schemas/config.schema.json`
- Create: `installer/config/liqvera.env.template`
- Create: `installer/config/ports.env.template`
- Create: `tests/installer/test_contracts.py`
- Modify: `architecture/architecture.yaml`, `handoff.md`

**Interfaces:** Produces schemas `liqvera-installer-release/v1`, `liqvera-install-state/v1`, `liqvera-install-config/v1` and exact error enum: `UNSUPPORTED_LINUX`, `DEPENDENCY_MISSING`, `UNSAFE_INSTALL_ROOT`, `PORT_OCCUPIED`, `RELEASE_DIGEST_MISMATCH`, `ARCHIVE_INVALID`, `CONFIG_INVALID`, `SECRET_REFERENCE_INVALID`, `MIGRATION_MISMATCH`, `HEALTH_TIMEOUT`, `ROLLBACK_RESTORE_REQUIRED`, `PURGE_CONFIRMATION_REQUIRED`.

- [ ] **Step 1: Add RED contract tests.** Assert Draft 2020-12 closed objects; version `0.0.2`; chain `31611`; `payment_enabled=false`; `source_mode=shadow`; loopback ports; five exact migrations; digest-only images; no secret values/free-form env; exact errors.
- [ ] **Step 2: Run** `.venv/bin/python -m pytest -q tests/installer/test_contracts.py`. **Expected:** FAIL because files are absent.
- [ ] **Step 3: Implement minimal schemas/templates.** Use `additionalProperties:false`, exact enums and lowercase 64-hex digests; templates contain only non-secret values and named `*_FILE` references.
- [ ] **Step 4: Run** `.venv/bin/python -m pytest -q tests/installer/test_contracts.py tests/graph`. **Expected:** PASS.
- [ ] **Step 5: Commit** `git commit -m "feat(installer): freeze Linux installer contracts"` with Task 1 files.

### Task 2: Verify and safely materialize release archives

**Files:**
- Create: `scripts/verify-liqvera-installer.py`
- Create: `tests/installer/test_archive_verifier.py`
- Modify: `pyproject.toml`, `architecture/architecture.yaml`, `handoff.md`

**Interfaces:** Produces Python `verify_installer(archive: Path, expected_sha256: str, destination: Path) -> VerifiedRelease`; CLI emits canonical `verified-release-v1` only after safe materialization.

- [ ] **Step 1: Add RED hostile-archive tests.** Cover valid archive; wrong outer digest; missing/extra file; duplicate normalized/casefold name; `../`, absolute and backslash traversal; Unicode collision; symlink/hardlink/FIFO/device; oversized member/aggregate; changed inner checksum; existing destination. Assert no executable appears on failure.
- [ ] **Step 2: Run** `.venv/bin/python -m pytest -q tests/installer/test_archive_verifier.py`. **Expected:** FAIL importing verifier.
- [ ] **Step 3: Implement minimal verifier.** Read bounded archive metadata, normalize names with POSIX separators + Unicode NFC + casefold collision keys, accept regular single-link files only, validate manifest/`SHA256SUMS`, and create-exclusive materialize into an invocation-owned private directory. Never execute content.
- [ ] **Step 4: Run** `.venv/bin/python -m pytest -q tests/installer/test_archive_verifier.py && .venv/bin/python -m bandit -q scripts/verify-liqvera-installer.py`. **Expected:** PASS.
- [ ] **Step 5: Commit** `git commit -m "feat(installer): verify archives before extraction"`.

### Task 3: Implement Linux preflight, config, and explicit dependency handling

**Files:**
- Create: `installer/lib/common.sh`
- Create: `installer/install.sh`
- Create: `tests/installer/fixtures/process-fixtures.json`
- Create: `tests/installer/test_linux_installer.py`
- Modify: `architecture/architecture.yaml`, `handoff.md`

**Interfaces:** Produces Bash functions `preflight`, `load_state`, `write_state_atomic`, `render_config`, `run_compose`, `reconcile_install`; CLI `install.sh --sha256 DIGEST [--version 0.0.2] [--install-dir PATH] [--config PATH] [--non-interactive] [--install-deps]`.

- [ ] **Step 1: Add RED tests with fake executables.** Cover Ubuntu/Debian and documented RPM-family fixtures, unsupported OS/arch, Bash/Docker/Compose floors, daemon unavailable, disk/memory, unsafe root/symlink/world-writable parent, paths with spaces, occupied port, restricted `0600` config, invalid secret reference, secret-canary redaction, and exact process allowlist.
- [ ] **Step 2: Add RED privilege tests.** Without `--install-deps`, missing Docker performs zero package calls. With it, print the exact allowlisted package command and require interactive confirmation; `--non-interactive --install-deps` fails without a separate exact approval input. Assert no implicit `sudo`.
- [ ] **Step 3: Run** `.venv/bin/python -m pytest -q tests/installer/test_linux_installer.py`. **Expected:** FAIL because scripts are absent.
- [ ] **Step 4: Implement minimal Bash phases.** Use Bash arrays, `set -euo pipefail`, no `eval`, no sourced untrusted config, fixed PATH for subprocesses, private temp dirs, and atomic/fsynced state/config writes.
- [ ] **Step 5: Run** `.venv/bin/python -m pytest -q tests/installer/test_linux_installer.py && shellcheck installer/install.sh installer/lib/common.sh`. **Expected:** PASS; missing provisioned ShellCheck is an explicit blocker, never silently downloaded.
- [ ] **Step 6: Commit** `git commit -m "feat(installer): add safe Linux preflight"`.

### Task 4: Integrate Compose, migrations 001–005, health, and optional systemd

**Files:**
- Create: `installer/compose.yaml`
- Create: `installer/manifests/v0.0.2.json`
- Create: `installer/systemd/liqvera.service.in`
- Create: `tests/installer/test_compose_install.py`
- Create: `tests/installer/test_systemd_integration.py`
- Modify: `installer/lib/common.sh`, `architecture/architecture.yaml`, `handoff.md`

**Interfaces:** Produces `check_migration_plan`, `wait_healthy`, `detect_service_manager() -> systemd-user|compose`, and `install_user_unit(EXPLICIT_OPTION)`. Consumes existing `deploy/mezo-evidence/compose.yaml` security contract and gateway migrations 001–005.

- [ ] **Step 1: Add RED Compose tests.** Assert exact services/networks/mounts/limits, digest-only images, loopback ports, no Docker socket/wallet/payment secrets, exact migration names/checksums, migration lock, unknown/checksum/downgrade refusal, bounded health, expected `EXTERNAL_GRANT_REQUIRED`, and port-race candidate shutdown with unchanged current pointer.
- [ ] **Step 2: Add RED systemd tests.** systemd present + explicit option writes only a user unit and invokes `systemctl --user`; default invokes no systemctl; absent/unusable systemd uses Compose and reports `service_manager=compose`; never write `/etc/systemd` or invoke root systemctl.
- [ ] **Step 3: Run** `.venv/bin/python -m pytest -q tests/installer/test_compose_install.py tests/installer/test_systemd_integration.py`. **Expected:** FAIL because files/functions are absent.
- [ ] **Step 4: Implement projection and adapters.** Package-time migration copies derive from existing source files; do not create a second migrator. Startup order is DB health → migration job → internal services → gateway → edge/web.
- [ ] **Step 5: Run focused tests.** Run `.venv/bin/python -m pytest -q tests/installer/test_compose_install.py tests/installer/test_systemd_integration.py`; run existing disposable PostgreSQL suite only with its explicit approved test URL. **Expected:** PASS or existing explicit DB skip.
- [ ] **Step 6: Commit** `git commit -m "feat(installer): orchestrate Compose and Linux services"`.

### Task 5: Add idempotent lifecycle and recovery

**Files:**
- Create: `installer/liqvera.sh`
- Create: `tests/installer/test_lifecycle.py`
- Modify: `installer/lib/common.sh`, `architecture/architecture.yaml`, `handoff.md`

**Interfaces:** Produces `run_lifecycle COMMAND OPTIONS STATE -> lifecycle-result-v1` and commands `status [--json]`, `logs [SERVICE] [--tail N] [--since DURATION]`, `start`, `stop`, `update --version VERSION --sha256 DIGEST`, `uninstall [--purge-data --confirm-purge TOKEN]`, `rollback`.

- [ ] **Step 1: Add lifecycle RED tests.** Cover clean install, same-release reinstall, every intent/completion crash boundary, concurrent lock, start/stop idempotency, bounded/redacted logs, update stage-before-switch, successful atomic symlink switch, health failure restore, migration-committed incompatible rollback refusal, compatible rollback, default uninstall preservation, purge-token mismatch, broad/symlink target refusal, and secret-bearing subprocess stderr redaction.
- [ ] **Step 2: Run** `.venv/bin/python -m pytest -q tests/installer/test_lifecycle.py`. **Expected:** FAIL because lifecycle wrapper is absent.
- [ ] **Step 3: Implement minimal lifecycle state machine.** Use one install lock, atomic intent/completion markers, immutable release directories, atomic `current` symlink replacement, explicit compatibility declarations, and backup/forward-fix instructions. Never auto-run down migrations.
- [ ] **Step 4: Run** `.venv/bin/python -m pytest -q tests/installer/test_lifecycle.py tests/installer/test_linux_installer.py`. **Expected:** PASS; mutations switching before health or purging without token must fail.
- [ ] **Step 5: Commit** `git commit -m "feat(installer): add recoverable Linux lifecycle"`.

### Task 6: Build and independently verify deterministic packages

**Files:**
- Create: `scripts/build-liqvera-installer.py`
- Create: `tests/installer/test_package_builder.py`
- Modify: `scripts/verify-liqvera-installer.py`, `Makefile`
- Modify: `engineering/changes/20260929-f7-live-acceptance-and-release-0-0-1-337ef5/release-artifact-manifest-v0.0.2.json`
- Modify: `architecture/architecture.yaml`, `handoff.md`

**Interfaces:** Produces `build_installer(source_commit: str, output: Path) -> BuildResult`, deterministic `liqvera-installer-0.0.2.zip`, detached `.sha256`, populated manifest, and `SHA256SUMS`.

- [ ] **Step 1: Add package-builder RED tests.** Reject dirty/wrong HEAD, non-allowlisted paths, `.env`, wallet material, `node_modules`, data/logs, secret canaries, mutable image tags, and migration drift. Assert normalized order/timestamps/modes, two-build byte equality, independent verifier success, and corrupt/missing/extra asset failure.
- [ ] **Step 2: Run** `.venv/bin/python -m pytest -q tests/installer/test_package_builder.py`. **Expected:** FAIL because builder is absent.
- [ ] **Step 3: Implement deterministic builder.** Use stdlib ZIP, sorted POSIX paths, commit-derived fixed UTC timestamp, fixed regular modes, create-new outputs, and environment-independent bytes. Generate checksums after final bytes.
- [ ] **Step 4: Build twice and verify.** Run `make liqvera-installer INSTALLER_OUT=/tmp/liqvera-installer-a`, repeat to a fresh `-b`, `cmp` archives, then `make liqvera-installer-verify INSTALLER_OUT=/tmp/liqvera-installer-a`. **Expected:** both builds and verifier PASS; use invocation-owned temp roots during execution.
- [ ] **Step 5: Commit** `git commit -m "feat(installer): build reproducible v0.0.2 package"`.

### Task 7: Prove supported Linux behavior and publish operator docs

**Files:**
- Create: `tests/installer/test_linux_acceptance.py`
- Create: `.github/workflows/installer-linux.yml`
- Modify: `README.md`, `docs/README.md`
- Modify: `docs/runbooks/startup-shutdown.md`, `docs/runbooks/observability.md`
- Modify: `engineering/changes/20260929-f7-live-acceptance-and-release-0-0-1-337ef5/release-notes-v0.0.2.md`
- Modify: `architecture/architecture.yaml`, `handoff.md`

**Interfaces:** Consumes all prior installer commands/artifacts; produces isolated Linux evidence and truthful operator/recovery documentation.

- [ ] **Step 1: Add docs/workflow RED tests.** Require exact install/status/logs/update/stop/uninstall/rollback commands, mandatory SHA, distro/architecture table, safe defaults, no-silent-root behavior, secret-file boundary, systemd user-only/fallback behavior, purge warning, rollback limits, and no macOS/Windows/PowerShell claims.
- [ ] **Step 2: Add isolated Linux matrix RED tests.** Required scenarios: Ubuntu clean install/reinstall, supported distro fixtures, corrupt outer/inner checksums, occupied port, systemd present/absent, interrupted install, update, compatible/incompatible rollback, default/purge uninstall, and secret scan. Ordinary PR jobs use mocks; real Docker/package-manager mutations require isolated explicitly approved runners.
- [ ] **Step 3: Run** `.venv/bin/python -m pytest -q tests/installer/test_linux_acceptance.py`. **Expected:** FAIL until docs/workflow/harness are complete.
- [ ] **Step 4: Complete docs and Linux workflow.** Never run `--install-deps` in ordinary PR CI. Attach commit/tree/artifact digests to clean-host evidence; unavailable gated runners remain explicit, never inferred PASS.
- [ ] **Step 5: Run focused/full verification.** Run `.venv/bin/python -m pytest -q tests/installer tests/graph`, gateway tests, then `.venv/bin/python scripts/grok_verify.py --mode pr`. **Expected:** PASS on one clean commit.
- [ ] **Step 6: Obtain exact-fingerprint code, test, security, data, and release reviews.** Any fix returns through its owning RED/GREEN tests. Then commit docs/workflow with `git commit -m "docs(installer): publish verified Linux workflow"`.

Do not implement macOS/Windows support, push, tag, publish v0.0.2, install host dependencies, or mutate external hosts under this plan without a new approved design and exact grants.
