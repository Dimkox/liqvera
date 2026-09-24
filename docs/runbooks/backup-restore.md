# Backup and restore

Back up PostgreSQL and the capture/artifact volumes as one named recovery
set. Preserve the source commit, image hashes, Compose project name, UTC
start/end times, volume names, database migration version, file digests,
operator, and retention class in a manifest outside the repository. Encrypt
the backup at rest and limit access. Caddy certificate state can be backed up
separately; it is not payment evidence.

## Consistent backup

For an authorized maintenance window, stop new quotes, let known attempts
settle or enter explicit uncertain/manual-review state, and stop the gateway,
report, and capture services. Keep PostgreSQL running. The following example
uses the live profile; replace it with fixture only when backing up fixture
state. Run from `deploy/mezo-evidence/` into a private backup directory.

```bash
docker compose --env-file env/live.env -p liqvera-live --profile live -f compose.yaml stop gateway-live report-live evidence-capture-live
docker compose --env-file env/live.env -p liqvera-live --profile live -f compose.yaml exec -T postgres-live pg_dump -U liqvera -d liqvera --format=custom > ledger.dump
docker compose --env-file env/live.env -p liqvera-live --profile live -f compose.yaml run --rm --no-deps --entrypoint tar evidence-capture-live -C /data/captures -cf - . > captures.tar
docker compose --env-file env/live.env -p liqvera-live --profile live -f compose.yaml run --rm --no-deps --entrypoint tar report-live -C /data/artifacts -cf - . > artifacts.tar
```

Check that every command exited zero, archives are nonempty and readable,
record cryptographic digests, and keep the ledger plus both archives together.
If any export fails, mark the recovery set incomplete. Restart only after the
operational gate is checked. A regular backup should be restored in an
isolated drill; an untested archive is not a proven recovery point.

## Isolated restore

Never restore over the running paid stack. Use a new project name and private
host, no edge service, and the matching versioned images/migrations. Review
the archive member names for traversal or symlinks before extraction. Create
fresh empty volumes by starting only PostgreSQL. Restore the database into
that empty database and capture/artifact bytes into the corresponding new
volumes using one-shot profile containers. The following commands are a
template for a controlled restore project:

```bash
docker compose --env-file env/live.env -p liqvera-restore --profile live -f compose.yaml up -d postgres-live
docker compose --env-file env/live.env -p liqvera-restore --profile live -f compose.yaml exec -T postgres-live pg_restore -U liqvera -d liqvera --no-owner < ledger.dump
docker compose --env-file env/live.env -p liqvera-restore --profile live -f compose.yaml run --rm --no-deps --entrypoint tar evidence-capture-live -C /data/captures -xf - < captures.tar
docker compose --env-file env/live.env -p liqvera-restore --profile live -f compose.yaml run --rm --no-deps --entrypoint tar report-live -C /data/artifacts -xf - < artifacts.tar
```

Verify row counts, migration version, artifact digests, sample offline bundle
verification, and entitlement-to-report mapping before starting any gateway.
The restore project must not publish Caddy or enable payment. A production
cutover or a decision to reopen payments needs independent review. Never use
`down --volumes` as a cleanup shortcut while evidence or payment records may
need recovery.
