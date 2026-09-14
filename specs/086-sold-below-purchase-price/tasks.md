---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: Sold for Less Than It Costs to Buy

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

This feature has four silences and they are the design, so each is proven with its positive
control before the class is written.

## Phase 1: Specification and Design Gates

- [x] T001 Confirm the five accepted scope decisions are recorded in `specs/086-sold-below-purchase-price/spec.md`
- [x] T002 Confirm every Constitution Check row is PASS and Complexity Tracking is empty in `specs/086-sold-below-purchase-price/plan.md`
- [x] T003 Complete the reviewer-owned domain review in `specs/086-sold-below-purchase-price/checklists/domain.md`
- [x] T004 Run `$speckit-analyze` and resolve every CRITICAL consistency or coverage finding

## Phase 2: Failing Proof

- [x] T005 [P] [US1] [FR-001] [FR-002] [FR-005] [DR-003] Add failing `test_derivation.py::test_sold_below_purchase_price` covering a line below the purchase price, one at exactly it, and both figures stated rather than adjusted
- [x] T006 [P] [FR-003] Add failing `test_derivation.py::test_the_price_standing_when_it_was_agreed_is_used`, with the positive control that a sale agreed after the rise is judged against the new price
- [x] T007 [P] [FR-004] Add failing `test_derivation.py::test_without_a_purchase_price_nothing_is_reported`, with the positive control that recording one reports the same line at once
- [x] T008 [P] [FR-006] Add failing `test_derivation.py::test_a_line_agreed_at_zero_is_a_decision`, with the positive control that a penny reports
- [x] T009 [P] [FR-007] [FR-009] Add failing `test_derivation.py::test_only_sales_lines_are_judged` covering a purchase order line and a line with no item, each with a positive control
- [x] T010 [P] [FR-008] Add failing `test_derivation.py::test_a_different_currency_or_unit_is_not_compared`, with the positive control that a matching pair reports
- [x] T011 [P] [FR-010] [FR-011] [DR-004] Add failing `test_derivation.py::test_the_pricing_entry_exposes_full_shape` asserting identity, severity, title, impact, record type/id, both prices, the shortfall and opaque traces
- [x] T012 [P] [FR-012] [DR-002] Add failing `test_derivation.py::test_the_pricing_entry_clears_through_reality` proving a corrected price clears the entry with nothing persisted
- [x] T013 [P] [FR-016] Add failing `test_derivation.py::test_the_pricing_entry_orders_longest_first` proving deterministic order across repeated reads
- [x] T014 [P] [DR-005] Add failing `test_derivation.py::test_the_pricing_class_is_tenant_scoped` proving neither the class nor the price lookup crosses tenants
- [x] T015 [P] [FR-013] Add failing `test_explanation.py::test_pricing_class_explanation_and_not_found_parity` covering the identity, a cleared one, a malformed one and a foreign tenant
- [x] T016 [P] [FR-015] Extend `test_explanation.py::test_shared_consumer_parity_includes_new_classes` so the shared row contract must carry it
- [x] T017 [FR-014] Update the closed registry expectation in `test_coverage.py` and the class list in `tests/test_application_catalog.py`

## Phase 3: The Derivation

- [x] T018 [FR-003] [DR-005] Add the standing-purchase-price lookup to `packages/reality-core/src/reality/services/exceptions.py`, using the same validity window and quantity-break ordering the resolver uses, and saying in its docstring that it answers a narrower question than `resolve_price` and why a customer party cannot be passed to that one
- [x] T019 [US1] [FR-001] [FR-002] [FR-004] [FR-005] [FR-006] [FR-007] [FR-008] [FR-009] [FR-010] Add `_sold_below_purchase_price_exceptions` over sales order lines, with each of the four silences written as an explicit guard rather than falling out of a query
- [x] T020 [FR-011] [FR-014] **Atomic activation** — register the derivator, place it in both order constants beside the other pricing class, and declare it in `packages/reality-core/config/operational_exception_catalog.yaml` with severity, record type, the `086/FR-001` authority, evidence, description, owner and clearing path
- [x] T021 [FR-014] Say plainly in the class's guidance that it compares an agreed sales price with an agreed purchase price, that it is not accounting margin, and that it is silent for a company keeping no purchase prices
- [x] T022 [FR-015] Prove rather than assert that no adapter change is required
- [x] T023 Create `specs/086-sold-below-purchase-price/quickstart.md` and record the result of the independent acceptance story

## Phase 4: Cross-References and Documentation

- [x] T024 Write the description so this class and `invoice_price_differs` name each other as the two things that can be wrong about a price — whether the invoice matches the agreement, and whether the agreement was sound
- [x] T025 Re-run the cross-reference review over all twenty-three classes and confirm every confusable pair is mutual
- [x] T026 [FR-014] Add the taxonomy row to `docs/features/operational_exceptions.md`, including what the class does not see
- [x] T027 [P] Regenerate the catalog reference and run `npm run format` in `apps/docs`
- [x] T028 [P] Add the specification row to `docs/SPEC_COVERAGE_MATRIX.md`

## Final Phase: Cross-Cutting Review

- [x] T900 Run `make spec-check`
- [x] T901 Run `make lint` and the complete backend PostgreSQL suite
- [x] T902 Run the `apps/docs` tests and format check
- [x] T903 [DR-001] Confirm no migration was added
- [x] T904 Review the final diff against the Constitution and the review risks in `plan.md`
- [x] T904a Measure the demo month's queue and confirm it is unchanged, recording that the demo keeps no purchase price list so this proves nothing about volume
- [x] T905 Re-derive the feature number with `scripts/next_feature_number.py` immediately before opening the pull request, and take the number it gives

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001 | T005 | T019, T020 | Done |
| FR-002 | T005 | T019 | Done |
| FR-003 | T006 | T018 | Done |
| FR-004 | T007 | T019 | Done |
| FR-005 | T005 | T019 | Done |
| FR-006 | T008 | T019 | Done |
| FR-007 | T009 | T019 | Done |
| FR-008 | T010 | T019 | Done |
| FR-009 | T009 | T019 | Done |
| FR-010 | T011 | T019 | Done |
| FR-011 | T011 | T020 | Done |
| FR-012 | T012 | T019 | Done |
| FR-013 | T015 | T020 | Done |
| FR-014 | T017 | T020, T021, T026 | Done |
| FR-015 | T016 | T022 | Done |
| FR-016 | T013 | T019 | Done |
| DR-001 | T903 | — | Done |
| DR-002 | T012 | T019 | Done |
| DR-003 | T005 | T019 | Done |
| DR-004 | T011 | T019 | Done |
| DR-005 | T014 | T018 | Done |
| DR-006 | T017 | T020 | Done |
