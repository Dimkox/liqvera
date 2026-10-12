# Validating Liqvera

Start from a clean checkout of the intended branch. Record `git rev-parse HEAD`, compare ancestry with main and published tags, and inspect `git status`. Never infer project capabilities from a stale worktree.

## Local checks

```sh
make verify PYTHON=.venv/bin/python
make liqvera-gateway liqvera-web
npm test --prefix apps/mezo-gateway
npm test --prefix apps/mezo-web
make mvp PYTHON=.venv/bin/python
```

The Python suite covers exact arithmetic, sealed capture, hostile bundles, installed-package boundaries, schema/state contracts and installer behavior. Node tests cover API validation, payment authority, retry/finality/recovery and browser orchestration. A skipped PostgreSQL test is not a pass: provision a disposable loopback database named `liqvera_f4_test_<suffix>`, set `TEST_DATABASE_URL` and `TEST_DATABASE_DISPOSABLE=1`, then run `npm run test:postgres --prefix apps/mezo-gateway`. Never use an existing application database.

Build Python wheels with `make liqvera-python` from clean source. Install them using `--no-index --find-links` into a fresh environment outside the source tree. Build and verify a canonical fixture bundle with the installed CLIs, and confirm tampering is rejected. The prototype ZIP has a separate format.

## Security

Run npm audit against both lockfiles, pip-audit against the exact installed runtime/dev closure and Trivy against each built image ID, including PostgreSQL and edge. Refresh advisory data and retain scanner versions, timestamps, digest bindings and unsuppressed results. Optional external Getzilla at commit `540c12f93e798c2f483455a5086ab0018ac3216e` supports `python3 /path/to/getzilla/scripts/getzilla_vulns.py --online --json` from this repository. A direct-pin scan alone does not cover transitive or OS dependencies.

## Acceptance

`make liqvera-acceptance ACCEPTANCE_OUTPUT=/absolute/new/result.json` executes the checked-in offline plan and writes bounded source-bound evidence. Its verifier requires the independently obtained result digest. Most external cases are deliberately NOT_RUN; partial local evidence is not overall PASS. Live payment, deployment and clean-host installer validation require their own scoped execution and evidence.
