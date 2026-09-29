# Integration analysis: external Grok/BMad boundary

Route: `7f0f98e3cdda`
Change: `20260928-repository-boundary-cleanup-7f0f98`
Role: `integration_architect` (read-only; this report is the only intended write)
Date: 2026-09-28

## Decision

Treat BMad and Adaptive Grok Build as two different dependencies.

1. **BMad can be externalized now.** The checked-in install identifies itself as
   BMad `6.10.0`, and that version maps to a real public upstream tag and npm
   package. Remove the generated BMad source trees from the product repository,
   retain a small project configuration/lock, and install the exact version into
   an ignored local tooling directory only when a contributor requests BMad.
2. **Adaptive Grok Build Pro cannot yet be honestly replaced by a downloadable
   package.** The repository contains its implementation, but no valid external
   package/repository/release locator for that implementation. `2.0.4` is only a
   hook-behaviour label. `@xai-official/grok@1.0.4` is the host Grok Build CLI,
   not the `adaptive_grok` Python stack. Deleting the stack and pretending either
   value is its package pin would break routing, receipts, policy hooks, and
   `scripts/grok_verify.py`.
3. The safe end-state is a **thin project seam plus a separately published,
   immutable factory plugin/artifact**. Until that artifact has a real locator
   and digest, either keep the approximately 193 KB Adaptive Grok core temporarily
   or make factory automation explicitly unavailable while preserving the
   independent project-native `make verify` path. Do not synthesize a dependency.

This is a tooling-boundary change only. It needs no application API, event, SQL,
migration, backfill, or product runtime change.

## Concrete ruling for Adaptive Grok

**No trustworthy external Adaptive Grok pin exists in the repository or in the
authoritative public material checked during this analysis.** The private
`multi-exchange-engine` baseline commit is historical provenance, not a public
tooling distribution. The official `@xai-official/grok` package is only the host
CLI. The local `2.0.4` text is not accompanied by an artifact URL, repository,
tag, package identifier, digest, license, or complete packaging command.

There are therefore only two honest choices for this change:

| Choice | What remains | Verification/safety result | Cost/risk | Ruling |
| --- | --- | --- | --- | --- |
| Retire the Adaptive Grok contract | Remove `.grok-stack`, Grok agents/skills/hooks/scripts and the mandatory route/receipt language from `AGENTS.md`; keep ordinary project tests, review process, and safety rules | `make verify` remains; adaptive routing, selected-agent enforcement, fingerprint receipts, and automated hook policy cease to be claimed | Smallest repository, but a deliberate workflow capability removal and broader documentation/acceptance change | Valid only with an explicit product-owner decision to drop the contract; do not describe it as an external integration |
| Keep a minimal local kernel temporarily | Retain only the code needed for route state, receipt binding, policy hooks, and the `grok_*` entrypoints; remove BMad and nonessential factory authoring/source | Preserves the current contributor contract and offline Grok verification while an external artifact is created | Some local tooling source remains; the boundary cleanup is partial until publication | **Recommended now**, because the requested scope says to preserve contributor safety gates and verification capability |

The minimal kernel is a transition, not a disguised external pin. Its exact file
set should be derived by characterization tests, not guessed: current doctor
requires `.grok/config.toml`, `.grok/hooks.json`, the adaptive-delivery skill,
routing config, all managed agents/skills, and local `adaptive_grok`; the route
and receipt commands import that package directly. Nonessential release
self-packaging templates, unused domain profiles/agents, and duplicate legacy
shims may be removed only when tests prove the active Liqvera route does not need
them.

If the owner insists that *all* Adaptive Grok sources leave this tree in the
same change, then the correct implementation is the first row: retire the
contract explicitly. A launcher pointed at an unset environment variable is not
preserved capability, and a reference to the Grok CLI is not a replacement.

## Repository evidence

### Inventory and product separation

- The tracked BMad footprint is 249 files / 1,755,254 bytes:
  `_bmad/**` plus `.agents/skills/bmad-*`.
- The tracked Adaptive Grok footprint is 142 files / 192,875 bytes:
  non-BMad `.agents/skills/**`, `.grok/**`, `.grok-stack/**`, and
  `scripts/grok_*.py`. Nine root compatibility hook shims add 8,676 bytes.
