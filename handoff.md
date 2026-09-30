# Liqvera — handoff

Updated: 2026-09-29 (F5 closed; F6 fake/static verification and independent reviews PASS). Repository: `Dimkox/liqvera`.
Branch: `feat/f3-f7-verification` (based on merged repository-cleanup main `f07562e`).

## F7 live acceptance and release 0.0.1 — 2026-09-29

The approved one-click installer concept is now captured as a design-only spec
at `docs/superpowers/specs/2026-09-29-one-click-installer-design.md`. It selects
a Docker-first, checksum-bound v0.0.2 package with safe testnet/shadow defaults,
Linux-only Bash lifecycle commands, Docker Engine/Compose v2, optional explicit
user-level systemd integration with Compose fallback, migrations 001–005,
bounded recovery, and an isolated Linux acceptance matrix. macOS, Windows, and
PowerShell are explicitly out of scope. The written spec is approved and its
task-sized TDD plan is at
`docs/superpowers/plans/2026-09-29-one-click-installer.md`. No installer scripts,
Compose changes, dependency installation, privilege action, or external
mutation were made. Plan Task 1 now freezes the three closed Draft 2020-12
release/config/state contracts and Linux-safe non-secret templates: product
`0.0.2`, chain `31611`, shadow source mode, payment disabled, loopback ports,
digest-only images, and exact migrations 001–005. No launcher or mutating
installer behavior exists yet. Independent Task 1 review removed the impossible
self-referential outer archive digest from the embedded manifest, added exact
launcher digest bindings, excluded P3 payment/grant inputs from installer
authority, and closed image references against trailing whitespace. Task 2 is
now implemented as an offline-only ZIP verifier/materializer: it requires the
independently supplied outer SHA-256, rejects unsafe/colliding/special/oversized
members and incomplete or changed inner inventories, validates the closed
release/migration identities, and publishes only a fully verified private
directory without executing archive content. Independent Task 2 review then
closed six archive races/bounds: verification now snapshots bounded bytes from
a nonblocking single-link descriptor before hashing/parsing; preflights the
non-ZIP64 single-disk central directory before stdlib allocation; requires the
exact approved asset/migration path set; rejects parser-altered NUL and all
control names; and publishes through Linux `renameat2(RENAME_NOREPLACE)` against
a bound parent directory. FIFO inputs and raced destinations fail without
publication. Task 2 re-review exposed two further divergence points, now closed:
temporary creation, every directory/file write, cleanup, and no-replace publish
are all relative to held directory descriptors, with selected-path identity
revalidated before success; parent replacement cannot redirect bytes or create
a false empty publication. EOCD-adjacent or embedded ZIP64 locator/end records
are rejected before `ZipFile`, so its parsed directory cannot exceed the
preflighted ordinary central directory. Task 3 now adds a Linux-only Bash
entrypoint and bounded Python runtime for closed preflight, private reference-only
configuration, atomic `CONFIGURED` state, read-only Docker probes, and an exact
digest-approved dependency command. It supports the frozen Ubuntu/Debian/Fedora/
RHEL and amd64/arm64 matrix, requires Bash 5.2, Docker 27, Compose 2.30, 4 GiB
free disk, 2 GiB memory, the local Docker socket, safe install ancestry, and
three available loopback ports. Ambient Docker/Compose/proxy authority is
rejected; dependency mutation is impossible without `--install-deps` plus the
exact NUL-joined command digest, and tests use only injected fakes. The verified
archive allowlist now includes the digest-bound runtime helper and its closed
schemas. Task 3 deliberately stops at `CONFIGURED`: Compose, migrations,
systemd, health, lifecycle, and release building remain Task 4+ boundaries.
Task 4 must still freeze the shadow fixture/runtime mapping, report-token
handling, one-migrator/lock behavior, immutable image identities, service
topology, and readiness semantics before it can mutate Docker state. The
current development environment does not provision `shellcheck`; no download
was attempted.

Task 3 independent review then found that the first vertical stopped its trust
checks too early. The repaired boundary now requires the exact Task 2 receipt,
matches its independently supplied outer digest/destination/manifest identity,
rehashes the complete materialized inventory, and rejects duplicate JSON keys.
All config, secret metadata, release/state identities, canonical versions and
host facts are validated before root creation. New installs retain a private
root descriptor and lock through descriptor-relative config/state publication,
revalidate the selected pathname, and remove invocation-owned partial output on
failure; retries validate and preserve matching state/config and reject corrupt
or conflicting installations. The launcher clears shell-startup authority
before entering Bash and passes numeric `BASH_VERSINFO`. Docker probes bind the
local socket in exact argv, suppress child output, close timeouts/errors, and
only missing installable Docker prerequisites can enter the exact preview plus
typed-digest dependency flow. Compose and all Task 4 mutations remain absent.
The second review repair binds the receipt to the verifier-produced digest of
the archive's full `SHA256SUMS` bytes, so coordinated member/inventory rewrites
cannot reuse the receipt. Install ancestry is now opened component-by-component
from `/` with `openat`/no-follow identity checks, while one descriptor-bound
lifecycle lock covers reconciliation, creation and publication. Mixed platform,
architecture, Bash or resource failures cannot enter dependency installation;
dotenv secret references reject all dollar/backtick/control expansion syntax;
and the interactive digest prompt is stderr-only so stdout remains one JSON
object.
The final R1 repair separates authority from the mutable receipt: Task 3 now
requires an independent `--inventory-sha256` and compares it to both the receipt
and the freshly rehashed full inventory. The Task 2 verifier emits this digest;
Task 6 must capture it directly from that completed verifier invocation and pass
it internally. A direct installer call without it fails before filesystem or
process activity, while the normal bootstrap contract still asks the end user
only for the published outer archive SHA-256.

Task 4 now provides a fail-closed shadow Compose projection and bounded
orchestration policies. Seven digest-only roles map installer `shadow` to
runtime `fixture`; only edge publishes `127.0.0.1:3000`, while metrics and all
service networks remain internal. Database password and report token are
separate private file references. The existing gateway migrator remains the
sole SQL applier and now binds the complete SQL byte inventory to both reviewed
001–005 constants and the verified release manifest before any database
mutation. It requires an exact ledger prefix plus a total-deadline nonblocking
advisory lock, refuses missing/extra/changed SQL and unknown/gap/duplicate/
checksum/post-005 state, and resumes only the missing committed suffix. The
projection restores application healthchecks, non-root users, resource bounds,
required mounts/aliases, the loopback public origin, and the report engine
commit input. Compose tmpfs mount options are quoted as single parsed entries.
Health requires both `SIMULATED_SOURCE` and
`EXTERNAL_GRANT_REQUIRED` within its monotonic total budget. Partial startup,
lost port, or health failure stops only the candidate. Optional systemd is
restricted to the exact private user-unit root; unsafe rendering is rejected
and reload/enable failure restores the prior unit or returns Compose fallback.
The source manifest remains `runnable=false` with null images until Task 6 binds
real reviewed digests. No Docker, database, or systemd mutation was performed.

Task 5 now adds the Linux `liqvera.sh` lifecycle wrapper and a closed,
atomically persisted lifecycle journal. One nonblocking descriptor-root lock
serializes status/log/start/stop/update/rollback/uninstall operations. Updates
consume only an already verified immutable staged release, record every durable
boundary, require a coherent backup receipt and exact 001–005 compatibility,
health-check the candidate before atomically switching `current`, and resume
non-irreversible crash phases. A migration-committed uncertain phase never
blindly reruns and requires compatible forward recovery or explicit restore;
down migrations do not exist. Default uninstall removes runtime only and
preserves configuration, logs, backups and volumes. Purge uses an exact token
bound to the install root, release and five named volumes, rejecting symlinked
or broad targets. Production Compose update remains deliberately fail-closed
until a reviewed database-ledger/coherent-backup adapter exists; ordinary
start/stop/logs/down use fixed absolute Docker argv without `--volumes`.

Task 5 independent review repair now records migration uncertainty before the
external call, reconciles an atomic `current` switch from the on-disk pointer,
and keeps one stable Compose project/data identity through update. Partial
start and health exceptions clean up and preserve the original failure. Health
requires the exact six unique running/healthy services; the canonical Compose
bytes and closed shadow-only runtime environment are revalidated before every
Docker call. Root replacement is detected against the held lock descriptor
before state publication. Purge removes containers first and the production
adapter verifies exact Compose ownership labels before deleting volumes. Token,
password and signature log forms are redacted, and the generated user unit now
passes the mandatory `--install-root`. Focused lifecycle/systemd/Compose checks
passed 59 tests; full installer+graph passed 394 tests. Real Docker/database/
systemd and destructive purge remain NOT_RUN.
The bounded re-review repair additionally binds all six runtime image values to
the immutable release metadata, performs lifecycle state and pointer writes
through the held root descriptor, and rejects root replacement around external
callbacks. Status uses the same pointer reconciliation path as mutations.
Readiness now requires exact unique running services, migrate exit zero and the
closed shadow blockers; log collection is streaming, byte-bounded and timed.
Volume ownership parsing preserves the full Compose project before the fixed
volume suffix. Second-cycle focused checks passed 63 tests and full
installer+graph passed 398 tests.
Final Task 5 code re-review removed an unsupported gateway CLI readiness probe.
The adapter now performs a direct proxy-free bounded loopback `GET /readyz`,
accepts only 200/503 JSON within 64 KiB, and validates the real gateway closed
readiness fields plus mandatory safe blockers. Focused lifecycle checks pass 27.
The final bounded correction targets the actually published edge endpoint at
`127.0.0.1:3000/readyz` and accepts only the reviewed safe-shadow blocker set;
unknown, storage, source and artifact-integrity blockers fail health. Focused
lifecycle checks pass 28.

Task 6 now provides an offline deterministic ZIP builder, detached outer
checksum, standalone bootstrap source, exact inner inventory and independently
verified materialization with explicit executable/data modes. The builder reads
only a closed tracked allowlist from the exact clean HEAD, binds commit/tree,
Compose, launchers, migrations and six immutable image references, and refuses
mutable tags, missing image authority, dirty/wrong subjects or existing output.
The bootstrap passes the verifier-produced inventory digest internally to the
installer; ordinary users do not invent that authority. Fixture builds are
byte-identical and verifier-accepted, including a UID-10003-readable 0644
migration projection. The production archive remains truthfully `NOT_BUILT`:
the tracked source manifest is `runnable=false` with six null image digests and
no reviewed registry image lock exists. No placeholder or mutable image was
promoted, and no network/publication occurred.

