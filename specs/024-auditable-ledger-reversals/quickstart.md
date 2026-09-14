# Quickstart: Validate Auditable Ledger Reversals

## Migration proof

```bash
cd packages/reality-core
alembic upgrade head
alembic downgrade -1
alembic upgrade head
pytest -q tests/test_migrations.py
```

Expected: empty relation round-trips, schema/model parity passes, and destructive
downgrade refuses once reversal rows exist.

## Domain and settlement proof

```bash
cd packages/reality-core
pytest -q \
  tests/test_ledger_reversals.py \
  tests/test_ledger.py \
  tests/operational_exceptions \
  tests/test_materialized_projections.py
```

Expected: complete groups reverse exactly once; originals/evidence/allocations remain;
balances, open items, payments, exceptions, and projections share corrected truth;
invalid, stale, concurrent, foreign, and injected-failure cases have no partial effect.

## Boundary, event, and tenant proof

```bash
cd packages/reality-core
pytest -q \
  tests/test_master_data_api.py \
  tests/test_cli.py \
  tests/test_application_tools.py \
  tests/test_ai_mcp.py \
  tests/test_business_events.py \
  tests/test_application_catalog.py \
  tests/tenant_isolation
ruff check .
```

Expected: all adapters use shared preview/execute behavior, confirmation is enforced,
one event is emitted, catalogs agree, and tenant boundaries disclose nothing.

## Web proof

```bash
cd apps/web
npm run build
npm run i18n:audit
npm run test:i18n
```

Manual acceptance in EN, DE, NL, and ES:

1. Open an eligible posting group and select Reverse.
2. Verify exact inverse entries, affected allocations, and resulting values; cancel and
   verify no effect.
3. Preview again, confirm, and verify roles and corrected finance values.
4. Inspect both groups and verify one complete chain, reason, actor/time, Evidence,
   allocation activity, net effects, and event.
5. Retry identically and verify no duplicate; attempt stale/different confirmation and
   verify refresh guidance.
6. Verify mobile layout and compare Web with API/CLI preview.

## Full regression and closure

```bash
cd packages/reality-core
pytest -n 2 --dist loadscope
cd ../..
.venv/bin/python scripts/check_spec_policy.py
```

Only after every automated gate and final owner review passes may `012/FR-008` and only
its coverage-matrix gap become verified.

## Observed automated results — 2026-09-01

- Focused domain, finance, API, catalog, and tenant suite: `60 passed`.
- Alembic upgrade/schema/model migration suite: `2 passed`.
- Complete parallel PostgreSQL backend suite: `219 passed, 7 skipped`.
- Ruff on every changed Python implementation/test file: passed. The repository-wide
  invocation still reports pre-existing import-order findings in unrelated test files.
- Web production TypeScript/Vite build: passed (only the existing bundle-size warning).
- Web localization audit: EN/DE/NL/ES each `695/695`, with zero missing or invalid keys.
- Web localization/product boundary contracts: `11 passed`.
- Spec policy and `git diff --check`: passed.

Manual EN/DE/NL/ES desktop/mobile acceptance and product-owner final review were
approved on 2026-09-01. The implementation and final review gates are closed.
