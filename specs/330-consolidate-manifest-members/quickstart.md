# Validation Guide

Use `SPECIFY_FEATURE_DIRECTORY=specs/330-consolidate-manifest-members` for Spec Kit commands so the concurrent feature pointer is untouched. Use the repository Python 3.12 virtual environment and an owned isolated PostgreSQL database, with `TEST_POSTGRES_ADMIN_URL` configured according to the existing test fixture contract. Never point migration tests at live business data.

From `packages/reality-core` after implementation:

```sh
../../.venv/bin/pytest -q tests/test_cost_manifest_members.py tests/test_cost_manifest_member_migration.py
../../.venv/bin/pytest -q tests/test_costing_services.py tests/test_costing_tools.py tests/test_cost_records.py tests/test_schema_indexes.py tests/test_reporting_graph_coverage.py
```

Expect five exact-column writable logical resources backed by one physical store, all-family/tenant collision parity, invalid-link refusal, unchanged historical reviews, once-only count/purge and exact populated rollback/re-upgrade. Confirm original columns by PostgreSQL inspection, not ORM metadata alone.

Run the complete backend suite and existing benchmark with its unchanged limits; run the benchmark serially if shared resources distort results. From repository root run `make lint`, `make spec-check`, `make docs-generate`, `make docs-catalog-check`, `make docs-build` and `make web-build`. Record source hashes, database version, commands/results, red-first evidence and any failure in `verification.md`. Do not mark tasks accepted while required checks remain red. Stop/remove only the owned test server after completion.
