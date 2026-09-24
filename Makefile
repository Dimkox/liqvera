.PHONY: verify verify-packages graph salvage artifacts wheels product demo prod

PYTHON ?= python3

graph:
	$(PYTHON) -B scripts/check-architecture-graph.py --manifest-root architecture --phase precommit --allow-declared-conflicts

salvage:
	$(PYTHON) scripts/verify-pr21-salvage.py --manifest architecture/salvage/pr21.yaml

wheels:
	$(PYTHON) -B scripts/build-stage-a-distributions.py --source-sha $$(git rev-parse HEAD) --out dist

artifacts:
	$(PYTHON) -B scripts/check-stage-a-artifacts.py --forbid-path 'cmd/**' 'internal/**' 'go.mod' 'go.sum' --forbid-binary engine

verify-packages:
	$(PYTHON) -B -m pytest tests/contracts tests/public_capture tests/readonly_analyzer tests/conformance tests/graph tests/installed tests/artifact -q

verify: graph salvage artifacts verify-packages
	@echo "stage-a verify passed"

product: wheels
	docker build --network=none -f deploy/images/Dockerfile.public-capture -t mee-public-capture:$$(git rev-parse HEAD) -t mee-public-capture:stage-a .
	docker build --network=none -f deploy/images/Dockerfile.readonly-analyzer -t mee-readonly-analyzer:$$(git rev-parse HEAD) -t mee-readonly-analyzer:stage-a .
	@echo "stage-a product ready: dist/*.whl mee-public-capture:stage-a mee-readonly-analyzer:stage-a"

demo:
	rm -rf $(CURDIR)/.stage-a/package
	install -d -m 0755 $(CURDIR)/.stage-a/package
	PYTHONPATH=$(CURDIR)/packages/contracts/src:$(CURDIR)/packages/public-capture/src:$(CURDIR)/packages/readonly-analyzer/src \
		MEE_CAPTURE_OUT=$(CURDIR)/.stage-a/package MEE_CAPTURE_SOURCE=fixture \
		$(PYTHON) -B -c "from mee_public_capture.config import load_public_configuration; from mee_public_capture.runtime import run_public_capture; raise SystemExit(run_public_capture(load_public_configuration()))"
	PYTHONPATH=$(CURDIR)/packages/contracts/src:$(CURDIR)/packages/public-capture/src:$(CURDIR)/packages/readonly-analyzer/src \
		MEE_FROZEN_PACKAGE=$(CURDIR)/.stage-a/package \
		$(PYTHON) -B -c "from mee_readonly_analyzer.__main__ import main; raise SystemExit(main())"

prod: product
	docker compose -f compose.stage-a.yml run --rm --no-deps prepare-data
	docker compose -f compose.stage-a.yml run --rm --no-deps capture
	docker compose -f compose.stage-a.yml run --rm --no-deps analyzer
	@echo "stage-a production loop passed"
