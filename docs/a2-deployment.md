# A2 deployment contract

Stage A images are `deploy/images/Dockerfile.public-capture` and
`deploy/images/Dockerfile.readonly-analyzer`. They copy exact wheels from
`dist/` only, install with `--no-index`, and do not copy repository source.
They do not install `multi_exchange_engine`, do not run Go, and do not
authorize trading.

The repository-root `Dockerfile` still packages the Go reference engine as
`TEST_ONLY_EXECUTABLE_SPEC`. That image is not a Stage A artifact and is
not part of `make verify`.

The Stage A image uses the digest-pinned base
`python:3.12.13-alpine3.23@sha256:601d3d3797e90e2534782e69c85fafb7971b43f24c7b1b079b7e48dd435e458d`
and runs as `65534:65534`.

The normal CI matrix runs the PostgreSQL integration gate on pinned PostgreSQL
16.11 and 17.7. It then runs the unit, replay, fault, and public-boundary
gates, builds both A2 stages, emits a CycloneDX SBOM with pinned Syft, and
fails on Trivy HIGH/CRITICAL findings. It does not publish an image.

`build-a2-on-claw.yml` is `workflow_dispatch` only on `[self-hosted, claw]`.
It builds `mee-a2:${{ github.sha }}` and the local `mee-a2:candidate` alias;
it does not run the A2 image or push a registry. To keep the scanner versions
pinned without `docker run`, it creates stopped scanner containers, copies out
their Syft/Trivy binaries, and executes those host-side binaries.
`build-a2-on-claw.yml` is `workflow_dispatch` only on `[self-hosted, claw]`;
its verification and promotion jobs do not run outside `refs/heads/main`.
Its PostgreSQL 16.11/17.7 matrix runs only tests and boundary checks. A single
post-matrix job builds `mee-a2:${{ github.sha }}`, runs pinned Syft and Trivy,
uploads both reports, verifies the exact OCI revision/image ID, and exercises
the production registry mount against that exact-SHA image. Only then may
`scripts/promote-a2-candidate.sh` move the local `mee-a2:candidate` alias. The
workflow has one global, non-cancelling concurrency group because the candidate
tag and host staging paths are shared state. It never pushes an image registry.

The promotion script stages these fixed app-stack inputs:

- `/home/operator/app-stack/secrets/a2-reviewed-perpetual-mappings.json`
- `/home/operator/app-stack/secrets/a2-reviewed-perpetual-mappings.json.sha256`
- `/home/operator/app-stack/secrets/mee-a2-candidate-receipt.json`

Each file is installed through a same-directory temporary as `root:root 0644`.
The registry and checksum move first; the canonical JSON receipt moves last as
the commit marker. It binds the source repository/revision, exact source and
candidate image IDs, reviewed-registry path/hash, workflow run ID, and UTC
promotion time. An app-stack deploy must reject absent/malformed receipts,
candidate image-ID mismatches, source-revision mismatches, and registry hash or
ownership/mode mismatches. The runner requires pre-reviewed non-interactive
`sudo` authority for only this staging boundary; `sudo -n` fails closed if that
authority is absent. Staging these inputs does not apply Compose, start A2, or
authorize fixture/public collection.

## Dockerfile validation loop

| Iteration | Command/path | Errors | Warnings | Fixes | Result |
| --- | --- | ---: | ---: | --- | --- |
| 1 | `bash C:/Users/Dmitry/.codex/skills/dockerfile-validator/scripts/dockerfile-validate.sh Dockerfile.a2` | tool bootstrap failed | not produced | No Dockerfile finding was emitted; validator could not create its temporary hadolint environment | partial |
| 2 | fallback static checks for `latest`, secret ENV/ARG, root USER, and HEALTHCHECK | 0 | 0 | Confirmed no `latest`, secret assignment, or root USER; confirmed urllib HEALTHCHECK | partial |
| 3 | controller `checkov -f Dockerfile.a2 --framework dockerfile` | 0 | 0 | 85 passed, 0 failed | pass |
| 4 | binding Alpine base decision | 0 HIGH/CRITICAL on exact digest | 0 | Replaced the retired Bookworm base in all stages; no Trivy waiver | pass |
| 5 | Alpine fallback static checks | 0 | 0 | Confirmed all three exact Alpine FROM lines, no retired Bookworm/latest, no secret ENV/ARG or root USER, Alpine UID/GID commands and urllib healthcheck present | partial |
| 6 | Claw exact-commit build and supply-chain gate | 0 | 1 minor review note | verify/production builds passed; pinned Syft and strict pinned Trivy reports produced | pass |

