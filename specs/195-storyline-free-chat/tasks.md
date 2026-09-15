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

- [x] T009 Restore post-send focus (FR-006), verify browser/web gates, update PR and 8080.

- [x] T010 Add/test direct library Free Play entry (FR-007); web/browser gates, PR and 8080.

- [x] T011 FR-008/009: standalone entry/evidence service regressions, implement shared
  setup and explicit trace eligibility, add independent UI and remove card actions;
  verify full gates, update PR scope and localhost preview. Supersedes T010's UI.

- [x] T012 [US1] [FR-008, FR-004] Add failing browser proofs for existing-company
  selection, default, read-only opening, reload and unavailable evidence; implement
  chooser and route state, localize, verify web/browser and update preview/PR.

- [x] T013 [FR-007] Remove narrator Sandbox chat shortcut, label/style Back to
  selection, update contract/browser regression, verify web/browser/spec and preview.

- [x] T014 [FR-007] Remove Free Play sidebar entry; retain tile, highlight Storyline
  on Free Play, test selection navigation, verify and update local preview/PR.

- [x] T015 [FR-010] Strengthen chat pending status, localize and verify pending/settled
  lifecycle and reduced motion; update web preview and PR.

- [x] T016 [FR-011] Restyle chat turns, add geometry/theme browser checks, verify
  build/browser and update preview/PR.

- [x] T017 [FR-012] Compact allowance disclosure, preserve exhaustion, verify browser
  and web build, update preview/PR.

- [x] T018 [FR-012] Move allowance into header popover, add settings usage view,
  preserve exhaustion, verify browser/build and update local preview/PR.

- [x] T019 [FR-013] Bound Free Play viewport/flex layout, add long-history scroll
  regression, verify build/browser and update preview/PR.
