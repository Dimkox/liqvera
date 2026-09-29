# Liqvera v0.0.2 acceptance evidence projection

This projection combines distinct sealed case evidence. It is not a new runner
result and must not be described as an overall PASS.

## New A07 result

- Result SHA-256: `b31bc68310c471d35de079d1e0a13232aa39dff4e99b42a9d21b9ce2dbe770de`
- Subject commit: `9f875a1ddc13cbf77242d5aadf6508b69756c022`
- Subject tree: `37324fcf3ae4c9699bee8383f5755d7802634ed6`
- Result overall status: `INCOMPLETE`
- A07: `PASS`
- A07 evidence SHA-256:
  `66ed10ff63a57b66cdd222e733c7098609f82aaff12392aba281d711c490efdb`
- Observation: canonical `SOURCE_UNAVAILABLE` from
  `HttpReportService.build`, one bounded request, no fixture fallback, and no
  artifact emitted.

The result itself still contains three `BLOCKED_EXTERNAL` rows because it is a
single A07 execution. Those rows are closed only in the aggregate by the
separately sealed A13/A14 and post-publication A29 evidence below.

## Previously retained exact external evidence

- A13/A14: `PASS` on transaction
  `0xfb5ab4a116966204dcece95a7ff099f53494074d84584ad072e140ff25453c06`,
  one settlement, 50 confirmations, zero buyer native-gas spend. Source result
  SHA-256:
  `53830fe2249e2754f3c0eeaab8d5292849b2ef55bd5f5c2ae51be7e081457e61`.
- A29: `PASS` after the published v0.0.1 credential-disabled anonymous
  recursive clone matched root VERSION `0.0.1`, kernel VERSION `2.0.19`, and
  submodule `cb9af4073ba6c3d515145164d771c75ebdfa3224`.
- Local A01/A08/A09/A27/A30: `PASS` in the corrected offline result SHA-256
  `4799bce919b3c7d2882ad0f67dee51e7945909664fe81dd95f120afced5d84d6`.

## Truthful aggregate

Across these sealed per-case sources: `PASS=9`, `NOT_RUN=21`,
`BLOCKED_EXTERNAL=0`, `FAIL=0`. Overall acceptance remains **INCOMPLETE**
because 21 canonical cases are still `NOT_RUN`. There is no single runner
result with these aggregate counts or an overall PASS.
