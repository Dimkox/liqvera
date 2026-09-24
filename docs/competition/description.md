# Liqvera — draft competition description

Liqvera is a prototype for verifiable market reports. A user requests a hypothetical BUY or SELL sweep over the available public Hyperliquid BTC linear perpetual order-book snapshot. The report preserves source evidence, exact calculation inputs and a downloadable bundle that can be checked offline. It is read-only analysis: no exchange order, custody, profit forecast or execution guarantee.

The intended Mezo integration gates access to an immutable report with `0.01` test MUSD on Mezo Testnet and allows paid users to retrieve the same report again without a second charge. This is an implementation objective until a distinct buyer-to-merchant transfer, finality, entitlement and repeat-access evidence pass A13–A14. A simulated local unlock is available for interface exploration and transfers nothing.

The technical foundation was imported from the earlier private Multi-Exchange Engine project into the standalone public Liqvera repository. The competition work extends that baseline with the report, API, testnet payment boundary, browser flow and acceptance tooling. Final submission copy must identify the actual released commit, evidence result, demo/video URLs and verified transaction only when they exist.
