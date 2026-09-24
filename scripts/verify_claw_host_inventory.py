#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
from typing import Any

try:
    from scripts.collect_claw_host_inventory import canonical_bytes, duplicate_reject
except ModuleNotFoundError:
    from collect_claw_host_inventory import canonical_bytes, duplicate_reject


FIELDS = {"schema_version", "authority", "status", "not_host_receipt", "repository", "controller_sha", "controller_tree", "collection_mode", "collector_path", "collector_sha256", "collection_id", "runner_name", "observed_at", "policy_sha256", "package_closure_sha256", "oci_archive_sha256", "os", "cgroup_v2", "engine", "app", "paths", "target_identity", "subids", "packages", "podman", "preflight_blockers", "inventory_payload_sha256"}
UNIT_FIELDS = {"unit", "load_state", "active_state", "sub_state", "fragment_path", "user", "group", "main_pid", "exec_start_path_sha256", "working_directory"}
PATH_FIELDS = {"path", "realpath", "kind", "uid", "gid", "mode", "device", "inode", "link_count"}
PACKAGE_FIELDS = {"name", "status", "version", "architecture", "selection"}
SUBID_FIELDS = {"name", "start", "count"}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_closed_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_bytes(), object_pairs_hook=duplicate_reject)
    if not isinstance(value, dict):
        raise ValueError("INVENTORY_OBJECT")
    return value


