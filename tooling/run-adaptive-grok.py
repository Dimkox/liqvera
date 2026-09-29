#!/usr/bin/env python3
"""Validate and execute the pinned Adaptive Grok Build Pro gitlink."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True

TOOLING = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLING))

from adaptive_grok_pin import (  # noqa: E402
    COMMIT,
    TAG,
    TRUSTED_SCRIPT_NAMES,
    VERSION,
    ToolingPinError,
    validate,
)

SCRIPTS = TRUSTED_SCRIPT_NAMES
HOOKS = {
    "post_tool_use.py",
    "pre_compact.py",
    "pre_tool_use.py",
    "session_end.py",
    "session_start.py",
    "stop_gate.py",
    "subagent_start.py",
    "subagent_stop.py",
    "user_prompt_submit.py",
}


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def main() -> int:
    root = _root()
    try:
        source = validate(root)
    except ToolingPinError as exc:
        print(f"Adaptive Grok pin validation failed: {exc}", file=sys.stderr)
        return 2

    invoked = Path(sys.argv[0]).name
    arguments = sys.argv[1:]
    if invoked == "grok_verify.py":
        target = root / "tooling/grok-verify.py"
    elif invoked in SCRIPTS:
        target = source / "scripts" / invoked
    elif arguments[:1] == ["--hook"] and len(arguments) >= 2 and arguments[1] in HOOKS:
        target = source / ".grok/hooks" / arguments[1]
        arguments = arguments[2:]
    elif arguments == ["--check"]:
        print(f'{{"commit": "{COMMIT}", "tag": "{TAG}", "version": "{VERSION}"}}')
        return 0
    else:
        print("Adaptive Grok entrypoint is not allowed", file=sys.stderr)
        return 2
    if not target.is_file() or target.is_symlink():
        print(f"Adaptive Grok entrypoint is unavailable: {target}", file=sys.stderr)
        return 2
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    os.execv(sys.executable, [sys.executable, str(target), *arguments])
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
