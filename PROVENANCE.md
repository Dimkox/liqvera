# Liqvera provenance

The current product baseline is the complete source published as v0.0.5, with subsequent publication notes at commit 97484401d50fa3fb28ebd813cc8320e7e51c72f5. Earlier development history remains in Git and is not required to run the application.

The standalone component migration preserves all application boundaries, immutable historical preview bytes, SQL migration checksums and published installer image identities. See [migration](docs/migration.md).

The protocol metadata package retains its exact [source lock](packages/mezo-protocol/source-lock.json), [upstream notice](packages/mezo-protocol/NOTICE.md) and [license](packages/mezo-protocol/LICENSE.upstream). Product licensing does not replace upstream obligations.

Optional external auditing used Getzilla commit 540c12f93e798c2f483455a5086ab0018ac3216e. Its code is not vendored or required by the product. Security evidence records advisory sources and image IDs separately from application release provenance.
