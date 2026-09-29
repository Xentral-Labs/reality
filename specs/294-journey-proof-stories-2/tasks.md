# Tasks: Journey Proof Stories, Round Two

**Input**: Design documents from `/specs/294-journey-proof-stories-2/`

**Tests**: The stories are the deliverable. Every "no finding" assertion has a positive control; every refusal asserts its code. `core/` means `packages/reality-core/`.

## Phase 1: Specification and Design Gates

- [x] T001 Record the approved eleven-journey scope in `specs/294-journey-proof-stories-2/spec.md`
- [x] T002 Record routes, expected outcomes, the readiness defect and decisions in `specs/294-journey-proof-stories-2/research.md`
- [x] T003 Complete the Constitution Check and outcome rule in `specs/294-journey-proof-stories-2/plan.md`

## Phase 2: Defect — a reviewed shipment movement honours readiness (FR-006)

- [ ] T004 [FR-006] Failing regression test: a reviewed `movement_create` shipment of an unpaid prepayment order is refused with `shipment_blocked_readiness` at preparation and execution and creates no movement; a paid one ships (positive control), in `core/tests/test_movement_create_readiness.py`
- [ ] T005 [FR-006] Consult `fulfillment_readiness` for `movement_create` shipments against customer deliveries in `core/src/reality/services/delivery_actions.py`, reusing the dispatch refusal values; run the delivery-action, shipment and fulfillment-safety suites

## Phase 3: User Story 1 — Purchasing and receipt (P1)

- [ ] T006 [P] [US1] [FR-001] [DR-002] G07 story: purchase tier price list, order line at the tier price, guided supplier invoice kept as stated with no finding, differing invoice through `document_create` reported as `invoice_price_differs`, in `core/tests/scenarios/test_catalog_purchasing.py`
- [ ] T007 [P] [US1] [FR-001] H03 story: receive 7 of 10, reviewed revision to 7 with a note; nothing open, not overdue (positive control), note and decision read back, in `core/tests/scenarios/test_catalog_purchasing.py`
- [ ] T008 [P] [US1] [FR-001] [DR-002] I06 story: receive 8, guided invoices of 6 and 4, `billed_not_received` for 2, third invoice refused with `invoice_quantity_exceeds_billable`, in `core/tests/scenarios/test_catalog_purchasing.py`
- [ ] T009 [P] [US1] [FR-001] I07 story: carrier party, free supplier invoice with stated net, owner assigns `inbound_freight` to the receipt; receipt cost includes it and names the carrier invoice, in `core/tests/scenarios/test_catalog_purchasing.py`
- [ ] T010 [P] [US1] [FR-001] K05 story: three variants on one purchase, one receipt, stock and reservation per variant, shortage only on the over-reserved variant, in `core/tests/scenarios/test_catalog_purchasing.py`

## Phase 4: User Story 2 — Sales and master data (P1)

- [ ] T011 [P] [US2] [FR-001] D16 story: free replacement through an advance exchange, reserved and shipped; movement explains the promise; no invoice, no unbilled finding (positive control: an ordinary unbilled shipment), in `core/tests/scenarios/test_catalog_orders_and_shipments.py`
- [ ] T012 [P] [US2] [FR-001] L06 story: dated order without stock, supplier order assigned; shortage blockers plus `protecting_supply` (zero before, as control), in `core/tests/scenarios/test_catalog_orders_and_shipments.py`
- [ ] T013 [P] [US2] [FR-001] O01 story: reserve, ship and invoice, then reviewed SKU change; same item on every record, stock unchanged, document line keeps its SKU, in `core/tests/scenarios/test_catalog_orders_and_shipments.py`

## Phase 5: User Story 3 — Source integration (P2)

- [ ] T014 [P] [US3] [FR-001] P04 story: Shopify order, cancelled version held for review, reviewed `commitment_cancel` with the cancellation's source record; line cancelled, reservation released, event carries source and reason, in `core/tests/scenarios/test_catalog_sources.py`
- [ ] T015 [P] [US3] [FR-001] P07 story: declared capability, daily arrivals, silence reported (control), backlog with exact repeats; counts equal distinct orders, silence clears, in `core/tests/scenarios/test_catalog_sources.py`

## Phase 6: User Story 4 — Combined story (P2)

- [ ] T016 [US4] [FR-001] [FR-006] R01 story written to the catalog sequence; expected to stop at "released anyway" and be pinned as a limitation, in `core/tests/scenarios/test_catalog_finance.py`

## Phase 7: User Story 5 — The Guide follows the evidence (P1)

- [ ] T017 [US5] [FR-006] Record each failed story's decision (defect or missing capability) in `specs/294-journey-proof-stories-2/research.md`
- [ ] T018 [US5] [FR-003] [FR-004] [FR-005] Promote passing journeys with evidence, limitations and English/German keywords in `core/config/business_journey_catalog.yaml`; correct R01's limitation
- [ ] T019 [US5] [FR-003] [FR-005] Extend `PROVEN_BY_STORY` and add the keyword check in `core/tests/test_business_journey_catalog.py`
- [ ] T020 [US5] [FR-006] Update rows, counts and findings in `docs/scenarios/coverage.md`
- [ ] T021 [US5] [FR-007] Run `make docs-generate` and commit the regenerated Guide and advisor knowledge
- [ ] T022 [US5] [SC-004] Ask the Guide an English and a German question per promoted journey, per `specs/294-journey-proof-stories-2/quickstart.md`

## Final Phase: Verification and Review

- [ ] T023 Add `test_catalog_sources.py` and `test_movement_create_readiness.py` to `docs/SPEC_COVERAGE_MATRIX.md` and update the three catalog module rows
- [ ] T024 Run Ruff (`--no-cache`), `make spec-check`, `make docs-catalog-check`, and grep tests and web scripts for pinned counts the change moves
- [ ] T025 Open the PR; the CI shards are the full-suite evidence
- [ ] T026 Review the diff against FR-001–FR-008, DR-001–DR-003 and the Constitution

## Dependencies

- T004–T005 come first, because R01 and any shipment story must not pass through the bypass.
- T006–T016 are independent of each other; write them sequentially within a module.
- T017–T022 follow the stories; T023–T026 close.

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001, FR-002 | T006–T016 | — | Pending |
| FR-003, FR-004 | T019 | T018 | Pending |
| FR-005 | T019, T022 | T018 | Pending |
| FR-006 | T004, T016, T017 | T005, T020 | Pending |
| FR-007 | T022 | T021 | Pending |
| FR-008 | T026 | — | Pending |
| DR-001–DR-003 | T006–T016 | — | Pending |
