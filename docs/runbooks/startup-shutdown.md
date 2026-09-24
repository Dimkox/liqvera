# Startup and shutdown

## Prepare

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
file. Create random `secrets/fixture_postgres_password` and
`secrets/live_postgres_password` with restrictive host permissions. Compose
may resolve both secret declarations while parsing either profile, so keep
both files present; use different values.

The code-completion phase explicitly defers execution. When verification is
authorized, first inspect the resolved configuration without pasting its
secret paths or values into public logs. Start only one profile per project:

```bash
cd deploy/mezo-evidence
docker compose --env-file env/fixture.env -p liqvera-fixture --profile fixture -f compose.yaml up -d --build
```

For a reviewed live-public/testnet deployment, use a separate project:

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

Before a demo, execute the repository's independent acceptance plan and
record code SHA, image hashes, environment, UTC time, commands, exit codes,
and omissions. Do not use a passing fixture run as live or payment evidence.

## Stop or update

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
