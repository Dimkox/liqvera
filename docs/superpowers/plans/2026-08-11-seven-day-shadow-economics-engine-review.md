# Seven-Day Shadow Economics Engine Plan Review

**Date:** 2026-08-11  
**Status:** binding execution clarification for [`2026-08-11-seven-day-shadow-economics-engine.md`](2026-08-11-seven-day-shadow-economics-engine.md)

This review records the pre-execution conflict scan required by the Superpowers workflow. If this file and the implementation plan differ on the points below, this file governs.

## Findings and resolutions

### 1. Test examples and the repository test runner

The repository CI uses `unittest` and runs tests before installing optional A2 dependencies. Several plan snippets were written as bare pytest-style functions while their commands invoked `python -m unittest`. That mismatch is rejected before implementation.

Binding rule:

- every new test is a `unittest.TestCase` method;
- bare `test_*` snippets in the plan are shorthand and must be wrapped in a concrete `TestCase` class;
- use `self.assertEqual`, `self.assertLessEqual`, `self.assertRaisesRegex`, and other unittest assertions;
- replace pytest's `tmp_path` with `tempfile.TemporaryDirectory()` and `pathlib.Path`;
- do not add pytest as a requirement for this increment;
- all focused commands remain `python -B -m unittest ... -v`;
- full discovery remains `python -B -m unittest discover -s tests -t . -v`.

Corrected mutation-test shape:

```python
import tempfile
import unittest
from pathlib import Path


class FrozenPackageTests(unittest.TestCase):
    def test_tampered_member_fails_before_iteration(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "pkg"
            write_frozen_package(
                make_minimal_reader(),
                package,
                "a" * 40,
                "b" * 64,
            )
            member = next((package / "raw_batches").iterdir())
            member.write_bytes(member.read_bytes() + b"x")
            with self.assertRaisesRegex(
                FrozenPackageError,
                "MEMBER_HASH_MISMATCH",
            ):
                FrozenPackageEvidenceReader(package)
```

The same conversion applies to the crossed-book and mapping-rejection snippets.

### 2. Optional PostgreSQL dependency boundary

`psycopg` is installed in the A2/PostgreSQL jobs, but the first general Python job executes discovery before dependency installation.

Binding rule:

- `multi_exchange_engine.shadow_economics.__init__` must not import `postgres_reader`;
- `postgres_reader.py` imports `psycopg` lazily inside the connection factory or behind an injected connector boundary;
- unit tests for SQL/query construction require no installed psycopg;
- PostgreSQL integration modules check `A2_TEST_DATABASE_URL` before importing psycopg and skip only in non-binding local discovery;
- the pinned PostgreSQL 16.11/17.7 CI jobs install exact A2 dependencies and must execute the new integration tests with zero skips.

### 3. Package placement

The repository currently contains a mature root `multi_exchange_engine.a2` and `multi_exchange_engine.shadow` implementation plus a separate incomplete `src/multi_exchange_engine` skeleton. Importing across two regular packages with the same name would be unsafe.

Binding rule for this seven-day increment:

- implement the analyzer at `multi_exchange_engine/shadow_economics/`;
- reuse only public, pure contracts from the root A2/shadow packages;
- do not copy modules into `src/`;
- do not perform package-layout consolidation during the sprint;
- record package-layout consolidation as later repository cleanup, not as a hidden prerequisite.

### 4. Migration number

The repository currently contains migrations `000001` and `000002`. The plan's `000003_shadow_economics_views` number is available and accepted.

### 5. Branch and verification boundary

- implementation must not occur on `main`;
- use branch `agent/seven-day-shadow-economics` unless an existing isolated branch for this exact plan already exists;
- every task must preserve the public/shadow-only gate and update `handoff.md` in the same task commit;
- no task is called complete without fresh test output from a real checkout or CI/Claw runner;
- connector-only file creation is not test evidence;
- if the runner cannot execute a required gate, report the task as pending verification rather than green.

## Conflict scan result

With the corrections above, no remaining plan requirement contradicts the approved design or current repository safety invariants. The next step is isolated-branch baseline verification, followed by Task 1 TDD.
