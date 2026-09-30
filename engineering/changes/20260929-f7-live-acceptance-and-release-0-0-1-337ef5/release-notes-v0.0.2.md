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

No v0.0.2 tag, push, or GitHub Release has been created. The immediately prior
artifact evidence binds release commit
`a75ba04b868473c057beb0e7f448eba8edaac6a7`, tree
`d80652ebbc53c379a5ef833f82cbf3fdc135b493`, archive SHA-256
`99ab4e1f0b0a39290f8b036eaf54e8d6ec14116c15bb048061c094fd5d355e3d`
(41,347 bytes), and inner inventory
`0ce551ba64e09bc343361c285b1a93ecb90fb9d4efe886020af878ad2a028d06`.
That artifact is stale after the packaged runtime dependency repair and must be
replaced by the next exact-subject double build before publication.
Two builds were byte-identical and both independently materialized 25 files.
The detached checksum, bootstrap, bootstrap checksum, and verifier hashes are
recorded in the release artifact manifest. All five Liqvera images use
anonymous Docker Hub refs with unchanged multiarch index digests; PostgreSQL is
the pinned official multiarch digest. Assets remain `NOT_PUBLISHED` pending
exact-fingerprint independent reviews.
