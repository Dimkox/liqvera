"""Task 6: both legacy namespace owners are gone."""

from __future__ import annotations

import subprocess


def test_legacy_namespace_is_absent_from_git() -> None:
    tracked = subprocess.check_output(["git", "ls-files"], text=True).splitlines()
    assert not any(
        path.startswith(("multi_exchange_engine/", "src/multi_exchange_engine/"))
        for path in tracked
    )


def test_legacy_import_fails() -> None:
    result = subprocess.run(
        [
            "python3",
            "-I",
            "-c",
            "import importlib; importlib.import_module('multi_exchange_engine')",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode != 0
    assert "ModuleNotFoundError" in result.stderr
