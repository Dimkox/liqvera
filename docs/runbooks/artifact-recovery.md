# Artifact recovery

The report JSON, evidence ZIP, and sealed capture inputs are immutable once
published. PostgreSQL records entitlement and artifact identity; artifact
bytes remain on the dedicated volumes. A healthy ledger with a missing or
corrupt artifact must not serve an alternate file, rebuild under the same
digest, or charge again.

1. Disable affected delivery and new quotes; preserve the capture and
   artifact volumes read-only for investigation. Record report ID, expected
   SHA-256, volume identity, file sizes, UTC times, and relevant database
   rows. Do not expose internal paths through the public API.
2. Copy the suspect files to a quarantined workspace. Run the offline bundle
   verifier against the copy and compare the report and bundle digests to
   the ledger. The verifier's integrity result does not prove that the
   exchange signed the original data.
3. Recover only the exact bytes from a verified backup, under the same
   report ID and digest. Stage them in a new temporary path, verify hash and
   archive safety, then publish atomically under the original identity.
   If no matching bytes exist, keep delivery unavailable and open an incident.
4. Recheck the entitlement-bound GET and evidence download using the
   original capability. Confirm that the response is the same artifact and
   no new payment is requested. Record the recovery operation and reviewer.

Keep raw captures and paid artifacts through the documented retention period
and any incident hold. Never prune a file referenced by an unresolved payment
attempt or paid entitlement. Recovery is a forward repair; it must not rewrite
ledger history or silently recalculate a historical market snapshot.
