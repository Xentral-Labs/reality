# Tasks: An Inspector row states one measure

## Setup
- [x] T001 Inventory every `value · qualifier` compound in the two row builders against `main` at 2a1725cd; classify each as qualifier or second measure; record the classification and the owner decisions in spec.md, write plan.md.

## US1 — A section's measures read as one column
- [x] T002 [US1] Add `meta`/`meta_parts` to `_row` in packages/reality-core/src/reality/services/operational_previews.py and to `InspectorRow` in apps/web/src/api.ts (FR-001, FR-002, FR-008).
- [x] T003 [US1] Render the measure and the qualifier as separate columns in `InspectorContent` in apps/web/src/unified/Inspector.tsx, stacked in `compact`; new class strings as module constants so the i18n audit passes (FR-005).
- [x] T004 [US1] Convert `stock_at_location` in operational_previews.py as the prototype the owner asked to judge before the rollout (FR-001, FR-003).
- [x] T005 [US1] Extend packages/reality-core/tests/test_stock_at_location.py: measure and moment as separate fields, and an import without a clock stating only its day (FR-001, FR-004).
- [x] T006 [US1] Write apps/web/scripts/inspector-row-shape.test.mjs: separate elements, tabular figures, the reserved column, the stacked compact preview, the unchanged plain row (FR-005, FR-008).

## US2 — A time that was never recorded is not shown
- [x] T007 [US2] Add `moment()` to packages/reality-core/src/reality/services/inspector_presentation.py, shared by both row builders (FR-004).
- [x] T008 [US2] Cover `moment()` in packages/reality-core/tests/test_inspector_presentation.py for the midnight, real-clock and `None` cases (FR-004).

## US3 — The link is the row, not the sentence
- [x] T009 [US3] Make the whole row the click target with a hover surface; move the accent and underline to the measure alone; keep the divider one width across linked and plain rows (FR-006).

## US4 — Nothing is lost where there is no second column
- [x] T010 [US4] Add `inspectorMeta` and `inspectorRowText` to apps/web/src/unified/inspectorFormat.ts; stack the qualifier in apps/web/src/unified/ContextExplorer.tsx; use the recomposed string for graph nodes and titles in apps/web/src/unified/ObjectGraph.tsx (FR-007).

## Rollout
- [x] T011 Add `meta` to `inspector_row` in packages/reality-core/src/reality/web/api.py with the same spelling `_row` uses (FR-009).
- [x] T012 Convert the ten qualifier compounds in web/api.py: the commitment inspector's reservations and movements, the three commitment lists, the ledger rows (measure and qualifier swap), the item and location recent movements, the shipment contents, the payment allocations (FR-001, FR-003, FR-010).
- [x] T013 Update `test_location_movements_name_their_item_and_their_direction` in test_stock_at_location.py: the item name is asserted in `meta` and asserted absent from the value, so the split cannot regress unnoticed.

## Verification
- [x] T014 Extend apps/web/scripts/stock-at-location-browser.mjs's stock fixture to the new row shape; add `inspectorMeta` to the `inspectorFormat` stub in apps/web/scripts/cost-record-inspector.test.mjs.
- [x] T015 Run the gates: `ruff check`, `ruff format`, `tsc -b`, `npm run build`, `npm run i18n:audit`, `npm run test:contracts`, and the python suites covering every converted inspector.
- [x] T016 Extend `specs/209-operational-previews/contracts/preview.md` with the optional `meta`/`meta_parts` field, add the coverage-matrix rows for spec 268, run `make spec-check`. Open the pull request (owner).

Dependencies: T001 → T002 → T003 → T004 → T005/T006; T007 → T008; T002 and T003 → T009, T010; T011 → T012 → T013; all → T014 → T015 → T016.

## Verification record (2026-09-24)

- `packages/reality-core/tests/test_inspector_presentation.py`: 8 pass, including the two
  new cases.
- `packages/reality-core/tests/test_stock_at_location.py`: 24 pass, including the two new
  cases and the amended location-movement assertion.
- `packages/reality-core/tests/`: `test_operational_previews`, `test_master_data_api`,
  `test_reference_workspace`, `test_unified_invoice_credit`, `test_unified_delivery_reads`,
  `test_shipment_api`, `test_partial_invoicing_rebilling`, `test_unified_customer_refund`
  all pass against the converted inspectors.
- `apps/web`: `tsc -b` clean, `npm run build` clean, `npm run i18n:audit` passes in en/de/nl/es,
  `npm run test:contracts` 368 pass (363 before, plus the five new row-shape cases).
- One pre-existing test needed the new field: `cost-record-inspector.test.mjs` stubs
  `./inspectorFormat` and had to learn `inspectorMeta`. It is a stub gap, not a behaviour
  change.
- `make spec-check`: passes with the new `specs/268-inspector-row-measure/` and the four
  coverage-matrix rows.
- `make lint`: **red, and red before this change.** 22 `I001` import-sort findings, all in
  test modules this feature does not touch — some on committed code, some in unrelated
  working-tree changes. Run from `packages/reality-core` as the gate does, `ruff check` and
  `ruff format --check` are clean on every file this feature changed. SC-006 is therefore not yet met and cannot be met by this feature alone;
  the pre-existing findings belong to whoever owns those modules.
- Owner review: prototype screenshotted from the real component before the rollout; the
  qualifier column was changed from left- to right-aligned on the owner's call.

## Note on order

The specification was written after the implementation, in the same session. The mandated
path is specify → plan → tasks → implement; here the owner asked for a proposal, then a
prototype, then the rollout, and the specification recorded the settled shape. This is
stated in spec.md under "Deviation from the mandated path".
