"""Release wheels must identify a clean, exact source tree."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tools.conformance.runner import ConformanceError, require_clean_exact_head


def test_source_guard_rejects_wrong_head_and_untracked_changes(tmp_path: Path) -> None:
    def git(*args: str) -> str:
        return subprocess.check_output(["git", "-C", str(tmp_path), *args], text=True).strip()

    git("init", "-q")
    git("-c", "user.name=Liqvera Test", "-c", "user.email=test@example.invalid",
        "commit", "--allow-empty", "-qm", "fixture")
    head = git("rev-parse", "HEAD")
    require_clean_exact_head(head, tmp_path)
    with pytest.raises(ConformanceError, match="does not match"):
        require_clean_exact_head("0" * 40, tmp_path)
    (tmp_path / "untracked.py").write_text("# unpublished code\n")
    with pytest.raises(ConformanceError, match="dirty"):
        require_clean_exact_head(head, tmp_path)


@pytest.mark.parametrize("value", ["", "dirty", "x" * 40, "f" * 39])
def test_source_guard_rejects_non_sha(value: str, tmp_path: Path) -> None:
    with pytest.raises(ConformanceError, match="hex SHA"):
        require_clean_exact_head(value, tmp_path)
