from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import re


ROOT = Path(__file__).resolve().parents[2]
COMPOSE = ROOT / "deploy" / "mezo-evidence" / "compose.yaml"


def rendered(profile: str) -> dict[str, object]:
    env = os.environ.copy()
    env.update(
        {
            "LIQVERA_ENGINE_COMMIT": "0" * 40,
            "LIQVERA_PUBLIC_ORIGIN": "https://reports.invalid",
            "LIQVERA_PAY_TO": "0x" + "1" * 40,
            "LIQVERA_SITE_ADDRESS": "reports.invalid",
        }
    )
    result = subprocess.run(
        [
            "docker",
            "compose",
            "--profile",
            profile,
            "-f",
            str(COMPOSE),
            "config",
            "--format",
            "json",
        ],
        cwd=COMPOSE.parent,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def service_networks(config: dict[str, object], service: str) -> set[str]:
    services = config["services"]
    assert isinstance(services, dict)
    item = services[service]
    assert isinstance(item, dict)
    networks = item["networks"]
    assert isinstance(networks, dict)
    return set(networks)


def test_fixture_profile_has_no_external_egress_and_live_keeps_required_egress() -> None:
    fixture = rendered("fixture")
    live = rendered("live")
    assert set(fixture["services"]) == {
        "evidence-capture-fixture", "report-fixture", "postgres-fixture",
        "migrate-fixture", "gateway-fixture", "web-fixture", "edge-fixture",
    }
    assert set(live["services"]) == {
        "evidence-capture-live", "report-live", "postgres-live",
        "migrate-live", "gateway-live", "web-live", "edge-live",
    }
    assert service_networks(fixture, "evidence-capture-fixture") == {"capture_report"}
    assert service_networks(fixture, "gateway-fixture") == {"edge", "gateway_db", "gateway_report", "operations"}
    assert service_networks(fixture, "edge-fixture") == {"edge"}
    assert service_networks(live, "evidence-capture-live") == {"capture_report", "capture_egress"}
    assert service_networks(live, "gateway-live") == {"edge", "gateway_db", "gateway_report", "operations", "payment_egress"}
    assert service_networks(live, "edge-live") == {"edge", "tls_egress"}
    for config in (fixture, live):
        networks = config["networks"]
        assert isinstance(networks, dict)
        operations = networks["operations"]
        assert isinstance(operations, dict)
        assert operations["internal"] is True


def test_fixture_publication_resource_security_health_and_secret_boundaries() -> None:
    fixture = rendered("fixture")
    services = fixture["services"]
    assert isinstance(services, dict)
    edge = services["edge-fixture"]
    assert isinstance(edge, dict)
    assert edge["ports"] == [{"mode": "ingress", "target": 8080, "published": "8080", "protocol": "tcp", "host_ip": "127.0.0.1"}]
    for name, service in services.items():
        assert isinstance(service, dict), name
        assert service["read_only"] is True, name
        assert service["cap_drop"] == ["ALL"], name
        assert "no-new-privileges:true" in service["security_opt"], name
        assert service["pids_limit"] > 0, name
        assert service["mem_limit"], name
        assert float(service["cpus"]) > 0, name
        if name != "migrate-fixture":
            assert "healthcheck" in service, name
    gateway = services["gateway-fixture"]
    assert gateway["environment"]["PAY_TO"] == ""
    assert gateway["environment"]["SOURCE_MODE"] == "fixture"
    assert gateway["environment"]["METRICS_HOST"] == "gateway-metrics"
    assert gateway["environment"]["METRICS_PORT"] == "9090"
    assert "ports" not in gateway


def test_exact_users_tmpfs_mount_modes_resources_and_profile_secrets() -> None:
    fixture = rendered("fixture")["services"]
    live = rendered("live")["services"]
    assert isinstance(fixture, dict) and isinstance(live, dict)
    expected = {
        "evidence-capture": ("10001:10001", ["/tmp:rw,noexec,nosuid,size=32m"], 402653184, 0.5, 128),
        "report": ("10002:10001", ["/tmp:rw,noexec,nosuid,size=64m"], 536870912, 1.0, 128),
        "postgres": ("70:70", ["/tmp:rw,noexec,nosuid,size=64m", "/var/run/postgresql:rw,nosuid,size=8m"], 805306368, 1.0, 128),
        "migrate": ("10003:10001", ["/tmp:rw,noexec,nosuid,size=32m"], 268435456, 0.5, 128),
        "gateway": ("10003:10001", ["/tmp:rw,noexec,nosuid,size=64m"], 536870912, 1.0, 256),
        "web": ("101:101", ["/tmp:rw,noexec,nosuid,size=8m", "/var/cache/nginx:rw,nosuid,size=8m", "/var/run:rw,nosuid,size=8m"], 134217728, 0.25, 64),
        "edge": ("10001:10001", ["/tmp:rw,noexec,nosuid,size=16m"], 201326592, 0.5, 128),
    }
    for profile, services in (("fixture", fixture), ("live", live)):
        for role, (user, tmpfs, memory, cpus, pids) in expected.items():
            service = services[f"{role}-{profile}"]
            assert service["user"] == user
            assert service["tmpfs"] == tmpfs
            assert int(service["mem_limit"]) == memory
            assert float(service["cpus"]) == cpus
            assert service["pids_limit"] == pids
        gateway_volumes = {item["target"]: item for item in services[f"gateway-{profile}"]["volumes"]}
        assert gateway_volumes["/data/artifacts"]["read_only"] is True
        report_volumes = {item["target"]: item for item in services[f"report-{profile}"]["volumes"]}
        assert report_volumes["/data/captures"]["read_only"] is True
        assert report_volumes["/data/artifacts"].get("read_only", False) is False
        assert "volumes" not in services[f"web-{profile}"]
        secrets = {
            name: {item["source"] for item in services[name].get("secrets", [])}
            for name in services
        }
        assert secrets[f"gateway-{profile}"] == {f"postgres_password_{profile}", f"report_token_{profile}"}
        assert secrets[f"report-{profile}"] == {f"report_token_{profile}"}
        assert secrets[f"postgres-{profile}"] == {f"postgres_password_{profile}"}
        assert secrets[f"migrate-{profile}"] == {f"postgres_password_{profile}"}


def test_metrics_are_private_and_csp_is_restrictive() -> None:
    main = (ROOT / "apps" / "mezo-gateway" / "src" / "main.ts").read_text()
    metrics = (ROOT / "apps" / "mezo-gateway" / "src" / "security" / "observability.ts").read_text()
    caddy = (ROOT / "deploy" / "mezo-evidence" / "Caddyfile").read_text()
    index = (ROOT / "apps" / "mezo-web" / "index.html").read_text()
    assert "createServer(telemetryHandler)" in main
    assert "config.metricsPort,config.metricsHost" in main
    assert "liqvera_${name}_total{" not in metrics
    assert "liqvera_payment_ready{" not in metrics
    expected_csp = (
        "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
        "connect-src 'self'; font-src 'self'; base-uri 'none'; form-action 'self'; "
        "frame-ancestors 'none'; object-src 'none'"
    )
    match = re.search(r'Content-Security-Policy "([^"]+)"', caddy)
    assert match and match.group(1) == expected_csp
    assert "unsafe-inline" not in caddy
    assert "/metrics" not in caddy
    assert re.findall(r"<script[^>]*>", index) == ['<script type="module" src="/src/main.ts">']
    assert "<style" not in index and " style=" not in index
