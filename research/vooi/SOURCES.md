# Source log

Snapshot date: **2026-08-10**.

Only primary/official sources are used for claims in `clients.lock.json` and
`architecture.md`. Search-engine results were used only to test for missing
native clients and are recorded as negative, qualified findings.

## Official product surfaces

| URL | Observation |
|---|---|
| https://vooi.io/ | Current official product positioning; Ultra, Perps Markets, API and docs links; unified multi-venue execution claims and legal boundary |
| https://ultra.vooi.io/ | Live Ultra terminal; footer observed as `VOOI Ultra Beta v1.0.1` |
| https://ultra.vooi.io/whats-new/ | Ultra changelog; Arbitrage Desk v1.0.0 dated 2026-07-23 and prior venue/API/MCP releases |
| https://ultra.vooi.io/api-tokens | API token console and MCP setup examples |
| https://pro.vooi.io/ | Live Pro terminal; footer observed as `VOOI Pro v1.12.0` |
| https://app.vooi.io/ | Light shutdown/migration page; footer observed as `VOOI Light v2.5.0` |
| https://t.me/VooiAppBot/vooi | Official Telegram Mini App entry point |
| https://t.me/vooiappbot | Official bot identity page |
| https://perps-api.vooi.io/mcp | Remote MCP endpoint documented by VOOI |
| https://perps-api.vooi.io/docs | On the snapshot date, redirected to Cloudflare Access; not treated as anonymously accessible schema |

## Official documentation

| URL | Observation |
|---|---|
| https://docs.vooi.io/vooi-pro-v1/vooi_pro-releasenotes | Pro v1.12.0 dated 2025-12-18; Telegram Mini App launch and ecosystem history |
| https://docs.vooi.io/vooi-light-v2 | Historical Light documentation |
| https://docs.vooi.io/vooi-ultra-v3 | Ultra product documentation |
| https://docs.vooi.io/ | Product navigation and legal documentation |

Documentation labels such as `VOOI ULTRA v3`, product footer versions such as
`Beta v1.0.1`, and changelog versions such as `v1.0.0` are different versioning
surfaces. The inventory preserves the exact label and source instead of
attempting to collapse them into one synthetic version.

## Official GitHub organization

Organization:

```text
https://github.com/vooi-app
```

The organization is verified for the `vooi.io` domain.

### Client repositories pinned for reproducibility

| Repository | Commit | License/classification |
|---|---|---|
| https://github.com/vooi-app/mcp | `9a5fc1aba5411a0c6e29822628b5ea834889caa7` | MIT; configuration/README only |
| https://github.com/vooi-app/vooi-signals-bot-example | `bb81ee0d5e48246f63b25f39a552622cc23af97d` | MIT; Python trading client example |
| https://github.com/vooi-app/vooi-funding-bot-example | `c3ceab29e80bb26fd6bde128280cb5da5428f3f1` | MIT plus trading disclaimer; Python strategy client |
| https://github.com/vooi-app/vooi-mm-bot-example | `879d15c677e9840dfe4164e3e700bf54c72d5082` | MIT; TypeScript/Node market-making client |

The API inventory is extracted from:

```text
vooi-app/vooi-mm-bot-example
commit 879d15c677e9840dfe4164e3e700bf54c72d5082
src/client/sdk.gen.ts
blob 8c52e42117cf989a37dc1c479290c72746778131
```

This is a generated client snapshot, not a guarantee that every endpoint is
still exposed or unchanged by the live server.

### Official repositories classified as non-clients

- https://github.com/vooi-app/vooi-assets
- https://github.com/vooi-app/DefiLlama-Adapters
- https://github.com/vooi-app/dimension-adapters
- https://github.com/vooi-app/scw-contracts
- https://github.com/vooi-app/.github
- https://github.com/vooi-app/react-iconsax
- https://github.com/vooi-app/assets

They remain in the machine-readable inventory so a later researcher does not
mistake an asset, analytics adapter, contract repository or dependency fork for
a user/client implementation.

## Native-client search boundary

Searches covered:

- official VOOI site and docs;
- official GitHub organization;
- indexed Google Play results;
- indexed Apple App Store results;
- combinations of `VOOI`, `Android`, `APK`, `iOS`, `mobile app`,
  `browser extension`;
- official Telegram identities.

No official native Android/iOS package or browser extension was verified.
Third-party APK catalog claims are deliberately excluded unless they can be
bound to an official package name, signing certificate or first-party store
listing.
