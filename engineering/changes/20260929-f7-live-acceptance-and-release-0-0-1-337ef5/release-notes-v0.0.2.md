# Liqvera v0.0.2 — draft release notes

This follow-up candidate adds exact A07 live-public evidence to the retained
v0.0.1 payment and anonymous-publication evidence.

## Linux installer

v0.0.2 adds a checksum-bound Linux-only installer for Ubuntu 22.04, Ubuntu
24.04, Debian 12, Fedora 40, Fedora 41, and RHEL 9 on amd64/arm64. It requires Bash
5.2, Python 3.9+ (standard library only), Docker Engine 27, Compose v2.30,
4 GiB free disk, and 2 GiB memory. The
archive is deterministic, contains exact migrations 001–005 and six
digest-pinned Docker Hub images, and is independently verified before any
member executes. Two builds from the final subject and both verifier results
must match before publication.

Installation starts only shadow mode on loopback with payment disabled. It
stores no wallet, payment grant, signature, database password, or service token;
only private secret-file references are accepted. Default uninstall preserves
data. Purge needs an exact preview token. Production update and rollback are
fail-closed because the shipped adapter has no coherent backup or database
ledger implementation; operators must reinstall the exact verified release or
apply a separately reviewed forward repair.

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
binds release commit `70141b662ff949c7d06e7801143e29ae14d253be`, tree
`1ede66694689d38e68b61560d67cd7a1dd614838`, archive SHA-256
`04e1cbc7b537be85addb1dd174fea2974f145685e782e589725b639cbc907b82`
(42,226 bytes), and inner inventory
`4c912e694b8ee1f44c5dd0c1b31a33fc3906e16d9c6295ac20688c4e4e0fba23`.
Two builds were byte-identical and both independently materialized 25 files.
The detached checksum, bootstrap, bootstrap checksum, and verifier hashes are
recorded in the release artifact manifest. All five Liqvera images use
anonymous Docker Hub refs with unchanged multiarch index digests; PostgreSQL is
the pinned official multiarch digest. Assets remain `NOT_PUBLISHED` pending
exact-fingerprint independent reviews.
