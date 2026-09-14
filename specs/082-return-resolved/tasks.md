---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: A Return Is Not Finished When It Arrives

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

Two are particular to this feature. The model attribute and its migration are one indivisible
step, as they were in Spec 076 — a field without its revision breaks every fresh database and
a revision without the field means nothing. And the write path must accept a resolution before
any story about outstanding quantities can be written at all.

## Phase 1: Specification and Design Gates

- [x] T001 Confirm the five accepted scope decisions are recorded in `specs/082-return-resolved/spec.md`
- [x] T002 Confirm every Constitution Check row is PASS and Complexity Tracking is empty in `specs/082-return-resolved/plan.md`
- [x] T003 Complete the reviewer-owned domain review in `specs/082-return-resolved/checklists/domain.md`
- [x] T004 Run `$speckit-analyze` and resolve every CRITICAL consistency or coverage finding

## Phase 2: Failing Proof

- [x] T005 [P] [US1] [FR-001] [FR-006] Add failing `tests/test_returns.py::test_a_movement_may_resolve_a_return` asserting the link persists and that a movement without one settles nothing
- [x] T006 [P] [US1] [FR-002] [FR-003] Add failing `tests/test_returns.py::test_a_resolution_is_validated` covering a target that is not a return, another tenant's return, another item, and a movement that does not leave the location the goods came back to
- [x] T007 [P] [US1] [FR-004] Add failing `tests/test_returns.py::test_resolutions_may_not_exceed_what_came_back`, with the positive control that resolving exactly what came back is accepted
- [x] T007a [P] [FR-004a] Add failing `tests/test_returns.py::test_a_backdated_resolution_is_accepted` proving it settles the return and teaches the norm a lag of zero
- [x] T008 [P] [US1] [FR-005] Add failing `tests/test_returns.py::test_a_return_may_be_resolved_in_parts` proving a restock and a scrap together settle one return
- [x] T009 [P] [FR-008] Add failing `test_derivation.py::test_the_resolution_norm_describes_this_tenant` asserting the threshold follows the median of resolved returns and that too little history claims nothing
- [x] T010 [P] [DR-005] Add failing `test_derivation.py::test_the_resolution_norm_is_learned_per_tenant` proving one tenant's speed never judges another
- [x] T011 [P] [US2] [FR-007] Add failing `test_derivation.py::test_return_unresolved` covering an old unresolved return, a partly resolved one, and a recent one
- [x] T012 [P] [FR-009] [DR-003] Add failing `test_derivation.py::test_a_voided_resolution_stops_counting`, covering a voided resolution and a voided return
- [x] T013 [P] [FR-010] [FR-011] [DR-004] Add failing `test_derivation.py::test_return_unresolved_exposes_full_entry_shape` asserting identity, severity, title, impact, record type/id, the quantities, the age, the threshold and opaque traces
- [x] T014 [P] [FR-012] [DR-001] [DR-002] Add failing `test_derivation.py::test_return_unresolved_clears_through_reality` proving restocking clears the entry with nothing persisted
- [x] T015 [P] [FR-016] Add failing `test_derivation.py::test_return_unresolved_orders_longest_first` proving deterministic order across repeated reads
- [x] T016 [P] [FR-013] Add failing `test_explanation.py::test_return_unresolved_explanation_and_not_found_parity` covering the identity, a cleared one, a malformed one and a foreign tenant
- [x] T017 [P] [FR-015] Extend `test_explanation.py::test_shared_consumer_parity_includes_new_classes` so the shared row contract must carry it
- [x] T018 [FR-014] Update the closed registry expectation in `test_coverage.py` and the class list in `tests/test_application_catalog.py`

## Phase 3: The Column and the Write Path

