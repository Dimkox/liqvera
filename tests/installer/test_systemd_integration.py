from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "installer/lib/orchestration.py"
SPEC = importlib.util.spec_from_file_location("installer_systemd", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
ORCHESTRATION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ORCHESTRATION)


def test_systemd_is_opt_in_and_falls_back_to_compose() -> None:
    assert ORCHESTRATION.detect_service_manager(False, lambda: True) == "compose"
    assert ORCHESTRATION.detect_service_manager(True, lambda: False) == "compose"
    assert ORCHESTRATION.detect_service_manager(True, lambda: True) == "systemd-user"


def test_user_unit_uses_only_systemctl_user_and_private_user_path(tmp_path: Path) -> None:
    template = (ROOT / "installer/systemd/liqvera.service.in").read_text()
    calls: list[tuple[str, ...]] = []
    unit = ORCHESTRATION.install_user_unit(
        True, template, tmp_path / "install % root", tmp_path / ".config/systemd/user", tmp_path,
        lambda argv: calls.append(argv) or 0,
    )
    assert unit == tmp_path / ".config/systemd/user/liqvera.service"
    assert calls == [
        ("/usr/bin/systemctl", "--user", "daemon-reload"),
        ("/usr/bin/systemctl", "--user", "enable", "--now", "liqvera.service"),
    ]
    assert "/etc/systemd" not in unit.read_text()
    assert "\\x20" in unit.read_text()
    assert "%%" in unit.read_text()


def test_user_unit_requires_explicit_option(tmp_path: Path) -> None:
    calls: list[tuple[str, ...]] = []
    with pytest.raises(ORCHESTRATION.OrchestrationError, match="CONFIG_INVALID"):
        ORCHESTRATION.install_user_unit(False, "x", tmp_path / "root", tmp_path, tmp_path,
                                        lambda argv: calls.append(argv) or 0)
    assert calls == []


@pytest.mark.parametrize("hostile", ["/etc/systemd/user", "/usr/lib/systemd/user", "/run/systemd/user"])
def test_user_unit_rejects_every_system_unit_root(tmp_path: Path, hostile: str) -> None:
    calls: list[tuple[str, ...]] = []
    with pytest.raises(ORCHESTRATION.OrchestrationError, match="CONFIG_INVALID"):
        ORCHESTRATION.install_user_unit(True, "x", tmp_path / "root", Path(hostile), tmp_path,
                                        lambda argv: calls.append(argv) or 0)
    assert calls == []


@pytest.mark.parametrize("suffix", ["\nX", "\\X", '"X', "$X", "\x7fX"])
def test_user_unit_rejects_unsafe_install_root(tmp_path: Path, suffix: str) -> None:
    with pytest.raises(ORCHESTRATION.OrchestrationError, match="CONFIG_INVALID"):
        ORCHESTRATION.install_user_unit(True, "@INSTALL_ROOT@", Path(str(tmp_path / "root") + suffix),
                                        tmp_path / ".config/systemd/user", tmp_path, lambda _: 0)


@pytest.mark.parametrize("failing_call", [1, 2])
def test_user_manager_failure_restores_prior_unit_and_returns_compose_fallback(
    tmp_path: Path, failing_call: int,
) -> None:
    unit_dir = tmp_path / ".config/systemd/user"
    unit_dir.mkdir(parents=True)
    (tmp_path / ".config").chmod(0o700)
    (tmp_path / ".config/systemd").chmod(0o700)
    unit_dir.chmod(0o700)
    unit = unit_dir / "liqvera.service"
    unit.write_text("prior")
    calls = 0

    def runner(_: tuple[str, ...]) -> int:
        nonlocal calls
        calls += 1
        return 1 if calls == failing_call else 0

    assert ORCHESTRATION.install_user_unit(True, "@INSTALL_ROOT@", tmp_path / "root", unit_dir,
                                            tmp_path, runner) is None
    assert unit.read_text() == "prior"


def test_user_unit_rejects_symlinked_or_writable_user_unit_ancestors(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (tmp_path / ".config").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ORCHESTRATION.OrchestrationError, match="CONFIG_INVALID"):
        ORCHESTRATION.install_user_unit(True, "@INSTALL_ROOT@", tmp_path / "root",
                                        tmp_path / ".config/systemd/user", tmp_path, lambda _: 0)

    (tmp_path / ".config").unlink()
    unit_dir = tmp_path / ".config/systemd/user"
    unit_dir.mkdir(parents=True)
    unit_dir.chmod(0o777)
    with pytest.raises(ORCHESTRATION.OrchestrationError, match="CONFIG_INVALID"):
        ORCHESTRATION.install_user_unit(True, "@INSTALL_ROOT@", tmp_path / "root", unit_dir,
                                        tmp_path, lambda _: 0)


def test_user_manager_exception_removes_invocation_owned_unit(tmp_path: Path) -> None:
    def fail(_: tuple[str, ...]) -> int:
        raise OSError("manager unavailable")

    assert ORCHESTRATION.install_user_unit(
        True, "@INSTALL_ROOT@", tmp_path / "root", tmp_path / ".config/systemd/user",
        tmp_path, fail,
    ) is None
    assert not (tmp_path / ".config/systemd/user/liqvera.service").exists()


def test_user_manager_rollback_never_follows_preexisting_temp_symlink(tmp_path: Path) -> None:
    unit_dir = tmp_path / ".config/systemd/user"
    unit_dir.mkdir(parents=True)
    (tmp_path / ".config").chmod(0o700)
    (tmp_path / ".config/systemd").chmod(0o700)
    unit_dir.chmod(0o700)
    unit = unit_dir / "liqvera.service"
    unit.write_text("prior")
    outside = tmp_path / "outside"
    outside.write_text("sentinel")
    (unit_dir / ".liqvera.service.rollback").symlink_to(outside)

    assert ORCHESTRATION.install_user_unit(
        True, "@INSTALL_ROOT@", tmp_path / "root", unit_dir, tmp_path, lambda _: 1,
    ) is None
    assert outside.read_text() == "sentinel"
    assert unit.read_text() == "prior"
