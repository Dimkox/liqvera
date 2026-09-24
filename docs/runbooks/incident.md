# Incident response

## First response

Record UTC detection time, affected project and image hashes, observed
request/quote/attempt IDs, current health/readiness, and the owner handling
the incident. Protect PostgreSQL, captures, artifacts, and relevant logs from
cleanup. Restrict access to logs because they may contain operational
metadata, even though signatures and capabilities must be redacted by design.

If an incident affects payment integrity, entitlement, chain identity,
finality, a possibly duplicated transfer, or artifact digest, close new
payments and deliveries for affected reports. Preserve in-flight and unknown
attempts; do not relabel them failed or issue replacement charges. Use
[payment recovery](payment-recovery.md) and [artifact recovery](artifact-recovery.md)
for the respective investigations. If public capture fails or is stale,
return a source error and keep the live profile from using fixture data.

For a suspected secret exposure, remove the exposed material from service
access, retain an incident record without copying its value, and have the
owner rotate it using the relevant provider. Rotate a report-service token in
report and gateway together; capture must never receive it. A repository
cleanup alone does not revoke a secret. Do not post a bearer capability,
signature, wallet key, database password, or raw authorization into chat,
tickets, or dashboards.

## Diagnosis and return to service

Correlate structured logs by safe request, quote, report, and attempt IDs.
Check `/healthz` and `/readyz` independently; a live process can be unready.
Inspect host storage, PostgreSQL availability, report service errors,
facilitator/RPC status, canonical chain and token checks, and the exact
artifact digest. Gather only bounded, redacted evidence. Check whether any
attempt entered `SUBMITTING` before stopping or restarting gateway workers.

Record a root cause, affected quote and entitlement scope, recovery action,
independent reviewer, and proof that no second settlement was initiated for
an existing authorization. Reopen new payments only after readiness is true
on the exact image set and the owner has reviewed the recovery result. An
unresolved authorization or missing immutable artifact stays under manual
review. Do not infer release approval from the incident resolution.