- `docs/README.md:64-66` says these directories support contributor/agent
  workflows and are not runtime features.
- `architecture/architecture.yaml:15223-15290` classifies all these paths as
  `VENDORED_TOOLING`.
- `Makefile:7-23` provides the product-native graph, salvage, artifact, and test
  gate. It does not import BMad or Adaptive Grok. The Grok layer calls project
  checks; the product does not call the Grok layer.
- `pyproject.toml:42-66` packages only the Liqvera/`mee-*` Python sources; neither
  `_bmad` nor `adaptive_grok` is a distribution dependency.

### Provenance that actually exists

- `PROVENANCE.md:7-10` and `provenance/import-manifest.json` bind the imported
  files to private upstream `Dimkox/multi-exchange-engine` at
  `4f6583f8590ea091d8a465de0c607e59bfe611a5`; every imported tooling file also
  has a source blob and SHA-256. This is exact historical provenance, but it is
  not an independently versioned public tooling dependency.
- The public Liqvera root import commit is
  `8734907d489168a8a6567b93bc85920001fefd85`. Fetching tooling from Liqvera's own
  old commit would be circular, would leave the bytes in repository history, and
  would not establish an upstream package boundary.
- No submodule, `.gitmodules`, or tooling-specific Git remote exists. The only
  configured remote is `https://github.com/Dimkox/liqvera.git`.

### BMad pin and upstream

Repository-local facts:

- `_bmad/_config/manifest.yaml:1-19` records installation and `core`/`bmm`
  version `6.10.0`.
- That same manifest says both modules are installer `built-in`, with
  `npmPackage: null` and `repoUrl: null`. Therefore the local manifest alone does
  not authorize guessing a package or repository.
- `_bmad/_config/manifest.yaml:20-21` records the `codex` integration. The
  installed output confirms that BMad generated `.agents/skills/bmad-*`.
- `_bmad/_config/files-manifest.csv` supplies per-file SHA-256 values for the
  installation, useful as migration comparison evidence but not as an external
  fetch locator.

External validation performed for this analysis:

- Official tag/release: `https://github.com/bmad-code-org/BMAD-METHOD/releases/tag/v6.10.0`
  (`081e64e` is displayed by GitHub).
- The tagged `package.json` identifies npm package `bmad-method`, version
  `6.10.0`, repository
  `git+https://github.com/bmad-code-org/BMAD-METHOD.git`, Node `>=20.12.0`, and
  MIT licensing:
  `https://raw.githubusercontent.com/bmad-code-org/BMAD-METHOD/v6.10.0/package.json`.
- `npm view bmad-method@6.10.0 ... --json` returned:

  ```text
  package: bmad-method@6.10.0
  tarball: https://registry.npmjs.org/bmad-method/-/bmad-method-6.10.0.tgz
  integrity: sha512-Z14VEk9R7JE0d016BLPiJPNcsS/ZIu97rC/76Ahe1IN7Wkqz3pK6Frljf5/FH8NZGOBawDY5SLyCybFcPJ/eMw==
  node: >=20.12.0
  ```

- Running `npx --yes bmad-method@6.10.0 install --list-tools` outside the repo
  confirmed tool ID `codex` and target `.agents/skills`; `install --help`
  confirmed `--directory`, `--modules`, `--tools`, `--set`, and `--yes`.

The exact package version and integrity make a real pinned BMad bootstrap
possible. The implementation must still compare generated output against the
current install before deleting the current tree; a version match does not by
itself prove identical installer options.

### Adaptive Grok references are not an external package pin

- `.grok/config.toml:1-12` points to the official Grok Build documentation and
  calls the local configuration “Adaptive Grok Build Pro”, but only says the
  hooks use `v2.0.4` fail-open semantics.
- `.grok/hooks/README.md:5-26` describes `2.0.4` behaviour (PreToolUse allows on
  import errors; Stop only warns). It does not name a repository, package,
  release asset, commit, or checksum.
- `.grok-stack/config/toolchain.json:37-52` pins the **host CLI** built version
  `1.0.4`, minimum `1.0.0`, with official xAI install URLs. This pin must not be
  relabelled as an Adaptive Grok stack version.
