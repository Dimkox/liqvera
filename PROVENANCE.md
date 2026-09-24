# Liqvera — source provenance

Import date: 2026-09-24. Destination: `Dimkox/liqvera`.

## Source and history boundary

- Upstream: `Dimkox/multi-exchange-engine` (private).
- Technical baseline: `4f6583f8590ea091d8a465de0c607e59bfe611a5`.
- Mezo specification: `97f4c7c3b9e1783f4a898412b538a4d6310b902a`, upstream PR 55.
- This repository starts with its own root commit. No upstream commits, branches, tags, issues, PR discussions, workflow runs, secrets or environments are imported.
- A new isolated local clone was used. Its working tree was clean before export. Existing user checkouts were not touched. No push or visibility change was made to the upstream repository.

The initial commit imports the reviewed technical baseline. Commit `2ca6b524dbc3d4cc288c1e8ffcec2a32e8cf075b` added the original specification byte-for-byte with its declared architecture node. That original remains available in [the import history](https://github.com/Dimkox/liqvera/blob/2ca6b524dbc3d4cc288c1e8ffcec2a32e8cf075b/docs/planning/MEE_MEZO_EVIDENCE_FACTORY_TZ.md).

The owner subsequently adopted **Liqvera** and **Market reports you can verify.**, with attribution to [MEZO ₿](https://mezo.org/) — [The Mezo Buildathon](https://app.akindo.io/wave-hacks/OVOO0gdrVU8379D10). The repository was renamed from `mee-mezo-evidence` to `liqvera`. The current specification is [LIQVERA_FACTORY_TZ.md](docs/planning/LIQVERA_FACTORY_TZ.md); its branding and publication status were updated, and the old path is a compatibility pointer. Source SHAs and the initial import manifest remain unchanged.

## File inventory and transformations

[`provenance/import-manifest.json`](provenance/import-manifest.json) lists all 815 baseline files with their source Git blob, original executable mode, source SHA-256 and imported SHA-256. It describes the **initial import**, before the separate Mezo documentation changes. There is no self-referential hash of the manifest itself.

793 files retain their exact source bytes. Privacy changes affect 22 files:

- Remove the personal author email field from the root and three package `pyproject.toml` files. Keep the author name and original `Proprietary` license metadata.
- Redact three private IPv4 occurrences in documentation.
- Replace 62 named home-directory references in 18 documents with `/home/operator`.

The manifest marks every changed baseline file. Windows archive line-ending conversion was reversed before hashing; it is not counted as a source change. Application source and test bytes are preserved. Generic filesystem defaults in CI scripts and synthetic test fixtures remain part of the technical baseline.

No baseline file is omitted. The source contained no tracked symlinks, submodules, LFS pointers, `.gitmodules`, generated binary archives, database dumps, private-key files or runtime log files in the reviewed inventory. The tracked `.env.example` is an example, not a copied runtime environment.

## Local secret scanning

Gitleaks **8.30.1** was obtained from the official release and its Windows x64 ZIP SHA-256 matched the official checksums file. Scanning and review ran locally; the private scan reports and full upstream clone remain outside this public repository.

Full-history scan:

```text
gitleaks git --log-opts "--all --full-history -m" --redact=100 --no-banner --report-format=json --report-path <private-report> <source>
```

Coverage: 46 local Git refs, 400 reachable commits; Gitleaks reports 394 scanned commits. These are different counters and are reported separately. Merge-parent diffs were included. Raw scanner result: exit 1, six `generic-api-key` detections at two distinct file/line locations. The source-tree scan returned exit 1 with the same two locations.

The detections concern a digest field in `scripts/claw_host_deployment_controller.py` and a file hash in `_bmad/_config/files-manifest.csv`. The controller constructs the field with `hashlib.sha256(...).hexdigest()`. The manifest value was independently matched against the SHA-256 of `.agents/skills/bmad-ux/assets/key-screens.md`; its older recorded directory path differs from the current location. Both are reviewed digest false positives, not suppressed to claim a zero-detection scan.

The final prepared snapshot scan included the import manifest and Mezo documents. It returned exit 1 with exactly the same two digest detections and no additional findings. No matched values, private author details or private scan reports are published here.

Automated scanning is evidence about this import, not a guarantee that all possible sensitive content is detectable.

## Workflows, attribution and verification limits

Inherited workflows are retained as technical reference. GitHub Actions was disabled on the destination **before the first push**. No upstream secrets, environments, runner registrations or deployment credentials were copied.

No tracked LICENSE or NOTICE file was present. Original source attribution and `Proprietary` package metadata are retained. No MIT, Apache or other new license is granted by this import.

Import checks cover file hashes, privacy transformations, new Git ancestry and local scans. Publication checks cover public metadata, anonymous cloning, tree equality, disabled Actions, and the unchanged private upstream main. The full application test suite, Docker builds, live exchange calls and Mezo on-chain payments are outside this repository-creation step and remain F1–F7 work.
