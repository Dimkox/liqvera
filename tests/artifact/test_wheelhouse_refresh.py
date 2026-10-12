"""A branch switch must not reintroduce unaudited dependency wheels."""
from __future__ import annotations

import hashlib
from pathlib import Path

from tools.conformance.distributions import build_all

ROOT = Path(__file__).resolve().parents[2]


def test_rebuild_removes_stale_wheel_candidates(tmp_path: Path) -> None:
    stale = tmp_path / "certifi-9999.0-py3-none-any.whl"
    stale.write_bytes(b"untrusted previous build")
    note = tmp_path / "operator-note.txt"
    note.write_text("Keep non-wheel files")

    built = build_all("worktree", tmp_path, root=ROOT, require_clean=False)

    assert not stale.exists()
    assert note.read_text() == "Keep non-wheel files"
    assert len(built) == 3
    for item in built:
        assert item.path.parent == tmp_path
        assert item.path.is_file()
        assert hashlib.sha256(item.path.read_bytes()).hexdigest() == item.sha256