- External validation showed official npm package
  `@xai-official/grok@1.0.4` with integrity
  `sha512-Nu3SFXTqwvCQr/LQFwrQYgngJhUQwX2h9ZSgzW4HowidjbPBWtMVO0xI88d2z6/zlDSNaT5YP/uk+2DthKQMsg==`.
  It supplies the Grok client, not the repository's `adaptive_grok` modules.
- Official Grok documentation supports user/project skills, enabled plugins,
  marketplaces, `--plugin-dir`, and trusted project hooks:
  `https://docs.x.ai/build/features/skills-plugins-marketplaces`. That is a
  suitable future delivery mechanism, but it is not evidence that this custom
  factory has already been published.
- `.grok-stack/adaptive_grok/deploy.py:13-34` expects a root `VERSION`,
  `scripts/package_stack.py`, release notes, and an
  `adaptive-grok-build-pro-v{version}.zip`. None of `VERSION`,
  `scripts/package_stack.py`, or a release asset is tracked. Its fallback would
  therefore be `0.0.0`. This is incomplete self-packaging code, not a usable
  external source.

## Current coupling that the seam must replace

| Consumer | Current coupling | Required seam behaviour |
| --- | --- | --- |
| `scripts/grok_*.py` | Prepends repository `.grok-stack` to `sys.path`, then imports `adaptive_grok` | Execute a version-checked external CLI/module; never silently use a different version |
| `.grok/hooks/*.py` | Imports the same local `.grok-stack`; project hooks require Grok trust | Thin hook launcher passes stdin/stdout unchanged to the pinned external plugin |
| Root hook shims | Dispatch to `.grok/hooks/<name>` and allow/no-op if absent | Either remove with legacy hook config or redirect to the same thin launcher |
| `.grok-stack/runtime/**` | Stores routes, approvals, receipts, and fingerprints in the repository worktree | Remain project-local, ignored runtime state; never move receipts into a shared global cache |
| `.grok-stack/config/**` | Routing, quality profiles, policy, tool pins | Retain only Liqvera-specific declarative config; generic defaults belong to the external factory |
| `.grok/agents/**` and non-BMad `.agents/skills/**` | Factory-generated agents and workflow skills | Deliver from the external plugin/package, not the Liqvera tree |
| `_bmad/**`, `.agents/skills/bmad-*` | BMad installer output plus team/user configuration | Install exact `bmad-method@6.10.0` locally; keep only non-sensitive team settings in a small project config |
| `AGENTS.md` | Repository safety and delivery contract | Keep in repo. It is project policy, not replaceable factory source |
| `make verify` | Independent product verification | Keep fully usable without BMad or Grok network/bootstrap |

## Recommended target design

### 1. Commit only a small dependency contract

Use one machine-readable lock (name is implementation-owned) that contains, at
minimum:

- dependency ID;
- exact version;
- immutable source URL or package name;
- registry integrity or SHA-256;
- expected entrypoint/API compatibility version;
- required host/runtime version;
- whether it is required for product verification or only agent authoring;
- cache/install location policy;
- provenance note.

The BMad row can be filled now from the verified package data above. The
Adaptive Grok row must remain `unavailable`/unset until an authorized owner
publishes a real artifact. A placeholder URL, `latest`, a branch name, or the
Grok CLI package is not acceptable.

### 2. BMad: local, ignored, optional

- Pin the installer invocation itself to `bmad-method@6.10.0`; never invoke
  unqualified `npx bmad-method` because that resolves the current latest.
- Verify npm integrity before execution. Prefer installation from a downloaded
  tarball whose integrity matches the lock, rather than trusting mutable cache
  state.
- Run the installer into a temporary/staging directory, with `--modules bmm`,
  `--tools codex`, and explicit configuration values reconstructed from the
  reviewed team configuration. Atomically move the completed install into an
  ignored local tooling/cache directory.
- Never commit `_bmad/config.user.toml`; user name/language preferences belong
  to local state. Keep only reviewed team defaults needed for reproducibility.
- Add a verification command that checks installed version `6.10.0` and the
  expected skill inventory. Do not require BMad for product build/test.
