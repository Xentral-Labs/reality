---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: Two Answers the Records Already Hold

**Input**: [`spec.md`](./spec.md), [`plan.md`](./plan.md), [`checklists/`](./checklists/)
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and resulting repository artifacts MUST be
written in English.

## Format

`- [x] T001 [P?] [US1] [FR-001] Action with exact file path`

Every functional/domain requirement MUST appear in at least one test task and one
implementation or documentation task. Test tasks precede the code they prove.

## Sequencing Constraints

The established rules apply: evidence exists before a class is declared, activating a class
is atomic, and a class without a description, an owner and a clearing path is refused.

One rule is now explicit. Every negative test carries a positive control in the same test,
because a negative written before its class exists passes for the wrong reason — which has
happened in Specs 069, 072 and 076.

## Phase 1: Specification and Design Gates

- [x] T001 Confirm the five accepted scope decisions are recorded in `specs/078-records-already-answer/spec.md`
- [x] T002 Confirm every Constitution Check row is PASS and Complexity Tracking is empty in `specs/078-records-already-answer/plan.md`
- [x] T003 Complete the reviewer-owned domain review in `specs/078-records-already-answer/checklists/domain.md`
- [x] T004 Run `$speckit-analyze` and resolve every CRITICAL consistency or coverage finding

## Phase 2: Failing Proof

- [x] T005 [P] [US1] [FR-001] [FR-005] Add failing `tests/operational_exceptions/test_derivation.py::test_credit_limit_exceeded` covering an excess, an amount exactly at the limit, and the excess reported with limit, outstanding and difference
- [x] T006 [P] [US1] [FR-002] Add failing `test_derivation.py::test_a_party_without_a_limit_is_never_reported`, with the positive control that recording a limit reports the same party at once
- [x] T007 [P] [FR-003] [DR-002] Add failing `test_derivation.py::test_credit_exposure_uses_the_shared_open_items` asserting the outstanding figure is read through the shared open-item derivation and equals what the aging register reports
- [x] T008 [P] [US1] [FR-004] Add failing `test_derivation.py::test_only_the_partys_own_currency_counts`, with the positive control that the same amount in the party's own currency reports
- [x] T009 [P] [US2] [FR-006] Add failing `test_derivation.py::test_duplicate_supplier_invoice` covering two invoices, three invoices, and the same number from two different suppliers
- [x] T010 [P] [US2] [FR-007] Add failing `test_derivation.py::test_numbers_are_matched_without_case_or_padding`, including that an empty number is neither reported nor matched against
- [x] T010a [P] [FR-008a] Add failing `test_derivation.py::test_a_reversed_invoice_is_not_a_duplicate`, with the positive control that the same pair reports while the first invoice stands
- [x] T011 [P] [FR-008] [FR-015] Add failing `test_derivation.py::test_the_original_is_the_same_document_every_read` proving the pair never swaps across repeated reads
- [x] T012 [P] [FR-009] [FR-010] [DR-003] [DR-004] Add failing `test_derivation.py::test_both_classes_expose_full_entry_shape` asserting identity, severity, title, impact, record type/id, causal values and opaque traces for both, including both SourceRecords on the duplicate entry
- [x] T013 [P] [FR-011] [DR-001] Add failing `test_derivation.py::test_both_classes_clear_through_reality` proving settlement clears the credit entry and a reversal clears the duplicate, with nothing persisted
- [x] T014 [P] [DR-005] Add failing `test_derivation.py::test_record_classes_are_tenant_scoped` proving neither leaks across tenants
- [x] T015 [P] [FR-012] Add failing `test_explanation.py::test_record_classes_explanation_and_not_found_parity` covering both identities, a cleared one, a malformed one and a foreign tenant
- [x] T016 [P] [FR-014] Extend `test_explanation.py::test_shared_consumer_parity_includes_new_classes` so the shared row contract must carry both
- [x] T017 [FR-013] Update the closed registry expectation in `test_coverage.py` and the class list in `tests/test_application_catalog.py`

## Phase 3: The Two Derivations

