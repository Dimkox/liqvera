"""Offline regression: effective TLS trust must exclude the compromised emSign root."""

import argparse
import hashlib
import importlib.util
import json
import os
import re
import ssl
from pathlib import Path

DISTRUSTED = {
    "86a1ecba089c4a8d3bbe2734c612ba341d813e043cf9e8a862cd5c57a36bbe6b",
    "d7a7a0fb5d7e2731d771e9484ebcdef71d5f0c3e0a2948782bc83ee0ea699ef4",
    "7dd78d5f4f13459a83dff9abbba62edbaf6f2d102bf257fd712f4d9f2746ed8d",
    "f2edaaff3d9b701fb4d14c9f285f8c0bad90fc3bcc1fa07d47f4718edaba34a5",
}


def inspect_store(name, cafile=None):
    context = ssl.create_default_context(cafile=cafile)
    roots = context.get_ca_certs(binary_form=True)
    fingerprints = {hashlib.sha256(root).hexdigest() for root in roots}
    if cafile is None:
        # OpenSSL loads hashed-directory certificates lazily. get_ca_certs()
        # alone misses these additional anchors until a handshake needs them.
        paths = ssl.get_default_verify_paths()
        directories = os.environ.get(paths.openssl_capath_env, paths.openssl_capath)
        for directory in directories.split(os.pathsep):
            path = Path(directory)
            if not directory or not path.is_dir():
                continue
            for entry in path.iterdir():
                if not re.fullmatch(r"[0-9a-fA-F]{8}\.\d+", entry.name):
                    continue
                data = entry.read_bytes()
                if b"-----BEGIN CERTIFICATE-----" in data:
                    certificates = re.findall(
                        rb"-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----", data, re.S
                    )
                    for certificate in certificates:
                        der = ssl.PEM_cert_to_DER_cert(certificate.decode("ascii"))
                        fingerprints.add(hashlib.sha256(der).hexdigest())
                else:
                    fingerprints.add(hashlib.sha256(data).hexdigest())
    assert len(fingerprints) > 50, f"{name}: trust store is unexpectedly empty or truncated"
    assert context.verify_mode == ssl.CERT_REQUIRED and context.check_hostname
    assert not (fingerprints & DISTRUSTED), f"{name}: compromised emSign trust remains"
    return {"store": name, "roots": len(fingerprints), "compromised_roots": 0}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cafile")
    parser.add_argument("--certifi", action="store_true")
    parser.add_argument("--pip", action="store_true")
    parser.add_argument("--without-pip", action="store_true")
    args = parser.parse_args()
    results = [inspect_store("explicit CA bundle" if args.cafile else "system", args.cafile)]
    if args.certifi:
        import certifi

        results.append(inspect_store("certifi " + certifi.__version__, certifi.where()))
    if args.pip:
        import pip
        from pip._internal.commands import create_command
        from pip._vendor import certifi as vendored_certifi

        results.append(inspect_store("pip " + pip.__version__, vendored_certifi.where()))
        command = create_command("install")
        options, _ = command.parse_args([])
        assert not options.trusted_hosts, "pip must not bypass certificate checks for trusted hosts"
        assert not options.cert, "Unexpected pip CA override requires separate verification"
        if "legacy-certs" not in options.deprecated_features_enabled:
            # Modern pip merges its bundle with system trust, even when a caller
            # checks an explicit CA file above. Verify that additional trust too.
            results.append(inspect_store("pip additional system trust"))
    if args.without_pip:
        assert importlib.util.find_spec("pip") is None, "pip remains in the runtime image"
        assert importlib.util.find_spec("ensurepip") is None, "ensurepip remains in the runtime image"
    print(json.dumps({"tls_verification": "required", "results": results}))


if __name__ == "__main__":
    main()
