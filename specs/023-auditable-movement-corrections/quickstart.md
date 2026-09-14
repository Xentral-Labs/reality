# Quickstart: Validate Auditable Movement Corrections

## Migration proof

```bash
cd packages/reality-core
alembic upgrade head
alembic downgrade -1
alembic upgrade head
pytest -q tests/test_migrations.py
```

Expected: the empty correction relation upgrades and downgrades cleanly; schema/model
parity passes. A guarded downgrade refuses destructive removal after correction rows
exist.

## Focused domain and derived-state proof

```bash
cd packages/reality-core
pytest -q \
  tests/test_movement_corrections.py \
  tests/test_inventory_and_fulfillment.py \
  tests/test_inventory_tracking_reservations.py \
  tests/operational_exceptions \
  tests/test_materialized_projections.py
```

Expected: all Movement types void and replace exactly; original/source/Reservation
history remains; stock, fulfilment, status, identity location, exceptions, and
projections show one net correction; invalid/dependent/retry/concurrent cases have no
partial effect.

## Boundary, event, and tenant proof

```bash
cd packages/reality-core
pytest -q \
  tests/test_master_data_api.py \
  tests/test_application_tools.py \
  tests/test_ai_mcp.py \
  tests/test_business_events.py \
  tests/test_application_catalog.py \
  tests/tenant_isolation
ruff check .
```

Expected: API/CLI/tool/MCP use shared behavior, interactive mutations require
confirmation, one event is emitted, catalogs agree, and foreign-tenant references do not
disclose or mutate data.

## Web proof

```bash
cd apps/web
npm run build
npm run i18n:audit
npm run test:i18n
```

Manual acceptance in EN, DE, NL, and ES:

1. Open an eligible Movement and select Correct.
2. Preview a void and verify exact inverse/net effects; cancel and verify no change.
3. Preview a quantity/location replacement, confirm, and verify list badges and final stock.
4. Inspect original, compensation, and replacement; verify the same complete chain,
   reason, actor/time, event, net effects, and direct source evidence.
5. Retry the same request and verify no second effect; submit a stale divergent preview
   and verify refresh guidance.
6. Verify mobile layout and compare Web results with the API/CLI preview for parity.

## Full regression and closure

```bash
cd packages/reality-core
pytest -q
cd ../..
.venv/bin/python scripts/check_spec_policy.py
```

Only after all automated gates and final owner review pass may `009/FR-009` and the
coverage-matrix Movement-correction gap become verified.

## Observed implementation results — 2026-08-31

- Focused correction/stock/fulfilment/tracking/exception/API slice: **52 passed**.
- Migration proof from the package directory: **2 passed**.
- Adapter, catalog, tool, MCP, and HTTP slice: **42 passed, 2 skipped**.
- Ruff: **passed**.
- Complete PostgreSQL backend suite: **214 passed, 7 skipped**.
- Web production build: **passed**; Vite retains the existing non-blocking chunk-size
  warning for the main bundle.
- EN/DE/NL/ES audit: **684/684 entries covered in every language**.
- Web localization/product-boundary suite: **11 passed**.

The six-step manual Web acceptance above and final product-owner review remain open.
