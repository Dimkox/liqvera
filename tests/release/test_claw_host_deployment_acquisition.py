from __future__ import annotations

import datetime as dt
import hashlib
import io
import json
from pathlib import Path
import tarfile

import pytest

from scripts.claw_host_deployment_controller import (
    AcquisitionError,
    _bounded_command,
    _extract_oci_layout_archive,
    acquire_begin_inputs,
    stage_approved_assets,
    verify_staged_inputs,
)
from scripts.claw_host_deployment_contract import canonical_bytes, verify_request


def test_bounded_command_returns_strict_stdout_and_rejects_failure_and_oversize():
    assert _bounded_command(["/usr/bin/printf", "Package\\nVersion\\nArchitecture\\n"]) == "Package\nVersion\nArchitecture"
    with pytest.raises(AcquisitionError, match="INPUT_VERIFY_COMMAND"):
        _bounded_command(["/usr/bin/false"])
    with pytest.raises(AcquisitionError, match="INPUT_VERIFY_COMMAND"):
        _bounded_command(["/usr/bin/printf", "x" * 4097])


def _asset(role: str, name: str, raw: bytes, asset_id: int) -> dict[str, object]:
    return {
        "id": asset_id,
        "name": name,
        "role": role,
        "size": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


class FakeAssets:
    def __init__(self, payloads: dict[int, bytes], *, chunk: int = 7) -> None:
        self.payloads = payloads
        self.chunk = chunk

    def iter_asset(self, asset_id: int):
        raw = self.payloads[asset_id]
        for offset in range(0, len(raw), self.chunk):
            yield raw[offset : offset + self.chunk]


def _approved_set(host_inventory_raw: bytes = b'{"schema_version":"fixture"}\n') -> tuple[list[dict[str, object]], dict[int, bytes], bytes]:
    payloads: dict[int, bytes] = {}
    assets: list[dict[str, object]] = []
    asset_id = 100
    for name in ("conmon", "fuse-overlayfs", "golang-github-containers-common", "golang-github-containers-image", "libslirp0", "libsubid4", "netavark", "podman", "slirp4netns", "uidmap"):
        raw = ("deb:" + name).encode()
        payloads[asset_id] = raw
        assets.append(_asset("deb:" + name, name + ".deb", raw, asset_id))
        asset_id += 1
    for role, name in (
        ("host_inventory", "claw-host-inventory.json"),
        ("oci_archive", "actionlint.tar"),
        ("oci_layout", "actionlint-oci-layout.tar"),
        ("oci_receipt", "actionlint.evidence-v2.json"),
        ("oci_sidecar", "actionlint.evidence-v2.json.sha256"),
    ):
        raw = host_inventory_raw if role == "host_inventory" else (role + ":bytes").encode()
        payloads[asset_id] = raw
        assets.append(_asset(role, name, raw, asset_id))
        asset_id += 1
    projected = [dict(item) for item in assets]
    manifest = (json.dumps({"schema_version": "claw-host-input-bundle-v1", "assets": projected}, sort_keys=True, separators=(",", ":")) + "\n").encode()
    payloads[asset_id] = manifest
    assets.append(_asset("bundle_manifest", "claw-host-input-bundle.json", manifest, asset_id))
    return sorted(assets, key=lambda item: (item["role"], item["name"], item["id"])), payloads, manifest


def test_exact_assets_are_staged_root_private_and_manifest_bound(tmp_path: Path) -> None:
    assets, payloads, manifest = _approved_set()
    result = stage_approved_assets(
        FakeAssets(payloads),
        assets,
        transaction_root=tmp_path / ("a" * 32),
        expected_bundle_manifest_sha256=hashlib.sha256(manifest).hexdigest(),
    )
    assert result["schema_version"] == "claw-host-staged-inputs-v1"
    assert [item["role"] for item in result["assets"]] == [item["role"] for item in assets]
    assert (tmp_path / ("a" * 32) / "inputs" / "manifest.json").read_bytes().endswith(b"\n")
    for item in result["assets"]:
        path = tmp_path / ("a" * 32) / "inputs" / str(item["staged_name"])
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]


