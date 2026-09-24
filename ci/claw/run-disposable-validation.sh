#!/usr/bin/env bash
set -euo pipefail
test "${RUNNER_NAME:-}" = claw-engine-runner || { echo 'SANDBOX_ERROR:RUNNER_AFFINITY' >&2; exit 2; }
test "$(podman info --format '{{.Host.Security.Rootless}}')" = true || { echo 'SANDBOX_ERROR:ROOTLESS_REQUIRED' >&2; exit 2; }
: "${MEE_SOURCE_DIR:?}" "${MEE_OUTPUT_DIR:?}" "${MEE_RESOURCE_NAME:?}" "${MEE_COMMAND_MANIFEST:?}"
source_dir=$(realpath -- "$MEE_SOURCE_DIR"); output_dir=$(realpath -- "$MEE_OUTPUT_DIR"); runner_root=$(realpath -- "${RUNNER_TEMP:?}")
case "$source_dir" in "$runner_root"/*) ;; *) echo 'SANDBOX_ERROR:SOURCE_ROOT_FORBIDDEN' >&2; exit 2;; esac
case "$output_dir" in "$runner_root"/*) ;; *) echo 'SANDBOX_ERROR:OUTPUT_ROOT_FORBIDDEN' >&2; exit 2;; esac
case "$source_dir/" in "$output_dir/"*) echo 'SANDBOX_ERROR:paths overlap' >&2; exit 2;; esac
case "$output_dir/" in "$source_dir/"*) echo 'SANDBOX_ERROR:paths overlap' >&2; exit 2;; esac
case "$MEE_RESOURCE_NAME" in mee-[a-f0-9]*-run-[0-9]*-attempt-[0-9]*-job-[a-z0-9-]*-shard-[a-z0-9-]*) ;; *) echo 'SANDBOX_ERROR:RESOURCE_SCOPE' >&2; exit 2;; esac
podman container exists "$MEE_RESOURCE_NAME" && { echo 'SANDBOX_ERROR:RESOURCE_COLLISION' >&2; exit 2; }
image='docker.io/rhysd/actionlint@sha256:9d36088643581e728c969f35141f88139fec77280b2be23c1f66f8e40e1025e7'
argv=(timeout 900s podman run --pull=never --rm --name="$MEE_RESOURCE_NAME" --label=io.mee.controller=story-1-2 --network=none --cap-drop=ALL --security-opt=no-new-privileges --read-only --pids-limit=256 --memory=2g --cpus=2 --userns=keep-id --tmpfs=/tmp:rw,noexec,nosuid,nodev,size=64m --mount="type=bind,src=$source_dir,dst=/workspace/source,ro=true" --mount="type=bind,src=$output_dir,dst=/workspace/output,rw=true" --entrypoint=/usr/local/bin/actionlint "$image" -format '{{json .}}' /workspace/source/.github/workflows/*.yml)
python3 -B - "$MEE_COMMAND_MANIFEST" "${argv[@]}" <<'PY'
import json,sys
open(sys.argv[1],'w').write(json.dumps(sys.argv[2:],ensure_ascii=False,separators=(',',':'))+'\n')
PY
"${argv[@]}"
test "$(du -sb -- "$output_dir" | cut -f1)" -le 16777216 || { echo 'SANDBOX_ERROR:OUTPUT_LIMIT' >&2; exit 2; }
