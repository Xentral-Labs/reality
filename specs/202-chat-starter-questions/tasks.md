# Tasks: Chat starter questions

## Phase 1: Specification and Design
- [x] T001 Review spec.md and plan.md; user-authorized scope, no open clarifications, Constitution PASS.
- [x] T002 Analyze spec.md, plan.md and tasks.md; see analysis.md.

## Phase 2: User Story 1
- [x] T003 [US1] [FR-001] [FR-002] [FR-003] [FR-004] Extend apps/web/scripts/unified-chat-composer-browser.mjs with starter acceptance; observe initial failure.
- [x] T004 [US1] [FR-001] [FR-002] [FR-003] Add starter buttons and draft/focus guards in apps/web/src/unified/ChatPage.tsx.
- [x] T005 [US1] [FR-004] Translate starter questions in apps/web/src/localization.tsx.

## Final Phase: Verification and Review
- [x] T006 Record behavior in docs/WEB_SPEC.md; run browser acceptance, make web-build and make spec-check; review diff and record evidence in verification.md.

## Dependencies and Implementation Strategy
T001 → T002 → T003 → T004 → T005 → T006. Single small story is the complete MVP. Translations can be prepared independently of the component after test planning; execute sequentially to preserve concurrent workspace edits.

## Requirement Coverage
| Requirement | Test | Implementation |
|---|---|---|
| FR-001 | T003 | T004 |
| FR-002 | T003 | T004 |
| FR-003 | T003 | T004 |
| FR-004 | T003 | T005 |
