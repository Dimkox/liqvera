from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError


ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "installer" / "schemas"
CONFIG = ROOT / "installer" / "config"
HEX40 = "1" * 40
HEX64 = "a" * 64

ERROR_CODES = {
    "UNSUPPORTED_LINUX",
    "DEPENDENCY_MISSING",
    "UNSAFE_INSTALL_ROOT",
    "PORT_OCCUPIED",
    "RELEASE_DIGEST_MISMATCH",
    "ARCHIVE_INVALID",
    "CONFIG_INVALID",
    "SECRET_REFERENCE_INVALID",
    "MIGRATION_MISMATCH",
    "HEALTH_TIMEOUT",
    "ROLLBACK_RESTORE_REQUIRED",
    "PURGE_CONFIRMATION_REQUIRED",
}

MIGRATIONS = [
    ("001_ledger.sql", "bc127e55c876961112f33ca2abdfac01827769d6156ddba2f42856d070c75b3b"),
    ("002_fix_immutable_ledger_identity.sql", "981f48215e64fdd0fb72be5a6df78238cf8050de722adb454b4e28b1940ccbcb"),
    ("003_live_grant_consumption.sql", "bbedff6137a648166b77233c56a466e46247480b404b8829b64f29123109bcf0"),
    ("004_receipt_confirmation_provenance.sql", "96bba00d344d81670a4c0f8741186004910e959f374ecd77ce78268d52fd465a"),
    ("005_receipt_confirmation_count.sql", "e99e5cffab60c08dfb1cd73d13caf2915f31aec542c26c87b016d0e125a23b11"),
]


def load_schema(name: str) -> dict[str, object]:
    schema = json.loads((SCHEMAS / name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["additionalProperties"] is False
    return schema


def assert_rejected(schema: dict[str, object], value: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(value)


def release_manifest() -> dict[str, object]:
    return {
        "schema_version": "liqvera-installer-release/v1",
        "product_version": "0.0.2",
        "git_commit": HEX40,
        "git_tree": "2" * 40,
        "archive_sha256": HEX64,
        "compose_sha256": "b" * 64,
        "images": {
            "edge": f"ghcr.io/dimkox/liqvera-edge@sha256:{'1' * 64}",
            "web": f"ghcr.io/dimkox/liqvera-web@sha256:{'2' * 64}",
            "gateway": f"ghcr.io/dimkox/liqvera-gateway@sha256:{'3' * 64}",
            "capture": f"ghcr.io/dimkox/liqvera-capture@sha256:{'4' * 64}",
            "report": f"ghcr.io/dimkox/liqvera-report@sha256:{'5' * 64}",
            "postgres": f"postgres@sha256:{'6' * 64}",
        },
        "migrations": [{"name": name, "sha256": digest} for name, digest in MIGRATIONS],
        "supported_linux": {
            "architectures": ["amd64", "arm64"],
            "distributions": ["ubuntu", "debian", "fedora", "rhel"],
        },
    }


def install_config() -> dict[str, object]:
    return {
        "schema_version": "liqvera-install-config/v1",
        "chain_id": 31611,
        "payment_enabled": False,
        "source_mode": "shadow",
        "ports": {
            "web": {"host": "127.0.0.1", "port": 3000},
            "gateway": {"host": "127.0.0.1", "port": 8080},
            "metrics": {"host": "127.0.0.1", "port": 9090},
        },
        "secret_files": {
            "DATABASE_PASSWORD_FILE": "/run/secrets/liqvera_database_password",
        },
    }


def install_state() -> dict[str, object]:
    return {
        "schema_version": "liqvera-install-state/v1",
        "product_version": "0.0.2",
        "release_sha256": HEX64,
        "git_commit": HEX40,
        "git_tree": "2" * 40,
        "install_root": "/srv/liqvera",
        "compose_project": "liqvera-local",
        "linux": {"distribution": "ubuntu", "architecture": "amd64"},
        "docker": {"engine_version": "27.5.1", "compose_version": "2.32.4"},
        "ports": {"web": 3000, "gateway": 8080, "metrics": 9090},
        "last_completed_phase": "CONFIGURED",
        "last_error": None,
        "created_at": "2026-09-29T00:00:00Z",
        "updated_at": "2026-09-29T00:00:00Z",
    }


def test_release_manifest_is_closed_and_binds_exact_release_inputs() -> None:
    schema = load_schema("release-manifest.schema.json")
    value = release_manifest()
    Draft202012Validator(schema).validate(value)

    for mutation in (
        {**value, "product_version": "0.0.1"},
        {**value, "archive_sha256": f"{HEX64}\n"},
        {**value, "images": {**value["images"], "web": "liqvera-web:latest"}},
        {**value, "migrations": value["migrations"][:-1]},
        {**value, "unexpected": True},
    ):
        assert_rejected(schema, mutation)

    wrong_order = {**value, "migrations": list(reversed(value["migrations"]))}
    assert_rejected(schema, wrong_order)


def test_install_config_enforces_safe_defaults_and_named_secret_files() -> None:
    schema = load_schema("config.schema.json")
    value = install_config()
    Draft202012Validator(schema).validate(value)

    for mutation in (
        {**value, "chain_id": 1},
        {**value, "payment_enabled": True},
        {**value, "source_mode": "live"},
        {**value, "ports": {**value["ports"], "web": {"host": "0.0.0.0", "port": 3000}}},
        {**value, "secret_files": {"DATABASE_PASSWORD": "plaintext"}},
        {**value, "FREE_FORM_ENV": "unsafe"},
    ):
        assert_rejected(schema, mutation)


def test_install_state_is_closed_and_uses_only_exact_error_codes() -> None:
    schema = load_schema("install-state.schema.json")
    value = install_state()
    Draft202012Validator(schema).validate(value)

    accepted = set()
    for code in ERROR_CODES:
        candidate = {**value, "last_error": code}
        Draft202012Validator(schema).validate(candidate)
        accepted.add(code)
    assert accepted == ERROR_CODES

    assert_rejected(schema, {**value, "last_error": "UNKNOWN_ERROR"})
    assert_rejected(schema, {**value, "release_sha256": HEX64.upper()})
    assert_rejected(schema, {**value, "secret": "must-not-exist"})


def test_env_templates_contain_only_closed_non_secret_defaults_and_file_references() -> None:
    expected = {
        "liqvera.env.template": {
            "LIQVERA_CHAIN_ID": "31611",
            "LIQVERA_PAYMENT_ENABLED": "false",
            "LIQVERA_SOURCE_MODE": "shadow",
            "DATABASE_PASSWORD_FILE": "/run/secrets/liqvera_database_password",
        },
        "ports.env.template": {
            "LIQVERA_WEB_HOST": "127.0.0.1",
            "LIQVERA_WEB_PORT": "3000",
            "LIQVERA_GATEWAY_HOST": "127.0.0.1",
            "LIQVERA_GATEWAY_PORT": "8080",
            "LIQVERA_METRICS_HOST": "127.0.0.1",
            "LIQVERA_METRICS_PORT": "9090",
        },
    }

    for name, wanted in expected.items():
        parsed = {}
        for line in (CONFIG / name).read_text(encoding="utf-8").splitlines():
            key, value = line.split("=", 1)
            parsed[key] = value
            if any(token in key for token in ("PASSWORD", "SECRET", "TOKEN", "KEY")):
                assert key.endswith("_FILE")
                assert value.startswith("/run/secrets/")
        assert parsed == wanted
