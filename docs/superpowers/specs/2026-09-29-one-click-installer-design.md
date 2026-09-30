# Liqvera one-click installer — design

Date: 2026-09-29

Status: proposed for written-spec review

Target product release: v0.0.2

## Intent

Provide a predictable first installation and lifecycle experience for a
self-hosted Liqvera testnet/shadow stack on Linux. The operator runs
`install.sh`, which consumes one versioned install package and produces the
declared Compose topology, configuration contract, migration state, health
verdict, and lifecycle commands.

Success means a clean supported host can verify a pinned v0.0.2 package,
generate local configuration without committing secrets, start the stack,
apply migrations 001–005 exactly once, and reach a bounded healthy state. A
reinstall is idempotent, failures preserve a recoverable prior installation,
and uninstall never removes operator data unless separately requested.

This document is design only. It authorizes no installer implementation,
dependency installation, privilege escalation, payment, deployment, or release.

## Non-goals and safety boundary

- No mainnet support, custody, private venue access, exchange writes, trading,
  wallet-key generation, wallet-key storage, or automatic payment.
- No silent `sudo`, package-manager invocation, firewall change, Docker daemon
  reconfiguration, port forwarding, or telemetry upload.
- No replacement for Docker Engine administration or host hardening.
- No in-place database downgrade and no automatic deletion of volumes.
- No promise that fixture or shadow evidence is live market acceptance.

The installed defaults remain Mezo Testnet, shadow/read-only market behavior,
no payment grant, no wallet payload, and no exchange credentials. Live payment
and external writes remain separately gated operator actions.

## Considered approaches

### 1. Docker-first release package — selected

Ship a thin Bash launcher around a versioned package containing
Compose, configuration templates, lifecycle metadata, and checksums. Docker
provides the runtime boundary; scripts handle preflight, verified materialization,
configuration, lifecycle orchestration, and recovery.

Advantages: reuse of existing Compose
and health contracts, no host-language dependency graph, bounded rollback by
release directory, and clear separation between installer authority and
container authority. Costs: Docker Engine is a prerequisite and Linux
filesystem, init-system, and port semantics need distribution coverage.

### 2. Native distribution packages

Build deb/rpm packages that install Node, Python, PostgreSQL, and services
directly. This gives deeper OS integration but multiplies service
managers, migration paths, permissions, signing systems, and rollback behavior.
It is disproportionate for v0.0.2 and expands host mutation substantially.

### 3. Language bootstrapper

Publish one Python or Node CLI that downloads and starts the stack. This appears
portable but creates a bootstrap-runtime/version problem, increases dependency
trust, and still needs separate privilege and Docker handling. It is useful only
after an installer-independent management CLI exists.

Docker-first is selected because Liqvera already has a Compose topology and
container boundaries, while the goal is safe repeatability rather than native
OS integration. The launchers remain small and behaviorally equivalent.

## Artifact and trust model

The v0.0.2 GitHub Release contains:

```text
liqvera-installer-0.0.2/
├── install.sh
├── liqvera.sh
├── lib/
│   ├── common.sh
│   └── runtime.py
├── schemas/
│   ├── config.schema.json
│   ├── install-state.schema.json
│   └── release-manifest.schema.json
├── compose.yaml
├── config/
│   ├── liqvera.env.template
│   └── ports.env.template
├── migrations/
│   ├── 001_*.sql
│   ├── 002_*.sql
│   ├── 003_*.sql
│   ├── 004_*.sql
│   └── 005_*.sql
├── manifests/
│   ├── release-manifest.json
│   └── migration-checksums.json
├── LICENSE-NOTICE.md
└── SHA256SUMS
```

The release page exposes a detached outer checksum for the installer archive.
v0.0.2 does not invent a code-signing root: the operator independently verifies
the bootstrap launcher's published SHA-256 before execution and supplies the
expected archive SHA-256 as a mandatory installer argument. The installer never
accepts a digest fetched from the same archive URL as sufficient trust. It
verifies the archive before extraction, then verifies every extracted regular
file against `SHA256SUMS` and rejects
missing, extra, duplicate, symlink, hardlink, traversal, or special-file entries.

The release manifest binds product version `0.0.2`, exact Git commit/tree,
Compose digest, image digests, migration names/checksums, supported Linux
architectures/distributions,
and launcher digests. Tags alone are not trusted. Mutable image tags are never
accepted; Compose uses immutable image digests.

Trust boundaries:

1. operator chooses the release source and expected outer digest;
2. launcher may read only declared inputs and the selected install root;
3. archive verification precedes execution of extracted content;
4. Docker receives only generated configuration and declared mounts;
5. PostgreSQL migrations are accepted only from the manifest-bound 001–005 set;
6. wallet, payment grant, `.env`, credential stores, and SSH/Git credentials are
   outside installer authority;
7. status/log commands redact configured secret values and authorization data.

## Installation layout and identity

Default roots are `$XDG_DATA_HOME/liqvera` or `~/.local/share/liqvera`.
An explicit `--install-dir` overrides the
default after canonical-path validation. Network shares, symlinked roots,
filesystem roots, existing non-Liqvera directories, and world-writable parent
directories fail closed.

