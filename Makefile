.PHONY: verify verify-packages artifacts wheels product \
	liqvera-python liqvera-gateway liqvera-web liqvera-images liqvera-compose \
	liqvera-acceptance liqvera-acceptance-verify liqvera-product

PYTHON ?= python3

wheels: liqvera-python

artifacts:
	$(PYTHON) -B scripts/check-python-artifacts.py --forbid-path 'cmd/**' 'internal/**' 'go.mod' 'go.sum' --forbid-binary engine

verify-packages:
	$(PYTHON) -B -m pytest tests -q

verify: artifacts verify-packages
	@echo "Liqvera local Python verification passed"

product: liqvera-product

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
