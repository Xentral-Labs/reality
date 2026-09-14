---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: Operator Guidance in the Exception Catalog

**Input**: [`spec.md`](./spec.md), [`plan.md`](./plan.md), [`checklists/`](./checklists/)
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and resulting repository artifacts MUST be
written in English.

## Format

`- [ ] T001 [P?] [US1] [FR-001] Action with exact file path`

Every functional/domain requirement MUST appear in at least one test task and one
implementation or documentation task. Test tasks precede the code they prove.

## Sequencing Constraints

The catalog gate refuses a class that fails validation, so requiring the new fields and
writing them must land together. Unlike a new class this is not an ordering hazard but a
single edit: the validator and the eight entries change in one step, or every catalog load
raises.

## Phase 1: Specification and Design Gates

- [ ] T001 Confirm the three accepted scope decisions are recorded and no clarification marker remains in `specs/071-catalog-operator-guidance/spec.md`
- [ ] T002 Confirm every Constitution Check row is PASS and Complexity Tracking is empty in `specs/071-catalog-operator-guidance/plan.md`
- [ ] T003 Complete the reviewer-owned domain review in `specs/071-catalog-operator-guidance/checklists/domain.md`
- [ ] T004 Run `$speckit-analyze` and resolve every CRITICAL consistency or coverage finding

## Phase 2: Failing Proof

- [ ] T005 [P] [US2] [FR-001] [DR-001] Add failing `tests/operational_exceptions/test_coverage.py::test_every_class_carries_operator_guidance` asserting all eight classes carry a non-empty description, owner and clearing path
- [ ] T006 [P] [US2] [FR-002] [DR-002] [DR-003] Add failing `test_coverage.py::test_catalog_rejects_missing_guidance` covering each field absent, empty and whitespace only, and asserting that causes are still accepted without guidance
- [ ] T007 [P] [US1] [FR-005] [DR-004] Add failing `test_coverage.py::test_generated_reference_carries_guidance` asserting both editions of the generated page render every class's description, owner and clearing path

## Phase 3: The Fields

- [ ] T008 [US2] [FR-001] [FR-002] Require `description`, `owner` and `clears_through` in `packages/reality-core/src/reality/catalogs.py` and write them for all eight classes in `packages/reality-core/config/operational_exception_catalog.yaml`, in one step
- [ ] T009 [US1] [FR-003] [FR-004] Review each description against its derivation so it states the business condition rather than the class name, and each clearing path against what actually removes the entry — `unexplained_movement` says explicitly that nothing does
- [ ] T010 [US1] [FR-009] Confirm the exception derivation and explanation suites pass untouched, proving the queue is unchanged

## Phase 4: The Generated Reference

- [ ] T011 [US1] [FR-005] Render the description, owner and clearing path for every class in `apps/docs/scripts/generate-catalog-reference.py`, keeping the guidance English on both editions
- [ ] T012 [US1] Regenerate `apps/docs/content/catalogs/exceptions.md` and `apps/docs/content/de/catalogs/exceptions.md`, then run `npm run format` in `apps/docs` — without the formatting pass every catalog page shows a whitespace-only diff

## Phase 5: Retire the Hand-Written Tables

- [ ] T013 [US1] [FR-007] Replace the per-class table in section 34 of `apps/docs/content/concepts/business-reality-guide/09-exceptions-and-approvals.md` with a reference to the generated catalog, keeping section 33 and the surrounding narrative
- [ ] T014 [US1] [FR-008] Remove the "Clears through" column from `docs/features/operational_exceptions.md`, keeping the class, cause and authority mapping
- [ ] T015 [P] [FR-006] Search the documentation for any other hand-maintained per-class list and record the result
- [ ] T016 [P] Add the specification row and the new evidence rows to `docs/SPEC_COVERAGE_MATRIX.md`

## Final Phase: Cross-Cutting Review

- [ ] T900 Run `make spec-check` and confirm the traceability tables match the delivered tests
- [ ] T901 Run `make lint` and the complete backend PostgreSQL suite
- [ ] T902 Confirm `apps/web` and `provider-site` are unchanged against `origin/main`
- [ ] T903 Confirm no migration was added and `services/exceptions.py` is untouched
- [ ] T904 Read the generated page as an operator would and confirm it answers what the condition is, who owns it and what clears it, for all eight classes

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001 | T005 | T008 | Pending |
| FR-002 | T006 | T008 | Pending |
| FR-003 | T009 | T008 | Pending |
| FR-004 | T009 | T008 | Pending |
| FR-005 | T007 | T011, T012 | Pending |
| FR-006 | T015 | T013, T014 | Pending |
| FR-007 | T015 | T013 | Pending |
| FR-008 | T015 | T014 | Pending |
| FR-009 | T010 | T008 | Pending |
| DR-001 | T005 | T008 | Pending |
| DR-002 | T006 | T008 | Pending |
| DR-003 | T006 | T008 | Pending |
| DR-004 | T007 | T011 | Pending |