```text
<install-root>/
├── current -> releases/0.0.2/        # atomic symlink
├── releases/0.0.2/                   # read-only verified package
├── config/runtime.env                # mode 0600
├── state/install-state.json          # non-secret lifecycle state
├── state/migration-state.json        # names and checksums only
├── data/                              # Docker-managed persistent data
├── logs/installer/                    # bounded, redacted local logs
└── rollback/previous.json             # prior version identity
```

`install-state.json` records
schema version, product version, release digest, commit/tree, install root,
Compose project name, selected ports, Linux distribution/architecture, Docker identity, timestamps,
and last completed phase. It contains no secret values.

## Interfaces and command contract

Initial installation:

```text
install.sh  --verified-release DIR --verified-receipt FILE --sha256 DIGEST
            --install-dir PATH --config PATH [--non-interactive]
            [--install-deps --approve-dependency-command SHA256]
```

Lifecycle wrapper:

```text
liqvera status [--json]
liqvera logs [SERVICE] [--tail N] [--since DURATION]
liqvera update --version VERSION --sha256 DIGEST
liqvera stop
liqvera start
liqvera uninstall [--purge-data --confirm-purge TOKEN]
liqvera rollback
```

All commands support `--help` and `--version`, have stable exit codes, write
human diagnostics to stderr, and reserve stdout for requested machine output.
Non-interactive mode requires all decisions explicitly; it never accepts a
default that broadens authority.

`--install-deps` is optional and explicit. Without it, missing Docker/Compose
returns a distribution-specific instruction and makes no host changes. With it, the
launcher prints the exact package-manager command and asks for confirmation.
Interactive confirmation requires typing the printed exact command digest;
non-interactive use requires that digest as an argument. The receipt is the
closed output of the independently verified Task 2 materialization and is
reconciled with the supplied outer digest and a fresh inner-file rehash before
any host mutation.
Privilege elevation is initiated visibly by the operator; the installer never
embeds credentials, bypasses policy, or silently invokes `sudo`. Unsupported
Linux distributions/architectures fail before dependency installation.

## Preflight

Preflight is read-only and completes before creating the install root:

- identify supported Linux distribution/architecture and Bash version;
- require Docker Engine and Compose v2 with minimum reviewed versions;
- verify daemon reachability and sufficient disk/memory without changing it;
- verify release URL is HTTPS on the exact allowed GitHub release host;
- validate expected version and outer SHA-256;
- resolve install root and reject unsafe ownership/link/filesystem conditions;
- check configured ports by binding probes and report the owning conflict where
  Linux permits it;
- validate configuration schema, testnet network, shadow mode, paths, and
  secret-file references without opening secret contents unnecessarily;
- inspect an existing install state and choose install, idempotent reconcile,
  update, or fail-closed conflict.

Preflight has a machine-readable JSON form used by tests and support. A failed
preflight performs zero Docker, filesystem, migration, network-service, or
privileged mutations beyond bounded release metadata download when requested.

## Configuration generation

The installer copies a closed template into `config/runtime.env`, substitutes
only validated non-secret values, and writes it create-exclusive with restrictive
permissions. Defaults bind loopback-only published ports, Mezo Testnet chain
31611, shadow/read-only source behavior, payment disabled, and no public hosted
endpoint.

Secrets are supplied as existing file paths or entered interactively into
restricted local files. They are never command-line values, echoed, logged,
included in `install-state.json`, copied into the release directory, or committed.
The installer may generate non-secret random identifiers (Compose project and
local journal identity), but never wallet keys or payment signatures. Config
regeneration is atomic: validate a private temporary file, fsync, rename, and
retain the last valid version for rollback.

## Compose, migrations, and health

The install package projects the existing Liqvera services: edge, web, gateway,
capture/report workers, and PostgreSQL, preserving current internal-only network
and metrics boundaries. Containers run with reviewed users, mounts, resource
limits, read-only filesystems where supported, and no Docker socket mount.

Startup order is database health, migration job, internal services, gateway,
then edge/web. The migration job:

- acquires the existing database migration lock;
- requires the exact manifest-bound 001–005 list and checksums;
- applies only missing forward migrations in order;
- treats checksum drift, unknown rows, partial state, or downgrade as fatal;
- is safe to rerun and never rewrites migration history.

Health is bounded by a total timeout and requires container state plus existing
service health/readiness contracts. Payment readiness may remain false under the
safe default, but it must report the expected `EXTERNAL_GRANT_REQUIRED` blocker.
Success never depends on external exchange or facilitator availability.

## Idempotency, update, rollback, and uninstall

Re-running install for the same verified release compares manifest, config
schema, Compose identity, and migration state. Matching state reconciles missing
containers and health only; it does not recreate config, volumes, or migrations.
Conflicting bytes or identity stop with an actionable diagnostic.

