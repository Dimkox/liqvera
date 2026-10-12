#!/bin/sh
set -eu
python -c 'import sys; assert sys.version_info[:3] == (3, 14, 8), "Review security backports before changing Python"'
cd /security-patches
printf '%s\n' \
  '431ff82e5da6d86e4885fdf989c576f0c1d8b24eb00eb80a90fa9169a8b07ba3  cpython-poplib.patch' \
  '9ed3354906075c84dd9dfb9acdf7dc9d092df098151d56bf21a6ddcad98bed9a  cpython-tempfile.patch' \
  | sha256sum -c -
apk add --no-cache --virtual .security-patch-tools patch
patch --batch --forward --fuzz=0 -d /usr/local/lib/python3.14 -p2 < cpython-poplib.patch
patch --batch --forward --fuzz=0 -d /usr/local/lib/python3.14 -p2 < cpython-tempfile.patch
apk del .security-patch-tools
mkdir -p /usr/local/share/liqvera-security
cp README.md /usr/local/share/liqvera-security/python-backports.md
sha256sum /usr/local/lib/python3.14/poplib.py /usr/local/lib/python3.14/tempfile.py \
  /usr/local/lib/python3.14/shutil.py > /usr/local/share/liqvera-security/python-backports.sha256
