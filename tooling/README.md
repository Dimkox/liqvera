# External development tooling

Liqvera does not vendor the Adaptive Grok or BMad implementation trees.

Adaptive Grok Build Pro is a Git submodule pinned to `v2.0.19` at commit
`cb9af4073ba6c3d515145164d771c75ebdfa3224`. Initialize it after cloning:

```bash
git submodule update --init --recursive
python3 tooling/run-adaptive-grok.py --check
```

The entrypoint validates the gitlink, checkout commit, tag, version, and clean
worktree before executing a hook or `scripts/grok_*.py` command. It never
fetches tooling implicitly. Version 2.0.19 is intentional: Liqvera opts into
its bounded `pytest-xdist` runner with `.grok-test-runner.json`; earlier local
versions executed the Python suite sequentially.

BMad is recorded only as the exact `bmad-method@6.10.0` npm artifact and SRI
in `tooling-lock.json`. It is not installed or executed by product commands.
