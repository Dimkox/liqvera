from pathlib import Path
import yaml

def test_phase_b_controller_is_dormant_claw_only_closed_sequence():
    text=Path(".github/workflows/run-claw-sandbox-probe.yml").read_text(); data=yaml.safe_load(text)
    job=data["jobs"]["probe"]
    assert job["runs-on"]==["self-hosted","claw","claw-engine-runner"]
    assert data["permissions"]=={"contents":"read","pull-requests":"read","actions":"read"}
    assert "repository_dispatch" in text and "run-story-1-2-phase-b-probe" in text
    ordered=["materialize_verified_source_tree.py","mee-controller-ledger-write","reconcile-owned-resources.sh","run-disposable-validation.sh","scripts.write_validation_receipt","scripts.verify_validation_receipt","scripts.write_validation_cleanup_receipt","scripts.verify_validation_cleanup_receipt"]
    assert [text.index(x) for x in ordered]==sorted(text.index(x) for x in ordered)
    assert "authority=NONE" in text
    assert "workflow_dispatch" not in text and "ubuntu-latest" not in text
    assert "--help" not in text
    for required in ("/pulls/${PR_NUMBER}", "/commits/${EXPECTED_HEAD_SHA}", "MEE_SOURCE_DIR", "MEE_OUTPUT_DIR", "MEE_RESOURCE_NAME"):
        assert required in text
    for required in ("/compare/", "/issues/comments/${APPROVAL_COMMENT_ID}", "verify_github_bootstrap_approval.py", "verify_same_repo_pr.py full", "command-manifest.json", "result.json", "rm -rf -- \"$MEE_SOURCE_DIR\" \"$MEE_OUTPUT_DIR\"", "test ! -e \"$MEE_SOURCE_DIR\""):
        assert required in text
    assert "sha256(b'phase-b-probe-v1')" not in text
    assert "sha256(b'actionlint-success')" not in text
    assert "run-name: run-story-1-2-phase-b-probe" in text and 'job_id=$(curl' in text
    cleanup=text.index('rm -rf -- "$MEE_SOURCE_DIR" "$MEE_OUTPUT_DIR"')
    receipt=text.index("scripts.write_validation_cleanup_receipt")
    assert cleanup < receipt
