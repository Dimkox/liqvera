#!/usr/bin/env bash
# INVOCATION: sudo -n bash ci/claw/install-controller-host-helper.sh REVIEWED_ROOT EXACT_SHA ROOT_VERIFIED_HOST_RECEIPT apply|resume
set -euo pipefail
test "$(id -u)" -eq 0
src=${1:?reviewed-package-root-required}; controller=${2:?exact-controller-sha-required}; host_receipt=${3:?root-verified-host-receipt-required}; mode=${4:-apply}
test ! -e /etc/mee-controller/github-token
cd -- "$src"
test "$(stat -c '%U:%G:%a' "$host_receipt")" = root:root:600
python3 -B scripts/verify_claw_host_bootstrap_receipt.py --receipt "$host_receipt" --policy ci/claw/host-bootstrap-policy.json --closure ci/claw/host-package-closure.json --oci-archive /var/lib/claw-engine-runner-bootstrap/image.oci --journal /var/lib/claw-engine-runner-bootstrap/journal.json --controller-sha "$controller"
test "$(git rev-parse HEAD)" = "$controller"
tmpdir=$(mktemp -d -p /run mee-controller-install.XXXXXX); test "${tmpdir#/run/}" != "$tmpdir"; trap 'rm -rf -- "$tmpdir"' EXIT
python3 - ci/claw/host-helper-manifest.json <<'PY' > "$tmpdir/hashes"
import json,sys
for x in json.load(open(sys.argv[1]))['artifacts']: print(f"{x['sha256']}  {x['source']}")
PY
sha256sum -c "$tmpdir/hashes"
visudo -cf ci/claw/sudoers/mee-controller-ledger
python3 - "$host_receipt" "$controller" ci/claw/host-helper-manifest.json > "$tmpdir/helper-receipt.json" <<'PY'
import hashlib,json,sys
source,controller,manifest=sys.argv[1:]
print(json.dumps({'schema_version':'claw-helper-install-receipt-v1','host_receipt_sha256':hashlib.sha256(open(source,'rb').read()).hexdigest(),'controller_sha':controller,'helper_manifest_sha256':hashlib.sha256(open(manifest,'rb').read()).hexdigest(),'status':'VERIFIED_POST_HOST_RECEIPT'},sort_keys=True,separators=(',',':')))
PY
flag=; test "$mode" = apply || { test "$mode" = resume; flag=--resume; }
exec python3 -B scripts/claw_helper_install_transaction.py --source "$src" --journal /var/lib/mee-controller/helper-install-journal.json --receipt "$tmpdir/helper-receipt.json" ${flag:+"$flag"}
