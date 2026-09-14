# Tasks: Copilot Decision Queue and Chat Archiving

## Phase 1: Specification and Design Gates

- [x] T001 Record approved scope and acceptance behavior in `specs/040-copilot-decision-queue/spec.md`
- [x] T002 Pass the Constitution Check in `specs/040-copilot-decision-queue/plan.md`
- [x] T003 Analyze requirement, plan, task, and contract consistency

## Phase 2: Failing Proof

- [x] T004 [P] [US1] Add decision-list and Home activity regressions in `packages/reality-core/tests/test_master_data_api.py`
- [x] T005 [P] [US2] Add archive, restore, retention, and tenant regressions in `packages/reality-core/tests/test_master_data_api.py`
- [x] T006 [P] [US1] Add decision tabs and empty-Copilot regressions in `apps/web/scripts/ux-support-trace-contract.test.mjs`

## Phase 3: User Story 1 — Central Decision Queue

- [x] T007 [US1] Add tenant-scoped proposal listing service and endpoint in `packages/reality-core/src/reality/services/core.py` and `packages/reality-core/src/reality/web/api.py`
- [x] T008 [US1] Add typed decision APIs and Exceptions tabs in `apps/web/src/api.ts` and `apps/web/src/App.tsx`
- [x] T009 [US1] Correct Home activity and empty-Copilot proposal visibility in `packages/reality-core/src/reality/web/api.py` and `apps/web/src/App.tsx`

## Phase 4: User Story 2 — Archive Conversations

- [x] T010 [US2] Add ChatSession archive state and migration in `packages/reality-core/src/reality/db/core.py` and `packages/reality-core/migrations/versions/0031_chat_session_archiving.py`
- [x] T011 [US2] Implement tenant-scoped archive/restore/list services and endpoints in `packages/reality-core/src/reality/services/core.py` and `packages/reality-core/src/reality/web/api.py`
- [x] T012 [US2] Replace delete interaction with active/archive/restore UI in `apps/web/src/api.ts` and `apps/web/src/App.tsx`

## Final Phase: Verification and Documentation

- [x] T013 Update `docs/WEB_SPEC.md`, `docs/features/chat.md`, and `docs/DATA_MODEL.md`
- [x] T014 Run focused backend and Web tests, migration checks, lint, spec-check, Web build, and i18n audit
- [x] T015 Review tenant boundaries, proposal invariance, schema scope, and final diff

## Dependencies

T004–T006 precede implementation. T010 precedes T011–T012. US1 and the archive UI are
independently testable; final verification follows both.

## Requirement Coverage

| Requirements | Tests | Implementation |
|---|---|---|
| FR-001–FR-004, FR-009 | T004, T006 | T007–T008 |
| FR-005–FR-007 | T005 | T010–T012 |
| FR-008, FR-010 | T004, T006 | T009 |
| DR-001–DR-004 | T004–T006, T015 | T007–T13 |

## Implementation Strategy

Deliver the central pending queue and correct Home first, then add reversible Chat archiving.
