# Python runtime security backports

The images use stable CPython 3.14.8, with production-file hunks extracted unchanged from these upstream patches:

- [b234a2b67539f787e191d2ef19a7cbdce32874e7](https://github.com/python/cpython/commit/b234a2b67539f787e191d2ef19a7cbdce32874e7): reject control characters in POP3 commands, CVE-2025-15367.
- [58ed0259cae509a19138795df302fe60b544dc74](https://github.com/python/cpython/commit/58ed0259cae509a19138795df302fe60b544dc74): the upstream 3.14 backport fixing the TemporaryDirectory cleanup race, CVE-2026-12345. Both shutil and tempfile changes are required.

These changes are covered by the CPython license already distributed with the base image. No application-specific changes are made to the patches. The patch script validates the interpreter version and patch hashes, rejects fuzzy/previously applied patches and records hashes of all three patched modules inside the image. Review/remove these backports when a stable interpreter release includes them; do not carry them blindly across interpreter upgrades.

Version-only vulnerability scans can still report these two CVEs. Retain their raw results and use the upstream patch identities, module hashes and non-root regression results as remediation evidence. This does not waive other Python findings.
