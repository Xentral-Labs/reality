# Tasks: Business-readable Activity

## Phase 1: Specification and Gates

- [x] T001 Capture approved scope and requirements in `specs/070-activity-business-language/spec.md`
- [x] T002 Pass the Constitution Check in `specs/070-activity-business-language/plan.md`
- [x] T003 Map requirements to executable tasks in `specs/070-activity-business-language/tasks.md`

## Phase 2: Failing Proof

- [x] T004 [US1] Add fixed Activity navigation contracts in `apps/web/scripts/workspace-actions-contract.test.mjs`
- [x] T005 [US2] Add business-readable timeline service/API proof in `packages/reality-core/tests/test_master_data_api.py`
- [x] T006 [US2] Add business-first Activity rendering contracts in `apps/web/scripts/workspace-actions-contract.test.mjs`

## Phase 3: Implementation

- [x] T007 [US1] Move Activity into primary navigation and exclude it from contextual Views in `apps/web/src/App.tsx`
- [x] T008 [US2] Produce tenant-scoped business display context in `packages/reality-core/src/reality/services/core.py`
- [x] T009 [US2] Extend types and render business-first rows with disclosed traceability in `apps/web/src/api.ts` and `apps/web/src/App.tsx`
- [x] T010 [US2] Add presentation and translations in `apps/web/src/styles.css` and `apps/web/src/localization.tsx`
- [x] T011 Update the durable Activity contract in `docs/WEB_SPEC.md`

## Phase 4: Verification

- [x] T012 Run focused backend/frontend tests, Web build, localization audit, spec check, and diff review

## Dependencies

US1 and US2 are independently testable after Phase 1. T004 precedes T007; T005-T006 precede T008-T010. T011 and T012 follow both stories.
