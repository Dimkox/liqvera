import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "extract_apk_indicators.py"
spec = importlib.util.spec_from_file_location("extract_apk_indicators", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


class ExtractIndicatorsTests(unittest.TestCase):
    def test_extracts_archive_inventory_and_redacts_url_queries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            apk_path = Path(tmp) / "sample.apk"
            output_path = Path(tmp) / "indicators.json"
            dex_payload = (
                b"https://api.goodcrypto.app/v1/orders?token=do-not-store\x00"
                b"wss://stream.goodcrypto.app/socket?auth=secret\x00"
                b"api.goodcrypto.app\x00"
                b"192.0.2.10\x00"
            )
            with zipfile.ZipFile(apk_path, "w") as archive:
                archive.writestr("classes.dex", dex_payload)
                archive.writestr("classes2.dex", b"https://example.org/path#frag")
                archive.writestr("lib/arm64-v8a/libcrypto.so", b"native")
                archive.writestr("META-INF/CERT.RSA", b"signature")
                archive.writestr("res/raw/config.json", b'{"endpoint":"https://api.goodcrypto.app/v2"}')

            report = module.analyze_archive(apk_path, max_entry_bytes=1024 * 1024)
            output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

            self.assertEqual(report["archive"]["file_name"], "sample.apk")
            self.assertEqual(report["archive"]["entry_count"], 5)
            self.assertEqual(report["dex_files"], ["classes.dex", "classes2.dex"])
            self.assertEqual(report["native_libraries"], ["lib/arm64-v8a/libcrypto.so"])
            self.assertEqual(report["signature_entries"], ["META-INF/CERT.RSA"])
            self.assertIn("https://api.goodcrypto.app/v1/orders", report["network_indicators"]["urls"])
            self.assertIn("wss://stream.goodcrypto.app/socket", report["network_indicators"]["urls"])
            self.assertNotIn("token=do-not-store", output_path.read_text(encoding="utf-8"))
            self.assertNotIn("auth=secret", output_path.read_text(encoding="utf-8"))
            self.assertIn("api.goodcrypto.app", report["network_indicators"]["domains"])
            self.assertIn("192.0.2.10", report["network_indicators"]["ip_addresses"])

    def test_skips_oversized_entries_and_reports_them(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            apk_path = Path(tmp) / "oversized.apk"
            with zipfile.ZipFile(apk_path, "w") as archive:
                archive.writestr("classes.dex", b"A" * 64)

            report = module.analyze_archive(apk_path, max_entry_bytes=16)

            self.assertEqual(report["scan"]["skipped_oversized_entries"], ["classes.dex"])
            self.assertEqual(report["network_indicators"]["urls"], [])

    def test_rejects_non_zip_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad_path = Path(tmp) / "not-an-apk.apk"
            bad_path.write_text("not a zip", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "valid ZIP/APK"):
                module.analyze_archive(bad_path, max_entry_bytes=1024)


if __name__ == "__main__":
    unittest.main()
