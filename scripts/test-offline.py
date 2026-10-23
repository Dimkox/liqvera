#!/usr/bin/env python3
"""Run the complete product gate using prepared dependencies and a disposable ledger."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
# Test-only database image; never an application deployment or existing database.
POSTGRES = 'postgres@sha256:f3bd19c606e442c3d7bdfa8002e03fe260a1023351e0ea4598032022b68dd6e3'
WHEELS = ROOT / '.venv/test-wheels'


def run(args: list[str], *, env=None, capture=False, collect=False):
    if not collect:
        return subprocess.run(args, cwd=ROOT, env=env, check=True, text=True,
                              stdout=subprocess.PIPE if capture else None)
    lines = []
    with subprocess.Popen(args, cwd=ROOT, env=env, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT) as process:
        for line in process.stdout:
            print(line, end='', flush=True)
            lines.append(line)
        code = process.wait()
    output = ''.join(lines)
    if code:
        raise subprocess.CalledProcessError(code, args, output=output)
    return subprocess.CompletedProcess(args, code, stdout=output)


def node_count(output: str) -> int:
    values = {key: int(value) for key, value in
              re.findall(r'(?:ℹ|#)\s*(tests|pass|fail|skipped)\s+(\d+)', output)}
    if (set(values) != {'tests', 'pass', 'fail', 'skipped'} or values['tests'] < 1
            or values['tests'] != values['pass'] or values['fail'] or values['skipped']):
        raise ValueError('Node gate must report all tests passed without skips')
    return values['tests']


def check_documented_counts(counts: dict) -> None:
    match = re.search(r'<!-- liqvera-test-counts: (.+?) -->', (ROOT / 'README.md').read_text())
    if match is None or json.loads(match[1]) != counts:
        raise ValueError('README test counts do not match the completed gate')


def prepare() -> None:
    WHEELS.mkdir(parents=True, exist_ok=True)
    for lock in ('requirements-dev.lock', 'requirements.lock'):
        run([sys.executable, '-m', 'pip', 'download', '--only-binary=:all:',
             '--dest', str(WHEELS), '-r', lock])
    run([sys.executable, '-m', 'pip', 'download', '--only-binary=:all:', '--dest', str(WHEELS),
         '--python-version', '314', '--implementation', 'cp', '--abi', 'cp314',
         '--platform', 'musllinux_1_2_x86_64', '-r', 'requirements.lock'])
    run(['docker', 'pull', POSTGRES])


def gateway(env: dict[str, str]) -> int:
    # Resolve only an already cached immutable image. No external database URL is accepted.
    image = run(['docker', 'image', 'inspect', POSTGRES, '--format', '{{.Id}}'],
                capture=True).stdout.strip()
    if re.fullmatch(r'sha256:[0-9a-f]{64}', image) is None:
        raise ValueError('invalid cached test image identity')
    name = 'liqvera-offline-test-' + uuid4().hex
    container = None
    try:
        created = run(['docker', 'run', '--pull=never', '-d', '--name', name,
                       '--label', 'liqvera.scope=disposable-offline-test',
                       '-e', 'POSTGRES_HOST_AUTH_METHOD=trust',
                       '-e', 'POSTGRES_DB=liqvera_f4_test_offline',
                       '-p', '127.0.0.1::5432', image], capture=True).stdout.strip()
        if re.fullmatch(r'[0-9a-f]{64}', created) is None:
            raise ValueError('test container creation did not return a bound identity')
        container = created
        ports = json.loads(run(['docker', 'inspect', '--format',
                                '{{json .NetworkSettings.Ports}}', container], capture=True).stdout)
        bindings = ports['5432/tcp']
        if len(bindings) != 1 or bindings[0]['HostIp'] != '127.0.0.1':
            raise ValueError('disposable database must be loopback-only')
        port = bindings[0]['HostPort']
        if re.fullmatch(r'[0-9]{1,5}', port) is None:
            raise ValueError('invalid disposable database port')
        for _ in range(100):
            ready = subprocess.run(['docker', 'exec', container, 'pg_isready', '-U', 'postgres'],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if ready.returncode == 0:
                break
            time.sleep(.1)
        else:
            raise ValueError('disposable database did not become ready')
        test_env = {**env, 'TEST_DATABASE_URL':
                    f'postgresql://postgres@127.0.0.1:{port}/liqvera_f4_test_offline',
                    'TEST_DATABASE_DISPOSABLE': '1'}
        tested = run(['npm', 'test', '--prefix', 'apps/mezo-gateway'], env=test_env, collect=True)
        return node_count(tested.stdout)
    finally:
        # Only the ID returned by this invocation may be removed. Never prune or
        # connect to another database, volume, Compose project or deployment.
        if container is not None:
            run(['docker', 'rm', '-fv', container], capture=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--prepare', action='store_true', help='Explicit online dependency preparation only')
    parser.add_argument('--gateway-only', action='store_true', help='Run the disposable-ledger Node gate only')
    args = parser.parse_args()
    if args.prepare:
        if args.gateway_only:
            parser.error('--prepare and --gateway-only are mutually exclusive')
        prepare()
        return 0
    env = {**os.environ, 'PIP_NO_INDEX': '1', 'PIP_FIND_LINKS': str(WHEELS),
           'PIP_DISABLE_PIP_VERSION_CHECK': '1'}
    if not args.gateway_only and not WHEELS.is_dir():
        raise ValueError('prepare local wheels first with make test-prepare')
    run(['apps/mezo-gateway/node_modules/.bin/tsc', '-p', 'packages/mezo-protocol/tsconfig.json'], env=env)
    gateway_tests = gateway(env)
    if not args.gateway_only:
        run(['npm', 'run', '--prefix', 'apps/mezo-web', 'build'], env=env)
        web = run(['npm', 'test', '--prefix', 'apps/mezo-web'], env=env, collect=True)
        python = run(['make', 'verify', 'PYTHON=' + sys.executable], env=env, collect=True)
        run([sys.executable, '-m', 'ruff', 'check', '.'], env=env)
        run([sys.executable, 'scripts/check-docs.py'], env=env)
        passed = re.search(r'\b(\d+) passed\b', python.stdout)
        if passed is None:
            raise ValueError('Python gate did not report a pass count')
        subtests = re.search(r'\b(\d+) subtests passed\b', python.stdout)
        if subtests is None:
            raise ValueError('Python gate did not report a subtest count')
        counts = {'python': int(passed[1]), 'python_subtests': int(subtests[1]),
                  'gateway': gateway_tests, 'web': node_count(web.stdout)}
        result = {'schema': 'liqvera-offline-test-counts/v1', 'counts': counts,
                  'source_commit': run(['git', 'rev-parse', 'HEAD'], capture=True).stdout.strip()}
        destination = ROOT / 'dist/test-results'
        destination.mkdir(parents=True, exist_ok=True)
        (destination / 'latest.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
        print('Completed offline test counts: '+json.dumps(counts, sort_keys=True), flush=True)
        check_documented_counts(counts)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
