#!/usr/bin/env bash
set -Eeuo pipefail

usage() {
  cat <<'EOF'
Usage: analyze-goodcryptox-apk.sh <apk|xapk|apkm|zip> [output-directory]

Creates a local, reproducible evidence bundle. Nothing is uploaded. By default
it does not decompile source code. Set GOODCRYPTOX_DECOMPILE=1 to run jadx and
apktool when they are installed; keep that output outside Git.
EOF
}

if [[ ${1:-} == "-h" || ${1:-} == "--help" ]]; then
  usage
  exit 0
fi
if [[ $# -lt 1 || $# -gt 2 ]]; then
  usage >&2
  exit 64
fi

INPUT=$1
if [[ ! -f "$INPUT" ]]; then
  printf 'error: input file does not exist: %s\n' "$INPUT" >&2
  exit 66
fi

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
EXTRACTOR="$SCRIPT_DIR/extract_apk_indicators.py"
if [[ ! -f "$EXTRACTOR" ]]; then
  printf 'error: companion extractor not found: %s\n' "$EXTRACTOR" >&2
  exit 69
fi

if ! python3 - "$INPUT" <<'PY'
import sys
import zipfile
raise SystemExit(0 if zipfile.is_zipfile(sys.argv[1]) else 1)
PY
then
  printf 'error: input is not a valid APK-compatible ZIP archive: %s\n' "$INPUT" >&2
  exit 65
fi

BASE_NAME=$(basename -- "$INPUT")
BASE_STEM=${BASE_NAME%.*}
OUTPUT=${2:-"$PWD/goodcryptox-analysis-${BASE_STEM}"}
mkdir -p -- "$OUTPUT"

{
  sha256sum -- "$INPUT"
  sha1sum -- "$INPUT"
  if command -v md5sum >/dev/null 2>&1; then
    md5sum -- "$INPUT"
  fi
} >"$OUTPUT/hashes.txt"

unzip -l -- "$INPUT" >"$OUTPUT/zip-listing.txt"
python3 "$EXTRACTOR" "$INPUT" --output "$OUTPUT/indicators.json"

{
  printf 'input=%s\n' "$INPUT"
  printf 'output=%s\n' "$OUTPUT"
  printf 'python3=%s\n' "$(command -v python3 || printf missing)"
  printf 'unzip=%s\n' "$(command -v unzip || printf missing)"
  for tool in apksigner apkanalyzer aapt2 aapt apktool jadx; do
    if command -v "$tool" >/dev/null 2>&1; then
      printf '%s=%s\n' "$tool" "$(command -v "$tool")"
    else
      printf '%s=missing\n' "$tool"
    fi
  done
} >"$OUTPUT/tool-status.txt"

if command -v file >/dev/null 2>&1; then
  file -- "$INPUT" >"$OUTPUT/file-type.txt" || true
fi

if command -v apksigner >/dev/null 2>&1; then
  apksigner verify --verbose --print-certs "$INPUT" >"$OUTPUT/apksigner.txt" 2>&1 || true
fi

if command -v apkanalyzer >/dev/null 2>&1; then
  apkanalyzer manifest print "$INPUT" >"$OUTPUT/manifest.xml" 2>"$OUTPUT/apkanalyzer-manifest.stderr" || true
  apkanalyzer dex packages "$INPUT" >"$OUTPUT/dex-packages.txt" 2>"$OUTPUT/apkanalyzer-dex.stderr" || true
fi

AAPT_BIN=""
if command -v aapt2 >/dev/null 2>&1; then
  AAPT_BIN=$(command -v aapt2)
elif command -v aapt >/dev/null 2>&1; then
  AAPT_BIN=$(command -v aapt)
fi
if [[ -n "$AAPT_BIN" ]]; then
  "$AAPT_BIN" dump badging "$INPUT" >"$OUTPUT/aapt-badging.txt" 2>&1 || true
  "$AAPT_BIN" dump permissions "$INPUT" >"$OUTPUT/aapt-permissions.txt" 2>&1 || true
fi

if [[ ${GOODCRYPTOX_DECOMPILE:-0} == "1" ]]; then
  if command -v apktool >/dev/null 2>&1; then
    apktool d --force --output "$OUTPUT/apktool" "$INPUT" >"$OUTPUT/apktool.log" 2>&1 || true
  fi
  if command -v jadx >/dev/null 2>&1; then
    jadx --output-dir "$OUTPUT/jadx" "$INPUT" >"$OUTPUT/jadx.log" 2>&1 || true
  fi
  cat >"$OUTPUT/DECOMPILED_OUTPUT_NOTICE.txt" <<'EOF'
This directory may contain decompiled proprietary material. Keep it local,
review it only for lawful interoperability/security research, and do not commit
or redistribute it without authorization.
EOF
fi

printf 'Analysis bundle written to %s\n' "$OUTPUT"
