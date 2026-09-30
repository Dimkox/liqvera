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
        True, template, tmp_path / "install root", tmp_path / "config/systemd/user",
        lambda argv: calls.append(argv) or 0,
    )
    assert unit == tmp_path / "config/systemd/user/liqvera.service"
    assert calls == [
        ("/usr/bin/systemctl", "--user", "daemon-reload"),
        ("/usr/bin/systemctl", "--user", "enable", "--now", "liqvera.service"),
    ]
    assert "/etc/systemd" not in unit.read_text()
    assert "\\x20" in unit.read_text()


def test_user_unit_requires_explicit_option(tmp_path: Path) -> None:
    calls: list[tuple[str, ...]] = []
    with pytest.raises(ORCHESTRATION.OrchestrationError, match="CONFIG_INVALID"):
        ORCHESTRATION.install_user_unit(False, "x", tmp_path / "root", tmp_path, lambda argv: calls.append(argv) or 0)
    assert calls == []