- [x] T018 [US1] [FR-001] [FR-002] [FR-004] [FR-005] [DR-002] Add `_credit_limit_exceeded_exceptions` to `packages/reality-core/src/reality/services/exceptions.py`, reading the outstanding amount through the shared open-item derivation, skipping a limit of zero, counting only the party's own default currency, and treating an amount equal to the limit as allowed
- [x] T019 [US2] [FR-006] [FR-007] [FR-008] [FR-008a] Add `_duplicate_supplier_invoice_exceptions`, grouping Documents by party and normalised number, ordering by `document_date` then `id` so the original never changes, and skipping documents with no number and documents whose posting has been reversed
- [x] T020 [FR-010] [FR-013] **Atomic activation** — register both derivators, place them in both order constants beside the receivable and the payable, and declare each in `packages/reality-core/config/operational_exception_catalog.yaml` with severity, record type, `078/FR-001` and `078/FR-006` authorities, evidence, description, owner and clearing path
- [x] T021 [FR-012] [DR-003] Verify the explanation path handles record type `party` and leaves the `import_job` `raw_source` branch unchanged
- [x] T022 [FR-014] Prove rather than assert that no adapter change is required, by explaining a `party`-carried entry through the untouched Inspector contract in `tests/test_master_data_api.py`
- [x] T023 Create `specs/078-records-already-answer/quickstart.md` and record the result of the two independent acceptance stories

## Phase 4: Cross-References and Documentation

- [x] T024 Write both descriptions so `credit_limit_exceeded` and `overdue_receivable` name each other as the total agreed versus one invoice being late, and `duplicate_supplier_invoice` names `overdue_payable` and `billed_not_received` as the other two things that can be wrong about a supplier invoice
- [x] T025 Say plainly in the credit class's guidance that a limit of zero means none is recorded, so a reader is never left guessing why a cash-only customer is silent
- [x] T026 Re-run the cross-reference review over all fifteen classes and confirm every confusable pair is mutual
- [x] T027 [FR-013] Add the two taxonomy rows to `docs/features/operational_exceptions.md`, including that `party` is now a carrier
- [x] T028 [P] Regenerate the catalog reference and run `npm run format` in `apps/docs`
- [x] T029 [P] Add the specification row to `docs/SPEC_COVERAGE_MATRIX.md`

## Final Phase: Cross-Cutting Review

- [x] T900 Run `make spec-check`
- [x] T901 Run `make lint` and the complete backend PostgreSQL suite
- [x] T902 Run the `apps/docs` tests and format check
- [x] T903 [DR-007] Confirm no migration was added and no stored value changed
- [x] T904 Review the final diff against the Constitution and the review risks in `plan.md`
- [x] T904a Measure the demo queue and report the number. Neither new class fires: the demo records no credit limit and no duplicate number. The first attempt measured `ensure_demo` rather than `run_normal_month` and drew a wrong conclusion that also went into Spec 076; both are corrected here, and `test_the_month_ends_with_exactly_these_exceptions` now pins the demo queue so the next class cannot change it unnoticed
- [x] T905 Re-derive the feature number immediately before opening the pull request

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001 | T005 | T018, T020 | Done |
| FR-002 | T006 | T018, T025 | Done |
| FR-003 | T007 | T018 | Done |
| FR-004 | T008 | T018 | Done |
| FR-005 | T005 | T018 | Done |
| FR-006 | T009 | T019, T020 | Done |
| FR-007 | T010 | T019 | Done |
| FR-008 | T011 | T019 | Done |
| FR-008a | T010a | T019 | Done |
| FR-009 | T012 | T018, T019 | Done |
| FR-010 | T012 | T020 | Done |
| FR-011 | T013 | T018, T019 | Done |
| FR-012 | T015 | T021 | Done |
| FR-013 | T017 | T020, T027 | Done |
| FR-014 | T016 | T022 | Done |
| FR-015 | T011 | T019 | Done |
| DR-001 | T013 | T018, T019 | Done |
| DR-002 | T007 | T018 | Done |
| DR-003 | T012 | T021 | Done |
| DR-004 | T012 | T018, T019 | Done |
| DR-005 | T014 | T018, T019 | Done |
| DR-006 | T017 | T020 | Done |
| DR-007 | T903 | — | Done |
