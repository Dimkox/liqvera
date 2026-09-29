from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess


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


def test_metrics_are_private_and_csp_is_restrictive() -> None:
    main = (ROOT / "apps" / "mezo-gateway" / "src" / "main.ts").read_text()
    metrics = (ROOT / "apps" / "mezo-gateway" / "src" / "security" / "observability.ts").read_text()
    caddy = (ROOT / "deploy" / "mezo-evidence" / "Caddyfile").read_text()
    assert "config.metricsPort,config.metricsHost" in main
    assert "liqvera_${name}_total{" not in metrics
    assert "liqvera_payment_ready{" not in metrics
    assert "Content-Security-Policy" in caddy
    assert "default-src 'none'" in caddy
    assert "script-src 'self'" in caddy
    assert "connect-src 'self'" in caddy
    assert "style-src 'self'" in caddy
    assert "unsafe-inline" not in caddy
    assert "/metrics" not in caddy
