---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: Overdue Payables

**Input**: [`spec.md`](./spec.md), [`plan.md`](./plan.md), [`checklists/`](./checklists/)
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and resulting repository artifacts MUST be
written in English.

## Format

`- [ ] T001 [P?] [US1] [FR-001] Action with exact file path`

Every functional/domain requirement MUST appear in at least one test task and one
implementation or documentation task. Test tasks precede the code they prove.

## Sequencing Constraints

The three rules established by earlier specifications apply: evidence exists before a class
is declared, activation is atomic, and a class without a description, an owner and a
clearing path is refused.

## Phase 1: Specification and Design Gates

- [ ] T001 Confirm the accepted scope decisions and the three removals are recorded in `specs/074-trade-control-gaps/spec.md`
- [ ] T002 Confirm every Constitution Check row is PASS and Complexity Tracking is empty in `specs/074-trade-control-gaps/plan.md`
- [ ] T003 Complete the reviewer-owned domain review in `specs/074-trade-control-gaps/checklists/domain.md`
- [ ] T004 Run `$speckit-analyze` and resolve every CRITICAL consistency or coverage finding

## Phase 2: Failing Proof

All paths below are under `packages/reality-core/tests/operational_exceptions/`.

- [ ] T005 [P] [US1] [FR-001] Add failing `test_derivation.py::test_overdue_payable` asserting the entry, its due date, days overdue and outstanding amount
- [ ] T006 [P] [US1] [FR-002] [DR-002] Add failing `test_derivation.py::test_payable_and_receivable_share_one_rule` proving both sides derive the same due date from the same terms, including the cascade to the party
- [ ] T007 [P] [US1] [FR-003] Add failing `test_derivation.py::test_overdue_payable_boundaries` covering settled, not yet due, reversed, unreadable date, and a sales invoice that must stay a receivable
- [ ] T008 [P] [FR-004] [DR-003] Add failing `test_derivation.py::test_overdue_payable_entry_shape` asserting identity, severity, title, impact, record type/id, causal values and an opaque trace
- [ ] T009 [P] [FR-005] [DR-001] Add failing `test_derivation.py::test_overdue_payable_clears_through_payment` proving payment removes the entry with nothing persisted
- [ ] T010 [P] [DR-004] Add failing `test_derivation.py::test_overdue_payable_is_tenant_scoped` proving no leak across tenants
- [ ] T011 [P] [FR-007] Add failing `test_derivation.py::test_overdue_payable_orders_longest_first` proving deterministic order across repeated reads
- [ ] T012 [P] [FR-006] Add failing `test_explanation.py::test_new_trade_classes_explanation_and_not_found_parity` covering the identity, a settled one, a malformed one and a foreign tenant
- [ ] T013 [P] [FR-009] Extend `test_explanation.py::test_shared_consumer_parity_includes_new_classes` so the shared row contract must carry the class
- [ ] T014 [FR-008] Update the closed registry expectation in `test_coverage.py` and the class list in `tests/test_application_catalog.py`

## Phase 3: One Rule, Two Sides

- [ ] T015 [US1] [FR-002] [DR-002] Parameterise the open-item exception in `packages/reality-core/src/reality/services/exceptions.py` by document type, class id and title, leaving the due date, outstanding amount and exclusions where they are
- [ ] T016 [US1] Confirm the whole backend suite still passes, proving the extraction changed no behaviour before the payable consumes it
- [ ] T017 [US1] [FR-001] [FR-003] [DR-004] Add the supplier-invoice derivator over the parameterised rule
- [ ] T018 [US1] [FR-004] [FR-007] [FR-008] **Atomic activation** — register the derivator, place `overdue_payable` ninth in both order constants, and declare the class with severity, record type, `074/FR-001` authority, evidence, description, owner and clearing path
- [ ] T019 [US1] [DR-006] Cross-reference the payable with the receivable and with the overdue supplier delivery, amending those two descriptions so every pair names its sibling from both sides
- [ ] T020 [US1] Create `specs/074-trade-control-gaps/quickstart.md` and record the result of the independent acceptance stories

## Phase 4: Documentation

- [ ] T021 [FR-008] Add the taxonomy row to `docs/features/operational_exceptions.md`
- [ ] T022 [P] Regenerate the catalog reference and run `npm run format` in `apps/docs`
- [ ] T023 [P] Add the specification row and the new evidence rows to `docs/SPEC_COVERAGE_MATRIX.md`
- [ ] T024 [DR-006] Re-run the cross-reference review over all ten classes and confirm every confusable pair is mutual

## Final Phase: Cross-Cutting Review

- [ ] T900 Run `make spec-check` and confirm the traceability tables match the delivered tests
- [ ] T901 Run `make lint` and the complete backend PostgreSQL suite
- [ ] T902 Run the `apps/docs` tests and format check
- [ ] T903 Confirm no migration was added and `apps/web` and `provider-site` are unchanged
- [ ] T904 Review the final diff against the Constitution and every FR and DR, including the review risks in `plan.md`
- [x] T904a Measure the first-deployment payable volume on a realistic tenant, as was done for the receivable
- [ ] T905 Re-derive the feature number immediately before opening the pull request

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001 | T005 | T017, T018 | Pending |
| FR-002 | T006 | T015 | Pending |
| FR-003 | T007 | T017 | Pending |
| FR-004 | T008 | T018 | Pending |
| FR-005 | T009 | T017 | Pending |
| FR-006 | T012 | T017 | Pending |
| FR-007 | T011 | T018 | Pending |
| FR-008 | T014 | T018, T021 | Pending |
| FR-009 | T013 | T018 | Pending |
| DR-001 | T009 | T017 | Pending |
| DR-002 | T006 | T015 | Pending |
| DR-003 | T008 | T017 | Pending |
| DR-004 | T010 | T017 | Pending |
| DR-005 | T014 | T018 | Pending |
| DR-006 | T024 | T019 | Pending |
