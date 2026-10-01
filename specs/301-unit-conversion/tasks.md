# Tasks: Unit Conversion Between Purchase and Stock Units

**Input**: Design documents from `/specs/301-unit-conversion/`

**Tests**: Tests precede each phase. Every "not reported" assertion has a positive control; every refusal asserts its code. `core/` means `packages/reality-core/`.

## Phase 1: Specification and Design Gates

- [x] T001 Record the owner's four decisions in `specs/301-unit-conversion/spec.md`
- [x] T002 Record today's behaviour and the design in `research.md`, `data-model.md` and `contracts/receipts-in-purchase-units.md`
- [x] T003 Complete the Constitution Check and design in `plan.md`

## Phase 2: Shared rule and schema

- [x] T004 Failing tests in `core/tests/test_purchase_units.py`:
  - the shared rule moved to `domain/units.py` behaves as before (the existing comparability tests stay green);
  - `promise_unit` tells a new promise from a recorded one;
  - the migration upgrades and downgrades, refusing while stated receipts exist;
  - the pairing check refuses one stated value without the other.
- [x] T005 `domain/units.py`, `exceptions._in_unit` importing it, migration `0106`, model columns (deferred, `FetchedValue`), `data_model.yaml` and the schema gates.

## Phase 3: Purchase orders and receipts (FR-001 to FR-003)

- [x] T006 [US1] Failing tests:
  - a purchase order of 5 cartons (factor 12) keeps the line at 5 box and promises 60;
  - a line in the stock unit is unchanged (control);
  - a line in pallets is refused with `purchase_unit_not_convertible`;
  - a receipt of 5 cartons records 60, keeps `5 box`, raises stock by 60 and closes the promise;
  - a receipt in the stock unit is unchanged (control);
  - a receipt in pallets is refused with `movement_unit_not_convertible`;
  - 6 cartons exceed the open 60 and are refused;
  - sales lines are unchanged.
- [x] T007 [US1] The conversion in `create_manual_order` (purchase only) and in `record_movement` / `_append_movement`; the refusal codes with translations.

## Phase 4: Readers (FR-001, FR-002)

- [x] T008 [US1] Failing tests:
  - a supplier invoice of 5 cartons against the received 60 reports neither `receipt_unbilled` nor `billed_not_received` (control: an invoice of 4 cartons reports one);
  - `item_oversold` counts a new promise once, not twelve times;
  - a recorded purchase-unit promise is named by `units_not_comparable` with `promise_in_purchase_unit`;
  - the delivery case shows open and received in both units;
  - costing needs no change: it takes the receipt's `quantity` as the stock-unit basis (`costing._admit_receipt`), which is what the receipt now records.
- [x] T009 [US1] The readers, `promise_unit` everywhere it decides, the reason in the catalog description, and the delivery-case values.

## Phase 5: Adapters and Web (FR-004)

- [x] T010 Failing adapter tests in `core/tests/test_purchase_unit_adapters.py`:
  - the MCP schemas carry `unit` and stay strict;
  - propose then confirm a receipt in cartons;
  - the Web pass-through;
  - the CLI `--unit`;
  - another company refused.
- [x] T011 MCP, Web and CLI wiring and the catalogs. Web:
  - the receipt form's unit selector and the converted quantity in the review;
  - the movement inspector's stated pair;
  - translations, with `npm run test:i18n`, the audit, prettier and the build.

## Phase 6: Story and Guide (FR-005)

- [x] T012 Business story O05 in `core/tests/scenarios/test_catalog_purchasing.py`.
- [x] T013 Promote O05 with story-first evidence and English and German keywords, and check that neighbouring questions keep their journeys. Update coverage, the roadmap and the coverage matrix, then run `make docs-generate`.

## Phase 7: Verification

- [x] T014 Full backend suite and the web checks (run alone)
- [x] T015 Manual check per `quickstart.md` on an isolated stack
- [x] T016 Review of the diff; fix findings
  - The promise records its unit (`commitment.unit`, owner decision), and line quantities convert by the relation fixed at ordering.
  - Billable positions and the practice lesson read deliveries in the line's unit.
  - An old order refuses a receipt in cartons.
  - The web resets the unit when the order changes.
  - The purchase view reads the promise in force.
  - A conversion that does not divide is named before an old purchase.
