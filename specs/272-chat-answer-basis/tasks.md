---
description: "Requirement-traceable Compact Chat Answer Basis implementation tasks"
---

# Tasks: Compact Chat Answer Basis

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

## Phase 1: Specification and Design Gates

- [x] T001 Confirm requirements review, assumptions, non-goals, and zero clarification markers in `specs/272-chat-answer-basis/spec.md`
- [x] T002 Confirm every Constitution Check row is PASS and post-design review remains PASS in `specs/272-chat-answer-basis/plan.md`
- [x] T003 Run Spec Kit analysis over `specs/272-chat-answer-basis/spec.md`, `plan.md`, and `tasks.md` and resolve every CRITICAL finding

## Phase 2: Failing Proof

- [x] T004 [P] [US1] [FR-001] [FR-002] [FR-004] [FR-012] Add failing ordinary-company capture, bounded snapshot, reload, historical-null, and persistence-failure tests in `packages/reality-core/tests/test_storyline_chat.py`
- [x] T005 [P] [US1] [FR-003] [FR-009] Add failing tenant/message authorization and existing Storyline trace compatibility API tests in `packages/reality-core/tests/test_storyline_chat.py`
- [x] T006 [P] [US1] [FR-005] [FR-006] [FR-007] [FR-008] [FR-010] [FR-011] Add failing compact basis/hidden-empty/localized markup contract tests in `apps/web/scripts/chat-answer-basis.test.mjs`

## Phase 3: User Story 1 — Understand an answer immediately (P1)

- [x] T007 [US1] [FR-001] [FR-002] [FR-004] Add nullable bounded `ChatMessage.answer_basis` mapping and migration in `packages/reality-core/src/reality/db/core.py` and `packages/reality-core/migrations/versions/0097_chat_answer_basis.py`
- [x] T008 [US1] [FR-001] [FR-002] [FR-004] Capture successful canonical reads for all chat replies without changing existing Storyline trace behavior in `packages/reality-core/src/reality/storyline/recorder.py`
- [x] T009 [US1] [FR-003] [FR-005] [FR-006] [FR-007] Present allowlisted fulfillment support rows and read message basis before optional Storyline trace in `packages/reality-core/src/reality/services/storyline.py`
- [x] T010 [US1] [FR-003] Expose the additive basis response through `packages/reality-core/src/reality/web/storyline_api.py`
- [x] T011 [US1] [FR-005] [FR-006] [FR-007] [FR-008] Update types and render the compact business-first disclosure in `apps/web/src/api.ts` and `apps/web/src/unified/StorylineChatEvidence.tsx`
- [x] T012 [US1] [FR-011] Add complete English/German/Dutch/Spanish answer-basis copy in `apps/web/src/localization.tsx`

## Phase 4: User Story 2 — Distinguish evidence from derivation (P1)

- [x] T013 [US2] [FR-005] [FR-010] Verify returned quantities remain recorded values and derived rows are explicitly labeled without business writes in `packages/reality-core/tests/test_storyline_chat.py`
- [x] T014 [US2] [FR-005] [FR-010] Render recorded and derived row roles distinctly without browser-side calculation in `apps/web/src/unified/StorylineChatEvidence.tsx`

## Phase 5: User Story 3 — Avoid false or empty explanations (P2)

- [x] T015 [US3] [FR-004] [FR-008] [FR-012] Verify old, no-read, and failed-capture replies return an unavailable basis while remaining readable in `packages/reality-core/tests/test_storyline_chat.py`
- [x] T016 [US3] [FR-008] [FR-012] Hide the entire disclosure unless basis or eligible legacy trace exists in `apps/web/src/unified/StorylineChatEvidence.tsx`

## Final Phase: Cross-Cutting Review

- [x] T017 [P] [FR-013] Update the durable chat explanation contract in `docs/WEB_SPEC.md`
- [x] T018 Run focused PostgreSQL tests in `packages/reality-core/tests/test_storyline_trace.py` and `packages/reality-core/tests/test_storyline_chat.py`
- [x] T019 Run `apps/web/scripts/chat-answer-basis.test.mjs`, frontend localization audit, formatting, and build
- [ ] T020 Run `make spec-check`, `make lint`, the complete required backend suite, and `make web-build`
- [x] T021 Review migration upgrade/downgrade, tenant scope, bounded JSON, unchanged user worktree files, and final diff against `specs/272-chat-answer-basis/spec.md`
- [x] T022 Record verification evidence and local walkthrough result in `specs/272-chat-answer-basis/verification.md`

## Dependencies

- Phase 1 gates all implementation; T003 must report no CRITICAL findings.
- Phase 2 tests precede T007–T016 and may run in parallel because they edit distinct test surfaces.
- T007 precedes T008; T008 precedes T009; T009 precedes T010–T012.
- User Story 2 extends the independently usable User Story 1 slice.
- User Story 3 depends on the additive response contract from User Story 1.
- Final documentation and verification follow green focused checks.

## Parallel Example

After Phase 1, T004, T005, and T006 can proceed independently. After the backend response shape is stable, T012 and T017 can proceed alongside frontend rendering work.

## Requirement Coverage

| Requirement | Test task(s) | Implementation/documentation task(s) | Status |
|---|---|---|---|
| FR-001 | T004 | T007-T008 | Verified |
| FR-002 | T004 | T007-T008 | Verified |
| FR-003 | T005 | T009-T010 | Verified |
| FR-004 | T004, T015 | T007-T008 | Verified |
| FR-005 | T006, T013 | T009, T011, T014 | Verified |
| FR-006 | T006 | T009, T011 | Verified |
| FR-007 | T006 | T009, T011 | Verified |
| FR-008 | T006, T015 | T011, T016 | Verified |
| FR-009 | T005 | T008-T010 | Verified |
| FR-010 | T006, T013 | T009, T014 | Verified |
| FR-011 | T006, T019 | T012 | Verified |
| FR-012 | T004, T015 | T016 | Verified |
| FR-013 | T020 | T017 | Implemented; full-suite gate open |

## Implementation Strategy

The MVP is User Story 1: persist exact ordinary-company read support and display a compact business basis. User Story 2 makes authority boundaries visually explicit. User Story 3 removes misleading empty explanations for historical and unsupported replies.
