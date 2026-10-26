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
        ("BorrowerOperations", "borrowerOperations", "MEZO_TESTNET_BORROWER_OPERATIONS_ABI"),
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
        allowed = {"view", "payable", "nonpayable"} if name == "BorrowerOperations" else {"view"}
        assert all(item in vendor and item.get("stateMutability") in allowed for item in abi)
        if name == "BorrowerOperations":
            assert {item["name"] for item in abi} == {
                "minNetDebt", "addColl", "repayMUSD", "withdrawMUSD", "borrowingRate",
                "getBorrowingFee", "getEntireSystemColl", "getEntireSystemDebt",
                "governableVariables",
            }
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

    response = json.loads((ROOT / "vendor/explorer/BorrowerOperationsImplementation.source.testnet.json").read_text())
    sources = response["result"][0]["AdditionalSources"]
    interface = next(x["SourceCode"] for x in sources if "interface IGovernableVariables" in x["SourceCode"])
    assert re.search(r"function isAccountFeeExempt\(\s*address _account\s*\) external view returns \(bool\)", interface)
    match = re.search(r"export const MEZO_TESTNET_GOVERNABLE_VARIABLES_ABI = (\[.*?\]) as const;", source, re.S)
    assert match
    assert json.loads(match[1]) == [{
        "type": "function", "name": "isAccountFeeExempt",
        "inputs": [{"name": "_account", "type": "address"}],
        "outputs": [{"name": "", "type": "bool"}], "stateMutability": "view",
    }]
