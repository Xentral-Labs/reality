---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: Long by This Company's Own Standard

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

One is particular to this feature. Both classes rest on a learned norm, so the norm helper is
proven on its own before either class is written — a class built on an untested statistic
would pass its story test for the wrong reason.

## Phase 1: Specification and Design Gates

- [x] T001 Confirm the five accepted scope decisions are recorded in `specs/080-learned-lag/spec.md`
- [x] T002 Confirm every Constitution Check row is PASS and Complexity Tracking is empty in `specs/080-learned-lag/plan.md`
- [x] T003 Complete the reviewer-owned domain review in `specs/080-learned-lag/checklists/domain.md`
- [x] T004 Run `$speckit-analyze` and resolve every CRITICAL consistency or coverage finding

## Phase 2: The Norm, Proven First

- [x] T005 [P] [FR-001] Add failing `test_derivation.py::test_the_fulfilment_norm_describes_this_tenant` asserting the threshold follows the median of completed promises
- [x] T006 [P] [FR-002] Add failing `test_derivation.py::test_the_billing_norm_describes_this_tenant` asserting the threshold follows the median of billed receipts
- [x] T007 [P] [FR-003] Add failing `test_derivation.py::test_one_slow_case_does_not_move_the_norm`, with the positive control that shifting the whole history does move it
- [x] T008 [P] [FR-004] Add failing `test_derivation.py::test_a_young_tenant_is_never_judged`, with the positive control that the case above the minimum reports at once
- [x] T009 [P] [FR-016] Add failing `test_derivation.py::test_a_backdated_shipment_cannot_drag_the_norm` proving a negative lag counts as zero
- [x] T010 [P] [DR-005] Add failing `test_derivation.py::test_norms_are_learned_per_tenant` proving one tenant's speed never judges another

## Phase 3: Failing Proof for the Two Classes

- [x] T011 [P] [US1] [FR-005] Add failing `test_derivation.py::test_order_stalled` covering a stalled undated promise, its clearing on shipment, and a promise inside the norm
- [x] T012 [P] [US1] [FR-006] Add failing `test_derivation.py::test_a_dated_promise_is_left_to_the_overdue_class`, with the positive control that the same promise without a date is reported
- [x] T012a [P] [FR-005a] Add failing `test_derivation.py::test_a_cancelled_promise_is_neither_reported_nor_learned_from`, with the positive control that the same promise uncancelled is reported
- [x] T012b [P] [FR-007a] Add failing `test_derivation.py::test_lag_classes_ignore_mismatched_units`, with the positive control that the same figures in the order line's unit report
- [x] T013 [P] [US2] [FR-007] Add failing `test_derivation.py::test_receipt_unbilled` covering an old unbilled receipt, its clearing when billed, and a recent one
- [x] T014 [P] [FR-008] Add failing `test_derivation.py::test_a_fast_tenant_is_not_reported_at_once`, with the positive control that the floor once passed does report
- [x] T015 [P] [FR-009] [FR-010] [DR-004] Add failing `test_derivation.py::test_lag_classes_expose_full_entry_shape` asserting identity, severity, title, impact, record type/id, the age, the norm, the threshold, and opaque traces
- [x] T016 [P] [FR-011] [DR-002] Add failing `test_derivation.py::test_lag_classes_clear_through_reality` proving shipping and billing each clear their entry with nothing persisted
- [x] T017 [P] [FR-015] Add failing `test_derivation.py::test_lag_classes_order_longest_first` proving deterministic order across repeated reads
- [x] T018 [P] [DR-003] Add failing `test_derivation.py::test_lag_classes_use_the_shared_movement_quantity` asserting quantities come from the correction-aware helper
- [x] T019 [P] [FR-012] Add failing `test_explanation.py::test_lag_classes_explanation_and_not_found_parity` covering both identities, a cleared one, a malformed one and a foreign tenant
- [x] T020 [P] [FR-014] Extend `test_explanation.py::test_shared_consumer_parity_includes_new_classes` so the shared row contract must carry both
- [x] T021 [FR-013] Update the closed registry expectation in `test_coverage.py` and the class list in `tests/test_application_catalog.py`

