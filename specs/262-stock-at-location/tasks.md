# Tasks: Stock at a location

## Setup
- [ ] T001 Inventory the current click paths against `origin/main`, record the owner decisions in spec.md, write plan.md.

## US1 — The pair, from the item
- [ ] T002 [US1] Write packages/reality-core/tests/test_stock_at_location.py with the pair cases: parity with `inventory_read`, zero and negative pairs, unknown half, a location that forbids stock, exact-location attribution across a parent and a child (FR-002, FR-003, FR-012).
- [ ] T003 [US1] Add the `stock` Inspector kind: `stock_inspector` in packages/reality-core/src/reality/web/api.py, the `stock` branch in packages/reality-core/src/reality/services/operational_previews.py, the kind sets in `get_inspector` and `require_tenant_surface_access`; point the item preview's location rows at it (FR-001–FR-004).
- [ ] T004 [US1] Extend packages/reality-core/tests/test_operational_previews.py for the pair sections and the retargeted location rows (FR-001, FR-002).

## US2 — A warehouse as a scope
- [ ] T005 [US2] Extend test_stock_at_location.py with the register cases: the three scoped views, item plus location, the `shortage` state under a scope, FR-007's item set, unknown location, and the statement-count shape of a scoped stock page (FR-005–FR-007, FR-010).
- [ ] T006 [US2] Add `location_id` to `inventory_page`, `reservation_page` and `movement_page` in packages/reality-core/src/reality/web/read_models.py, to `warehouse_register` in packages/reality-core/src/reality/web/warehouse_reads.py (with `scope.location`) and to the endpoint in web/api.py (FR-005, FR-006, FR-010).
- [ ] T007 [US2] Web: `Selection.location` and the URL parameter in apps/web/src/unified/routing.ts, the client parameter in apps/web/src/api.ts, the chip, the stated scope and the scoped movement direction in apps/web/src/unified/WarehousePage.tsx (FR-006, FR-008, FR-009).
- [ ] T008 [US2] Write apps/web/scripts/stock-at-location-contract.test.mjs for the chip, the URL and the restored scope (FR-008).

## US3 — The pair, from the location
- [ ] T009 [US3] Retitle and retarget the location inspector's stock section, carry the item's unit, and add Open warehouse for the location family in apps/web/src/unified/MasterDataPage.tsx (FR-011); cover the rows in packages/reality-core/tests/test_inspector_register.py.

## Verification
- [ ] T010 Write apps/web/scripts/stock-at-location-browser.mjs for the click path in both editions and themes (SC-001, SC-005).
- [ ] T011 German wording in apps/web/src/localization.tsx in the agreed ERP vocabulary; `npm run test:i18n` and `npm run i18n:audit` (FR-014).
- [ ] T012 Document the behaviour in docs/WEB_SPEC.md, docs/features/movements.md, docs/features/reservations.md and docs/SPEC_COVERAGE_MATRIX.md.
- [ ] T013 Run every gate, measure the scoped page against the unscoped one on a quiet machine (SC-004), check live on the local stack, open the pull request.

Dependencies: T001 → T002 → T003 → T004; T005 → T006 → T007 → T008; T003 and T006 → T009; all → T010 → T013. T002 and T005 share one file and are written before their implementation tasks.
