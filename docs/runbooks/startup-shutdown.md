# Startup and shutdown

## Linux operator install

The v0.0.2 installer is Linux-only. Obtain the bootstrap, verifier, archive,
and detached checksum files from the same reviewed release, but obtain the
published SHA-256 values through the independently reviewed release manifest.
Never use `curl | bash` and never execute archive contents before verification.

```bash
sha256sum --check install-liqvera-0.0.2.sh.sha256
sha256sum --check verify-liqvera-installer.py.sha256
sha256sum --check liqvera-installer-0.0.2.zip.sha256
root="${XDG_DATA_HOME:-$HOME/.local/share}/liqvera"
bash ./install-liqvera-0.0.2.sh \
  ./liqvera-installer-0.0.2.zip <published-archive-sha256> \
  ./verify-liqvera-installer.py ./verified-liqvera "$root" ./liqvera-config.json
"$root/liqvera.sh" --install-root "$root" status --json
```

The verifier and installed lifecycle use only Python 3.9+ and the standard
library. The verifier must run from the download directory without a source
checkout; neither path requires `jsonschema`.

The config is closed: chain 31611, shadow source, payment disabled, loopback
`127.0.0.1` ports, and required references to private database-password and
report-token files. Create both files as single-link regular files owned by the
installing user, non-empty, at most 64 KiB, and mode 0600. A usable config is:

```json
{
  "schema_version": "liqvera-install-config/v1",
  "chain_id": 31611,
  "payment_enabled": false,
  "source_mode": "shadow",
  "ports": {
    "web": {"host": "127.0.0.1", "port": 3000},
    "gateway": {"host": "127.0.0.1", "port": 8080},
    "metrics": {"host": "127.0.0.1", "port": 9090}
  },
  "secret_files": {
    "DATABASE_PASSWORD_FILE": "/home/USER/.config/liqvera/database-password",
    "REPORT_SERVICE_TOKEN_FILE": "/home/USER/.config/liqvera/report-service-token"
  }
}
```

Replace `USER` with the installing account and run `chmod 0600` on both secret
files before installation. The config accepts no secret values, wallets, signatures, payment
grants, mainnet, or exchange authority. `--install-deps` is optional and never
silent: the installer prints the exact package-manager command and requires
its typed digest before invoking `sudo`. User systemd is separately opt-in;
the default and fallback service manager is Docker Compose.

The stable wrapper supports idempotent `start`, `stop`, `status --json`, and
bounded logs:

```bash
"$root/liqvera.sh" --install-root "$root" start
"$root/liqvera.sh" --install-root "$root" stop
"$root/liqvera.sh" --install-root "$root" logs gateway --tail 200 --since 15m
"$root/liqvera.sh" --install-root "$root" uninstall
```

The CLI exposes `update` and `rollback` syntax, but the production Compose
adapter deliberately has no coherent-backup or migration-ledger implementation;
both remain fail-closed with `ROLLBACK_RESTORE_REQUIRED` and are not operational
v0.0.2 procedures. Stage a later verified release only after that adapter and
its recovery proof are independently reviewed.

Default uninstall removes runtime containers but preserves configuration,
logs, backups, artifacts, and all five named volumes. Destructive removal is a
two-step operation: first run `uninstall --purge-data` to obtain the exact
root/release/volume-bound token, then repeat with
`uninstall --purge-data --confirm-purge <token>`. Never guess or reuse a token.

Interrupted download or checksum failure leaves no installed release. An
occupied port, unsafe root, migration mismatch, or health timeout fails closed.
Retry an unchanged verified install after correcting host preflight failures.
After migration commit, rollback is allowed only when the prior image accepts
the exact current ledger; otherwise preserve data and apply a reviewed forward
repair or restore a coherent backup. No down migration exists.

## Advanced source/developer Compose

### Prepare

Use a host with Docker Engine and Compose, sufficient persistent storage, a
trusted clock, and backups. Review the exact tree, image build inputs, and
current acceptance status. Never point this stack at mainnet or supply
exchange trading credentials. The original `compose.stage-a.yml` remains a
separate Stage A workflow.

