# Tasks: Blocked Stock and Best-Before Dates

**Input**: Design documents from `/specs/304-blocked-stock/`

**Tests**: Tests precede each phase. Every "not reported" or "unchanged" assertion has a positive control, and every refusal asserts its code. `core/` means `packages/reality-core/`.

## Phase 1: Specification and Design Gates

- [x] T001 Record the owner's four decisions in `spec.md`
- [x] T002 Record today's behaviour and the design in `research.md`, `data-model.md` and `contracts/blocked-stock.md`
- [x] T003 Complete the Constitution Check and design in `plan.md`

## Phase 2: Schema and services (FR-001, FR-003)

- [x] T004 Failing tests in `core/tests/test_stock_blocks.py`:
  - migration and checks;
  - blocking up to what is free, and its refusals (beyond free stock, beyond what is not reserved, unknown reason, foreign tenant);
  - blocking by lot or serial;
  - partial and full release and scrap, with their split rows and events;
  - a scrap's adjustment;
  - no movement for a block or release.
- [x] T005 Migration `0108`, `StockBlock`, `services/stock_blocks.py`, `blocked_quantity`, refusals with translations, and the table gates.

## Phase 3: Readers (FR-002)

- [x] T006 Failing tests in `core/tests/test_stock_block_readers.py`:
  - reserving takes only unblocked stock;
  - shipping, transferring or adjusting out blocked stock is refused;
  - inventory and detail rows show blocked and available;
  - readiness, the queue, item_oversold, reorder points, stock in another warehouse and stock expired all subtract blocks;
  - nothing changes without blocks;
  - releasing restores availability.
- [x] T007 The readers, the projection invalidation, and `test_expiry_blocks_nothing` restated.
  - `test_expiry_blocks_nothing` stays as it is: the date still blocks nothing by itself.

## Phase 4: Receipt and adapters (FR-001, FR-004)

- [ ] T008 Failing tests in `core/tests/test_stock_block_adapters.py`:
  - a reviewed receipt with a blocked part, and the package receipt;
  - MCP block, release and scrap propose and confirm with strict schemas;
  - Web and a foreign tenant;
  - CLI.
- [ ] T009 Receipt blocking, the delivery-action reviews, MCP, Web, CLI and the catalogs.

## Phase 5: Web

- [ ] T010 The warehouse view's blocked column and Block action; the blocks list with release and scrap; "Of which blocked" in the receipt form; "Block" on the expired-stock finding.
- [ ] T011 Translations, `test:i18n`, the audit, the build and the browser fixtures.

## Phase 6: Stories and Guide (FR-005)

- [ ] T012 Stories B05, H08, H15 and J05.
- [ ] T013 Promotion, routing check, coverage, roadmap, matrix, `docs/features/inventory.md` and `make docs-generate`.

## Phase 7: Verification

- [ ] T014 Full backend suite and web checks
- [ ] T015 Manual check per `quickstart.md`
- [ ] T016 Review of the diff; fix findings
