"""Strict integration checks for the initialized Adaptive Grok tooling link."""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "tooling/adaptive-grok-build-pro"
COMMIT = "cb9af4073ba6c3d515145164d771c75ebdfa3224"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _copy_owned_tooling(destination: Path) -> None:
    tooling = destination / "tooling"
    tooling.mkdir(parents=True)
    for name in (
        "adaptive_grok_pin.py",
        "grok-verify.py",
        "run-adaptive-grok.py",
        "tooling-lock.json",
    ):
        source = ROOT / "tooling" / name
        if source.exists():
            shutil.copy2(source, tooling / name)


def _pinned_fixture(tmp_path: Path) -> Path:
    root = tmp_path / "consumer"
    root.mkdir()
    _copy_owned_tooling(root)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(
        [
            "git",
            "update-index",
            "--add",
            "--cacheinfo",
            f"160000,{COMMIT},tooling/adaptive-grok-build-pro",
        ],
        cwd=root,
        check=True,
    )
    subprocess.run(
        ["git", "clone", "-q", "--shared", str(SOURCE), "adaptive-grok-build-pro"],
        cwd=root / "tooling",
        check=True,
    )
    subprocess.run(
        ["git", "checkout", "-q", COMMIT],
        cwd=root / "tooling/adaptive-grok-build-pro",
        check=True,
    )
    return root


def _hook_command(event: str) -> str:
    hooks = json.loads((ROOT / ".grok/hooks.json").read_text())["hooks"][event]
    return hooks[0]["hooks"][0]["command"]


def _run_hook(root: Path, event: str = "PreToolUse") -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        _hook_command(event),
        cwd=root,
        shell=True,
        input="{}",
        text=True,
        capture_output=True,
        check=False,
    )


def _run_direct_verify(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "tooling/grok-verify.py", "--help"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )


def test_initialized_submodule_matches_the_locked_runtime() -> None:
    launcher = _load(ROOT / "tooling/run-adaptive-grok.py", "strict_launcher")
    assert launcher.validate(ROOT) == SOURCE
    assert "pytest-xdist" in (
        SOURCE / ".grok-stack/adaptive_grok/python_test_runner.py"
    ).read_text()
    completed = _run_direct_verify(ROOT)
    assert completed.returncode == 0, completed.stderr
    assert "route-selected verification" in completed.stdout
    override = _load(ROOT / "tooling/grok-verify.py", "strict_runtime")
    requested = override.python_test_runner.selected_workers(ROOT)
    if os.environ.get("_GROK_TEST_CHILD") == "1":
        assert requested == 0
    else:
        assert requested is not None and requested > 1
        effective, engine = override.python_test_runner.select_engine(
            requested, measured=True
        )
        assert effective == requested
        assert engine == "pytest-xdist"


@pytest.mark.parametrize("event", ["PreToolUse", "Stop"])
def test_safety_hooks_reject_a_missing_submodule(tmp_path: Path, event: str) -> None:
    root = tmp_path / "missing"
    _copy_owned_tooling(root)

    completed = _run_hook(root, event)

    assert completed.returncode != 0
    assert '"decision":"allow"' not in completed.stdout
    assert "Adaptive Grok pin validation failed" in completed.stderr


def test_safety_hook_rejects_a_wrong_lock(tmp_path: Path) -> None:
    root = tmp_path / "wrong-lock"
    _copy_owned_tooling(root)
    lock_path = root / "tooling/tooling-lock.json"
    lock = json.loads(lock_path.read_text())
    lock["adaptive_grok_build_pro"]["version"] = "2.0.18"
    lock_path.write_text(json.dumps(lock))

    completed = _run_hook(root)

    assert completed.returncode != 0
    assert '"decision":"allow"' not in completed.stdout
    assert "lock does not match" in completed.stderr


@pytest.mark.parametrize("state", ["wrong-head", "dirty"])
def test_safety_hook_rejects_an_untrusted_checkout(
    tmp_path: Path, state: str
) -> None:
    root = _pinned_fixture(tmp_path)
    if state == "wrong-head":
        subprocess.run(
            ["git", "checkout", "-q", f"{COMMIT}^"],
            cwd=root / "tooling/adaptive-grok-build-pro",
            check=True,
        )
    else:
        (root / "tooling/adaptive-grok-build-pro/untracked-marker").write_text("dirty")

    completed = _run_hook(root)

    assert completed.returncode != 0
    assert '"decision":"allow"' not in completed.stdout
    expected = "locked commit" if state == "wrong-head" else "checkout is modified"
    assert expected in completed.stderr


