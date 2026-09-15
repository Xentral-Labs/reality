# Tasks: Chat response latency

## Setup and foundation
- [x] T001 Review accepted scope and requirements in specs/206-chat-response-latency/spec.md; record baseline/latest main and Constitution PASS in plan.md.
- [x] T002 Review protocol, disconnect, permission and test coverage in specs/206-chat-response-latency/research.md and contracts/stream.md; analyze all requirements before implementation.

## US3 — bounded inventory work (FR-006, DR-001–002, SC-003)
- [x] T003 [US3] Add parity, cross-tenant and 1-to-20-item query-count tests in packages/reality-core/tests/test_chat_latency.py; observe scaling failure.
- [x] T004 [US3] Batch inventory reads in packages/reality-core/src/reality/services/core.py through current commitment terms and tenant-scoped reads.

## US2 — provider efficiency (FR-003–005, FR-007, DR-001–002)
- [x] T005 [US2] Add cache, compact lossless results, permissions and long-history tests in packages/reality-core/tests/test_chat_latency.py and test_chat_streaming.py.
- [x] T006 [US2] Bound history in packages/reality-core/src/reality/services/core.py; cache static prefixes/build schemas once/compact results and redact timings in agent/mcp_chat.py.

## US1 — incremental answers (FR-001–003, DR-002–003, SC-001)
- [x] T007 [US1] Add fragmented SSE, tool assembly, truncation and error tests in packages/reality-core/tests/test_chat_streaming.py.
- [x] T008 [US1] Implement callback/SSE provider handling in packages/reality-core/src/reality/agent/streaming.py and agent/mcp_chat.py; thread callback through services/core.py without changing recorder/confirmation flow.
- [x] T009 [US1] Add API preflight/stream/failure tests in packages/reality-core/tests/test_chat_streaming.py; implement worker-owned session and stream transport in web/chat_stream.py and web/api.py.
- [x] T010 [US1] Add executable decoder tests and delayed browser proof in apps/web/scripts/chat-stream.test.mjs and chat-stream-browser.mjs before frontend changes.
- [x] T011 [US1] Implement decoder in apps/web/src/chatStream.ts, streaming API option in api.ts and provisional/final reconciliation in unified/ChatPage.tsx.

## Verification and review
- [x] T012 Run targeted and full required checks; generate catalog docs; update docs/features/chat.md and docs/WEB_SPEC.md; record exact evidence in specs/206-chat-response-latency/verification.md (SC-002).
- [x] T013 Repeat measured questions with first text/cache/round/tool timings, review final diff and document limitations in specs/206-chat-response-latency/verification.md (SC-004).

## Dependencies and implementation strategy
T001–T002 gate all code. Tests precede their implementation. US3 then US2 then US1 respects domain/services before adapters and avoids shared-file races. Provider research can run independently; implementation is sequential. MVP is US1 with US2 provider support; complete all accepted tasks before delivery. No parallel code edits to core.py or API/UI files.