Final release review found that the verified archive stopped at configuration
instead of becoming an installed runnable release. The repaired vertical now
copies only verifier-rehashed payload bytes into
`releases/0.0.2-<archive-prefix>`, writes an inventory-bound lifecycle record,
switches `current`, renders the exact six digest-only image references, and
invokes the existing start/health lifecycle. Lifecycle use revalidates the
full `SHA256SUMS` inventory and compares mutable `release.json` identities to
the embedded verified release manifest, so coordinated metadata and env image
rewrites cannot replace image authority. Materialization explicitly applies
0755 launcher/directory and 0644 non-secret data modes even under umask 077.
Focused archive/contracts/runtime/lifecycle verification passes 137 tests.
The five application refs now use anonymously pullable Docker Hub names with
the unchanged externally verified multiarch index digests; PostgreSQL remains
the pinned official digest. No release/tag/push occurred in this repair step.
The bounded security follow-up moves the transient verifier receipt outside
the exact package inventory, publishes the stable root lifecycle wrapper used
by the user-systemd unit, makes non-secret release directories UID-10003
traversable, admits only the two reviewed secret-file env keys, and rechecks
current release identity against the independently pinned install state on
every lifecycle read. Focused package/archive/runtime/lifecycle/systemd checks
pass 155 tests.

Task 7 now adds a non-publishing, read-only Claw workflow and a Linux-only
operator contract covering the supported distro/architecture matrix, exact
bootstrap and stable-wrapper commands, safe defaults, bounded logs/status,
recovery, forward-only migrations, data-preserving uninstall and token-bound
purge. The checked-in matrix uses mocked host facts and is labelled contract
evidence; a real isolated clean-host Docker run remains `NOT_RUN`. The prior
installer archive hashes are explicitly stale after integration repairs and
will be replaced only by two byte-identical builds from the final Task 7 docs
commit, each accepted by the independent verifier. Publication remains held
for exact-fingerprint independent reviews.
The frozen Task 7 release subject is `55f08c586d009c1b6fd7cd60de12025777d2bea3`
/ tree `ad8a205d3ddb7faae69e914fbb2ebdb471f05848`. Two clean builds are
byte-identical at archive SHA-256 `a6f3c083…1aad17d`; both independent verifier
runs report 25 files and inventory `ad66569f…ca68bd2`. The retained out-of-tree
asset set includes the 970-byte bootstrap, its detached checksum, the 41,157-byte
archive, its detached checksum, and the 22,093-byte verifier. Nothing is
published; clean-host Docker acceptance remains `NOT_RUN`.
Final lifecycle review reproduced the narrower crash window after atomic
`current` rename but before install-authority persistence. Recovery now relaxes
authority only when the durable operation journal's exact verified candidate
matches the on-disk pointer; it immediately republishes install authority and
closes the operation. Ordinary status and non-journaled tampering remain strict.
The same final review closed a root-swap window after the initial health
callback: the held root identity is now asserted before either the healthy
no-op return or any adapter start effect. Operator docs now require detached
verification of the verifier itself, provide the closed two-secret-file config,
and state truthfully that production update/rollback remain fail-closed until a
coherent backup and migration-ledger adapter exists.
Release review then found that the documented detached verifier still imported
`jsonschema` and loaded its schema relative to a repository checkout. The
verifier now freezes the exact v0.0.2 closed manifest contract in its standalone
asset, uses only the Python 3.9+ standard library, and is exercised from an
isolated download directory under `python -I`. The purge confirmation boundary
now emits a canonical `liqvera-purge-preview/v1` JSON object containing the
exact five targets and root/release-bound token, then exits without mutation;
the confirmed second invocation remains required. Focused archive/lifecycle/
operator checks pass 77 tests. All earlier v0.0.2 archive hashes are stale
until the post-fix double build is recorded in a separate evidence commit.
During authorized multiarch publication the production web Docker build exposed
strict TypeScript narrowing gaps in receipt verification and the reviewed JS
x402 bridge import. The minimal source typing repair preserves all runtime
guards; web production build and all 20 browser tests pass before image rebuild.
Authorized GHCR publication completed all five amd64/arm64 OCI indexes with
SBOM/provenance attestations. Capture/report/gateway bind source `9505cd8`; the
web typing repair required source `a435954`, which also binds web/edge. The exact
index digests plus official multiarch `postgres:16-alpine` digest are frozen in
`installer/manifests/image-lock-v0.0.2.json`; source manifest is now runnable.
Clean production builds from `5a1e8dc` were byte-identical: archive SHA-256
`3754f5128f42b3d1565a72511e1c369d45309d0d44ae7798f7a1337ea9ffd79a`,
inner inventory `db30f81def0faf3a3ad72680bb4b9d0dddf5d56a844091ae9e6e063cbcf7071a`,
25 files. Both archives passed independent materialization verification.

Follow-up v0.0.2 preparation advances only root product VERSION to `0.0.2`;
component versions remain unchanged. New sealed A07 result
`b31bc68310c471d35de079d1e0a13232aa39dff4e99b42a9d21b9ce2dbe770de`
at commit `9f875a1ddc13cbf77242d5aadf6508b69756c022` / tree
`37324fcf3ae4c9699bee8383f5755d7802634ed6` passed canonical
`SOURCE_UNAVAILABLE`, with no fixture fallback or emitted artifact; its A07
evidence hash is
`66ed10ff63a57b66cdd222e733c7098609f82aaff12392aba281d711c490efdb`.

| Case | Status | Exact evidence |
| --- | --- | --- |
| A07 | PASS | result `b31bc683…770de`, evidence `66ed10ff…efdb` |
| A13 | PASS | retained live result `53830fe…57e61`, tx `0xfb5ab4a116966204dcece95a7ff099f53494074d84584ad072e140ff25453c06` |
| A14 | PASS | same retained result and transaction; settlement count remains one |
| A29 | PASS | v0.0.1 credential-disabled anonymous recursive clone |

Together with local A01/A08/A09/A27/A30, the multi-result projection is 9
PASS, 21 NOT_RUN, zero BLOCKED_EXTERNAL, and zero FAIL. It remains INCOMPLETE:
the 21 cases were genuinely not executed, and no single runner has an overall
PASS. No v0.0.2 build, push, tag, or release has occurred.

Liqvera v0.0.1 is published at
`https://github.com/Dimkox/liqvera/releases/tag/v0.0.1`; the immutable tag
targets `a0fd5f0884a3fd1a6663982ea5df387b47528bdd`. Public re-download hashes
passed: source zip `a6d8a6adb4350f1bf3f30c719e3f3c0e24527fc2289cb256fa50e2b9cc8ae2d8`,
release notes `f1ddb3fa85a49c9cccc280d0bd8cf66d1f2b0a1428473174813ba3981bf27b7f`,
manifest `220a53603360adc43c27bd9a711440274239558ba2c1c2da0b0ffbe4cdd7100d`,
and `SHA256SUMS` `b002e6b3bef3d5faa66c7ddbf8b8d07e157c6b76f4db33d0ce8d2c028827ec19`.
A credential-disabled anonymous recursive clone passed A29 and observed root
VERSION `0.0.1`, kernel VERSION `2.0.19`, and submodule commit
`cb9af4073ba6c3d515145164d771c75ebdfa3224`. The change package is now
`released`. This post-release metadata commit is intentionally after the tag
and does not alter published bytes.

Remaining limitations are unchanged: the retained full live result is overall
FAIL because of its historical A08/A09 interpreter defect even though A13/A14
PASS; the corrected candidate is INCOMPLETE with honest NOT_RUN/BLOCKED cases;
all 156 frozen vectors remain NOT_RUN; no hosted deployment, mainnet, custody,
private venue, or exchange mutation is claimed.

Release preparation now records two sealed results without copying their
private paths, signatures, or payment payload. The live result
`53830fe2…57e61` at `ca9e04c` has A13/A14 PASS on one transaction
`0xfb5ab4a116966204dcece95a7ff099f53494074d84584ad072e140ff25453c06`,
one settlement, 50 confirmations, and zero buyer native-gas spend; its overall
status is nevertheless FAIL because A08/A09 accidentally used system Python.
The corrected offline result `4799bce9…84d6` at `76c0b63` is INCOMPLETE with
5 PASS (A01/A08/A09/A27/A30), 4 BLOCKED_EXTERNAL, 21 NOT_RUN, and no FAIL.
That historical candidate used root product VERSION `0.0.1`; the current
follow-up candidate is `0.0.2`. Component versions remain unchanged.
The preparation notes and tracked manifest are historical pre-publication
inputs; the exact published hashes and A29 result above supersede their pending
fields without rewriting the immutable tag.
The first verifier on the preparation commit correctly rejected the four new
tracked paths as absent from repository inventory. VERSION now has an explicit
build-packaging classifier and all four paths have graph owners; the complete
graph suite passes 229 tests. A fresh final verifier was required because
this inventory repair changed the repository fingerprint. That final verifier
and all five independent reviews, including the artifact-bound release review,
subsequently passed. The F7 package has advanced through `verifying` and
`reviewing` to `ready`; this metadata-only transition commit changes the final
Git identity and requires the usual receipt refresh before publication.

The local P3 authorization boundary now follows the facilitator capability
observed by the approved analysis: exact Permit2 with the
`eip2612GasSponsoring` extension, not the earlier EIP-3009 assumption. The
gateway binds the official x402 2.16 canonical Permit2 and exact proxy constants,
requires MUSD's EIP-2612 domain, hashes both signatures out of durable correlation,
and verifies a byte-canonical `settleWithPermit` call before accepting the exact
Transfer/finality evidence. The P3 plan and byte-exact grant bind the method,
addresses, approval mode, required extension and identity-policy version. The
browser uses the approved read-only RPC only to construct the off-chain permit;
no buyer approval transaction is accepted. Local installed-SDK constants were
verified before the later authorized live run. That run subsequently produced
the retained A13/A14 evidence summarized above; it did not include a buyer
approval transaction.

The first Permit2 review found three fail-closed interoperability defects and
they are repaired locally: the Node operator's former copied plan digest could
diverge from Python, mixed-case wire signatures hashed differently from decoded
ABI bytes, and the official SDK preserves the server extension description when
it enriches EIP-2612 info. Node now derives its digest from the complete canonical
plan and an executable Python-to-compiled-Node regression compares it. Signature
commitments normalize hex case. Production browser and gateway tests now run the
pinned official SDK end to end and validate the recursively merged extension.

Human-gate evidence is refreshed at scope digest
`80efec81ec63901f3b9368643624102d8544422841bbc8fc4c1f2e04691b7df7` from
the user's explicit continuation and one-time testnet authorization. It approves
the exact Permit2/EIP-2612 design, preserves the no-new-migration 001–005 plan,
refreshes both isolated PostgreSQL resources, and identifies the single allowed
facilitator write at `https://facilitator.vativ.io/` for exactly 0.01 test MUSD,
one submission, zero buyer native gas and confirm-only UNKNOWN handling. These
records are local workflow evidence, not credentials or the byte-exact short-lived
P3 grant/wallet payload; no payment, RPC call, database write or migration was
performed while recording them.

