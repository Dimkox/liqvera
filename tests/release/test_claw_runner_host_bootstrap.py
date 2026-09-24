import json
from pathlib import Path

def test_host_bootstrap_contract_is_closed_and_reversible():
    p=json.loads(Path("ci/claw/host-bootstrap-policy.json").read_text())
    assert p["os"]=={"id":"ubuntu","version_id":"24.04"}
    assert p["runner_user"]=="claw-engine-runner"
    assert p["runner_home"]=="/var/lib/claw-engine-runner"
    assert p["app_service"]=="actions.runner.Dimkox-openclaw-airgap-farm.claw-runner.service"
    closure=json.loads(Path(p["package_closure"]).read_text())
    assert len(closure["packages"])==10
    for name in ("verify-claw-engine-runner-host.sh","rollback-claw-engine-runner-host.sh"):
        text=Path("ci/claw",name).read_text()
        assert "claw-runner.service" in text and "is-active" in text
        assert "/home/pall/actions-runner" in text
    bootstrap=Path("scripts/claw_host_bootstrap_transaction.py").read_text()
    assert "useradd" in bootstrap and "subuid" in bootstrap and "subgid" in bootstrap
    assert "cp -a --reflink=auto" not in bootstrap and p["runner_tree"]=="/home/pall/actions-runner-engine"
    assert "tree_metadata_projection" in bootstrap and "restore_tree_metadata" in bootstrap
    assert "User={p['runner_user']}" in bootstrap and "XDG_RUNTIME_DIR" in bootstrap
    assert "podman info" in Path("ci/claw/verify-claw-engine-runner-host.sh").read_text()
    assert 'mv "$tree"' not in bootstrap and "rm -rf" not in bootstrap
    assert "failpoint" in bootstrap and "CREDENTIAL_STATE_MISMATCH" in bootstrap
    assert "credentials.sha256" not in bootstrap
    assert "--pull=never" in Path("ci/claw/verify-claw-engine-runner-host.sh").read_text()
    assert len(closure["packages"])==10 and all(len(x["sha256"])==64 for x in closure["packages"])
    assert p["runner_uid"]==p["runner_gid"]==980 and p["subuid_start"]==p["subgid_start"]==231072
    assert p["runner_home"] != p["runner_tree"]
    assert p["status"]=="PRE_HOST_OCI_EVIDENCE_APPROVED" and p["authority"]=="NONE"
    assert p["oci_archive_sha256"]=="2d592eff34c82eb369ba82ad0500ad4dad7263b0e86469d74f45f885579a3e08"
    approval=json.loads(Path(p["oci_evidence_approval"]).read_text())
    assert approval["v1_receipt_accepted"] is False and approval["not_host_receipt"] is True
    assert approval["source_commit"]=="3804ab99a148b134ce717fc3903895d8867f1d9f"
    assert approval["source_tree"]=="36e6198b96983a8a11197073c475190bc94d0ad3"
    assert approval["receipt_sha256"]=="502f5606c717f1c4159df46884979b565cc1a95ca9c696ccfdc9edf9612f2e43"
    assert approval["sidecar_file_sha256"]=="c193612b1bff4adb5de128a323b3de083345e8b6d241d5526f4a28ec15951a31"
    assert approval["evidence_policy_sha256"]=="53c42ec2e4b9dc8c993245170b1590444f64239adc7710cf28e9661c33daa3f4"
    for operation in ("snapshot_host","install_packages","create_identity","stop_engine","app_canary"):
        assert operation in bootstrap
    assert "for name in reversed(applied)" in bootstrap and "ROLLBACK_BLOCKED" in bootstrap

def test_installer_has_explicit_root_bash_contract():
    text=Path("ci/claw/install-controller-host-helper.sh").read_text()
    assert "INVOCATION: sudo -n bash" in text

def test_real_transaction_requires_external_v2_evidence_inputs():
 text=Path('scripts/claw_host_bootstrap_transaction.py').read_text()
 for token in ('--oci-layout','--oci-evidence-receipt','--oci-evidence-sidecar','verify_oci_evidence_approval','verify_oci('):assert token in text
 wrapper=Path('ci/claw/bootstrap-claw-engine-runner-host.sh').read_text()
 assert 'resume) test "$#" -eq 0' in wrapper and 'rollback) test "$#" -eq 0' in wrapper
 assert "credential-binding.json" in text and "RECOVERY_FROM_DURABLE_JOURNAL" not in text
