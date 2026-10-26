# Web image curl and Brotli findings remediated — October 26, 2026

Source commit [`8a5af5c`](https://github.com/Dimkox/liqvera/commit/8a5af5c5db0cf2a0e9932822d1b383700b084da8), tree `ee66e01070c759fee4e840c39b99af9b1a456154`. PR #33 and the exact-source [post-merge CI run](https://github.com/Dimkox/liqvera/actions/runs/40319743197) passed.

## Root cause and change

The pinned nginx base image included `curl`; `libcurl` and `brotli-libs` were only its unused dependencies. The Compose healthcheck uses BusyBox `wget`, and the static Nginx runtime does not invoke curl. The final web image now removes `curl` and asserts all three packages are absent. The upstream curl advisory marks versions through 8.22.0 affected by CVE-2026-92392 and 8.23.0 as fixed; this runtime does not need the curl client or library. [curl advisory](https://curl.se/docs/CVE-2026-92392.html). The Brotli decoder flaw affected versions through 1.2.0; [upstream Brotli 1.2.1 release](https://github.com/google/brotli/releases/tag/v1.2.1) contains the fix. This runtime no longer contains that decoder library.

## Rollout and verification

Built `liqvera-web-candidate:8a5af5c` as image `sha256:eb40e136088cf45f680821dd87837dc3e0f2e77cd34f9ca3f0f896ba00bcdb9e`, using the existing `LIQVERA_WALLETCONNECT_PROJECT_ID` from `/home/pall/.local/share/liqvera/deploy/walletconnect.env`; the value is not recorded. Recreated only `web-live` with `--no-deps`; the previous web image remains available as `liqvera-web-candidate:783e8a3` (`sha256:9d9a434a54c7aed89a4c8a8a80372330f028babb2e32c385f392f19b78697e15`).

The new image and live container contain none of `curl`, `libcurl` or `brotli-libs`. Nginx configuration validation and the BusyBox `wget` healthcheck pass. Trivy reports 0 findings, down from 49 on the prior image. Grype reports 3 Medium BusyBox backport matches, down from 52; no Critical or High match remains and no new match appeared. All seven services are healthy. The public site and API returned HTTP 200; the bundle retains `v0.2.0`, WalletConnect, Trove protection and the BTC sale planner.

No database, migration, payment state, grant, sealed artifact, wallet signature or blockchain transaction was changed.
