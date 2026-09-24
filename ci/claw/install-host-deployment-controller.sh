#!/usr/bin/env bash
# Owner-controlled D0 only. This script is never invoked from a pall runner.
set -euo pipefail
test "$(id -u)" -eq 0
test "$#" -ge 4 || { echo "required-arguments: source_root controller_sha controller_tree mode" >&2; exit 2; }
source_root=$1
controller_sha=$2
controller_tree=$3
mode=$4
test ! -e /etc/mee-controller/github-token
case "$mode" in
  apply)
    test "$#" -eq 6 || { echo "apply-requires-approval-comment-and-repository-metadata" >&2; exit 2; }
    d0_comment=$5
    repository_metadata=$6
    ;;
  resume|rollback)
    test "$#" -eq 4 || { echo "unexpected-argument-count-for-recovery" >&2; exit 2; }
    ;;
  *)
    echo "unknown-mode: $mode" >&2
    exit 2
    ;;
esac
test "$(git -C "$source_root" rev-parse HEAD)" = "$controller_sha"
test "$(git -C "$source_root" rev-parse 'HEAD^{tree}')" = "$controller_tree"
if test "$mode" = apply; then
  /usr/bin/python3.14 -B - "$source_root" "$controller_sha" "$controller_tree" "$d0_comment" "$repository_metadata" <<'PY'
import datetime as dt
import hashlib
import pathlib
import sys

root, source_sha, source_tree, comment_path, repository_path = sys.argv[1:]
sys.path.insert(0, root)
from scripts.claw_host_deployment_contract import load_closed_bytes, verify_d0_approval

manifest = pathlib.Path(root, "ci/claw/host-deployment-controller-manifest.json")
verify_d0_approval(
    load_closed_bytes(pathlib.Path(comment_path).read_bytes(), max_bytes=1048576),
    load_closed_bytes(pathlib.Path(repository_path).read_bytes(), max_bytes=1048576),
    repository="Dimkox/multi-exchange-engine",
    source_sha=source_sha,
    source_tree=source_tree,
    install_manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),
    now=dt.datetime.now(dt.timezone.utc),
)
PY
fi
exec /usr/bin/python3.14 -B "$source_root/scripts/claw_host_deployment_install.py" \
  --source "$source_root" \
  --manifest "$source_root/ci/claw/host-deployment-controller-manifest.json" \
  --journal /var/lib/mee-claw-host-deploy/install-journal.json \
  --controller-sha "$controller_sha" \
  --controller-tree "$controller_tree" \
  --mode "$mode"