@pytest.mark.parametrize("state", ["missing", "wrong-lock", "wrong-head", "dirty"])
def test_direct_verifier_rejects_untrusted_tooling_before_import(
    tmp_path: Path, state: str
) -> None:
    if state in {"wrong-head", "dirty"}:
        root = _pinned_fixture(tmp_path)
    else:
        root = tmp_path / state
        _copy_owned_tooling(root)

    if state == "wrong-lock":
        lock_path = root / "tooling/tooling-lock.json"
        lock = json.loads(lock_path.read_text())
        lock["adaptive_grok_build_pro"]["tag"] = "v2.0.18"
        lock_path.write_text(json.dumps(lock))
    elif state == "wrong-head":
        subprocess.run(
            ["git", "checkout", "-q", f"{COMMIT}^"],
            cwd=root / "tooling/adaptive-grok-build-pro",
            check=True,
        )
    elif state == "dirty":
        (root / "tooling/adaptive-grok-build-pro/untracked-marker").write_text("dirty")

    completed = _run_direct_verify(root)

    assert completed.returncode == 2
    assert "Adaptive Grok pin validation failed" in completed.stderr
    assert "Traceback" not in completed.stderr


@pytest.mark.parametrize(
    ("state", "target"),
    [
        ("assume-bytes", "scripts/grok_verify.py"),
        ("skip-bytes", "scripts/grok_verify.py"),
        ("assume-mode", "VERSION"),
    ],
)
def test_direct_verifier_rejects_index_hidden_byte_and_mode_changes(
    tmp_path: Path, state: str, target: str
) -> None:
    root = _pinned_fixture(tmp_path)
    source = root / "tooling/adaptive-grok-build-pro"
    flag = "--skip-worktree" if state == "skip-bytes" else "--assume-unchanged"
    subprocess.run(["git", "update-index", flag, target], cwd=source, check=True)
    if state.endswith("bytes"):
        with (source / target).open("a", encoding="utf-8") as stream:
            stream.write("\n# hidden tamper\n")
    else:
        (source / target).chmod(0o755)
    assert (
        subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=source,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        == ""
    )

    completed = _run_direct_verify(root)

    assert completed.returncode == 2
    assert "Adaptive Grok pin validation failed" in completed.stderr


@pytest.mark.parametrize("state", ["bytes", "mode"])
def test_direct_verifier_compares_worktree_bytes_and_mode_to_head(
    tmp_path: Path, state: str
) -> None:
    root = _pinned_fixture(tmp_path)
    source = root / "tooling/adaptive-grok-build-pro"
    target = source / ("scripts/grok_verify.py" if state == "bytes" else "VERSION")
    if state == "bytes":
        with target.open("a", encoding="utf-8") as stream:
            stream.write("\n# visible tamper\n")
    else:
        subprocess.run(
            ["git", "config", "core.filemode", "false"], cwd=source, check=True
        )
        target.chmod(0o755)

    completed = _run_direct_verify(root)

    assert completed.returncode == 2
    expected = "tracked bytes differ" if state == "bytes" else "tracked mode differs"
    assert f"{expected} from HEAD" in completed.stderr


def test_direct_verifier_rejects_ignored_importable_files(tmp_path: Path) -> None:
    root = _pinned_fixture(tmp_path)
    source = root / "tooling/adaptive-grok-build-pro"
    ignored = source / ".grok-stack/adaptive_grok/__pycache__/hijack.pyc"
    ignored.parent.mkdir()
    ignored.write_bytes(b"not trusted bytecode")
    assert subprocess.run(
        ["git", "check-ignore", "--quiet", str(ignored.relative_to(source))],
        cwd=source,
        check=False,
    ).returncode == 0

    completed = _run_direct_verify(root)

    assert completed.returncode == 2
    assert "Adaptive Grok pin validation failed" in completed.stderr


def test_recurring_trivy_gate_discovers_container_configs_and_threshold(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "repo"
    (root / "services/new").mkdir(parents=True)
    (root / "deploy").mkdir()
    (root / "services/new/Dockerfile.worker").write_text("FROM scratch\n")
    (root / "deploy/compose.yaml").write_text("services: {}\n")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True)

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "trivy-args.jsonl"
    executable = bin_dir / "trivy"
    executable.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, sys\n"
        "with open(os.environ['TRIVY_ARG_LOG'], 'a') as stream:\n"
        "    stream.write(json.dumps(sys.argv[1:]) + '\\n')\n"
    )
    executable.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("TRIVY_ARG_LOG", str(log))

    override = _load(ROOT / "tooling/grok-verify.py", "strict_verify_override")
    result = override._explicit_trivy(root)

    assert result.status == "pass"
    calls = [json.loads(line) for line in log.read_text().splitlines()]
    assert calls == [
        [
            "config",
            "--exit-code",
            "1",
            "--severity",
            "MEDIUM,HIGH,CRITICAL",
            "deploy/compose.yaml",
        ],
        [
            "config",
            "--exit-code",
            "1",
            "--severity",
            "MEDIUM,HIGH,CRITICAL",
            "services/new/Dockerfile.worker",
        ],
    ]
