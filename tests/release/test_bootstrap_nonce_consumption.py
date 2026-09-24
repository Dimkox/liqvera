import json, subprocess, sys
from pathlib import Path

import pytest

from scripts.write_bootstrap_nonce_consumption import ConsumptionError, main, write_consumption
from scripts.verify_bootstrap_nonce_consumption import verify_consumption


def record():
    h, s = "a" * 64, "b" * 40
    return {"schema_version":"bootstrap-nonce-consumption-v1","repository":"Dimkox/multi-exchange-engine","approval_comment_id":5264584000,"approval_body_sha256":h,"nonce":"N"*43,"controller_sha":s,"controller_tree":s,"probe_pr_number":25,"probe_head_sha":s,"probe_head_tree":s,"run_id":1,"run_attempt":1,"runner_name":"claw-engine-runner","consumed_at":"2026-08-12T00:00:00Z","status":"CONSUMED"}


def test_writer_is_exclusive_closed_and_independently_verified(tmp_path):
    path=tmp_path/"ledger"/"claim.json"; write_consumption(record(),path)
    assert verify_consumption(path,record()) == record()
    with pytest.raises(ConsumptionError,match="NONCE_ALREADY_CONSUMED"): write_consumption(record(),path)
    bad={**record(),"command":"id"}
    with pytest.raises(ConsumptionError,match="UNKNOWN_FIELD"): write_consumption(bad,tmp_path/"bad")


def test_schema_is_closed_and_pr24_nonce_is_retired():
    schema=json.loads(Path("schemas/bootstrap-nonce-consumption-v1.schema.json").read_text())
    assert schema["additionalProperties"] is False
    assert schema["properties"]["runner_name"]["const"] == "claw-engine-runner"
    assert "5264583724" in Path("ci/claw/sandbox-policy.json").read_text()
    assert "RETIRED_UNUSED" in Path("ci/claw/sandbox-policy.json").read_text()


def test_host_helper_has_closed_stdin_only_cli():
    assert callable(main)
    source=Path("scripts/write_bootstrap_nonce_consumption.py").read_text()
    assert "sys.stdin.buffer.read(65537)" not in source
    assert "fcntl.flock" in source
    assert 'Path("/var/lib/mee-controller")' in source
    assert "/etc/mee-controller/github-token" not in source
    assert "verified_github_consumption" in source
    assert "run_id" in source and "run_attempt" in source


def test_runner_owned_projection_is_never_an_authority_input(tmp_path):
    import hashlib
    import scripts.write_bootstrap_nonce_consumption as writer
    claim=tmp_path/"claim.json"; claim.write_text(json.dumps(record()))
    source=Path("scripts/write_bootstrap_nonce_consumption.py").read_text()
    assert "verified_claim_path" not in source and "SUDO_UID" not in source

def test_root_helper_uses_bounded_ephemeral_stdin_token_only():
    source=Path("scripts/write_bootstrap_nonce_consumption.py").read_text()
    install=Path("ci/claw/install-controller-host-helper.sh").read_text()
    workflow=Path(".github/workflows/run-claw-sandbox-probe.yml").read_text()
    assert "/etc/mee-controller/github-token" not in source
    assert "test ! -e /etc/mee-controller/github-token" in install
    assert "sys.stdin.buffer.read(16385)" in source
    assert "EPHEMERAL_ENVELOPE_DUPLICATE" in source
    assert "| sudo -n /usr/local/libexec/mee-controller-ledger-write" in workflow
    assert "unset GITHUB_TOKEN TOKEN" in workflow
    assert "GITHUB_TOKEN" not in source
    assert "RUNNER_NAME" not in source
    assert "sudo -E" not in workflow and "--preserve-env" not in workflow

def test_real_cli_rejects_every_argument_without_reading_token():
    p=subprocess.run([sys.executable,"scripts/write_bootstrap_nonce_consumption.py","forged"],input="secret",text=True,capture_output=True)
    assert p.returncode==2 and p.stderr.strip()=="NONCE_WRITER_ERROR:ARGV_FORBIDDEN"
    assert "secret" not in p.stdout+p.stderr


def test_writer_retries_short_regular_file_writes(tmp_path,monkeypatch):
    import scripts.write_bootstrap_nonce_consumption as writer
    real=writer.os.write
    def short(fd,data): return real(fd,data[:max(1,len(data)//2)])
    monkeypatch.setattr(writer.os,"write",short)
    path=tmp_path/"claim"; writer.write_consumption(record(),path)
    assert json.loads(path.read_text())==record()
