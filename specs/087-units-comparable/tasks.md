---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: Say When the Units Do Not Meet

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

This feature has an additional constraint the others did not: it changes a rule six shipped
classes already use. The shared decision is therefore built and proven against the **existing**
suites before the new class exists, so that "nothing moved" is evidence rather than a claim.

## Phase 1: Specification and Design Gates

- [x] T001 Confirm the five accepted scope decisions are recorded in `specs/087-units-comparable/spec.md`
- [x] T002 Confirm every Constitution Check row is PASS and Complexity Tracking is empty in `specs/087-units-comparable/plan.md`
- [x] T003 Complete the reviewer-owned domain review in `specs/087-units-comparable/checklists/domain.md`
- [x] T004 Run `$speckit-analyze` and resolve every CRITICAL consistency or coverage finding

## Phase 2: Failing Proof for the Shared Decision

- [x] T005 [P] [US1] [FR-001] [FR-002] Add failing `test_derivation.py::test_a_stated_conversion_lets_the_comparison_happen`, ordering in boxes and billing in pieces, asserting the shortfall is reported in the unit of the agreement and that both figures are ones the tenant recorded
- [x] T006 [P] [FR-003] Add failing `test_derivation.py::test_an_inexact_conversion_is_declined`, with the positive control that the same pair made exact reports at once
- [x] T007 [P] [FR-004] Add failing `test_derivation.py::test_a_useless_factor_is_no_relation` covering zero and a negative factor, each with a positive control
- [x] T008 [P] [FR-005] Add failing `test_derivation.py::test_a_third_unit_has_no_stated_relation`, with the positive control that the item's own purchase unit converts
- [x] T009 [P] [FR-006] [FR-008a] Add failing `test_derivation.py::test_prices_are_never_converted`, proving `invoice_price_differs` stays silent for a price pair whose quantities convert perfectly and that the decline produces no `units_not_comparable` entry either, with the positive control that a matching-unit price difference still reports
- [x] T010 [P] [DR-003] Add failing `test_derivation.py::test_one_decision_answers_comparability` asserting no class decides units for itself
- [x] T011 [FR-015] Run the complete existing `tests/operational_exceptions/` suite unchanged and record that it passes, before the new class exists

## Phase 3: The Shared Decision

- [x] T012 [FR-001] [FR-002] [FR-003] [FR-004] [FR-005] Add the comparability helper to `packages/reality-core/src/reality/services/exceptions.py`: given a line and a target unit, return the quantity in that unit or nothing, converting only across the item's own stock and purchase units, only by a factor above zero, and only where the result is exact
- [x] T013 [FR-006] Add the deliberately narrower helper the price classes use — units equal or no comparison — and say in its docstring that it exists so a price can never reach the converting one
- [x] T014 [DR-003] Replace the three inline unit checks in `_billed_quantity`, `_credited_quantity` and `_invoice_price_differs_exceptions` with the appropriate helper, leaving no fourth copy of the rule
- [x] T015 [FR-015] Re-run the complete existing suite and confirm it still passes untouched

## Phase 4: Failing Proof for the Class

- [x] T016 [P] [US2] [FR-007] [FR-008] Add failing `test_derivation.py::test_units_not_comparable` proving one entry per item naming both units and the line count, and none per line
- [x] T016a [P] [FR-008] Add failing `test_derivation.py::test_the_entry_says_which_of_the_two_went_wrong`, distinguishing an item with no stated relation from one whose stated relation leaves a remainder
- [x] T017 [P] [FR-009] [DR-004] Add failing `test_derivation.py::test_the_units_entry_exposes_full_shape` asserting identity, severity, title, impact, record type/id, the units, the line count and opaque traces
- [x] T018 [P] [FR-010] [DR-002] Add failing `test_derivation.py::test_the_units_entry_clears_through_reality` proving that stating the relation clears the entry with nothing persisted
- [x] T019 [P] [FR-014] Add failing `test_derivation.py::test_the_units_entry_orders_deterministically` across repeated reads and several items
- [x] T020 [P] [DR-005] Add failing `test_derivation.py::test_the_units_class_is_tenant_scoped` proving neither the class nor the conversion lookup crosses tenants
- [x] T021 [P] [FR-011] Add failing `test_explanation.py::test_units_class_explanation_and_not_found_parity` covering the identity, a cleared one, a malformed one and a foreign tenant
- [x] T022 [P] [FR-013] Extend `test_explanation.py::test_shared_consumer_parity_includes_new_classes` so the shared row contract must carry it
- [x] T023 [FR-012] Update the closed registry expectation in `test_coverage.py` and the class list in `tests/test_application_catalog.py`

