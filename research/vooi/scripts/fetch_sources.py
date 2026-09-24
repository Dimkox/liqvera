#!/usr/bin/env python3
"""Acquire pinned public VOOI sources without executing them.

This tool performs only:
- unauthenticated HTTPS GET requests for public web pages and same-origin
  JavaScript/CSS/manifest assets referenced by their HTML;
- Git fetches of exact commits from the official public repositories listed in
  clients.lock.json.

It never sends cookies, wallet data, API tokens or authenticated requests.
Downloaded material is written below an ignored artifacts directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, build_opener

USER_AGENT = "multi-exchange-engine-vooi-research/1.0 (+static-public-acquisition)"
MAX_OBJECT_BYTES = 32 * 1024 * 1024
MAX_WEB_OBJECTS_PER_CLIENT = 256
FETCHABLE_LINK_RELS = {
    "stylesheet",
    "manifest",
    "modulepreload",
}


class AcquisitionError(RuntimeError):
    """Raised when an acquisition violates a safety or integrity rule."""


class AssetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.urls: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value for key, value in attrs if value is not None}
        tag = tag.lower()
        if tag == "script" and values.get("src"):
            self.urls.add(values["src"])
            return
        if tag == "link" and values.get("href"):
            rels = {part.lower() for part in values.get("rel", "").split()}
            as_value = values.get("as", "").lower()
            if rels & FETCHABLE_LINK_RELS or ("preload" in rels and as_value in {"script", "style"}):
                self.urls.add(values["href"])


@dataclass(frozen=True)
class Download:
    requested_url: str
    final_url: str
    content_type: str
    body: bytes

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.body).hexdigest()


def load_inventory(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_https_url(url: str) -> tuple[str, str]:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise AcquisitionError(f"only absolute HTTPS URLs are allowed: {url!r}")
    if parsed.username or parsed.password:
        raise AcquisitionError("credentials in URLs are forbidden")
    return parsed.hostname.lower(), parsed.path


def fetch(url: str) -> Download:
    expected_host, _ = safe_https_url(url)
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/javascript,text/css,application/manifest+json,application/json;q=0.8,*/*;q=0.1",
            "Cache-Control": "no-cache",
        },
        method="GET",
    )
    opener = build_opener()
    try:
        with opener.open(request, timeout=30) as response:
            final_url = response.geturl()
            final_host, _ = safe_https_url(final_url)
            if final_host != expected_host:
                raise AcquisitionError(
                    f"cross-host redirect rejected: {expected_host!r} -> {final_host!r}"
                )
            declared = response.headers.get("Content-Length")
            if declared and int(declared) > MAX_OBJECT_BYTES:
                raise AcquisitionError(f"declared object too large: {declared} bytes")
            body = response.read(MAX_OBJECT_BYTES + 1)
            if len(body) > MAX_OBJECT_BYTES:
                raise AcquisitionError(f"object exceeds {MAX_OBJECT_BYTES} bytes")
            content_type = response.headers.get_content_type()
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        raise AcquisitionError(f"GET failed for {url}: {exc}") from exc
    return Download(url, final_url, content_type, body)


def extension_for(url: str, content_type: str) -> str:
    suffix = Path(urlsplit(url).path).suffix
    if suffix and len(suffix) <= 10 and suffix.replace(".", "").isalnum():
        return suffix.lower()
    guessed = mimetypes.guess_extension(content_type) or ".bin"
    if guessed == ".jpe":
        return ".jpg"
    return guessed


def store_download(base: Path, item: Download) -> dict:
    objects = base / "objects"
    objects.mkdir(parents=True, exist_ok=True)
    suffix = extension_for(item.final_url, item.content_type)
    target = objects / f"{item.sha256}{suffix}"
    if target.exists():
        current = hashlib.sha256(target.read_bytes()).hexdigest()
        if current != item.sha256:
            raise AcquisitionError(f"existing object hash mismatch: {target}")
    else:
        target.write_bytes(item.body)
    return {
        "requested_url": item.requested_url,
        "final_url": item.final_url,
        "content_type": item.content_type,
        "size": len(item.body),
        "sha256": item.sha256,
        "object": str(target.relative_to(base)),
    }


def selected_ids(raw: str | None) -> set[str] | None:
    if raw is None:
        return None
    values = {value.strip() for value in raw.split(",") if value.strip()}
    if not values:
        raise AcquisitionError("--include did not contain any client IDs")
    return values


def acquire_web(inventory: dict, output: Path, include: set[str] | None) -> None:
    web_root = output / "web"
    for client in inventory["web_clients"]:
        client_id = client["id"]
        if include is not None and client_id not in include:
            continue
        url = client["url"]
        host, _ = safe_https_url(url)
        client_root = web_root / client_id
        client_root.mkdir(parents=True, exist_ok=True)

        root_download = fetch(url)
        records = [store_download(client_root, root_download)]

        if root_download.content_type == "text/html":
            parser = AssetParser()
            parser.feed(root_download.body.decode("utf-8", errors="replace"))
            asset_urls: list[str] = []
            for raw_asset_url in sorted(parser.urls):
                absolute = urljoin(root_download.final_url, raw_asset_url)
                asset_host, _ = safe_https_url(absolute)
                if asset_host == host:
                    asset_urls.append(absolute)
            if len(asset_urls) > MAX_WEB_OBJECTS_PER_CLIENT:
                raise AcquisitionError(
                    f"{client_id}: HTML referenced {len(asset_urls)} same-origin assets; "
                    f"limit is {MAX_WEB_OBJECTS_PER_CLIENT}"
                )
            for asset_url in asset_urls:
                records.append(store_download(client_root, fetch(asset_url)))

        metadata = {
            "client_id": client_id,
            "source_url": url,
            "captured_unix": int(time.time()),
            "authenticated": False,
            "javascript_executed": False,
            "objects": records,
        }
        (client_root / "capture.json").write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"captured {client_id}: {len(records)} objects")


def run_git(args: list[str], cwd: Path | None = None) -> str:
    env = os.environ.copy()
    env.update(
        {
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_CONFIG_NOSYSTEM": "1",
        }
    )
    completed = subprocess.run(
        ["git", *args],
        cwd=cwd,
        env=env,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        raise AcquisitionError(
            f"git {' '.join(args)} failed ({completed.returncode}): "
            f"{completed.stderr.strip()}"
        )
    return completed.stdout.strip()


def acquire_repositories(
    inventory: dict,
    output: Path,
    include: set[str] | None,
    force: bool,
) -> None:
    repos_root = output / "repositories"
    repos_root.mkdir(parents=True, exist_ok=True)

    for client in inventory["programmatic_clients"]:
        client_id = client["id"]
        if include is not None and client_id not in include:
            continue
        target = repos_root / client_id
        if target.exists():
            if not force:
                raise AcquisitionError(f"{target} already exists; use --force to replace")
            shutil.rmtree(target)

        repo = client["repo"]
        commit = client["commit"]
        safe_https_url(repo)

        target.mkdir(parents=True)
        run_git(["init", "--quiet"], target)
        run_git(["remote", "add", "origin", repo], target)
        run_git(["fetch", "--quiet", "--depth", "1", "origin", commit], target)
        run_git(["checkout", "--quiet", "--detach", "FETCH_HEAD"], target)
        actual = run_git(["rev-parse", "HEAD"], target)
        if actual != commit:
            raise AcquisitionError(
                f"{client_id}: expected {commit}, fetched {actual}"
            )

        metadata = {
            "client_id": client_id,
            "repo": repo,
            "expected_commit": commit,
            "actual_commit": actual,
            "fetched_unix": int(time.time()),
            "executed_downloaded_code": False,
        }
        (target / "SOURCE-METADATA.json").write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"fetched {client_id}@{actual}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    base = Path(__file__).resolve().parents[1]
    parser.add_argument(
        "mode",
        choices=("repos", "web", "all"),
        help="Which public sources to acquire",
    )
    parser.add_argument(
        "--inventory",
        type=Path,
        default=base / "clients.lock.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=base / "artifacts",
        help="Ignored destination for downloaded material",
    )
    parser.add_argument(
        "--include",
        help="Comma-separated client IDs; default is every entry in the selected mode",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing repository checkout",
    )
    args = parser.parse_args()

    try:
        inventory = load_inventory(args.inventory)
        include = selected_ids(args.include)
        args.output.mkdir(parents=True, exist_ok=True)
        if args.mode in {"repos", "all"}:
            acquire_repositories(inventory, args.output, include, args.force)
        if args.mode in {"web", "all"}:
            acquire_web(inventory, args.output, include)
    except (OSError, json.JSONDecodeError, AcquisitionError) as exc:
        print(f"acquisition failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
