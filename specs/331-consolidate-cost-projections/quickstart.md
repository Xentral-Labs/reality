# Validation guide

Run from repository root with the existing virtual environment and PostgreSQL test
instance available at the configured TEST_POSTGRES_ADMIN_URL. Tests create isolated
databases; never point migration checks at a business database.

```sh
make spec-check
cd packages/reality-core
../../.venv/bin/pytest tests/test_cost_projections.py tests/test_cost_projection_migration.py
../../.venv/bin/pytest tests/test_inventory_generations.py tests/test_contribution_generations.py tests/test_captured_report.py tests/test_company_generation_jobs.py tests/test_cost_records.py
```

Expect four shared physical output tables, thirteen logical compatibility views, exact
legacy result/identity parity, tenant and family rejection, safe retries/publication,
and a lossless populated downgrade. Then run repository lint, complete tests, catalog
and build gates. Record actual results in verification.md; red checks stay incomplete.