## Phase 5: The Class

- [x] T024 [US2] [FR-007] [FR-008] [FR-009] [FR-010] [FR-014] [DR-002] [DR-005] Add `_units_not_comparable_exceptions` over the pairs the comparisons declined, grouping by item and sorting on the item's identity because the condition has no meaningful instant
- [x] T025 [FR-012] **Atomic activation** — register the derivator, place it in both order constants, and declare it in `packages/reality-core/config/operational_exception_catalog.yaml` with severity, record type, the `087/FR-007` authority, evidence, description, owner and clearing path
- [x] T026 [FR-012] Write the guidance so it names the checks being declined for this item, and says plainly that the fix is to state the item's conversion once rather than to touch the lines
- [x] T027 [FR-013] Prove rather than assert that no adapter change is required
- [x] T028 Create `specs/087-units-comparable/quickstart.md` and record the result of the independent acceptance story

## Phase 6: Cross-References and Documentation

- [x] T029 Write the description so this class and the quantity classes it blinds name each other: it says which checks are not being made, and they say that a pair in incomparable units is reported there instead of ignored
- [x] T030 Re-run the cross-reference review over all twenty-four classes and confirm every confusable pair is mutual
- [x] T031 [FR-012] Add the taxonomy row to `docs/features/operational_exceptions.md`, including the comparability rule and why prices are excluded from it
- [x] T032 [P] Regenerate the catalog reference and run `npm run format` in `apps/docs`
- [x] T033 [P] Add the specification row to `docs/SPEC_COVERAGE_MATRIX.md`

## Final Phase: Cross-Cutting Review

- [x] T900 Run `make spec-check`
- [x] T901 Run `make lint` and the complete backend PostgreSQL suite
- [x] T902 Run the `apps/docs` tests and format check
- [x] T903 [DR-001] Confirm no migration was added
- [x] T904 Review the final diff against the Constitution and the review risks in `plan.md`
- [x] T904a Measure the demo month's queue and confirm it is unchanged, recording what the demo does and does not record about units rather than treating an unchanged queue as proof
- [x] T905 Re-derive the feature number with `scripts/next_feature_number.py` immediately before opening the pull request, and take the number it gives

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001 | T005 | T012 | Done |
| FR-002 | T005 | T012 | Done |
| FR-003 | T006 | T012 | Done |
| FR-004 | T007 | T012 | Done |
| FR-005 | T008 | T012 | Done |
| FR-006 | T009 | T013, T014 | Done |
| FR-007 | T016 | T024, T025 | Done |
| FR-008 | T016, T016a | T024 | Done |
| FR-008a | T009 | T024 | Done |
| FR-009 | T017 | T024 | Done |
| FR-010 | T018 | T024 | Done |
| FR-011 | T021 | T025 | Done |
| FR-012 | T023 | T025, T026, T031 | Done |
| FR-013 | T022 | T027 | Done |
| FR-014 | T019 | T024 | Done |
| FR-015 | T011, T015 | T014 | Done |
| DR-001 | T903 | — | Done |
| DR-002 | T018 | T024 | Done |
| DR-003 | T010 | T014 | Done |
| DR-004 | T017 | T024 | Done |
| DR-005 | T020 | T024 | Done |
| DR-006 | T023 | T025 | Done |
