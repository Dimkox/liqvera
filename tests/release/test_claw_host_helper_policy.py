import hashlib, json
from pathlib import Path


def test_host_helper_manifest_hashes_exact_source_artifacts():
    m=json.loads(Path("ci/claw/host-helper-manifest.json").read_text())
    assert m["authority"] == "NONE"
    for item in m["artifacts"]:
        data=Path(item["source"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == item["sha256"]
    assert m["state_retention"] == "PRESERVE_FORENSIC_LEDGER"

def test_helper_install_is_post_host_receipt_and_emits_distinct_receipt():
    text=Path('ci/claw/install-controller-host-helper.sh').read_text()
    assert text.index('verify_claw_host_bootstrap_receipt.py') < text.index('helper-receipt.json')
    assert 'claw-helper-install-receipt-v1' in text and 'VERIFIED_POST_HOST_RECEIPT' in text


def test_sudoers_is_closed_without_shell_or_wildcards():
    text=Path("ci/claw/sudoers/mee-controller-ledger").read_text()
    assert "NOPASSWD:" in text
    assert "*" not in text and "/bin/sh" not in text
    assert text.strip().endswith('NOPASSWD: /usr/local/libexec/mee-controller-ledger-write ""')
    install=Path("ci/claw/install-controller-host-helper.sh").read_text()
    for token in ("sha256sum -c", "visudo -cf", "claw_helper_install_transaction.py", "helper-install-journal.json"):
        assert token in install
