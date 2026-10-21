"""Reject the public compromised root even when OpenSSL loads it lazily.

The fixture is a public CA certificate, contains no private key, and is never
trusted outside a temporary offline test process.
"""

import os
import subprocess
import sys
from pathlib import Path

import certifi
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "deploy/security/check-tls-trust.py"
INCIDENT = ROOT / "deploy/security/fixtures/emsign-ecc-root-ca-g3.pem"


@pytest.mark.parametrize("location", ["clean", "file", "directory", "directory-list"])
def test_compromised_root_is_rejected_on_every_openssl_lookup_path(tmp_path, location):
    bundle = tmp_path / "roots.pem"
    bundle.write_bytes(Path(certifi.where()).read_bytes())
    directory = tmp_path / "certs"
    directory.mkdir()
    if location == "file":
        bundle.write_bytes(bundle.read_bytes() + INCIDENT.read_bytes())
    if location in {"directory", "directory-list"}:
        # Actual OpenSSL subject_hash for this public root, also used by c_rehash.
        (directory / "14bc7599.0").write_bytes(INCIDENT.read_bytes())
    capath = str(directory)
    if location == "directory-list":
        empty = tmp_path / "empty"
        empty.mkdir()
        capath = str(empty) + os.pathsep + capath
    env = {key: os.environ[key] for key in ["PATH", "HOME"] if key in os.environ}
    env.update(SSL_CERT_FILE=str(bundle), SSL_CERT_DIR=capath)
    result = subprocess.run(
        [sys.executable, str(SCRIPT)], env=env, capture_output=True, text=True, timeout=10
    )
    if location == "clean":
        assert result.returncode == 0, result.stderr
    else:
        assert result.returncode != 0
        assert "compromised emSign trust remains" in result.stderr
