"""Trove read surfaces are sourced and preserve the actual six-value ABI."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "packages/mezo-protocol"


def test_trove_exports_are_exact_read_only_vendor_items():
    source = (ROOT / "src/index.ts").read_text()
    lock = json.loads((ROOT / "source-lock.json").read_text())["sources"]["testnet_explorer"][
        "contracts"
    ]
    assert "export const MEZO_TESTNET_TROVES" in source
    for name, field, exported in [
        ("TroveManager", "troveManager", "MEZO_TESTNET_TROVE_MANAGER_ABI"),
        ("SortedTroves", "sortedTroves", "MEZO_TESTNET_SORTED_TROVES_ABI"),
        ("PriceFeed", "priceFeed", "MEZO_TESTNET_PRICE_FEED_ABI"),
    ]:
        proxy = next(e for e in lock if e["name"] == name)
        assert f'{field}: "{proxy["address"]}"' in source
        vendor = json.loads((ROOT / f"vendor/{name}.implementation.testnet.json").read_bytes())
        match = re.search(r"export const " + exported + r" = (\[.*?\]) as const;", source, re.S)
        assert match
        abi = json.loads(match[1])
        assert abi
        assert all(item in vendor and item.get("stateMutability") == "view" for item in abi)
        if name == "TroveManager":
            method = next(m for m in abi if m["name"] == "getEntireDebtAndColl")
            assert [i["name"] for i in method["outputs"]] == [
                "coll",
                "principal",
                "interest",
                "pendingCollateral",
                "pendingPrincipal",
                "pendingInterest",
            ]
