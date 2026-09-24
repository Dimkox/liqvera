"""Static contract for the deliberately unhardened F3 MVP demonstration."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_make_mvp_runs_the_dedicated_runner_with_all_source_packages() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    assert "mvp:" in makefile
    assert "scripts/run-f3-mvp.py" in makefile
    for source_root in (
        "packages/contracts/src",
        "packages/public-capture/src",
        "packages/readonly-analyzer/src",
        "packages/evidence-report/src",
    ):
        assert source_root in makefile


def test_runner_freezes_the_fixture_only_mvp_boundary() -> None:
    source = (ROOT / "scripts" / "run-f3-mvp.py").read_text(encoding="utf-8")
    ast.parse(source)

    for expected in (
        'MVP_SIDE", "BUY"',
        'MVP_QUANTITY", "0.15"',
        'MEE_CAPTURE_SOURCE": "fixture"',
        'MEE_PUBLIC_VENUES": "hyperliquid"',
        'MEE_CAPTURE_OUT": str(package_root)',
        '"--package"',
        '"--output"',
        '"--side"',
        '"--quantity"',
        "load_public_configuration",
        "run_public_capture",
        "report_cli.main",
        "SIMULATED / UNVERIFIED",
        "Payments and live verification are not implemented.",
    ):
        assert expected in source

    assert 'mvp_root / "package"' in source
    assert 'mvp_root / "output"' in source
    assert "shutil.rmtree" in source
    assert "relative_to(mvp_root)" in source


def test_readme_documents_the_exact_demo_outputs_and_limits() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    normalized = " ".join(readme.split())

    assert "## F3 MVP prototype" in readme
    assert "make mvp" in readme
    assert "`.mvp/output/report.json`" in readme
    assert "`.mvp/output/evidence.zip`" in readme
    assert "SIMULATED" in readme
    assert "UNVERIFIED" in readme
    assert "Payments and live verification are not implemented" in normalized
