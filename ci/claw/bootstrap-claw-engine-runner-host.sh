#!/usr/bin/env bash
set -euo pipefail
# apply: sudo -n bash ... apply DEBS OCI_ARCHIVE OCI_LAYOUT V2_RECEIPT V2_SIDECAR CONTROLLER_SHA
# recovery: sudo -n bash ... resume|rollback (durable root transaction state only)
test "$(id -u)" -eq 0
mode=${1:?apply-resume-or-rollback-required}; shift
common=(--policy ci/claw/host-bootstrap-policy.json --closure ci/claw/host-package-closure.json --journal /var/lib/claw-engine-runner-bootstrap/journal.json --receipt /var/lib/claw-engine-runner-bootstrap/VERIFIED.json)
case "$mode" in
 apply) test "$#" -eq 6; exec python3 -B scripts/claw_host_bootstrap_transaction.py "${common[@]}" --debs "$1" --oci-archive "$2" --oci-layout "$3" --oci-evidence-receipt "$4" --oci-evidence-sidecar "$5" --controller-sha "$6";;
 resume) test "$#" -eq 0; exec python3 -B scripts/claw_host_bootstrap_transaction.py "${common[@]}" --resume;;
 rollback) test "$#" -eq 0; exec python3 -B scripts/claw_host_bootstrap_transaction.py "${common[@]}" --rollback;;
 *) exit 2;;
esac
