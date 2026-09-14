.PHONY: test lint spec-check status api app docs mcp analytics analytics-down stack dev dev-up dev-logs dev-status dev-down web-build docs-generate docs-catalog-check docs-build railway-deploy compose-up tree

test:
	cd packages/reality-core && ../../.venv/bin/pytest
lint:
	cd packages/reality-core && ../../.venv/bin/ruff check .
spec-check:
	python3 scripts/check_spec_policy.py
status:
	cd packages/reality-core && ../../.venv/bin/python -m reality.cli.app status
api:
	docker compose up --build api
app:
	docker compose up --build web
docs:
	docker compose up --build docs
mcp:
	docker compose up --build mcp
analytics:
	docker compose -f compose.analytics.yml up --build
analytics-down:
	docker compose -f compose.analytics.yml down --remove-orphans
stack:
	docker compose up --build
dev:
	docker compose -f compose.yml -f compose.dev.yml up --build
dev-up:
	docker compose -f compose.yml -f compose.dev.yml up --build --detach
dev-logs:
	docker compose -f compose.yml -f compose.dev.yml logs --follow --tail=200
dev-status:
	docker compose -f compose.yml -f compose.dev.yml ps
dev-down:
	docker compose -f compose.yml -f compose.dev.yml down --remove-orphans
web-build:
	cd apps/web && npm run format:check && npm run test:i18n && npm run i18n:audit && npm run build
docs-generate:
	PYTHONPATH=packages/reality-core/src .venv/bin/python apps/docs/scripts/generate-catalog-reference.py
docs-catalog-check: docs-generate
	git diff --exit-code -- apps/docs/content/tool-usage apps/docs/content/de/tool-usage apps/docs/content/storylines apps/docs/content/de/storylines apps/docs/content/public/storylines apps/docs/.vitepress/data
docs-build: docs-generate
	PYTHONPATH=packages/reality-core/src .venv/bin/python -m unittest discover -s apps/docs/scripts -p 'test_*_reference.py'
	cd apps/docs && npm run format:check && npm run test && npm run build
railway-deploy:
	./scripts/deploy_railway_demo.sh
compose-up:
	docker compose up --build
tree:
	find . -maxdepth 4 -type f | sort
