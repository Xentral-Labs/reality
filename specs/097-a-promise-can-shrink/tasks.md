---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: Eighty of the Hundred

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

**The rename lands alone**, so the suite proves an operation that shipped hours ago still works
before anything new is added to it.

**The shared rule exists before any caller uses it.** This is the fourth derived figure this work
has had to keep single-sourced — units, learned thresholds, the date in force — and the pattern
by now is to write it once rather than find copies later.

## Phase 1: Specification and Design Gates

- [x] T001 Confirm the accepted scope decisions are recorded in `specs/097-a-promise-can-shrink/spec.md`
- [x] T002 Confirm every Constitution Check row is PASS and the Complexity Tracking entry justifies the column in `specs/097-a-promise-can-shrink/plan.md`
- [x] T003 Complete the reviewer-owned domain review in `specs/097-a-promise-can-shrink/checklists/domain.md`
- [x] T004 Run `$speckit-analyze` and resolve every CRITICAL consistency or coverage finding
- [x] T005 Confirm against the code that nothing assigns to `Commitment.quantity` and that `create_commitment` is reachable from no surface, so this is a missing capability rather than an awkward one

## Phase 2: The Rename, Alone

- [x] T006 [FR-009] Rename `revise_commitment_due_date` to `revise_commitment` in the service, the command catalog, the tenant isolation catalog, the business event catalog, the agent tool, the MCP schema and the endpoint
- [x] T007 [FR-010] Run the complete existing backend suite and record that the operation still behaves exactly as it did

## Phase 3: The Statement

- [x] T008 [P] [FR-001] [DR-002] [DR-006] Add failing `test_commitment_revisions.py::test_one_statement_can_restate_both`, asserting one record carries both figures, the promise is untouched, and each figure is the one stated
- [x] T009 [P] [FR-002] [FR-003] [FR-008] Add failing `test_commitment_revisions.py::test_a_statement_must_restate_something` covering neither figure, zero, a negative quantity and a closed promise, each with a positive control
- [x] T010 [P] [FR-004] Add failing `test_commitment_revisions.py::test_the_quantity_in_force_is_the_latest_stated`, including a later statement about the date alone leaving an earlier quantity standing
- [x] T011 [P] [FR-006] Add failing `test_commitment_revisions.py::test_a_promise_can_shrink_below_what_arrived`
- [x] T012 [P] [FR-007] Add failing `test_commitment_revisions.py::test_shrinking_to_what_arrived_finishes_the_promise`
- [x] T013 [DR-001] Add the nullable `quantity` to `CommitmentRevision`, relax `due_at`, and add `migrations/versions/0042_commitment_revision_quantity.py` with no backfill
- [x] T014 [FR-001] [FR-002] [FR-003] [FR-006] [FR-007] [DR-003] Add `commitment_quantity` beside `commitment_due_at` and extend the operation, settling the promise when its stated quantity falls to what has moved

## Phase 4: What Reads It

- [x] T015 [P] [FR-005] Add failing `test_derivation.py::test_a_shrunk_promise_is_judged_by_what_is_in_force`
- [x] T016 [P] [DR-003] Add failing `test_derivation.py::test_one_rule_answers_the_quantity_in_force`
- [x] T017 [FR-005] Read the quantity in force in `open_quantity` and in the three places the exceptions module reads the promise directly
- [x] T018 [FR-010] Run the complete suite and confirm nothing moved for an unrevised promise
- [x] T019 Create `specs/097-a-promise-can-shrink/quickstart.md` and record the three independent acceptance stories

## Phase 5: Surfaces and Documentation

- [x] T020 [FR-009] Add the quantity to the command's parameter descriptions, the MCP schema and the endpoint body
- [x] T021 [FR-009] Run the drift gates and confirm every catalog agrees
- [x] T022 Record the quantity in force and the reserved-stock limit in `docs/features/commitments.md`
- [x] T023 [P] Record the supplier confirming a smaller quantity in `docs/features/procure_to_pay.md`
- [x] T024 [P] Regenerate the catalog reference and run `npm run format` in `apps/docs`
- [x] T025 [P] Add the specification row to `docs/SPEC_COVERAGE_MATRIX.md`, recording that this reverses a Spec 093 non-goal and why

## Final Phase: Cross-Cutting Review

- [x] T900 Run `make spec-check`
- [x] T901 Run `make lint` and the complete backend PostgreSQL suite in CI's invocation and ordering
- [x] T902 Run the `apps/docs` tests and format check
- [x] T903 [DR-001] Confirm exactly one migration was added and that it has a working downgrade
- [x] T904 Review the final diff against the Constitution and the review risks in `plan.md`
- [x] T904a Confirm the demo month's pinned queue is unchanged
- [x] T905 Re-derive the feature number with `scripts/next_feature_number.py` immediately before opening the pull request, and take the number it gives

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001 | T008 | T013, T014 | Done |
| FR-002 | T009 | T014 | Done |
| FR-003 | T009 | T014 | Done |
| FR-004 | T010 | T014 | Done |
| FR-005 | T015 | T017 | Done |
| FR-006 | T011 | T014 | Done |
| FR-007 | T012 | T014 | Done |
| FR-008 | T009 | T014 | Done |
| FR-009 | T021 | T006, T020 | Done |
| FR-010 | T007, T018 | — | Done |
| DR-001 | T903 | T013 | Done |
| DR-002 | T008 | T014 | Done |
| DR-003 | T016 | T014, T017 | Done |
| DR-004 | T009 | T014 | Done |
| DR-005 | T901 | — | Done |
| DR-006 | T008 | T014 | Done |
