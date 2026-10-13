# Liqvera repository instructions

Liqvera — Market reports you can verify. Repository: Dimkox/liqvera.
Canonical specification: docs/specification.md. Documentation, UI and commits use English.

1. Before work, read README.md, docs/architecture.md, handoff.md, Git status and recent history. Confirm branch ancestry against main and published tags; inventory worktrees before cleanup.
2. Preserve the complete product: web, gateway, public capture, report/verifier and payment guards. Missing files on an old branch do not prove missing implementation.
3. Commit each coherent significant step after its checks pass; update handoff.md in the same commit.
4. Never read or commit secrets, wallet keys, passwords, tokens or private grants. Record variable names and locations only.
5. Market data is public and read-only. Tests never authorize live exchange mutation, payments, grant renewal, deployment or publication.
6. Technical identifiers use Liqvera. The approved namespace migration is breaking; document it and preserve immutable historical evidence and SQL migrations.
7. No external delivery framework is required to build or verify the product. Optional external tools do not own repository policy or runtime behavior.
8. Run relevant Python, Node and artifact tests. Inspect actual results before claiming success. Do not equate mocks, static checks or partial acceptance with live acceptance.
9. Substantial implementation changes require an independent read-only review of the actual diff. One implementation owner edits application code.
10. Keep source changes separate from deployments. Preserve existing databases, unknown payment states, sealed bundles and published release assets.

11. Keep one Liqvera web/API product. Do not reintroduce the retired Linux installer, separate prototype website, exchange credential templates or external delivery framework.
