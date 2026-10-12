#!/usr/bin/env python3
"""Check local Markdown file links without network access."""
from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    errors = []
    paths = [*ROOT.glob("*.md"), *ROOT.joinpath("docs").rglob("*.md")]
    for directory in ("services", "deploy", "installer", "packages"):
        paths.extend(p for p in ROOT.joinpath(directory).rglob("*.md") if not any(part in {"node_modules", "dist", "__pycache__"} for part in p.parts))
    for path in sorted(paths):
        for match in re.finditer(r"\[[^\]]*\]\(([^)]+)\)", path.read_text()):
            target = match.group(1).split()[0].strip("<>")
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            resolved = (path.parent / unquote(parsed.path)).resolve()
            if not resolved.is_relative_to(ROOT) or not resolved.exists():
                errors.append(f"{path.relative_to(ROOT)}: broken local link {target}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"documentation links passed ({len(paths)} documents)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
