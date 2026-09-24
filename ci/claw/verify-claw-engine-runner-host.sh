#!/usr/bin/env bash
set -euo pipefail
engine=actions.runner.Dimkox-multi-exchange-engine.claw-engine-runner.service; app=actions.runner.Dimkox-openclaw-airgap-farm.claw-runner.service; tree=/home/pall/actions-runner-engine
test "$(systemctl show -p User --value "$engine")" = claw-engine-runner; test "$(systemctl show -p WorkingDirectory --value "$engine")" = "$tree"
test "$(systemctl is-active "$engine")" = active; test "$(systemctl is-active "$app")" = active
test "$(systemctl show -p WorkingDirectory --value "$app")" = /home/pall/actions-runner
runuser -u claw-engine-runner -- env HOME=/var/lib/claw-engine-runner XDG_RUNTIME_DIR=/run/user/980 podman info --format '{{.Host.Security.Rootless}}' | grep -Fx true
runuser -u claw-engine-runner -- env HOME=/var/lib/claw-engine-runner XDG_RUNTIME_DIR=/run/user/980 podman image exists docker.io/rhysd/actionlint@sha256:9d36088643581e728c969f35141f88139fec77280b2be23c1f66f8e40e1025e7
runuser -u claw-engine-runner -- env HOME=/var/lib/claw-engine-runner XDG_RUNTIME_DIR=/run/user/980 podman run --pull=never --rm --network=none docker.io/rhysd/actionlint@sha256:9d36088643581e728c969f35141f88139fec77280b2be23c1f66f8e40e1025e7 -version >/dev/null
journalctl -u "$engine" --since '-2 minutes' --no-pager | grep -F 'Listening for Jobs'
IFS= read -r token; test -n "$token"; curl --fail --silent --config <(printf 'header = "Authorization: Bearer %s"\n' "$token") "https://api.github.com/repos/Dimkox/multi-exchange-engine/actions/runners" | python3 -c "import json,sys; r=[x for x in json.load(sys.stdin)['runners'] if x['name']=='claw-engine-runner']; assert len(r)==1 and r[0]['status']=='online' and {'self-hosted','claw','claw-engine-runner'}<={x['name'] for x in r[0]['labels']}"; unset token
