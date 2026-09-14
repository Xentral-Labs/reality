---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: The Discount Nobody Is Watching

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

Two constraints are particular to this feature. The schema lands before anything reads it, and
the columns are proven to change nothing for a term that states no discount before any
derivation is written. And **DR-007 is checked as a rule, not only as a test**: no division may
appear anywhere in this feature's code.

## Phase 1: Specification and Design Gates

- [x] T001 Confirm the accepted scope decisions are recorded in `specs/088-early-payment-discount/spec.md`
- [x] T002 Confirm every Constitution Check row is PASS and the Complexity Tracking entry justifies the schema change in `specs/088-early-payment-discount/plan.md`
- [x] T003 Complete the reviewer-owned domain review in `specs/088-early-payment-discount/checklists/domain.md`
- [x] T004 Run `$speckit-analyze` and resolve every CRITICAL consistency or coverage finding
- [x] T005 Re-check the "this needs schema" note against the model rather than believing it, and record the answer in the Complexity Tracking table

## Phase 2: The Schema and Its Silence

- [x] T006 [FR-001] [DR-001] Add failing `test_payment_terms.py::test_a_payment_term_can_state_a_discount`, with the positive control that a term stating neither figure behaves exactly as before
- [x] T007 [P] [FR-002] [FR-003] Add failing `test_payment_terms.py::test_a_discount_rate_and_window_are_validated` covering a rate of zero, a rate of a hundred, negative days, and each half of the condition alone — every one with a positive control
- [x] T008 [DR-001] Add `discount_percent` and `discount_days` to `packages/reality-core/src/reality/db/core.py`, both nullable, and one revision `migrations/versions/0039_early_payment_discount.py` with no backfill
- [x] T009 [FR-001] [FR-002] [FR-003] Accept and validate both figures in `create_payment_term` and `update_payment_term`, refusing either half alone
- [x] T010 [FR-001] Run the complete existing backend suite unchanged and record that it passes, before anything reads the columns

## Phase 3: One Rule for the Window

- [x] T011 [P] [FR-004] [FR-005] [DR-003] Add failing `test_payment_terms.py::test_the_discount_deadline_is_one_shared_rule` proving the deadline comes from the same place as the due date and resolves the term the same way, with the positive control that a term without a discount yields no deadline
- [x] T012 [FR-004] [DR-003] Add `invoice_discount_date` beside `invoice_due_date` in `packages/reality-core/src/reality/services/core.py`, and enrich every aging register row with the deadline and the governing term
- [x] T013 [FR-005] Prove rather than assert that `effective_payment_term` is reused and no second term resolution exists

## Phase 4: Failing Proof for the Class and the Cause

- [x] T014 [P] [US1] [FR-007] Add failing `test_derivation.py::test_purchase_discount_available` covering an unpaid supplier invoice inside its window, with the positive control that a term granting no discount reports nothing for the same invoice
- [x] T015 [P] [FR-008] [DR-002] Add failing `test_derivation.py::test_the_discount_entry_ends_both_ways` proving settlement ends it and the deadline passing ends it, with nothing persisted either way
- [x] T016 [P] [FR-006] Add failing `test_derivation.py::test_no_discount_amount_is_ever_reported` asserting that every money figure in the entry equals a figure the ledger holds
- [x] T017 [P] [US2] [FR-010] [FR-011] Add failing `test_derivation.py::test_a_discount_taken_explains_the_remainder` covering a remainder within the rate, one beyond it, a payment after the deadline and an invoice nobody paid — each with a positive control — and asserting the entry is otherwise identical
- [x] T018 [P] [FR-012] Add failing `test_derivation.py::test_the_discount_reason_works_on_both_sides` covering a customer taking one and the company taking one from a supplier
- [x] T019 [P] [FR-013] [DR-004] Add failing `test_derivation.py::test_the_discount_entry_exposes_full_shape` asserting identity, severity, title, impact, record type/id, the rate, the deadline, the outstanding amount and opaque traces
- [x] T020 [P] [FR-017] Add failing `test_derivation.py::test_the_discount_entry_orders_by_deadline` proving the soonest expiry is first and the order is the same on repeated reads
- [x] T021 [P] [DR-005] Add failing `test_derivation.py::test_the_discount_class_is_tenant_scoped` proving neither the class, the cause nor the deadline lookup crosses tenants
- [x] T022 [P] [DR-007] Add failing `test_derivation.py::test_nothing_in_this_feature_divides`, walking the syntax tree of the discount comparison and both derivations for a division node rather than searching the text for a slash
- [x] T023 [P] [FR-014] Add failing `test_explanation.py::test_discount_class_explanation_and_not_found_parity` covering the identity, a cleared one, a malformed one and a foreign tenant
- [x] T024 [P] [FR-016] Extend `test_explanation.py::test_shared_consumer_parity_includes_new_classes` so the shared row contract must carry it
- [x] T025a [FR-009] Add failing `test_coverage.py::test_the_discount_guidance_names_both_endings`, reading the class's own guidance for both ways it ends
- [x] T025 [FR-015] [DR-006] Update the closed registry expectation in `test_coverage.py`, the cause vocabulary expectation, and the class list in `tests/test_application_catalog.py`