Update stages the new archive in a new release directory, verifies it, validates
configuration compatibility, snapshots non-secret state and the database using
the existing approved backup mechanism, starts the candidate, runs forward
migrations, and switches the current pointer only after health passes. Because
database migrations are forward-only, rollback has two modes:

- before a new migration commits: stop candidate and restore the old pointer;
- after migration commits: roll forward with the compatible prior image only if
  the manifest declares compatibility; otherwise stop and require explicit
  restore from the pre-update backup. Never run down migrations automatically.

`stop` preserves configuration and data. Default `uninstall` stops/removes
containers, networks, verified release directories, and wrappers but preserves
config, logs, backups, and volumes. `--purge-data` requires an explicit generated
confirmation token, prints exact targets, refuses broad/root paths, and is a
separate destructive action.

## Failure recovery

Each mutating phase writes an intent and completion marker atomically. On
restart, the installer derives the last complete phase rather than guessing.

| Failure | Recovery |
| --- | --- |
| Download interrupted | Delete only invocation-owned partial file; retry from zero |
| Checksum/archive invalid | Quarantine candidate; leave current untouched |
| Port becomes occupied | Stop candidate services; retain staged release and report port |
| Migration lock busy | Exit retryable without a second migration runner |
| Migration fails | Preserve logs and database; do not switch current pointer |
| Health timeout | Stop candidate; restore prior pointer if migration-compatible |
| Host reboot | `status` reports incomplete phase; explicit install/update resumes |
| Rollback unavailable | Keep services stopped and print backup/forward-fix procedure |

No automatic retry crosses an authority boundary. Downloads may be retried
before verification; migrations, payments, and destructive cleanup are not
blindly retried.

## Linux and service-manager behavior

The supported runtime is Linux with a reviewed Bash version, Docker Engine, and
Compose v2. Mode and ownership checks are mandatory. Supported distributions
are an explicit manifest allowlist; distribution-specific branches are limited
to optional dependency-install command selection.

When systemd is present and running, an explicit installer option may install a
user-level Liqvera unit that invokes the lifecycle wrapper. The default does not
write system units or call `systemctl`. Without usable systemd, lifecycle
commands operate directly through Docker Compose and status reports
`service_manager=compose`. A missing or unusable systemd never triggers root
unit installation as a fallback.

## Observability and support

Installer logs are local, timestamped, bounded, and structured with phase,
release digest, service, outcome, and stable error code. Redaction covers env
values, URLs with credentials, capabilities, payment payloads, signatures, and
database passwords. `status --json` reports version, commit/tree, config digest,
migration names/checksums, container/health summaries, ports, and blockers—never
secret values or raw environment.

No telemetry leaves the host. Support bundles are explicit, preview their file
list, omit data volumes/secrets by construction, and are outside the first
implementation unless separately approved.

## Acceptance matrix

| Scenario | Required evidence |
| --- | --- |
| Ubuntu clean install | Verified v0.0.2 archive, generated restricted config, migrations 001–005 once, healthy safe-default stack |
| Ubuntu reinstall | Same release reconciles idempotently; config/data preserved; migrations unchanged |
| Linux distribution matrix | Supported Ubuntu/Debian and documented RPM-family fixtures produce equivalent state/commands |
| systemd present | Explicit user-unit option installs/validates only a user unit; no root unit writes |
| systemd absent | Compose lifecycle fallback works and reports `service_manager=compose` |
| Corrupt outer checksum | Fails before extraction/execution and leaves current install unchanged |
| Corrupt inner file | Fails closed on `SHA256SUMS`; no Compose or migration call |
| Occupied port | Preflight or startup race reports exact port; candidate stopped; current install preserved |
| Interrupted download/install | Invocation-owned partials cleaned; durable prior install remains usable |
| Migration checksum drift | Startup blocked before application services; database untouched beyond read/lock |
| Update success | New release staged/verified/healthy, pointer switches atomically, previous release retained |
| Update health failure | Candidate stopped and prior compatible release restored |
| Rollback after migration | Compatibility rule enforced; otherwise explicit backup restore required |
| Stop/start | Idempotent and preserves config/data |
| Default uninstall | Runtime removed; config/data/backups retained |
| Purge uninstall | Exact targets plus confirmation token; broad/symlink targets rejected |
| Secret/log scan | No secret values, payloads, capabilities, or credentials in state/log/output |
| Safe defaults | Testnet/shadow, payment disabled, loopback ports, no exchange writes |

Tests use disposable temporary roots, fake Docker/Compose/process adapters, and
disposable databases. Real clean-host acceptance runs only on isolated Ubuntu,
supported Linux workers. Dependency installation tests inspect planned
commands by default; any real package-manager mutation requires separate CI
environment approval.

## Implementation boundaries for the later plan

The later implementation plan should split shared schemas/state semantics,
release packaging, Bash launcher, optional user-systemd integration, Compose integration,
and isolated-host acceptance into reviewable steps. It must add failing tests
before behavior, preserve the existing Compose/runtime security constraints,
and require independent security/release review before publishing v0.0.2.

No implementation begins until this written spec is reviewed and approved and
a separate implementation plan is written and selected for execution.
