# Upstream notice

`vendor/MUSD.matsnet.json` is an unmodified copy of the official Matsnet MUSD
deployment artifact from [`mezo-org/musd`](https://github.com/mezo-org/musd),
pinned at commit `aa25fd6defbe6c1385940e183ea7a0a3df4533d8`. The upstream repository is
licensed under GPL-3.0; the exact upstream license is retained as
`LICENSE.upstream`.

The artifact contains the full deployed-contract ABI and compiler metadata.
Liqvera's authored `src/index.ts` export deliberately presents only read-only
token inspection, the `Transfer` event, and EIP-2612 metadata. It does not
expose minting, burning, borrowing, liquidation, ownership, or administrative
operations.

`source-lock.json` records the pinned MUSD, Mezod, and Mezo documentation
revisions, upstream paths, Git blob identifiers for copied files, and SHA-256
digests. No private source, key, credential, or live-chain response is included.