## Phase 5: The Class and the Cause

- [x] T026 [US1] [FR-007] [FR-008] [FR-013] [FR-017] [DR-002] [DR-005] Add `_purchase_discount_available_exceptions` over the aging register, sorting on the deadline
- [x] T027 [US2] [FR-010] [FR-011] [FR-012] [DR-007] Add the discount test to `_open_item_exceptions` as a cause on both open-item classes, with both sides of the comparison multiplied out and a comment saying that a division here would be a defect
- [x] T028 [FR-015] [DR-006] **Atomic activation** — register the derivator, place the class in both order constants, add the cause to the closed vocabulary, and declare both in `packages/reality-core/config/operational_exception_catalog.yaml` with severity, record type, the `088/FR-007` and `088/FR-010` authorities, evidence, description, owner and clearing path
- [x] T029 [FR-009] Say plainly in the class's guidance that it goes quiet both when the discount is taken and when it is lost, and that only the payment says which
- [x] T030 Create `specs/088-early-payment-discount/quickstart.md` and record the result of the two independent acceptance stories

## Phase 6: Surfaces

- [x] T031 [FR-018] Add failing surface tests covering the API, MCP and CLI paths that record a payment term
- [x] T032 [FR-018] Carry both figures through `packages/reality-core/src/reality/web/api.py`, `mcp/catalog.py` and `cli/app.py`, keeping every one of them working unchanged when neither figure is stated
- [x] T033 [FR-018] Add the two parameter descriptions to `packages/reality-core/config/command_catalog.yaml` and confirm the records-discover field list still matches the model

## Phase 7: Cross-References and Documentation

- [x] T034 Write the descriptions so this class and the two overdue classes name each other: one is an invoice not yet due where money can still be saved, the others are invoices past due — and the discount reason is what connects them
- [x] T035 Re-run the cross-reference review over all twenty-five classes and confirm every confusable pair is mutual
- [x] T036 [FR-015] Add the taxonomy row and the discount rule to `docs/features/operational_exceptions.md`, including why no amount is computed
- [x] T037 [P] Record the two new payment-term figures in `docs/features/master_data.md` and the window rule in `docs/features/ledger.md`
- [x] T038 [P] Regenerate the catalog reference and run `npm run format` in `apps/docs`
- [x] T039 [P] Add the specification row to `docs/SPEC_COVERAGE_MATRIX.md`

## Final Phase: Cross-Cutting Review

- [x] T900 Run `make spec-check`
- [x] T901 Run `make lint` and the complete backend PostgreSQL suite
- [x] T902 Run the `apps/docs` tests and format check
- [x] T903 [DR-001] Confirm exactly one migration was added and that it has a working downgrade
- [x] T904 Review the final diff against the Constitution and the review risks in `plan.md`
- [x] T904a [DR-007] Read the whole diff for a division operator and confirm there is none
- [x] T904b Measure the demo month's queue and confirm it is unchanged, recording that the demo records no discount terms so this proves nothing about volume
- [x] T905 Re-derive the feature number with `scripts/next_feature_number.py` immediately before opening the pull request, and take the number it gives

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001 | T006, T010 | T008, T009 | Done |
| FR-002 | T007 | T009 | Done |
| FR-003 | T007 | T009 | Done |
| FR-004 | T011 | T012 | Done |
| FR-005 | T011 | T013 | Done |
| FR-006 | T016 | T026, T027 | Done |
| FR-007 | T014 | T026, T028 | Done |
| FR-008 | T015 | T026 | Done |
| FR-009 | T025a | T029 | Done |
| FR-010 | T017 | T027 | Done |
| FR-011 | T017 | T027 | Done |
| FR-012 | T018 | T027 | Done |
| FR-013 | T019 | T026 | Done |
| FR-014 | T023 | T028 | Done |
| FR-015 | T025 | T028, T029, T036 | Done |
| FR-016 | T024 | T028 | Done |
| FR-017 | T020 | T026 | Done |
| FR-018 | T031 | T032, T033 | Done |
| DR-001 | T903 | T008 | Done |
| DR-002 | T015 | T026 | Done |
| DR-003 | T011 | T012 | Done |
| DR-004 | T019 | T026 | Done |
| DR-005 | T021 | T026, T027 | Done |
| DR-006 | T025 | T028 | Done |
| DR-007 | T022, T904a | T027 | Done |