- Do not auto-upgrade to 6.11/6.12: upstream release notes show breaking skill
  renames after 6.10.0.

### 3. Adaptive Grok: publish first, then bridge

The factory owner must first create a separate immutable distribution (a Grok
plugin/marketplace package, a dedicated repository tag, or a checksummed release
archive) containing:

- `adaptive_grok` runtime;
- generic agent definitions and the 15 managed workflow skills;
- hook entrypoints;
- default routing/quality/policy schemas;
- its own tests, license/notice, version metadata, changelog, and supported Grok
  CLI range.

After publication, Liqvera should retain only:

- `.grok/config.toml` or equivalent project config;
- `.grok/hooks.json` only if project hook registration cannot be supplied by the
  plugin;
- a tiny launcher/bootstrapper;
- Liqvera-specific route/policy/quality overrides;
- ignored `.grok-stack/runtime/` state;
- `AGENTS.md` and the external-dependency lock.

The launcher should resolve in this order: explicit approved local factory path,
exact-version cache, then (only under an explicit bootstrap command) the locked
remote artifact. Normal hooks and verification must never download code as a
side effect.

### 4. Keep product and factory verification separate

- `make verify` (and focused project tests) remains the offline product gate.
- The thin `scripts/grok_verify.py` replacement may call the external factory to
  choose profiles and write fingerprint-bound receipts.
- If the external factory is unavailable, product checks may still pass, but the
  command must not create a verification receipt or declare the adaptive route
  complete.
- Receipt fingerprints must continue to bind the Liqvera tree and route ID, not
  the external package cache. Add the external factory version and artifact
  digest to receipt metadata so evidence is reproducible.

## Offline and degraded behaviour

| Condition | Required behaviour |
| --- | --- |
| Network unavailable, exact dependency already cached | Run the cached artifact after digest/version verification; no network probe is needed |
| Network unavailable, BMad absent | BMad authoring commands report `BMAD_UNAVAILABLE_OFFLINE`; product build/test remains available |
| Network unavailable, Adaptive Grok absent | `make verify` remains available; adaptive routing/review/receipt commands fail non-zero with `FACTORY_UNAVAILABLE_OFFLINE`; no receipt or completion claim |
| Hook fires while Adaptive Grok is absent/broken | Preserve the documented 2.0.4 compatibility behaviour: PreToolUse allows and Stop warns. Emit a clear tooling-degraded message; never claim policy enforcement |
| Deploy/external-write wrapper called without factory | Fail closed. Never fall through to `git push`, `gh release create`, deployment, or production mutation |
| Cache has wrong version or digest | Quarantine/ignore it and fail; never fall back to newest or another installed version |
| Partial download/extraction | Stage in a temporary directory, validate digest and layout, then atomically rename; remove only the failed staging directory |
| Registry/upstream returns redirect or mutable asset | Follow only an explicitly allowed host policy and validate final bytes; digest mismatch is fatal |
| BMad installer proposes an update | Ignore the proposal; the lock remains `6.10.0` until a reviewed change updates it |

The hook fail-open rule is not equivalent to a working safety gate. In degraded
mode the durable `AGENTS.md` prohibitions remain authoritative, and all local
side-effect/deploy wrappers must still fail closed. Status/doctor output must say
that automated policy enforcement is unavailable.

## Failure modes and mitigations

1. **Version-name collision.** `2.0.4` (custom hook semantics) and `1.0.4`
   (official Grok CLI) describe different things. Mitigation: separate lock rows
   and compatibility fields.
2. **Unpublished factory dependency.** No external Adaptive Grok locator exists.
   Mitigation: do not delete its only working copy until publication or an
   explicit decision to drop adaptive automation.
3. **Private-source dependency.** The historical source is a private product
   repository. Mitigation: do not make public Liqvera contributors depend on it;
   publish a separately licensed tooling artifact first.
4. **Generated-output drift.** Reinstalling BMad 6.10.0 with different answers can
   change skills/config despite the same version. Mitigation: explicit installer
   arguments, staged output, inventory comparison against the current manifest,
   and characterization tests.