The first live P3 preflight failed safely with `PAYMENT_NOT_READY`; the quote
remained `READY` and the ledger contained zero attempts. Vativ advertises its
method per asset under `/supported` `kind.extra.assets[]`, while the initial
local parser expected a top-level `kind.extra.assetTransferMethod`. The parser
now requires exactly one matching MUSD entry with the pinned address, `MUSD`,
18 decimals, EIP-712 `Mezo USD`/`1`, Permit2, and `supportsEip2612=true`, plus
the sole `eip2612GasSponsoring` extension. Missing, duplicate, malformed, or
wrong-capability fixtures fail closed. No settlement was attempted during repair.

The operator now separates grant parsing for durable replay from authority to
start a settlement. An expired but structurally valid grant may reach the
durable-consumption lookup and can only return its retained `CONFIRMED` receipt
or run confirm-only reconciliation; it cannot call settlement again. An
unconsumed expired grant, including preflight, still fails with
`LIVE_GRANT_EXPIRED`, and the 15-minute maximum lifetime remains enforced before
every first submission. Context binding is enforced before either branch, so a
consumed expired grant with a changed commit, tree, plan, buyer, or payee fails
with `LIVE_GRANT_MISMATCH` rather than reaching retained evidence. Local A08/A09 dispatch also uses the repository's
verified `.venv/bin/python` explicitly and fails closed if that runtime is
missing, avoiding accidental `/usr/bin/python` execution. Focused regression
tests passed without network, wallet, payment, or database activity.

Route `337ef5ec16a0` and change package
`engineering/changes/20260929-f7-live-acceptance-and-release-0-0-1-337ef5/`
are now `released`. Four route-selected analyses were synthesized into sequential
P0–P5 gates. Their initial local-only phases performed no external mutation;
the later explicitly authorized payment and publication produced the retained
evidence summarized above. The earlier local-only route `fd7ffd5cc17f` is
coherently retained as cancelled before implementation. Further payment or
mutation of the immutable release remains **NO-GO**.

P0 repairs the A01–A30 runner's semantic validation, tamper-evident evidence, final
clean Git binding, local-vs-real A30 classification, and fault/mutation suite.
P1 executes locally eligible cases into a fresh mode-0700 out-of-tree result;
missing real prerequisites remain explicit. P2 permits only separately granted
allowlisted public reads. P3 first implements and independently reviews real
authorization identity, finality, and browser x402 wiring, then requires a new
exact grant for one human-confirmed Mezo Testnet envelope: chain 31611, pinned
MUSD, exactly 0.01 test MUSD, distinct approved buyer/payee, one submission
maximum, and a numeric test-BTC gas cap. Any possible broadcast followed by
timeout is `UNKNOWN`, never retryable; only exact confirmation reconciliation
may continue.

The first P0/P1 reviews failed because exit-zero test commands could certify
their own prose claims, the plan accepted arbitrary command capability, status
reasons were open, sealing was not atomic, and retained evidence lacked a
standalone verifier. The repair keeps only five fully configured local cases
(A01, A08, A09, A27, A30), validates a closed observation shape for each, and
gives every other local case a canonical prerequisite-specific `NOT_RUN`
reason. `BLOCKED_EXTERNAL` is restricted to non-local cases with the one
canonical missing-grant reason; live mode remains unavailable because no exact
grant contract exists.

The only executable capability is the pinned current Python running the exact
checked-in dispatcher and case ID with a constructed offline environment; plan
shells, alternate argv, environment inputs, symlinks, hardlinks, replacement,
and mutation are rejected. The runner hashes the exact parsed plan bytes,
revalidates evidence and the plan, then performs its final clean commit/tree
check immediately before atomic link publication. Results and evidence are
made read-only and are **tamper-evident, not immutable**. The standalone
verifier reloads schema and semantic algebra and rehashes the result, runner,
plan, and every evidence object while rejecting linked/replaced files.

Regression coverage includes status contradictions, generic reasons, exact
A13/A14 receipt linkage, plan/link mutation, evidence symlink/hardlink attacks,
post-seal mutation, and interrupted publication. Final clean-HEAD acceptance
and full verification must be regenerated after this repair commit. Reviews
remain failed/stale until independent rerun; P2–P5 remain gated.

The first real producer→consumer run of the repair reached all five commands
and exposed a Node 22 TAP-format boundary: npm reports `ℹ tests N`, not the
older `# tests N`, so A30's closed observation correctly rejected a zero count.
The parser now accepts both native TAP spellings. Status algebra also
distinguishes a nonzero process failure from an exit-zero semantic-validation
failure; both are FAIL, while an exit-zero timeout remains contradictory.
The next local run reached the intended 5 PASS / 4 BLOCKED_EXTERNAL / 21
NOT_RUN result. Direct invocation of the new verifier then found its script
entry point lacked the repository root on `sys.path`; the entry point now adds
the same explicit repository import root used by other checked-in scripts.

The second review rejected the remaining hard-coded semantic booleans and a
late post-publication Git race. Configured cases now retain the exact pytest or
Node TAP identities observed in process output; the consumer requires a closed
case-specific subset, binds observed subject commit/tree, and additionally
checks the frozen route baseline or vector digest/count/Go-free tree where
applicable. Five per-case unrelated-success mutants are rejected.

FAIL reasons are now a closed four-value algebra with exact exit-code/timing
relationships. Evidence directories are fsynced and sealed bottom-up mode
0500; the root is sealed only after atomic result publication. Both producer
and CLI verifier compare the current clean repository with the sealed subject.
If drift appears in the late window, the canonical result name is atomically
renamed with `.invalid` rather than left accepted. Regression tests cover that
late mutation and post-seal unlink prevention.

The third review narrowed two remaining semantic gaps. A01 now exports the
frozen route baseline to a temporary read-only candidate extraction, runs the
same bounded acceptance-contract command against baseline and current trees,
and retains separate commit/tree, argv, exit, status, and transcript hashes.
The accepted delta is exact: baseline exit 4 because it predates the F7
contract test, while the current tree passes its named checks. The temporary
extraction is removed without changing the candidate or Git metadata.

A27 now supplements its vector identities with the canonical Stage A artifact
verifier and exact CLI decision/closed-enum tests. Evidence requires the frozen
`INSUFFICIENT_EVIDENCE`/non-GO verdict and binds the retained shadow fixture's
path, byte digest, terminal digest, and 38-record count. One-sided A01 evidence
and vectors-only A27 evidence are explicit negative regressions.

The fourth review found two portability/baseline gaps. Nested A01/A27 command
evidence now records a portable CPython implementation/version/executable-byte
identity plus exact argv tail, never an absolute interpreter path. A compatible
system Python can therefore verify evidence produced through the repository
venv while a different interpreter binary still fails closed. A27 now reads
both fixture files directly from the frozen baseline commit and requires the
current byte digest, record count, and terminal digest to equal that baseline;
changing fixture and terminal together is an explicit rejected mutation.

P4 defines Liqvera product release `0.0.1` while retaining inherited/component
package and API versions `0.1.0`, and builds scanned manifest-bound artifacts
plus `SHA256SUMS` from one frozen commit. Final acceptance/evidence stays
immutable outside that subject tree. P5 requires a separate exact publication
grant for a fast-forward of `Dimkox/liqvera` main, annotated `v0.0.1`, draft
GitHub Release, allowlisted asset upload/download re-hash, and final owner
confirmation. Partial publication recovery is additive: never force-push or
move a published tag.

The user approved `scope_and_design_approval` for exact gate scope digest
`82c9cb3127d0b55ca43f34ec816c8349a1d770ef52d0e4293ace580a36820f73`;
this is distinct from the canonical spec-content digest. The external-write
gate remains pending. `migration_or_external_write_approval` is not a blanket
grant and must be
realized as short-lived exact P2, P3, and P5 action records. Any changed tree,
plan, target, envelope, amount, gas cap, artifact, limitation, or remote OID
invalidates its affected grant. Mainnet, real/user funds, custody, private keys,
exchange mutation, deployment, unrelated repositories, and secret inspection
remain forbidden.

The local-only P2/P3 prerequisite slice now adds closed public-read grants bound
to commit, tree, plan digest, case, exact HTTPS method/URL, limits and a maximum
15-minute lifetime. It rejects credential-bearing URLs, private or reserved
addresses, changed DNS answers, excess attempts/time/bytes, and unknown
destinations. During that local-only phase no grant was issued and A07/A29 were
`BLOCKED_EXTERNAL`; the later publication run completed A29 as recorded above.

The gateway now has explicit EIP-3009 identity and a twelve-confirmation
canonical Mezo Testnet finality policy. A separate exact payment grant binds
chain 31611, pinned MUSD, exactly 0.01 test MUSD, distinct buyer/payee, candidate
commit/tree/plan, one settlement submission, a 15-minute ceiling and maximum
`100000000000000` wei (0.0001 test BTC) gas. Ordinary startup supplies no grant,
performs no facilitator call, and reports `EXTERNAL_GRANT_REQUIRED`. The browser
registers the pinned official core/EVM x402 client against an injected wallet;
an ambiguous post-signature result returns only recovery and is never retried.
At that local-only prerequisite phase, no network, wallet, RPC, facilitator,
payment, database, release, or secret action occurred. The later one-time grant
was consumed by the retained A13/A14 run and cannot authorize another payment.

The follow-up security repair removes process-local grant consumption. Migration
003 adds an append-only one-to-one grant-digest/grant-ID/payment-attempt relation;
the ledger consumes it atomically with `VERIFIED -> SUBMITTING`, before the sole
facilitator call. A conflict leaves the attempt unsubmitted, while any committed
row remains spent across restart and replicas. The reviewed EIP-3009 binding now
decodes the exact `transferWithAuthorization` selector and all nine ABI words,
including the signature commitment, rather than accepting a nonce substring.
Grant expiry is rechecked during initialization, verification and immediately
before settlement. Ordinary startup still composes `null` authority and performs
no external call. The migration was authored and tested structurally but not
applied to any database in this local-only phase.

The exact EIP-3009 activation model now follows the official x402 scheme: the
buyer signs the exact transfer authorization while the facilitator broadcasts
and pays gas. The approved numeric test-BTC ceiling is therefore a buyer-native-
gas spend cap; this exact path requires a zero buyer native-balance delta and
does not claim control of facilitator gas. Confirmation checks a non-buyer
`tx.from`, before/after buyer balance equality, the exact token Transfer and
twelve-block canonical finality. Missing observations enter manual review.
The transactional adapter retains restart/concurrency coverage; migration 003
was not applied to any database.

