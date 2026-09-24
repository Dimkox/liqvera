# Validation and deployment host

## Claw access paths

The Claw host is available through both the local network and Tailscale:

| Path | Address |
|---|---|
| LAN | `[redacted private IP]` |
| Tailscale IPv4 | `100.119.249.65` |
| Tailscale MagicDNS | `claw.taild9f611.ts.net` |

- Hostname: `claw`.
- SSH user: `pall`.
- Prefer the Tailscale hostname outside the LAN.
- Credentials are never stored in this repository, Docker build arguments, image layers, CI logs, or Basic Memory.

During the 2026-07-20 validation run, the direct Tailscale IPv4 connection timed out from the validating workstation while the LAN route succeeded. The Tailscale address and MagicDNS name remain documented access paths; verify current Tailscale peer/routing state before relying on that route for deployment.

Verified on 2026-07-20:

- Docker Engine `29.6.2`.
- Docker Compose `5.3.1`.
- Architecture `x86_64`.
- `golang:1.26.5-alpine3.23` and `alpine:3.23.3` manifests are available from Claw.

## Isolation rule

- `/home/operator/app-stack` is the existing live application area and is outside this project's validation scope.
- Temporary validation uses a dedicated path below `/home/operator/codex-validation/`.
- This repository currently defines CI only. It contains no automatic deployment and no live-execution arming path.

## Intended validation command

```bash
docker build --target verify -t multi-exchange-engine:verify .
docker build -t multi-exchange-engine:dev .
docker run --rm --read-only --cap-drop=ALL --security-opt=no-new-privileges \
  -p 8080:8080 multi-exchange-engine:dev
```
