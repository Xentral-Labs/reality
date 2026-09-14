---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: The Hold Nobody Lifted

**Input**: [`spec.md`](./spec.md), [`plan.md`](./plan.md), [`checklists/`](./checklists/)
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and resulting repository artifacts MUST be
written in English.

## Format

`- [x] T001 [P?] [US1] [FR-001] Action with exact file path`

Every functional/domain requirement MUST appear in at least one test task and one
implementation or documentation task. Test tasks precede the code they prove.

## Sequencing Constraints

The established rules apply. One is particular to this feature.

**The reachability check comes before the design**, not after it. Spec 091 found five shipped
classes whose clearing path nothing reached, and this is the check that would have caught them.

## Phase 1: Specification and Design Gates

- [x] T001 Confirm the accepted scope decisions are recorded in `specs/107-a-hold-nobody-lifted/spec.md`
- [x] T002 Confirm every Constitution Check row is PASS and that no Complexity Tracking exception is claimed in `specs/107-a-hold-nobody-lifted/plan.md`
- [x] T003 Complete the reviewer-owned domain review in `specs/107-a-hold-nobody-lifted/checklists/domain.md`
- [x] T004 Run `$speckit-analyze` and resolve every CRITICAL consistency or coverage finding
- [x] T005 [DR-006] Confirm from the command catalog that `release_commitment_hold` and `release_party_delivery_hold` are reachable from every adapter their commands declare, and record it in `plan.md`
- [x] T006 Confirm against the code that `exceptions.py` reads neither hold record, and that `_stale_promises` skips held promises with no expiry

## Phase 2: The Two Classes

- [x] T007 [P] [FR-001] [FR-004] [FR-006] [FR-009] [DR-004] Add failing `test_derivation.py::test_commitment_hold_unreleased`, covering the entry, a hold on a closed promise, and the entry clearing on release
- [x] T008 [P] [FR-001] [FR-005] [FR-007] [FR-008] [FR-009] Add failing `test_derivation.py::test_party_hold_unreleased`, covering the count rather than a sum, a hold blocking nothing, and the hold type
- [x] T009 [P] [FR-002] [FR-003] Add failing `test_derivation.py::test_a_hold_is_judged_by_this_company_s_own_rhythm`, including the floor and silence below the minimum
- [x] T010 [P] [DR-003] Add failing `test_derivation.py::test_each_hold_kind_learns_its_own_rhythm`
- [x] T011 [P] [FR-010] Add failing `test_derivation.py::test_a_hold_suppresses_nothing`
- [x] T012 [P] [DR-005] Add failing `test_derivation.py::test_holds_are_tenant_scoped`
- [x] T013 [FR-001] [DR-003] Add `_unreleased_hold_exceptions` and its two learned thresholds to `src/reality/services/exceptions.py`
- [x] T014 [DR-002] Add both class ids to `CLASS_ORDER`, `OPERATIONAL_EXCEPTION_CLASS_ORDER` and `DERIVATION_REGISTRY`
- [x] T015 [FR-004] [FR-005] [FR-008] Add both entries to `config/operational_exception_catalog.yaml`, with the severity argument and the clearing path in their guidance
- [x] T016 [FR-011] Run the complete backend suite and confirm nothing moved for a company that holds nothing
- [x] T017 Create `specs/107-a-hold-nobody-lifted/quickstart.md` and record the three independent acceptance stories

## Phase 3: Documentation

- [x] T018 [FR-008] Record both classes in `docs/features/operational_exceptions.md`, including why a forgotten hold is permanent
- [x] T019 [P] Record the class in `docs/features/commitment_holds.md`
- [x] T020 [P] Record the class in `docs/features/party_delivery_holds.md`
- [x] T021 [P] Regenerate the catalog reference and run `npm run format` in `apps/docs`
- [x] T022 [P] Add the specification row to `docs/SPEC_COVERAGE_MATRIX.md`

## Final Phase: Cross-Cutting Review

- [x] T900 Run `make spec-check`
- [x] T901 Run `make lint` and the complete backend PostgreSQL suite in CI's invocation and ordering
- [x] T902 Run the `apps/docs` tests and format check
- [x] T903 [DR-001] Confirm no migration and no new command were added
- [x] T904 Review the final diff against the Constitution and the review risks in `plan.md`
- [x] T904a Confirm the demo month's pinned queue is unchanged
- [x] T905 Re-derive the feature number with `scripts/next_feature_number.py` immediately before opening the pull request, and take the number it gives

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001 | T007, T008 | T013, T014 | Done |
| FR-002 | T009 | T013 | Done |
| FR-003 | T009 | T013 | Done |
| FR-004 | T007 | T013, T015 | Done |
| FR-005 | T008 | T013, T015 | Done |
| FR-006 | T007 | T013 | Done |
| FR-007 | T008 | T013 | Done |
| FR-008 | T008 | T015 | Done |
| FR-009 | T007, T008 | T013 | Done |
| FR-010 | T011 | — | Done |
| FR-011 | T016, T901 | — | Done |
| DR-001 | T903 | — | Done |
| DR-002 | T901 | T014 | Done |
| DR-003 | T010 | T013 | Done |
| DR-004 | T007 | T013 | Done |
| DR-005 | T012 | T013 | Done |
| DR-006 | T005 | T005 | Done |
