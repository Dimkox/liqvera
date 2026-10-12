# Liqvera engineering lessons

## Confirm the product baseline before cleanup

The initial cleanup treated stale F1 as the latest product without comparing main, tags or other worktrees. This produced false whole-product absence/security claims while the full UI/API/payment implementation remained intact on main. Inventory refs and verify ancestry before editing or interpreting missing files; this correction is based on the complete v0.0.5 application.
