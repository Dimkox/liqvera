#!/usr/bin/env python3
"""Bounded Task 4 orchestration policies; all external effects are injected."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

SAFE_SHADOW_REASONS = frozenset({
    "SIMULATED_SOURCE", "EXTERNAL_GRANT_REQUIRED", "PAYMENT_SERVICE_UNAVAILABLE", "PAY_TO_MISSING",
})


class OrchestrationError(RuntimeError):
    pass


def check_migration_plan(
    expected: list[tuple[str, str]], applied: list[tuple[str, str]],
) -> list[tuple[str, str]]:
    if len({name for name, _ in applied}) != len(applied) or len(applied) > len(expected):
        raise OrchestrationError("MIGRATION_MISMATCH: duplicate or unknown ledger row")
    if applied != expected[:len(applied)]:
        raise OrchestrationError("MIGRATION_MISMATCH: ledger is not an exact checksum prefix")
    return expected[len(applied):]


def wait_healthy(
    observe: Callable[[], dict[str, object]], clock: Callable[[], float],
    sleep: Callable[[float], None], deadline_seconds: float = 120.0,
) -> dict[str, object]:
    started = clock()
    while clock() - started <= deadline_seconds:
        observation = observe()
        reasons = observation.get("reasons")
        if (
            observation.get("containers") == "healthy"
            and observation.get("storage") is True
            and observation.get("integration") is True
            and observation.get("payment") is False
            and isinstance(reasons, list)
            and "SIMULATED_SOURCE" in reasons
            and set(reasons).issubset(SAFE_SHADOW_REASONS)
        ):
            return observation
        sleep(1.0)
    raise OrchestrationError("HEALTH_TIMEOUT: candidate did not reach honest shadow health")


def start_candidate(
    project: str, up: Callable[[str], None], port_available: Callable[[], bool],
    health: Callable[[], dict[str, object]], down: Callable[[str], None],
) -> dict[str, object]:
    if not port_available():
        down(project)
        raise OrchestrationError("PORT_OCCUPIED: edge port lost before candidate start")
    up(project)
    try:
        return health()
    except Exception:
        down(project)
        raise


def detect_service_manager(explicit_systemd: bool, usable_user_manager: Callable[[], bool]) -> str:
    return "systemd-user" if explicit_systemd and usable_user_manager() else "compose"


def _systemd_escape(path: Path) -> str:
    return str(path).replace("%", "%%").replace(" ", "\\x20")


def install_user_unit(
    explicit: bool, template: str, install_root: Path, unit_directory: Path,
    runner: Callable[[tuple[str, ...]], int],
) -> Path:
    if not explicit:
        raise OrchestrationError("CONFIG_INVALID: systemd integration is not authorized")
    unit_directory = unit_directory.resolve(strict=False)
    if not unit_directory.is_absolute() or str(unit_directory).startswith("/etc/"):
        raise OrchestrationError("CONFIG_INVALID: only a user unit directory is allowed")
    unit_directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    unit = unit_directory / "liqvera.service"
    rendered = template.replace("@INSTALL_ROOT@", _systemd_escape(install_root.resolve(strict=False)))
    temporary = unit_directory / ".liqvera.service.tmp"
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, unit)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    commands = (
        ("/usr/bin/systemctl", "--user", "daemon-reload"),
        ("/usr/bin/systemctl", "--user", "enable", "--now", "liqvera.service"),
    )
    for command in commands:
        if runner(command) != 0:
            raise OrchestrationError("CONFIG_INVALID: systemd user operation failed")
    return unit
