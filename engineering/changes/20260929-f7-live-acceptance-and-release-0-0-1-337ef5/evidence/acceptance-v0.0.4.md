# v0.0.4 public deployment and paid E2E evidence

Date: 2026-10-01 UTC

## Signed-v2 final candidate

- Deployed commit: `dcdc7ae6086007d1ccaab8bc563c137c0e099feb`
- Deployed tree: `2459af5d0202a7d8e63ce44548d1f70fa0221ab6`
- Migration 006: applied exactly once after a validated PostgreSQL custom-format
  backup; existing ledger/artifact volumes were preserved
- Signed authority: 23 hours, 20 maximum settlement submissions,
  `200000000000000000` maximum total atomic test MUSD, one per payer
- Public `/readyz`: `ready=true`, `payment_ready=true`
- Headless Chrome: EIP-6963 provider discovery, Mezo chain 31611, historical
  integrity/render/download, repository link, and exact version-neutral
  `https://github.com/Dimkox/liqvera/releases` link passed
- Historical report SHA-256:
  `8f8fd199de1674e5b3f154e50609792bd7bdd711e15cd8a8c15cd703bcaac7dd`
- Historical bundle SHA-256:
  `a6cc771d3fb8428325d32855fef53417f7da25c893db3a99b49802f482adc4fc`

Exactly one encrypted-signer invocation submitted the final v2 payment. It
initially returned `PAYMENT_UNCERTAIN`; read-only reconciliation observed the
existing transaction and moved the quote to `PAID` without another settlement.

- Hyperliquid source time: `2026-10-01T01:37:22.535Z`
- Report ID: `c956cd81-5ec2-439b-909b-4a9d8474cce3`
- Quote ID: `b15c2a5a-6343-4cbf-b26d-f538ae73dbc8`
- Transaction:
  `0x4a04dc72c9f4b9051262b5c14db18369b9140d3012f7b02c3c8d3c6952778455`
- Explorer:
  `https://explorer.test.mezo.org/tx/0x4a04dc72c9f4b9051262b5c14db18369b9140d3012f7b02c3c8d3c6952778455`
- Receipt block: `15882012`
- Confirmations in delivered receipt: `23`
- Report SHA-256:
  `da6515c2435b64ed8054a90d05d7087f7e52a3482aa3f0705d122caf83c70748`
- Evidence ZIP SHA-256:
  `051a3be6c5099eb140caf10d14e880febae0919fc6c8074fafcca2705882d473`

Both paid JSON and ZIP delivery returned HTTP 200. The exact ZIP passed the
repository offline verifier against the quoted report digest. A transient
Cloudflare HTTP/2 connection loss interrupted one post-payment read-only ZIP
transfer; the same paid entitlement later delivered successfully. No payment
resubmission, mainnet call, exchange mutation, push, tag, or release occurred.

## Earlier v0.0.4 candidate evidence

## Candidate and public smoke

- Deployed candidate: `0f3e745d41022c33fbb075c9816b35b1c6a3cabe`
- Candidate tree: `4f363e6b8855e1944e133902e5ada099356ed814`
- Public origin: `https://liqvera.site`
- `/`, `/readyz`, `/demo/latest-live/report.json`, and
  `/demo/latest-live/evidence.zip`: HTTP 200
- Readiness: `ready=true`, `payment_ready=true`
- Historical report SHA-256:
  `8f8fd199de1674e5b3f154e50609792bd7bdd711e15cd8a8c15cd703bcaac7dd`
- Historical bundle SHA-256:
  `a6cc771d3fb8428325d32855fef53417f7da25c893db3a99b49802f482adc4fc`
- Footer used the exact general releases URL
  `https://github.com/Dimkox/liqvera/releases`; no version/tag URL was present.
- EIP-6963 discovery, deterministic multi-provider selection, legacy fallback,
  Mezo switch/add, rejection, and no-provider tests passed; the production web
  build and web image build passed.

The bounded live grant was regenerated without exposing its values and bound
to the exact candidate commit/tree. Its host file remained UID 10003, GID
10001, mode 0400. No credential, capability, wallet key, password, signature,
or grant bytes are retained in this evidence.

## Fresh one-submit Mezo Testnet E2E

- Hyperliquid source time: `2026-10-01T00:11:13.143Z`
- Report ID: `aa96d734-a394-4334-bec0-eca92eb4bd7d`
- Quote ID: `f82c4457-4c4d-45f1-b9f0-e9ff65ca0675`
- Report request ID: `904ace08-bd00-4545-8b37-62193f2a392a`
- Network: `eip155:31611`
- Amount: `10000000000000000` atomic test MUSD (`0.01` MUSD)
- Transaction:
  `0xc5344f48b973d10f5925912e8c5f0b8c69ecdfe4e01ee15209f81771b0cccb6f`
- Explorer:
  `https://explorer.test.mezo.org/tx/0xc5344f48b973d10f5925912e8c5f0b8c69ecdfe4e01ee15209f81771b0cccb6f`
- Receipt block: `15880746`
- Observed confirmations at JSON delivery: `22`
- Report SHA-256:
  `7a4aac444250b63b919d34e2429e39af7202d1029c950c6110103484abec57a7`
- Evidence ZIP SHA-256:
  `7afec508ad2eb5c86551c5fba703463bfe0033bfbc18988d4ccb036b533bce02`

The encrypted signer workflow was invoked exactly once. Its client request
ended without a response inside the local 30-second observation window, so it
was not invoked again. GET-only reconciliation moved the quote from
`PAYMENT_UNCERTAIN` to `PAID`. JSON delivery returned HTTP 200. The immediate
ZIP read returned a transient HTTP 202 while the quote remained PAID; one later
GET returned HTTP 200 without another payment submission. The downloaded ZIP
matched the quoted digest and passed:

```text
PYTHONPATH=packages/evidence-report/src:packages/contracts/src:packages/readonly-analyzer/src \
  .venv/bin/python -m mee_evidence_report.evidence_cli verify \
  <downloaded-evidence.zip> \
  --report-sha256 7a4aac444250b63b919d34e2429e39af7202d1029c950c6110103484abec57a7
exit 0
```

No mainnet call, exchange mutation, real-fund transfer, payment retry, push,
tag, or GitHub Release occurred.
