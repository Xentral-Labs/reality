# Validation guide: Decision-gated interpretation and admission

**Status**: Initial explicit preparation/approval tests and tools are implemented.
Full rollout and its remaining acceptance proofs are pending; consult the feature
contract and measured verification evidence before making completion claims.

## Prerequisites

Use the repository Python environment and an isolated PostgreSQL instance as
required by `packages/reality-core/tests/conftest.py`. Never run destructive fixtures
against a tenant's production database. Use scoped source fixtures and separate
reviewer/foreign-tenant principals. Frontend checks use the existing npm setup.

## Focused verification after implementation

```bash
.venv/bin/pytest packages/reality-core/tests/test_intake_admission.py packages/reality-core/tests/test_source_ingestion.py packages/reality-core/tests/test_unified_item_csv_import.py packages/reality-core/tests/test_proposal_decision_policy.py packages/reality-core/tests/test_decision_attribution.py
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
