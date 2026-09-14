---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: A Return May Say What It Reverses

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

One is particular to this feature. The write path has to accept a return against a commitment
before any story about returned quantities can be written at all, so Phase 3 comes before the
derivations and before the correction to `shipped_not_billed`.

## Phase 1: Specification and Design Gates

- [x] T001 Confirm the five accepted scope decisions are recorded in `specs/079-returns-connect/spec.md`
- [x] T002 Confirm every Constitution Check row is PASS and Complexity Tracking is empty in `specs/079-returns-connect/plan.md`
- [x] T003 Complete the reviewer-owned domain review in `specs/079-returns-connect/checklists/domain.md`
- [x] T004 Run `$speckit-analyze` and resolve every CRITICAL consistency or coverage finding

## Phase 2: Failing Proof

- [x] T005 [P] [US1] [FR-001] [FR-002] Add failing `tests/test_movements.py::test_a_return_may_name_the_delivery_it_reverses` covering acceptance against a customer delivery and refusal against a supplier delivery
- [x] T006 [P] [US1] [FR-003] Add failing `tests/test_movements.py::test_a_return_may_not_exceed_what_went_out`, with the positive control that a return up to the shipped quantity is accepted
- [x] T007 [P] [US1] [FR-004] [DR-004] Add failing `tests/test_movements.py::test_a_return_leaves_the_promise_kept` asserting fulfilled and open quantity are unchanged and no delivery class appears
- [x] T008 [P] [DR-008] Add failing `tests/test_movements.py::test_a_returned_movement_is_still_correctable` proving the existing correction path handles a commitment-carrying return
- [x] T009 [P] [FR-005] Add failing `tests/test_documents.py::test_a_credit_note_line_credits_an_order_line` covering acceptance on the sales side and refusal against a purchase order line
- [x] T010 [P] [US2] [FR-006] Add failing `test_derivation.py::test_returned_goods_are_not_reported_as_unbilled` covering a full return, a partial return, and billing what the customer kept
- [x] T011 [P] [US3] [FR-007] Add failing `test_derivation.py::test_returned_not_credited` covering nothing credited, partly credited, and nothing returned
- [x] T012 [P] [US4] [FR-008] Add failing `test_derivation.py::test_credited_not_returned` covering crediting beyond the return, and crediting with nothing returned at all
- [x] T012a [P] [FR-007a] Add failing `test_derivation.py::test_goods_that_were_never_billed_need_no_credit`, with the positive control that billing the line first reports the return at once
- [x] T012b [P] [FR-008a] Add failing `test_derivation.py::test_one_line_produces_at_most_one_return_entry` across a credited-short and a credited-long line
- [x] T012c [P] [FR-011a] Add failing `test_derivation.py::test_a_voided_movement_stops_counting`, covering a voided shipment reported as unbilled today and a voided return
- [x] T013 [P] [US3] [FR-009] Add failing `test_derivation.py::test_crediting_sums_across_credit_notes` proving two credit note lines both count towards one order line
- [x] T014 [P] [FR-010] Add failing `test_derivation.py::test_return_classes_ignore_mismatched_units`, with the positive control that the same figures in the order line's unit report
- [x] T015 [P] [FR-011] [DR-003] Add failing `test_derivation.py::test_one_returned_quantity_path` asserting the returned quantity is read through one shared helper
- [x] T016 [P] [FR-012] [FR-013] [DR-005] Add failing `test_derivation.py::test_return_classes_expose_full_entry_shape` asserting identity, severity, title, impact, record type/id, causal values and opaque traces for both
- [x] T017 [P] [FR-014] [DR-002] Add failing `test_derivation.py::test_return_classes_clear_through_reality` proving crediting and receiving each clear their entry with nothing persisted
- [x] T018 [P] [FR-018] Add failing `test_derivation.py::test_return_classes_order_longest_first` proving deterministic order across repeated reads
- [x] T019 [P] [DR-006] Add failing `test_derivation.py::test_return_classes_are_tenant_scoped` proving neither leaks across tenants
- [x] T020 [P] [FR-015] Add failing `test_explanation.py::test_return_classes_explanation_and_not_found_parity` covering both identities, a cleared one, a malformed one and a foreign tenant
- [x] T021 [P] [FR-017] Extend `test_explanation.py::test_shared_consumer_parity_includes_new_classes` so the shared row contract must carry both
- [x] T022 [FR-016] Update the closed registry expectation in `test_coverage.py` and the class list in `tests/test_application_catalog.py`

## Phase 3: The Write Path

