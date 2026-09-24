# Tasks: Stock at a location

## Setup
- [x] T001 Inventory the current click paths against `origin/main`, record the owner decisions in spec.md, write plan.md.

## US1 — The pair, from the item
- [x] T002 [US1] Write packages/reality-core/tests/test_stock_at_location.py with the pair cases: parity with `inventory_read`, zero and negative pairs, unknown half, a location that forbids stock, exact-location attribution across a parent and a child (FR-002, FR-003, FR-012).
- [x] T003 [US1] Add the `stock` Inspector kind: `stock_inspector` in packages/reality-core/src/reality/web/api.py, the `stock` branch in packages/reality-core/src/reality/services/operational_previews.py, the kind sets in `get_inspector` and `require_tenant_surface_access`; point the item preview's location rows at it (FR-001–FR-004).
- [x] T004 [US1] Extend packages/reality-core/tests/test_operational_previews.py for the pair sections and the retargeted location rows (FR-001, FR-002).

## US2 — A warehouse as a scope
- [x] T005 [US2] Extend test_stock_at_location.py with the register cases: the three scoped views, item plus location, the `shortage` state under a scope, FR-007's item set, unknown location, and the statement-count shape of a scoped stock page (FR-005–FR-007, FR-010).
- [x] T006 [US2] Add `location_id` to `inventory_page`, `reservation_page` and `movement_page` in packages/reality-core/src/reality/web/read_models.py, to `warehouse_register` in packages/reality-core/src/reality/web/warehouse_reads.py (with `scope.location`) and to the endpoint in web/api.py (FR-005, FR-006, FR-010).
- [x] T007 [US2] Web: `Selection.location` and the URL parameter in apps/web/src/unified/routing.ts, the client parameter in apps/web/src/api.ts, the chip, the stated scope and the scoped movement direction in apps/web/src/unified/WarehousePage.tsx (FR-006, FR-008, FR-009).
- [x] T008 [US2] Write apps/web/scripts/stock-at-location-contract.test.mjs for the chip, the URL and the restored scope (FR-008).

## US3 — The pair, from the location
- [x] T009 [US3] Retitle and retarget the location inspector's stock section, carry the item's unit, and add Open warehouse for the location family in apps/web/src/unified/MasterDataPage.tsx (FR-011); cover the rows in packages/reality-core/tests/test_inspector_register.py.

## US4 — Each number answers its own question (added 2026-09-24)
- [x] T014 [US4] Extend test_stock_at_location.py: the location read's query count at two item counts, the record endpoint, named and signed movement rows, the counts, the movement that stayed here (FR-015–FR-017).
- [x] T015 [US4] Give each stock quantity its own destination in apps/web/src/unified/WarehousePage.tsx, with a title that says where it leads (FR-015).
- [x] T016 [US4] Name and sign the location inspector's movement rows; derive `location_detail` set-based, bound what it lists, count what it only counts; read the location record directly in `GET /locations/{id}` (FR-016, FR-017).

## Verification
- [x] T010 Write apps/web/scripts/stock-at-location-browser.mjs for the click path in both editions and themes (SC-001, SC-005).
- [x] T011 German wording in apps/web/src/localization.tsx in the agreed ERP vocabulary; `npm run test:i18n` and `npm run i18n:audit` (FR-014).
- [x] T012 Document the behaviour in docs/WEB_SPEC.md, docs/features/movements.md, docs/features/reservations.md and docs/SPEC_COVERAGE_MATRIX.md.
- [x] T013 Run every gate, measure the scoped page against the unscoped one on a quiet machine (SC-004), check live on the local stack, open the pull request.

Dependencies: T001 → T002 → T003 → T004; T005 → T006 → T007 → T008; T003 and T006 → T009; all → T010 → T013. T002 and T005 share one file and are written before their implementation tasks.

## Verification record (2026-09-23)

- `packages/reality-core/tests/test_stock_at_location.py`: 18 pass, including the pair against
  `location_inventory_rows`, a pair that nets to zero, a negative pair, an unknown pair, a
  location whose `allows_stock` was turned off after its movements, parent/child attribution,
  the three scoped views, combined scopes, the scoped `shortage` state and the query-shape bound.
- The specification claimed `record_movement` accepts a location that forbids stock. It does not
  (`services/core.py:4709`); the case is reachable only by turning the flag off afterwards, and
  both the test and the edge case now say so.
- `apps/web/scripts/stock-at-location-browser.mjs` (en/light, de/dark): pass — a location quantity
  opens the item in that place, the pair reaches both scoped registers, the scope is stated and
  cleared. `stock-at-location-contract.test.mjs`: 7 pass. `npm run test:i18n`: 360 pass.
  `npm run i18n:audit`: 4 × PASS. `npm run build` and `prettier --check .`: green.
- Live against the local stack (branch API on 8099, company `ten_4e24dfbda1`): the scoped stock
  register answers 18 items in Rotterdam and 3 in Singapore; `inspector/stock/{item}:{location}`
  returns the pair with its movements; the location inspector's rows carry the unit and address
  the pair; a location that netted to zero stays listed.
- SC-004, measured back to back on a quiet machine, 2,000 items × 20 locations × 12,000 movements:
  unscoped stock page 145 ms for 2,000 rows, scoped 28 ms for 200 rows (0.19×). The scoped page is
  cheaper because FR-007 narrows the item set; the shape is the same single query.
- Full backend suite: 4,113 pass, 9 skipped. One failure, `test_application_catalog`, came from
  editing that file's pinned counts while the run was in flight; the catalog entry for the new pair
  read raises them from 565 to 566. Re-run afterwards: every suite that reads the isolation catalog,
  627 pass. A second branch adding a discovered operation will conflict on that number.
- `make docs-catalog-check` is red on plain `origin/main` (19 generated files differ, storylines
  and German pages included). Baseline-checked in a detached worktree at `origin/main`: the same
  19 files, so it is not this change. Not repaired here.

## Verification record, US4 (2026-09-24)

- `test_stock_at_location.py` now 22 pass, including the four US4 cases.
- SC-006, same synthetic company as SC-004 (2,000 items, 20 locations): reading one location
  **before** 4,551 ms and 8,002 statements, **after** 12 ms and 6 statements. The statement count
  no longer grows with the item count, which is what the automated test pins; the endpoint
  `GET /locations/{id}` issues 2.
- Live against the local stack: the location explanation reads
  `Supplier Return = -1.0000 pcs · Beacon Desk Organizer · 2026-09-21T19:42:55`, and the demo
  company's transfer whose origin and destination are the same location shows 0 — it changed
  nothing there.
- `stock-at-location-browser.mjs` extended: each of the three quantities is clicked in both
  editions and lands on its own answer. `stock-at-location-contract.test.mjs` 8 pass,
  `npm run test:i18n` 361 pass, i18n audit 4 × PASS, build and prettier green.
- A throwaway measurement company cannot be deleted by removing its business rows alone: the
  scheduler and worker create `projection_row`, `projection_checkpoint`, `scheduled_job` and
  `scheduled_job_run` for it within seconds, and psql runs a multi-statement `-c` as one
  transaction, so one foreign-key error rolls the whole cleanup back.
