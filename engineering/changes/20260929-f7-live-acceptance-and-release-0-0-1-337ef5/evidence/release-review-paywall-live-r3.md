# Release re-review R3 — grant-less live rollback

Review subject: `e3df6833e8916d01f55028e63d4db1632a805a75..ea3098732b369f92d4a8ec7503cfda6153a582ee`

Scope: only the R2 rollback blocker.

Decision: **GO — prior rollback blocker closed**

## Result

The checked-in `deploy/mezo-evidence/compose.live-disabled.yaml` atomically replaces the `gateway-live` secret list and environment. Its resolved configuration:

- removes `payment_grant_live` from the gateway and top-level secret inventory;
- removes `LIQVERA_LIVE_GRANT_FILE`;
- removes `LIQVERA_SUBJECT_COMMIT`, `LIQVERA_SUBJECT_TREE`, `LIQVERA_PLAN_SHA256`, and `LIQVERA_LIVE_BUYER` together;
- preserves the live-public source, payee, report service, artifact store, metrics, and loopback database endpoint;
- preserves `network_mode: service:gateway-net-live`, so the gateway can start against the reviewed credential-free `127.0.0.1:5432/liqvera` endpoint without payment authority.

With no grant-file setting, `loadConfig` produces a null live context and ordinary gateway composition takes the existing null-grant path. The running service therefore remains fail-closed with `EXTERNAL_GRANT_REQUIRED` rather than failing while opening a missing or expired grant.

## Operator command and documentation

Both `docs/runbooks/testnet-demo.md` and the change-package `rollback.md` provide the exact checked-in override command:

```bash
docker compose --env-file env/live.env -p liqvera-live --profile live \
  -f compose.yaml -f compose.live-disabled.yaml up -d --build --force-recreate gateway-live
```

The instructions correctly prohibit moving/deleting the enabled grant file, preserve PostgreSQL and artifact volumes, and forbid resubmitting UNKNOWN attempts. `env/live.env` remains an intentionally ignored operator input established by the surrounding startup runbook; it was not present in this review worktree and no replacement product file was created.

## Verification

- `.venv/bin/python -m pytest tests/operations/test_f6_static.py -q` — **5 passed**.
- The documented Compose file order and profile were resolved with an empty external env file plus explicit non-secret bindings — **PASS (`disabled-compose-ok`)**.
- The resolved JSON was independently asserted to contain no grant secret, no grant-file variable, and no grant-context variables, while retaining `service:gateway-net-live`.
- No container startup, external network call, secret read, payment, or deployment was performed.

## Decision boundary

The R2 operational rollback blocker is closed. This GO is limited to the reviewed grant-less live rollback path; it does not create evidence of a hosted deployment, live Hyperliquid capture, Mezo Testnet settlement, or overall F7 completion. Those claims remain governed by their separate fingerprint-bound verification, review, human-gate, and external-evidence requirements.
