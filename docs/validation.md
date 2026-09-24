# Validation record — 2026-07-20

This record covers the Stage 0 shadow-only foundation. It is evidence for build and safety mechanics, not authorization for live trading.

## Result

| Check | Environment | Result |
|---|---|---|
| `gofmt`, `go vet`, unit tests, coverage, binary build | Windows, Go 1.26.5 | Pass |
| `go test -race ./...` | Claw, `golang:1.26.5-bookworm` | Pass |
| GitHub Actions workflow lint | Local `actionlint` validator | Pass |
| Hadolint | Claw, `hadolint/hadolint:v2.14.0-alpine` | Pass, 0 findings |
| Checkov Dockerfile scan | Claw, `bridgecrew/checkov:3.3.8` | Pass, 92 checks and 0 failures |
| Docker `verify` stage | Claw, Docker Engine 29.6.2 | Pass |
| Docker production image | Claw, Docker Engine 29.6.2 | Pass |
| Hardened runtime smoke | Claw, read-only root, all capabilities dropped, no-new-privileges, no network | Healthy |
| PostgreSQL migration up/down | Claw, PostgreSQL 18.3 | Pass: 12 tables up, RLS on 11 tenant tables, 0 tables after down |

The Checkov process could not download optional Prisma Cloud guideline mappings because that external endpoint timed out. Its local Dockerfile scan completed with exit code 0 and all 92 checks passing.

## Dockerfile validation iterations

| Iteration | Finding | Change | Revalidation |
|---|---|---|---|
| 1 | The bundled Windows validator failed before analysis because its Cygwin temporary virtual environment could not locate `pip`. | Used the documented container-based fallback on Claw. | Hadolint and Checkov passed. |
| 2 | Base image tags were versioned but not immutable. | Pinned the Go builder and Alpine runtime to registry digests. | Both scanners, both build stages, and Linux race tests passed. |
| 3 | The Dockerfile frontend tag was mutable. | Pinned `docker/dockerfile:1` to the digest resolved by Docker. | Hadolint, Checkov, and production build passed. |

## Runtime and image facts

- Production image size: 6,469,262 bytes (about 6.17 MiB).
- Runtime identity: numeric non-root user/group `10001:10001`.
- Health check: loopback `GET /healthz` through BusyBox `wget`.
- Runtime smoke used `--read-only`, `--cap-drop=ALL`, `--security-opt=no-new-privileges`, and `--network none`.
- `/v1/meta` reported `mode=shadow`, `live_execution=false`, and `withdrawals=false`.
- No package manager, source tree, Go toolchain, configuration, or credentials are copied into the production stage.

Alpine is retained instead of a shell-free runtime because the image owns an executable Docker health check. The process itself remains a statically linked Go binary with no shell entrypoint.

## Remaining release gates

- Add SBOM generation and vulnerability scanning after the dependency graph exists.
- Add PostgreSQL repository integration and transaction/outbox tests.
- Add exchange-contract conformance tests, recorded WebSocket replay, and fault injection.
- Add signed image provenance before any registry promotion.
- Keep live execution disabled until shadow evidence and an explicit release decision exist.
