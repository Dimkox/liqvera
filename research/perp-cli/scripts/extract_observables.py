#!/usr/bin/env python3
"""Extract static URL/env/bin-like observables from acquired public artifacts."""

from __future__ import annotations

import argparse
import json
import re
import tarfile
from pathlib import Path
from typing import Iterable

MAX_TEXT_BYTES = 4 * 1024 * 1024
TEXT_SUFFIXES = {
    ".ts", ".tsx", ".js", ".mjs", ".cjs", ".json", ".md", ".yml", ".yaml",
    ".sh", ".txt", ".toml", ".ini", ".env", ".css", ".html",
}
URL_RE = re.compile(r"https://[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]+")
ENV_RE = re.compile(r"\b[A-Z][A-Z0-9_]{2,}\b")
COMMAND_RE = re.compile(r"\bperp(?:-mcp|-guardrail)?\b")


def safe_text(data: bytes) -> str:
    if len(data) > MAX_TEXT_BYTES:
        return ""
    if b"\x00" in data[:4096]:
        return ""
    return data.decode("utf-8", errors="replace")


def record_text(source: str, text: str, out: dict) -> None:
    for url in URL_RE.findall(text):
        out["urls"].setdefault(url.rstrip(").,;\"'"), []).append(source)
    for env in ENV_RE.findall(text):
        if any(token in env for token in ("PRIVATE_KEY", "API_KEY", "PASSPHRASE", "TOKEN", "SECRET")):
            out["secret_like_env_names"].setdefault(env, []).append(source)
        elif env.startswith(("PACIFICA_", "HYPERLIQUID_", "LIGHTER_", "ASTER_", "OWS_", "HL_")):
            out["env_names"].setdefault(env, []).append(source)
    for command in COMMAND_RE.findall(text):
        out["command_tokens"].setdefault(command, []).append(source)

    if source.endswith("package.json"):
        try:
            package = json.loads(text)
        except json.JSONDecodeError:
            return
        if isinstance(package, dict) and isinstance(package.get("bin"), dict):
            for name, target in package["bin"].items():
                out["bin_entrypoints"][name] = {"target": target, "source": source}


def iter_regular_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def scan_tarball(path: Path, out: dict) -> None:
    try:
        with tarfile.open(path, "r:gz") as tf:
            for member in tf.getmembers():
                if not member.isfile():
                    continue
                suffix = Path(member.name).suffix.lower()
                if suffix not in TEXT_SUFFIXES or member.size > MAX_TEXT_BYTES:
                    continue
                fh = tf.extractfile(member)
                if fh is None:
                    continue
                data = fh.read(MAX_TEXT_BYTES + 1)
                text = safe_text(data)
                if text:
                    record_text(f"{path}:{member.name}", text, out)
    except (tarfile.TarError, OSError):
        return


def dedupe(out: dict) -> None:
    for key in ("urls", "env_names", "secret_like_env_names", "command_tokens"):
        for name, sources in list(out[key].items()):
            out[key][name] = sorted(set(sources))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("-o", "--output", type=Path, required=True)
    args = parser.parse_args()

    out = {
        "urls": {},
        "env_names": {},
        "secret_like_env_names": {},
        "command_tokens": {},
        "bin_entrypoints": {},
    }

    for path in iter_regular_files(args.root):
        try:
            text = safe_text(path.read_bytes())
        except OSError:
            continue
        if text:
            record_text(str(path), text, out)

    for path in args.root.rglob("*.tgz"):
        if path.is_file():
            scan_tarball(path, out)

    dedupe(out)
    args.output.write_text(
        json.dumps(out, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({k: len(v) for k, v in out.items()}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