From `deploy/mezo-evidence/`, copy the chosen `env/*.env.example` to the
matching ignored `env/*.env`. Set `LIQVERA_ENGINE_COMMIT` to the 40-character
lowercase SHA of the exact source build. For live, set a real HTTPS public
origin and matching Caddy DNS name. The operator must establish DNS, TLS
reachability, host firewall rules, outbound destination allowlists, and a
backup location before exposing port 80/443. Do not put secrets in an env
file. Create random `secrets/fixture_postgres_password`,
`secrets/live_postgres_password`, `secrets/fixture_report_service_token`, and
`secrets/live_report_service_token` with owner-only write and group-only read
permissions (host group GID `10001`, mode `0640`). Keep
database passwords and internal report tokens distinct for each profile.
For compatibility with both services, report tokens must be 32–256 characters
from `[A-Za-z0-9_-]` only, with no whitespace.
Compose may resolve all secret declarations while parsing either profile, so
keep all four files present. The report token must be mounted only into report
and gateway; never pass it to capture.

The local F6 phase statically resolves both profiles but explicitly defers
container execution. When runtime verification is separately authorized,
first inspect the resolved configuration without pasting its
secret paths or values into public logs. Start only one profile per project:

```bash
cd deploy/mezo-evidence
docker compose --env-file env/fixture.env -p liqvera-fixture --profile fixture -f compose.yaml up -d --build
```

For a reviewed live-public/testnet deployment, use a separate project:

Before parsing Compose, provision `secrets/live_payment_grant` as UID 10003 mode
`0400` and export the exact non-secret `LIQVERA_SUBJECT_COMMIT`,
`LIQVERA_SUBJECT_TREE`, `LIQVERA_PLAN_SHA256`, `LIQVERA_LIVE_BUYER`, and
`LIQVERA_PAY_TO` bindings. The grant is mounted read-only only at
`gateway-live:/run/secrets/payment_grant`; fixture, capture, report, web, and
edge services never receive it. `gateway-live` shares the live PostgreSQL
network namespace so its credential-free endpoint is the reviewed loopback
identity `postgresql://127.0.0.1:5432/liqvera`.

With local bind-backed Compose secrets, Docker does not apply the service
secret's declared `uid`, `gid`, or `mode`: those are documentation for a real
secret backend. The host `live_payment_grant` must therefore actually be owned
by UID 10003 with mode `0400`. PostgreSQL passwords and report tokens must be
host-readable by shared GID 10001 (mode `0640`). Verify with `stat` before start.

```bash
cd deploy/mezo-evidence
docker compose --env-file env/live.env -p liqvera-live --profile live -f compose.yaml up -d --build
```

Do not activate both profiles in one Compose project. Confirm the expected
containers and health states with `docker compose ... ps`, then request
`/healthz`, `/readyz`, and `/v1/capabilities` through Caddy. The fixture edge
binds only `127.0.0.1:8080`; the live edge publishes host 80/443 and uses
Caddy TLS. `/healthz` proves process liveness only. `/readyz` must keep new
payments closed if storage, chain, facilitator, recipient, authorization
identity, or finality checks are missing. A live source failure must report
`SOURCE_UNAVAILABLE`; it must never silently use fixture data.

Fixture services have no `capture_egress`, `payment_egress`, or `tls_egress`
membership. Live capture, gateway, and edge retain only their corresponding
egress networks. Metrics remain private on the internal `operations` network
at `gateway-metrics:9090/metrics`; Caddy and the host publish no metrics route.

Before a demo, execute the repository's independent acceptance plan and
record code SHA, image hashes, environment, UTC time, commands, exit codes,
and omissions. Do not use a passing fixture run as live or payment evidence.

### Stop or update

Stop new quote creation at the gateway's reviewed operational gate before a
planned update. Allow in-flight confirmed deliveries and reconciliation to
finish; preserve `PAYMENT_UNCERTAIN` records. If no safe drain control exists,
stop the gateway and record the interruption, then reconcile before reopening.
`docker compose ... stop` retains containers and volumes; `docker compose ...
down` removes containers and networks but retains named volumes by default.
Never use `down --volumes` on a stack with payment or evidence state.

For updates, back up the ledger and both evidence volumes, run reviewed
migrations with a forward-recovery plan, then deploy pinned replacement image
hashes. The ledger and immutable artifacts must survive rollback. If a
schema or payment-state migration has run, recover by forward fix rather than
reverting state blindly.
