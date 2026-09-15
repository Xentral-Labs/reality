# Tasks
## Foundation
- [x] T001 Specify/review scope and Constitution Check in specs/195-storyline-free-chat/.
## US1 — Free chat
- [x] T002 Add behavioral handoff/send/reload checks in apps/web/scripts/storyline-browser.mjs (FR-001–002, FR-005).
## US2 — Evidence
- [x] T003 Add exact association/isolation/retention tests in packages/reality-core/tests/test_storyline_chat.py (FR-003–004, DR-001).
- [x] T004 Implement scoped collection in packages/reality-core/src/reality/storyline/recorder.py and shared core.send_chat_message (FR-003).
- [x] T005 Implement service/API evidence read in services/storyline.py and web/storyline_api.py (FR-003–004, DR-001).
## Integration
- [x] T006 Embed shared ChatPage and evidence renderer in apps/web/src/unified/StorylinePage.tsx, StorylineNarrator.tsx, ChatPage.tsx, StorylineChatEvidence.tsx and apps/web/src/api.ts (FR-001–005).
- [x] T007 Update apps/web/src/localization.tsx and docs/features/chat.md, docs/WEB_SPEC.md (FR-005).
- [x] T008 Run focused/full tests, browser proof, lint, spec and web/docs gates; record verification.md (all).

Dependencies: T001 → tests T002/T003 → T004 → T005 → T006 → T007 → T008.
Independent test preparations can be batched; no agents needed. Deliver both stories
as one coherent increment because free chat must carry truthful evidence.
