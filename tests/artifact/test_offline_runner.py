"""The offline gate must never clean up an unrelated container on failure."""
import importlib.util
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest


def runner():
    path = Path(__file__).resolve().parents[2] / 'scripts/test-offline.py'
    spec = importlib.util.spec_from_file_location('liqvera_offline_test_runner', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_failed_create_never_deletes_a_guessed_container(monkeypatch):
    module = runner()
    calls = []

    def run(args, **kwargs):
        calls.append(args)
        if args[:3] == ['docker', 'image', 'inspect']:
            return SimpleNamespace(stdout='sha256:' + 'a'*64)
        raise subprocess.CalledProcessError(1, args)

    monkeypatch.setattr(module, 'run', run)
    with pytest.raises(subprocess.CalledProcessError):
        module.gateway({})
    assert not any(args[:2] == ['docker', 'rm'] for args in calls)


def test_unsafe_binding_removes_only_the_created_id(monkeypatch):
    module = runner()
    calls = []
    created = 'b'*64

    def run(args, **kwargs):
        calls.append(args)
        if args[:3] == ['docker', 'image', 'inspect']:
            return SimpleNamespace(stdout='sha256:' + 'a'*64)
        if args[:2] == ['docker', 'run']:
            return SimpleNamespace(stdout=created)
        if args[:2] == ['docker', 'inspect']:
            return SimpleNamespace(stdout='{"5432/tcp":[{"HostIp":"0.0.0.0","HostPort":"12345"}]}')
        assert args == ['docker', 'rm', '-fv', created]
        return SimpleNamespace(stdout='')

    monkeypatch.setattr(module, 'run', run)
    with pytest.raises(ValueError, match='loopback-only'):
        module.gateway({})
    assert calls[-1] == ['docker', 'rm', '-fv', created]


def test_count_parser_accepts_local_and_ci_reports_but_never_skipped_tests():
    module = runner()
    for prefix in ('#', 'ℹ'):
        assert module.node_count('\n'.join(f'{prefix} {key} {value}' for key, value in
                                          [('tests', 98), ('pass', 98), ('fail', 0), ('skipped', 0)])) == 98
    with pytest.raises(ValueError, match='without skips'):
        module.node_count('# tests 98\n# pass 84\n# fail 0\n# skipped 14')


def test_completed_counts_must_match_the_documented_counts(tmp_path, monkeypatch):
    module = runner()
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    (tmp_path / 'README.md').write_text('<!-- liqvera-test-counts: {"python":1,"gateway":2,"web":3} -->')
    module.check_documented_counts({'python': 1, 'gateway': 2, 'web': 3})
    with pytest.raises(ValueError, match='README test counts'):
        module.check_documented_counts({'python': 1, 'gateway': 2, 'web': 4})
