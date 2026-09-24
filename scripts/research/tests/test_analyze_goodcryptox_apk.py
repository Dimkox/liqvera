import json
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).parents[3]
SCRIPT = ROOT / "scripts" / "research" / "analyze-goodcryptox-apk.sh"


class AnalyzeWrapperTests(unittest.TestCase):
    def test_generates_local_analysis_bundle_without_persisting_url_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            apk_path = tmp_path / "sample.apk"
            output_dir = tmp_path / "out"
            with zipfile.ZipFile(apk_path, "w") as archive:
                archive.writestr(
                    "classes.dex",
                    b"https://api.goodcrypto.app/orders?api_key=never-write-this",
                )
                archive.writestr("AndroidManifest.xml", b"binary-manifest")

            result = subprocess.run(
                ["bash", str(SCRIPT), str(apk_path), str(output_dir)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((output_dir / "hashes.txt").is_file())
            self.assertTrue((output_dir / "zip-listing.txt").is_file())
            self.assertTrue((output_dir / "indicators.json").is_file())
            self.assertTrue((output_dir / "tool-status.txt").is_file())
            indicators = json.loads((output_dir / "indicators.json").read_text(encoding="utf-8"))
            self.assertIn(
                "https://api.goodcrypto.app/orders",
                indicators["network_indicators"]["urls"],
            )
            self.assertNotIn(
                "never-write-this",
                (output_dir / "indicators.json").read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
