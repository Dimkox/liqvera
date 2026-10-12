.PHONY: verify verify-packages artifacts wheels product demo mvp mvp-web prod \
	liqvera-python liqvera-gateway liqvera-web liqvera-images liqvera-compose \
	liqvera-acceptance liqvera-product

PYTHON ?= python3

wheels:
	$(PYTHON) -B scripts/build-stage-a-distributions.py --source-sha $$(git rev-parse HEAD) --out dist

artifacts:
	$(PYTHON) -B scripts/check-stage-a-artifacts.py --forbid-path 'cmd/**' 'internal/**' 'go.mod' 'go.sum' --forbid-binary engine

verify-packages:
	$(PYTHON) -B -m pytest tests -q

verify: artifacts verify-packages
	@echo "Liqvera local Python verification passed"

product: wheels
	docker build -f deploy/images/Dockerfile.public-capture -t liqvera-public-capture:$$(git rev-parse HEAD) -t liqvera-public-capture:stage-a .
	docker build -f deploy/images/Dockerfile.readonly-analyzer -t liqvera-readonly-analyzer:$$(git rev-parse HEAD) -t liqvera-readonly-analyzer:stage-a .
	@echo "stage-a product ready: dist/*.whl liqvera-public-capture:stage-a liqvera-readonly-analyzer:stage-a"

demo:
	rm -rf $(CURDIR)/.stage-a/package
	install -d -m 0755 $(CURDIR)/.stage-a/package
	PYTHONPATH=$(CURDIR)/packages/contracts/src:$(CURDIR)/packages/public-capture/src:$(CURDIR)/packages/readonly-analyzer/src \
		LIQVERA_CAPTURE_OUT=$(CURDIR)/.stage-a/package LIQVERA_CAPTURE_SOURCE=fixture \
		$(PYTHON) -B -c "from liqvera_public_capture.config import load_public_configuration; from liqvera_public_capture.runtime import run_public_capture; raise SystemExit(run_public_capture(load_public_configuration()))"
	PYTHONPATH=$(CURDIR)/packages/contracts/src:$(CURDIR)/packages/public-capture/src:$(CURDIR)/packages/readonly-analyzer/src \
		LIQVERA_FROZEN_PACKAGE=$(CURDIR)/.stage-a/package \
		$(PYTHON) -B -c "from liqvera_readonly_analyzer.__main__ import main; raise SystemExit(main())"

mvp:
	PYTHONPATH=$(CURDIR)/packages/contracts/src:$(CURDIR)/packages/public-capture/src:$(CURDIR)/packages/readonly-analyzer/src:$(CURDIR)/packages/evidence-report/src \
		$(PYTHON) -B scripts/run-f3-mvp.py

mvp-web:
	PYTHONPATH=$(CURDIR)/packages/contracts/src:$(CURDIR)/packages/public-capture/src:$(CURDIR)/packages/readonly-analyzer/src:$(CURDIR)/packages/evidence-report/src \
		$(PYTHON) -B scripts/run-mvp-web.py

# Full application build targets. Acceptance is a separate explicit command.
liqvera-python:
	$(PYTHON) -B scripts/build-liqvera-python-distributions.py \
		--source-sha $$(git rev-parse HEAD) --out dist/liqvera/python

liqvera-gateway:
	npm ci --ignore-scripts --prefix apps/mezo-gateway
	apps/mezo-gateway/node_modules/.bin/tsc -p packages/mezo-protocol/tsconfig.json
	npm run --prefix apps/mezo-gateway build

liqvera-web:
	npm ci --ignore-scripts --prefix apps/mezo-web
	apps/mezo-web/node_modules/.bin/tsc -p packages/mezo-protocol/tsconfig.json
	npm run --prefix apps/mezo-web build

liqvera-images:
	docker compose -f deploy/mezo-evidence/compose.yaml build

liqvera-compose:
	docker compose -f deploy/mezo-evidence/compose.yaml config --quiet

ACCEPTANCE_PLAN ?= acceptance/offline-plan.json

liqvera-acceptance:
	@test -n "$(ACCEPTANCE_OUTPUT)" || \
		(echo "ACCEPTANCE_OUTPUT is required and must name a new JSON result" >&2; exit 2)
	$(PYTHON) -B scripts/run-mezo-acceptance.py --mode offline --plan "$(ACCEPTANCE_PLAN)" --output "$(ACCEPTANCE_OUTPUT)"

liqvera-acceptance-verify:
	@test -n "$(ACCEPTANCE_RESULT_SHA256)" || \
		(echo "ACCEPTANCE_RESULT_SHA256 is required" >&2; exit 2)
	$(PYTHON) -B scripts/verify-mezo-acceptance.py "$(ACCEPTANCE_OUTPUT)" --sha256 "$(ACCEPTANCE_RESULT_SHA256)"

liqvera-product: liqvera-python liqvera-gateway liqvera-web liqvera-images liqvera-compose
	@echo "Liqvera product artifacts built; acceptance remains a separate explicit target"

INSTALLER_OUT ?= build/installer
INSTALLER_IMAGE_LOCK ?=

liqvera-installer:
	@test -n "$(INSTALLER_IMAGE_LOCK)" || (echo "INSTALLER_IMAGE_LOCK is required" >&2; exit 2)
	$(PYTHON) -B scripts/build-liqvera-installer.py --source-commit "$$(git rev-parse HEAD)" \
		--output "$(INSTALLER_OUT)" --image-lock "$(INSTALLER_IMAGE_LOCK)"

liqvera-installer-verify:
	@digest="$$(sha256sum "$(INSTALLER_OUT)/liqvera-installer-0.0.2.zip" | cut -d' ' -f1)"; \
	destination="$$(mktemp -d)/verified"; \
	$(PYTHON) -B scripts/verify-liqvera-installer.py \
		"$(INSTALLER_OUT)/liqvera-installer-0.0.2.zip" "$$digest" "$$destination"

prod: product
	docker compose -f compose.stage-a.yml run --rm --no-deps prepare-data
	docker compose -f compose.stage-a.yml run --rm --no-deps capture
	docker compose -f compose.stage-a.yml run --rm --no-deps analyzer
	@echo "stage-a production loop passed"