The runner now exposes the same closed live-case orchestration used by the fake
end-to-end suite. Its authority envelope binds the current commit/tree, an
internally derived canonical plan, expiry, exact A07/A29 request bodies and
bounds, and one shared A13/A14 payment grant. A13 executes once; A14 can only
reuse its confirmed transaction, while UNKNOWN remains spent and blocks A14 in
confirm-only state. The CLI accepts only `--live-grants`, never a boolean. With
a valid exact bundle it can now execute only A07/A29 through the bounded
production public-read transport and seal closed subject/plan/grant/target/
response observations; without a one-time grant A13/A14 reduce to
`BLOCKED_EXTERNAL` with `EXACT_PAYMENT_GRANT_ABSENT`. The retained authorized
run is separate evidence and ordinary offline results remain externally blocked.
Public-read grants now carry a canonical UUID and a digest derived from their
entire closed grant document. The executor derives the one-shot marker name
itself inside a mode-0700 state directory and fsyncs both marker and directory;
operators can no longer select an alternate marker filename to replay a grant.
Browser transport bounds are executable tests: timeout, redirect rejection,
credentials omission, and declared/streamed response caps all fail closed.
The first full verifier after adding these four files exposed only the expected
repository-inventory omissions (five graph tests); all four paths are now bound
to their existing runtime owners and the focused graph checks pass 5/5.
After that repair, the pinned PR verifier passed: 1,217 Python tests plus 85
subtests, coverage, secret scan, SQL safety, Ruff, Bandit and configuration
scan. Focused evidence also includes 68 acceptance/contract tests, 17 browser
tests and 24 gateway tests (five disposable-PostgreSQL tests intentionally
skipped). No public read, payment, database migration, secret access or other
external action occurred.

The P2 semantic repair removes the earlier transport-only interpretation.
A successful Hyperliquid response can no longer pass A07: the runner builds and
invokes the real gateway `HttpReportService.build` adapter against a controlled
503, requires canonical `SOURCE_UNAVAILABLE`, and proves no fixture fallback or
artifact. A29 no longer claims PASS: Git/libcurl does not expose a sufficiently
reviewer-verifiable preemptive network-byte counter. Hard wall-time, process
memory, stdout/stderr, single-file and aggregate-disk envelopes are implemented
and tested, but the runner reports `A29_NETWORK_BYTE_CAP_UNENFORCEABLE`.
Per-case errors become sealed FAIL rows rather than aborting the whole result.

Live operators must provide three explicit inputs: `--live-grants` pointing to
the exact current-subject bundle, `--operator-state-dir` pointing to a
pre-existing external mode-0700 directory, and a new external `--output` path.
The create-once mode-0400 journal identity file contains an issuer-approved
UUID; its exact digest and UUID are bound into the P2-only bundle and both P2
grants. The CLI validates it before case execution, and marker names derive
from grant UUID plus full grant digest. A different journal fails pre-I/O.
Browser payment deadlines now
remain active through complete body streaming; a stalled-body regression is
covered. P3 code is locally activatable for a separately approved exact grant,
human wallet signature, configured facilitator, approved read-only RPC, and
applied migration 003; none of those live inputs was consumed here.
The exact P3 inputs are: one short-lived byte-exact A13/A14 grant bound to the
clean commit/tree and canonical P3 plan; lowercase buyer and distinct payee;
scheme `exact`, broadcaster `facilitator`, chain `eip155:31611`, the frozen MUSD
address and `10000000000000000` atomic amount; one-submit budget; and
`max_buyer_native_gas_wei=100000000000000`. The grant additionally binds
`asset_transfer_method=permit2`, canonical Permit2
`0x000000000022D473030F116dDEE9F6B43aC78BA3`, exact proxy
`0x402085c248EeA27D92E8b30b2C58ed07f9E20001`, approval mode
`eip2612-gas-sponsoring`, required extension `eip2612GasSponsoring`, and identity
version `liqvera-permit2-eip2612-identity/v1`. The human wallet supplies only
the off-chain Permit2 and EIP-2612 signatures; no buyer chain approval is allowed.
The configured facilitator performs the sole submission,
and the approved read-only Mezo RPC supplies chain, receipt, transaction,
canonical-block and before/after buyer-balance observations. Migration 003 must
already be applied through a separately approved database operation.
Migration 004 persists the confirmation observations in the append-only receipt
row so later A13 evidence does not depend on a mutable RPC re-query. It has an
explicit zero-legacy-receipts stop condition. The P3 CLI is separate from P2:
`--p3-live-grants` validates the linked bundle and, without an injected human
wallet signature/output seam, seals A13/A14 as
`HUMAN_WALLET_SIGNATURE_REQUIRED` before any external I/O.
The opt-in PostgreSQL command is
`TEST_DATABASE_URL=postgresql://.../liqvera_f4_test_<suffix> TEST_DATABASE_DISPOSABLE=1 npm --prefix apps/mezo-gateway run test:postgres`;
those are the only two test-specific environment names. It was not run because
no explicitly disposable database URL was provided or inspected.

The user subsequently approved and applied migrations 001–004 only to isolated
target `docker://liqvera-f7-postgres/database/liqvera_f4_test_fdae49d`.
The first migrator run applied all four files, the second was idempotent, and
the real PostgreSQL suite passed 6/6: twenty independent pools had one grant
winner, restart admitted zero further consumption, injected rollback retained
`VERIFIED` without consumption, and append-only update/delete were rejected.
No credential value is retained and this evidence grants no other DB or network
operation.

P3 now has a separate bounded operator executable (`npm --prefix
apps/mezo-gateway run p3-operator -- ...`) and the acceptance runner accepts its
closed linked A13/A14 result. It consumes a byte-bounded exact P3 grant and a
human-wallet-produced signed x402 payload—never a private key—and requires
exactly one of `DATABASE_URL` or `DATABASE_URL_FILE`, an HTTPS facilitator URL,
and a read-only HTTPS Mezo RPC URL. Before network I/O it checks the current
clean commit/tree, canonical P3 plan and exact 001–005 migration checksums.
Durable consumption/`SUBMITTING` precedes the sole settlement; pending or lost
responses remain spent and confirm-only, with sealed A13/A14 observations using
the canonical `PAYMENT_CONFIRMATION_PENDING` blocker rather than a false wallet
omission. Deterministic fake E2E covers confirmed and pending paths plus replay.
No live payment or network call was performed.

The P3 grant also binds the exact facilitator URL, read-only RPC URL and a
stable SHA-256 identity of the credential-free PostgreSQL endpoint
(`scheme//host:port/database`). Another host, port or database therefore fails
before external use. Grant, signed-payment and database-URL files must be
private single-link regular files and are opened with `O_NOFOLLOW` under an
inode/size check. The canonical P3 plan pins both HTTPS endpoints and names the
database identity mechanism.

A14 is produced by a second independent operator invocation, not by reusing an
in-process A13 observation. It must reload the durable grant consumption and
attempt, return the same confirmed transaction with `settlement_count=1`, and
cannot enter the settlement branch again.

Final trust-boundary repair snapshots the already validated grant and signed
payment bytes into create-exclusive private files, passes their SHA-256 digests
to Node, and never reopens the operator-supplied paths. PostgreSQL endpoint URLs
with any query, `sslmode`, socket override or fragment are rejected before Pool
construction. Additive migration 005 persists the actually observed canonical
confirmation count (minimum 12), so fresh and durable replay results have the
same runner-compatible receipt shape. The user then approved and applied
migration 005 only to retained isolated database
`liqvera_f4_test_fdae49d`: pre/post `receipts=0`, exact 001–005 ledger,
idempotent second migrator run, and `confirmations int4 NOT NULL CHECK >= 12`.
The behavior suite could not reuse that retained database because its fixed
upgrade fixtures require a fresh target; no cleanup was performed. Separately
approved `liqvera_f4_test_9c86bf9_verify` passed all 6/6 PostgreSQL tests,
including twenty-pool one-winner, restart, rollback and append-only behavior.
The operator accepts only `127.0.0.1`, `::1`, or `localhost` for PostgreSQL;
every `localhost` resolution must itself be loopback. Remote DNS and
non-loopback numeric addresses fail before Pool construction. This invariant is
bound in both the canonical P3 plan and exact grant.
Final migration identities are `001_ledger.sql`
`bc127e55c876961112f33ca2abdfac01827769d6156ddba2f42856d070c75b3b`,
`002_fix_immutable_ledger_identity.sql`
`981f48215e64fdd0fb72be5a6df78238cf8050de722adb454b4e28b1940ccbcb`,
`003_live_grant_consumption.sql`
`bbedff6137a648166b77233c56a466e46247480b404b8829b64f29123109bcf0`,
`004_receipt_confirmation_provenance.sql`
`96bba00d344d81670a4c0f8741186004910e959f374ecd77ce78268d52fd465a`,
and `005_receipt_confirmation_count.sql`
`e99e5cffab60c08dfb1cd73d13caf2915f31aec542c26c87b016d0e125a23b11`.
The clean pinned verifier passed 1,219 tests plus 85 subtests at fingerprint
`5fde3a92ac8a464b32d0630a531bdb790516c9c96cab922509a310c699cb0ce5`.
Focused repair checks pass: 69 acceptance/contract tests, 18 browser
tests, and 29 gateway tests with five explicitly disposable-PostgreSQL skips.
The clean pinned PR verifier passed 1,218 tests plus 85 subtests at fingerprint
`8dda2e9858734b76a624a8ec309ccc22177845a54526babd15eda4b78ba8b499`.
The clean pinned PR verifier passed 1,218 tests plus 85 subtests, coverage,
Ruff, Bandit, secret scan, SQL safety, contract structure and configuration
scan at fingerprint `2749fdfb20570131d0d15e80171eaa5a885fdf24a8bfd54b13003de4c173acc5`.
No public read, clone, payment, database migration, secret access or other
external action occurred.

## F6 local UI and operations verification — 2026-09-29

Route `26ffb293d4ff` and change package
`engineering/changes/20260929-f6-local-ui-and-operations-verification-26ffb2/`
have completed the four route-selected read-only analyses. The approved design is
strictly local: a deterministic browser harness with fake EIP-1193, same-origin
API, storage, crypto, timers and test-only adapter; the smallest injectable UI
seam; fixture-egress correction with resolved-profile assertions; internal-only
metrics observability; the canonical restrictive CSP; and exact README,
runbook, handoff and acceptance truth.

The repository owner re-approved current exact scope digest
`20d2f1aae1a80242fa6b178e0416a1831dee03948c7f740cadf3ecea6a1ccb99`
after the typed evidence paths changed,
and the package is `approved`. The recorded migration plan is explicitly a
no-op: this phase does not start containers, create a database/schema/volume,
or perform an external write. Any later need for those actions stops for a new
exact approval.

