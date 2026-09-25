---
description: "Requirement-traceable Chat agent decision tasks"
---

# Tasks: Chat Agent Decisions

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/chat-decision.md`, `quickstart.md`
**Gate**: Constitution Check passed, owner approved scope, no clarification marker

## Phase 1: Specification and Design Gates

- [x] T001 Confirm owner requirements approval and close clarification markers in `specs/274-chat-agent-decisions/spec.md`
- [x] T002 Confirm every Constitution Check row is PASS in `specs/274-chat-agent-decisions/plan.md`
- [x] T003 Generate reviewer-owned security requirements checklist in `specs/274-chat-agent-decisions/checklists/security.md`
- [x] T004 Run `$speckit-analyze` and resolve every CRITICAL finding across `specs/274-chat-agent-decisions/spec.md`, `plan.md`, and `tasks.md`

## Phase 2: Foundational Failing Proof and Persistence

- [x] T005 [P] [US2] [FR-006] [DR-003] Add Chat/person/MCP/unknown attribution and tenant-isolation cases in `packages/reality-core/tests/test_decision_attribution.py`
- [x] T006 [P] [US2] [FR-006] [DR-005] Add upgrade/downgrade and closed-channel constraint cases in `packages/reality-core/tests/test_migrations.py`
- [x] T007 [US2] [FR-006] [DR-003] Add nullable checked Chat settlement channel in `packages/reality-core/src/reality/db/core.py` and `packages/reality-core/migrations/versions/0098_chat_agent_decisions.py`
- [x] T008 [US2] [FR-006] [DR-003] Carry server-observed settlement channel through decision claim, rejection, restoration and replay in `packages/reality-core/src/reality/tools/application.py` and `packages/reality-core/src/reality/mcp/catalog.py`
- [x] T009 [US2] [FR-006] [DR-003] Return distinct `chat_agent` attribution from `packages/reality-core/src/reality/services/decision_attribution.py`

## Phase 3: User Story 1 — Prepare and Confirm in Chat (P1)

**Independent criterion**: An ordinary Chat turn proposes an exact Party without effect and later confirms the same opaque proposal once, while prepare-only remains pending.

- [x] T010 [P] [US1] [FR-001] [FR-003] [FR-012] Add provider-schema and two-round propose/confirm tests in `packages/reality-core/tests/test_mcp_chat.py` and `packages/reality-core/tests/test_chat_scope_security.py`
- [x] T011 [P] [US1] [FR-002] [FR-007] [FR-010] [DR-001] Extend PostgreSQL proposal-before-effect, confirmation, replay and receipt proof in `packages/reality-core/tests/test_application_tools.py`
- [x] T012 [US1] [FR-001] [FR-003] [FR-012] Offer read/propose/confirm to both ordinary provider adapters while preserving read-only mode in `packages/reality-core/src/reality/agent/mcp_chat.py`
- [x] T013 [US1] [FR-002] [FR-003] [FR-004] [FR-010] Replace human-only prompt language with exact decision-first agent guidance in `packages/reality-core/src/reality/agent/mcp_chat.py`
- [x] T014 [US1] [FR-003] [FR-004] Correct generic approval/rejection schemas and errors without weakening operation-specific owner rules in `packages/reality-core/src/reality/mcp/catalog.py` and `packages/reality-core/config/command_catalog.yaml`
- [x] T015 [US1] [FR-002] [FR-003] [FR-007] [DR-001] Run the independent proposal/confirmation story and record evidence in `specs/274-chat-agent-decisions/quickstart.md`

## Phase 4: User Story 2 — Truthful Controlled Attribution (P1)

**Independent criterion**: Equivalent decisions settled through Chat, Web and MCP read respectively as Chat agent, person and token; injected content grants nothing.

- [x] T016 [P] [US2] [FR-005] [FR-012] Replace blanket-confirmation attack expectations with authority-preserving injected-content cases for both providers in `packages/reality-core/tests/test_chat_scope_security.py`
- [x] T017 [P] [US2] [FR-011] Add ordered propose/decide correlation and event-range proof in `packages/reality-core/tests/test_engine_room_channels.py`
- [x] T018 [US2] [FR-005] [FR-006] [FR-011] Set Chat settlement context only inside the server-owned Chat tool boundary in `packages/reality-core/src/reality/agent/mcp_chat.py` and `packages/reality-core/src/reality/mcp/catalog.py`
- [x] T019 [US2] [FR-006] [DR-003] Update durable Chat and decision attribution contracts in `docs/features/chat.md` and `specs/014-agent-interaction/spec.md`
- [x] T020 [US2] [FR-006] [FR-011] Run the three-mode attribution and interaction story and record evidence in `specs/274-chat-agent-decisions/quickstart.md`

## Phase 5: User Story 3 — Preserve Stricter Authority (P2)

**Independent criterion**: Ordinary Chat confirmation succeeds, while owner/person, stale-review and read-only Playground cases retain zero-effect refusals.

- [x] T021 [P] [US3] [FR-005] [FR-008] Preserve protected finance/membership/delivery authority regressions in `packages/reality-core/tests/test_application_tools.py`
- [x] T022 [P] [US3] [FR-009] Preserve read-only Playground schema and dispatch regressions in `packages/reality-core/tests/test_playground_chat.py`
- [x] T023 [US3] [FR-007] [FR-008] Preserve owner/person/current-review enforcement and clear false attribution on safe restoration in `packages/reality-core/src/reality/tools/application.py`
- [x] T024 [US3] [FR-008] Document the agent-to-owner handoff for protected decisions in `docs/features/chat.md`
- [x] T025 [US3] [FR-005] [FR-007] [FR-008] [FR-009] Run protected-operation and Playground stories and record evidence in `specs/274-chat-agent-decisions/quickstart.md`

## Final Phase: Cross-Cutting Review

- [x] T026 [FR-004] [FR-012] Run `make docs-generate` and retain generated `apps/docs/content/tool-usage/` pages and `apps/docs/.vitepress/data/tool-usage.json`
- [x] T027 Run focused Chat, application, attribution, interaction and migration pytest suites listed in `specs/274-chat-agent-decisions/quickstart.md`
- [x] T028 Run `make docs-catalog-check`, `make spec-check`, Ruff and required PostgreSQL backend suite
- [x] T029 Review migration chain/up/down behavior and final diff against every FR/DR and the Constitution
- [x] T030 Update `specs/274-chat-agent-decisions/tasks.md`, acceptance evidence and `docs/V0_CHECKLIST.md` only after all required checks are green

## Dependencies

- T004 gates implementation.
- T005-T009 establish durable attribution before US1/US2 integration.
- US1 (T010-T015) delivers the executable Chat lifecycle.
- US2 (T016-T020) depends on US1 and durable attribution.
- US3 (T021-T025) depends on US1 confirm access but is independently verified.
- T026-T030 follow all story phases.

## Parallel Opportunities

- T005 and T006 can proceed independently before T007-T009.
- T010 and T011 cover separate provider/service surfaces.
- T016 and T017 cover separate security/telemetry surfaces.
- T021 and T022 cover protected production and Playground boundaries separately.

## Requirement Coverage

| Requirement | Test task(s) | Implementation/documentation task(s) |
|---|---|---|
| FR-001-FR-004 | T010-T011 | T012-T014, T019 |
| FR-005-FR-006 | T005, T016 | T007-T009, T018-T019 |
| FR-007-FR-010 | T011, T021-T022 | T012-T013, T023-T024 |
| FR-011-FR-012 | T010, T017 | T012, T018, T026 |
| DR-001-DR-002 | T011 | T008, T012-T014 |
| DR-003-DR-005 | T005-T006 | T007-T009, T018-T019 |

## Implementation Strategy

Implement persistence and failing proof first, then the smallest MVP (US1), then truthful attribution and protected-boundary regressions. Do not expose confirm before durable Chat attribution is available. Documentation and status close only after all gates pass.
