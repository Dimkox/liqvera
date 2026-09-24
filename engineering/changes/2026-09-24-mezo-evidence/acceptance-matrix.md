# Acceptance matrix

Status values are `NOT_RUN`, `PASS`, `FAIL`, or `BLOCKED_EXTERNAL`. Evidence is
added only after executing the named scenario against a recorded commit.

| IDs | Area | Planned stage | Current status |
| --- | --- | --- | --- |
| A01 | Baseline before/after | F1/F7 | FAIL — initial public baseline recorded |
| A02–A06 | Exact calculation, validation, identity | F2–F3 | NOT_RUN |
| A07 | Live source outage | F3 | NOT_RUN |
| A08–A09 | Bundle tamper/offline replay | F3 | NOT_RUN |
| A10–A12 | 402, invalid payments, atomic units | F4–F5 | NOT_RUN |
| A13–A14 | Real testnet payment and repeat access | F5/F7 | BLOCKED_EXTERNAL — merchant and funded buyer not supplied |
| A15–A20 | Concurrency, idempotency, crash, expiry | F4–F5 | NOT_RUN |
| A21–A25 | Authorization, artifact loss, RPC/facilitator, redaction | F4–F5 | NOT_RUN |
| A26 | Container/network isolation | F6 | NOT_RUN |
| A27–A29 | Stage A, clean install, public provenance | F1/F7 | NOT_RUN |
| A30 | Wallet/browser recovery | F6–F7 | NOT_RUN |