The implementation adds production-used browser policy and orchestration seams
with fourteen deterministic Node scenarios for wrong chain/switch, payer-preserving account
and chain changes, typed pre-submit cancellation, ambiguous outcomes, exact
reload request/idempotency identity, fixture gating, and one-call
no-resettlement. The orchestration harness records the real recovery/payment
decision path through fake API, session persistence, notices, wallet events,
and adapter calls. Wallet events now bind through a provider-to-state-sink
module whose production dependency surface has no payment callback; account or
chain events can only refresh wallet state. A wallet revalidation failure is
handled before the guarded submission try: it preserves the clear guard,
persists nothing, invokes no adapter, and renders a no-payment warning.
The production composition is structurally locked to the direct state-only
sink call, so wrapping an event with `submitPayment` fails the focused suite.
A provider rejection now applies fail-closed disconnected state without an
unhandled rejection, resolves the serialized event queue, and permits the next
wallet event to recover normally. Four static operations tests resolve both Compose profiles
and assert exact services, networks, loopback publication, per-profile secret
identity, exact users/tmpfs/mount modes/resources, healthchecks, internal
metrics, and CSP. Fixture capture,
gateway, and edge no longer inherit live egress networks. Gateway metrics bind
only to `gateway-metrics` on an internal operations network, accept only
`GET /metrics`, and have no host/Caddy route. Two executable gateway telemetry
tests assert the exact label-free metric set, no high-cardinality identifiers,
404 for other paths, and readiness independent of health. Caddy sends the exact
canonical restrictive CSP including `frame-ancestors 'none'`, without
`unsafe-inline`; source HTML has no incompatible inline script/style.

The exact web install/build is not yet evidenced: an offline
lifecycle-disabled install stopped because the exact Vite 7.1.5 tarball is
absent from the local npm cache, and this no-external route does not authorize
a registry request. The first full pinned verifier completed its checks but
could not record a receipt because the typed spec used symbolic test labels;
v2.0.19 requires existing repository paths. Those evidence references now
point to the real browser and operations test files. A clean rerun and
independent route reviews remain next. The subsequent full run reached the
Python suite and exposed only missing architecture-inventory ownership for the
new F6 package and tests: 1153 tests and 85 subtests passed, while five graph
policy tests failed on the undeclared paths. The inventory now binds every F6
package file and both new test/source artifacts; the exact five-test graph
regression slice passes, and the repaired tree then passed the full pinned PR
verifier before the first reviews. Those reviews correctly rejected helper-only
browser coverage and shallow operations assertions. The current repair binds
the harness to production `resumeFlow`, `submitPayment`, and wallet listeners;
it also closes exact Compose, telemetry, and CSP mutation gaps. Final clean
HEAD `f1667511149c5062443cd2c518ce40d8492b7507` passed the full pinned verifier
at fingerprint `292558635bb303d8cf302468899eba4ac82d2d742ccff8e4939e8cfe886c970b`.
Independent code, test, security, data, and release reviewers all returned
PASS with no findings on that exact fingerprint and did not modify the tree.
Their reports are stored and registered, and the package advanced through
`verifying` and `reviewing` to `ready` with `evidence_gaps: []`. The tracked
state-close commit requires one final verifier and receipt refresh. Production's
x402 adapter remains deliberately unregistered and fixture payment remains
fail closed. This route will not use a real wallet, RPC, facilitator, transfer,
testnet/mainnet payment, live capture/profile, shared environment, deployment,
release, exchange mutation, or push. Static evidence cannot establish runtime
A26 acceptance: all 156 frozen vectors and A26/A30 remain `NOT_RUN`; A13/A14
remain externally blocked.

## F5 local mocked state-machine verification — 2026-09-29

Route `583d09e0cf44` and change package
`engineering/changes/20260929-f5-local-mocked-state-machine-verification-583d09/`
are implementing a strictly fake-only Node vertical with no database, migration,
RPC, facilitator, wallet, transfer, exchange, deployment, release, or push.
Four read-only analyses froze the scope; route `c3dad647a9f8` was cancelled
before implementation because keyword routing attached inapplicable external
write gates to the same local-only intent.

RED tests reproduced that an authoritative confirmation rejected by
`Ledger.confirm` as `PAYMENT_REJECTED` remained ordinary uncertainty in both
`Gateway.read` and `reconcileOne`: neither entered manual review immediately.
The minimal repair distinguishes a confirmation already observed from earlier
payment failures and treats only its binding rejection (plus the existing
manual-review error) as frozen `inconsistent_receipt` evidence. Both paths
retain the fail-closed 202 response, enter paired `MANUAL_REVIEW`, create no
entitlement or delivery, and never settle again.

Nine deterministic scenarios execute real gateway/reconciliation/recovery
orchestration with a structural in-memory ledger, scripted payment port, and
per-test temporary artifacts: direct and reconciled mismatch, post-submit lost
response and HTTP replay, canonical duplicate use, stale verified pre-submit
recovery, bounded null-confirm reconciliation, packaged frozen-state guards,
successful confirm-only reconciliation, entitlement reuse, and reorganization
withholding. The worker success case asserts terminal `CONFIRMED`/`PAID`, one
entitlement, ordered `unknown -> confirm -> CONFIRMED event`, zero settle or
delivery, and no second eligible lease; this kills the test-reviewer's late
`unknown` mutation. After the first reviewers
rejected the original no-op contract double, the fixture now loads production
`Contracts` and packaged `states.json`; it validates receipt shape, a valid
scoped transition, and an unmet-guard `INVALID_STATE`. Reconciliation models
the count returned by the leasing update, records `PAYMENT_UNCERTAIN` below ten
and `MANUAL_REVIEW` at ten, and mismatch tests assert ordered trace plus absent
delivery so the earlier review mutation is killed. The focused file passes 9
tests; the complete gateway suite passes 15 and skips the five
explicitly disposable-PostgreSQL F4 cases when no database URL is supplied.
`MANUAL_REVIEW -> PAID/CONFIRMED` recovery remains an explicit residual: the
worker cannot lease that state and the adapter lacks an idempotent restore-only
operation, so this route does not mock a false PASS. Production identity and
finality remain unresolved, and all 156 frozen vectors remain `NOT_RUN`.

Pinned full verification passed clean implementation HEAD `72ba728092e4041ba0b37f23baa5c6373dbd28f9`
with fingerprint `b467a6f9c3312a70f0a7ae946750c1a5405afa29e6bdab7509e8aaac482c2db1`:
1155 pytest tests and 85 subtests passed together with change-spec, diff,
secret, contracts, SQL, nine Trivy targets, Ruff, Bandit, coverage, and source
stability. Independent code, test, and data reviewers all returned PASS with
no findings on that exact fingerprint and did not modify the candidate. Their
reports are stored in this change package and were registered after the
report-bearing tree passed full verification. With no human gate, the durable
package advanced through `verifying` and `reviewing` to `ready`. The tracked
state-close commit requires one final verifier and receipt refresh on its exact
fingerprint. Do not infer testnet payment, persistence, acceptance, deployment,
or release readiness.

The pre-review pinned verifier execution completed its configured checks but could
not record a receipt because the new typed acceptance entries used the
unsupported key `verification`; the v2.0.19 schema requires `evidence`. After
that correction, the verifier correctly rejected the superseded red-risk
package's untouched generated `UNKNOWN` placeholders even though its lifecycle
state was cancelled. Both packages now have schema-valid typed evidence; the
superseded package remains cancelled and grants no approval. The corrected
packages passed exact validation in the final verifier.

## F4 local gateway and ledger verification — 2026-09-29

Route `725677143509` and change package
`engineering/changes/20260929-f4-local-gateway-and-ledger-verification-725677/`
are `approved` with no human gate. Five route-selected read-only analyses agree
on the bounded implementation: repair the two reproduced TypeScript build
errors, add a gateway-owned Node test harness, and prove cleanup/idempotency
semantics against loopback HTTP and a uniquely disposable PostgreSQL database.

The confirmed recovery defect is cross-component, not schema-level: the report
service documents HTTP 200 `deleted:false` as authoritative already-absent
success after a lost response, while the gateway currently accepts only
`deleted:true`. The adapter regression reproduced that mismatch and acceptance
of an unknown field. The minimum repair now accepts either boolean only in an
exact matching two-field HTTP 200 body. The two reproduced TypeScript errors
are repaired. A test-review P1 then exposed missing executable coverage for
the adapter's internal deadline: the test-first loopback run accepted a valid
response delayed beyond an injected 20 ms deadline because the constructor
still hard-coded 2000 ms. `HttpReportService` now accepts a typed injectable
cleanup timeout while retaining 2000 ms as the production default. The focused
suite reports 6 passes and 5 explicit disposable-PostgreSQL skips, including
fail-closed internal-deadline and caller-abort subtests; typecheck and build
also pass.

The first disposable PostgreSQL run passed migration/rerun and 20-way
idempotency, then exposed SQLSTATE `42703`: migration 001's shared immutable
identity function dereferences `OLD.tx_hash` for an artifact row, preventing
the intended `AVAILABLE -> DELETED` update. The user explicitly answered
“Делай”, approving only the required forward-only 002 function repair and
local disposable verification. Migration `001_ledger.sql` and the frozen
vector catalog remain byte-identical. The repaired disposable suite reports
five passes: fresh 001-to-002 and rerun, 001-only upgrade, 20-way idempotency,
fail-closed recovery, and lost-response convergence with artifact/payment
immutability checks. No dependency upgrade, other migration,
shared database, facilitator, RPC, wallet, chain, exchange, live capture,
deployment, release, or payment action is in scope. The next step is the pinned
route-selected independent code, test, and data reviews.

The pinned v2.0.19 full verifier previously passed clean implementation fingerprint
`55e3ce270b2cdc118ced8ca3daa9ab0bdab59e43`: all diff/spec/secret/contract/SQL,
nine Trivy, Ruff, Bandit, 22-worker pytest, coverage, and source-stability gates
passed. The timeout repair changes that fingerprint; its pinned full verifier
is therefore run only after the coherent repair is committed and clean. Runtime
status is authoritative, and no receipt is treated as current across a tracked
change. Independent code, test, and data reviewers then returned PASS with no
findings on clean HEAD `587bf5c0a5edd1712c4cd3cd3e4ade258fff8ffe` and tree
fingerprint `e88d85fbe2da4789b634f5d2c88bf73beeb9740274c566ba06297f8c1cb4c83b`.
Their coordinator-provided reports are persisted in the active change evidence
directory and registered in the architecture inventory. The report-bearing
tree passed pinned verification, and its exact report paths were recorded as
PASS receipts. With no human gate, the v2.0.19 change CLI advanced the durable
package through `reviewing` to `ready`. That tracked state-close change makes
the preceding receipts stale by design, so the verifier and all three review
receipts are refreshed once more after this commit. The implementation owner
does not self-review.

## F3 offline artifact verification repair — 2026-09-29

