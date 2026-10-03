# Validation guide: Intake decision coverage, demo and safe rollout

**Status**: Planned runtime validation. New tests/tools named here do not exist yet;
do not present these scenarios as executed implementation evidence.

## Prerequisites

Use the repository Python environment and an isolated PostgreSQL instance as
required by `packages/reality-core/tests/conftest.py`. Never run destructive fixtures
against a tenant's production database. Use scoped source fixtures and separate
reviewer/foreign-tenant principals. Frontend checks use the existing npm setup.

## Focused verification after implementation

```bash
.venv/bin/pytest packages/reality-core/tests/test_intake_rollout_coverage.py packages/reality-core/tests/test_demo_data_intake.py packages/reality-core/tests/test_demo_data_security.py packages/reality-core/tests/test_demo_data_startup.py packages/reality-core/tests/test_demo_data_api.py packages/reality-core/tests/test_demo_entrypoint_parity.py packages/reality-core/tests/test_decision_trail_details.py
```

Exercise every spec acceptance scenario, inspect accepted-record counts before
approval, then inspect source → decision → receipt → effects after approval.
Repeat with foreign IDs, stale source/state/permission, concurrent approvers and
failure injection on both sides of commit. Verify that recovery reads do not mutate.

## Required repository gates

```bash
make spec-check
make lint
make test
make web-build
make docs-generate
make business-annotations-check
```

When command/event/MCP schemas change, regenerate and inspect the catalog outputs,
then run `make docs-catalog-check` against the committed/generated baseline.
Run migration/rollback tests when schema changes. Use the existing browser harness
for changed review/import surfaces; frontend build alone is not a browser proof.

## Expected result

Zero accepted business effects before approval; one coherent result per exact
approved unit; unchanged raw data and truthful pending/refused/replayed outcomes.
All required checks must be green before tasks or release status are marked done.
