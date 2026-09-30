# Liqvera v0.0.2 — draft release notes

This follow-up candidate adds exact A07 live-public evidence to the retained
v0.0.1 payment and anonymous-publication evidence.

## Linux installer

v0.0.2 adds a checksum-bound Linux-only installer for Ubuntu 22.04, Ubuntu
24.04, Debian 12, Fedora 40, Fedora 41, and RHEL 9 on amd64/arm64. It requires Bash
5.2, Docker Engine 27, Compose v2.30, 4 GiB free disk, and 2 GiB memory. The
archive is deterministic, contains exact migrations 001–005 and six
digest-pinned Docker Hub images, and is independently verified before any
member executes. Two builds from the final subject and both verifier results
must match before publication.

Installation starts only shadow mode on loopback with payment disabled. It
stores no wallet, payment grant, signature, database password, or service token;
only private secret-file references are accepted. Default uninstall preserves
data. Purge needs an exact preview token. Updates switch `current` only after
health; rollback after migration is limited to an exactly compatible ledger,
otherwise forward repair or coherent backup restore is required.

The checked-in acceptance harness covers the supported matrix with mocked host
facts, checksum and inventory rejection, reinstall, occupied-port failure,
systemd/Compose selection, update recovery, rollback and purge contracts. That
is contract evidence, not a real clean-host Docker run. Isolated clean-host
acceptance remains `NOT_RUN`; the release must not claim it as PASS.

## Evidence added

- A07 passed with canonical `SOURCE_UNAVAILABLE`, no fixture fallback, and no
  artifact emitted.
- A13/A14 retain one confirmed 0.01 test-MUSD settlement with zero buyer native
  gas and no replay settlement.
- A29 retains the credential-disabled anonymous recursive-clone proof from the
  published v0.0.1 release.

The combined sealed per-case projection has 9 PASS, 21 NOT_RUN, zero
BLOCKED_EXTERNAL, and zero FAIL. It remains **INCOMPLETE** and is not a single runner overall PASS. Component versions remain unchanged at `0.1.0` (root
workspace metadata `0.1.0.dev0`); only the Liqvera product VERSION advances to
`0.0.2`.

No v0.0.2 tag, push, or GitHub Release has been created. Final artifact evidence
must bind the reviewed release commit/tree, archive/inventory hashes, detached
checksum, bootstrap/verifier assets, and all immutable image references.
