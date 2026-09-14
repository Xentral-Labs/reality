---
description: "Requirement-traceable command Action guidance tasks"
---

# Tasks: Command Action Guidance

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`  
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

## Phase 1: Specification and Design Gates

- [x] T001 Confirm approved scope and absence of clarification markers in `specs/051-command-action-guidance/spec.md`
- [x] T002 Confirm every Constitution Check row is PASS in `specs/051-command-action-guidance/plan.md`
- [x] T003 Run `$speckit-analyze` and resolve every CRITICAL finding across `specs/051-command-action-guidance/`

## Phase 2: Failing Proof

- [x] T004 [P] [US1] [FR-001] [FR-002] Add failing Action-description enrichment and missing-effect rejection tests in `packages/reality-core/tests/test_application_catalog.py`
- [x] T005 [P] [US2] [FR-001] [FR-006] Add failing application-reference description assertion in `packages/reality-core/tests/test_http_boundary.py`
- [x] T006 [P] [US1] [US2] [FR-003] [FR-004] [FR-005] [FR-006] [FR-007] [FR-008] Add failing launcher/form guidance contracts in `apps/web/scripts/workspace-actions-contract.test.mjs`
- [x] T007 Run focused tests and record the intended failures in `specs/051-command-action-guidance/quickstart.md`

## Phase 3: Catalog and API Contract

- [x] T008 [US1] [FR-001] [FR-002] Derive and validate Action descriptions in `packages/reality-core/src/reality/catalogs.py`
- [x] T009 [US2] [FR-001] Add the required Action description type in `apps/web/src/api.ts`
- [x] T010 [US1] [US2] [FR-001] [FR-002] Run catalog and HTTP tests and record results in `specs/051-command-action-guidance/quickstart.md`

## Phase 4: Product Web Guidance

- [x] T011 [US1] [FR-003] [FR-004] [FR-005] Render and search descriptions with separate prerequisites in `apps/web/src/App.tsx`
- [x] T012 [US2] [FR-006] [FR-007] [FR-008] Pass the description through the shared Action form without changing confirmation in `apps/web/src/App.tsx`
- [x] T013 [P] [US1] [US2] [FR-009] Add `Requires` and classified effect translations in `apps/web/src/localization.tsx`
- [x] T014 [P] [US1] [US2] Add responsive guidance hierarchy in `apps/web/src/tailwind.css`
- [x] T015 [US1] [US2] [FR-003] [FR-004] [FR-005] [FR-006] [FR-007] [FR-008] [FR-009] Run frontend contracts, i18n audit, and build and record results in `specs/051-command-action-guidance/quickstart.md`

## Final Phase: Verification and Review

- [ ] T016 [SC-001] [SC-002] [SC-003] [SC-004] Run desktop/mobile visual acceptance in all affected launcher/form states and record results in `specs/051-command-action-guidance/quickstart.md`
- [ ] T017 [SC-005] Run `make spec-check`, `make lint`, and the complete required PostgreSQL suite and record results in `specs/051-command-action-guidance/quickstart.md`
- [x] T018 Audit the final diff against the Constitution, user-owned concurrent changes, no-schema claim, and rollback plan

## Dependencies

- T001-T003 gate implementation.
- T004-T007 precede the implementation they prove.
- T008-T010 precede Web consumption.
- T011-T014 are sequential where they share files; verification follows all implementation.

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) |
|---|---|---|
| FR-001-FR-002 | T004-T005 | T008-T010 |
| FR-003-FR-008 | T006 | T011-T012, T015 |
| FR-009 | T006, T015 | T013-T015 |
| FR-010 | T017-T018 | T018 |
| SC-001-SC-005 | T015-T017 | T016-T018 |
