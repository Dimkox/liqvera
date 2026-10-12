# Standalone Liqvera on the current product baseline

**Goal:** remove inherited branding and delivery-tool dependencies while preserving the complete v0.0.5 application and producing current security/runtime evidence.

**Baseline:** origin/main 9748440. The older cleanup branch is not the implementation source.

**Constraints:** no live deployment, settlement, grant renewal or exchange mutation. Keep published sealed evidence bytes unchanged. All active package names, CLIs, configuration and new schema identifiers use Liqvera. Record compatibility and migration explicitly. Use current Getzilla externally; never embed its engine in the product.

- [x] Inventory branches and recover the complete baseline; audit exact deployed images and both npm locks with fresh advisory data.
- [ ] Remove obsolete delivery tooling and inherited product research/host automation. Preserve application, contracts, installer, fixtures, payment safeguards and meaningful tests.
- [ ] Migrate active technical identifiers and document the breaking boundary. Retain a bounded verifier for immutable historical artifacts if required.
- [ ] Remediate Python, npm and image dependencies without weakening payment constraints. Compare before/after findings.
- [ ] Rewrite README, architecture, specification, deployment, security and runbooks around actual Liqvera behavior.
- [ ] Run Python, gateway and browser suites, installed report/ZIP verification, disposable database checks and isolated fixture composition. Verify source inventory against main and check historical hashes.
- [ ] Obtain independent read-only review, commit coherent checked steps with handoff updates and report remaining limits.
