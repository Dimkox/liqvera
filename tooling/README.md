# External development tooling

Liqvera does not vendor the Adaptive Grok or BMad implementation trees.

Adaptive Grok Build Pro is a Git submodule pinned to `v2.0.19` at commit
`cb9af4073ba6c3d515145164d771c75ebdfa3224`. Initialize it after cloning:

```bash
git submodule update --init --recursive
python3 tooling/run-adaptive-grok.py --check
make verify-tooling
```

The entrypoint validates the gitlink, checkout commit, tag, version, and clean
worktree before executing a hook or `scripts/grok_*.py` command. Validation
rejects `assume-unchanged`/`skip-worktree` index flags globally, then verifies
the explicit runtime/instruction trust closure directly against HEAD: engine,
Grok scripts/hooks/config/templates/agents/skills, plus root policy and VERSION.
The closure is capped at 256 files / 2 MB; v2.0.19 uses 177 files / 1,232,921
bytes, so historical packages and release evidence are never hashed per hook.
Ordinary dirty/untracked detection still covers the entire checkout. Ignored
importable code is forbidden in Python execution roots. Python
bytecode generation is disabled at the boundary so validation cannot create an
ignored import path. Version 2.0.19 is intentional: Liqvera opts into its
bounded `pytest-xdist` runner with `.grok-test-runner.json`; earlier local
versions executed the Python suite sequentially.

The thin Liqvera override in `grok-verify.py` supplies the four package source
roots that the isolated upstream runner intentionally does not read from
`pyproject.toml`, retains Liqvera's `tests/release` exclusion, and fails if the
requested run degrades from `pytest-xdist` to a serial engine. The verification
policy and receipt implementation continue to execute from the pinned
submodule.

Ordinary product tests and `make verify-packages` validate the static gitlink
and lock without requiring a recursive clone. `make verify-tooling` is the
strict initialized-submodule suite: it exercises commit/tag/VERSION/clean-tree
and HEAD byte/mode validation, index-flag and import-hijack rejection,
direct-entrypoint rejection, fail-closed hooks, and recurring container
scanning. Hooks never synthesize an allow/empty response when the pin is
unavailable or invalid.

Every PR verification discovers all tracked Dockerfiles and Compose files and
passes each to Trivy. The recurring blocking threshold is
`MEDIUM,HIGH,CRITICAL`; LOW findings remain visible in explicit audit output
without turning inherited health-check debt into an undocumented waiver.

BMad is recorded only as the exact `bmad-method@6.10.0` npm artifact and SRI
in `tooling-lock.json`. It is not installed or executed by product commands.
