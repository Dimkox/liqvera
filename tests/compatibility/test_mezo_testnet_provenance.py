"""Offline ABI provenance and call-surface constraints for Testnet analytics."""

import hashlib
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2] / "packages/mezo-protocol"
LOCK = json.loads((ROOT / "source-lock.json").read_text())
CONTRACTS = LOCK["sources"]["testnet_explorer"]["contracts"]


@pytest.mark.parametrize("entry", CONTRACTS, ids=lambda e: e["name"])
def test_testnet_abi_bytes_match_source_lock(entry):
    raw = (ROOT / entry["local_path"]).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == entry["sha256"]
    assert entry["chain_id"] == 31611
    assert entry["address"] in entry["url"]
    assert entry["url"].startswith("https://api.explorer.test.mezo.org/api?")
    assert isinstance(json.loads(raw), list)


@pytest.mark.parametrize(("name", "functions"), [
    ("Pool", {"token0", "token1", "stable", "getReserves", "getAmountOut"}),
    ("Router", {"getAmountsOut"}),
    ("PoolFactory", {"getFee"}),
    ("TroveManagerImplementation", {"getEntireDebtAndColl", "getCurrentICR", "MCR", "CCR"}),
    ("SortedTrovesImplementation", {"getFirst", "getLast", "getPrev", "getNext", "getSize"}),
    ("PriceFeedImplementation", {"fetchPrice"}),
])
def test_required_analytics_methods_are_read_only(name, functions):
    entry = next(e for e in CONTRACTS if e["name"] == name)
    abi = json.loads((ROOT / entry["local_path"]).read_bytes())
    methods = {m["name"]: m for m in abi if m["type"] == "function"}
    assert functions <= methods.keys()
    assert all(methods[f]["stateMutability"] == "view" for f in functions)


def test_proxy_provenance_keeps_implementation_separate():
    for name in ("TroveManager", "SortedTroves", "PriceFeed"):
        proxy = next(e for e in CONTRACTS if e["name"] == name)
        implementation = next(e for e in CONTRACTS if e["name"] == name + "Implementation")
        assert proxy["implementation_address"] == implementation["address"]
        assert proxy["address"] != implementation["address"]


def test_exported_dex_metadata_has_sourced_testnet_addresses():
    source = (ROOT / "src/index.ts").read_text()
    assert "export const MEZO_TESTNET_DEX" in source
    for name in ("Pool", "Router", "PoolFactory"):
        address = next(e["address"] for e in CONTRACTS if e["name"] == name)
        assert address in source


@pytest.mark.parametrize("entry", CONTRACTS, ids=lambda e: e["name"])
def test_retained_explorer_source_and_proxy_metadata(entry):
    response = entry["source_response"]
    raw = (ROOT / response["local_path"]).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == response["sha256"]
    source = json.loads(raw)["result"][0]
    assert hashlib.sha256(source["SourceCode"].encode()).hexdigest() == entry["source_sha256"]
    assert json.loads(source["ABI"]) == json.loads((ROOT / entry["local_path"]).read_bytes())
    if "implementation_metadata" in entry:
        metadata = entry["implementation_metadata"]
        raw = (ROOT / metadata["local_path"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == metadata["sha256"]
        assert any(item["address"].lower() == entry["implementation_address"].lower()
                   for item in json.loads(raw)["implementations"])


def test_named_dex_addresses_and_exported_abis_match_vendor():
    source = (ROOT / "src/index.ts").read_text()
    for name, field, exported in [
        ("Pool", "musdBtcPool", "MEZO_TESTNET_POOL_ABI"),
        ("Router", "router", "MEZO_TESTNET_ROUTER_ABI"),
        ("PoolFactory", "poolFactory", "MEZO_TESTNET_POOL_FACTORY_ABI"),
    ]:
        entry = next(e for e in CONTRACTS if e["name"] == name)
        assert f'{field}: "{entry["address"]}"' in source
        match = re.search(r"export const " + exported + r" = (\[.*?\]) as const;", source, re.S)
        assert match
        exported_abi = json.loads(match[1])
        vendor = json.loads((ROOT / entry["local_path"]).read_bytes())
        expected = {"Pool": {"token0", "token1", "stable", "getReserves", "getAmountOut"},
                    "Router": {"getAmountsOut"}, "PoolFactory": {"getFee"}}
        assert {item["name"] for item in exported_abi} == expected[name]
        assert all(item in vendor for item in exported_abi)
        assert all(item["stateMutability"] == "view" for item in exported_abi)
