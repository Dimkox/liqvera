#!/usr/bin/env python3
"""Check local Markdown file links without network access."""
from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]



def check_mezo_readme(readme: str, protocol: str) -> list[str]:
    """Validate the integration table without RPC or a wallet configuration."""
    errors = []
    try:
        section = readme.split("## Mezo integration\n", 1)[1].split("\n## ", 1)[0]
        table = section.split("| Contract |", 1)[1].split("\n\n", 1)[0]
        chain = re.search(r"export const MEZO_TESTNET = \{(.*?)\} as const;", protocol, re.S)[1]
        explorer = re.search(r'explorerUrl: "([^"]+)"', chain)[1]
        musd = re.search(r"export const MUSD_TESTNET = \{(.*?)\} as const;", protocol, re.S)[1]
        dex = re.search(r"export const MEZO_TESTNET_DEX = \{(.*?)\} as const;", protocol, re.S)[1]
        expected = {
            re.search(r'address: "(0x[0-9a-fA-F]{40})"', musd)[1],
            re.search(r'permit2Address: "(0x[0-9a-fA-F]{40})"', protocol)[1],
            re.search(r'exactProxyAddress: "(0x[0-9a-fA-F]{40})"', protocol)[1],
            *re.findall(r'"(0x[0-9a-fA-F]{40})"', dex),
        }
        links = re.findall(r'\[(0x[0-9a-fA-F]{40})\]\(([^)]+)\)', table)
        addresses = [url for _, url in links]
        if any(url != f"{explorer}/address/{label}" for label, url in links):
            errors.append("README Mezo address label differs from explorer destination")
        if len(addresses) != len(expected) or set(addresses) != {f"{explorer}/address/{a}" for a in expected}:
            errors.append("README Mezo contract table differs from protocol metadata")
        for link in re.findall(r'\]\((https://[^)]+)\)', section):
            if "explorer" in urlsplit(link).netloc and not link.startswith(explorer + "/"):
                errors.append("README Mezo explorer link uses the wrong network")
    except (IndexError, TypeError):
        errors.append("README Mezo integration table or protocol metadata missing")
    return errors

def main() -> int:
    errors = check_mezo_readme((ROOT / "README.md").read_text(),
                               (ROOT / "packages/mezo-protocol/src/index.ts").read_text())
    paths = [*ROOT.glob("*.md"), *ROOT.joinpath("docs").rglob("*.md")]
    for directory in ("services", "deploy", "packages"):
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
