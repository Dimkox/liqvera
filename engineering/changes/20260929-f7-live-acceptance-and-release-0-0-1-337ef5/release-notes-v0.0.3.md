# Liqvera v0.0.3 — live report and automated testnet demo

v0.0.3 records the Buildathon MVP's live-public Hyperliquid report path and
three newly confirmed automated Mezo Testnet payments. It is an evidence and
source milestone; the checksum-bound Linux installer remains v0.0.2.

## Added evidence

- Live public BTC perpetual snapshot report
  `820df2f8-5bd6-41ad-a94d-98b5078f4d64`, report SHA-256
  `770ba84eeaaec8d1092c9179c2079cebbe891b128b448e722e4367dee87eed9b`,
  bundle SHA-256
  `92fa784431cf92848dbdb8033b111367fb8d624c70906c1cd0c5cc94a1a5d527`.
- Three new payments of 0.01 test MUSD on Mezo Testnet:
  `0x1ca6255bfd83de27feaafd805e27a4dae535e6c5d832be0c875e997dba2b181e`,
  `0x19304292f6a08d1061c4cf3e83d506f67ca0f7b88d67220c45d376c362b335a8`,
  and `0xdab835ad81cd66b56911d6dd4b389ecf2c383e067ba9c52bbf293427eb113c23`.
- Every payment reached at least twelve canonical confirmations and recorded
  zero buyer native-gas spend. A client-side timeout that had settled on-chain
  was recovered confirm-only from its canonical MUSD Transfer log.

No mainnet payment, exchange mutation, custody action, or deployment occurred.
The public evidence asset contains identifiers and hashes only; wallet material,
signatures, grants, passwords, and database credentials are excluded.
