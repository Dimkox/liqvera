#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -P -- "${BASH_SOURCE[0]%/*}" && pwd -P)"
exec /usr/bin/python3 -I -B "${script_dir}/lib/lifecycle.py" "$@"
