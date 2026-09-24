#!/usr/bin/env bash
set -euo pipefail
test "$(id -u)" -eq 0
systemctl disable --now mee-controller-reconcile.timer 2>/dev/null || true
rm -f /etc/systemd/system/mee-controller-reconcile.timer /etc/systemd/system/mee-controller-reconcile.service /etc/sudoers.d/mee-controller-ledger /usr/local/libexec/mee-controller-reconcile /usr/local/libexec/mee-controller-ledger-write
# /var/lib/mee-controller is deliberately retained as forensic single-use state.
