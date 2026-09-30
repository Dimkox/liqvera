#!/usr/bin/env python3
"""Bounded Task 4 orchestration policies; all external effects are injected."""

from __future__ import annotations

import os
import stat
from contextlib import suppress
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
    observe: Callable[[float], dict[str, object]], clock: Callable[[], float],
    sleep: Callable[[float], None], deadline_seconds: float = 120.0,
) -> dict[str, object]:
    started = previous = clock()
    while True:
        current = clock()
        if current < previous:
            raise OrchestrationError("HEALTH_CLOCK_INVALID: monotonic clock moved backwards")
        previous = current
        if current - started > deadline_seconds:
            break
        observation = observe(max(0.0, deadline_seconds - (current - started)))
        after_observe = clock()
        if after_observe < current:
            raise OrchestrationError("HEALTH_CLOCK_INVALID: monotonic clock moved backwards")
        previous = after_observe
        if after_observe - started > deadline_seconds:
            raise OrchestrationError("HEALTH_TIMEOUT: observation exceeded health deadline")
        reasons = observation.get("reasons")
        if (
            observation.get("containers") == "healthy"
            and observation.get("storage") is True
            and observation.get("integration") is True
            and observation.get("payment") is False
            and isinstance(reasons, list)
            and all(isinstance(reason, str) for reason in reasons)
            and len(reasons) == len(set(reasons))
            and "SIMULATED_SOURCE" in reasons
            and "EXTERNAL_GRANT_REQUIRED" in reasons
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
    try:
        up(project)
        return health()
    except Exception:
        with suppress(Exception):
            down(project)
        raise


def detect_service_manager(explicit_systemd: bool, usable_user_manager: Callable[[], bool]) -> str:
    return "systemd-user" if explicit_systemd and usable_user_manager() else "compose"


def _systemd_escape(path: Path) -> str:
    value = str(path)
    if any(ord(char) < 32 or ord(char) == 127 for char in value) or any(
        char in value for char in ('\\', '"', "'", "$", "`")
    ):
        raise OrchestrationError("CONFIG_INVALID: unsafe systemd path")
    return value.replace("%", "%%").replace(" ", "\\x20")


def install_user_unit(
    explicit: bool, template: str, install_root: Path, unit_directory: Path,
    user_home: Path, runner: Callable[[tuple[str, ...]], int],
) -> Path | None:
    if not explicit:
        raise OrchestrationError("CONFIG_INVALID: systemd integration is not authorized")
    if not install_root.is_absolute():
        raise OrchestrationError("CONFIG_INVALID: install root must be absolute")
    unit_directory = unit_directory.resolve(strict=False)
    expected_directory = user_home.resolve(strict=True) / ".config/systemd/user"
    if unit_directory != expected_directory:
        raise OrchestrationError("CONFIG_INVALID: only a user unit directory is allowed")
    escaped_root = _systemd_escape(install_root.resolve(strict=False))
    parent = user_home.resolve(strict=True)
    for component in (".config", "systemd", "user"):
        parent /= component
        if parent.exists() or parent.is_symlink():
            metadata = parent.lstat()
            if (not stat.S_ISDIR(metadata.st_mode) or metadata.st_uid != os.getuid()
                    or metadata.st_mode & 0o022):
                raise OrchestrationError("CONFIG_INVALID: unsafe user unit ancestor")
        else:
            parent.mkdir(mode=0o700)
    if stat.S_IMODE(unit_directory.stat().st_mode) != 0o700:
        raise OrchestrationError("CONFIG_INVALID: user unit directory must be private")
    unit = unit_directory / "liqvera.service"
    prior: bytes | None = None
    if unit.exists() or unit.is_symlink():
        metadata = unit.lstat()
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1 or metadata.st_uid != os.getuid():
            raise OrchestrationError("CONFIG_INVALID: unsafe existing user unit")
        prior = unit.read_bytes()
    rendered = template.replace("@INSTALL_ROOT@", escaped_root)
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
        try:
            succeeded = runner(command) == 0
        except Exception:
            succeeded = False
        if not succeeded:
            rollback = unit_directory / ".liqvera.service.rollback"
            if prior is None:
                unit.unlink(missing_ok=True)
            else:
                rollback.write_bytes(prior)
                os.chmod(rollback, 0o600)
                os.replace(rollback, unit)
            try:
                runner(("/usr/bin/systemctl", "--user", "daemon-reload"))
            except Exception:
                return None
            return None
    return unit
