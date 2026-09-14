---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: A Fee Is a Charge, Not a Smaller Credit

**Input**: [`spec.md`](./spec.md), [`plan.md`](./plan.md), [`checklists/`](./checklists/)
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and resulting repository artifacts MUST be
written in English.

## Format

`- [x] T001 [P?] [US1] [FR-001] Action with exact file path`

Every functional/domain requirement MUST appear in at least one test task and one
implementation or documentation task. Test tasks precede the code they prove.

## Sequencing Constraints

One constraint is particular to this feature: **the measurement comes before the specification is
believed.** It did, and its output is in the plan. Nothing else here is allowed to assume the
derivation is wrong, because it is not.

## Phase 1: Specification and Design Gates

- [x] T001 Confirm the accepted scope decisions are recorded in `specs/095-a-fee-is-a-charge/spec.md`
- [x] T002 Confirm every Constitution Check row is PASS and Complexity Tracking is empty in `specs/095-a-fee-is-a-charge/plan.md`
- [x] T003 Complete the reviewer-owned domain review in `specs/095-a-fee-is-a-charge/checklists/domain.md`
- [x] T004 Run `$speckit-analyze` and resolve every CRITICAL consistency or coverage finding
- [x] T005 Confirm by measurement that the intended recording already clears the class, and record both numbers in the plan

## Phase 2: Pinning Both Recordings

- [x] T006 [US1] [FR-001] [FR-002] [FR-003] [DR-002] Add `test_derivation.py::test_a_restocking_fee_is_a_charge_not_a_smaller_credit`, asserting a full credit with a charge line clears the class, that the credit note total is still the reduced amount, and that a credit for fewer units reports the difference
- [x] T007 [FR-005] Confirm the test passes without touching any derivation

## Phase 3: The Guidance

- [x] T008 [FR-004] Add to `returned_not_credited` in `packages/reality-core/config/operational_exception_catalog.yaml` how a fee, a damage deduction or a write-off is recorded, and what a smaller credit quantity means instead
- [x] T009 [FR-004] Add `test_coverage.py::test_the_return_guidance_says_how_to_record_a_fee`, reading the guidance rather than checking it exists
- [x] T010 Create `specs/095-a-fee-is-a-charge/quickstart.md` and record the measurement and the two recordings

## Phase 4: Documentation

- [x] T011 [FR-004] Record the two recordings in `docs/features/operational_exceptions.md`
- [x] T012 [P] Regenerate the catalog reference and run `npm run format` in `apps/docs`
- [x] T013 [P] Add the specification row to `docs/SPEC_COVERAGE_MATRIX.md`, recording that this was a suspected defect and was not one

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
| FR-001 | T006 | — (already correct) | Done |
| FR-002 | T006 | — (already correct) | Done |
| FR-003 | T006 | — (already correct) | Done |
| FR-004 | T009 | T008, T011 | Done |
| FR-005 | T007, T903 | — | Done |
| DR-001 | T903 | — | Done |
| DR-002 | T006 | T006 | Done |
| DR-003 | T901 | — | Done |
