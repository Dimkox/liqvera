from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "verify_inventory", BASE / "scripts" / "verify_inventory.py"
)
verify_inventory = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(verify_inventory)


class InventoryTests(unittest.TestCase):
    def test_inventory_contract(self) -> None:
        data = verify_inventory.validate_inventory(BASE / "clients.lock.json")
        self.assertEqual(data["schema_version"], 1)
        self.assertEqual(len(data["supported_exchanges"]), 4)
        self.assertEqual(
            {item["id"] for item in data["supported_exchanges"]},
            {"pacifica", "hyperliquid", "lighter", "aster"},
        )

    def test_bin_entrypoints(self) -> None:
        data = json.loads((BASE / "clients.lock.json").read_text(encoding="utf-8"))
        official = {item["id"]: item for item in data["official_components"]}
        self.assertEqual(official["perp-cli-bin"]["target"], "dist/index.js")
        self.assertEqual(official["perp-mcp-bin"]["target"], "dist/mcp-server.js")
        self.assertEqual(
            official["perp-guardrail-bin"]["target"],
            "dist/guardrail/perp-guardrail.js",
        )


if __name__ == "__main__":
    unittest.main()
