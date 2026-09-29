# Liqvera v0.0.2 — draft release notes

This follow-up candidate adds exact A07 live-public evidence to the retained
v0.0.1 payment and anonymous-publication evidence.

## Evidence added

- A07 passed with canonical `SOURCE_UNAVAILABLE`, no fixture fallback, and no
  artifact emitted.
- A13/A14 retain one confirmed 0.01 test-MUSD settlement with zero buyer native
  gas and no replay settlement.
- A29 retains the credential-disabled anonymous recursive-clone proof from the
  published v0.0.1 release.

The combined sealed per-case projection has 9 PASS, 21 NOT_RUN, zero
BLOCKED_EXTERNAL, and zero FAIL. It remains **INCOMPLETE** and is not a single
runner overall PASS. Component versions remain unchanged at `0.1.0` (root
workspace metadata `0.1.0.dev0`); only the Liqvera product VERSION advances to
`0.0.2`.

No v0.0.2 artifact, tag, push, or GitHub Release has been created. Final notes
must bind the reviewed release commit/tree and exact downloaded artifact hashes.
