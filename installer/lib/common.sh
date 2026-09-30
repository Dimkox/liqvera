#!/usr/bin/env bash

# This file is source-only and performs no work while loading.
liqvera_runtime_path() {
    local library_dir
    library_dir="$(cd -P -- "${BASH_SOURCE[0]%/*}" && pwd -P)"
    printf '%s/runtime.py\n' "${library_dir}"
}

liqvera_run_runtime() {
    local runtime
    runtime="$(liqvera_runtime_path)"
    exec /usr/bin/python3 -I -B "${runtime}" "$@"
}
