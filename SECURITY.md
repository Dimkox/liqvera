# Liqvera security

Liqvera consumes public market data and produces evidence. It has no authority to submit exchange orders, withdraw funds or use private venue credentials. Testnet report payments are a separate, explicitly bounded integration; they do not authorize trading.

## Secrets and trust

Never commit or log keys, passwords, bearer capabilities, wallet signatures, private grants or secret-file contents. Use separate database and internal-report credentials. Capture receives neither. The browser uses the user's wallet through supported signing interfaces and never receives private key material. Signed authority is externally issued and bound to reviewed source, database, plan and budget.

Missing/expired authority, malformed inputs, stale source data, ambiguous payment outcomes and artifact digest mismatch fail closed. Unknown settlement is confirm-only. SQL migrations and sealed artifacts are immutable. Source cleanup must never rewrite their identity or reset a consumed grant.

## Untrusted data

HTTP input, market payloads and imported ZIP files are untrusted. Enforce bounded size, exact schemas and decimal syntax, safe paths, strict archive metadata and offline resource resolution. Hashes prove integrity relative to retained bytes; they do not independently attest the exchange. Reports make no execution or profit promise.

## Dependencies and disclosure

Audit exact Python and Node dependency closures and built OS images against current advisory data. Include development tools, transitive packages and every deployment component. Record unsuppressed findings with scanner/database timestamps; an empty direct-pin scan is insufficient. See [the current baseline](docs/security/2026-10-12-baseline.md) and [validation](docs/validation.md).

Report vulnerabilities privately to the repository owner with affected commit/image, reproduction and impact; do not publish credentials or an exploit against the live service. Publication, deployment, grant renewal and new payments require explicit scoped authorization. Before sharing a release, review source and history for secrets and verify checksums, license notices and recovery evidence.
