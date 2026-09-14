---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: The Invoice Nobody Booked

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

Two are particular to this feature. **The rename lands first, alone**, so the existing suites
prove that four shipped classes did not move before anything new reads the renamed helpers. And
the separate-rhythm test is written before either class, because sharing a history is the
mistake this line of work has already made once.

## Phase 1: Specification and Design Gates

- [x] T001 Confirm the accepted scope decisions are recorded in `specs/092-invoice-unposted/spec.md`
- [x] T002 Confirm every Constitution Check row is PASS and Complexity Tracking is empty in `specs/092-invoice-unposted/plan.md`
- [x] T003 Complete the reviewer-owned domain review in `specs/092-invoice-unposted/checklists/domain.md`
- [x] T004 Run `$speckit-analyze` and resolve every CRITICAL consistency or coverage finding
- [x] T005 Confirm against the code that the accounts meaning "booked" are the ones the posting operations use to refuse a second posting

## Phase 2: The Rename, Alone

- [x] T006 [DR-003] [FR-015] Rename `_credit_notes`, `_credit_is_posted`, `_credit_posting_threshold` and `_unposted_credit_exceptions` in `packages/reality-core/src/reality/services/exceptions.py` to names that do not claim to be about credits, and say in a comment why
- [x] T006a [FR-015] Align `supplier_credit_unposted` with its own operation by asking `accounts_payable` rather than `inventory`, and add `test_derivation.py::test_a_class_and_its_operation_agree_on_booked`
- [x] T007 [FR-014] Run the complete existing backend suite and record that four shipped classes did not move

## Phase 3: Failing Proof

- [x] T008 [P] [US1] [FR-001] [FR-004] [FR-009] [DR-002] Add failing `test_derivation.py::test_sales_invoice_unposted`, covering a tenant below the minimum history, one past its norm, one inside it, and booking clearing the entry
- [x] T009 [P] [US2] [FR-002] Add failing `test_derivation.py::test_supplier_invoice_unposted` on the same terms
- [x] T010 [P] [FR-003] Add failing `test_derivation.py::test_each_document_type_learns_its_own_rhythm`, proving a sales-invoice rhythm does not judge supplier invoices, with the positive control that its own rhythm does
- [x] T011 [P] [FR-005] Add failing `test_derivation.py::test_a_reversed_posting_is_not_an_unbooked_one`, with the positive control that a genuinely unbooked invoice on the same tenant reports
- [x] T012 [P] [FR-006] Add failing `test_derivation.py::test_a_document_with_no_date_says_nothing`, with a positive control
- [x] T013 [P] [FR-007] Add failing `test_derivation.py::test_the_four_unposted_sides_stay_apart`
- [x] T014 [P] [FR-008] [DR-004] Add failing `test_derivation.py::test_the_unposted_invoice_entries_expose_full_shape`
- [x] T015 [P] [FR-013] Add failing `test_derivation.py::test_the_unposted_invoice_entries_order_deterministically`
- [x] T016 [P] [DR-005] Add failing `test_derivation.py::test_the_unposted_invoice_classes_are_tenant_scoped`
- [x] T017 [P] [DR-003] Add failing `test_derivation.py::test_all_four_unposted_classes_share_one_body`
- [x] T018 [P] [FR-010] Add failing `test_explanation.py::test_unposted_invoice_explanation_and_not_found_parity`
- [x] T019 [P] [FR-012] Extend `test_explanation.py::test_shared_consumer_parity_includes_new_classes` so the shared row contract must carry both
- [x] T020 [FR-011] Update the closed registry expectation in `test_coverage.py` and the class list in `tests/test_application_catalog.py`

## Phase 4: The Classes

- [x] T021 [US1] [US2] [FR-001] [FR-002] [FR-003] Add the two document-type constants and the two derivators to `packages/reality-core/src/reality/services/exceptions.py`
- [x] T022 [FR-011] **Atomic activation** — register both derivators, place them in both order constants ahead of the credit-note pair, and declare both in `packages/reality-core/config/operational_exception_catalog.yaml` with severity, record type, the `092/FR-001` and `092/FR-002` authorities, evidence, description, owner and clearing path
- [x] T023 [FR-011] Write the guidance so each class says what it hides while it stands — no aging, no reminder, no payment run, no discount — and names its credit-note counterpart
- [x] T024 [FR-012] Prove rather than assert that no adapter change is required
- [x] T025 Create `specs/092-invoice-unposted/quickstart.md` and record the result of the three independent acceptance stories

## Phase 5: Cross-References and Documentation

- [x] T026 Re-run the cross-reference review over all thirty-one classes and confirm every confusable pair is mutual
- [x] T027 [FR-011] Add the taxonomy rows to `docs/features/operational_exceptions.md`, including why four unposted classes exist and what each hides
- [x] T028 [P] Record in `docs/features/ledger.md` that the distance between recording and booking is now reported for all four document types
- [x] T029 [P] Regenerate the catalog reference and run `npm run format` in `apps/docs`
- [x] T030 [P] Add the specification row to `docs/SPEC_COVERAGE_MATRIX.md`

## Final Phase: Cross-Cutting Review

- [x] T900 Run `make spec-check`
- [x] T901 Run `make lint` and the complete backend PostgreSQL suite in CI's invocation and ordering
- [x] T902 Run the `apps/docs` tests and format check
- [x] T903 [DR-001] Confirm no migration was added and no diff under `services/core.py`
- [x] T904 Review the final diff against the Constitution and the review risks in `plan.md`
- [x] T904a Confirm the demo month's pinned queue is unchanged, and record that the demo books everything it records so this proves nothing about volume
- [x] T905 Re-derive the feature number with `scripts/next_feature_number.py` immediately before opening the pull request, and take the number it gives

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001 | T008 | T021, T022 | Done |
| FR-002 | T009 | T021, T022 | Done |
| FR-003 | T010 | T021 | Done |
| FR-004 | T008 | T021 | Done |
| FR-005 | T011 | T021 | Done |
| FR-006 | T012 | T021 | Done |
| FR-007 | T013 | T021 | Done |
| FR-008 | T014 | T021 | Done |
| FR-009 | T008 | T021 | Done |
| FR-010 | T018 | T022 | Done |
| FR-011 | T020 | T022, T023, T027 | Done |
| FR-012 | T019 | T024 | Done |
| FR-013 | T015 | T021 | Done |
| FR-014 | T007 | T006 | Done |
| FR-015 | T006a | T006a | Done |
| DR-001 | T903 | — | Done |
| DR-002 | T008 | T021 | Done |
| DR-003 | T017 | T006, T021 | Done |
| DR-004 | T014 | T021 | Done |
| DR-005 | T016 | T021 | Done |
| DR-006 | T020 | T022 | Done |
