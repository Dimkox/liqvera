# Liqvera security

Liqvera consumes public market data and produces evidence. It has no exchange-account credentials, perpetual-order authority or custody. The browser can prepare Mezo Testnet spot swaps and Trove-protection transactions for explicit signature in the user’s connected wallet; the gateway and report services cannot sign or submit them. Mezo report payments remain a separate, explicitly bounded integration and do not authorize trading.

## Secrets and trust

Never commit or log keys, passwords, bearer capabilities, wallet signatures, private grants or secret-file contents. Use separate database and internal-report credentials. Capture receives neither. The browser uses the user's wallet through supported signing interfaces and never receives private key material. Merchant payments require explicit `LIQVERA_PAYMENT_MODE=merchant`, a fixed recipient, and a fresh wallet authorization for each purchase. The default `grant` mode additionally requires externally issued authority bound to source, database, plan and budget. Neither mode gives the server a wallet key.

Missing/expired wallet authorization (and operator authority in grant mode), malformed inputs, stale source data, ambiguous payment outcomes and artifact digest mismatch fail closed. Unknown settlement is confirm-only. SQL migrations and sealed artifacts are immutable. Source cleanup must never rewrite their identity or reset a consumed grant.

## Untrusted data

HTTP input, market payloads and imported ZIP files are untrusted. Enforce bounded size, exact schemas and decimal syntax, safe paths, strict archive metadata and offline resource resolution. Hashes prove integrity relative to retained bytes; they do not independently attest the exchange. Reports make no execution or profit promise.

## Dependencies and disclosure

Audit exact Python and Node dependency closures and built OS images against current advisory data. Include development tools, transitive packages and every deployment component. Record unsuppressed findings with scanner/database timestamps; an empty direct-pin scan is insufficient. See [the baseline](docs/security/2026-10-12-baseline.md), [completed remediation and exact-image evidence](docs/security/2026-10-12-remediation.md), and [validation](docs/validation.md).

Report vulnerabilities privately to the repository owner with affected commit/image, reproduction and impact; do not publish credentials or an exploit against the live service. Publication, deployment, grant renewal and new payments require explicit scoped authorization. Before sharing a release, review source and history for secrets and verify checksums, license notices and recovery evidence.
