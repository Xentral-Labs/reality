---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: When the Other Side Says a New Date

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

**The schema lands and proves it changed nothing before any class reads it.** A tenant with no
revisions must behave exactly as it does today, and that is run as a whole suite rather than
argued.

**The shared rule exists before any class calls it.** The date in force is the third derived
figure this line of work has had to make single-sourced after finding copies of it — units in
087, learned thresholds in 089 — so it is written once, from the start.

## Phase 1: Specification and Design Gates

- [x] T001 Confirm the accepted scope decisions are recorded in `specs/093-promises-can-be-revised/spec.md`
- [x] T002 Confirm every Constitution Check row is PASS and the Complexity Tracking entry justifies the table against a column in `specs/093-promises-can-be-revised/plan.md`
- [x] T003 Complete the reviewer-owned domain review in `specs/093-promises-can-be-revised/checklists/domain.md`
- [x] T004 Run `$speckit-analyze` and resolve every CRITICAL consistency or coverage finding
- [x] T005 Confirm against the code that nothing updates `due_at` today, so this is a missing capability rather than an unreachable one

## Phase 2: The Record

- [x] T006 [P] [FR-001] [FR-002] [DR-002] [DR-007] Add failing `test_commitment_revisions.py::test_a_new_date_never_erases_the_old_one`, asserting the promise's own date is untouched, every statement is kept, and each carries when it was stated
- [x] T007 [P] [FR-003] Add failing `test_commitment_revisions.py::test_the_date_in_force_is_the_latest_stated`, including two statements at the same instant
- [x] T008 [P] [FR-008] Add failing `test_commitment_revisions.py::test_a_revision_is_refused_where_it_makes_no_sense` covering a fulfilled promise, a cancelled one, an unknown one and an unreadable date, each with a positive control
- [x] T009 [P] [FR-009] Add failing `test_commitment_revisions.py::test_a_hold_does_not_block_recording_what_was_said`
- [x] T010 [P] [DR-004] Add failing `test_commitment_revisions.py::test_revisions_are_tenant_scoped`
- [x] T011 [DR-001] Add the `CommitmentRevision` model to `packages/reality-core/src/reality/db/core.py` and one revision `migrations/versions/0040_commitment_revisions.py` with no backfill
- [x] T012 [FR-001] [FR-008] [FR-009] [FR-010] [DR-003] Add `revise_commitment_due_date` and the shared date-in-force rule to `packages/reality-core/src/reality/services/core.py`
- [x] T013 [FR-013] Run the complete existing backend suite and record that a tenant with no revisions behaves exactly as it does today

## Phase 3: Failing Proof for the Queue

- [x] T014 [P] [US1] [FR-004] Add failing `test_derivation.py::test_a_revised_promise_is_judged_by_its_new_date`, with the positive control that the same promise past its revised date reports again
- [x] T015 [P] [US1] [FR-006] [FR-007] [DR-005] Add failing `test_derivation.py::test_a_revision_cannot_buy_silence`, asserting the reason, the original date, the number of moves, and that nothing else about the entry changed
- [x] T016 [P] [US2] [FR-010] Add failing `test_derivation.py::test_both_directions_can_be_revised`
- [x] T017 [P] [FR-005] Add failing `test_derivation.py::test_a_dated_promise_is_no_longer_a_stalled_order`, with a positive control
- [x] T018 [P] [FR-012] Add failing `test_derivation.py::test_revised_promises_order_deterministically`
- [x] T019 [P] [DR-003] Add failing `test_derivation.py::test_one_rule_answers_the_date_in_force`
- [x] T020 [DR-006] Update the cause vocabulary expectation in `test_coverage.py`

## Phase 4: The Queue

- [x] T021 [FR-004] [FR-005] Read the date in force in `_commitment_exceptions` and in the undated-order class, through the one shared rule
- [x] T022 [FR-006] [FR-007] Add the `promise_was_revised` cause and the conditional causal values, so an unrevised promise's entry is byte-identical to today's
- [x] T023 [DR-006] Declare the cause in `packages/reality-core/src/reality/catalogs.py` and on both overdue classes in `packages/reality-core/config/operational_exception_catalog.yaml`, with authority and evidence
- [x] T024 [FR-006] Say in the guidance what a revised promise means, what the class still reports, and what it deliberately does not
- [x] T025 Create `specs/093-promises-can-be-revised/quickstart.md` and record the result of the three independent acceptance stories

## Phase 5: Surfaces and Catalogs

- [x] T026 [FR-011] Declare the operation in `packages/reality-core/config/command_catalog.yaml` with parameter descriptions, agent coverage and capability guidance
- [x] T027 [FR-011] Declare the operation and its tool in `packages/reality-core/config/tenant_isolation_catalog.yaml`
- [x] T028 [FR-011] Add the agent tool, the MCP schema and the endpoint
- [x] T029 [FR-011] Run the drift gates and confirm every catalog agrees

## Phase 6: Cross-References and Documentation

- [x] T030 [FR-006] Record the revision and the date in force in `docs/features/commitments.md`
- [x] T031 [P] Add the cause and what it means to `docs/features/operational_exceptions.md`, including the blind spot it leaves
- [x] T032 [P] Record the supplier acknowledgement in `docs/features/procure_to_pay.md`
- [x] T033 [P] Regenerate the catalog reference and run `npm run format` in `apps/docs`
- [x] T034 [P] Add the specification row to `docs/SPEC_COVERAGE_MATRIX.md`

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
| FR-001 | T006 | T011, T012 | Done |
| FR-002 | T006 | T011 | Done |
| FR-003 | T007 | T012 | Done |
| FR-004 | T014 | T021 | Done |
| FR-005 | T017 | T021 | Done |
| FR-006 | T015 | T022, T023, T024 | Done |
| FR-007 | T015 | T022 | Done |
| FR-008 | T008 | T012 | Done |
| FR-009 | T009 | T012 | Done |
| FR-010 | T016 | T012 | Done |
| FR-011 | T029 | T026, T027, T028 | Done |
| FR-012 | T018 | T021 | Done |
| FR-013 | T013 | — | Done |
| DR-001 | T903 | T011 | Done |
| DR-002 | T006 | T012 | Done |
| DR-003 | T019 | T012, T021 | Done |
| DR-004 | T010 | T012 | Done |
| DR-005 | T015 | T022 | Done |
| DR-006 | T020 | T023 | Done |
| DR-007 | T006 | T012 | Done |
