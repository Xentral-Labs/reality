---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: [FEATURE NAME]

**Input**: `spec.md`, `plan.md`, and applicable supporting artifacts
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and resulting repository artifacts MUST be
written in English.

## Format

`- [ ] T001 [P?] [US1] [FR-001] Action with exact file path`

Every functional/domain requirement MUST appear in at least one test task and one
implementation or documentation task. Test tasks precede the code they prove.

## Phase 1: Specification and Design Gates

- [ ] T001 Confirm requirements review and close clarification markers in `spec.md`
- [ ] T002 Confirm all Constitution Check rows are PASS in `plan.md`
- [ ] T003 Run `$speckit-analyze` and resolve all CRITICAL findings

## Phase 2: Failing Proof

- [ ] T004 [US1] [FR-001] Add or update failing unit/service/story test in [exact path]
- [ ] T005 [US1] [DR-001] Add tenant and provenance assertions in [exact path]

## Phase 3: User Story 1 (P1)

- [ ] T006 [US1] [FR-001] Implement domain/service behavior in [exact path]
- [ ] T007 [US1] [FR-001] Expose through shared tool and required adapters in [exact paths]
- [ ] T008 [US1] [DR-001] Add Inspect/explanation trace in [exact path or N/A]
- [ ] T009 [US1] Run the independent acceptance story and record result in `quickstart.md`

[Add one independently testable phase per additional user story.]

## Final Phase: Cross-Cutting Review

- [ ] T900 Run spec/traceability audit
- [ ] T901 Run Ruff and complete backend PostgreSQL suite
- [ ] T902 Run frontend build, i18n audit, and applicable UI tests
- [ ] T903 Review migration chain and rollback when schema changed
- [ ] T904 Review final diff against Constitution and all FR/DR requirements
- [ ] T905 Update docs and status checklists only after required checks are green

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001 | T004 | T006-T007 | Pending |
