# Tasks: Reorder Point and Replenishment Proposal

**Input**: Design documents from `/specs/302-reorder-point/`

**Tests**: Tests precede each phase. Every "not reported" assertion has a positive control, and every refusal asserts its code. `core/` means `packages/reality-core/`.

## Phase 1: Specification and Design Gates

- [x] T001 Record the owner's four decisions in `specs/302-reorder-point/spec.md`
- [x] T002 Record today's behaviour and the design in `research.md`, `data-model.md` and `contracts/reorder-points.md`
- [x] T003 Complete the Constitution Check and design in `plan.md`

## Phase 2: Schema and services (FR-001)

- [x] T004 Failing tests in `core/tests/test_reorder_points.py`:
  - the migration upgrades and downgrades, and refuses while points exist;
  - the unique key and the value check;
  - setting, changing and removing a point, with events;
  - refusals for a non-stocked or inactive item, a location without stock, invalid values, a change since the review, and removing a point that does not exist;
  - another company sees and changes nothing.
- [x] T005 Migration `0107`, `ItemReorderPoint`, `services/reorder_points.py` and the refusal codes with translations. Also `data_model.yaml` and the docs field rows, the reference and isolation catalogs and their counts, and `resource_catalog.yaml`.

## Phase 3: The derived proposal (FR-002, FR-003)

- [x] T006 [US1] Failing tests in `core/tests/test_reorder_point_reached.py`:
  - at or below the point is reported (boundary: equal is reported; one above is not, as control);
  - only the location below is reported;
  - active reservations reduce available stock, and released ones do not;
  - an open purchase to the location counts as incoming, a purchase to another location does not, and a received or cancelled purchase is no longer incoming;
  - a revised promise counts as revised;
  - an old promise in cartons is converted by the factor;
  - the proposed quantity is in cartons when it divides and in pieces otherwise;
  - the supplier and price come from one purchase list, direct or through a group;
  - several or no suppliers name none (`supplier_choice`);
  - a sales list never counts;
  - an item without a point is never reported, whatever its stock;
  - the statement count does not grow with the number of points;
  - ids are unique, and tenants are isolated.
- [x] T007 [US1] `_reorder_point_reached_exceptions`, registered in every place the class gates name. Also the catalog entry, the narrowed-refresh dependencies, and the explanation with scalar causal values and structures in the trace.

## Phase 4: Adapters (FR-004)

- [x] T008 Failing adapter tests in `core/tests/test_reorder_point_adapters.py`:
  - the MCP schemas are strict;
  - propose then confirm set and remove;
  - the review shows the current and the new values;
  - Web read and proposal, with a foreign tenant refused;
  - CLI list, set and remove;
  - an MCP `order_create_propose` filled from an entry's causal values creates the order on confirmation and clears the entry.
- [x] T009 Application tools, MCP tools, topic and guidance, Web endpoints and the CLI group. Also the command catalog descriptions and `make docs-generate`.

## Phase 5: Web (FR-004)

- [x] T010 Web:
  - the master-data item detail gets the "Reorder points" section with `ReorderPointCard` (set, change, remove through the review);
  - `AttentionPage` gets "Prepare purchase order" for `reorder_point_reached`;
  - `OrderCard` takes an `initial` draft.
- [x] T011 Translations, `npm run test:i18n`, the audit, prettier and the build. Add a browser test in the sharded web suite if the item detail has one.
  - The item detail has none; the page is checked in the browser in T015.

## Phase 6: Story and Guide (FR-005)

- [ ] T012 Business story G02 in `core/tests/scenarios/test_catalog_purchasing.py`.
- [ ] T013 Promote G02 with story-first evidence and English and German keywords, and check that neighbouring questions keep their journeys. Update coverage, the roadmap and the coverage matrix, then run `make docs-generate`.

## Phase 7: Verification

- [ ] T014 Full backend suite and the web checks (run alone)
- [ ] T015 Manual check per `quickstart.md` on an isolated stack
- [ ] T016 Review of the diff; fix findings
