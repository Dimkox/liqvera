"""The source and wheel metadata expose only the four owned runtime namespaces."""
from __future__ import annotations

import subprocess
import tomllib
from pathlib import Path

EXPECTED = {
    'contracts': 'liqvera_contracts',
    'public-capture': 'liqvera_public_capture',
    'readonly-analyzer': 'liqvera_readonly_analyzer',
    'evidence-report': 'liqvera_evidence_report',
}


def test_only_approved_runtime_namespace_roots_are_tracked() -> None:
    tracked = subprocess.check_output(['git', 'ls-files'], text=True).splitlines()
    actual = {(Path(name).parts[1], Path(name).parts[3]) for name in tracked
              if name.startswith('packages/') and len(Path(name).parts) > 4
              and Path(name).parts[2] == 'src' and name.endswith('.py')}
    assert actual == set(EXPECTED.items())
    assert not any(name.startswith('src/') and name.endswith('.py') for name in tracked)
    roots = {Path(name).parts[0] for name in tracked
             if len(Path(name).parts) == 2 and Path(name).name == '__init__.py'}
    assert roots <= {'tests', 'tools'}


def test_wheels_declare_only_owned_namespaces() -> None:
    for package, namespace in EXPECTED.items():
        metadata = tomllib.loads((Path('packages') / package / 'pyproject.toml').read_text())
        assert metadata['tool']['hatch']['build']['targets']['wheel']['packages'] == [f'src/{namespace}']
