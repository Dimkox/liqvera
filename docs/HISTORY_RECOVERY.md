# Split-History Recovery

The audited `main` and `feature/a2-boundary-scan` do not share a merge base.
They must be treated as separate code lines, not normal branches of one
implementation.

## Safe procedure

1. Preserve both remote refs and create immutable backup tags or branches.
2. Inventory each line independently: languages, services, schemas, tests,
   deployment assets, and current operational use.
3. Identify reusable components by behavior and interface, not by filename.
4. Choose one target architecture after the inventory.
5. Port selected components through reviewed commits with tests.
6. Never use `--allow-unrelated-histories`, force-push `main`, or reset one
   line onto the other merely to make Git history look clean.

The cleanup branch deliberately changes only the current Python `main` and
leaves the older line untouched.
