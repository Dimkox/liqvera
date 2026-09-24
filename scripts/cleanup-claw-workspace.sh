#!/usr/bin/env bash
# Remove only this GitHub Actions run's explicitly named temporary workspace.
set -euo pipefail

if [[ "$#" -ne 1 ]]; then
  echo "usage: $0 RUN_TEMP_PATH" >&2
  exit 64
fi

[[ "${GITHUB_RUN_ID:-}" =~ ^[0-9]+$ ]]
[[ "${GITHUB_RUN_ATTEMPT:-}" =~ ^[0-9]+$ ]]
[[ -n "${GITHUB_JOB:-}" ]]
[[ -n "${CLAW_WORKSPACE_SHARD:-}" ]]
[[ -n "${RUNNER_TEMP:-}" ]]

runner_temp="$(realpath -e -- "${RUNNER_TEMP}")"
job_name="$(printf '%s' "${GITHUB_JOB}" | tr -c 'A-Za-z0-9._-' '_')"
workspace_shard="$(printf '%s' "${CLAW_WORKSPACE_SHARD}" | tr -c 'A-Za-z0-9._-' '_')"
target="$(realpath -m -- "$1")"
expected="${runner_temp}/${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}-${job_name}-${workspace_shard}"

if [[ "${runner_temp}" == "/" || "${target}" != "${expected}" ]]; then
  echo "refusing to clean a path outside this run's temporary workspace" >&2
  exit 64
fi

if [[ ! -e "${target}" ]]; then
  exit 0
fi

rm -rf -- "${target}"
