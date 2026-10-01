# Tasks: Orders Served From Several Warehouses

**Input**: Design documents from `/specs/303-multi-warehouse-orders/`

**Tests**: Tests precede each phase. Every "not reported" assertion has a positive control, and every refusal asserts its code. `core/` means `packages/reality-core/`.

## Phase 1: Specification and Design Gates

- [x] T001 Record the owner's four decisions in `specs/303-multi-warehouse-orders/spec.md`
- [x] T002 Record today's behaviour and the design in `research.md`, `data-model.md` and `contracts/several-warehouses.md`
- [x] T003 Complete the Constitution Check and design in `plan.md`

## Phase 2: Reservation at a named location (FR-001)

- [x] T004 Failing tests in `core/tests/test_multi_warehouse_reservations.py`:
  - reserving without a location is unchanged (control);
  - reserving the rest at a named second location records it there, judged by that location's availability;
  - an inactive location, one without stock, and a location of another company are refused;
  - nothing available there reserves nothing;
  - lots and serials at the named location;
  - a release frees it.
- [x] T005 `location_id` through `_preview_reservation`, `reserve`, and the delivery review of `reserve`, with refusal codes and translations.

## Phase 3: Readiness and shipping per location (FR-002, D02)

- [x] T006 Failing tests:
  - 6 reserved at home and 4 in Munich make 10 ready;
  - 4 in Munich with Munich's stock moved away counts only what is there;
  - the queue agrees with the readiness read;
  - shipping 6 from home and 4 from Munich in two packaged dispatches consumes each warehouse's reservations and fulfils the promise;
  - shipping from a warehouse where nothing is reserved for the promise is refused;
  - every existing readiness, queue and shipment test stays green.
- [x] T007 The shared per-location readiness rule in `fulfillment_readiness`, the queue and blockers projection, the packaged dispatch gate and the shipment preview.
  - `stock_cover` is the one rule. A plain movement shipment, which never checked reservations, is unchanged; that is recorded as a limitation.

## Phase 4: Stock in another warehouse (FR-003)

- [x] T008 Failing tests in `core/tests/test_stock_in_another_location.py`:
  - reported when the own location cannot cover the rest and others can, with locations most-available first;
  - not reported when home covers it, when nothing elsewhere is available, when fully reserved, or when held, cancelled or shipped (each with a positive control);
  - inactive and non-stock locations are ignored;
  - a reviewed reservation there clears it;
  - a reviewed transfer clears it;
  - the statement count does not grow with promises;
  - ids are unique, and tenants are isolated.
- [x] T009 The class with all its registrations, catalog entry, labels and translations.

## Phase 5: Adapters and Web (FR-004)

- [ ] T010 Failing adapter tests in `core/tests/test_multi_warehouse_adapters.py`:
  - the MCP `reservation_propose` carries `location_id` and stays strict;
  - propose then confirm a reservation elsewhere;
  - a transfer proposed from the finding's trace;
  - Web pass-through, with a foreign tenant refused;
  - CLI.
- [ ] T011 MCP, Web and CLI wiring and catalogs.
- [ ] T012 Web:
  - the location choice in the reserve form;
  - "Reserve there" and "Prepare transfer" on the finding;
  - reservations by location in the delivery case;
  - translations, `test:i18n`, the audit, prettier, the build, and the browser-suite fixtures that read the changed pages.

## Phase 6: Stories and Guide (FR-005)

- [ ] T013 Business stories D02, B06 and A02 in `core/tests/scenarios/test_catalog_orders_and_shipments.py`.
- [ ] T014 Promote D02, B06 and A02 with story-first evidence and English and German keywords, and check that neighbouring questions keep their journeys. Update coverage, the roadmap and the coverage matrix, then run `make docs-generate`.

## Phase 7: Verification

- [ ] T015 Full backend suite and the web checks (run alone)
- [ ] T016 Manual check per `quickstart.md` on an isolated stack
- [ ] T017 Review of the diff; fix findings