@pytest.mark.parametrize("mode", ["extra", "missing", "duplicate_role"])
def test_asset_set_is_exact_before_any_write(tmp_path: Path, mode: str) -> None:
    assets, payloads, manifest = _approved_set()
    if mode == "extra":
        assets.append(_asset("deb:extra", "extra.deb", b"extra", 999))
        payloads[999] = b"extra"
    elif mode == "missing":
        assets.pop(0)
    else:
        assets[1] = dict(assets[1], role=assets[0]["role"])
    with pytest.raises(AcquisitionError, match="ASSET_SET"):
        stage_approved_assets(FakeAssets(payloads), assets, transaction_root=tmp_path / ("b" * 32), expected_bundle_manifest_sha256=hashlib.sha256(manifest).hexdigest())
    assert not (tmp_path / ("b" * 32) / "inputs").exists()


@pytest.mark.parametrize("mode,error", [("size", "ASSET_SIZE"), ("digest", "ASSET_DIGEST"), ("stream", "ASSET_STREAM")])
def test_download_failure_removes_partial_input(tmp_path: Path, mode: str, error: str) -> None:
    assets, payloads, manifest = _approved_set()
    victim = next(item for item in assets if item["role"] == "oci_receipt")
    if mode == "size":
        payloads[int(victim["id"])] += b"x"
    elif mode == "digest":
        replacement = bytearray(payloads[int(victim["id"])])
        replacement[0] ^= 1
        payloads[int(victim["id"])] = bytes(replacement)
    else:
        class Broken(FakeAssets):
            def iter_asset(self, asset_id: int):
                yield b"one"
                raise OSError("network")
        client = Broken(payloads)
        with pytest.raises(AcquisitionError, match=error):
            stage_approved_assets(client, assets, transaction_root=tmp_path / ("c" * 32), expected_bundle_manifest_sha256=hashlib.sha256(manifest).hexdigest())
        assert not list((tmp_path / ("c" * 32)).rglob("*.part"))
        return
    with pytest.raises(AcquisitionError, match=error):
        stage_approved_assets(FakeAssets(payloads), assets, transaction_root=tmp_path / ("c" * 32), expected_bundle_manifest_sha256=hashlib.sha256(manifest).hexdigest())
    assert not list((tmp_path / ("c" * 32)).rglob("*.part"))


def test_bundle_manifest_rejects_reordered_or_unapproved_projection(tmp_path: Path) -> None:
    assets, payloads, manifest = _approved_set()
    manifest_asset = next(item for item in assets if item["role"] == "bundle_manifest")
    bad = json.loads(manifest)
    bad["assets"][0]["size"] += 1
    raw = (json.dumps(bad, sort_keys=True, separators=(",", ":")) + "\n").encode()
    payloads[int(manifest_asset["id"])] = raw
    manifest_asset["size"] = len(raw)
    manifest_asset["sha256"] = hashlib.sha256(raw).hexdigest()
    with pytest.raises(AcquisitionError, match="BUNDLE_MANIFEST"):
        stage_approved_assets(FakeAssets(payloads), assets, transaction_root=tmp_path / ("d" * 32), expected_bundle_manifest_sha256=manifest_asset["sha256"])


def test_installed_entrypoints_pin_claw_python_314() -> None:
    root = Path(__file__).resolve().parents[2]
    assert (root / "scripts/claw_host_deployment_controller.py").read_text().startswith("#!/usr/bin/python3.14\n")
    assert (root / "scripts/claw_host_deployment_client.py").read_text().startswith("#!/usr/bin/python3.14\n")
    assert "ExecStart=/usr/bin/python3.14 /usr/local/libexec/mee-claw-host-deploy" in (root / "ci/claw/systemd/mee-claw-host-deploy@.service").read_text()
    installer = (root / "ci/claw/install-host-deployment-controller.sh").read_text()
    assert installer.count("/usr/bin/python3.14") == 2
    assert "exec python3 " not in installer


def _layout_archive(path: Path, *, unsafe_name: str | None = None, link: bool = False) -> None:
    with tarfile.open(path, "w") as archive:
        entries = {
            "oci-layout/oci-layout": b'{"imageLayoutVersion":"1.0.0"}',
            "oci-layout/index.json": b'{"schemaVersion":2,"manifests":[]}',
            "oci-layout/blobs/sha256/" + "a" * 64: b"blob",
        }
        if unsafe_name:
            entries[unsafe_name] = b"escape"
        for name, raw in entries.items():
            info = tarfile.TarInfo(name)
            info.size = len(raw)
            archive.addfile(info, io.BytesIO(raw))
        if link:
            info = tarfile.TarInfo("oci-layout/link")
            info.type = tarfile.SYMTYPE
            info.linkname = "/etc/passwd"
            archive.addfile(info)


