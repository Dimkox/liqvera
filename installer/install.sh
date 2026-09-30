#!/usr/bin/env bash
set -euo pipefail
readonly PATH='/usr/bin:/bin'
export PATH

readonly INSTALLER_DIR="$(cd -P -- "${BASH_SOURCE[0]%/*}" && pwd -P)"
# shellcheck source=installer/lib/common.sh
source "${INSTALLER_DIR}/lib/common.sh"

usage() {
    cat <<'EOF'
Usage: install.sh --verified-release DIR --sha256 DIGEST --install-dir DIR --config FILE [OPTIONS]

Options:
  --verified-release DIR              Task 2 materialized release directory
  --sha256 DIGEST                     Independently supplied archive SHA-256
  --install-dir DIR                   Narrow local installation root
  --config FILE                       Closed JSON installer configuration
  --install-deps                      Permit the separately approved dependency command
  --approve-dependency-command SHA256 Exact NUL-joined command digest approval
  --non-interactive                   Disable prompts; grants no authority
  --help                              Show this help
  --version                           Print 0.0.2
EOF
}

args=()
while (($#)); do
    case "$1" in
        --help)
            usage
            exit 0
            ;;
        --version)
            printf '0.0.2\n'
            exit 0
            ;;
        --verified-release|--sha256|--install-dir|--config|--approve-dependency-command)
            if (($# < 2)); then
                printf 'CONFIG_INVALID: missing value for %s\n' "$1" >&2
                exit 2
            fi
            args+=("$1" "$2")
            shift 2
            ;;
        --install-deps|--non-interactive)
            args+=("$1")
            shift
            ;;
        *)
            printf 'CONFIG_INVALID: unknown argument\n' >&2
            exit 2
            ;;
    esac
done

args+=(--bash-version "${BASH_VERSION}")
liqvera_run_runtime "${args[@]}"
