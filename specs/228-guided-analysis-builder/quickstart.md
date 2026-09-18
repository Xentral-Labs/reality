# Validation

1. Start PostgreSQL and the normal API/web stack (`make dev-up`).
2. Open Analytics, select a declared example, change a period/filter/group and check matching results.
3. Open Connections; select a node and edit its conditions, then return to Result.
4. Open Cypher; execute the generated text with parameters; introduce an error, switch tabs and verify the draft survives.
5. Save a successful query and reopen it from My reports. Check different companies and owners do not share drafts/reports.
6. Check 390px/1440px layouts and keyboard tabs/controls.
7. Run `make spec-check`, `make lint`, `make test`, `make web-build`, `make docs-generate`, `make docs-catalog-check`.

Expected: real bounded results, no false freshness/financial KPI claims, unchanged fan-out/unit refusals, no query clause loss.
