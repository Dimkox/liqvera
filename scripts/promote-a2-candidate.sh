#!/usr/bin/env bash
set -euo pipefail

readonly expected_registry_sha256="8f17d2fb68518233e3de01af9ce202a5c6c5e1399e75673d72ce7d96fa2472c1"
readonly source_sha="${GITHUB_SHA:?GITHUB_SHA is required}"
readonly source_image="${SOURCE_IMAGE:?SOURCE_IMAGE is required}"
readonly workflow_run_id="${GITHUB_RUN_ID:?GITHUB_RUN_ID is required}"
readonly source_repository="${GITHUB_REPOSITORY:?GITHUB_REPOSITORY is required}"
readonly workspace="${GITHUB_WORKSPACE:?GITHUB_WORKSPACE is required}"
readonly runner_temp="${RUNNER_TEMP:?RUNNER_TEMP is required}"
readonly registry_source="${workspace}/config/a2-reviewed-perpetual-mappings.json"
readonly target_directory="/home/pall/app-stack/secrets"
readonly registry_target="${target_directory}/a2-reviewed-perpetual-mappings.json"
readonly hash_target="${target_directory}/a2-reviewed-perpetual-mappings.json.sha256"
readonly receipt_target="${target_directory}/mee-a2-candidate-receipt.json"

fail() {
  printf 'A2 candidate promotion failed: %s\n' "$1" >&2
  exit 1
}

[[ "${source_sha}" =~ ^[0-9a-f]{40}$ ]] || fail "invalid source revision"
[[ "${source_image}" == "mee-a2:${source_sha}" ]] || fail "unexpected source image"
[[ "${workflow_run_id}" =~ ^[0-9]+$ ]] || fail "invalid workflow run id"
[[ "${source_repository}" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]] || \
  fail "invalid source repository"
[[ -f "${registry_source}" && ! -L "${registry_source}" ]] || \
  fail "reviewed registry source unavailable"

registry_sha256="$(sha256sum "${registry_source}" | cut -d ' ' -f 1)"
[[ "${registry_sha256}" == "${expected_registry_sha256}" ]] || \
  fail "reviewed registry hash mismatch"

source_revision="$(
  docker image inspect \
    --format '{{ index .Config.Labels "org.opencontainers.image.revision" }}' \
    "${source_image}"
)"
[[ "${source_revision}" == "${source_sha}" ]] || fail "image revision mismatch"
source_image_id="$(docker image inspect --format '{{.Id}}' "${source_image}")"
[[ "${source_image_id}" =~ ^sha256:[0-9a-f]{64}$ ]] || \
  fail "invalid source image id"

docker tag "${source_image}" mee-a2:candidate
candidate_image_id="$(docker image inspect --format '{{.Id}}' mee-a2:candidate)"
[[ "${candidate_image_id}" == "${source_image_id}" ]] || \
  fail "candidate image id mismatch"

receipt_local="$(mktemp "${runner_temp}/mee-a2-candidate-receipt.XXXXXX")"
hash_local="$(mktemp "${runner_temp}/mee-a2-reviewed-registry.XXXXXX.sha256")"
cleanup_local() {
  rm -f "${receipt_local}" "${hash_local}"
}
trap cleanup_local EXIT

promoted_at_utc="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
printf '%s  %s\n' \
  "${registry_sha256}" \
  "$(basename "${registry_target}")" >"${hash_local}"
python -B - \
  "${receipt_local}" \
  "${source_repository}" \
  "${source_sha}" \
  "${source_image}" \
  "${source_image_id}" \
  "${candidate_image_id}" \
  "${registry_target}" \
  "${registry_sha256}" \
  "${workflow_run_id}" \
  "${promoted_at_utc}" <<'PY'
import json
from pathlib import Path
import sys

(
    output,
    source_repository,
    source_revision,
    source_image,
    source_image_id,
    candidate_image_id,
    reviewed_registry_path,
    reviewed_registry_sha256,
    workflow_run_id,
    promoted_at_utc,
) = sys.argv[1:]
receipt = {
    "candidate_image": "mee-a2:candidate",
    "candidate_image_id": candidate_image_id,
    "promoted_at_utc": promoted_at_utc,
    "reviewed_registry_path": reviewed_registry_path,
    "reviewed_registry_sha256": reviewed_registry_sha256,
    "schema_version": "mee-a2-candidate-promotion-receipt/v1",
    "source_image": source_image,
    "source_image_id": source_image_id,
    "source_repository": source_repository,
    "source_revision": source_revision,
    "workflow_run_id": workflow_run_id,
}
Path(output).write_text(
    json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n",
    encoding="utf-8",
)
PY

sudo -n test -d "${target_directory}" || fail "staging directory unavailable"
sudo -n test ! -L "${target_directory}" || fail "staging directory is a symlink"
for target in "${registry_target}" "${hash_target}" "${receipt_target}"; do
  sudo -n test ! -L "${target}" || fail "staging target is a symlink"
done

readonly suffix="${workflow_run_id}.$$"
readonly registry_temporary="${target_directory}/.a2-reviewed-registry.${suffix}"
readonly hash_temporary="${target_directory}/.a2-reviewed-registry-hash.${suffix}"
readonly receipt_temporary="${target_directory}/.mee-a2-candidate-receipt.${suffix}"
cleanup_root() {
  sudo -n rm -f \
    "${registry_temporary}" \
    "${hash_temporary}" \
    "${receipt_temporary}"
}
trap 'cleanup_root; cleanup_local' EXIT

sudo -n install -o root -g root -m 0644 "${registry_source}" "${registry_temporary}"
sudo -n install -o root -g root -m 0644 "${hash_local}" "${hash_temporary}"
sudo -n install -o root -g root -m 0644 "${receipt_local}" "${receipt_temporary}"

sudo -n mv -f "${registry_temporary}" "${registry_target}"
sudo -n mv -f "${hash_temporary}" "${hash_target}"
[[ "$(sudo -n stat -c '%U:%G %a' "${registry_target}")" == "root:root 644" ]] || \
  fail "reviewed registry ownership or mode mismatch"
[[ "$(sudo -n stat -c '%U:%G %a' "${hash_target}")" == "root:root 644" ]] || \
  fail "reviewed registry hash ownership or mode mismatch"
[[ "$(sudo -n sha256sum "${registry_target}" | cut -d ' ' -f 1)" == \
  "${registry_sha256}" ]] || fail "staged reviewed registry hash mismatch"
(cd "${target_directory}" && sudo -n sha256sum -c "$(basename "${hash_target}")")

# The receipt is the commit marker: app-stack must reject a candidate without it.
sudo -n mv -f "${receipt_temporary}" "${receipt_target}"
[[ "$(sudo -n stat -c '%U:%G %a' "${receipt_target}")" == "root:root 644" ]] || \
  fail "promotion receipt ownership or mode mismatch"
sudo -n cmp -s "${receipt_local}" "${receipt_target}" || \
  fail "promotion receipt mismatch"

printf 'A2 candidate promoted: revision=%s image_id=%s registry_sha256=%s receipt=%s\n' \
  "${source_sha}" \
  "${source_image_id}" \
  "${registry_sha256}" \
  "${receipt_target}"
