#!/usr/bin/python3.14
"""Root-side framed controller backed by the durable host journal and receipts."""
from __future__ import annotations

import hashlib
import io
import json
import os
import datetime as dt
import re
import secrets
import shutil
import socket
import stat
import struct
import subprocess
import sys
import tarfile
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Callable

try:
    from scripts.claw_host_deployment_contract import (
        ContractError, DeploymentRequest, canonical_bytes, load_closed_bytes,
        verify_approval, verify_legacy_recovery_approval, verify_request, verify_rollback_receipt,
    )
except ModuleNotFoundError:
    sys.path.insert(0, "/usr/local/libexec/mee-claw-host-deploy-lib")
    from claw_host_deployment_contract import (  # type: ignore[no-redef]
        ContractError, DeploymentRequest, canonical_bytes, load_closed_bytes,
        verify_approval, verify_legacy_recovery_approval, verify_request, verify_rollback_receipt,
    )


HEADER = struct.Struct("!I")
MAX_REQUEST = 32768
MAX_RESPONSE = 8192
RESPONSE_FIELDS = {
    "schema_version", "authority", "action", "transaction_id", "state",
    "receipt_sha256",
}
RESPONSE_STATES = {
    "D0_VERIFIED", "BEGIN_ACCEPTED", "HOST_APPLIED_PENDING_FINALIZE",
    "APPLYING", "VERIFYING", "FINALIZING", "COMMITTED", "ROLLING_BACK",
    "ROLLED_BACK", "ROLLBACK_BLOCKED",
}


class ControllerError(RuntimeError):
    pass


class AcquisitionError(ControllerError):
    pass


