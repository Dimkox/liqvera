from pathlib import Path
import re
import subprocess

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_controller_workflow_is_claw_only_pinned_and_fused_materialization_only():
    path = ROOT / ".github/workflows/validate-pr-on-claw.yml"
    source = path.read_text()
    data = yaml.safe_load(source)
    assert data["permissions"] == {"contents": "read", "pull-requests": "read"}
    assert all(job["runs-on"] == ["self-hosted", "claw", "claw-engine-runner"] for job in data["jobs"].values())
    for use in re.findall(r"uses:\s*([^\s#]+)", source):
        assert re.search(r"@[0-9a-f]{40}$", use)
    forbidden = ["pip install", "pytest", "unittest", "npm ", "go test", "docker ", "podman ", "deploy", "private api", "live trading"]
    executable_source=re.sub(r"--allowed-path\s+[^\s\\]+", "", source).casefold()
    assert not [token for token in forbidden if token in executable_source]
    assert "persist-credentials: false" in source
    assert "scripts/materialize_verified_source_tree.py" in source


def test_controller_payload_has_no_command_selection():
    source = (ROOT / ".github/workflows/validate-pr-on-claw.yml").read_text().casefold()
    assert "client_payload.command" not in source
    assert "client_payload.script" not in source


def test_legacy_bootstrap_does_not_execute_story_1_1_pr_code():
    source = (ROOT / ".github/workflows/verify-a2-pr-on-claw.yml").read_text()
    assert "tests/release/test_claw_source_controller_policy.py" not in source
    assert "actionlint .github/workflows/validate-pr-on-claw.yml" not in source
    assert "BOOTSTRAP_SCOPE: TRANSITIONAL_BOOTSTRAP_DIAGNOSTIC_ONLY" in source
    assert "upload-artifact" not in source
    assert "verification.log" not in source


def test_owner_comment_approval_precedes_materialization_and_cleanup_precedes_observation():
    source = (ROOT / ".github/workflows/validate-pr-on-claw.yml").read_text()
    assert source.index("Verify exact owner approval comment") < source.index("Fused fetch verify and atomic extract exact source")
    assert source.index("Prove source cleanup") < source.index("Write non-authoritative materialization observation")
    assert "approval_comment_id" in source
    assert "/issues/comments/" in source
    assert "/pulls/${PR_NUMBER}/reviews/" not in source
    assert "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a" in source
    assert '"actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a"' in source
    assert "if: always()" in source


def test_source_controller_allowed_paths_equal_current_pr_change_set():
    source=(ROOT/".github/workflows/validate-pr-on-claw.yml").read_text()
    allowed=sorted(re.findall(r"--allowed-path\s+([^\s\\]+)",source))
    # The authenticated API returns this PR's changed paths, not the cumulative
    # path set since the historical TOFU bootstrap. Bind the source controller
    # to the exact landed PR #43 head; deleted paths would remain visible in
    # this diff and therefore remain part of the authenticated API path set.
    changed=subprocess.run(["git","diff","--name-only","1e879f91a98651ca75bee2ed4cee1c2b35084cb6"],cwd=ROOT,check=True,capture_output=True,text=True).stdout.splitlines()
    # Keep the BMAD/Superpowers installed approval-path synchronization scope
    # bounded while exact changed-set equality below remains the authority.
    assert len(allowed) <= 128
    assert len(allowed) == len(set(allowed))
    assert allowed == sorted(changed)


def test_story_documents_tofu_landing_without_impossible_prelanding_self_validation():
    story=(ROOT/"docs/implementation/1-1-bootstrap-trusted-default-branch-pr-identity-controller.md").read_text()
    handoff=(ROOT/"handoff.md").read_text()
    required=["TOFU_SOURCE_INSTALL", "exact 57-path", "authority=NONE", "Story 1.2", "5264583724", "RETIRED_UNUSED"]
    assert all(token in story for token in required)
    assert all(token in handoff for token in required)
    assert "exact-SHA Claw evidence and landing approval remain blocked" not in story
    assert "exact-SHA Claw and landing review remain pending" not in story
    assert "first exact-SHA Claw/actionlint/sandbox self-validation" in story
    epics=(ROOT/"docs/planning/epics.md").read_text(encoding="utf-8")
    stale=["bootstrap Claw run, malicious identity/archive fixtures, actionlint", "No success is claimed until the exact PR SHA has a Claw run", "pinned actionlint/action policy and `git diff --check`; record that merge remains RED and request"]
    assert not [phrase for phrase in stale if phrase in story or phrase in handoff or phrase in epics]
    assert "Story 1.1 local/landing success" in story
    assert "Story 1.2 authoritative success" in story


def test_actionlint_knows_every_claw_runner_label():
    config = yaml.safe_load((ROOT / ".github/actionlint.yaml").read_text())
    assert config["self-hosted-runner"]["labels"] == ["claw", "claw-engine-runner"]
