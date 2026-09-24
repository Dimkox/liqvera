# Mistakes

Root causes, not symptoms. Record only mistakes that caused a real problem.

## 2026-08-18 — Treated research completion as Git publication

**Symptom:** The Kakao/Korea research session was presented as delivered even though no repository file, branch, commit or PR existed.
**Root cause:** Completion was inferred from the research tool output instead of verifying the target repository, canonical path, inbound links and remote SHA. Publication work is complete only after the file is readable from the intended Git ref and the commit/PR state is verified.

## 2026-08-17 — Treated the plan's `go test` step as executable policy

**Symptom:** Go 1.26.5 was installed and five Go analysis agents were launched, then killed.
**Root cause:** The M0-M3 task file was read as the run contract. Owner policy (hypotheses only in Python) was not applied before spawning agents or fetching a toolchain.

## 2026-08-17 — Dropped a non-graph YAML into architecture/

**Symptom:** `GraphLoadError: repository manifest set is invalid (unexpected: conformance.yaml)`.
**Root cause:** Assumed `architecture/` is a folder for any schema document. The loader's authority set is the closed `_REPOSITORY_MANIFESTS` list of top-level `*.yaml` names.

## 2026-08-17 — Put new graph nodes in data-contracts.yaml

**Symptom:** `grok_verify` `contract-structure` failed: missing `openapi:` / `asyncapi:`.
**Root cause:** Chose a path because its *graph kind* is Contract. The quality profile keys off the filename token `contract`, not `kind: Contract`.

## 2026-08-17 — Edited the Claw PR workflow to attach a local pytest gate

**Symptom:** `secret-scan` failed on `.github/workflows/verify-a2-pr-on-claw.yml`.
**Root cause:** Verification scans the whole changed file. The pre-existing `password="$(...)"` assignment already matches `generic-secret`; touching the file for an unrelated step reopened that match.

## 2026-08-17 — Quoted the workflow password assignment in decisions.md

**Symptom:** `grok_verify` `secret-scan` failed on `decisions.md` after the memory files were committed.
**Root cause:** The log copied the exact `password=` quoted assignment that the scanner matches. Memory files are scanned like product files; describe the pattern, do not paste the matching text.

## 2026-08-17 — Used a hyphenated script path as an importable module

**Symptom:** `tests/conformance/test_stage_a_excludes_go.py` could not import the artifact scanner.
**Root cause:** Inspection logic lived only in `scripts/check-stage-a-artifacts.py`. A hyphenated CLI name is not a Python module; shared logic belongs under `tools/`.

## 2026-09-24 — Inferred project language from the conversation

**Symptom:** Newly published Liqvera documentation used Russian even though the owner requires English throughout the project.
**Root cause:** The artifact language was inferred from the chat instead of being treated as a separate project requirement. Use English by default and preserve that decision in `AGENTS.md`.