ASSET_NAME = re.compile(r"^[A-Za-z0-9_.:+-]{1,180}$")
ASSET_ROLE = re.compile(r"^(bundle_manifest|host_inventory|oci_archive|oci_layout|oci_receipt|oci_sidecar|deb:[a-z0-9][a-z0-9+.-]{0,127})$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
TRANSACTION_ID = re.compile(r"^[0-9a-f]{32}$")
MAX_ASSET_BYTES = 536_870_912
MAX_BUNDLE_BYTES = 1_073_741_824
STAGED_ASSET_FIELDS = {"id", "name", "role", "size", "sha256", "staged_name"}
PERSISTED_STAGED_FIELDS = {
    "schema_version", "authority", "transaction_id", "assets",
    "bundle_manifest_sha256", "controller_sha", "controller_tree",
    "policy_sha256", "closure_sha256", "approval_body_sha256",
    "host_inventory_sha256", "rollback_deadline_seconds",
    "approval_comment_id", "release_id",
}
BEGIN_INTENT_FIELDS = {
    "schema_version", "transaction_id", "approval_comment_id", "release_id",
    "approval_body_sha256", "nonce_sha256", "staged_manifest_sha256",
    "controller_sha", "controller_tree", "rollback_deadline_seconds",
}
HOST_APPLY_INTENT_FIELDS = {
    "schema_version", "transaction_id", "begin_intent_sha256",
}
LEGACY_RECOVERY_AUTHORIZATION_FIELDS = {
    "schema_version", "authority", "not_host_receipt", "status", "repository",
    "transaction_id", "begin_intent_sha256", "staged_manifest_sha256",
    "nonce_record_sha256", "terminal_journal_sha256", "credential_binding_sha256",
    "old_controller_sha", "old_controller_tree", "reason", "recovery_controller_sha",
    "recovery_controller_tree", "recovery_install_manifest_sha256",
    "approval_comment_id", "approval_body_sha256", "approval_owner_login", "approval_owner_id",
}
LEGACY_RECOVERY_RECEIPT_FIELDS = {
    "schema_version", "authority", "not_host_receipt", "status", "transaction_id",
    "authorization_sha256", "journal_sha256", "credential_binding_sha256",
    "rollback_intent_sha256", "rollback_receipt_sha256", "recovery_controller_sha",
    "recovery_controller_tree", "created_at",
}


def _read_exact(stream: io.BufferedIOBase, size: int) -> bytes:
    chunks: list[bytes] = []
    remaining = size
    while remaining:
        chunk = stream.read(remaining)
        if not chunk:
            raise ControllerError("FRAME_TRUNCATED")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def read_frame(stream: io.BufferedIOBase, *, limit: int = MAX_REQUEST, reject_trailing: bool = False) -> bytes:
    header = stream.read(HEADER.size)
    if len(header) != HEADER.size:
        raise ControllerError("FRAME_HEADER")
    size = HEADER.unpack(header)[0]
    if size < 2 or size > limit:
        raise ControllerError("FRAME_SIZE")
    payload = _read_exact(stream, size)
    if reject_trailing and stream.read(1):
        raise ControllerError("FRAME_TRAILING")
    return payload


def encode_frame(payload: bytes, *, limit: int = MAX_REQUEST) -> bytes:
    if not isinstance(payload, bytes) or len(payload) < 2 or len(payload) > limit:
        raise ControllerError("FRAME_SIZE")
    return HEADER.pack(len(payload)) + payload


def _atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        view = memoryview(data)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise OSError("SHORT_WRITE")
            view = view[written:]
        os.fsync(fd)
        os.close(fd)
        fd = -1
        os.replace(temporary, path)
        if os.name == "posix":
            parent = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(parent)
            finally:
                os.close(parent)
    except BaseException:
        if fd >= 0:
            os.close(fd)
        Path(temporary).unlink(missing_ok=True)
        raise


def _exclusive(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
    owned = True
    try:
        view = memoryview(data)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise ControllerError("EXCLUSIVE_WRITE")
            view = view[written:]
        os.fsync(fd)
        os.close(fd)
        fd = -1
        if os.name == "posix":
            parent = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(parent)
            finally:
                os.close(parent)
        owned = False
    finally:
        if fd >= 0:
            os.close(fd)
        if owned:
            try:
                path.unlink()
            except FileNotFoundError:
                pass
            else:
                if os.name == "posix":
                    parent = os.open(path.parent, os.O_RDONLY)
                    try:
                        os.fsync(parent)
                    finally:
                        os.close(parent)


def _read_private_state(path: Path, *, max_bytes: int, error: str) -> bytes:
    try:
        before = path.lstat()
    except OSError:
        raise ControllerError(error) from None
    if path.is_symlink() or not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        raise ControllerError(error)
    if os.name == "posix" and (
        before.st_uid != os.geteuid() or before.st_gid != os.getegid()
        or stat.S_IMODE(before.st_mode) != 0o600
    ):
        raise ControllerError(error)
    identity = lambda value: (
        value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns,
        value.st_ctime_ns, value.st_uid, value.st_gid,
        stat.S_IMODE(value.st_mode), value.st_nlink,
    )
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    except OSError:
        raise ControllerError(error) from None
    try:
        opened = os.fstat(fd)
        if identity(opened) != identity(before):
            raise ControllerError(error)
        chunks: list[bytes] = []
        remaining = max_bytes + 1
        while remaining:
            chunk = os.read(fd, min(65_536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        after = os.fstat(fd)
        if identity(after) != identity(opened):
            raise ControllerError(error)
    finally:
        os.close(fd)
    raw = b"".join(chunks)
    if len(raw) > max_bytes:
        raise ControllerError(error)
    return raw


def _state_path_present(path: Path, *, error: str) -> bool:
    try:
        path.lstat()
    except FileNotFoundError:
        return False
    except OSError:
        raise ControllerError(error) from None
    return True


def _require_private_directory(path: Path, *, error: str) -> None:
    try:
        info = path.lstat()
    except OSError:
        raise ControllerError(error) from None
    if path.is_symlink() or not stat.S_ISDIR(info.st_mode):
        raise ControllerError(error)
    if os.name == "posix" and (info.st_uid != os.geteuid() or info.st_gid != os.getegid() or stat.S_IMODE(info.st_mode) != 0o700):
        raise ControllerError(error)


def _validate_asset_set(assets: object) -> list[dict[str, object]]:
    if not isinstance(assets, list) or len(assets) != 16:
        raise AcquisitionError("ASSET_SET")
    checked: list[dict[str, object]] = []
    for item in assets:
        if not isinstance(item, dict) or set(item) != {"id", "name", "role", "size", "sha256"}:
            raise AcquisitionError("ASSET_SET")
        if not isinstance(item["id"], int) or isinstance(item["id"], bool) or item["id"] <= 0:
            raise AcquisitionError("ASSET_SET")
        if not isinstance(item["name"], str) or not ASSET_NAME.fullmatch(item["name"]):
            raise AcquisitionError("ASSET_SET")
        if not isinstance(item["role"], str) or not ASSET_ROLE.fullmatch(item["role"]):
            raise AcquisitionError("ASSET_SET")
        if not isinstance(item["size"], int) or isinstance(item["size"], bool) or not 1 <= item["size"] <= MAX_ASSET_BYTES:
            raise AcquisitionError("ASSET_SET")
        if not isinstance(item["sha256"], str) or not SHA256.fullmatch(item["sha256"]):
            raise AcquisitionError("ASSET_SET")
        checked.append(dict(item))
    order = [(item["role"], item["name"], item["id"]) for item in checked]
    if order != sorted(order):
        raise AcquisitionError("ASSET_SET")
    if len({item["id"] for item in checked}) != 16 or len({item["name"] for item in checked}) != 16 or len({item["role"] for item in checked}) != 16:
        raise AcquisitionError("ASSET_SET")
    roles = [str(item["role"]) for item in checked]
    if sum(role.startswith("deb:") for role in roles) != 10 or set(role for role in roles if not role.startswith("deb:")) != {
        "bundle_manifest", "host_inventory", "oci_archive", "oci_layout", "oci_receipt", "oci_sidecar",
    }:
        raise AcquisitionError("ASSET_SET")
    if sum(int(item["size"]) for item in checked) > MAX_BUNDLE_BYTES:
        raise AcquisitionError("ASSET_SET")
    return checked


def _write_streamed_asset(client: object, item: dict[str, object], target: Path) -> None:
    temporary = target.with_name("." + target.name + ".part")
    fd = -1
    total = 0
    digest = hashlib.sha256()
    try:
        fd = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        try:
            chunks = client.iter_asset(int(item["id"]))
            for chunk in chunks:
                if not isinstance(chunk, bytes) or not chunk:
                    raise AcquisitionError("ASSET_STREAM")
                total += len(chunk)
                if total > int(item["size"]):
                    raise AcquisitionError("ASSET_SIZE")
                digest.update(chunk)
                view = memoryview(chunk)
                while view:
                    written = os.write(fd, view)
                    if written <= 0:
                        raise AcquisitionError("ASSET_STREAM")
                    view = view[written:]
        except AcquisitionError:
            raise
        except BaseException as exc:
            raise AcquisitionError("ASSET_STREAM") from exc
        if total != int(item["size"]):
            raise AcquisitionError("ASSET_SIZE")
        if digest.hexdigest() != item["sha256"]:
            raise AcquisitionError("ASSET_DIGEST")
        os.fsync(fd)
        os.close(fd)
        fd = -1
        os.replace(temporary, target)
        if os.name == "posix":
            parent = os.open(target.parent, os.O_RDONLY)
            try:
                os.fsync(parent)
            finally:
                os.close(parent)
    except BaseException:
        if fd >= 0:
            os.close(fd)
        temporary.unlink(missing_ok=True)
        raise


def _verify_release_bundle_manifest(raw: bytes, approved: list[dict[str, object]], expected_sha256: str) -> None:
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise AcquisitionError("BUNDLE_MANIFEST")
    try:
        value = load_closed_bytes(raw, max_bytes=1_048_576)
    except ContractError as exc:
        raise AcquisitionError("BUNDLE_MANIFEST") from exc
    if set(value) != {"schema_version", "assets"} or value["schema_version"] != "claw-host-input-bundle-v1":
        raise AcquisitionError("BUNDLE_MANIFEST")
    expected_assets = [item for item in approved if item["role"] != "bundle_manifest"]
    if value["assets"] != expected_assets or raw != canonical_bytes(value):
        raise AcquisitionError("BUNDLE_MANIFEST")


def stage_approved_assets(
    client: object,
    assets: object,
    *,
    transaction_root: Path,
    expected_bundle_manifest_sha256: str,
) -> dict[str, object]:
    """Stream one closed approved asset set into a new root-private input directory."""
    approved = _validate_asset_set(assets)
    if not isinstance(expected_bundle_manifest_sha256, str) or not SHA256.fullmatch(expected_bundle_manifest_sha256):
        raise AcquisitionError("BUNDLE_MANIFEST")
    root = Path(transaction_root)
    if not TRANSACTION_ID.fullmatch(root.name):
        raise AcquisitionError("TRANSACTION_ID")
    inputs = root / "inputs"
    try:
        inputs.mkdir(parents=True, mode=0o700, exist_ok=False)
        if inputs.is_symlink():
            raise AcquisitionError("INPUT_ROOT")
        os.chmod(inputs, 0o700)
        staged: list[dict[str, object]] = []
        for item in approved:
            staged_name = str(item["name"])
            target = inputs / staged_name
            _write_streamed_asset(client, item, target)
            staged.append({**item, "staged_name": staged_name})
        bundle = next(item for item in staged if item["role"] == "bundle_manifest")
        _verify_release_bundle_manifest(
            (inputs / str(bundle["staged_name"])).read_bytes(), approved,
            expected_bundle_manifest_sha256,
        )
        value: dict[str, object] = {
            "schema_version": "claw-host-staged-inputs-v1",
            "authority": "NONE",
            "transaction_id": root.name,
            "assets": staged,
            "bundle_manifest_sha256": expected_bundle_manifest_sha256,
        }
        _atomic(inputs / "manifest.json", canonical_bytes(value))
        return value
    except BaseException:
        if inputs.exists() and not inputs.is_symlink():
            shutil.rmtree(inputs)
        raise


class GitHubAcquisitionClient:
    """Bounded GitHub metadata/log/asset client with cross-host auth stripping."""

    API = "https://api.github.com"
    API_HOST = "api.github.com"
    ASSET_HOSTS = {"github.com", "objects.githubusercontent.com", "release-assets.githubusercontent.com"}

    def __init__(self, token: str, repository: str, *, opener: object | None = None) -> None:
        if not isinstance(token, str) or not token or len(token) > 4096:
            raise AcquisitionError("GITHUB_TOKEN")
        if not isinstance(repository, str) or "/" not in repository:
            raise AcquisitionError("GITHUB_REPOSITORY")
        self._token = token
        self.repository = repository
        if opener is None:
            import urllib.request
            class NoRedirect(urllib.request.HTTPRedirectHandler):
                def redirect_request(self, req, fp, code, msg, headers, newurl):
                    return None
            opener = urllib.request.build_opener(NoRedirect())
        self._opener = opener

    def close(self) -> None:
        self._token = ""

    def _request(self, url: str, *, accept: str, authorization: bool, limit: int, redirects: bool = False) -> bytes:
        import urllib.error
        import urllib.parse
        import urllib.error
        import urllib.request
        headers = {"Accept": accept, "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "mee-claw-host-deploy/1"}
        if authorization:
            headers["Authorization"] = "Bearer " + self._token
        for _ in range(4):
            request = urllib.request.Request(url, headers=headers)
            try:
                response = self._opener.open(request, timeout=30)
            except urllib.error.HTTPError as exc:
                if not redirects or exc.code not in {301, 302, 303, 307, 308}:
                    raise AcquisitionError("GITHUB_REQUEST") from exc
                location = exc.headers.get("Location")
                parsed = urllib.parse.urlparse(location or "")
                if parsed.scheme != "https" or parsed.hostname not in self.ASSET_HOSTS:
                    raise AcquisitionError("GITHUB_REDIRECT") from exc
                url = location
                headers = {key: value for key, value in headers.items() if key.lower() != "authorization"}
                continue
            except BaseException as exc:
                raise AcquisitionError("GITHUB_REQUEST") from exc
            raw = response.read(limit + 1)
            break
        else:
            raise AcquisitionError("GITHUB_REDIRECT")
        if len(raw) > limit:
            raise AcquisitionError("GITHUB_RESPONSE_SIZE")
        return raw

    def get_json(self, path: str) -> dict[str, object]:
        if not isinstance(path, str) or not path.startswith("/repos/") or "\x00" in path:
            raise AcquisitionError("GITHUB_PATH")
        raw = self._request(self.API + path, accept="application/vnd.github+json", authorization=True, limit=4_194_304)
        try:
            return load_closed_bytes(raw, max_bytes=4_194_304)
        except ContractError as exc:
            raise AcquisitionError("GITHUB_JSON") from exc

    def iter_asset(self, asset_id: int):
        if not isinstance(asset_id, int) or asset_id <= 0:
            raise AcquisitionError("ASSET_ID")
        import urllib.parse
        import urllib.request
        url = f"{self.API}/repos/{self.repository}/releases/assets/{asset_id}"
        headers = {"Accept": "application/octet-stream", "Authorization": "Bearer " + self._token, "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "mee-claw-host-deploy/1"}
        for redirect in range(4):
            try:
                response = self._opener.open(urllib.request.Request(url, headers=headers), timeout=30)
            except urllib.error.HTTPError as exc:
                if exc.code not in {301, 302, 303, 307, 308}:
                    raise AcquisitionError("ASSET_STREAM") from exc
                location = exc.headers.get("Location")
                parsed = urllib.parse.urlparse(location or "")
                if parsed.scheme != "https" or parsed.hostname not in self.ASSET_HOSTS:
                    raise AcquisitionError("ASSET_REDIRECT") from exc
                url = location
                headers = {key: value for key, value in headers.items() if key.lower() != "authorization"}
                continue
            except BaseException as exc:
                raise AcquisitionError("ASSET_STREAM") from exc
            status = getattr(response, "status", response.getcode())
            if status in {301, 302, 303, 307, 308}:
                location = response.headers.get("Location")
                parsed = urllib.parse.urlparse(location or "")
                if parsed.scheme != "https" or parsed.hostname not in self.ASSET_HOSTS:
                    raise AcquisitionError("ASSET_REDIRECT")
                url = location
                headers = {key: value for key, value in headers.items() if key.lower() != "authorization"}
                continue
            if status != 200:
                raise AcquisitionError("ASSET_STATUS")
            while True:
                chunk = response.read(65_536)
                if not chunk:
                    return
                yield chunk
            return
        raise AcquisitionError("ASSET_REDIRECT")


def acquire_begin_inputs(
    client: object,
    *,
    request: DeploymentRequest,
    installed_identity: dict[str, object],
    policy_path: Path,
    closure_path: Path,
    transaction_root: Path,
    now: dt.datetime,
    observation_verifier: Callable[..., object] | None = None,
    staged_input_verifier: Callable[..., object] | None = None,
) -> dict[str, object]:
    """Authenticate D1 evidence and stage exact immutable inputs before any host WAL."""
    if request.action != "begin" or request.approval_comment_id is None or request.release_id is None:
        raise AcquisitionError("BEGIN_SCOPE")
    try:
        policy_sha = hashlib.sha256(Path(policy_path).read_bytes()).hexdigest()
        closure_sha = hashlib.sha256(Path(closure_path).read_bytes()).hexdigest()
        repository_metadata = client.get_json(f"/repos/{request.repository}")
        comment = client.get_json(f"/repos/{request.repository}/issues/comments/{request.approval_comment_id}")
        release = client.get_json(f"/repos/{request.repository}/releases/{request.release_id}")
        approval = verify_approval(
            comment, repository_metadata, release,
            request=request, installed_identity=installed_identity,
            expected_policy_sha256=policy_sha, expected_closure_sha256=closure_sha,
            now=now,
        )
    except AcquisitionError:
        raise
    except BaseException as exc:
        raise AcquisitionError("APPROVAL") from exc

    staged = stage_approved_assets(
        client, approval["assets"], transaction_root=Path(transaction_root),
        expected_bundle_manifest_sha256=str(approval["bundle_manifest_sha256"]),
    )
    staged_assets = staged.get("assets")
    inventory_items = [item for item in staged_assets if isinstance(item, dict) and item.get("role") == "host_inventory"] if isinstance(staged_assets, list) else []
    if len(inventory_items) != 1:
        raise AcquisitionError("HOST_OBSERVATION")
    observation_path = Path(transaction_root) / "inputs" / str(inventory_items[0]["staged_name"])
    observation_raw = observation_path.read_bytes()
    if hashlib.sha256(observation_raw).hexdigest() != approval["host_inventory_sha256"]:
        raise AcquisitionError("HOST_OBSERVATION")
    try:
        observation = load_closed_bytes(observation_raw, max_bytes=750_000)
    except ContractError as exc:
        raise AcquisitionError("HOST_OBSERVATION") from exc
    if observation_raw != canonical_bytes(observation) or observation.get("repository") != request.repository:
        raise AcquisitionError("HOST_OBSERVATION")
    if observation.get("observed_at") != approval["host_inventory_observed_at"]:
        raise AcquisitionError("HOST_OBSERVATION_TIME")
    expected_observation = {
        key: observation.get(key)
        for key in (
            "repository", "controller_sha", "controller_tree", "collection_mode",
            "collector_path", "collector_sha256", "collection_id", "runner_name", "observed_at",
        )
    }
    if observation.get("collection_mode") != "DIRECT_CLAW" or observation.get("preflight_blockers") != []:
        raise AcquisitionError("HOST_OBSERVATION")
    if observation_verifier is None:
        try:
            from scripts.verify_claw_host_inventory import verify_observation
        except ModuleNotFoundError:
            from verify_claw_host_inventory import verify_observation
        observation_verifier = verify_observation
    try:
        observation_verifier(observation, Path(policy_path), Path(closure_path), expected_observation)
    except BaseException as exc:
        raise AcquisitionError("HOST_OBSERVATION_VERIFY") from exc

    if staged_input_verifier is None:
        staged_input_verifier = verify_staged_inputs
    try:
        staged_input_verifier(staged, Path(transaction_root) / "inputs", Path(policy_path), Path(closure_path), approval)
    except BaseException as exc:
        inputs = Path(transaction_root) / "inputs"
        if inputs.exists() and not inputs.is_symlink():
            shutil.rmtree(inputs)
        raise AcquisitionError("STAGED_INPUT_VERIFY") from exc
    staged.update({
        "controller_sha": installed_identity["controller_sha"],
        "controller_tree": installed_identity["controller_tree"],
        "policy_sha256": policy_sha,
        "closure_sha256": closure_sha,
        "approval_body_sha256": approval["approval_body_sha256"],
        "host_inventory_sha256": approval["host_inventory_sha256"],
        "rollback_deadline_seconds": approval["rollback_deadline_seconds"],
        "approval_nonce": approval["nonce"],
        "approval_comment_id": approval["approval_comment_id"],
        "release_id": approval["release_id"],
    })
    persisted = {key: value for key, value in staged.items() if key != "approval_nonce"}
    if set(persisted) != PERSISTED_STAGED_FIELDS:
        raise AcquisitionError("STAGED_MANIFEST")
    _atomic(Path(transaction_root) / "inputs" / "manifest.json", canonical_bytes(persisted))
    return staged


def _bounded_command(argv: list[str], *, limit: int = 4096) -> str:
    try:
        result = subprocess.run(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=20, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AcquisitionError("INPUT_VERIFY_COMMAND") from exc
    if result.returncode != 0 or len(result.stdout) > limit:
        raise AcquisitionError("INPUT_VERIFY_COMMAND")
    try:
        return result.stdout.decode("utf-8", "strict").strip()
    except UnicodeDecodeError as exc:
        raise AcquisitionError("INPUT_VERIFY_COMMAND") from exc


def _extract_oci_layout_archive(archive: Path, destination: Path) -> Path:
    if destination.exists():
        raise AcquisitionError("OCI_LAYOUT_EXISTS")
    destination.mkdir(mode=0o700)
    seen: set[str] = set()
    total = 0
    try:
        with tarfile.open(archive, mode="r:*") as source:
            members = source.getmembers()
            if not 1 <= len(members) <= 256:
                raise AcquisitionError("OCI_LAYOUT_ARCHIVE")
            for member in members:
                name = member.name.replace("\\", "/")
                parts = [part for part in name.split("/") if part not in {"", "."}]
                if not parts or name.startswith("/") or ".." in parts or name in seen or member.issym() or member.islnk() or not (member.isdir() or member.isfile()):
                    raise AcquisitionError("OCI_LAYOUT_ARCHIVE")
                seen.add(name)
                target = destination.joinpath(*parts)
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True, mode=0o700)
                    continue
                total += member.size
                if member.size < 0 or total > MAX_ASSET_BYTES:
                    raise AcquisitionError("OCI_LAYOUT_ARCHIVE")
                target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                extracted = source.extractfile(member)
                if extracted is None:
                    raise AcquisitionError("OCI_LAYOUT_ARCHIVE")
                fd = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0), 0o600)
                try:
                    remaining = member.size
                    while remaining:
                        chunk = extracted.read(min(65_536, remaining))
                        if not chunk:
                            raise AcquisitionError("OCI_LAYOUT_ARCHIVE")
                        view = memoryview(chunk)
                        while view:
                            written = os.write(fd, view)
                            if written <= 0:
                                raise AcquisitionError("OCI_LAYOUT_ARCHIVE")
                            view = view[written:]
                        remaining -= len(chunk)
                    if extracted.read(1):
                        raise AcquisitionError("OCI_LAYOUT_ARCHIVE")
                    os.fsync(fd)
                finally:
                    os.close(fd)
        if os.name == "posix":
            parent = os.open(destination, os.O_RDONLY)
            try:
                os.fsync(parent)
            finally:
                os.close(parent)
    except BaseException:
        if destination.exists() and not destination.is_symlink():
            shutil.rmtree(destination)
        raise
    root = destination
    children = list(destination.iterdir())
    if len(children) == 1 and children[0].is_dir():
        root = children[0]
    if not (root / "oci-layout").is_file() or not (root / "index.json").is_file() or not (root / "blobs" / "sha256").is_dir():
        raise AcquisitionError("OCI_LAYOUT_ARCHIVE")
    return root


def verify_staged_inputs(
    staged: dict[str, object], inputs: Path, policy_path: Path, closure_path: Path,
    approval: dict[str, object],
) -> None:
    """Reverify package tuples and OCI evidence solely from staged immutable bytes."""
    try:
        closure = load_closed_bytes(Path(closure_path).read_bytes(), max_bytes=1_048_576)
        policy = load_closed_bytes(Path(policy_path).read_bytes(), max_bytes=1_048_576)
    except (OSError, ContractError) as exc:
        raise AcquisitionError("INPUT_POLICY") from exc
    packages = closure.get("packages")
    if not isinstance(packages, list) or len(packages) != 10:
        raise AcquisitionError("PACKAGE_CLOSURE")
    assets = staged.get("assets")
    if not isinstance(assets, list) or any(not isinstance(item, dict) or set(item) != STAGED_ASSET_FIELDS for item in assets):
        raise AcquisitionError("STAGED_MANIFEST")
    by_role = {str(item["role"]): item for item in assets}
    expected_roles = {"deb:" + str(item.get("name")) for item in packages if isinstance(item, dict)}
    if set(role for role in by_role if role.startswith("deb:")) != expected_roles:
        raise AcquisitionError("PACKAGE_CLOSURE")
    for package in packages:
        if not isinstance(package, dict) or set(package) != {"name", "version", "architecture", "sha256"}:
            raise AcquisitionError("PACKAGE_CLOSURE")
        item = by_role["deb:" + str(package["name"])]
        if item["sha256"] != package["sha256"]:
            raise AcquisitionError("PACKAGE_DIGEST")
        path = inputs / str(item["staged_name"])
        fields = _bounded_command(["/usr/bin/dpkg-deb", "--field", str(path), "Package", "Version", "Architecture"]).splitlines()
        expected_fields = [
            f"Package: {package['name']}",
            f"Version: {package['version']}",
            f"Architecture: {package['architecture']}",
        ]
        if fields != expected_fields:
            raise AcquisitionError("PACKAGE_METADATA")
    archive = by_role.get("oci_archive")
    if not isinstance(archive, dict) or archive["sha256"] != policy.get("oci_archive_sha256") or archive["sha256"] != approval.get("oci_archive_sha256"):
        raise AcquisitionError("OCI_ARCHIVE")
    for role in ("oci_layout", "oci_receipt", "oci_sidecar", "bundle_manifest"):
        if role not in by_role:
            raise AcquisitionError("OCI_EVIDENCE")
    layout_root = _extract_oci_layout_archive(
        inputs / str(by_role["oci_layout"]["staged_name"]), inputs / "verified-oci-layout",
    )
    try:
        try:
            from scripts.verify_oci_evidence_approval import main as verify_oci_approval
        except ModuleNotFoundError:
            from verify_oci_evidence_approval import main as verify_oci_approval
        approval_path = Path("/usr/local/libexec/mee-claw-host-deploy-lib/oci-evidence-approval.json")
        if not approval_path.is_file():
            raise AcquisitionError("OCI_APPROVAL_NOT_INSTALLED")
        rc = verify_oci_approval([
            "--policy", str(policy_path), "--approval", str(approval_path),
            "--approval-policy-path", "ci/claw/oci-evidence-approval.json",
            "--receipt", str(inputs / str(by_role["oci_receipt"]["staged_name"])),
            "--receipt-sha256", str(inputs / str(by_role["oci_sidecar"]["staged_name"])),
            "--archive", str(inputs / str(by_role["oci_archive"]["staged_name"])),
            "--layout", str(layout_root), "--closure", str(closure_path),
            "--origin", "https://github.com/Dimkox/multi-exchange-engine.git",
        ])
        if rc != 0:
            raise AcquisitionError("OCI_EVIDENCE")
    finally:
        if (inputs / "verified-oci-layout").exists():
            shutil.rmtree(inputs / "verified-oci-layout")


def _verify_response(value: object, request: DeploymentRequest) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != RESPONSE_FIELDS:
        raise ControllerError("RESPONSE_FIELDS")
    if value["schema_version"] != "claw-host-deployment-response-v1" or value["authority"] != "NONE":
        raise ControllerError("RESPONSE_AUTHORITY")
    if value["action"] != request.action:
        raise ControllerError("RESPONSE_BINDING")
    if request.action == "begin":
        if not isinstance(value["transaction_id"], str) or not re.fullmatch(r"[0-9a-f]{32}", value["transaction_id"]):
            raise ControllerError("RESPONSE_BINDING")
    elif value["transaction_id"] != request.transaction_id:
        raise ControllerError("RESPONSE_BINDING")
    if value["state"] not in RESPONSE_STATES:
        raise ControllerError("RESPONSE_STATE")
    receipt = value["receipt_sha256"]
    if receipt is not None and (not isinstance(receipt, str) or len(receipt) != 64 or any(ch not in "0123456789abcdef" for ch in receipt)):
        raise ControllerError("RESPONSE_RECEIPT")
    return value


class RequestRegistry:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    @staticmethod
    def _key(request: DeploymentRequest) -> str:
        parts = (
            request.action, request.transaction_id or "begin",
            str(request.approval_comment_id or 0),
            str(request.release_id or 0),
        )
        return hashlib.sha256("\0".join(parts).encode()).hexdigest()

    def handle(
        self, raw: bytes,
        dispatch: Callable[[DeploymentRequest], dict[str, object]],
    ) -> dict[str, object]:
        try:
            value = load_closed_bytes(raw, max_bytes=MAX_REQUEST)
            action = value.get("action")
            if not isinstance(action, str):
                raise ContractError("REQUEST_ACTION")
            request = verify_request(value, expected_action=action)
        except ContractError as exc:
            raise ControllerError(str(exc)) from exc
        key = self._key(request)
        lock = self.root / "locks" / f"{key}.lock"
        lock.parent.mkdir(parents=True, exist_ok=True)
        fd = -1
        windows_exclusive = False
        try:
            if os.name == "posix":
                import fcntl
                fd = os.open(lock, os.O_CREAT | os.O_RDWR, 0o600)
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError as exc:
                    raise ControllerError("REQUEST_BUSY") from exc
            else:
                try:
                    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                    windows_exclusive = True
                except FileExistsError as exc:
                    raise ControllerError("REQUEST_BUSY") from exc
            return _verify_response(dispatch(request), request)
        finally:
            if "request" in locals():
                object.__setattr__(request, "github_token", None)
            if fd >= 0:
                os.close(fd)
                if windows_exclusive:
                    lock.unlink(missing_ok=True)


class LocalActionDispatcher:
    """Route one verified request to a fixed installed local operation."""

    def __init__(self, runtime: object) -> None:
        self.runtime = runtime

    def __call__(self, request: DeploymentRequest) -> dict[str, object]:
        operation = getattr(self.runtime, request.action, None)
        if operation is None or not callable(operation):
            raise ControllerError("ACTION_NOT_IMPLEMENTED")
        try:
            return operation(request)
        except ControllerError:
            raise
        except Exception as exc:
            raise ControllerError("ACTION_FAILED") from exc


class HostDeploymentRuntime:
    """Production local root operations; no workflow or runner checkout input."""

    D0_RECEIPT = Path("/var/lib/mee-claw-host-deploy/D0-VERIFIED.json")
    ROOT = Path("/var/lib/mee-claw-host-deploy")
    POLICY = Path("/usr/local/libexec/mee-claw-host-deploy-lib/host-bootstrap-policy.json")
    CLOSURE = Path("/usr/local/libexec/mee-claw-host-deploy-lib/host-package-closure.json")
    LEGACY_RECOVERY_FACTS = {
        "repository": "Dimkox/multi-exchange-engine",
        "transaction_id": "e8725f1d09cf11696bff392912d141cf",
        "begin_intent_sha256": "430a48857f202b75156b1688956ec5875422e6311fe7c7f0f8b6fc06b873a924",
        "staged_manifest_sha256": "71b95360756db0e5e59dd02fa4b50a2243efe375128dd84c8e13cf8d34bffb1e",
        "nonce_record_sha256": "87dfc3089898cd20dee90ffac875988a15c4c39ae6581e00516bcf7ea69804ce",
        "terminal_journal_sha256": "c2d1966ca9f8496c88a078dca26f551845b2ca2f62ed975e0cf4703176930411",
        "credential_binding_sha256": "fce9ef6ffab54b241aa8c471a87b27c96a96841897a2143765f66bce55839244",
        "old_controller_sha": "0e5ce5c95f031c9413da4784754776deba13b8c4",
        "old_controller_tree": "ba01a6d07727833a1c50d6904f5b15c7d39e447a",
        "reason": "PRE_MARKER_TERMINAL_ROLLBACK_COMPATIBILITY",
    }

    def __init__(self, *, root: Path | None = None, policy: Path | None = None, closure: Path | None = None) -> None:
        self.root = Path(root or self.ROOT)
        self.policy_path = Path(policy or self.POLICY)
        self.closure_path = Path(closure or self.CLOSURE)

    @staticmethod
    def _response(action: str, transaction_id: str, state: str, receipt_sha256: str | None = None) -> dict[str, object]:
        return {
            "schema_version": "claw-host-deployment-response-v1",
            "authority": "NONE",
            "action": action,
            "transaction_id": transaction_id,
            "state": state,
            "receipt_sha256": receipt_sha256,
        }

    def _identity(self) -> dict[str, object]:
        receipt = self._d0_receipt()
        return {
            "schema_version": "claw-host-deployment-installed-v1",
            "repository": receipt["repository"],
            "default_branch": "main",
            "controller_sha": receipt["controller_sha"],
            "controller_tree": receipt["controller_tree"],
        }

    def _d0_receipt(self) -> dict[str, object]:
        raw = _read_private_state(self.root / "D0-VERIFIED.json", max_bytes=16_384, error="D0_IDENTITY")
        receipt = load_closed_bytes(raw, max_bytes=16_384)
        fields = {
            "schema_version", "authority", "not_host_receipt", "repository",
            "controller_sha", "controller_tree", "install_manifest_sha256",
            "artifact_count", "status", "created_at",
        }
        if set(receipt) != fields or raw != canonical_bytes(receipt) or receipt.get("status") != "D0_VERIFIED" or receipt.get("authority") != "NONE" or receipt.get("not_host_receipt") is not True:
            raise ControllerError("D0_IDENTITY")
        return receipt

    def _policy(self) -> dict[str, object]:
        value = load_closed_bytes(self.policy_path.read_bytes(), max_bytes=1_048_576)
        if value.get("repository") != "Dimkox/multi-exchange-engine" or value.get("runner_name") != "claw-engine-runner":
            raise ControllerError("HOST_POLICY")
        return value

    def _paths(self, transaction_id: str) -> tuple[Path, Path, Path]:
        if not re.fullmatch(r"[0-9a-f]{32}", transaction_id):
            raise ControllerError("TRANSACTION_ID")
        durable = Path(str(self._policy()["transaction_root"]))
        return durable / f"{transaction_id}.json", durable / f"{transaction_id}.receipt.json", self.root / "transactions" / transaction_id

    def _assert_no_active_transaction(self) -> None:
        durable = Path(str(self._policy()["transaction_root"]))
        if not durable.exists():
            return
        for path in durable.glob("[0-9a-f]" * 32 + ".json"):
            value = load_closed_bytes(path.read_bytes(), max_bytes=4_194_304)
            if value.get("status") in {"OPEN", "COMMITTED"}:
                raise ControllerError("ACTIVE_TRANSACTION")

    @contextmanager
    def _controller_lock(self):
        if os.name != "posix":
            raise ControllerError("ROOT_LOCK_UNAVAILABLE")
        import fcntl

        lock_root = self.root / "locks"
        lock_root.mkdir(parents=True, exist_ok=True, mode=0o700)
        path = lock_root / "begin.lock"
        fd = os.open(path, os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
        try:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise ControllerError("ACTIVE_TRANSACTION") from exc
            yield
        finally:
            os.close(fd)

    def _consume_nonce(self, staged: dict[str, object], transaction_id: str) -> None:
        nonce = staged.get("approval_nonce")
        if not isinstance(nonce, str) or not re.fullmatch(r"[A-Za-z0-9_-]{43}", nonce):
            raise ControllerError("APPROVAL_NONCE")
        value: dict[str, object] = {
            "schema_version": "claw-host-deployment-nonce-consumption-v1",
            "transaction_id": transaction_id,
            "approval_comment_id": staged.get("approval_comment_id"),
            "release_id": staged.get("release_id"),
            "approval_body_sha256": staged.get("approval_body_sha256"),
            "nonce_sha256": hashlib.sha256(nonce.encode()).hexdigest(),
        }
        self._write_nonce_record(value)

    def _write_nonce_record(self, value: dict[str, object]) -> None:
        fields = {"schema_version", "transaction_id", "approval_comment_id", "release_id", "approval_body_sha256", "nonce_sha256"}
        if set(value) != fields or value.get("schema_version") != "claw-host-deployment-nonce-consumption-v1":
            raise ControllerError("APPROVAL_NONCE")
        if not isinstance(value["approval_comment_id"], int) or not isinstance(value["release_id"], int) or not re.fullmatch(r"[0-9a-f]{64}", str(value["approval_body_sha256"])):
            raise ControllerError("APPROVAL_NONCE")
        if not isinstance(value["transaction_id"], str) or not TRANSACTION_ID.fullmatch(value["transaction_id"]):
            raise ControllerError("APPROVAL_NONCE")
        if not isinstance(value["nonce_sha256"], str) or not SHA256.fullmatch(value["nonce_sha256"]):
            raise ControllerError("APPROVAL_NONCE")
        try:
            _exclusive(self.root / "nonces" / f"{value['nonce_sha256']}.json", canonical_bytes(value))
        except FileExistsError as exc:
            raise ControllerError("APPROVAL_NONCE_REPLAY") from exc

    def _create_begin_intent(self, staged: dict[str, object], transaction_id: str) -> dict[str, object]:
        nonce = staged.get("approval_nonce")
        manifest_path = self.root / "transactions" / transaction_id / "inputs" / "manifest.json"
        if not isinstance(nonce, str) or not re.fullmatch(r"[A-Za-z0-9_-]{43}", nonce) or not manifest_path.is_file():
            raise ControllerError("BEGIN_INTENT")
        manifest_raw = manifest_path.read_bytes()
        manifest = load_closed_bytes(manifest_raw, max_bytes=1_048_576)
        if set(manifest) != PERSISTED_STAGED_FIELDS or "approval_nonce" in manifest or manifest_raw != canonical_bytes(manifest):
            raise ControllerError("BEGIN_INTENT")
        value: dict[str, object] = {
            "schema_version": "claw-host-deployment-begin-intent-v1",
            "transaction_id": transaction_id,
            "approval_comment_id": staged.get("approval_comment_id"),
            "release_id": staged.get("release_id"),
            "approval_body_sha256": staged.get("approval_body_sha256"),
            "nonce_sha256": hashlib.sha256(nonce.encode()).hexdigest(),
            "staged_manifest_sha256": hashlib.sha256(manifest_raw).hexdigest(),
            "controller_sha": staged.get("controller_sha"),
            "controller_tree": staged.get("controller_tree"),
            "rollback_deadline_seconds": staged.get("rollback_deadline_seconds"),
        }
        self._verify_begin_intent(value, manifest)
        _exclusive(self.root / "transactions" / transaction_id / "begin-intent.json", canonical_bytes(value))
        return value

    @staticmethod
    def _verify_begin_intent(value: dict[str, object], manifest: dict[str, object]) -> None:
        if set(value) != BEGIN_INTENT_FIELDS or value.get("schema_version") != "claw-host-deployment-begin-intent-v1":
            raise ControllerError("BEGIN_INTENT")
        transaction_id = value.get("transaction_id")
        if not isinstance(transaction_id, str) or not TRANSACTION_ID.fullmatch(transaction_id) or manifest.get("transaction_id") != transaction_id:
            raise ControllerError("BEGIN_INTENT")
        for field in ("approval_comment_id", "release_id"):
            if not isinstance(value.get(field), int) or value[field] != manifest.get(field):
                raise ControllerError("BEGIN_INTENT")
        for field in ("approval_body_sha256", "controller_sha", "controller_tree"):
            expected = SHA256 if field == "approval_body_sha256" else re.compile(r"^[0-9a-f]{40}$")
            if not isinstance(value.get(field), str) or not expected.fullmatch(value[field]) or value[field] != manifest.get(field):
                raise ControllerError("BEGIN_INTENT")
        if not isinstance(value.get("nonce_sha256"), str) or not SHA256.fullmatch(value["nonce_sha256"]):
            raise ControllerError("BEGIN_INTENT")
        if not isinstance(value.get("staged_manifest_sha256"), str) or not SHA256.fullmatch(value["staged_manifest_sha256"]):
            raise ControllerError("BEGIN_INTENT")
        deadline = value.get("rollback_deadline_seconds")
        if not isinstance(deadline, int) or isinstance(deadline, bool) or deadline != manifest.get("rollback_deadline_seconds"):
            raise ControllerError("BEGIN_INTENT")

    def _load_begin_intent(self, path: Path) -> tuple[dict[str, object], dict[str, object]]:
        value = load_closed_bytes(path.read_bytes(), max_bytes=4096)
        transaction_id = value.get("transaction_id")
        if not isinstance(transaction_id, str) or path.parent.name != transaction_id:
            raise ControllerError("BEGIN_INTENT")
        manifest_path = path.parent / "inputs" / "manifest.json"
        manifest_raw = manifest_path.read_bytes()
        manifest = load_closed_bytes(manifest_raw, max_bytes=1_048_576)
        if set(manifest) != PERSISTED_STAGED_FIELDS or manifest_raw != canonical_bytes(manifest):
            raise ControllerError("BEGIN_INTENT")
        self._verify_begin_intent(value, manifest)
        if hashlib.sha256(manifest_raw).hexdigest() != value["staged_manifest_sha256"]:
            raise ControllerError("BEGIN_INTENT")
        return value, manifest

    def _host_apply_intent(self, transaction_id: str, *, create: bool) -> dict[str, object]:
        transaction_root = self.root / "transactions" / transaction_id
        begin_path = transaction_root / "begin-intent.json"
        begin_raw = begin_path.read_bytes()
        begin_intent, _ = self._load_begin_intent(begin_path)
        if begin_intent.get("transaction_id") != transaction_id:
            raise ControllerError("HOST_APPLY_INTENT")
        expected: dict[str, object] = {
            "schema_version": "claw-host-deployment-host-apply-intent-v1",
            "transaction_id": transaction_id,
            "begin_intent_sha256": hashlib.sha256(begin_raw).hexdigest(),
        }
        path = transaction_root / "host-apply-intent.json"
        if create:
            try:
                _exclusive(path, canonical_bytes(expected))
            except FileExistsError:
                pass
        raw = _read_private_state(path, max_bytes=4096, error="HOST_APPLY_INTENT")
        value = load_closed_bytes(raw, max_bytes=4096)
        if set(value) != HOST_APPLY_INTENT_FIELDS or value != expected or raw != canonical_bytes(value):
            raise ControllerError("HOST_APPLY_INTENT")
        return value

    @staticmethod
    def _public_journal_state(value: dict[str, object]) -> str:
        phase = value.get("phase")
        if not isinstance(phase, str):
            raise ControllerError("HOST_STATUS")
        if phase == "PREPARED":
            return "BEGIN_ACCEPTED"
        if phase.startswith("APPLYING(") or phase.startswith("APPLIED("):
            return "APPLYING"
        if phase == "VERIFIED":
            return "FINALIZING"
        if phase in RESPONSE_STATES:
            return phase
        raise ControllerError("HOST_STATUS")

    def _begin_replay(self, request: DeploymentRequest) -> dict[str, object] | None:
        intent_matches: list[tuple[dict[str, object], dict[str, object]]] = []
        transaction_root = self.root / "transactions"
        if transaction_root.is_dir():
            for path in sorted(transaction_root.glob("[0-9a-f]" * 32 + "/begin-intent.json")):
                intent, manifest = self._load_begin_intent(path)
                if intent["approval_comment_id"] == request.approval_comment_id and intent["release_id"] == request.release_id:
                    intent_matches.append((intent, manifest))
        if len(intent_matches) > 1:
            raise ControllerError("BEGIN_INTENT_STATE")
        if intent_matches:
            intent, manifest = intent_matches[0]
            nonce_path = self.root / "nonces" / f"{intent['nonce_sha256']}.json"
            expected_nonce = {
                "schema_version": "claw-host-deployment-nonce-consumption-v1",
                "transaction_id": intent["transaction_id"],
                "approval_comment_id": intent["approval_comment_id"],
                "release_id": intent["release_id"],
                "approval_body_sha256": intent["approval_body_sha256"],
                "nonce_sha256": intent["nonce_sha256"],
            }
            if nonce_path.is_file():
                if load_closed_bytes(nonce_path.read_bytes(), max_bytes=4096) != expected_nonce:
                    raise ControllerError("APPROVAL_NONCE_STATE")
            else:
                self._write_nonce_record(expected_nonce)
            transaction_id = str(intent["transaction_id"])
            journal, _, _ = self._paths(transaction_id)
            if not journal.is_file():
                return self._continue_begin(request, intent, manifest)
            value = load_closed_bytes(journal.read_bytes(), max_bytes=4_194_304)
            state = self._public_journal_state(value)
            receipt = self._paths(transaction_id)[1]
            if state == "ROLLED_BACK":
                _, receipt = self._rollback_paths(transaction_id)
            digest = hashlib.sha256(receipt.read_bytes()).hexdigest() if receipt.is_file() else None
            return self._response("begin", transaction_id, state, digest)

        matches: list[dict[str, object]] = []
        nonce_root = self.root / "nonces"
        if nonce_root.is_dir():
            fields = {"schema_version", "transaction_id", "approval_comment_id", "release_id", "approval_body_sha256", "nonce_sha256"}
            for path in sorted(nonce_root.glob("[0-9a-f]" * 64 + ".json")):
                value = load_closed_bytes(path.read_bytes(), max_bytes=4096)
                if set(value) != fields or value.get("schema_version") != "claw-host-deployment-nonce-consumption-v1" or value.get("nonce_sha256") != path.stem:
                    raise ControllerError("APPROVAL_NONCE_STATE")
                if value.get("approval_comment_id") == request.approval_comment_id and value.get("release_id") == request.release_id:
                    matches.append(value)
        if not matches:
            return None
        if len(matches) != 1:
            raise ControllerError("APPROVAL_NONCE_STATE")
        transaction_id = matches[0].get("transaction_id")
        if not isinstance(transaction_id, str) or not TRANSACTION_ID.fullmatch(transaction_id):
            raise ControllerError("APPROVAL_NONCE_STATE")
        journal, host_receipt, _ = self._paths(transaction_id)
        if not journal.is_file():
            raise ControllerError("APPROVAL_NONCE_INCOMPLETE")
        value = load_closed_bytes(journal.read_bytes(), max_bytes=4_194_304)
        state = self._public_journal_state(value)
        receipt = host_receipt
        if state == "ROLLED_BACK":
            _, receipt = self._rollback_paths(transaction_id)
        digest = hashlib.sha256(receipt.read_bytes()).hexdigest() if receipt.is_file() else None
        return self._response("begin", transaction_id, state, digest)

    def _continue_begin(
        self, request: DeploymentRequest, intent: dict[str, object], staged: dict[str, object],
    ) -> dict[str, object]:
        transaction_id = str(intent["transaction_id"])
        journal, receipt, staging_root = self._paths(transaction_id)
        assets = staged.get("assets")
        if not isinstance(assets, list):
            raise ControllerError("STAGED_MANIFEST")
        by_role = {str(item.get("role")): item for item in assets if isinstance(item, dict)}
        required_roles = {"oci_archive", "oci_layout", "oci_receipt", "oci_sidecar"}
        if not required_roles <= set(by_role):
            raise ControllerError("STAGED_MANIFEST")
        inputs = staging_root / "inputs"
        extracted_root = staging_root / "oci-layout"
        if extracted_root.exists():
            if extracted_root.is_symlink() or not extracted_root.is_dir():
                raise ControllerError("OCI_LAYOUT_STATE")
            shutil.rmtree(extracted_root)
        layout_root = _extract_oci_layout_archive(inputs / str(by_role["oci_layout"]["staged_name"]), extracted_root)
        host = self._host_module()
        argv = [
            *self._host_args(transaction_id), "--debs", str(inputs),
            "--oci-archive", str(inputs / str(by_role["oci_archive"]["staged_name"])),
            "--oci-layout", str(layout_root),
            "--oci-evidence-receipt", str(inputs / str(by_role["oci_receipt"]["staged_name"])),
            "--oci-evidence-sidecar", str(inputs / str(by_role["oci_sidecar"]["staged_name"])),
            "--controller-sha", str(intent["controller_sha"]),
            "--deadline-seconds", str(intent["rollback_deadline_seconds"]),
        ]
        self._host_apply_intent(transaction_id, create=True)
        if host.main(argv, token_reader=lambda: request.github_token) != 0:
            raise ControllerError("HOST_APPLY")
        value = load_closed_bytes(journal.read_bytes(), max_bytes=4_194_304)
        if value.get("phase") != "HOST_APPLIED_PENDING_FINALIZE" or value.get("status") != "OPEN":
            raise ControllerError("HOST_PENDING_STATE")
        return self._response("begin", transaction_id, "HOST_APPLIED_PENDING_FINALIZE")

    @staticmethod
    def _host_module():
        try:
            from scripts import claw_host_bootstrap_transaction as host
        except ModuleNotFoundError:
            import claw_host_bootstrap_transaction as host
        return host

    def _host_args(self, transaction_id: str, *, rollback: bool = False) -> list[str]:
        journal, receipt, _ = self._paths(transaction_id)
        args = ["--policy", str(self.policy_path), "--closure", str(self.closure_path), "--journal", str(journal), "--receipt", str(receipt)]
        if rollback:
            args.append("--rollback")
        return args

    def _recovery_backend(self, transaction_id: str, token_reader: Callable[[], str] | None = None):
        host = self._host_module()
        policy = self._policy()
        closure = load_closed_bytes(self.closure_path.read_bytes(), max_bytes=1_048_576)
        durable = Path(str(policy["transaction_root"]))
        binding = host.closed(durable / "credential-binding.json", {"transaction_id", "controller_sha", "policy_sha256"})
        if binding.get("transaction_id") != transaction_id:
            raise ControllerError("TRANSACTION_BINDING")
        records = sorted(closure.get("packages", []), key=lambda value: value["name"])
        archives = sorted((durable / "packages").glob("*.deb"))
        return host.RealBackend(
            policy, archives=archives, package_records=records,
            oci_archive=durable / "image.oci", token_reader=token_reader,
            credential_binding=binding,
        )

    def begin(self, request: DeploymentRequest) -> dict[str, object]:
        with self._controller_lock():
            return self._begin_locked(request)

    def _begin_locked(self, request: DeploymentRequest) -> dict[str, object]:
        replay = self._begin_replay(request)
        if replay is not None:
            return replay
        self._assert_no_active_transaction()
        transaction_id = secrets.token_hex(16)
        journal, receipt_path, staging_root = self._paths(transaction_id)
        if journal.exists() or receipt_path.exists() or staging_root.exists():
            raise ControllerError("TRANSACTION_COLLISION")
        client = GitHubAcquisitionClient(request.github_token, request.repository)
        try:
            staged = acquire_begin_inputs(
                client, request=request, installed_identity=self._identity(),
                policy_path=self.policy_path, closure_path=self.closure_path,
                transaction_root=staging_root, now=dt.datetime.now(dt.timezone.utc),
            )
            intent = self._create_begin_intent(staged, transaction_id)
            self._consume_nonce(staged, transaction_id)
            persisted = load_closed_bytes((staging_root / "inputs" / "manifest.json").read_bytes(), max_bytes=1_048_576)
            return self._continue_begin(request, intent, persisted)
        finally:
            client.close()

    def _runner_projection(self, token: str) -> dict[str, object]:
        try:
            from scripts.verify_claw_runner_api_canary import verify
        except ModuleNotFoundError:
            from verify_claw_runner_api_canary import verify
        projection = verify(token, self._policy())
        if not isinstance(projection, dict):
            raise ControllerError("RUNNER_PROJECTION")
        return projection

    def _rollback_paths(self, transaction_id: str) -> tuple[Path, Path]:
        journal, _, _ = self._paths(transaction_id)
        return (
            journal.parent / f"{transaction_id}.rollback-intent.json",
            journal.parent / f"{transaction_id}.rollback-receipt.json",
        )

    def _legacy_recovery_paths(self) -> tuple[Path, Path]:
        root = self.root / "transactions" / str(self.LEGACY_RECOVERY_FACTS["transaction_id"])
        return root / "legacy-recovery-authorization.json", root / "legacy-recovery-receipt.json"

    def _legacy_recovery_state(self) -> tuple[dict[str, object], object, bytes, bytes]:
        facts = self.LEGACY_RECOVERY_FACTS
        transaction_id = str(facts["transaction_id"])
        journal, host_receipt, transaction_root = self._paths(transaction_id)
        durable = journal.parent
        for path in (self.root / "transactions", transaction_root, transaction_root / "inputs", durable):
            _require_private_directory(path, error="LEGACY_RECOVERY_STATE")
        begin_raw = _read_private_state(transaction_root / "begin-intent.json", max_bytes=4096, error="LEGACY_RECOVERY_STATE")
        manifest_raw = _read_private_state(transaction_root / "inputs" / "manifest.json", max_bytes=1_048_576, error="LEGACY_RECOVERY_STATE")
        begin = load_closed_bytes(begin_raw, max_bytes=4096)
        manifest = load_closed_bytes(manifest_raw, max_bytes=1_048_576)
        self._verify_begin_intent(begin, manifest)
        if begin.get("controller_sha") != facts["old_controller_sha"] or begin.get("controller_tree") != facts["old_controller_tree"]:
            raise ControllerError("LEGACY_RECOVERY_STATE")
        nonce_path = self.root / "nonces" / f"{begin.get('nonce_sha256')}.json"
        nonce_raw = _read_private_state(nonce_path, max_bytes=4096, error="LEGACY_RECOVERY_STATE")
        nonce = load_closed_bytes(nonce_raw, max_bytes=4096)
        expected_nonce = {
            "schema_version": "claw-host-deployment-nonce-consumption-v1",
            "transaction_id": transaction_id,
            "approval_comment_id": begin.get("approval_comment_id"),
            "release_id": begin.get("release_id"),
            "approval_body_sha256": begin.get("approval_body_sha256"),
            "nonce_sha256": begin.get("nonce_sha256"),
        }
        if nonce != expected_nonce or nonce_raw != canonical_bytes(nonce):
            raise ControllerError("LEGACY_RECOVERY_STATE")
        journal_raw = _read_private_state(journal, max_bytes=4_194_304, error="LEGACY_RECOVERY_STATE")
        host = self._host_module()
        journal_object = host.Journal.load_private(durable, journal, ("ROLLED_BACK",))
        if not host.is_terminal_rolled_back_journal(journal_object.value):
            raise ControllerError("LEGACY_RECOVERY_STATE")
        binding_path = durable / "credential-binding.json"
        binding_raw = _read_private_state(binding_path, max_bytes=4096, error="LEGACY_RECOVERY_STATE")
        binding = load_closed_bytes(binding_raw, max_bytes=4096)
        if binding != {
            "transaction_id": transaction_id,
            "controller_sha": facts["old_controller_sha"],
            "policy_sha256": hashlib.sha256(self.policy_path.read_bytes()).hexdigest(),
        } or binding_raw != canonical_bytes(binding):
            raise ControllerError("LEGACY_RECOVERY_STATE")
        expected_hashes = {
            "begin_intent_sha256": hashlib.sha256(begin_raw).hexdigest(),
            "staged_manifest_sha256": hashlib.sha256(manifest_raw).hexdigest(),
            "nonce_record_sha256": hashlib.sha256(nonce_raw).hexdigest(),
            "terminal_journal_sha256": hashlib.sha256(journal_raw).hexdigest(),
            "credential_binding_sha256": hashlib.sha256(binding_raw).hexdigest(),
        }
        if any(expected_hashes[key] != facts[key] for key in expected_hashes):
            raise ControllerError("LEGACY_RECOVERY_STATE")
        for path in (transaction_root / "host-apply-intent.json", host_receipt, durable / "credential-state"):
            if _state_path_present(path, error="LEGACY_RECOVERY_STATE"):
                raise ControllerError("LEGACY_RECOVERY_STATE")
        journal_object.assert_private_identity()
        return dict(facts), host, journal_raw, binding_raw

    def recover_legacy_terminal(self, approval_comment: Path | None = None, repository_metadata: Path | None = None) -> dict[str, object]:
        with self._controller_lock():
            facts, host, journal_before, binding_before = self._legacy_recovery_state()
            transaction_id = str(facts["transaction_id"])
            authorization_path, compatibility_receipt = self._legacy_recovery_paths()
            rollback_intent, rollback_receipt = self._rollback_paths(transaction_id)
            identity = self._identity()
            d0 = self._d0_receipt()
            expected = {
                **facts,
                "recovery_controller_sha": identity["controller_sha"],
                "recovery_controller_tree": identity["controller_tree"],
                "recovery_install_manifest_sha256": d0["install_manifest_sha256"],
            }
            if not _state_path_present(authorization_path, error="LEGACY_RECOVERY_AUTHORIZATION"):
                if approval_comment is None or repository_metadata is None:
                    raise ControllerError("LEGACY_RECOVERY_AUTHORIZATION")
                if any(_state_path_present(path, error="LEGACY_RECOVERY_STATE") for path in (rollback_intent, rollback_receipt, compatibility_receipt)):
                    raise ControllerError("LEGACY_RECOVERY_STATE")
                approved = verify_legacy_recovery_approval(
                    load_closed_bytes(_read_private_state(Path(approval_comment), max_bytes=1_048_576, error="LEGACY_RECOVERY_AUTHORIZATION"), max_bytes=1_048_576),
                    load_closed_bytes(_read_private_state(Path(repository_metadata), max_bytes=1_048_576, error="LEGACY_RECOVERY_AUTHORIZATION"), max_bytes=1_048_576),
                    expected=expected, now=dt.datetime.now(dt.timezone.utc),
                )
                authorization = {
                    "schema_version": "claw-host-deployment-legacy-recovery-authorization-v1",
                    "authority": "NONE", "not_host_receipt": True,
                    "status": "RETROSPECTIVE_COMPATIBILITY_RECOVERY_APPROVED",
                    **expected,
                    "approval_comment_id": approved["approval_comment_id"],
                    "approval_body_sha256": approved["approval_body_sha256"],
                    "approval_owner_login": approved["approval_owner_login"],
                    "approval_owner_id": approved["approval_owner_id"],
                }
                _exclusive(authorization_path, canonical_bytes(authorization))
            authorization_raw = _read_private_state(authorization_path, max_bytes=16_384, error="LEGACY_RECOVERY_AUTHORIZATION")
            authorization = load_closed_bytes(authorization_raw, max_bytes=16_384)
            if set(authorization) != LEGACY_RECOVERY_AUTHORIZATION_FIELDS or authorization.get("schema_version") != "claw-host-deployment-legacy-recovery-authorization-v1" or any(authorization.get(key) != value for key, value in expected.items()) or authorization.get("authority") != "NONE" or authorization.get("not_host_receipt") is not True or authorization.get("status") != "RETROSPECTIVE_COMPATIBILITY_RECOVERY_APPROVED" or authorization_raw != canonical_bytes(authorization):
                raise ControllerError("LEGACY_RECOVERY_AUTHORIZATION")
            approval_comment_id = authorization.get("approval_comment_id")
            approval_owner_id = authorization.get("approval_owner_id")
            if (
                not isinstance(approval_comment_id, int) or isinstance(approval_comment_id, bool) or approval_comment_id <= 0
                or not isinstance(approval_owner_id, int) or isinstance(approval_owner_id, bool) or approval_owner_id <= 0
                or authorization.get("approval_owner_login") != str(facts["repository"]).split("/", 1)[0]
                or not isinstance(authorization.get("approval_body_sha256"), str)
                or not SHA256.fullmatch(str(authorization["approval_body_sha256"]))
            ):
                raise ControllerError("LEGACY_RECOVERY_AUTHORIZATION")
            if _state_path_present(rollback_receipt, error="LEGACY_RECOVERY_STATE"):
                _read_private_state(rollback_receipt, max_bytes=16_384, error="LEGACY_RECOVERY_STATE")
            intent = self._rollback_intent(transaction_id, self._paths(transaction_id)[1])
            if intent.get("prior_host_receipt_sha256") is not None:
                raise ControllerError("LEGACY_RECOVERY_STATE")
            response = self._finish_rollback(transaction_id, intent, host)
            rollback_receipt_raw = _read_private_state(rollback_receipt, max_bytes=16_384, error="LEGACY_RECOVERY_RECEIPT")
            rollback_receipt_value = load_closed_bytes(rollback_receipt_raw, max_bytes=16_384)
            created_at = rollback_receipt_value.get("created_at")
            if not isinstance(created_at, str) or not created_at.endswith("Z"):
                raise ControllerError("LEGACY_RECOVERY_RECEIPT")
            journal_after = _read_private_state(self._paths(transaction_id)[0], max_bytes=4_194_304, error="LEGACY_RECOVERY_MUTATION")
            binding_after = _read_private_state(self._paths(transaction_id)[0].parent / "credential-binding.json", max_bytes=4096, error="LEGACY_RECOVERY_MUTATION")
            if journal_before != journal_after or binding_before != binding_after:
                raise ControllerError("LEGACY_RECOVERY_MUTATION")
            if _state_path_present(transaction_root := self.root / "transactions" / transaction_id / "host-apply-intent.json", error="LEGACY_RECOVERY_STATE"):
                raise ControllerError("LEGACY_RECOVERY_MUTATION")
            receipt_value = {
                "schema_version": "claw-host-deployment-legacy-recovery-receipt-v1",
                "authority": "NONE", "not_host_receipt": True,
                "status": "RETROSPECTIVE_COMPATIBILITY_RECOVERY_COMPLETE",
                "transaction_id": transaction_id,
                "authorization_sha256": hashlib.sha256(authorization_raw).hexdigest(),
                "journal_sha256": hashlib.sha256(journal_before).hexdigest(),
                "credential_binding_sha256": hashlib.sha256(binding_before).hexdigest(),
                "rollback_intent_sha256": hashlib.sha256(_read_private_state(rollback_intent, max_bytes=4096, error="LEGACY_RECOVERY_RECEIPT")).hexdigest(),
                "rollback_receipt_sha256": response["receipt_sha256"],
                "recovery_controller_sha": identity["controller_sha"],
                "recovery_controller_tree": identity["controller_tree"],
                "created_at": created_at,
            }
            if _state_path_present(compatibility_receipt, error="LEGACY_RECOVERY_RECEIPT"):
                existing_raw = _read_private_state(compatibility_receipt, max_bytes=16_384, error="LEGACY_RECOVERY_RECEIPT")
                existing = load_closed_bytes(existing_raw, max_bytes=16_384)
                if existing_raw != canonical_bytes(existing) or set(existing) != LEGACY_RECOVERY_RECEIPT_FIELDS or existing.get("schema_version") != "claw-host-deployment-legacy-recovery-receipt-v1" or existing.get("authority") != "NONE" or existing.get("not_host_receipt") is not True:
                    raise ControllerError("LEGACY_RECOVERY_RECEIPT")
                for key, value in receipt_value.items():
                    if existing.get(key) != value:
                        raise ControllerError("LEGACY_RECOVERY_RECEIPT")
            else:
                _exclusive(compatibility_receipt, canonical_bytes(receipt_value))
            return response

    def _rollback_intent(self, transaction_id: str, host_receipt: Path) -> dict[str, object]:
        intent_path, _ = self._rollback_paths(transaction_id)
        if _state_path_present(intent_path, error="ROLLBACK_INTENT"):
            raw = _read_private_state(intent_path, max_bytes=4096, error="ROLLBACK_INTENT")
            value = load_closed_bytes(raw, max_bytes=4096)
            if raw != canonical_bytes(value):
                raise ControllerError("ROLLBACK_INTENT")
        else:
            value = {
                "schema_version": "claw-host-deployment-rollback-intent-v1",
                "transaction_id": transaction_id,
                "prior_host_receipt_sha256": hashlib.sha256(host_receipt.read_bytes()).hexdigest() if host_receipt.is_file() else None,
            }
            _exclusive(intent_path, canonical_bytes(value))
        if set(value) != {"schema_version", "transaction_id", "prior_host_receipt_sha256"} or value.get("schema_version") != "claw-host-deployment-rollback-intent-v1" or value.get("transaction_id") != transaction_id:
            raise ControllerError("ROLLBACK_INTENT")
        prior = value.get("prior_host_receipt_sha256")
        if prior is not None and (not isinstance(prior, str) or not SHA256.fullmatch(prior)):
            raise ControllerError("ROLLBACK_INTENT")
        return value

    @staticmethod
    def _verify_prior_host_receipt(intent: dict[str, object], host_receipt: Path) -> None:
        expected = intent["prior_host_receipt_sha256"]
        if expected is None:
            if host_receipt.exists():
                raise ControllerError("ROLLBACK_PRIOR_RECEIPT")
            return
        if not host_receipt.is_file() or hashlib.sha256(host_receipt.read_bytes()).hexdigest() != expected:
            raise ControllerError("ROLLBACK_PRIOR_RECEIPT")

    def _finish_rollback(self, transaction_id: str, intent: dict[str, object], host: object) -> dict[str, object]:
        journal, host_receipt, _ = self._paths(transaction_id)
        _, rollback_receipt = self._rollback_paths(transaction_id)
        journal_value = load_closed_bytes(journal.read_bytes(), max_bytes=4_194_304)
        if journal_value.get("phase") != "ROLLED_BACK" or journal_value.get("status") != "ROLLED_BACK":
            raise ControllerError("HOST_ROLLBACK_STATE")
        prior_sha = intent["prior_host_receipt_sha256"]
        if host_receipt.is_file():
            self._verify_prior_host_receipt(intent, host_receipt)
            host.durable_unlink(host_receipt)
        identity = self._identity()
        expected = {
            "expected_transaction_id": transaction_id,
            "expected_policy_sha256": hashlib.sha256(self.policy_path.read_bytes()).hexdigest(),
            "expected_closure_sha256": hashlib.sha256(self.closure_path.read_bytes()).hexdigest(),
            "expected_journal_sha256": hashlib.sha256(journal.read_bytes()).hexdigest(),
            "expected_controller_sha": str(identity["controller_sha"]),
            "expected_controller_tree": str(identity["controller_tree"]),
            "expected_prior_host_receipt_sha256": prior_sha,
        }
        if rollback_receipt.is_file():
            value = verify_rollback_receipt(load_closed_bytes(rollback_receipt.read_bytes(), max_bytes=16_384), **expected)
        else:
            value = verify_rollback_receipt({
                "schema_version": "claw-host-deployment-rollback-receipt-v1",
                "authority": "NONE",
                "not_host_receipt": True,
                "receipt_kind": "ROLLBACK",
                "transaction_id": transaction_id,
                "controller_sha": identity["controller_sha"],
                "controller_tree": identity["controller_tree"],
                "policy_sha256": expected["expected_policy_sha256"],
                "closure_sha256": expected["expected_closure_sha256"],
                "journal_sha256": expected["expected_journal_sha256"],
                "prior_host_receipt_sha256": prior_sha,
                "status": "ROLLED_BACK",
                "created_at": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
            }, **expected)
            _atomic(rollback_receipt, canonical_bytes(value))
        return self._response("rollback", transaction_id, "ROLLED_BACK", hashlib.sha256(rollback_receipt.read_bytes()).hexdigest())

    def finalize(self, request: DeploymentRequest) -> dict[str, object]:
        with self._controller_lock():
            return self._finalize_locked(request)

    def _finalize_locked(self, request: DeploymentRequest) -> dict[str, object]:
        if request.transaction_id is None:
            raise ControllerError("TRANSACTION_ID")
        host = self._host_module()
        journal_path, receipt_path, _ = self._paths(request.transaction_id)
        journal_value = load_closed_bytes(journal_path.read_bytes(), max_bytes=4_194_304)
        if journal_value.get("phase") == "ROLLED_BACK" and journal_value.get("status") == "ROLLED_BACK":
            rolled_back = self._rollback_locked(request)
            return self._response(
                "finalize", request.transaction_id, "ROLLED_BACK",
                rolled_back["receipt_sha256"],
            )
        if journal_value.get("phase") != "COMMITTED" or journal_value.get("status") != "COMMITTED":
            projection = self._runner_projection(request.github_token)
            backend = self._recovery_backend(request.transaction_id, token_reader=lambda: request.github_token)
            host.finalize(backend, host.Journal.resume(journal_path), projection)
        expected = host.receipt(self.policy_path, self.closure_path, Path(str(self._policy()["transaction_root"])) / "image.oci", journal_path, self._identity()["controller_sha"])
        try:
            from scripts.verify_claw_host_bootstrap_receipt import verify as verify_receipt
        except ModuleNotFoundError:
            from verify_claw_host_bootstrap_receipt import verify as verify_receipt
        if receipt_path.is_file():
            value = load_closed_bytes(receipt_path.read_bytes(), max_bytes=1_048_576)
            verify_receipt(value, expected)
        else:
            value = verify_receipt(expected, expected)
            _atomic(receipt_path, canonical_bytes(value))
        receipt_sha = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
        return self._response("finalize", request.transaction_id, "COMMITTED", receipt_sha)

    def status(self, request: DeploymentRequest) -> dict[str, object]:
        if request.transaction_id is None:
            raise ControllerError("TRANSACTION_ID")
        journal, receipt, _ = self._paths(request.transaction_id)
        value = load_closed_bytes(journal.read_bytes(), max_bytes=4_194_304)
        state = self._public_journal_state(value)
        if state == "ROLLED_BACK":
            receipt = journal.parent / f"{request.transaction_id}.rollback-receipt.json"
        digest = hashlib.sha256(receipt.read_bytes()).hexdigest() if receipt.is_file() else None
        return self._response("status", request.transaction_id, state, digest)

    def rollback(self, request: DeploymentRequest) -> dict[str, object]:
        with self._controller_lock():
            return self._rollback_locked(request)

    def _rollback_locked(self, request: DeploymentRequest) -> dict[str, object]:
        if request.transaction_id is None:
            raise ControllerError("TRANSACTION_ID")
        journal, receipt, _ = self._paths(request.transaction_id)
        rollback_intent, rollback_receipt = self._rollback_paths(request.transaction_id)
        journal_value = load_closed_bytes(journal.read_bytes(), max_bytes=4_194_304)
        pre_mutation_initialization = (
            journal_value.get("phase") == "PREPARED"
            and journal_value.get("status") == "OPEN"
            and journal_value.get("applied") == []
            and journal_value.get("current") is None
        )
        terminal_rollback = journal_value.get("phase") == "ROLLED_BACK" and journal_value.get("status") == "ROLLED_BACK"
        committed = journal_value.get("phase") == "COMMITTED" and journal_value.get("status") == "COMMITTED"
        if committed and not receipt.is_file():
            raise ControllerError("ROLLBACK_PRIOR_RECEIPT")
        if not committed and not terminal_rollback and receipt.exists():
            raise ControllerError("ROLLBACK_PRIOR_RECEIPT")
        rollback_intent_present = _state_path_present(rollback_intent, error="ROLLBACK_INTENT")
        if terminal_rollback and not rollback_intent_present:
            if receipt.exists():
                raise ControllerError("ROLLBACK_PRIOR_RECEIPT")
            self._host_apply_intent(request.transaction_id, create=False)
        if rollback_receipt.is_file():
            identity = self._identity()
            if not rollback_intent_present:
                raise ControllerError("ROLLBACK_INTENT")
            intent = self._rollback_intent(request.transaction_id, receipt)
            value = verify_rollback_receipt(
                load_closed_bytes(rollback_receipt.read_bytes(), max_bytes=16_384),
                expected_transaction_id=request.transaction_id,
                expected_policy_sha256=hashlib.sha256(self.policy_path.read_bytes()).hexdigest(),
                expected_closure_sha256=hashlib.sha256(self.closure_path.read_bytes()).hexdigest(),
                expected_journal_sha256=hashlib.sha256(journal.read_bytes()).hexdigest(),
                expected_controller_sha=str(identity["controller_sha"]),
                expected_controller_tree=str(identity["controller_tree"]),
                expected_prior_host_receipt_sha256=intent["prior_host_receipt_sha256"],
            )
            return self._response("rollback", request.transaction_id, str(value["status"]), hashlib.sha256(rollback_receipt.read_bytes()).hexdigest())
        intent = self._rollback_intent(request.transaction_id, receipt)
        if journal_value.get("phase") != "ROLLED_BACK" or journal_value.get("status") != "ROLLED_BACK":
            self._verify_prior_host_receipt(intent, receipt)
            host = self._host_module()
            result = host.main(self._host_args(request.transaction_id, rollback=True))
            if result == 0 and not journal.exists():
                if not pre_mutation_initialization or receipt.exists() or rollback_receipt.exists():
                    raise ControllerError("HOST_ROLLBACK_STATE")
                host.durable_unlink(rollback_intent)
                return self._response("rollback", request.transaction_id, "ROLLED_BACK")
            journal_value = load_closed_bytes(journal.read_bytes(), max_bytes=4_194_304)
            if result != 0:
                if journal_value.get("phase") == "ROLLBACK_BLOCKED" and journal_value.get("status") == "OPEN":
                    return self._response("rollback", request.transaction_id, "ROLLBACK_BLOCKED")
                raise ControllerError("HOST_ROLLBACK")
        if journal_value.get("phase") != "ROLLED_BACK" or journal_value.get("status") != "ROLLED_BACK":
            raise ControllerError("HOST_ROLLBACK_STATE")
        host = self._host_module()
        return self._finish_rollback(request.transaction_id, intent, host)

    def reconcile(self) -> None:
        with self._controller_lock():
            self._reconcile_locked()

    def _reconcile_locked(self) -> None:
        host = self._host_module()
        durable = Path(str(self._policy()["transaction_root"]))
        failures: list[str] = []
        for journal_path in sorted(durable.glob("[0-9a-f]" * 32 + ".json")):
            transaction_id = journal_path.stem
            try:
                raw = load_closed_bytes(journal_path.read_bytes(), max_bytes=4_194_304)
                if raw.get("phase") == "ROLLED_BACK" and raw.get("status") == "ROLLED_BACK":
                    response = self._rollback_locked(DeploymentRequest(
                        action="rollback", github_token=None,
                        repository="Dimkox/multi-exchange-engine",
                        transaction_id=transaction_id,
                    ))
                    if response["state"] != "ROLLED_BACK":
                        raise ControllerError("RECONCILE_ROLLBACK_STATE")
                    continue
                interrupted = {
                    "PREPARED", "VERIFYING", "ROLLING_BACK", "ROLLBACK_BLOCKED",
                }
                phase = raw.get("phase")
                if raw.get("status") == "OPEN" and (
                    phase in interrupted
                    or isinstance(phase, str) and (phase.startswith("APPLYING(") or phase.startswith("APPLIED("))
                ):
                    response = self._rollback_locked(DeploymentRequest(
                        action="rollback", github_token=None,
                        repository="Dimkox/multi-exchange-engine",
                        transaction_id=transaction_id,
                    ))
                    if response["state"] != "ROLLED_BACK":
                        raise ControllerError("RECONCILE_ROLLBACK_BLOCKED")
                    continue
                journal = host.Journal.resume(journal_path)
                if journal.value.get("phase") not in {"HOST_APPLIED_PENDING_FINALIZE", "FINALIZING", "VERIFIED"}:
                    continue
                if host.deadline_due(journal):
                    receipt = durable / f"{transaction_id}.receipt.json"
                    intent = self._rollback_intent(transaction_id, receipt)
                    if not host.reconcile_deadline(self._recovery_backend(transaction_id), journal):
                        raise ControllerError("DEADLINE_RACE")
                    self._finish_rollback(transaction_id, intent, host)
            except (OSError, ValueError, host.TxError, ControllerError):
                failures.append(transaction_id)
        if failures:
            raise ControllerError("RECONCILE_FAILED")


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) in {1, 3} and args[0] == "--recover-legacy-e872":
        try:
            if os.name != "posix" or os.geteuid() != 0:
                raise ControllerError("ROOT_REQUIRED")
            comment = Path(args[1]) if len(args) == 3 else None
            repository = Path(args[2]) if len(args) == 3 else None
            HostDeploymentRuntime().recover_legacy_terminal(comment, repository)
            return 0
        except (ContractError, ControllerError, OSError, ValueError):
            return 2
    if args == ["--reconcile"]:
        try:
            HostDeploymentRuntime().reconcile()
            return 0
        except (ControllerError, OSError, ValueError):
            return 2
    if args:
        return 2
    try:
        if os.name != "posix" or os.geteuid() != 0:
            raise ControllerError("ROOT_REQUIRED")
        inherited = socket.socket(fileno=0)
        if hasattr(socket, "SO_PEERCRED"):
            credentials = inherited.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12)
            _, uid, _ = struct.unpack("3i", credentials)
            if uid != 0:
                raise ControllerError("PEER_NOT_ROOT")
        raw = read_frame(inherited.makefile("rb"), reject_trailing=True)
        response = RequestRegistry(Path("/var/lib/mee-claw-host-deploy")).handle(
            raw, LocalActionDispatcher(HostDeploymentRuntime()),
        )
        inherited.sendall(encode_frame(canonical_bytes(response), limit=MAX_RESPONSE))
        return 0
    except (ControllerError, OSError) as exc:
        print(f"CLAW_HOST_DEPLOYMENT_CONTROLLER_ERROR:{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
