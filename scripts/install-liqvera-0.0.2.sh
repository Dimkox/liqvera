#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 6 ]]; then
  echo "usage: $0 ARCHIVE OUTER_SHA256 VERIFIER VERIFIED_DIR INSTALL_DIR CONFIG" >&2
  exit 2
fi
archive=$1
outer_sha256=$2
verifier=$3
verified_dir=$4
install_dir=$5
config=$6
receipt=$(/usr/bin/python3 -I -B "$verifier" "$archive" "$outer_sha256" "$verified_dir")
inventory_sha256=$(/usr/bin/python3 -I -B -c 'import json,sys; print(json.load(sys.stdin)["inventory_sha256"])' <<<"$receipt")
receipt_root=$(mktemp -d "${TMPDIR:-/tmp}/liqvera-verification-receipt.XXXXXXXX")
chmod 0700 "$receipt_root"
receipt_path="$receipt_root/receipt.json"
(umask 077; printf '%s\n' "$receipt" >"$receipt_path")
status=0
"$verified_dir/install.sh" --verified-release "$verified_dir" \
  --verified-receipt "$receipt_path" \
  --sha256 "$outer_sha256" --inventory-sha256 "$inventory_sha256" \
  --install-dir "$install_dir" --config "$config" || status=$?
rm -f -- "$receipt_path"
rmdir -- "$receipt_root"
exit "$status"