The primary validator's temporary hadolint bootstrap failed because its
temporary `pip` executable was absent. The authoring worktree did not expose
`docker` or `hadolint`, so local image builds are not claimed. Controller
evidence later ran Checkov with 85 passed and 0 failed. The full workflow
validator reports only the known custom self-hosted `claw` label warning;
actionlint passes when that label is ignored. The controller validated exact
commit `c5b2b0f71b3169f097b017696fafe595634aa48c` in isolated Claw path
`/home/operator/codex-validation/mee-a2-task12-c5b2b0f-20260728`: verify and
production builds exited 0; pinned Syft wrote a 311328-byte CycloneDX report;
pinned Trivy 0.72.0 strict HIGH/CRITICAL exited 0 with 0 findings and a
109710-byte JSON report. The image was 26458760 bytes and inspection confirmed
USER `10001:10001`, the exec-form CMD, urllib healthcheck, and OCI revision
`c5b2b0f`. The A2 container was never started and `/home/operator/app-stack` was
untouched. Reports are retained under ignored
`.superpowers/sdd/task12-claw-final/`. Reviewer Minor remains: FROM-line
parsing is formatting-sensitive; each pinned FROM must stay on one physical
line.

## Verify-stage contract inputs

The verify stage intentionally copies `Dockerfile.a2`, `.dockerignore`,
`requirements-a2.txt`, the reviewed mapping registry, and only the two A2
workflow files after `.dockerignore` re-includes their exact parent paths. The
full test-discovery audit found these are the repository-root inputs not
already covered by the copied package, migrations, tests, or scripts. The
production stage does not copy any of them.

## Reviewed registry runtime input

The production image creates `/app/config` as a root-owned `0755` mount point,
but does not copy the reviewed registry into the image. Every Linux A2 process
requires these exact runtime inputs:

- `A2_REVIEWED_MAPPING_REGISTRY_FILE=/app/config/a2-reviewed-perpetual-mappings.json`
- `A2_REVIEWED_MAPPING_REGISTRY_SHA256=8f17d2fb68518233e3de01af9ce202a5c6c5e1399e75673d72ce7d96fa2472c1`

The runtime reads that exact file before its database claim and fails closed if
it is absent or its SHA-256 differs. The accepted hash is stored in the PLAN
run manifest, binding the frozen universe to the reviewed input. On resume it
compares the current reviewed hash with that persisted manifest before adding a
`RESTART` lifecycle event; a different otherwise-valid registry is rejected.
Task 14 Compose must bind-mount a root-owned host registry file at that target
with `:ro`; it must not copy the registry into the image or make `/app`
writable. A registry review that changes the file requires a matching reviewed
Compose hash update and release-candidate rebuild.

After building a local candidate image, run the non-service production smoke:

```powershell
python -B scripts/smoke-a2-registry-mount.py --image mee-a2:candidate
```

It runs the image only as UID/GID `10001`, with a read-only filesystem and no
collector entrypoint. It proves the present mount is accepted and that missing
or byte-tampered mounts fail; it does not start A2 or contact a venue.

## Local checks

```bash
make verify
```

The old `tests.a2` suite and `multi_exchange_engine` compile path are gone.
Do not run `go test` as Stage A proof. Merge-phase graph stays fail-closed
until Story 1.2 supplies trusted policy time; that is not a local self-attest.

The project intentionally has no registry publication path in either A2
workflow. Deployment, secrets, and any measured run remain out of scope.

## Task 13 release-candidate evidence

The final Task 13 candidate is commit
`2593ec088684c05709bc8c8293e48e400b68a242`. Independent adversarial review
reported zero Critical, Important, or Minor findings after the reviewed
registry, resume provenance, and exact `FROM` regressions were closed.

Local discovery ran 404 tests successfully with 19 expected PostgreSQL-only
skips. Claw then built the exact source archive in
`/home/operator/codex-validation/mee-a2-task13-2593ec0-QE2EDegv`. The production
mount smoke passed present/missing/tampered cases without network access or
collector startup. Pinned PostgreSQL 16.11 and 17.7 each passed 22 integration
tests without skips. Pinned Syft emitted a 311332-byte CycloneDX report, and
pinned Trivy 0.72.0 reported zero HIGH/CRITICAL findings in a 109824-byte JSON
report. The 26459830-byte image has user `10001:10001` and the exact candidate
revision label.

This evidence promotes only the isolated image to the local
`mee-a2:candidate` tag. It does not validate the future Task 14 Compose or n8n
artifacts and does not authorize a public warm-up, measured capture, or trade.