Route `08fa9d84745d` and change package
`engineering/changes/20260929-f3-offline-artifact-verification-repair-08fa9d/`
are `ready` with no human gate because the scope is fixture-only and explicitly
forbids migrations and external writes. The superseded broad route
`f6f2495b4648` was cancelled before implementation: its task wording introduced
an inapplicable migration/external-write gate even though its approved scope
excluded both. Four read-only analyses are retained in the active package.

Implementation remains limited to failing-regression-first coverage of the
installed canonical F3 fixture-to-report/bundle/publish/verifier loop, tamper rejection,
duplicate report UUIDs, incomplete publication, packaged resources, and the
confirmed acceptance contract defect. A regression first reproduced rejection
of the runner's real 40-character Git OIDs; the schema now uses a dedicated
40-hex `git_oid` definition while true content digests remain 64-hex SHA-256.
Canonical source tests cover exact build/publish/read/verify, bundle and report
tamper, matching and differing duplicate UUID publication, partial targets, and
pre-rename verification failure. A no-index wheel test installs all four local
packages into an isolated environment, proves imports come from that install,
then exercises both installed F3 commands outside the checkout. The new focused
slice reports 13 passed; the surrounding capture/analyzer/contracts slice
reports 738 passed and 85 subtests. The full PR verifier exposed and now has
repairs for whitespace, typed evidence paths, and graph inventory ownership of
the new package/tests. The final committed-tree run passes diff, both change
specs, secret, contract, SQL, all nine Trivy targets, Ruff, Bandit, and source
stability. The apparent parallel factory/import collisions were reproduced and
are not shared-state races: the failing command used `/usr/bin/python3`, which
lacks the project packages and Hatchling. The same complete 20-test factory,
installation, and canonical F3 slice passes with 22 workers in the pinned local
environment. Hyperliquid SDK 0.24.0 declares `eth-account>=0.10.0,<0.14.0`, and
the provisioned compatible version is 0.13.7, so the stale project pin was
repaired from 0.14.0 to 0.13.7; its characterization and `pip check` now pass.
The final full verifier run from the pinned environment passes: 22 workers ran
`1147 passed, 85 subtests passed` in 67.24 seconds, coverage passed, and diff,
both change specs, secret, contract, SQL, all nine Trivy targets, Ruff, Bandit,
and source stability are green. A final receipt refresh after this handoff
commit is required; route-selected independent code, test, and data review is
the next coordinator action and has not been performed by the implementation
owner.

The first independent code and test reviews then found that JSON Schema's `$`
accepted a terminal newline and that malformed `repository.tree` values lacked
negative coverage. Both `git_oid` and `sha256` now combine their lowercase-hex
patterns with exact `minLength`/`maxLength`; commit and tree share the complete
short, long, uppercase, non-hex, and terminal-newline matrix, while stdout,
stderr, and evidence digests each reject terminal newlines at their exact error
paths. The repaired focused slice reports `21 passed`. The original FAIL review
reports are preserved as evidence; full verification and independent re-review
must bind the new tree before closure. The first post-review full run otherwise
passed 1150 tests and coverage, but correctly rejected the three newly tracked
review reports until their graph inventory ownership was declared.

Independent code, test, and data re-reviews all PASS the repaired candidate
`a24e1ed` at fingerprint
`1e8ebe8852e4d569f7a4c6cf4b9a6a7618f540a5ee923a5bebbd0e6a81b67957`
with no open findings. Their complete reports preserve the original failures,
the repair probes, scratch identities, and `reviewed-tree-modified: no` claims.
The final reports were persisted in `8fc0d3b`; the pinned verifier then passed
`1155 passed, 85 subtests passed` in 66.13 seconds, plus coverage and every
configured PR check. The package progressed through `verifying`, `reviewing`,
and `ready`. Because those durable transitions change the tree fingerprint,
the untracked runtime verification and review receipts are refreshed once more
after committing this state; `scripts/grok_status.py` is authoritative for
their fingerprint currency.
Gateway/F4 through F7, graph orphan cleanup,
network, database, RPC/facilitator/wallet/payment/exchange actions, Compose
start, deployment, release, and push remain outside this route. All 156 broad
acceptance vectors remain `NOT_RUN`.