def test_oci_layout_archive_extracts_only_closed_regular_tree(tmp_path: Path) -> None:
    archive = tmp_path / "layout.tar"
    _layout_archive(archive)
    root = _extract_oci_layout_archive(archive, tmp_path / "out")
    assert root.name == "oci-layout"
    assert (root / "index.json").is_file()


@pytest.mark.parametrize("unsafe_name,link", [("../escape", False), ("/absolute", False), (None, True)])
def test_oci_layout_archive_rejects_escape_and_links(tmp_path: Path, unsafe_name: str | None, link: bool) -> None:
    archive = tmp_path / "layout.tar"
    _layout_archive(archive, unsafe_name=unsafe_name, link=link)
    with pytest.raises(AcquisitionError, match="OCI_LAYOUT_ARCHIVE"):
        _extract_oci_layout_archive(archive, tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_staged_input_verifier_passes_physical_and_logical_approval_paths(tmp_path: Path, monkeypatch) -> None:
    import scripts.claw_host_deployment_controller as controller
    import scripts.verify_oci_evidence_approval as approval_verifier

    packages = [
        {"name": f"package-{index}", "version": "1", "architecture": "amd64", "sha256": f"{index:064x}"}
        for index in range(10)
    ]
    archive_sha = "f" * 64
    policy = tmp_path / "policy.json"
    closure = tmp_path / "closure.json"
    policy.write_text(json.dumps({"oci_archive_sha256": archive_sha}))
    closure.write_text(json.dumps({"packages": packages}))
    assets = [
        {"id": index, "name": item["name"] + ".deb", "role": "deb:" + item["name"], "size": 1, "sha256": item["sha256"], "staged_name": item["name"] + ".deb"}
        for index, item in enumerate(packages)
    ]
    assets.extend(
        {"id": 100 + index, "name": role, "role": role, "size": 1, "sha256": archive_sha if role == "oci_archive" else "e" * 64, "staged_name": role}
        for index, role in enumerate(("oci_archive", "oci_layout", "oci_receipt", "oci_sidecar", "bundle_manifest"))
    )
    seen: list[str] = []
    original_is_file = Path.is_file
    monkeypatch.setattr(
        controller,
        "_bounded_command",
        lambda argv: "\n".join((f"Package: {Path(argv[2]).stem}", "Version: 1", "Architecture: amd64")),
    )
    monkeypatch.setattr(controller, "_extract_oci_layout_archive", lambda _archive, destination: destination / "oci-layout")
    monkeypatch.setattr(Path, "is_file", lambda self: True if str(self) == "/usr/local/libexec/mee-claw-host-deploy-lib/oci-evidence-approval.json" else original_is_file(self))
    monkeypatch.setattr(approval_verifier, "main", lambda argv: seen.extend(argv) or 0)

    verify_staged_inputs({"assets": assets}, tmp_path, policy, closure, {"oci_archive_sha256": archive_sha})

    assert seen[seen.index("--approval") + 1] == "/usr/local/libexec/mee-claw-host-deploy-lib/oci-evidence-approval.json"
    assert seen[seen.index("--approval-policy-path") + 1] == "ci/claw/oci-evidence-approval.json"


def _begin_fixture(tmp_path: Path):
    observation = {
        "repository": "Dimkox/multi-exchange-engine",
        "controller_sha": "1" * 40,
        "controller_tree": "2" * 40,
        "collection_mode": "DIRECT_CLAW",
        "collector_path": "scripts/collect_claw_host_inventory.py",
        "collector_sha256": "3" * 64,
        "collection_id": "7" * 32,
        "runner_name": "claw-engine-runner",
        "observed_at": "2026-08-13T09:00:00Z",
        "preflight_blockers": [],
    }
    observation_raw = canonical_bytes(observation)
    observation_sha = hashlib.sha256(observation_raw).hexdigest()
    assets, payloads, manifest = _approved_set(observation_raw)
    body = {
        "schema_version": "claw-host-deployment-approval-v1",
        "decision": "APPROVE_CLAW_HOST_TRANSITION",
        "repository": "Dimkox/multi-exchange-engine",
        "source_sha": "a" * 40,
        "source_tree": "b" * 40,
        "policy_sha256": hashlib.sha256(b"policy").hexdigest(),
        "closure_sha256": hashlib.sha256(b"closure").hexdigest(),
        "oci_archive_sha256": next(item["sha256"] for item in assets if item["role"] == "oci_archive"),
        "oci_archive_size": next(item["size"] for item in assets if item["role"] == "oci_archive"),
        "oci_archive_format": "docker-archive",
        "image_manifest_digest": "sha256:" + "4" * 64,
        "host_inventory_sha256": observation_sha,
        "host_inventory_observed_at": observation["observed_at"],
        "bundle_manifest_sha256": hashlib.sha256(manifest).hexdigest(),
        "release_id": 900,
        "release_tag": "claw-host-inputs-2026-08-13",
        "assets": assets,
        "rollback_deadline_seconds": 900,
        "expires_at": "2026-08-13T10:00:00Z",
        "nonce": "A" * 43,
    }
    comment = {
        "id": 800,
        "user": {"login": "Dimkox", "id": 42},
        "author_association": "OWNER",
        "created_at": "2026-08-13T09:15:00Z",
        "updated_at": "2026-08-13T09:15:00Z",
        "issue_url": "https://api.github.com/repos/Dimkox/multi-exchange-engine/issues/34",
        "html_url": "https://github.com/Dimkox/multi-exchange-engine/issues/34#issuecomment-800",
        "body": canonical_bytes(body).decode().rstrip("\n"),
    }
    release = {"id": 900, "tag_name": body["release_tag"], "draft": True, "prerelease": False, "assets": [{"id": x["id"], "name": x["name"], "size": x["size"]} for x in assets]}
    api = {
        "/repos/Dimkox/multi-exchange-engine": {"full_name": body["repository"], "default_branch": "main", "owner": {"login": "Dimkox", "id": 42}},
        "/repos/Dimkox/multi-exchange-engine/issues/comments/800": comment,
        "/repos/Dimkox/multi-exchange-engine/releases/900": release,
    }

    class FullFake(FakeAssets):
        def get_json(self, path: str):
            return api[path]

    policy = tmp_path / "policy.json"
    closure = tmp_path / "closure.json"
    policy.write_bytes(b"policy")
    closure.write_bytes(b"closure")
    request = verify_request({"schema_version": "claw-host-deployment-request-v1", "action": "begin", "github_token": "sentinel-ephemeral-token", "repository": body["repository"], "approval_comment_id": 800, "release_id": 900, "transaction_id": None}, expected_action="begin")
    installed = {"schema_version": "claw-host-deployment-installed-v1", "repository": body["repository"], "default_branch": "main", "controller_sha": body["source_sha"], "controller_tree": body["source_tree"]}
    return FullFake(payloads), request, installed, policy, closure, api


def test_full_begin_acquisition_authenticates_projection_before_staging(tmp_path: Path) -> None:
    client, request, installed, policy, closure, _ = _begin_fixture(tmp_path)
    seen: dict[str, object] = {}
    result = acquire_begin_inputs(
        client,
        request=request,
        installed_identity=installed,
        policy_path=policy,
        closure_path=closure,
        transaction_root=tmp_path / ("e" * 32),
        now=dt.datetime(2026, 8, 13, 9, 30, tzinfo=dt.timezone.utc),
        observation_verifier=lambda value, _p, _c, expected: seen.update(value=value, expected=expected),
        staged_input_verifier=lambda *_args, **_kwargs: seen.update(staged=True),
    )
    assert result["transaction_id"] == "e" * 32
    assert seen["staged"] is True
    assert seen["expected"]["collector_sha256"] == "3" * 64
    assert "sentinel-ephemeral-token" not in json.dumps(result)
    assert "sentinel-ephemeral-token" not in "".join(path.read_text(errors="ignore") for path in (tmp_path / ("e" * 32)).rglob("*") if path.is_file())
    persisted = (tmp_path / ("e" * 32) / "inputs" / "manifest.json").read_bytes()
    assert b'"approval_nonce"' not in persisted
    assert b"A" * 43 not in persisted


def test_full_begin_rejects_inventory_asset_hash_swap(tmp_path: Path) -> None:
    client, request, installed, policy, closure, _ = _begin_fixture(tmp_path)
    inventory = next(item for item in json.loads(client.get_json("/repos/Dimkox/multi-exchange-engine/issues/comments/800")["body"])["assets"] if item["role"] == "host_inventory")
    client.payloads[int(inventory["id"])] += b"swap"
    with pytest.raises(AcquisitionError, match="ASSET_SIZE"):
        acquire_begin_inputs(client, request=request, installed_identity=installed, policy_path=policy, closure_path=closure, transaction_root=tmp_path / ("f" * 32), now=dt.datetime(2026, 8, 13, 9, 30, tzinfo=dt.timezone.utc), observation_verifier=lambda *_args: None, staged_input_verifier=lambda *_args: None)
