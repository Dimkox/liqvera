# F7 acceptance evidence for release preparation

Recorded 2026-09-29 from two sealed, mode-0400 out-of-tree results. Their
private filesystem locations, payment payload, and signatures are deliberately
not copied into the repository.

## Live payment result

- Result SHA-256: `53830fe2249e2754f3c0eeaab8d5292849b2ef55bd5f5c2ae51be7e081457e61`
- Subject commit: `ca9e04c660ff4f9ff0fc45cc37df9793311982d4`
- Subject tree: `48f7039654e5288626bb6c9430b087e00d911567`
- A13: `PASS`
- A14: `PASS`
- Transaction: `0xfb5ab4a116966204dcece95a7ff099f53494074d84584ad072e140ff25453c06`
- Network/asset/amount: `eip155:31611`, pinned MUSD,
  `10000000000000000` atomic units (0.01 MUSD)
- Settlement count: `1`; confirmations observed: `50`
- Buyer native balance before/after: `4999999714058416` /
  `4999999714058416`; buyer native gas spent: `0`
- Durable ledger observation supplied by the operator:
  `PAID`, attempts `1`, grant consumptions `1`, receipts `1`, entitlements `1`
- Later read at block `15855575`: buyer MUSD
  `1799990000000000000000`, buyer native `4999999714058416`;
  merchant MUSD `10000000000000000`, merchant native `0`.

This result's overall status is **FAIL**, not PASS: A08 and A09 failed because
the first full runner selected the system Python rather than the provisioned
repository environment. The payment claims above are restricted to the two
independently sealed case rows and their linked evidence. The runtime-selection
defect was repaired later in commit `76c0b63da3ccdc14529b2b1fdbe02a0b67f6950d`.

## Release-candidate offline result

- Result SHA-256: `4799bce919b3c7d2882ad0f67dee51e7945909664fe81dd95f120afced5d84d6`
- Subject commit: `76c0b63da3ccdc14529b2b1fdbe02a0b67f6950d`
- Subject tree: `b4be60f2b07cf3d55c4363d3465544d1b512c668`
- Overall status: **INCOMPLETE**
- Counts: `PASS=5`, `BLOCKED_EXTERNAL=4`, `NOT_RUN=21`, `FAIL=0`
- Passing cases: A01, A08, A09, A27, A30

The result proves the configured local assertions only. It does not convert
the honest blocked/not-run inventory into release acceptance, does not prove
A29 anonymous-clone publication, and is not bound to the later release-prep
commit that adds `VERSION` and these documents. A final clean result, verifier,
reviews, and artifact build remain required on the exact release commit.
