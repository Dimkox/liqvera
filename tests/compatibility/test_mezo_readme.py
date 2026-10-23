"""Judge-facing contract links cannot drift from the pinned Testnet metadata."""

import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_mezo_readme_contract_links_are_pinned_and_typo_is_rejected():
    checker = runpy.run_path(str(ROOT / "scripts/check-docs.py"))
    validate = checker["check_mezo_readme"]
    source = (ROOT / "packages/mezo-protocol/src/index.ts").read_text()
    readme = (ROOT / "README.md").read_text()
    assert validate(readme, source) == []
    bad = readme.replace("https://explorer.test.mezo.org/address/0xd16A5", "https://explorer.mezo.org/address/0xd16A5")
    assert validate(bad, source)
    bad = readme.replace("0xd16A5Df82120ED8D626a1a15232bFcE2366d6AA9", "0x1111111111111111111111111111111111111111")
    assert validate(bad, source)

    bad = readme.replace("[0xd16A5Df82120ED8D626a1a15232bFcE2366d6AA9]", "[0x1111111111111111111111111111111111111111]")
    assert validate(bad, source)