def _closed(value: object, fields: set[str], error: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(error)
    return value


def _no_secret_fields(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if re.search(r"(?:token|password|secret|credential|authorization|environment)", key, re.I):
                raise ValueError("SECRET_FIELD")
            _no_secret_fields(item)
    elif isinstance(value, list):
        for item in value:
            _no_secret_fields(item)
    elif isinstance(value, str) and re.search(r"(?:authorization:|bearer |token=|password=|secret=|/\.credentials(?:$|/)|/\.runner(?:$|/))", value, re.I):
        raise ValueError("SECRET_VALUE")


def _derive_preflight_blockers(facts: dict[str, object]) -> list[str]:
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


def verify_observation(value: dict[str, Any], policy_path: Path, closure_path: Path, expected: dict[str, object]) -> dict[str, Any]:
    _no_secret_fields(value)
    _closed(value, FIELDS, "INVENTORY_FIELDS")
    if value["schema_version"] != "claw-host-inventory-observation-v2" or value["authority"] != "NONE" or value["status"] != "HOST_INVENTORY_OBSERVED" or value["not_host_receipt"] is not True or value["collection_mode"] != "DIRECT_CLAW":
        raise ValueError("INVENTORY_AUTHORITY")
    for key, item in expected.items():
        if value.get(key) != item:
            raise ValueError("INVENTORY_IDENTITY")
    if not re.fullmatch(r"[0-9a-f]{40}", value["controller_sha"]) or not re.fullmatch(r"[0-9a-f]{40}", value["controller_tree"]) or not re.fullmatch(r"[0-9a-f]{64}", value["collector_sha256"]):
        raise ValueError("INVENTORY_IDENTITY")
    if value["collector_path"] != "scripts/collect_claw_host_inventory.py" or not re.fullmatch(r"[0-9a-f]{32}", value["collection_id"]) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value["observed_at"]):
        raise ValueError("INVENTORY_IDENTITY")
    policy = json.loads(policy_path.read_bytes(), object_pairs_hook=duplicate_reject)
    closure = json.loads(closure_path.read_bytes(), object_pairs_hook=duplicate_reject)
    if value["policy_sha256"] != _sha(policy_path) or value["package_closure_sha256"] != _sha(closure_path) or value["oci_archive_sha256"] != policy["oci_archive_sha256"]:
        raise ValueError("INVENTORY_INPUTS")
    if value["repository"] != policy["repository"] or value["runner_name"] != policy["runner_name"]:
        raise ValueError("INVENTORY_IDENTITY")
    os_value = _closed(value["os"], {"id", "version_id", "architecture", "kernel"}, "OS_PROJECTION")
    if os_value["id"] != policy["os"]["id"] or os_value["version_id"] != policy["os"]["version_id"] or os_value["architecture"] not in {"x86_64", "amd64"} or not os_value["kernel"] or value["cgroup_v2"] is not True:
        raise ValueError("OS_PROJECTION")
    for key, expected_unit, expected_working in (("engine", policy["engine_service"], policy["runner_tree"]), ("app", policy["app_service"], policy["app_working_directory"])):
        unit = _closed(value[key], UNIT_FIELDS, key.upper() + "_PROJECTION")
        expected_exec_digest = hashlib.sha256((str(expected_working).rstrip("/") + "/runsvc.sh").encode()).hexdigest()
        if unit["unit"] != expected_unit or unit["load_state"] != "loaded" or unit["active_state"] != "active" or unit["sub_state"] != "running" or not isinstance(unit["main_pid"], int) or unit["main_pid"] <= 1 or unit["user"] != "pall" or unit["group"] != "pall" or unit["working_directory"] != expected_working or not str(unit["fragment_path"]).startswith("/etc/systemd/system/") or unit["exec_start_path_sha256"] != expected_exec_digest:
            raise ValueError("APP_CANARY" if key == "app" else "ENGINE_PROJECTION")
    expected_paths = [policy["runner_tree"], policy["runner_home"], policy["app_working_directory"]]
    if not isinstance(value["paths"], list) or [item.get("path") for item in value["paths"] if isinstance(item, dict)] != expected_paths:
        raise ValueError("PATH_PROJECTION")
    for index, item in enumerate(value["paths"]):
        projection = _closed(item, PATH_FIELDS, "PATH_PROJECTION")
        if index == 1:
            expected_missing = {"path": policy["runner_home"], "realpath": "", "kind": "missing", "uid": None, "gid": None, "mode": None, "device": None, "inode": None, "link_count": None}
            if projection != expected_missing:
                raise ValueError("PATH_PROJECTION")
            continue
        if projection["realpath"] != projection["path"] or projection["kind"] != "directory" or not isinstance(projection["uid"], int) or not isinstance(projection["gid"], int) or not re.fullmatch(r"0[0-7]{3}", projection["mode"] or "") or not all(isinstance(projection[name], int) and projection[name] > 0 for name in ("device", "inode", "link_count")):
            raise ValueError("PATH_PROJECTION")
    identity = _closed(value["target_identity"], {"user_present", "group_present", "uid", "gid", "uid_occupant", "gid_occupant"}, "TARGET_IDENTITY")
    if identity != {"user_present": False, "group_present": False, "uid": None, "gid": None, "uid_occupant": None, "gid_occupant": None}:
        raise ValueError("TARGET_IDENTITY")
    subids = _closed(value["subids"], {"subuid_target", "subgid_target", "subuid_overlaps", "subgid_overlaps"}, "SUBID_PROJECTION")
    for name in subids:
        if not isinstance(subids[name], list) or len(subids[name]) > 128:
            raise ValueError("SUBID_PROJECTION")
        for item in subids[name]:
            if not isinstance(item, dict) or set(item) != SUBID_FIELDS or not isinstance(item["name"], str) or not item["name"] or len(item["name"]) > 128 or not isinstance(item["start"], int) or isinstance(item["start"], bool) or not isinstance(item["count"], int) or isinstance(item["count"], bool) or item["start"] <= 0 or item["count"] <= 0 or item["start"] + item["count"] > 2**32:
                raise ValueError("SUBID_PROJECTION")
    expected_packages = [item["name"] for item in closure["packages"]]
    if not isinstance(value["packages"], list) or [item.get("name") for item in value["packages"] if isinstance(item, dict)] != expected_packages:
        raise ValueError("PACKAGE_BASELINE")
    for item in value["packages"]:
        package = _closed(item, PACKAGE_FIELDS, "PACKAGE_BASELINE")
        if package["status"] == "absent":
            if any(package[name] is not None for name in ("version", "architecture", "selection")):
                raise ValueError("PACKAGE_BASELINE")
        elif package["status"] in {"installed", "other"}:
            if not isinstance(package["version"], str) or not re.fullmatch(r"[A-Za-z0-9.+:~_-]{1,128}", package["version"]):
                raise ValueError("PACKAGE_BASELINE")
            if not isinstance(package["architecture"], str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", package["architecture"]):
                raise ValueError("PACKAGE_BASELINE")
            if not isinstance(package["selection"], str) or not re.fullmatch(r"[A-Za-z?+ -]{3,4}", package["selection"]):
                raise ValueError("PACKAGE_BASELINE")
        else:
            raise ValueError("PACKAGE_BASELINE")
    podman = _closed(value["podman"], {"present", "version"}, "PODMAN_BASELINE")
    if not isinstance(podman["present"], bool) or podman["version"] is not None:
        raise ValueError("PODMAN_BASELINE")
    facts = {key: value[key] for key in ("subids", "packages", "podman")}
    blockers = value["preflight_blockers"]
    if not isinstance(blockers, list) or blockers != _derive_preflight_blockers(facts):
        raise ValueError("PREFLIGHT_BLOCKERS")
    unsigned = {key: item for key, item in value.items() if key != "inventory_payload_sha256"}
    if value["inventory_payload_sha256"] != hashlib.sha256(canonical_bytes(unsigned)).hexdigest():
        raise ValueError("INVENTORY_DIGEST")
    return value


def emit_log_envelope(observation_path: Path, policy_path: Path, closure_path: Path, expected: dict[str, object]) -> tuple[str, str]:
    raw = observation_path.read_bytes()
    value = json.loads(raw, object_pairs_hook=duplicate_reject)
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise ValueError("INVENTORY_ENCODING")
    verify_observation(value, policy_path, closure_path, expected)
    return (
        "HOST_INVENTORY_OBSERVATION_SHA256=" + hashlib.sha256(raw).hexdigest(),
        "HOST_INVENTORY_OBSERVATION_B64=" + base64.b64encode(raw).decode("ascii"),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    for name in ("observation", "policy", "closure", "repository", "controller-sha", "controller-tree", "collector-path", "collector-sha256", "collection-id", "runner-name"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--emit-log-envelope", action="store_true")
    args = parser.parse_args(argv)
    expected = {"repository": args.repository, "controller_sha": args.controller_sha, "controller_tree": args.controller_tree, "collection_mode": "DIRECT_CLAW", "collector_path": args.collector_path, "collector_sha256": args.collector_sha256, "collection_id": args.collection_id, "runner_name": args.runner_name}
    if args.emit_log_envelope:
        for line in emit_log_envelope(Path(args.observation), Path(args.policy), Path(args.closure), expected):
            print(line, flush=True)
    else:
        verify_observation(load_closed_json(Path(args.observation)), Path(args.policy), Path(args.closure), expected)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