- [x] T023 [US1] [FR-001] [FR-002] [FR-003] In `packages/reality-core/src/reality/services/core.py`, let `record_movement` accept a `return` against a customer-delivery Commitment, refuse one against a supplier-delivery Commitment, exempt returns from the open-quantity check, and refuse a return larger than what was shipped against that Commitment
- [x] T024 [FR-004] [DR-004] Leave `fulfilled_quantity` counting shipments alone, and say next to it why returns are deliberately not subtracted there, so the next reader does not read a kept promise as a bug
- [x] T025 [US3] [FR-005] Teach `_pricing_direction` that `credit_note` is a sales-side document, so the existing billed-line validation accepts a credit note line against a sales order line and refuses one against a purchase order line

## Phase 4: The Correction and the Two Classes

- [x] T026 [US2] [FR-006] [FR-011] [FR-011a] [DR-003] Move both the exception queue and the service layer onto one correction-aware movement quantity in `packages/reality-core/src/reality/services/core.py`, parameterised by movement type, so the queue stops counting voided movements and `shipped_not_billed` subtracts what came back
- [x] T027 [US3] [FR-007] [FR-007a] [FR-008a] [FR-009] [FR-010] [FR-012] Add `_returned_not_credited_exceptions` over customer-delivery promises, reporting only the billed part of a return less what has been credited
- [x] T028 [US4] [FR-008] [FR-012] Add `_credited_not_returned_exceptions`, reporting only where some quantity has come back
- [x] T029 [FR-013] [FR-016] **Atomic activation** — register both derivators, place them in both order constants beside the invoicing classes, and declare each in `packages/reality-core/config/operational_exception_catalog.yaml` with severity, record type, `079/FR-007` and `079/FR-008` authorities, evidence, description, owner and clearing path
- [x] T030 [FR-017] Prove rather than assert that no adapter change is required
- [x] T031 Create `specs/079-returns-connect/quickstart.md` and record the result of the four independent acceptance stories

## Phase 5: Cross-References and Documentation

- [x] T032 Write both descriptions so `returned_not_credited` and `shipped_not_billed` name each other as the two sides of one line's life, and `credited_not_returned` names `billed_not_received` as its mirror across goods and money
- [x] T033 Re-run the cross-reference review over all seventeen classes and confirm every confusable pair is mutual
- [x] T034 [FR-016] Add the two taxonomy rows to `docs/features/operational_exceptions.md`, including that a return may now name the delivery it reverses
- [x] T035 Record in `docs/features/movements.md` that a `return` may carry the customer-delivery Commitment it reverses, that it never changes fulfilment, and that it may not exceed what went out
- [x] T036 [P] Regenerate the catalog reference and run `npm run format` in `apps/docs`
- [x] T037 [P] Add the specification row to `docs/SPEC_COVERAGE_MATRIX.md`

## Final Phase: Cross-Cutting Review

- [x] T900 Run `make spec-check`
- [x] T901 Run `make lint` and the complete backend PostgreSQL suite
- [x] T902 Run the `apps/docs` tests and format check
- [x] T903 [DR-001] Confirm no migration was added and no stored value changed
- [x] T904 Review the final diff against the Constitution and the review risks in `plan.md`
- [x] T904a Decide what happens to the demo month's return: left as it is. Before this feature its orphaned return demonstrated a gap in the model; after it, the same record demonstrates somebody recording goods back without saying what they came back from, which Reality is right to report. `test_the_month_ends_with_exactly_these_exceptions` is unchanged, and the reason is recorded in quickstart.md and the pull request
- [x] T905 Re-derive the feature number immediately before opening the pull request

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001 | T005 | T023 | Done |
| FR-002 | T005 | T023 | Done |
| FR-003 | T006 | T023 | Done |
| FR-004 | T007 | T024 | Done |
| FR-005 | T009 | T025 | Done |
| FR-006 | T010 | T026 | Done |
| FR-007 | T011 | T027, T029 | Done |
| FR-007a | T012a | T027 | Done |
| FR-008 | T012 | T028, T029 | Done |
| FR-008a | T012b | T027, T028 | Done |
| FR-009 | T013 | T027 | Done |
| FR-010 | T014 | T027, T028 | Done |
| FR-011 | T015 | T026 | Done |
| FR-011a | T012c | T026 | Done |
| FR-012 | T016 | T027, T028 | Done |
| FR-013 | T016 | T029 | Done |
| FR-014 | T017 | T027, T028 | Done |
| FR-015 | T020 | T029 | Done |
| FR-016 | T022 | T029, T034 | Done |
| FR-017 | T021 | T030 | Done |
| FR-018 | T018 | T027, T028 | Done |
| DR-001 | T903 | — | Done |
| DR-002 | T017 | T027, T028 | Done |
| DR-003 | T015 | T026 | Done |
| DR-004 | T007 | T024 | Done |
| DR-005 | T016 | T027, T028 | Done |
| DR-006 | T019 | T027, T028 | Done |
| DR-007 | T022 | T029 | Done |
| DR-008 | T008 | T023 | Done |