- [x] T019 [FR-001] **Model and migration together** — add `resolves_movement_id` as a nullable self-referencing foreign key on `Movement` in `packages/reality-core/src/reality/db/core.py` and create revision `0038_return_resolution` in `packages/reality-core/migrations/versions/`, revising `0037_invoice_order_link`, adding the column and dropping it on downgrade
- [x] T020 [FR-002] [FR-003] [FR-004] [DR-005] Validate the reference in `record_movement`: a `return` of the same tenant, the same item, out of the location the return brought the goods into, and never more in total than came back
- [x] T021 [FR-001] Accept the reference on the movement write model in `packages/reality-core/src/reality/web/api.py` and in the movement tool schema in `packages/reality-core/src/reality/mcp/catalog.py`
- [x] T022 Confirm the migration chain applies to an empty database and the whole backend suite passes with the column present and unused

## Phase 4: The Class

- [x] T023 [FR-008] [DR-005] Add the resolution norm to `packages/reality-core/src/reality/services/exceptions.py` using Spec 080's learned-threshold helper with its own floor, and record that floor's reasoning beside the others
- [x] T024 [US2] [FR-007] [FR-009] [FR-010] [DR-003] Add `_return_unresolved_exceptions` over returns with an outstanding quantity, reading both sides through the correction-aware movement path
- [x] T025 [FR-011] [FR-014] **Atomic activation** — register the derivator, place it in both order constants beside the other return classes, and declare it in `packages/reality-core/config/operational_exception_catalog.yaml` with severity, record type, the `082/FR-007` authority, evidence, description, owner and clearing path
- [x] T026 [FR-015] Prove rather than assert that no adapter change is required beyond the write field
- [x] T027 Classify any new public read in `packages/reality-core/config/tenant_isolation_catalog.yaml`
- [x] T028 Create `specs/082-return-resolved/quickstart.md` and record the result of the two independent acceptance stories

## Phase 5: Cross-References and Documentation

- [x] T029 Write the description so `return_unresolved` and `returned_not_credited` name each other as the two halves of one return's life — goods sitting against money not given back
- [x] T030 Extend `unexplained_movement`'s description to say that a return naming its delivery and settled by a later movement is explained at both ends
- [x] T031 Re-run the cross-reference review over all twenty classes and confirm every confusable pair is mutual
- [x] T032 [FR-014] Add the taxonomy row to `docs/features/operational_exceptions.md`, and record that the learned-norm rule now has four users
- [x] T033 Record the new relationship in `docs/DATA_MODEL.md` and in `docs/features/movements.md`, including that a null reference means the movement settles no return
- [x] T034 [P] Regenerate the catalog reference and run `npm run format` in `apps/docs`
- [x] T035 [P] Add the specification row and the new evidence rows to `docs/SPEC_COVERAGE_MATRIX.md`

## Final Phase: Cross-Cutting Review

- [x] T900 Run `make spec-check`
- [x] T901 Run `make lint` and the complete backend PostgreSQL suite
- [x] T902 Run the `apps/docs` tests and format check
- [x] T903 Review the migration chain and the downgrade path
- [x] T904 Review the final diff against the Constitution and the review risks in `plan.md`
- [x] T904a Measure the demo month's queue, report the number, and decide deliberately whether to teach the demo the new link
- [x] T905 Re-derive the feature number immediately before opening the pull request

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001 | T005 | T019, T021 | Done |
| FR-002 | T006 | T020 | Done |
| FR-003 | T006 | T020 | Done |
| FR-004 | T007 | T020 | Done |
| FR-004a | T007a | T020, T023 | Done |
| FR-005 | T008 | T020 | Done |
| FR-006 | T005 | T024 | Done |
| FR-007 | T011 | T024, T025 | Done |
| FR-008 | T009 | T023 | Done |
| FR-009 | T012 | T024 | Done |
| FR-010 | T013 | T024 | Done |
| FR-011 | T013 | T025 | Done |
| FR-012 | T014 | T024 | Done |
| FR-013 | T016 | T025 | Done |
| FR-014 | T018 | T025, T032 | Done |
| FR-015 | T017 | T026 | Done |
| FR-016 | T015 | T024 | Done |
| DR-001 | T014 | T024 | Done |
| DR-002 | T014 | T024 | Done |
| DR-003 | T012 | T024 | Done |
| DR-004 | T013 | T024 | Done |
| DR-005 | T010 | T020, T023 | Done |
| DR-006 | T018 | T025 | Done |
| DR-007 | T904 | — | Done |
