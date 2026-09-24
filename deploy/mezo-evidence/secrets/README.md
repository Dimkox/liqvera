# Local Compose secret files

Create `fixture_postgres_password` or `live_postgres_password` here before
starting the corresponding stack. Use a unique, random value for each Compose
project. This directory ignores every file other
than this README. Do not put wallet keys, seed phrases, payment signatures,
or exchange credentials in this directory: the application never needs them.

Compose mounts the selected password into PostgreSQL and the gateway at
`/run/secrets/postgres_password`. Limit host access to the operator account
(for example, mode `0600`); keep secure backups outside the repository. The
gateway derives `DATABASE_URL` in memory and never prints it. A production
secret manager may replace the file mount while preserving the same path.
