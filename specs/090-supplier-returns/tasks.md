---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: Goods Going Back the Other Way

**Input**: [`spec.md`](./spec.md), [`plan.md`](./plan.md), [`checklists/`](./checklists/)
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and resulting repository artifacts MUST be
written in English.

## Format

`- [x] T001 [P?] [US1] [FR-001] Action with exact file path`

Every functional/domain requirement MUST appear in at least one test task and one
implementation or documentation task. Test tasks precede the code they prove.

## Sequencing Constraints

The established rules apply: evidence exists before a class is declared, activating a class is
atomic, a class without a description, an owner and a clearing path is refused, and every
negative test carries a positive control in the same test.

Two constraints are particular to this feature. The goods move before anything watches them: the
movement kind and its bounds are proven first, and the classes are written only once a supplier
return can actually be recorded. And the one shipped class this corrects is corrected with its
own failing test first, so the change is visible rather than incidental.

## Phase 1: Specification and Design Gates

- [x] T001 Confirm the accepted scope decisions are recorded in `specs/090-supplier-returns/spec.md`
- [x] T002 Confirm every Constitution Check row is PASS and Complexity Tracking is empty in `specs/090-supplier-returns/plan.md`
- [x] T003 Complete the reviewer-owned domain review in `specs/090-supplier-returns/checklists/domain.md`
- [x] T004 Run `$speckit-analyze` and resolve every CRITICAL consistency or coverage finding
- [x] T005 Confirm against the code that a movement type is the only thing missing, rather than assuming it from the spec 089 note

## Phase 2: Failing Proof for the Movement

- [x] T006 [P] [US1] [FR-001] [FR-002] [FR-005] [FR-006] [DR-007] Add failing `test_returns.py::test_goods_go_back_to_the_supplier`, asserting stock falls, fulfilment does not, and every figure is one that was recorded
- [x] T007 [P] [FR-003] Add failing `test_returns.py::test_a_supplier_return_is_refused_without_its_delivery` covering a customer delivery, another item and a missing location, each with a positive control
- [x] T008 [P] [FR-004] Add failing `test_returns.py::test_a_supplier_return_cannot_exceed_what_arrived`, including a fully received promise where the open quantity is zero and a return must still be possible
- [x] T009 [P] [US2] [FR-007] Add failing `test_returns.py::test_a_supplier_return_settles_a_customer_return`, covering the wrong location and a return already settled in full
- [x] T010 [P] [FR-008] Add failing `test_returns.py::test_a_corrected_supplier_return_stops_counting`
- [x] T011 [DR-005] Add failing `test_returns.py::test_supplier_returns_are_tenant_scoped`

## Phase 3: The Movement

- [x] T012 [FR-001] [FR-002] [FR-003] [FR-004] Add `supplier_return` to the movement vocabulary in `packages/reality-core/src/reality/services/core.py`, with its direction and its commitment guards, and say in a comment why the bound is what arrived rather than what is open
- [x] T013 [FR-007] Prove rather than assert that the existing settlement rules govern it unchanged
- [x] T014 [FR-021] Run the complete existing backend suite and record that nothing moved

## Phase 4: Failing Proof for the Classes and the Correction

- [x] T015 [P] [US3] [FR-009] [FR-011] Add failing `test_derivation.py::test_supplier_return_not_credited`, with the positive control that crediting it clears the entry and the silence for goods no invoice billed
- [x] T016 [P] [FR-010] Add failing `test_derivation.py::test_supplier_credit_not_returned`, with the positive control that a rebate with nothing returned is never reported
- [x] T017 [P] [US4] [FR-012] Add failing `test_derivation.py::test_receipt_unbilled_counts_what_is_still_here`, covering a partial and a complete return
- [x] T018 [P] [FR-013] Add failing `test_derivation.py::test_a_return_does_not_unmake_a_receipt`, proving `billed_not_received` is unchanged by a return
- [x] T019 [P] [FR-014] [DR-004] Add failing `test_derivation.py::test_the_supplier_return_entries_expose_full_shape`
- [x] T020 [P] [FR-015] [DR-002] Add failing `test_derivation.py::test_the_supplier_return_entries_clear_through_reality` with nothing persisted
- [x] T021 [P] [FR-019] Add failing `test_derivation.py::test_an_unreconcilable_supplier_credit_is_reported_not_judged`
- [x] T022 [P] [FR-020] Add failing `test_derivation.py::test_the_supplier_return_entries_order_deterministically`
- [x] T023 [P] [DR-003] Add failing `test_derivation.py::test_both_return_directions_share_one_body`
- [x] T024 [P] [DR-005] Add failing `test_derivation.py::test_the_supplier_return_classes_are_tenant_scoped`
- [x] T025 [P] [FR-016] Add failing `test_explanation.py::test_supplier_return_explanation_and_not_found_parity`
- [x] T026 [P] [FR-017] Extend `test_explanation.py::test_shared_consumer_parity_includes_new_classes` so the shared row contract must carry both
- [x] T027 [FR-017] Update the closed registry expectation in `test_coverage.py` and the class list in `tests/test_application_catalog.py`

