# Validation Guide: Census Membership

Status: implemented; current-main integration verification in progress.

## Prerequisites

Read spec/plan/contracts, pass tasks/analyze gates and freeze actual isolated revision-
0120 predecessor DDL first. Use Python 3.12+, existing .venv and an owned isolated
PostgreSQL server. Supply `TEST_POSTGRES_ADMIN_URL`; fixtures create disposable DBs.
Never point at live company data. Preserve durability/UTC and original benchmark limit.
Set `SPECIFY_FEATURE_DIRECTORY=specs/327-consolidate-census-members` to avoid disturbing
concurrent active feature 325. Do not switch/stage/commit the shared workspace.

## Planned targeted checks

From repository root after test-first implementation:

```bash
cd packages/reality-core
../../.venv/bin/pytest -q tests/test_cost_census_members.py tests/test_cost_census_member_migration.py
../../.venv/bin/pytest -q tests/test_cost_census_storage.py tests/test_cost_census_migration.py tests/test_cost_captured_basis_storage.py tests/test_cost_captured_basis_migration.py tests/test_company_generation_manifest.py tests/test_cost_records.py tests/test_schema_indexes.py tests/test_reporting_graph_coverage.py
```

Expected: exact original 6/6/7/7 fields; four families/two tenants/equal IDs; NULL outcome;
real family-safe self/consumer FKs; physical/logical immutability and both admission/seal
race orders; populated upgrade/downgrade/re-upgrade and exact predecessor guards.
Count once; preserve migrated protected-history purge refusal and rollback isolation.

## Complete acceptance

From root run `make lint`, `make spec-check`, `git diff --check`, `make docs-generate`,
`make docs-catalog-check`, `make docs-build`, `make web-build`. Catalog checking needs
an isolated staged generated baseline, not staging the shared user index.
Run the complete backend suite with only its existing 10,000-source benchmark separated
for a subsequent unchanged serial run. Record exact commands/source SHA/logs/counts.

The original planning baseline was 147/21. Integrated with main c55e0714, the
pre-census model is 153/21 and the result is 150 physical tables/25 views; invariant
saving is exactly three. Do not count targeted
reruns twice or call planning readiness acceptance. Stop only the owned test server;
no live migration, merge or deployment follows automatically.
