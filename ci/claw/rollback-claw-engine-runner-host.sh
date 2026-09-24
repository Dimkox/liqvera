#!/usr/bin/env bash
set -euo pipefail
test "$(id -u)" -eq 0; tx=/var/lib/claw-engine-runner-bootstrap; engine=actions.runner.Dimkox-multi-exchange-engine.claw-engine-runner.service; app=actions.runner.Dimkox-openclaw-airgap-farm.claw-runner.service
test -f "$tx/ownership.acl"; systemctl stop "$engine"
rm -f "/etc/systemd/system/$engine.d/10-claw-user.conf"; cp -a "$tx/subuid" /etc/subuid; cp -a "$tx/subgid" /etc/subgid; setfacl --restore="$tx/ownership.acl"
loginctl disable-linger claw-engine-runner || true; systemctl daemon-reload; systemctl start "$engine"
python3 - "$tx/packages.before" <<'PY' | xargs -r apt-get remove --yes
import sys
before={x.split('\t',1)[0] for x in open(sys.argv[1])}
names={'conmon','fuse-overlayfs','golang-github-containers-common','golang-github-containers-image','libslirp0','libsubid4','netavark','podman','slirp4netns','uidmap'}
print(*sorted(names-before))
PY
getent passwd claw-engine-runner >/dev/null && userdel claw-engine-runner || true; getent group claw-engine-runner >/dev/null && groupdel claw-engine-runner || true
read -r app_active < "$tx/app.before"; test "$(systemctl is-active "$app")" = "$app_active"; test "$(systemctl show -p WorkingDirectory --value "$app")" = /home/pall/actions-runner
printf ROLLED_BACK > "$tx/state"
