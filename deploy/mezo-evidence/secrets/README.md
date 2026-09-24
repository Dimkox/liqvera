# Local Compose secret files

Create `fixture_postgres_password`, `live_postgres_password`,
`fixture_report_service_token`, and `live_report_service_token` here before
starting either stack. Use distinct, random values for each profile and each
purpose. This directory ignores every file other than this README. Do not put
wallet keys, seed phrases, payment signatures, or exchange credentials here:
the application never needs them.

Compose mounts the selected password into PostgreSQL and the gateway at
`/run/secrets/postgres_password`. For local Compose file-backed secrets, own
each host file by the operator, set group GID `10001`, and set mode `0640`;
the gateway has that primary group and PostgreSQL has it as a supplemental
group. Verify those host permissions before startup. Keep secure backups
outside the repository. The gateway derives `DATABASE_URL` in memory and never
prints it. A production secret manager may replace the file mount while
preserving the same path.

Compose mounts the matching report token only into the report service and
gateway at `/run/secrets/report_service_token`. Capture, PostgreSQL, web,
Caddy, and the migration job never receive this token. The report reads it
through `LIQVERA_INTERNAL_TOKEN_FILE`; the gateway reads it through
`REPORT_SERVICE_TOKEN_FILE`. Generate at least 32 random bytes per token;
use host group GID `10001` and mode `0640` so the distinct non-root report and
gateway UIDs can read their mounts. Never copy a token into an env file or log,
and rotate the token with a coordinated restart of both services. Do not use
the token as a public API bearer capability.
