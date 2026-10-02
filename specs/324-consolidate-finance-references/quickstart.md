# Validation Guide

Use disposable PostgreSQL through `TEST_POSTGRES_ADMIN_URL` and installed `.venv`. From `packages/reality-core` run:

```bash
../../.venv/bin/pytest -q tests/test_finance_reference_store.py tests/test_finance_reference_migration.py
../../.venv/bin/pytest -q tests/finance/test_references.py tests/finance/test_target_mappings.py tests/finance/test_source_mappings.py tests/finance/test_components.py
```

Expect one physical store, both original writable logical names, exact ID/column parity and exact populated rollback schema. Run full backend, migration/index, company deletion and repository documentation/build gates per plan. Never migrate a live company for verification.
