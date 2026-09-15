---
description: "Requirement-traceable empty Chat Session removal tasks"
---

# Tasks: Delete Empty Chat Sessions

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/http-api.md`
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

## Phase 1: Specification and Design Gates

- [x] T001 Confirm requirements review and close clarification markers in `specs/204-delete-empty-chat/spec.md`
- [x] T002 Confirm all Constitution Check rows are PASS in `specs/204-delete-empty-chat/plan.md`
- [x] T003 Run `$speckit-analyze` and resolve all CRITICAL findings across `specs/204-delete-empty-chat/`

## Phase 2: Failing Proof

- [x] T004 [US1] [FR-001] [FR-002] [FR-005] Add failing empty-delete and non-empty-archive API stories in `packages/reality-core/tests/test_master_data_api.py`
- [x] T005 [P] [US1] [FR-006] [FR-007] [DR-001] Add proposal-invariance and cross-tenant assertions in `packages/reality-core/tests/test_master_data_api.py`
- [x] T006 [P] [US2] [FR-003] Add failing session message-count projection assertions in `packages/reality-core/tests/test_master_data_api.py`
- [x] T007 [P] [US2] [FR-004] Add failing delete/archive wording proof in `apps/web/scripts/chat-archive-contract.test.mjs`

## Phase 3: User Story 1 - Remove an abandoned empty conversation (P1)

- [x] T008 [US1] [FR-001] [FR-002] [FR-005] [FR-006] [FR-007] [DR-001] [DR-002] [DR-004] Implement tenant-scoped conditional removal in `packages/reality-core/src/reality/services/core.py`
- [x] T009 [US1] [FR-001] [FR-002] [DR-002] Keep the existing removal transport delegated to the shared service in `packages/reality-core/src/reality/web/api.py`
- [x] T010 [US1] Run the US1 independent acceptance proof from `specs/204-delete-empty-chat/quickstart.md`

## Phase 4: User Story 2 - Understand the consequence before confirming (P2)

- [x] T011 [US2] [FR-003] Add batch tenant-scoped message counts to session projection in `packages/reality-core/src/reality/services/core.py` and `packages/reality-core/src/reality/web/api.py`
- [x] T012 [P] [US2] [FR-003] Type `message_count` in `apps/web/src/api.ts`
- [x] T013 [US2] [FR-004] Render `Delete chat` with permanent confirmation for empty sessions and preserve archive wording otherwise in `apps/web/src/unified/ChatPage.tsx`
- [x] T014 [P] [US2] [FR-004] Add complete translations in `apps/web/src/localization.tsx`
- [x] T015 [US2] Run the US2 independent acceptance proof from `specs/204-delete-empty-chat/quickstart.md`

## Final Phase: Cross-Cutting Review

- [x] T900 [DR-003] Run the Spec Policy check and verify no source, evidence, Reality schema, or migration changed
- [x] T901 Run focused backend PostgreSQL/API tests and required backend quality checks
- [x] T902 Run Web contract tests, formatting, i18n audit, and production build
- [x] T903 Confirm migration and data-backfill impact is none in `specs/204-delete-empty-chat/plan.md`
- [x] T904 Review final diff against the Constitution and FR-001–FR-007/DR-001–DR-004
- [x] T905 Update `specs/204-delete-empty-chat/tasks.md` only after every required check is green

## Dependencies

- Phase 1 blocks all implementation.
- Phase 2 failing proofs block their corresponding implementation tasks.
- US1 establishes authoritative removal semantics before US2 presents those semantics.
- T011 blocks T012 and T013; T013 and T014 jointly deliver the UI wording.

## Parallel Opportunities

- T005, T006, and T007 can be authored in parallel after specification gates.
- T012 and T014 touch independent frontend files after the projection contract is fixed.

## Implementation Strategy

Deliver US1 first as the safe minimum: the backend stops polluting archives even for existing
callers. Then deliver US2 so the Web UI describes the server-owned consequence before confirmation.

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status   |
| ----------- | ------------ | ---------------------- | -------- |
| FR-001      | T004         | T008–T009              | Verified |
| FR-002      | T004         | T008–T009              | Verified |
| FR-003      | T006         | T011–T012              | Verified |
| FR-004      | T007         | T013–T014              | Verified |
| FR-005      | T004         | T008                   | Verified |
| FR-006      | T005         | T008                   | Verified |
| FR-007      | T005         | T008                   | Verified |
| DR-001      | T005         | T008, T011             | Verified |
| DR-002      | T004         | T008–T009              | Verified |
| DR-003      | T900         | T900                   | Verified |
| DR-004      | T004         | T008                   | Verified |
