# Internal evidence report service and offline CLI

Code status: IMPLEMENTED_UNVERIFIED. Execution, tests, hostile-archive checks,
installed-wheel validation, performance measurement, and acceptance are pending.

Run `mee-evidence-report-service` or `python -m mee_evidence_report.service`.
Configuration: `LIQVERA_CAPTURE_ROOT` (read-only raw volume),
`LIQVERA_ARTIFACT_ROOT` (owned output volume), `LIQVERA_ENGINE_COMMIT` (required
40 lowercase hex source commit), `LIQVERA_SOURCE_MODE` (`fixture` by default),
`LIQVERA_CAPTURE_URL` (`http://evidence-capture:8081`),
`LIQVERA_REPORT_HOST` (`0.0.0.0`), and `LIQVERA_REPORT_PORT` (8082).
Network policy must allow the internal capture service and deny external egress.
The service rejects gateway credential/payment/database environment names.

`POST /internal/v1/reports` accepts exactly:

```json
{
  "report_id": "00000000-0000-4000-8000-000000000001",
  "instrument_id": "hyperliquid:BTC:perpetual",
  "side": "BUY",
  "quantity_base": "0.15"
}
```

It generates a capture UUID, requests the fixed capture, reads retained input,
and publishes `<artifact-root>/<report_id>/report.json` and `evidence.zip`.
The success body contains `report_id`, `report_sha256`, `bundle_sha256`,
`report_size_bytes`, `bundle_size_bytes`, `snapshot_at`, `created_at`,
`snapshot_status`, `source_mode`, and `limitations`. No report body or arbitrary
filesystem path is returned. A repeated identical ID/request verifies and returns
the retained artifact; a changed request or conflicting immutable output fails.
The gateway must independently verify file hashes before settlement and delivery.

Errors contain `code` and `retryable`; input failures use 422, internal source or
storage failures 503, and ID/build conflicts 409. At most four requests execute
at once. Body size is 16 KiB. A 15-second build budget includes capture; an expired
response never becomes a ready quote. `GET /healthz` and `/readyz` report process
and storage state. `payment_ready` remains false and blockers are explicit.

Live reports currently reject with `IDENTITY_UNVERIFIED` after validating source
bytes, instrument, ordering, and timing. No supplied mapping or `APPROVED` string
can bypass the absent reviewed trust evidence. Fixture reports are `SIMULATED`
and must be rejected by the gateway before any chargeable quote. The retained
kernel admits only strictly positive displayed sizes; zero-size rows fail closed
without normalization. The legacy fixture demo interfaces remain available.

The canonical build and verifier entrypoints are:

```text
mee-evidence-build --package /raw/CAPTURE_ID --output-root /artifacts \
  --report-id REPORT_UUID --side BUY --quantity 0.15 --engine-commit COMMIT_SHA
mee-evidence-verify /artifacts/REPORT_UUID/evidence.zip --report-sha256 TRUSTED_SHA256
```

The build command requires an existing output root and never overwrites a report.
The verifier needs only the installed Python distributions and the archive, not
a wallet, database, network, or source checkout. It validates packaged F2/F3
schemas with pinned jsonschema/referencing; remote references have no retriever.
These dependencies provide maintained Draft 2020-12 validation instead of a new
schema dialect. Wheel resources contain the original frozen schemas and runtime
dependency list. Factory packaging must additionally retain a full installation
lock; the runtime list identifies direct analytical/schema dependencies only.

Bundles are sorted `ZIP_STORED`, fixed 1980 timestamp, fixed regular-file mode,
no extras/comments/encryption, at most 32 members and 10 MiB total. The verifier
preflights central and local metadata before body reads, checks the complete
manifest, reconstructs a private sealed input, reuses exact `sweep_depth`, and
requires byte-identical report and bundle reproduction. Report digests remain
external to report bodies. Offline success means integrity/reproducibility
relative to supplied evidence; it does not authenticate Hyperliquid or establish
execution, profitability, payment validity, or a trusted source-code signature.

Publication flushes files and directories, checks hashes and bundle reproduction,
and renames staging only when complete. Hidden staging and orphan locks stay
non-ready after crashes. Recovery must match the original digest and must never
charge again. No automatic deletion or overwrite is implemented here; retain
inputs and follow the gateway entitlement/unknown-payment retention policy.
Published directories use mode 0750 and files 0640. The report and gateway
containers need the same artifact-reader group; the gateway mount is read-only.