## Phase 5: The Classes and the Correction

- [x] T028 [US3] [FR-009] [FR-010] [FR-011] [DR-003] Parameterise `_return_exceptions` by commitment type and crediting document type, and produce both pairs from the one body
- [x] T029 [FR-012] Add the buying-side kept quantity and use it in `_receipt_unbilled_exceptions`, saying in a comment that this is the same correction spec 079 made on the selling side
- [x] T030 [FR-013] Leave `_billed_not_received_exceptions` counting the raw receipt, and say in a comment why subtracting there would accuse a supplier of not delivering what it delivered
- [x] T031 [FR-019] Teach `units_not_comparable` that a supplier credit note credits a supplier delivery
- [x] T032 [FR-017] **Atomic activation** — register both derivators, place them in both order constants beside their selling-side mirrors, and declare both in `packages/reality-core/config/operational_exception_catalog.yaml` with severity, record type, the `090/FR-009` and `090/FR-010` authorities, evidence, description, owner and clearing path
- [x] T033 [FR-017] Write the guidance so each new class and its selling-side mirror name each other, and so `receipt_unbilled` says it counts what is still here
- [x] T034 Create `specs/090-supplier-returns/quickstart.md` and record the result of the four independent acceptance stories

## Phase 6: Surfaces and Catalogs

- [x] T035 [FR-018] Carry the movement kind through `packages/reality-core/src/reality/mcp/catalog.py` and any surface that enumerates movement kinds
- [x] T036 [FR-018] Run the drift gates and confirm every catalog agrees

## Phase 7: Cross-References and Documentation

- [x] T037 Re-run the cross-reference review over all twenty-nine classes and confirm every confusable pair is mutual
- [x] T038 [FR-017] Add the taxonomy rows to `docs/features/operational_exceptions.md`, including the corrected and the deliberately uncorrected class
- [x] T039 [P] Record the movement kind in `docs/features/movements.md` and the closed chain in `docs/features/procure_to_pay.md`
- [x] T040 [P] Regenerate the catalog reference and run `npm run format` in `apps/docs`
- [x] T041 [P] Add the specification row to `docs/SPEC_COVERAGE_MATRIX.md`, recording that the survey's last gap is closed

## Final Phase: Cross-Cutting Review

- [x] T900 Run `make spec-check`
- [x] T901 Run `make lint` and the complete backend PostgreSQL suite
- [x] T902 Run the `apps/docs` tests and format check
- [x] T903 [DR-001] Confirm no migration was added
- [x] T904 Review the final diff against the Constitution and the review risks in `plan.md`
- [x] T904a Measure the demo month's queue and confirm it is unchanged, recording that the demo records no supplier return so this proves nothing about volume
- [x] T905 Re-derive the feature number with `scripts/next_feature_number.py` immediately before opening the pull request, and take the number it gives

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001 | T006 | T012 | Done |
| FR-002 | T006 | T012 | Done |
| FR-003 | T007 | T012 | Done |
| FR-004 | T008 | T012 | Done |
| FR-005 | T006 | T012 | Done |
| FR-006 | T006 | T012 | Done |
| FR-007 | T009 | T013 | Done |
| FR-008 | T010 | T012 | Done |
| FR-009 | T015 | T028, T032 | Done |
| FR-010 | T016 | T028 | Done |
| FR-011 | T015 | T028 | Done |
| FR-012 | T017 | T029 | Done |
| FR-013 | T018 | T030 | Done |
| FR-014 | T019 | T028 | Done |
| FR-015 | T020 | T028 | Done |
| FR-016 | T025 | T032 | Done |
| FR-017 | T026, T027 | T032, T033, T038 | Done |
| FR-018 | T036 | T035 | Done |
| FR-019 | T021 | T031 | Done |
| FR-020 | T022 | T028 | Done |
| FR-021 | T014 | — | Done |
| DR-001 | T903 | — | Done |
| DR-002 | T020 | T028 | Done |
| DR-003 | T023 | T028 | Done |
| DR-004 | T019 | T028 | Done |
| DR-005 | T011, T024 | T012, T028 | Done |
| DR-006 | T027 | T032 | Done |
| DR-007 | T006 | T012 | Done |
