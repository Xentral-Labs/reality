# Quickstart: Validate Canonical Core Catalogs

No PostgreSQL service or `REALITY_DATABASE_URL` is required for focused catalog tests.

```bash
.venv/bin/pytest -q backend/tests/test_application_catalog.py
python3 scripts/check_spec_policy.py
make lint
make test
make frontend-build
```

Expected evidence: four categories; all known Events including `fact.observed`,
`payment_term.updated`, `price_list.updated`, and `party_group.updated`; exact
Projection coverage; offline validation; authorized reference access; and no hard-coded
frontend Projection inventory.

## Verified 2026-08-31

- Focused catalog and HTTP boundary tests on the isolated PR branch: `10 passed`.
- Complete isolated backend suite: `137 passed, 7 skipped` with `PYTHONPATH` pinned to
  the PR worktree so the shared editable virtual environment cannot import another
  worktree's sources.
- Ruff: all checks passed.
- Spec policy: passed.
- Frontend TypeScript and Vite production build: passed.
- i18n audit executed and reported 28 pre-existing untranslated English strings; this
  feature introduced no new listed string.
- Offline load with an unreachable PostgreSQL URL validated 37 Events and 48 data-model
  tables without making a database connection.
- No Alembic migration or database schema change was introduced.