**Market reports you can verify.** Built for [MEZO ₿](https://mezo.org/) —
[The Mezo Buildathon](https://app.akindo.io/wave-hacks/OVOO0gdrVU8379D10).

## Repository boundary cleanup — 2026-09-28

Branch `chore/repository-cleanup` is an isolated worktree based on merged main
commit `0c2cb97f8048f7da8bd193634f4502f24b0e541e`. Route
`7f0f98e3cdda` and change package
`engineering/changes/20260928-repository-boundary-cleanup-7f0f98/` cover a
repository-only retirement of inherited Go Stage-0 and vendored agent tooling.
Six parallel read-only analyses and the route-selected implementation are
complete. Full route verification passed at clean fingerprint
`aa5925f320da68843a52362e1654549d3a658899`. Independent code, test, security,
and data re-reviews all passed that same fingerprint with no findings; their
reviewer-provided summaries are stored under the active change package. The
v2.0.19 change CLI advanced the durable package through `approved`,
`implementing`, `verifying`, and `reviewing` to `ready`; no human gates are
declared. It generated and mirrored a clean implementation checkpoint at
`f7401a903d53c8ecb34415ce474a63f110a4ccdb`. These transition-only repository
changes make the five pre-transition receipts stale, so final verifier and
independent-review refresh remains pending for the state-close fingerprint.
No product runtime, payment, deployment, release, or acceptance status has
changed.

The retired Go unit is `go.mod`, `cmd/`, `internal/`, the root Go
`Dockerfile`, and the historical Stage-0-only `migrations/000001_init.*`.
Its five useful safety invariants remain covered by Python characterization
tests and the immutable public import commit
`8734907d489168a8a6567b93bc85920001fefd85`. The A2
`migrations/000002_a2_raw_capture.*`, gateway ledger, SQLite demo, schemas,
vectors, fixtures, and `provenance/import-manifest.json` remain unchanged.

BMad is externalized at the exact `bmad-method@6.10.0` npm identity and SRI in
`tooling/tooling-lock.json`; no BMad factory payload remains copied into the
repository. Adaptive Grok is a portable gitlink at
`tooling/adaptive-grok-build-pro`, pinned to local tag `v2.0.19` and commit
`cb9af4073ba6c3d515145164d771c75ebdfa3224`. Version 2.0.19 was chosen
specifically for its bounded parallel pytest verifier; the older releases run
the suite sequentially and are materially slower. Both project-owned execution
entrypoints fail closed unless the gitlink, HEAD, tag, VERSION, and clean
checkout all match the shared lock validator. Hooks no longer synthesize
allow/empty output after validation failure; thin symlinks preserve hook and
skill discovery without copying framework source.

Ordinary product/conformance tests validate the static lock and gitlink and do
not require an initialized submodule. The separately invoked
`make verify-tooling` suite exercises the initialized runtime, missing,
wrong-lock, wrong-HEAD, and dirty/untracked states, direct execution, hooks,
and dynamic Trivy discovery. A final security re-review then demonstrated that
Git's `assume-unchanged` flag could hide modified verifier bytes from status.
The shared validator rejects all index optimization/state flags globally and
hashes the explicit runtime/instruction trust closure against HEAD, including
engine, Grok scripts/hooks/config/templates/agents/skills, root policy, and the
two change-spec schemas loaded by `spec.py`. It also rejects ignored importable
code in Python execution roots. Historical
packages, distributions, and release evidence remain subject to global
dirty/untracked detection but are not reread for every hook. The bounded
closure contains 179 files / 1,241,709 bytes (limits: 256 / 2,000,000), reducing
warm launcher validation from 0.67 seconds to 0.13–0.16 seconds. Entry points
disable bytecode generation so validation does not create its own ignored
code. The final focused aggregate reports `282 passed`, including 21 strict
tooling cases. The graph CLI still reports only the inherited 26
`IMPLEMENTATION_ORPHAN` findings plus six active declared conflicts; it has no
cleanup-specific inventory, dangling-reference, or retired-Go error.

A local `git clone --no-recurse-submodules` of implementation commit
`058092d2c243d732eb4a44d876a46ae98b64c102` passed the ordinary repository
boundary suite: `8 passed`. This proves fresh ordinary checks do not require an
initialized Adaptive Grok checkout; strict runtime checks remain explicit.

An isolated repository-local `.venv` supplies the exact v2.0.19 runner
versions and declared build backend without changing the global interpreter.
The stale README heading and public-capture metadata expectations are repaired.
A complete-inventory 22-worker measured diagnostic reports
`1134 passed, 85 subtests passed` and 36.16% branch-aware coverage across
10,413 statements. The denominator includes all tracked Python below
`packages/`, `scripts/`, `tools/`, and `tooling/`, including zero-covered owned
modules; it omits only tests, the eight external Grok symlink entrypoints,
generated build paths, and the pinned submodule. The prior 59.18% result is
invalid because it omitted owned scripts, standalone tools, and project-owned
tooling. The truthful initial floor is 36%, the integer below the observed
result; it must not regress and is roadmap debt to raise with targeted tests.
The full PR verifier passed the committed denominator baseline at fingerprint
`aa5925f320da68843a52362e1654549d3a658899`; the recurring
gate dynamically found nine tracked container inputs (seven Dockerfiles and
two Compose files) and passed all at the explicit
`MEDIUM,HIGH,CRITICAL` threshold. A separate LOW audit retains the inherited
`DS-0026` missing-`HEALTHCHECK` finding on each Dockerfile. Four route-selected
independent re-reviews passed with no findings. Their reports are stored. The
durable change package is now `ready`; its transition-only fingerprint still
requires a final verifier and review-receipt refresh before closure.

F3 is locally verified and `ready`; F4 has focused local evidence but awaits
full verification/review. F5–F7 remain `IMPLEMENTED_UNVERIFIED`; all 156
vectors remain `NOT_RUN`,
A13–A14 remain `BLOCKED_EXTERNAL`, payment readiness remains false, and no
testnet payment, deployment, release, or publication is claimed.

## Current state and next action

F1 is **complete-with-blockers** and F2's static contract phase is complete.
F4 is **FOCUSED-VERIFIED / ROUTE-UNVERIFIED** and F5–F7 remain
**IMPLEMENTED_UNVERIFIED**. The accepted
[ADR-0002](docs/adr/0002-liqvera-report-payment-boundary.md) fixes only runtime,
ledger, immutable-artifact, and testnet authority. It does not freeze API
payloads or database schemas and does not authorize payment or release.

The integrated tree now contains:

- pinned official `mezo-org/musd` material plus recorded `mezod` and
  documentation revisions in `packages/mezo-protocol`;
- fixed public Hyperliquid capture, strict evidence inspection, exact report
  assembly, deterministic bounded bundles, offline verification, atomic
  publication, and internal capture/report services;
- the F2 Express API, PostgreSQL ledger/migration, capability and idempotency
  boundaries, immutable artifact adapters, reconciliation/retention workers,
  and official x402 adapter boundary;
- the Mezo Testnet Vite browser application, isolated Compose/images, Caddy,
  environment examples, secret-file conventions, and operations runbooks;
- the result-producing A01–A30 acceptance runner and honest competition
  drafts; and
- exact architecture inventory bindings plus separate `liqvera-python`,
  `liqvera-gateway`, `liqvera-web`, `liqvera-images`, `liqvera-compose`, and
  `liqvera-acceptance` targets. Existing `wheels`/`product` Stage A semantics
  remain the original three Python distributions and two images.

The earlier fixture MVP evidence remains historical and unchanged: its focused
slices reported 6 builder, 6 CLI/bundle, and 3 demo-contract tests passing;
`make mvp` exited 0 for BUY `0.15`, VWAP `1.1`, notional `0.165`,
`snapshot_status=SIMULATED`, and `execution_authority=NONE`. That run produced
report SHA-256 `998ada1362a523f8abfbbddd26bd43f04d08a5d0388c35837fc084c215dcf0f3`
and ZIP SHA-256 `e320026264d42046b39650a7e1376430891ece631dd722a6f160603db449fda1`.
It does not verify the newer canonical F3–F7 code or factory integration.

The evidence-report wheel now carries its schemas, SQLite demo migration,
runtime dependency declaration, and local demo web assets. Gateway builds copy
their schema and migration resources; web builds retain their Vite-owned static
bundle. Gateway and web `package-lock.json` files were generated using
`npm install --package-lock-only --ignore-scripts`; no `node_modules` trees or
build outputs were retained. The current gateway audit observation is 32
advisories (28 moderate, 4 high); the retained web observation is 31 (27
moderate, 4 high). These
counts are unresolved audit input for the deferred verification phase, not a
security acceptance result.

Per the owner's instruction, no graph command, Python test, typecheck, wheel or
web build, Docker build, Compose render/start, acceptance execution, live
capture, facilitator/RPC mutation, testnet payment, Grok receipt, independent
review, deployment, release, or push ran for this code-completion integration.
The next action is the deferred verification and defect-repair phase in
dependency order: factory/resource builds, typechecks, graph, focused/full
tests, browser, Compose/security/fault checks, then separately authorized live
acceptance.

Payment remains deliberately disabled. `PAY_TO_MISSING`, canonical
authorization identity, facilitator compatibility, `FINALITY_RULE_UNVERIFIED`,
funded buyer/signature/receipt evidence, and inherited Trivy findings remain
open. All 156 vectors remain `NOT_RUN`; A13–A14 remain `BLOCKED_EXTERNAL`.
Fixture reports remain `SIMULATED`, non-chargeable, and
`execution_authority=NONE`. Unknown settlement remains `PAYMENT_UNCERTAIN`,
and no second payment may be offered.

The owner approved the repaired [F2 implementation plan](docs/superpowers/plans/2026-09-24-liqvera-f2-contracts.md)
after its independent re-review at `50f16225c23f5fde046b483321f86bb7d6bbf4f1`
and authorized parallel implementation in isolated task worktrees. The six
artifact slices and Task 1/3 review repairs are now integrated in task order;
one integration owner maintains the shared graph, handoff and task records.
The published contracts cover closed schemas/OpenAPI, public reasons,
request/quote/payment/delivery states, exact BUY/SELL vectors, and payment
atomic-unit/idempotency/auth obligations. They add no runtime service.

Task 1's three Important numeric-semantics findings and Task 3's HTTPS
evidence-reference finding passed scoped re-review after repair. Task 2 was
approved. Task 4's artifacts were found coherent; integration supplied its
shared graph/handoff bindings and verified state/vector linkage. Task 5 was
approved with one Minor wording issue;
the 202 description now says "without paid report fields" and retains the
JSON recovery error body. Its existing response-schema assertion covers that
body, so no prose-matching test was added. Task 6 review found one Important
gap in validating the on-disk vector envelope; its test-only repair is now
integrated. Integration also reproduced and repaired a state-schema symbol
pattern that rejected its own `report_sha256` field, adding full document
validation and unsafe-name regressions. Both repairs were included in the
reviewed integration snapshot.

Independent whole-branch review of `644cb702ae879b9d7c8acac1039eb8c5bf37d2aa`
identified cross-contract safety/standards gaps. The consolidated repair adds
evidence GET 202 recovery, expired-quote 410 after scope checks, fixture-source
rejection after more specific reasons, eligible-only quote previews, exact UTC
fractional expiry comparisons, unresolved reencoded-authorization assertions,
mathematically integral JSON number validation, and coherent readiness gates.
The approved plan now reflects those corrections; simulated offline reports
remain valid and no runtime layer or SDK identity rule was introduced.

F2 is **static-contract complete**. The fixture CLI, local browser MVP, and
separate Liqvera factory are integrated; verification, hardening, and defect
cleanup remain without treating implementation as canonical F3 acceptance.
The [final F2 evidence](engineering/changes/2026-09-24-mezo-evidence/evidence/f2-contracts.md)
binds implementation `3729bdc131ca4ac971ab04e735da2e113d68ad71`, tree
`155d7fb44f5953f814f5463c381dde14932a8ab3`, and fingerprint
`2dd9403812ddcb5b3780ae314626316ee2381e27addaf3511b2c20be83d7138a`.
This closure commit changes documentation only; it does not rebind product
verification to its own future hash or manufacture a factory receipt.

Independent session/subagent code, security, edge and acceptance reviews all
APPROVED the final implementation with no remaining findings. Code/security/
edge inspected `74a7b6f..3729bdc`: code ran 65 focused tests (65 deselected),
security 78 (52 deselected), and edge 79 plus six boundary probes; all passed
their diff checks. Acceptance inspected the clean final SHA/tree, recomputed
the fingerprint and verified scope/status/count logs. These results were
consolidated by the coordinating agent; no separate final-review report files
or repository-local receipts exist, and the writer did not self-approve.

All 156 vectors remain `NOT_RUN`. A02–A06/A10–A12/A15–A20 remain `NOT_RUN`;
A13–A14 remain `BLOCKED_EXTERNAL`. Payment readiness remains false, with
PAY_TO_MISSING, FINALITY_RULE_UNVERIFIED, funded buyer/signature/receipt,
SDK/canonical authorization identity and inherited Trivy blockers unchanged.
No runtime acceptance, payment, deployment, release or push is claimed.

Documentation-only closure checks passed: `git diff --check`, `make graph`
(the same seven inherited conflicts), all 226 graph tests in 20.09s, and
balanced-fence/local-link checks across five Markdown files (18 local links).
The implementation fingerprint is unchanged. No new full-suite or Grok run
is claimed for this documentation-only commit.

Edge re-review of `74a7b6f25ea4fe947eca5748481ee247aa1c8f32` found that
readiness still admitted payment_ready=false without a blocker explanation.
The micro-fix adds the missing nonempty-blocker constraint and corrects the
truth table; the focused regression and eight affected combinations failed
before implementation. Healthy future readiness remains representable and
the final scoped re-reviews confirmed this finding is addressed.

Readiness micro-fix verification: targeted RED exited 1 with nine failures,
56 passes and 65 deselected in 1.70s; GREEN exited 0 with 65 passes and 65
deselected in 1.58s. Resource tests passed 130 in 38.40s; all six F2 modules
passed 446 in 193.52s. `make verify` passed 1087 tests and 85 subtests in
326.32s; bare pytest passed the same counts in 327.91s. Graph (the same seven
inherited conflicts), Ruff and diff checks exited 0. Grok `--mode pr
--no-record` exited 1 only for inherited Trivy; all other applicable checks
passed, with coverage explicitly skipped by runner policy. Direct Trivy
again found exactly two inherited LOW DS-0026 Dockerfile findings (exit 1).
The stable pre-verification-record staged tree was
`a6598b786db2ac3b5bf60457c3c69e127df14f1b`; its graph/schema/test index
fingerprint is
`2dd9403812ddcb5b3780ae314626316ee2381e27addaf3511b2c20be83d7138a`.
Only verification prose changed afterward. Runtime remains NOT_RUN and no
new unresolved failure or factory receipt is claimed.

### Historical repair waves — not current receipts

Scoped review of `fd672f89c6bde8d1b1170b2e7a8c631ebed4d793` found three
remaining edge cases. The final follow-up now binds the reencoding scenario
and flag in both directions, preserves exact timestamp fractions beyond
Python's decimal-string integer conversion limit, and closes readiness truth
tables in both directions. Capabilities require an explanation when blocked
and cannot report payment readiness for fixture data; overall readiness must
equal all gates plus no blockers. The targeted regressions went from eight
failures to 77 passes. Code/security/acceptance approved `74a7b6f`; edge
identified the final blocker-list issue fixed and approved at `3729bdc`.
The historical counts below do not replace the final implementation evidence.

Final follow-up verification on 2026-09-24: targeted RED exited 1 with eight
failures, 69 passes and 118 deselected (5.23s); GREEN exited 0 with 77 passes
and 118 deselected (5.19s). Both affected modules passed 195 tests in 189.25s;
all six F2 modules passed 445 in 195.59s. `make verify` passed 1086 tests and
85 subtests in 328.48s; bare pytest passed the same counts in 329.68s. Graph
(the same seven inherited conflicts), Ruff and diff checks exited 0. Grok
`--mode pr --no-record` exited 1 only for Trivy; every other applicable check
passed, with coverage explicitly skipped by existing runner policy. Direct
Trivy exited 1 for exactly the two inherited LOW DS-0026 Dockerfile findings.
The stable pre-verification-record staged tree was
`8fb46171a70190217b60170eb50967da52955f40`; its graph/schema/test index
fingerprint is
`a5654aacb56cce7d1087f6df000ea14dba97c6fa0d17da2920aa366b607cc84a`.
Subsequent changes only record results in continuity prose. No new failure,
factory receipt, runtime acceptance or external mutation is claimed.

Consolidated repair verification on 2026-09-24: the new focused regressions
first failed as expected (23 failed, 16 passed, 219 deselected), then passed
(39 passed, 219 deselected in 5.87s). The final six-module contract suite
passed 368 tests in 191.16s. `make verify` passed 1009 tests and 85 subtests in
322.79s; bare pytest passed the same counts in 323.83s. Graph, changed-Python
Ruff, and staged/unstaged diff checks passed. Grok `--mode pr --no-record`
exited 1 only for Trivy, with every other applicable check passing and coverage
explicitly skipped by runner policy. Direct Trivy again found exactly the two
inherited LOW DS-0026 findings. No new unresolved failure or receipt exists.

The stable pre-verification-record staged tree was
`c4a5bd7764e3b65def7251064b7f1a0739bd9fa5`; the graph/schema/test index
fingerprint (using the command in the existing evidence draft) is
`a6c58a366d7b0354013f615f93a41862d4d34416d07a30212fc9bd514565cf7a`.
Later edits only recorded verification in continuity prose; the final approval
and evidence binding above supersede this historical repair snapshot.
Runtime acceptance stays `NOT_RUN`, with
A13–A14 `BLOCKED_EXTERNAL`; F1 payment/finality and Trivy blockers remain.

Pre-repair integration verification on 2026-09-24 passed `git diff --check`, `make graph`
(the same seven declared conflicts), changed-Python Ruff, all six F2 contract
modules (329 passed in 179.24s), `make verify` (970 passed and 85 subtests in
311.17s), and bare pytest (970 passed and 85 subtests in 311.25s). Grok PR
verification with `--no-record` exited 1 only for Trivy; every other applicable
check passed, zero potential secrets were reported, and coverage was skipped
by runner policy. Direct Trivy inspection confirmed exactly two inherited LOW
DS-0026 findings. No waiver or artificial healthcheck was added. See the
[F2 evidence](engineering/changes/2026-09-24-mezo-evidence/evidence/f2-contracts.md)
for the final artifact fingerprint and historical isolated-task results.

Planning verification: `git diff --check`, authoring-placeholder scan and
`make graph` passed for the repair; graph
verification retains the seven inherited declared conflicts. The new plan has
an exact DOCUMENTATION inventory binding. No product files changed and no
new `make verify`, Grok receipt, runtime acceptance, payment, or release result
is claimed by this planning step.
The repair's 11 JSON snippets parse; all nine primitive patterns reject the
four tested trailing line terminators (LF, CRLF, U+2028 and U+2029). These are
plan-snippet checks, not implemented API or payment acceptance.
Documentation-only review closure also passed `git diff --check` and
`make graph`, with the same seven inherited declared conflicts.

The full delivery sequence is contracts → verifiable report → API/ledger →
testnet settlement → UI/operations → acceptance. The canonical specification
is `docs/planning/LIQVERA_FACTORY_TZ.md`; its legacy filename remains a
compatibility pointer. Preserve inherited `mee-*` names.

No active `.grok-stack/runtime/active-route.json` exists in this public
worktree. `grok_status.py` reports null route/change and no receipt gaps,
which is not factory approval. No factory receipt was created or claimed.
F1 Tasks 1–5 and the final whole-branch transport repair passed independent
review. No Critical or Important finding remains open from F1.

## Verified F1 implementation

Evidence is bound to literal implementation SHA
`37d3e2cf3c64ef2c5d260bccf64e4f107e3f2c25`, captured before the refreshed
closure documentation edits. The rewritten implementation commit passed a
clean detached-worktree verification before 18:25:49Z. See
[F1 verification](engineering/changes/2026-09-24-mezo-evidence/evidence/f1-verification.md)
and [compatibility result](engineering/changes/2026-09-24-mezo-evidence/evidence/f1-compatibility.json).

Fresh commands on 2026-09-24:

| Command | Exit | Result |
| --- | ---: | --- |
| `PATH="$PWD/.venv/bin:$PATH" make verify` | 0 | 641 tests, 85 subtests; Stage A verification passed |
| `PATH="$PWD/.venv/bin:$PATH" python -B scripts/grok_verify.py --mode pr --no-record` | 1 | Only Trivy failed; all other applicable checks passed; coverage explicitly skipped by runner policy |
| `trivy config --exit-code 1 .` | 1 | Exactly two LOW DS-0026 missing-HEALTHCHECK findings |
| `PATH="$PWD/.venv/bin:$PATH" python -B scripts/check-mezo-compatibility.py --lock docs/compatibility/mezo-evidence-v1.json` | 0 | COMPATIBILITY_PASS_PAYMENT_BLOCKED |
| `.venv/bin/python -m pip check` | 0 | No broken requirements |
| `PATH="$PWD/.venv/bin:$PATH" python -B -m pytest tests/compatibility/test_mezo_compatibility.py -q` | 0 | 107 focused tests |

Python 3.12.3, pytest 9.1.1, Hatchling 1.32.4. npm is not used by the probe.
Seven inherited declared graph conflicts remain; the precommit graph check
permits their explicit declaration and does not resolve them.
The exact architecture inventory, focused Ruff checks, and `git diff --check`
passed against the implementation tree. Existing DOCUMENTATION bindings are
unchanged. Final review found no remaining Critical or Important issue.

PR integration merge `94cb8ab2ccba21dfcb8c902814ed3728ba42ab7d`
incorporates the English-documentation baseline from `origin/main`. A fresh
`make verify` passed 641 tests and 85 subtests in 129.26 seconds. The Grok PR
profile reported zero potential secrets and passed every applicable check
except the already named Trivy policy blocker. The synthetic proxy credential
fixture is assembled at runtime; the Basic Auth-shaped literal and its old
introducing commit are absent from the rewritten PR history.

PR #2 (`feat/mezo-evidence-f1-impl` into `main`) is open and mergeable. The
local branch, remote branch, and pull-request head were verified at rewritten
pre-handoff snapshot `237ecbc21901ca7045663b090a537a1ad824a36d` after the
guarded force-push; later commits in this section only record that result.
GitHub reported `MERGEABLE`, and the rerun GitGuardian Security Checks
conclusion was `SUCCESS` (completed 2026-09-24T18:36:51Z). No PR merge was
performed.

## Active blockers and limits

- `BLOCKED_TRIVY_HEALTHCHECK_POLICY`: Trivy rejects both one-shot Stage A
  Dockerfiles for LOW `DS-0026`. Their CLI exit codes and Compose
  `service_completed_successfully` conditions express job completion.
  No long-running readiness contract exists. A meaningful policy decision
  requires separate scope and review; no artificial healthcheck, ignore,
  waiver, or severity filter was added. The full pipeline remains FAIL.
- `PAY_TO_MISSING`: no non-zero operator-owned merchant receiver supplied.
- `FINALITY_RULE_UNVERIFIED`: no approved finality rule or confirmation count.
- A funded buyer, signature, testnet transfer, and receipt evidence are absent.
  Payment readiness is false; A13–A14 remain blocked and other payment rows
  remain not run. Compatibility is public technical evidence only.
- Private salvage source commit
  `7fe6918690f8bc1da5826c67e3619de4126e4f54` remains unavailable. Public
  verification proves target bytes, not private provenance.
- Docker image builds, full clean-machine README/demo acceptance, and fresh
  anonymous publication checks were not run in Task 5. A28/A29 are not passed.
  F7 must rerun acceptance against its final commit.
- Public endpoints and SDK registry availability can change; later external
  unavailability must become `BLOCKED_EXTERNAL`, not an inferred pass.
- The live transport requires POSIX `setitimer`, the main thread, and no
  active caller real-time timer; unsupported contexts fail closed before I/O.
  It is a synchronous CLI probe, not a background transport service.

No payment, signature, private-source verification, factory receipt,
deployment, PR merge, tag, or release occurred during F1 closure. The F1
branch was pushed only to open and repair PR #2. Mainnet, custody, exchange
mutation, merchant private keys, user secrets, and exchange credentials remain
excluded. Shadow-only and the old Stage A verdict remain unchanged. Synthetic
timing and placeholder live identity still require F3.

## Completed F1 work and historical evidence

Initial public baseline `d7a60169985e3a697d7eb5cf29b19b00cb8c0f7a` failed:
four publication paths were absent from graph inventory, salvage required a
private Git object, and wheel tests lacked Hatchling. Its recorded suite had
504 passed, 5 graph failures, 6 wheel errors, and 85 subtests; artifacts passed.
[Initial evidence](engineering/changes/2026-09-24-mezo-evidence/evidence/source-baseline.md)
is preserved separately from the current results.

- Task 1, `37d193b`: exact publication/provenance inventory bindings and graph
  classification; 22 focused tests passed.
- Task 2, `14b2ea4` and `4f8b0d7`: closed-schema salvage manifest verifies
  four pinned target entries, including two entries for one reader file.
  Default result is `items=4 targets=verified source_objects=unavailable`.
  Strict mode requires actual source blob bytes; synthetic Git fixtures test
  missing/corrupt payloads without private objects.
- Task 3, `282616d`: pinned Hatchling 1.32.4 in the development extra,
  ignored local environment, and compatible `eth-account==0.13.7` with
  `hyperliquid-python-sdk==0.24.0`. The initial clean resolver rejected
  eth-account 0.14.0; the corrected clean install and pip check passed.
  The then-current suite passed 534 tests and 85 subtests.
- Task 4, `3c09b44` and `df70f93`: sanitized closed compatibility lock and
  stdlib probe. Review found ambient proxies, npm redirects, and incomplete
  HTTP framing. The approved repair uses four literal registry URLs,
  disabled proxies, redirect refusal, identity encoding, bounded reads, and
  strict Content-Length validation. 89 focused tests passed; final full
  suite at that point had 623 tests and 85 subtests. No npm subprocess/cache remains.
- Final review repair, `37d3e2c`: the public bytecode endpoint legitimately
  uses chunked transfer. A private strict response reader now limits decoded
  data to 2 MiB, framing to 64 KiB, and each framing line to 8 KiB; it rejects
  chunk extensions, all trailers, and malformed/missing CRLF. One 12-second
  total deadline covers connection/TLS, headers, body, and chunk termination,
  restores the prior signal handler, and creates no background worker.
  Real-wire regression RED was 10 failed/89 passed; the final focused suite
  has 107 tests and the full suite has 641 tests plus 85 subtests. The renewed
  live probe passed with byte-identical sanitized evidence and mandatory
  payment blockers. No release or payment gate changed.

The live probe confirms Mezo Testnet 31611, MUSD 18 decimals, x402 v2 exact,
SDK family 2.16.0, and BTC book sides with 20 levels each. It stores no raw
market values, HTTP bodies, credentials, or capabilities and never reads
`PAY_TO`. Its two payment blockers remain mandatory.

## Public snapshot continuity

F0 imported upstream technical snapshot
`4f6583f8590ea091d8a465de0c607e59bfe611a5` into independent public history.
The specification came from
`97f4c7c3b9e1783f4a898412b538a4d6310b902a` (upstream PR 55).
[PROVENANCE.md](PROVENANCE.md) and the import manifest preserve source hashes,
privacy transformations, publication checks, and scan limits. Upstream refs,
secrets, environments, and private history were not imported. Inherited
Actions were disabled at publication; F1 did not change remote settings.

The final F0 secret scan had two reviewed digest false positives and no
unresolved findings. Its publication checks are historical F0 evidence,
not current F1 application or payment verification. Root project metadata is
`0.1.0.dev0`; Stage A packages are `0.1.0`; root product VERSION is now `0.0.2`.
Historical documentation remains context; use this handoff, README,
the change package, runtime tests, and accepted ADRs for current state.
