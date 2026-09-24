"""Public-capture runtime: validate adapters and optionally seal a frozen package."""

from __future__ import annotations

import time
from uuid import uuid4

from mee_public_capture.config import PublicCaptureConfig
from mee_public_capture.package import REVIEWED_BTC, REVIEWED_LIGHTER_BTC, write_frozen_package
from mee_public_capture.public_adapters import hyperliquid, lighter

FIXTURE_BOOK = (
    b'{"coin":"BTC","time":1,"levels":[[{"px":"1.0","sz":"1.0"}],[{"px":"1.1","sz":"1.0"}]]}'
)
FIXTURE_LIGHTER_SNAPSHOT = (
    b'{"channel":"order_book:1","type":"subscribed/order_book","timestamp":1,'
    b'"order_book":{"nonce":10,"bids":[{"price":"1.0","size":"1.0"}],'
    b'"asks":[{"price":"1.1","size":"1.0"}]}}'
)


def run_public_capture(config: PublicCaptureConfig) -> int:
    if config.mode != "public":
        return 2
    adapters = {
        "hyperliquid": hyperliquid.HyperliquidPublicAdapter,
        "lighter": lighter.LighterPublicAdapter,
    }
    for venue in config.venues:
        if venue not in adapters:
            return 2
        _ = adapters[venue]
    if config.output is None:
        return 0
    started = int(time.time() * 1000)
    try:
        envelopes, mappings = _envelopes_and_mappings(config)
        write_frozen_package(
            config.output,
            run_id=uuid4(),
            started_at_ms=started,
            terminated_at_ms=started + 1,
            venues=config.venues,
            envelopes=envelopes,
            mappings=mappings,
        )
    except Exception:
        return 1
    print(f"frozen package written root={config.output}")
    return 0


def _envelopes_and_mappings(
    config: PublicCaptureConfig,
) -> tuple[tuple[tuple[str, bytes], ...], list[dict[str, object]]]:
    if config.source == "fixture":
        return _fixture_envelopes(config.venues)
    if config.source != "public":
        raise ValueError("unsupported capture source")
    if "hyperliquid" not in config.venues:
        raise ValueError("public source does not collect Lighter")
    return (("hyperliquid", _live_hyperliquid_payload()),), [REVIEWED_BTC]


def _fixture_envelopes(
    venues: tuple[str, ...],
) -> tuple[tuple[tuple[str, bytes], ...], list[dict[str, object]]]:
    envelopes: list[tuple[str, bytes]] = []
    mappings: list[dict[str, object]] = []
    for venue in venues:
        if venue == "hyperliquid":
            envelopes.append(("hyperliquid", FIXTURE_BOOK))
            mappings.append(REVIEWED_BTC)
        elif venue == "lighter":
            envelopes.append(("lighter", FIXTURE_LIGHTER_SNAPSHOT))
            mappings.append(REVIEWED_LIGHTER_BTC)
    return tuple(envelopes), mappings


def _live_hyperliquid_payload() -> bytes:
    import httpx

    with httpx.Client(timeout=10.0) as client:
        response = client.post(
            "https://api.hyperliquid.xyz/info",
            json={"type": "l2Book", "coin": "BTC"},
        )
        response.raise_for_status()
        return response.content
