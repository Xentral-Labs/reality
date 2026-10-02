# Validation guide

Use only the existing temporary PostgreSQL test fixtures. Do not apply migrations to
business databases for verification.

From packages/reality-core:

```sh
../../.venv/bin/pytest tests/test_account_defaults.py tests/test_account_default_migration.py tests/test_account_deletion.py tests/test_access_application_deletion_api.py
../../.venv/bin/pytest tests/finance tests/test_postgresql_integration.py tests/test_schema_indexes.py tests/test_migrations.py tests/test_cost_projections.py tests/test_cost_projection_migration.py
```

Expect one fewer physical table, identical readable old selections, unsupported legacy
writes, exact migration/rollback and unchanged historical financial account provenance.
Run complete backend and repository build/catalog/spec/lint gates before acceptance;
record actual results in verification.md, retaining red-task status where required.
