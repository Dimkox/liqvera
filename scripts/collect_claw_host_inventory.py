#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import stat
import subprocess
import threading
from typing import Any


def duplicate_reject(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("DUPLICATE_KEY")
        result[key] = value
    return result


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run(argv: list[str], *, max_stdout_bytes: int = 16384) -> subprocess.CompletedProcess[str]:
    if max_stdout_bytes < 1 or max_stdout_bytes > 65536:
        raise ValueError("COMMAND_OUTPUT_BOUND")
    process = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    assert process.stdout is not None
    timer = threading.Timer(10.0, process.kill)
    timer.start()
    try:
        raw = process.stdout.read(max_stdout_bytes + 1)
        if len(raw) > max_stdout_bytes:
            process.kill()
            process.wait()
            raise RuntimeError("COMMAND_OUTPUT_TOO_LARGE")
        returncode = process.wait()
    finally:
        timer.cancel()
        process.stdout.close()
    try:
        stdout = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise RuntimeError("COMMAND_OUTPUT_ENCODING") from exc
    return subprocess.CompletedProcess(argv, returncode, stdout=stdout, stderr="")


def _unit_projection(unit: str, expected_working_directory: str) -> dict[str, object]:
    names = ("LoadState", "ActiveState", "SubState", "FragmentPath", "User", "Group", "MainPID", "ExecStart", "WorkingDirectory")
    result = _run(["/usr/bin/systemctl", "show", "--no-pager", *["--property=" + name for name in names], unit])
    if result.returncode:
        raise RuntimeError("UNIT_PROJECTION_FAILED:" + unit)
    values: dict[str, str] = {}
    for line in result.stdout.splitlines():
        key, separator, value = line.partition("=")
        if separator and key in names:
            values[key] = value
    if set(values) != set(names):
        raise RuntimeError("UNIT_PROJECTION_INCOMPLETE:" + unit)
    if not values["Group"] and values["User"]:
        import grp
        import pwd

        values["Group"] = grp.getgrgid(pwd.getpwnam(values["User"]).pw_gid).gr_name
    exec_match = re.fullmatch(r"\{\s*path=([^\s;}]+)\s*;.*\}", values["ExecStart"])
    expected_exec = expected_working_directory.rstrip("/") + "/runsvc.sh"
    if not exec_match or exec_match.group(1) != expected_exec:
        raise RuntimeError("UNIT_EXEC_START_PATH:" + unit)
    return {
        "unit": unit,
        "load_state": values["LoadState"],
        "active_state": values["ActiveState"],
        "sub_state": values["SubState"],
        "fragment_path": values["FragmentPath"],
        "user": values["User"],
        "group": values["Group"],
        "main_pid": int(values["MainPID"]),
        "exec_start_path_sha256": hashlib.sha256(expected_exec.encode()).hexdigest(),
        "working_directory": values["WorkingDirectory"],
    }


def _path_projection(value: str) -> dict[str, object]:
    path = Path(value)
    try:
        before = path.lstat()
        resolved = path.resolve(strict=True)
        after = path.lstat()
    except (FileNotFoundError, OSError):
        return {"path": value, "realpath": "", "kind": "missing", "uid": None, "gid": None, "mode": None, "device": None, "inode": None, "link_count": None}
    stable = (before.st_dev, before.st_ino, before.st_mode, before.st_nlink) == (after.st_dev, after.st_ino, after.st_mode, after.st_nlink)
    kind = "directory" if stat.S_ISDIR(before.st_mode) else "symlink" if stat.S_ISLNK(before.st_mode) else "other"
    if not stable:
        kind = "changed"
    return {"path": value, "realpath": str(resolved), "kind": kind, "uid": before.st_uid, "gid": before.st_gid, "mode": f"{stat.S_IMODE(before.st_mode):04o}", "device": before.st_dev, "inode": before.st_ino, "link_count": before.st_nlink}


def _strict_subids(path: Path, target: str, proposed_start: int, proposed_count: int) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    entries: list[dict[str, object]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        parts = raw.split(":")
        if len(parts) != 3 or not parts[0] or not parts[1].isdigit() or not parts[2].isdigit():
            raise ValueError("SUBID_FORMAT")
        start, count = int(parts[1]), int(parts[2])
        if start <= 0 or count <= 0 or start + count > 2**32:
            raise ValueError("SUBID_RANGE")
        entries.append({"name": parts[0], "start": start, "count": count})
    wanted = [item for item in entries if item["name"] == target]
    end = proposed_start + proposed_count
    overlaps = [item for item in entries if item["name"] != target and max(proposed_start, int(item["start"])) < min(end, int(item["start"]) + int(item["count"]))]
    return wanted, overlaps


def _read_stable_regular(path: Path, *, max_bytes: int, require_root: bool) -> bytes:
    try:
        before = path.lstat()
    except OSError as exc:
        raise RuntimeError("DPKG_STATUS_UNREADABLE") from exc
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or (require_root and before.st_uid != 0) or before.st_size > max_bytes:
        raise RuntimeError("DPKG_STATUS_IDENTITY")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
        try:
            opened = os.fstat(descriptor)
            if (opened.st_dev, opened.st_ino, opened.st_mode, opened.st_nlink, opened.st_size) != (before.st_dev, before.st_ino, before.st_mode, before.st_nlink, before.st_size):
                raise RuntimeError("DPKG_STATUS_CHANGED")
            chunks: list[bytes] = []
            total = 0
            while True:
                chunk = os.read(descriptor, min(65536, max_bytes + 1 - total))
                if not chunk:
                    break
                chunks.append(chunk)
                total += len(chunk)
                if total > max_bytes:
                    raise RuntimeError("DPKG_STATUS_TOO_LARGE")
            after = os.fstat(descriptor)
        finally:
            os.close(descriptor)
    except OSError as exc:
        raise RuntimeError("DPKG_STATUS_UNREADABLE") from exc
    final = path.lstat()
    stable = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns) == (final.st_dev, final.st_ino, final.st_size, final.st_mtime_ns, final.st_ctime_ns)
    if not stable:
        raise RuntimeError("DPKG_STATUS_CHANGED")
    return b"".join(chunks)


def _parse_dpkg_status(raw: bytes) -> dict[str, dict[str, str]]:
    if b"\x00" in raw or b"\r" in raw:
        raise RuntimeError("DPKG_STATUS_FORMAT")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise RuntimeError("DPKG_STATUS_ENCODING") from exc
    paragraphs: list[str] = []
    current: list[str] = []
    for line in text.split("\n"):
        if line == "":
            if current:
                paragraphs.append("\n".join(current))
                current = []
            continue
        current.append(line)
    if current:
        paragraphs.append("\n".join(current))
    if not paragraphs:
        raise RuntimeError("DPKG_STATUS_EMPTY")
    packages: dict[str, dict[str, str]] = {}
    for paragraph in paragraphs:
        if len(paragraph.encode()) > 65536:
            raise RuntimeError("DPKG_STATUS_PARAGRAPH")
        fields: dict[str, str] = {}
        previous = ""
        for line in paragraph.splitlines():
            if line.startswith((" ", "\t")):
                if not previous:
                    raise RuntimeError("DPKG_STATUS_CONTINUATION")
                continue
            key, separator, value = line.partition(":")
            if value.startswith(" "):
                value = value[1:]
            if not separator:
                raise RuntimeError("DPKG_STATUS_DELIMITER")
            if value.startswith(" "):
                raise RuntimeError("DPKG_STATUS_FIELD_PADDING")
            if not re.fullmatch(r"[A-Za-z0-9-]{1,64}", key):
                raise RuntimeError("DPKG_STATUS_FIELD_NAME")
            if key in fields:
                raise RuntimeError("DPKG_STATUS_DUPLICATE_FIELD")
            fields[key] = value
            previous = key
        package = fields.get("Package")
        if package is None:
            raise RuntimeError("DPKG_STATUS_PACKAGE_MISSING")
        if not re.fullmatch(r"[a-z0-9][a-z0-9+.-]{0,127}", package) or package in packages:
            raise RuntimeError("DPKG_STATUS_PACKAGE")
        packages[package] = fields
    return packages


def _package_projection(closure: dict[str, object], status_path: Path = Path("/var/lib/dpkg/status"), *, require_root: bool = True) -> list[dict[str, object]]:
    database = _parse_dpkg_status(_read_stable_regular(status_path, max_bytes=32 * 1024 * 1024, require_root=require_root))
    output: list[dict[str, object]] = []
    for item in closure["packages"]:
        name = item["name"]
        fields = database.get(name)
        if fields is None:
            output.append({"name": name, "status": "absent", "version": None, "architecture": None, "selection": None})
            continue
        status = fields.get("Status", "")
        version = fields.get("Version", "")
        architecture = fields.get("Architecture", "")
        if not re.fullmatch(r"[a-z-]{1,32} [a-z-]{1,32} [a-z-]{1,32}", status) or not re.fullmatch(r"[A-Za-z0-9.+:~_-]{1,128}", version) or not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", architecture):
            raise RuntimeError("DPKG_STATUS_TARGET_FIELDS")
        installed = status == "install ok installed"
        output.append({"name": name, "status": "installed" if installed else "other", "version": version, "architecture": architecture, "selection": "ii " if installed else "?? "})
    return output


def preflight_blockers(facts: dict[str, object]) -> list[str]:
    blockers: set[str] = set()
    subids = facts["subids"]
    if subids["subuid_target"] or subids["subgid_target"]:
        blockers.add("TARGET_SUBID_PRESENT")
    if subids["subuid_overlaps"] or subids["subgid_overlaps"]:
        blockers.add("SUBID_RANGE_OVERLAP")
    if any(item["status"] != "absent" for item in facts["packages"]):
        blockers.add("PACKAGE_BASELINE_PRESENT")
    if facts["podman"]["present"]:
        blockers.add("PODMAN_ALREADY_PRESENT")
    return sorted(blockers)


def _podman_projection() -> dict[str, object]:
    for path in (Path("/usr/bin/podman"), Path("/bin/podman")):
        try:
            metadata = path.lstat()
        except FileNotFoundError:
            continue
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1 or metadata.st_uid != 0:
            raise RuntimeError("PODMAN_PATH_IDENTITY")
        return {"present": True, "version": None}
    return {"present": False, "version": None}


def probe_host(policy: dict[str, object], closure: dict[str, object]) -> dict[str, object]:
    import grp
    import pwd

    os_release = {}
    for line in Path("/etc/os-release").read_text(encoding="utf-8").splitlines():
        key, separator, value = line.partition("=")
        if separator and key in {"ID", "VERSION_ID"}:
            os_release[key] = value.strip().strip('"')
    try:
        user = pwd.getpwnam(str(policy["runner_user"]))
    except KeyError:
        user = None
    try:
        group = grp.getgrnam(str(policy["runner_group"]))
    except KeyError:
        group = None
    try:
        uid_occupant = pwd.getpwuid(int(policy["runner_uid"])).pw_name
    except KeyError:
        uid_occupant = None
    try:
        gid_occupant = grp.getgrgid(int(policy["runner_gid"])).gr_name
    except KeyError:
        gid_occupant = None
    subuid_target, subuid_overlaps = _strict_subids(Path("/etc/subuid"), str(policy["runner_user"]), int(policy["subuid_start"]), int(policy["subid_count"]))
    subgid_target, subgid_overlaps = _strict_subids(Path("/etc/subgid"), str(policy["runner_group"]), int(policy["subgid_start"]), int(policy["subid_count"]))
    return {
        "os": {"id": os_release.get("ID", ""), "version_id": os_release.get("VERSION_ID", ""), "architecture": platform.machine(), "kernel": platform.release()},
        "cgroup_v2": Path("/sys/fs/cgroup/cgroup.controllers").is_file(),
        "engine": _unit_projection(str(policy["engine_service"]), str(policy["runner_tree"])),
        "app": _unit_projection(str(policy["app_service"]), str(policy["app_working_directory"])),
        "paths": [_path_projection(str(policy[key])) for key in ("runner_tree", "runner_home", "app_working_directory")],
        "target_identity": {"user_present": user is not None, "group_present": group is not None, "uid": user.pw_uid if user else None, "gid": group.gr_gid if group else None, "uid_occupant": uid_occupant, "gid_occupant": gid_occupant},
        "subids": {"subuid_target": subuid_target, "subgid_target": subgid_target, "subuid_overlaps": subuid_overlaps, "subgid_overlaps": subgid_overlaps},
        "packages": _package_projection(closure),
        "podman": _podman_projection(),
    }


def build_observation(policy_path: Path, closure_path: Path, facts: dict[str, object], identity: dict[str, object]) -> dict[str, object]:
    policy = json.loads(policy_path.read_bytes(), object_pairs_hook=duplicate_reject)
    value = {"schema_version": "claw-host-inventory-observation-v2", "authority": "NONE", "status": "HOST_INVENTORY_OBSERVED", "not_host_receipt": True, **identity, "policy_sha256": _sha(policy_path), "package_closure_sha256": _sha(closure_path), "oci_archive_sha256": policy["oci_archive_sha256"], **facts, "preflight_blockers": preflight_blockers(facts)}
    value["inventory_payload_sha256"] = hashlib.sha256(canonical_bytes(value)).hexdigest()
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    for name in ("policy", "closure", "output", "repository", "controller-sha", "controller-tree", "collector-path", "collector-sha256", "collection-id", "runner-name"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args(argv)
    policy_path, closure_path = Path(args.policy), Path(args.closure)
    policy = json.loads(policy_path.read_bytes(), object_pairs_hook=duplicate_reject)
    closure = json.loads(closure_path.read_bytes(), object_pairs_hook=duplicate_reject)
    identity = {"repository": args.repository, "controller_sha": args.controller_sha, "controller_tree": args.controller_tree, "collection_mode": "DIRECT_CLAW", "collector_path": args.collector_path, "collector_sha256": args.collector_sha256, "collection_id": args.collection_id, "runner_name": args.runner_name, "observed_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    output = Path(args.output)
    output.write_bytes(canonical_bytes(build_observation(policy_path, closure_path, probe_host(policy, closure), identity)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