## Phase 4: The Rule and the Two Classes

- [x] T022 [FR-001] [FR-002] [FR-003] [FR-004] [FR-008] [FR-016] [DR-007] Add the learned-threshold helper to `packages/reality-core/src/reality/services/exceptions.py`, returning nothing below the minimum history rather than a lenient number, and record the eight constants with their reasoning beside Spec 072's four
- [x] T023 [US1] [FR-005] [FR-005a] [FR-006] Add `_order_stalled_exceptions` over open undated customer-delivery promises with quantity outstanding, excluding cancelled ones from both the reporting and the norm
- [x] T024 [US2] [FR-007] [FR-007a] [DR-003] Add `_receipt_unbilled_exceptions` over purchase order lines with an unbilled remainder, reading quantities through the shared correction-aware helper and skipping a pair recorded in different units
- [x] T025 [FR-010] [FR-013] **Atomic activation** — register both derivators, place them in both order constants beside the classes they neighbour, and declare each in `packages/reality-core/config/operational_exception_catalog.yaml` with severity, record type, `080/FR-005` and `080/FR-007` authorities, evidence, description, owner and clearing path
- [x] T026 [FR-014] Prove rather than assert that no adapter change is required
- [x] T027 Create `specs/080-learned-lag/quickstart.md` and record the result of the two independent acceptance stories

## Phase 5: Cross-References and Documentation

- [x] T028 Write both descriptions so `order_stalled` and `overdue_outgoing_customer_commitment` name each other as the dated and undated ways a delivery goes wrong, and `receipt_unbilled` names `billed_not_received` as the opposite direction
- [x] T029 Say plainly in `order_stalled`'s guidance that the norm moves with the business, so an entry can clear because the company got slower rather than because anything shipped
- [x] T030 Re-run the cross-reference review over all nineteen classes and confirm every confusable pair is mutual
- [x] T031 [FR-013] Add the two taxonomy rows to `docs/features/operational_exceptions.md`, and record that the learned-norm rule now has three users rather than one
- [x] T032 [P] Regenerate the catalog reference and run `npm run format` in `apps/docs`
- [x] T033 [P] Add the specification row to `docs/SPEC_COVERAGE_MATRIX.md`

## Final Phase: Cross-Cutting Review

- [x] T900 Run `make spec-check`
- [x] T901 Run `make lint` and the complete backend PostgreSQL suite
- [x] T902 Run the `apps/docs` tests and format check
- [x] T903 [DR-001] Confirm no migration was added and no stored value changed
- [x] T904 Review the final diff against the Constitution and the review risks in `plan.md`
- [x] T904a Measure the demo month: the queue is unchanged and both norms come back as None, because the month has fewer than five finished promises and fewer than five invoiced receipts. Neither class can fire there in either direction, so the pinned demo queue needed no change — recorded in quickstart.md as the weak test of the classes that it is
- [x] T905 Re-derive the feature number immediately before opening the pull request

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001 | T005 | T022 | Done |
| FR-002 | T006 | T022 | Done |
| FR-003 | T007 | T022 | Done |
| FR-004 | T008 | T022 | Done |
| FR-005 | T011 | T023, T025 | Done |
| FR-005a | T012a | T023 | Done |
| FR-006 | T012 | T023 | Done |
| FR-007 | T013 | T024, T025 | Done |
| FR-007a | T012b | T024 | Done |
| FR-008 | T014 | T022 | Done |
| FR-009 | T015 | T023, T024 | Done |
| FR-010 | T015 | T025 | Done |
| FR-011 | T016 | T023, T024 | Done |
| FR-012 | T019 | T025 | Done |
| FR-013 | T021 | T025, T031 | Done |
| FR-014 | T020 | T026 | Done |
| FR-015 | T017 | T023, T024 | Done |
| FR-016 | T009 | T022 | Done |
| DR-001 | T903 | — | Done |
| DR-002 | T016 | T023, T024 | Done |
| DR-003 | T018 | T024 | Done |
| DR-004 | T015 | T023, T024 | Done |
| DR-005 | T010 | T022 | Done |
| DR-006 | T021 | T025 | Done |
| DR-007 | T904 | T022 | Done |
