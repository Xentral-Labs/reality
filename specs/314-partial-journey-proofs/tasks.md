# Tasks: Journey Proof Stories, Round Three

**Input**: Design documents from `/specs/314-partial-journey-proofs/`

**Tests**: A regression test precedes each fix and fails without it. Stories are the deliverable. Every "no finding" assertion has a positive control; every refusal and failure asserts its code. `core/` means `packages/reality-core/`.

## Phase 1: Specification and Design Gates

- [x] T001 Record the scope and the owner's four decisions in `specs/314-partial-journey-proofs/spec.md`
- [x] T002 Record routes, findings, decisions and the migration order in `specs/314-partial-journey-proofs/research.md`
- [x] T003 Complete the Constitution Check and design in `specs/314-partial-journey-proofs/plan.md` and `data-model.md`

## Phase 2: Defect — a receipt explains itself or is reported (FR-003, FR-004)

- [x] T004 [FR-003] [FR-004] Failing tests in `core/tests/test_movement_reasons.py`:
  - a receipt without a commitment recorded with reason "free sample" through reviewed `movement_create` is explained as `explicit_reason` with that reason and is not reported;
  - the same without a reason is reported (positive control);
  - a blank reason counts as none;
  - a `shipment_receive` receipt without a commitment and without a reason is reported;
  - a correction onto a purchase clears it.
- [x] T005 [FR-003] Keep a non-blank reason on a receipt, shipment or return without a commitment as a `movement_reason_stated` change record in `core/src/reality/services/core.py`; read it in `core/src/reality/services/movement_explanations.py`.
- [x] T006 [FR-004] In `core/src/reality/services/exceptions.py`, exclude movements with a stated reason from `unexplained_movement` and stop a shipment package from explaining a receipt without a commitment. Pass a line's `reason` through `shipment_receive` if the review refuses it. Run the delivery-action, shipment, movement-correction and operational-exception suites, and update tests that pinned the old package rule.

## Phase 3: Defect — a unique stated reference is a candidate (FR-005)

- [x] T007 [FR-005] Failing test in `core/tests/test_payment_candidates_reference.py`:
  - a payment stating shop order 9701 before the order exists is unallocated with its reason;
  - after the order is taken in and invoiced for 100, a payment of 95 has that invoice as a candidate with the reason "stated reference names this invoice";
  - a reference matching two invoices keeps "among others" (control).
- [x] T008 [FR-005] Add the unique-reference reason in `core/src/reality/services/payment_intake.py::payment_candidates`; run the payment-intake and settlement suites.

## Phase 4: Defect — a shop line without price or quantity (FR-006)

- [x] T009 [FR-006] Failing tests in `core/tests/test_shop_line_gaps.py`:
  - an order whose second line has no price, or a null price, is interpreted; that line has `unit_price` null, its payload is kept, and `order_line_price_missing` names it, while a priced line raises nothing (control);
  - an order whose line has no quantity, or a null quantity, fails with `source_line_quantity_missing`, is reported by `source_interpretation_failure`, and a second order in the same batch is interpreted;
  - a later shop version stating the price is held as `price_changed`;
  - billing offers the unpriced position without a price.
- [x] T010 [FR-006] Migration making `document_line.unit_price` nullable, numbered after rebasing onto `main` (research R8), with a downgrade that refuses null prices; update the model in `core/src/reality/db/core.py` and `config/data_model.yaml`.
- [x] T011 [FR-006] Shopify line interpretation in `core/src/reality/services/core.py`: a missing or null price becomes null, and a missing, null or non-positive quantity is a coded failure. Confirm `process_pending_import_jobs` keeps other jobs going.
- [x] T012 [FR-006] New class `order_line_price_missing` with every class gate: CLASS_ORDER, DERIVATION_REGISTRY, catalogs order, `operational_exception_catalog.yaml`, test class lists, reference-integrity count, German label. Add the refusal codes to `service_refusals.json` with de/nl/es translations.
- [x] T013 [FR-006] Audit every `DocumentLine.unit_price` reader for null: exceptions, billing, credit actions, shop order changes, refunds, projections, payment intake, playground, web, demo data. Run the migrations, schema, billing, Shopify and operational-exception suites.

## Phase 5: Stories (FR-001, FR-002)

- [x] T014 [P] [US1] F04 story in `core/tests/scenarios/test_catalog_stock_and_returns.py`:
  - an invoiced delivery of 2, then an unannounced return of 2: stock is back, `unexplained_movement` is reported, and nothing is owed;
  - a reviewed `movement_correct` links it: `returned_not_credited` 2 (positive control), unexplained clears;
  - a credit of 2 settles it and nothing remains.
- [x] T015 [P] [US1] F08 story in `core/tests/scenarios/test_catalog_stock_and_returns.py`:
  - an announced return of 2, due in 5 days; credit note and refund paid before arrival;
  - nothing is reported before the due date, and `announced_return_not_arrived` after it (control);
  - 1 back reports `credited_not_returned` 1, and 2 back fulfils the announcement and clears everything.
- [x] T016 [P] [US2] H09 story in `core/tests/scenarios/test_catalog_purchasing.py`:
  - a sample receipt with a reason is explained and not reported;
  - a misdelivery through `shipment_receive` without a reason is reported;
  - a correction onto a purchase clears it.
- [x] T017 [P] [US3] P02 story in `core/tests/scenarios/test_catalog_sources.py`:
  - a refund before its order fails, then links itself once the order is in and the retry is due;
  - a payment before its order is unallocated; after invoicing, it is a candidate by its reference;
  - a person allocates it, and nothing unallocated remains.
- [x] T018 [P] [US3] P05 story in `core/tests/scenarios/test_catalog_sources.py`:
  - an order with an unpriced line is accepted, and the gap is reported (control: the priced line);
  - an order without a quantity fails with its code, while the next order is interpreted.
- [x] T019 [P] [US4] P08 story in `core/tests/scenarios/test_catalog_sources.py`:
  - a legacy `sales_order` file row of 10 with 4 delivered; a reviewed `commitment_revise` to 6 cites the legacy source;
  - reserve, ship and invoice 6; the open rest is reported as unbilled before the invoice (control);
  - nothing is reported for the 4, and everything traces to the source.
- [x] T020 [P] B09 story pinning today's behaviour in `core/tests/scenarios/test_catalog_purchasing.py`: after a receipt of 4 against assignments of 3 + 3 + 3, `protecting_supply` stays 3 each, and uncovered promises are only those a person has not reserved.

## Phase 6: Guide and Records (FR-007–FR-009)

- [x] T021 [FR-007] Promote F04, F08, H09, P02, P05 and P08 in `core/config/business_journey_catalog.yaml` with story-first evidence and English and German keywords and question examples. Add them to `PROVEN_BY_STORY` and `FINDABLE_BY_KEYWORD`. Check neighbouring questions with `search_journeys`.
- [x] T022 [FR-008] Update B09's limitation, and list B09 with its finding in `specs/305-backorder-allocation/spec.md`.
- [x] T023 [FR-009] Update the counts and rows in `docs/scenarios/coverage.md`, the note in `docs/scenarios/roadmap.md`, and the new test files in `docs/SPEC_COVERAGE_MATRIX.md`. Run `make docs-generate`, `make docs-catalog-check`, `make spec-check` and lint.

## Phase 7: Verification

- [ ] T024 Full backend suite from a clean worktree and the web checks
- [ ] T025 Review of the diff; fix findings
