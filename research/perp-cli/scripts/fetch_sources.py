#!/usr/bin/env python3
"""Fetch the exact public Git revisions pinned in clients.lock.json.

The script only runs `git init`, `git remote add`, `git fetch` and detached
checkout against public HTTPS repositories listed in the research inventory.
It does not run downloaded project code or package lifecycle scripts.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit


class AcquisitionError(RuntimeError):
    pass


def run_git(args: list[str], cwd: Path) -> str:
    env = os.environ.copy()
    env.update({"GIT_TERMINAL_PROMPT": "0", "GIT_CONFIG_NOSYSTEM": "1"})
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        env=env,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        raise AcquisitionError(result.stderr.strip() or "git command failed")
    return result.stdout.strip()


def validate_repo_url(url: str) -> None:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != "github.com":
        raise AcquisitionError(f"only public github.com HTTPS repos are allowed: {url}")
    if parsed.username or parsed.password:
        raise AcquisitionError("credentials in repository URLs are forbidden")


def repo_items(inventory: dict) -> list[dict]:
    found: list[dict] = []
    for section in ("official_components", "third_party_surfaces"):
        for item in inventory.get(section, []):
            if item.get("kind") in {"source_repository", "third_party_repository"}:
                found.append(item)
    return found


def fetch_repo(item: dict, root: Path, force: bool) -> None:
    validate_repo_url(item["repo"])
    target = root / item["id"]
    if target.exists():
        if not force:
            raise AcquisitionError(f"{target} exists; use --force")
        shutil.rmtree(target)
    target.mkdir(parents=True)

    run_git(["init", "--quiet"], target)
    run_git(["remote", "add", "origin", item["repo"]], target)
    run_git(["fetch", "--quiet", "--depth", "1", "origin", item["commit"]], target)
    run_git(["checkout", "--quiet", "--detach", "FETCH_HEAD"], target)
    actual = run_git(["rev-parse", "HEAD"], target)
    if actual != item["commit"]:
        raise AcquisitionError(f"expected {item['commit']}, got {actual}")
    print(f"{item['id']}: {actual}")


def main() -> int:
    parser = argparse.ArgumentParser()
    base = Path(__file__).resolve().parents[1]
    parser.add_argument("mode", choices=("repos",))
    parser.add_argument("--inventory", type=Path, default=base / "clients.lock.json")
    parser.add_argument("--output", type=Path, default=base / "artifacts" / "repositories")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    try:
        inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
        args.output.mkdir(parents=True, exist_ok=True)
        for item in repo_items(inventory):
            fetch_repo(item, args.output, args.force)
    except (OSError, json.JSONDecodeError, AcquisitionError) as exc:
        print(f"perp-cli source acquisition failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
