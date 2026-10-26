# Web footer version deployed — October 26, 2026

Source commit [`783e8a3`](https://github.com/Dimkox/liqvera/commit/783e8a3227967f2361da7d73c2e87dd1a6922635), tree `80c301848f707f1892fd8310d65b5f4e539f6d55` at the deployment source checkpoint. PR #30 and the exact-source [post-merge CI run](https://github.com/Dimkox/liqvera/actions/runs/40314474948) passed.

## Rollout

Built the pinned web Dockerfile as `liqvera-web-candidate:783e8a3`, image `sha256:9d9a434a54c7aed89a4c8a8a80372330f028babb2e32c385f392f19b78697e15`. The build used the existing `LIQVERA_WALLETCONNECT_PROJECT_ID` configuration from `/home/pall/.local/share/liqvera/deploy/walletconnect.env`; its value is not recorded. The image contains `Liqvera v0.2.0` and the configured WalletConnect application ID.

Recreated only `web-live` using a Compose override piped on stdin, `--no-deps`, `--pull never` and `--force-recreate`. The Compose manifest was not changed. The previous web image remains available as `liqvera-web-candidate:a6154ec` (`sha256:82fb7a75dc3631838054d84e2579dae690c5835aa120c4117863fe2d23f6779e`). All seven services reported healthy after rollout; no database, migrations, payment state, grants, sealed artifacts, wallet signatures or blockchain transactions were touched.

## Published checks

- `https://liqvera.site/` returned HTTP 200 and now serves `assets/index-C6L3_8ec.js`, containing footer version `v0.2.0`.
- The published bundle retains WalletConnect, Trove protection and the BTC sale planner.
- `https://liqvera.site/v1/capabilities` returned HTTP 200.

Fresh October 26 vulnerability databases reported the same findings for the new image and the immediately preceding web image: Trivy found 49 package findings (3 High, 2 Medium and 44 Low); Grype returned 52 matches (1 Critical, 2 High, 3 Medium and 46 Unknown). The findings and package versions were identical between the images, so this source-only release introduced no additional scanner finding. The existing findings remain present in the deployed image.
