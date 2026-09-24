from pathlib import Path


def test_reconciler_is_label_and_ledger_scoped():
    text=Path("ci/claw/reconcile-owned-resources.sh").read_text()
    assert "io.mee.controller=story-1-2" in text
    assert "/var/lib/mee-controller" in text
    assert "podman pod ps" in text
    assert "podman network ls" in text
    assert "podman volume ls" in text
    assert "mee.repository_sha256" in text and "mee.run_id" in text and "mee.source_sha" in text
    assert "resources.jsonl" in text
    assert "podman system prune" not in text
    assert "podman rm -a" not in text
    assert "docker" not in text


def test_reconcile_workflow_is_claw_only_and_authority_none():
    text=Path(".github/workflows/reconcile-claw-sandboxes.yml").read_text()
    assert "[self-hosted, claw, claw-engine-runner]" in text
    assert "RUNNER_NAME" in text and "claw-engine-runner" in text
    assert "authority=NONE" in text
    assert "RUNNER_NAME: claw-engine-runner" in text
    assert "ubuntu-latest" not in text
