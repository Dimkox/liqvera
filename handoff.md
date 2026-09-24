# Liqvera — handoff

Date: 2026-09-24. Repository: `Dimkox/liqvera`.

## Brand and buildathon

**Market reports you can verify.**

Built for [MEZO ₿](https://mezo.org/) — [The Mezo Buildathon](https://app.akindo.io/wave-hacks/OVOO0gdrVU8379D10).

The owner approved the Liqvera name and tagline. The canonical repository is [Dimkox/liqvera](https://github.com/Dimkox/liqvera). The current specification is `docs/planning/LIQVERA_FACTORY_TZ.md`; the previous path remains a compatibility pointer for factory links. Technical `mee-*` package names and data formats are retained.

## What is ready

The `main` branch contains an independent technical snapshot of upstream `4f6583f8590ea091d8a465de0c607e59bfe611a5`, with a fresh Git history. A separate documentation commit imported the specification from `97f4c7c3b9e1783f4a898412b538a4d6310b902a` (upstream PR 55) and updated the entry points. Upstream secrets, environments, old refs, and history were not imported.

The import inventory and checksums are in [PROVENANCE.md](PROVENANCE.md) and the [manifest](provenance/import-manifest.json). Author contact details and private infrastructure addresses were removed from the publication. Inherited workflows remain part of the technical snapshot, but GitHub Actions execution is disabled in the new repository.

## Project language

The owner requires English as the default throughout the project. The README, specification, planning documents, research, and historical documentation are now in English without changes to technical requirements or historical status. The specification also requires English operator documentation. `AGENTS.md` records the English default for future documentation and product content. Language-recognition patterns in inherited tooling and five original source filenames cited in the Solana archive remain exact references; the initial import manifest remains immutable.

Translation checks covered all 340 tracked Markdown files. No Russian prose or newly broken relative links/heading references remain. The specification retains all 21 numbered sections, 30 acceptance checks, phases F0–F7, inline literals, numeric values, and URLs. Code fences and technical identifiers were preserved; Russian comments and diagram labels were translated. Only Markdown files changed, and the README graph retains all ten required edges. These are documentation checks, not application or payment test results.

## Next action

Complete F1 from the [specification](docs/planning/LIQVERA_FACTORY_TZ.md): verify baseline tests, instrument metadata, Mezo Testnet, and payment configuration. Then implement F2–F7: contracts → verifiable report → API/storage → test MUSD payment → interface → acceptance.

Preserve the existing Stage A verdict. Placeholder metadata provenance, synthetic capture timing, and the missing payment flow remain implementation tasks. Mainnet, trading, and user capital are not authorized.

## Verification boundary

File provenance, fresh history, and local scans were checked. The final Gitleaks scan returned exactly two hash detections: one was confirmed by its computation in code, and the other by matching the SHA-256 of the corresponding file. No unreviewed findings remained. Publication was verified through public metadata, an anonymous clone, and tree equality. These checks cover the import; the full `make verify`, Docker builds, and on-chain payment were not run.

Historical upstream documents are retained as context. If they conflict with the new repository status, use this handoff, README, and PROVENANCE. No local `.grok-stack/runtime/active-route.json` is present; no factory receipts were created or claimed.
