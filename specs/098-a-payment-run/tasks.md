---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: One Friday, Forty Payments

**Input**: [`spec.md`](./spec.md), [`plan.md`](./plan.md), [`checklists/`](./checklists/)
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and resulting repository artifacts MUST be
written in English.

## Format

`- [x] T001 [P?] [US1] [FR-001] Action with exact file path`

Every functional/domain requirement MUST appear in at least one test task and one
implementation or documentation task. Test tasks precede the code they prove.

## Sequencing Constraints

The established rules apply. Two are particular to this feature.

**The duplicate rule moves before anything consumes it**, with the whole suite proving the
exception class that has owned it since Spec 078 still reports exactly what it reported.

**The payable rule exists before either caller.** This is the fifth derived figure this line of
work has had to keep single-sourced, and the pattern by now is to write it once rather than find
copies later.

## Phase 1: Specification and Design Gates

- [x] T001 Confirm the accepted scope decisions are recorded in `specs/098-a-payment-run/spec.md`
- [x] T002 Confirm every Constitution Check row is PASS and that no Complexity Tracking exception is claimed in `specs/098-a-payment-run/plan.md`
- [x] T003 Complete the reviewer-owned domain review in `specs/098-a-payment-run/checklists/domain.md`
- [x] T004 Run `$speckit-analyze` and resolve every CRITICAL consistency or coverage finding
- [x] T005 Confirm against the code that `post_supplier_payment` takes exactly one invoice and that nothing in the product records a decision above a payment, so this is a missing capability rather than an awkward one

## Phase 2: The Duplicate Rule Moves, Alone

- [x] T006 [DR-002] Move the party-and-number grouping out of `_duplicate_supplier_invoice_exceptions` into `core.duplicate_supplier_invoices`, leaving the exception class as its consumer
- [x] T007 [FR-015] Run the complete existing backend suite and record that the duplicate class reports exactly what it reported

## Phase 3: What Is Payable

- [x] T008 [P] [FR-001] [DR-002] Add failing `test_payment_runs.py::test_one_rule_decides_what_is_payable` and `::test_the_duplicate_rule_has_one_home`
- [x] T009 [P] [FR-002] [FR-006] Add failing `test_payment_runs.py::test_what_is_not_payable_and_why`, covering all four exclusions, each with a positive control
- [x] T010 [FR-001] [FR-002] Add `payable_supplier_invoices` to `services/core.py`, returning the payable register rows and the withheld rows with their reasons

## Phase 4: The Preview

- [x] T011 [P] [FR-003] Add failing `test_payment_runs.py::test_the_preview_writes_nothing`
- [x] T012 [P] [FR-004] Add failing `test_payment_runs.py::test_the_preview_proposes_what_is_due_and_what_is_discountable`, including the order two identical reads must produce
- [x] T013 [P] [FR-005] [DR-006] Add failing `test_payment_runs.py::test_the_discount_is_named_never_applied`
- [x] T014 [P] [FR-007] Add failing `test_payment_runs.py::test_the_preview_totals_per_supplier_and_overall`
- [x] T015 [P] [DR-003] Add failing `test_payment_runs.py::test_the_preview_reads_the_register`
- [x] T016 [FR-003] [FR-004] [FR-005] [FR-006] [FR-007] [DR-003] Add `preview_payment_run` to `services/core.py`, assembling every figure from `aging_register`

## Phase 5: The Run

- [x] T017 [P] [FR-008] Add failing `test_payment_runs.py::test_a_run_pays_exactly_what_it_was_given`
- [x] T018 [P] [FR-009] [FR-010] Add failing `test_payment_runs.py::test_a_run_refuses` and `::test_a_run_is_one_currency`, each refusal with a positive control
- [x] T019 [P] [FR-011] Add failing `test_payment_runs.py::test_a_failed_run_leaves_nothing_behind`
- [x] T020 [P] [FR-012] Add failing `test_payment_runs.py::test_a_run_is_recorded_as_one_decision`
- [x] T021 [P] [FR-013] Add failing `test_payment_runs.py::test_a_payment_in_a_run_is_an_ordinary_payment`
- [x] T022 [P] [DR-004] Add failing `test_payment_runs.py::test_a_run_is_tenant_scoped`
- [x] T023 [FR-008] [FR-009] [FR-010] [FR-011] [FR-012] [FR-013] Add `execute_payment_run` to `services/core.py`, refusing everything before it writes and committing once
- [x] T024 [FR-015] Run the complete suite and confirm nothing moved for a tenant that runs no payment run
- [x] T025 Create `specs/098-a-payment-run/quickstart.md` and record the three independent acceptance stories

## Phase 6: Surfaces and Documentation

- [x] T026 [DR-007] Declare both commands in `config/command_catalog.yaml`, add both operations to `config/tenant_isolation_catalog.yaml`, and add `payments.run` to `config/business_event_catalog.yaml`
- [x] T027 [DR-007] Add the agent tools, the MCP schemas and the endpoints
- [x] T028 [FR-014] Correct the `purchase_discount_available` guidance in `config/operational_exception_catalog.yaml` to name the operation that now exists
- [x] T029 [DR-007] Run the drift gates and confirm every catalog agrees
- [x] T030 Record the payment run in `docs/features/procure_to_pay.md`, including what it refuses to compute and the missing per-invoice block
- [x] T031 [P] Record in `docs/features/operational_exceptions.md` that the discount entry now has an operation behind it
- [x] T032 [P] Regenerate the catalog reference and run `npm run format` in `apps/docs`
- [x] T033 [P] Add the specification row to `docs/SPEC_COVERAGE_MATRIX.md`

## Final Phase: Cross-Cutting Review

- [x] T900 Run `make spec-check`
- [x] T901 Run `make lint` and the complete backend PostgreSQL suite in CI's invocation and ordering
- [x] T902 Run the `apps/docs` tests and format check
- [x] T903 [DR-001] Confirm no migration was added
- [x] T904 Review the final diff against the Constitution and the review risks in `plan.md`
- [x] T904a Confirm the demo month's pinned queue is unchanged
- [x] T905 Re-derive the feature number with `scripts/next_feature_number.py` immediately before opening the pull request, and take the number it gives

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001 | T008 | T010 | Done |
| FR-002 | T009 | T010 | Done |
| FR-003 | T011 | T016 | Done |
| FR-004 | T012 | T016 | Done |
| FR-005 | T013 | T016 | Done |
| FR-006 | T009 | T010, T016 | Done |
| FR-007 | T014 | T016 | Done |
| FR-008 | T017 | T023 | Done |
| FR-009 | T018 | T023 | Done |
| FR-010 | T018 | T023 | Done |
| FR-011 | T019 | T023 | Done |
| FR-012 | T020 | T023, T026 | Done |
| FR-013 | T021 | T023 | Done |
| FR-014 | T029 | T028, T031 | Done |
| FR-015 | T007, T024 | — | Done |
| DR-001 | T903 | — | Done |
| DR-002 | T008 | T006 | Done |
| DR-003 | T015 | T016 | Done |
| DR-004 | T022 | T010, T016, T023 | Done |
| DR-005 | T901 | — | Done |
| DR-006 | T013 | T023 | Done |
| DR-007 | T029 | T026, T027 | Done |
