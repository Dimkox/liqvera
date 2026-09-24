# Requirements — Liqvera Mezo Evidence

## Product acceptance

- [ ] A valid live-public BTC perpetual request produces one immutable report and bundle.
- [ ] Invalid, stale, crossed, insufficient-depth, or identity-unverified input is rejected before payment.
- [ ] An authorized unpaid read returns HTTP 402 without paid fields.
- [ ] Exactly 0.01 test MUSD settles on Mezo Testnet to an operator-owned merchant address.
- [ ] Confirmed settlement creates one entitlement for the exact report digest.
- [ ] Repeat report and bundle access causes no additional settlement.
- [ ] Offline verification detects any significant tampering without network, wallet, or DB access.
- [ ] Existing Stage A behavior and `INSUFFICIENT_EVIDENCE` remain intact.

## Non-functional requirements

- Exact decimal/rational market arithmetic and integer payment units.
- Capability secrets of at least 256 random bits; only hashes persisted.
- Transaction-safe behavior for at least 20 concurrent retries.
- No paid response before durable entitlement.
- Bounded upstream, settlement, and reconciliation attempts.
- Non-root containers, least-privilege networks, explicit egress, CSP/CORS/TLS guidance.
- Redaction of capability and payment authorization material from all logs.

## Completion authority

The full A01–A30 matrix in `acceptance-matrix.md` is authoritative. Mocked
payment tests cannot satisfy the real testnet acceptance requirement.
