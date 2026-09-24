from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.extract_observables import redact_url, scan_roots
from scripts.fetch_sources import AssetParser
from scripts.verify_inventory import validate_api_csv_files, validate_inventory


class VerifyInventoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.base = Path(__file__).resolve().parents[1]

    def test_inventory_and_api_surface_validate(self) -> None:
        data = validate_inventory(self.base / "clients.lock.json")
        self.assertEqual(4, len(data["programmatic_clients"]))
        self.assertEqual(
            77,
            validate_api_csv_files(
                sorted((self.base / "data").glob("api-surface-*.csv"))
            ),
        )


class StaticExtractionTests(unittest.TestCase):
    def test_secret_like_query_values_and_userinfo_are_redacted(self) -> None:
        redacted = redact_url(
            "https://user:pass@example.test/path?token=abc123&market=BTC"
        )
        self.assertNotIn("user", redacted)
        self.assertNotIn("pass", redacted)
        self.assertNotIn("abc123", redacted)
        self.assertIn("token=%3Credacted%3E", redacted)
        self.assertIn("market=BTC", redacted)

    def test_scan_does_not_emit_bearer_value(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "sample.py").write_text(
                'URL = "https://api.example.test/x?api_key=sensitive"\n'
                'HEADER = "Bearer abcdefghijklmnopqrstuvwxyz"\n'
                'PATH = "/exchange/markets"\n'
                'TOKEN = os.getenv("VOOI_BEARER_TOKEN")\n',
                encoding="utf-8",
            )
            result = scan_roots([root])
            payload = json.dumps(result)
            self.assertNotIn("sensitive", payload)
            self.assertNotIn("abcdefghijklmnopqrstuvwxyz", payload)
            self.assertIn("/exchange/markets", payload)
            self.assertIn("VOOI_BEARER_TOKEN", payload)


class AssetParserTests(unittest.TestCase):
    def test_only_static_code_and_manifest_links_are_collected(self) -> None:
        parser = AssetParser()
        parser.feed(
            '<script src="/app.js"></script>'
            '<link rel="stylesheet" href="/app.css">'
            '<link rel="manifest" href="/manifest.webmanifest">'
            '<link rel="icon" href="/icon.png">'
            '<img src="/image.png">'
        )
        self.assertEqual(
            {"/app.js", "/app.css", "/manifest.webmanifest"},
            parser.urls,
        )


if __name__ == "__main__":
    unittest.main()
