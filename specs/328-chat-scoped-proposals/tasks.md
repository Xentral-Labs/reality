# Tasks

- [x] T001 Specify and approve scope (all).
- [x] T002 Plan, research, data model; Constitution Check PASS (all).
- [x] T003 Failing service/API tests in `packages/reality-core/tests/test_chat_scoped_proposals.py` (FR-001–FR-007, DR-001–DR-004).
- [x] T004 Migration `0115_chat_scoped_proposals.py` and `ChangeProposal.chat_session_id` (DR-001–DR-003).
- [x] T005 `CHAT_SESSION` context in `tools/application.py`; set in `send_chat_message`; user message sent time (FR-001, FR-002, FR-004).
- [x] T006 `chat_proposals`, `pending_proposals_elsewhere`, `proposal_anchor`; removal archives (FR-003, FR-004, FR-006, FR-007).
- [x] T007 `copilots_payload` returns session proposals, anchors, deciders, `pending_elsewhere` (FR-003–FR-006).
- [x] T008 Web: anchored proposals, settled decision line, elsewhere hint, translations; browser fixtures (FR-004–FR-006, FR-009).
- [x] T009 Docs: `chat.md`, `chat_sessions.md`, `DATA_MODEL.md`, data model reference, coverage matrix (all).
- [ ] T010 Verify scoped suites, catalog/index gates, web build/i18n, spec/lint; CI green (all).

Dependencies: T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010.