5. **Transitive npm drift.** The tagged BMad package uses semver ranges for its
   own dependencies. Mitigation: lock the tarball integrity and use a generated
   npm lock/cache for bootstrap execution; retain the BMad output-inventory
   comparison.
6. **Hook discovery/trust missing.** Grok project hooks require `/hooks-trust`.
   Mitigation: doctor reports a distinct degraded state and documents the manual
   trust step; no claim that hooks ran when they did not.
7. **Receipt trust drift.** Moving code out of tree can make old fingerprints
   insufficient to identify the verifier. Mitigation: record factory
   version/digest and config digest in every new receipt; invalidate receipts when
   project config changes.
8. **Bootstrap supply-chain attack.** `curl | bash`, `npx latest`, and unsigned
   mutable branches execute unreviewed code. Mitigation: exact artifact,
   integrity verification, allowed host, safe archive extraction, and no
   automatic install from a hook.
9. **Cache contamination across repositories.** Shared mutable config/runtime
   can leak approvals or routes. Mitigation: package code may be globally cached,
   but runtime state, approvals, config overrides, and receipts stay scoped to
   the Liqvera worktree.
10. **Historical-provenance loss.** Deleting active files does not erase why they
    existed. Mitigation: keep `PROVENANCE.md`, import manifest records, and Git
    history; update current docs to say the tooling is external/optional.
11. **License/redistribution ambiguity for Adaptive Grok.** Liqvera records no
    standalone tooling license or notice, and the root package is Proprietary.
    Mitigation: require an owner-approved license/notice before publishing the
    extracted factory publicly.

## Acceptance criteria for implementation

- BMad source/output directories are absent from tracked HEAD, while the lock
  names `bmad-method@6.10.0`, the official upstream/tag, and registry integrity.
- A clean online bootstrap generates the expected BMad `core`/`bmm` Codex skills
  in an ignored location; a second run is idempotent.
- An offline run succeeds from an already verified cache and fails clearly when
  the cache is absent.
- No bootstrap runs from normal product build, test, hook, or import paths.
- `make verify` remains runnable without BMad, Grok authentication, or network.
- No Adaptive Grok dependency is named unless its URL/package, exact version,
  digest, license, and entrypoint have been verified.
- `scripts/grok_*` and hooks either execute the exact external factory or report
  degraded/unavailable status; they never silently skip receipts while returning
  success for route completion.
- PreToolUse/Stop missing-factory behaviour matches the documented 2.0.4 soft
  compatibility contract; deploy/external-write commands remain fail-closed.
- New receipts include the external factory identity/digest plus Liqvera tree,
  route, and project-config fingerprints.
- Architecture inventory/tests are updated atomically from `VENDORED_TOOLING`
  paths to the new minimal tooling/config boundary.
- No product package, API, database schema, migration, deployment service, or
  shadow-only safety invariant changes.

## Recommended migration sequence

1. Characterize current `make verify`, Grok doctor/route/status/verification,
   hook degradation, receipt invalidation, and BMad inventory.
2. Add the dependency lock and thin launcher tests before deleting sources.
3. Externalize BMad 6.10.0 and verify online, cached-offline, missing-offline,
   digest-mismatch, and idempotent cases.
4. Publish and independently verify the Adaptive Grok artifact. This is a
   prerequisite, not something Liqvera can infer from current metadata.
5. Switch Grok scripts/hooks to the external entrypoint; verify exact version,
   input/output protocol, route selection, receipt binding, and fail-closed
   deployment paths.
6. Remove tracked factory sources, update graph classification/docs/provenance,
   run the complete selected verification profiles, then perform independent
   review.

Rollback is straightforward before a release: restore the vendored tooling paths
and their architecture inventory entries from the pre-cleanup commit. Runtime
receipts created by a different verifier identity must be invalidated, not
reused.

## Bottom line

BMad has a real, reproducible external dependency today:
`bmad-method@6.10.0`. Adaptive Grok Build Pro does not. The repository can remove
BMad immediately behind a pinned optional bootstrap, but a complete Grok source
removal must wait for a separately published, checksummed factory artifact or an
explicit decision to abandon adaptive routing/receipt automation. The official
Grok CLI/plugin mechanism is the right host seam; the CLI itself is not the
missing factory package.
