# Liqvera component namespace migration

This is an unpublished breaking component migration from 0.1.0 to 0.2.0 on top of the full v0.0.5 source baseline. Python distributions/imports/CLIs, public capture configuration prefixes, generated schema identifiers and gateway identity now use Liqvera. Rebuild the browser, gateway and all Python services together; mixed old/new schema producers are unsupported.

Use a new virtual environment and fresh output directories. Do not overlay old wheelhouses, reuse an old editable install, relabel sealed JSON, rewrite signed authorities or point an unreviewed candidate at a live ledger. The current source requires a new reviewed grant bound to its own exact commit/tree before payments could be enabled; old grants cannot authorize it.

SQL migration files and their checksums are unchanged. Existing payment/entitlement records and sealed artifacts belong to their historical version. Keep the matching published application/verifier and coherent backups to read them. Migrate live state only through a separately reviewed, bounded forward migration that preserves unknown outcomes, digest bindings and consumed authority. No such live-state migration or deployment is performed by this cleanup.

The wallet-free historical preview is an explicit compatibility boundary: its published JSON and ZIP, fixed report ID and SHA-256 values remain unchanged. The browser checks those exact bytes before rendering. Current build/verifier commands produce and accept the new namespace; historical bundles use the matching v0.0.5 verifier. Published installer image locks and third-party license/source notices also retain original bytes.

Rollback for this source-only change is to rebuild the previous reviewed commit in a separate environment. Do not run down migrations, recreate live volumes or restore a database independently of its sealed artifacts.

The v0.0.2 operator retains its original Compose contract and readiness-schema check for the immutable images it installs. Use source Compose for the unpublished 0.2.0 components; rebuilding the old operator with new images is not a supported upgrade.

The two retired raw-capture SQL migrations remain byte-identical recovery references under `migrations/`; current services do not apply them.
