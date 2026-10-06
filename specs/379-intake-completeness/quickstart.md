# Validation

Use the repository virtual environment and the existing disposable PostgreSQL test fixture (never the retained simulator database).

1. Run `cd packages/reality-core && ../../.venv/bin/pytest tests/test_intake_completeness.py tests/scenarios/test_live_company.py`.
2. Run affected intake, pricing, company-date, adapter and business-story groups.
3. Run `make lint`, `make spec-check`, `make business-annotations-check`, `make docs-generate`, `make test`, `make web-build`, and `make docs-build`.
4. Create the PR and require all GitHub quality jobs for the current head to succeed. Do not report queued/running jobs as green.

Expected: raw retention with no business effects for essential gaps; allowed incomplete orders show review issues; dated simulator orders and replay are exact; original amounts and tenant guards remain intact.
