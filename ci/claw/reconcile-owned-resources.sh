#!/usr/bin/env bash
set -euo pipefail
test "${RUNNER_NAME:-}" = claw-engine-runner || exit 2
ledger=/var/lib/mee-controller/resources.jsonl
test -f "$ledger" || { echo 'RECONCILE_BLOCKED:LEDGER_UNAVAILABLE' >&2; exit 2; }
records=$(mktemp); trap 'rm -f -- "$records"' EXIT
python3 -B - "$ledger" <<'PY' > "$records"
import json,re,sys
for line in open(sys.argv[1],encoding='utf-8'):
 x=json.loads(line)
 if set(x)!={'resource_kind','resource_name','repository_sha256','run_id','source_sha','controller_sha'}: raise SystemExit('RECONCILE_BLOCKED:LEDGER_SCHEMA_INVALID')
 if x['resource_kind'] not in {'container','pod','network','volume'} or not re.fullmatch(r'[a-zA-Z0-9_.-]{1,200}',x['resource_name']): raise SystemExit('RECONCILE_BLOCKED:LEDGER_VALUE_INVALID')
 if not re.fullmatch(r'[0-9a-f]{64}',x['repository_sha256']) or not re.fullmatch(r'[0-9]+',str(x['run_id'])) or not re.fullmatch(r'[0-9a-f]{40}',x['source_sha']) or not re.fullmatch(r'[0-9a-f]{40}',x['controller_sha']): raise SystemExit('RECONCILE_BLOCKED:LEDGER_VALUE_INVALID')
 print(x['resource_kind'],x['resource_name'],x['repository_sha256'],x['run_id'],x['source_sha'],x['controller_sha'],sep='\t')
PY
while IFS=$'\t' read -r kind name repo run source controller; do
  test -n "$kind" && test -n "$name" && test -n "$repo" && test -n "$run" && test -n "$source" && test -n "$controller"
  filters=(--filter label=io.mee.controller=story-1-2 --filter "label=mee.repository_sha256=$repo" --filter "label=mee.run_id=$run" --filter "label=mee.source_sha=$source" --filter "label=mee.controller_sha=$controller")
  case "$kind" in
    container) mapfile -t matches < <(podman ps -a "${filters[@]}" --format '{{.Names}}');;
    pod) mapfile -t matches < <(podman pod ps "${filters[@]}" --format '{{.Name}}');;
    network) mapfile -t matches < <(podman network ls "${filters[@]}" --format '{{.Name}}');;
    volume) mapfile -t matches < <(podman volume ls "${filters[@]}" --format '{{.Name}}');;
    *) echo 'RECONCILE_BLOCKED:LEDGER_KIND_INVALID' >&2; exit 2;;
  esac
  test "${#matches[@]}" -le 1 && { test "${#matches[@]}" -eq 0 || test "${matches[0]}" = "$name"; } || { echo 'RECONCILE_BLOCKED:IDENTITY_COLLISION' >&2; exit 2; }
  if test "${#matches[@]}" -eq 1; then
    case "$kind" in container) podman rm -f -- "$name";; pod) podman pod rm -f -- "$name";; network) podman network rm -- "$name";; volume) podman volume rm -- "$name";; esac
  fi
done < "$records"
printf '%s\n' 'authority=NONE' 'status=OWNED_LEDGER_RESOURCES_ABSENT'
