---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: An Operation Nobody Declared

**Input**: [`spec.md`](./spec.md), [`plan.md`](./plan.md), [`checklists/`](./checklists/)
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and resulting repository artifacts MUST be
written in English.

## Format

`- [x] T001 [P?] [US1] [FR-001] Action with exact file path`

Every functional/domain requirement MUST appear in at least one test task and one
implementation or documentation task. Test tasks precede the code they prove.

## Sequencing Constraints

The established rules apply, and one is particular to this feature: **the gate is written before
anything is declared**, so its first run produces the fourteen names rather than a green tick.
A completeness gate that has never failed is not evidence of completeness.

## Phase 1: Specification and Design Gates

- [x] T001 Confirm the accepted scope decisions are recorded in `specs/094-every-command-is-declared/spec.md`
- [x] T002 Confirm every Constitution Check row is PASS and Complexity Tracking is empty in `specs/094-every-command-is-declared/plan.md`
- [x] T003 Complete the reviewer-owned domain review in `specs/094-every-command-is-declared/checklists/domain.md`
- [x] T004 Run `$speckit-analyze` and resolve every CRITICAL consistency or coverage finding
- [x] T005 Re-measure all three candidate populations and record the counts in the plan rather than describing them

## Phase 2: The Gate, Failing

- [x] T006 [US1] [FR-001] [FR-005] [FR-009] Add `test_application_catalog.py::test_every_reachable_mutation_is_declared_or_explained`, deriving its population from the tenant isolation catalog and the surface modules and defining no list of its own
- [x] T007 Run it and record the fourteen names it produces, so the gate is proven to fail before it is satisfied
- [x] T008 [P] [FR-002] [FR-003] [FR-004] [DR-003] Add `test_application_catalog.py::test_the_command_gate_fails_in_both_directions`, covering an empty reason, a service both declared and exempt, and an exemption naming a service outside the population — each with a positive control

## Phase 3: The Eight

- [x] T009 [P] [US2] [FR-006] Declare releasing a reservation in `packages/reality-core/config/command_catalog.yaml`
- [x] T010 [P] [US2] [FR-007] Declare updating a pricing group
- [x] T011 [P] [US2] [FR-008] Declare the six bulk master-data operations as related services of the single-record commands they belong to
- [x] T012 [FR-006] [FR-007] [FR-008] Add `test_application_catalog.py::test_the_eight_operations_the_gate_found_are_declared`
- [x] T013 [FR-001] Add the parameter descriptions the capability guidance requires for anything newly declared

## Phase 4: The Six

- [x] T014 [DR-002] Record the five chat session operations and the import worker step in the command catalog as explicitly not commands, one reason each
- [x] T015 [FR-001] Run the gate and confirm it passes for the right reason — every name accounted for, none silenced without a reason

## Phase 5: Documentation

- [x] T016 [DR-002] Record in `docs/features/operational_fields.md` what the command catalog now guarantees and what it deliberately does not
- [x] T017 [P] Regenerate the catalog reference and run `npm run format` in `apps/docs`
- [x] T018 [P] Add the specification row to `docs/SPEC_COVERAGE_MATRIX.md`, recording that this is the structural item Spec 091 named

## Final Phase: Cross-Cutting Review

- [x] T900 Run `make spec-check`
- [x] T901 Run `make lint` and the complete backend PostgreSQL suite in CI's invocation and ordering
- [x] T902 Run the `apps/docs` tests and format check
- [x] T903 [DR-001] Confirm no migration was added and no diff under `services/`
- [x] T904 Review the final diff against the Constitution and the review risks in `plan.md`
- [x] T905 Re-derive the feature number with `scripts/next_feature_number.py` immediately before opening the pull request, and take the number it gives

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001 | T006, T015 | T009, T010, T011, T013, T014 | Done |
| FR-002 | T008 | T014 | Done |
| FR-003 | T008 | T014 | Done |
| FR-004 | T008 | T014 | Done |
| FR-005 | T006, T007 | T006 | Done |
| FR-006 | T012 | T009 | Done |
| FR-007 | T012 | T010 | Done |
| FR-008 | T012 | T011 | Done |
| FR-009 | T006 | T006 | Done |
| FR-010 | T901 | — | Done |
| DR-001 | T903 | — | Done |
| DR-002 | T006 | T014, T016 | Done |
| DR-003 | T008 | T006 | Done |
| DR-004 | T901 | — | Done |
