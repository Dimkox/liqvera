#!/usr/bin/env python3
"""Inspect an isolated installed distribution for Stage A namespace purity."""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
from pathlib import Path


_PROBE = r"""
import importlib.metadata
import json
import sys

name = sys.argv[1]
dist = importlib.metadata.distribution(name)
requires = tuple(str(item) for item in (dist.requires or ()))
top_level = []
text = dist.read_text("top_level.txt")
if text:
    top_level = [line.strip() for line in text.splitlines() if line.strip()]
files = []
for item in dist.files or ():
    path = str(item)
    if path.endswith(".py"):
        files.append(path)
print(json.dumps({"requires": requires, "top_level": top_level, "files": files}))
"""


_CAMEL = __import__("re").compile(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\W|$)|\d+")


def _requirement_name(item: str) -> str:
    return item.split(" ", 1)[0].split("[", 1)[0].split("==", 1)[0].split(">", 1)[0].split("<", 1)[0].lower()


def _identifier_tokens(name: str) -> set[str]:
    parts = {part.casefold() for part in _CAMEL.findall(name) if part}
    parts.add(name.casefold())
    return parts


def _allows_order_book(tokens: set[str]) -> bool:
    return "order" in tokens and "book" in tokens


def _scan_symbols(source: str, forbidden: set[str]) -> set[str]:
    tree = ast.parse(source)
    hits: set[str] = set()
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Name):
            names.append(node.id)
        elif isinstance(node, ast.Attribute):
            names.append(node.attr)
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            names.append(node.name)
        for name in names:
            tokens = _identifier_tokens(name)
            for symbol in forbidden:
                if symbol == "order" and _allows_order_book(tokens):
                    continue
                if symbol in tokens:
                    hits.add(name)
    return hits


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", required=True)
    parser.add_argument("--distribution", required=True)
    parser.add_argument("--allow-namespace", action="append", default=[])
    parser.add_argument("--forbid-namespace", nargs="*", default=[])
    parser.add_argument("--forbid-dependency", nargs="*", default=[])
    parser.add_argument("--allow-dependency", nargs="*", default=None)
    parser.add_argument("--forbid-symbol", nargs="*", default=[])
    args = parser.parse_args(argv)

    probe = subprocess.run(
        [args.python, "-I", "-c", _PROBE, args.distribution],
        check=False,
        text=True,
        capture_output=True,
    )
    if probe.returncode != 0:
        sys.stderr.write(probe.stderr)
        return probe.returncode or 1
    payload = json.loads(probe.stdout)
    requires = tuple(payload["requires"])
    top_level = tuple(payload["top_level"])
    allowed = tuple(args.allow_namespace)
    if allowed and any(name not in allowed for name in top_level):
        sys.stderr.write(f"unexpected top-level modules: {top_level}\n")
        return 1
    forbidden_ns = set(args.forbid_namespace)
    if forbidden_ns.intersection(top_level):
        sys.stderr.write(f"forbidden namespace present: {top_level}\n")
        return 1
    require_names = {_requirement_name(item) for item in requires}
    forbidden_deps = {item.lower() for item in args.forbid_dependency}
    overlap = require_names.intersection(forbidden_deps)
    if overlap:
        sys.stderr.write(f"forbidden dependency present: {sorted(overlap)}\n")
        return 1
    if args.allow_dependency is None:
        if requires:
            sys.stderr.write(f"dependency closure must be empty: {requires}\n")
            return 1
    else:
        allowed_deps = {item.lower() for item in args.allow_dependency}
        extra = require_names - allowed_deps
        if extra:
            sys.stderr.write(f"undeclared dependency present: {sorted(extra)}\n")
            return 1
    if args.forbid_symbol:
        forbidden = {item.casefold() for item in args.forbid_symbol}
        locate = subprocess.run(
            [
                args.python,
                "-I",
                "-c",
                "import importlib.metadata, json, sys;"
                "dist=importlib.metadata.distribution(sys.argv[1]);"
                "print(json.dumps([str(dist.locate_file(item)) "
                "for item in (dist.files or []) if str(item).endswith('.py')]))",
                args.distribution,
            ],
            check=False,
            text=True,
            capture_output=True,
        )
        if locate.returncode != 0:
            sys.stderr.write(locate.stderr)
            return locate.returncode or 1
        hits: set[str] = set()
        for path in json.loads(locate.stdout):
            try:
                source = Path(path).read_text(encoding="utf-8")
            except OSError:
                continue
            hits.update(_scan_symbols(source, forbidden))
        if hits:
            sys.stderr.write(f"forbidden symbol present: {sorted(hits)}\n")
            return 1
    for namespace in forbidden_ns:
        leaked = subprocess.run(
            [args.python, "-I", "-c", f"import {namespace}"],
            check=False,
            text=True,
            capture_output=True,
        )
        if leaked.returncode == 0:
            sys.stderr.write(f"forbidden namespace importable: {namespace}\n")
            return 1
    print(f"installed boundary passed: {args.distribution}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
