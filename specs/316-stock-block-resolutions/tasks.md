# Tasks: Stock Blocks Keep What Was Stated

**Input**: [spec.md](spec.md), [plan.md](plan.md), [data-model.md](data-model.md)

## Phase 1: Tests first

- [x] T001 [FR-001, FR-002, FR-003, FR-007, DR-001, DR-002] Rewrite the release/scrap tests in `packages/reality-core/tests/test_stock_blocks.py`: block 20, release 5, scrap 3, release 12. Check the stated quantity, one id, the resolutions, the open quantity and the derived status. Add schema checks for the resolution table.
- [x] T002 [FR-005] Add to `tests/test_stock_blocks.py`: a block made by a receipt keeps `receipt_movement_id` after a whole scrap; the scrap's movement sits on its resolution.
- [x] T003 [FR-008] Migration test in `tests/test_stock_blocks.py`: seed a 304-shaped chain at `0108`, upgrade, assert the fold and unchanged blocked quantity; downgrade refuses with resolutions.
- [x] T004 [FR-004, SC-002] Extend `tests/test_stock_block_readers.py`: after a partial release and a partial scrap, every reader subtracts the open quantity.
- [x] T005 [FR-006] Update `tests/test_stock_block_adapters.py` for the `active|resolved|all` filter and the row shape.

## Phase 2: Schema and shared rule

- [x] T006 [DR-001, DR-002] Migration `packages/reality-core/migrations/versions/0109_stock_block_resolution.py` and the `StockBlock` / `StockBlockResolution` models in `src/reality/db/core.py`.
- [x] T007 [FR-003, FR-004, SC-003] `_open_stock_blocks` in `src/reality/services/core.py`. Use it in `blocked_quantity` and `blocked_within_identity`, in the item supply read, in `web/read_models.py`, `services/inventory_positions.py`, `services/projections.py` and `services/exceptions.py`, and in the correction guard.

## Phase 3: Service and adapters

- [x] T008 [FR-001, FR-002, FR-007] `src/reality/services/stock_blocks.py`: append-only resolutions, open-quantity validation and review, row shape, list filter. Add `_movement_id` to `record_movement`.
- [x] T009 [FR-006] MCP enum in `src/reality/mcp/catalog.py`; `apps/web/src/api.ts` and `apps/web/src/unified/StockBlockCard.tsx`.

## Phase 4: Gates and docs

- [x] T010 Reporting-graph coverage, `tests/test_schema_indexes.py`, the isolation catalog and its pinned count, `docs/SPEC_COVERAGE_MATRIX.md`.
- [x] T011 `docs/DATA_MODEL.md`, `docs/features/inventory.md`, `make docs-generate`.
- [ ] T012 Full suite, ruff, web build/format/i18n checks; diff review against the spec. Done locally: ruff, web format/build/i18n, the stock-block, inventory, fulfillment, correction, delivery-action, exception, projection and story suites (427 tests), the catalog/isolation/graph/index gates and migrations. The full suite runs in CI.
