---
description: "Requirement-traceable Human Chat Confirmation implementation tasks"
---

# Tasks: Human Chat Confirmation

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

## Phase 1: Specification and Design Gates

- [x] T001 Confirm requirements review and close clarification markers in `specs/278-human-chat-confirmation/spec.md`
- [x] T002 Confirm every Constitution Check row is PASS in `specs/278-human-chat-confirmation/plan.md`
- [x] T003 Run `speckit-analyze` and resolve all CRITICAL findings in `specs/278-human-chat-confirmation/`

## Phase 2: Failing Proof

- [x] T004 [P] [US1] [FR-001,FR-002,FR-003,FR-008] Change built-in production Chat catalog assertions to require read/propose access and omit every settlement tool and alias in `packages/reality-core/tests/test_mcp_chat.py`
- [x] T005 [P] [US1] [FR-003,FR-008,DR-003,DR-004] Add zero-effect refusal coverage for conversation/tool-shaped confirmation attempts in `packages/reality-core/tests/test_chat_scope_security.py`
- [x] T006 [P] [US1] [FR-004,FR-005,DR-001] Verify master-data and order proposals remain inert before confirmation in `packages/reality-core/tests/test_chat_master_data.py`, `packages/reality-core/tests/test_chat_mcp_orders.py`, and the provider boundary in `packages/reality-core/tests/test_chat_scope_security.py`
- [x] T007 [P] [US2] [FR-006,FR-007,DR-001,DR-003] Identify regression proof that Web confirmation of a Chat-origin proposal records the human and executes once in `packages/reality-core/tests/test_master_data_api.py` and `packages/reality-core/tests/test_decision_attribution.py`
- [x] T008 [P] [US3] [FR-009,FR-010,FR-011] Update Playground and operational-read catalog assertions in `packages/reality-core/tests/test_playground_chat.py` and `packages/reality-core/tests/test_mcp_chat.py`

## Phase 3: User Story 1 — Chat prepares but cannot decide (P1)

**Independent test**: A provider prepares a proposal and attempts settlement; the model was never offered the decision tool, the proposal remains pending and no target/event exists.

- [x] T009 [US1] [FR-001,FR-002,FR-003,FR-008,DR-003] Narrow ordinary built-in Chat access to read/propose while retaining dispatch enforcement in `packages/reality-core/src/reality/agent/mcp_chat.py`
- [x] T010 [US1] [FR-004,FR-005] Replace self-confirmation instructions with exact pending-proposal human handoff wording in `packages/reality-core/src/reality/agent/mcp_chat.py`
- [x] T011 [US1] [DR-001,DR-004] Verify pending proposal state, zero proposal-attributed effects and Chat interaction recording in `packages/reality-core/tests/test_chat_master_data.py` and `packages/reality-core/tests/test_chat_scope_security.py`

## Phase 4: User Story 2 — Human review remains executable (P1)

**Independent test**: A Chat-origin proposal is separately confirmed or rejected through authenticated Web review with correct human attribution, stale checks and exactly-once effect.

- [x] T012 [US2] [FR-006,FR-007,DR-001,DR-003] Preserve and verify canonical human confirmation/rejection for Chat-origin proposals in `packages/reality-core/tests/test_master_data_api.py` and `packages/reality-core/tests/test_decision_attribution.py`
- [x] T013 [US2] [FR-006,FR-007] Run focused proposal-review and decision-attribution suites and record evidence in `specs/278-human-chat-confirmation/quickstart.md`

## Phase 5: User Story 3 — Agent retains operational awareness (P2)

**Independent test**: Chat retains canonical reads and proposal preparation, reports blockers, and stops at a durable pending decision in a multi-step workflow.

- [x] T014 [US3] [FR-009,FR-010,FR-011,DR-002] Verify production read/propose and Playground read-only schemas without weakening external MCP in `packages/reality-core/tests/test_mcp_chat.py` and `packages/reality-core/tests/test_playground_chat.py`
- [x] T015 [US3] [FR-010,FR-011,DR-002] Verify canonical order readiness and inert proposal coverage in `packages/reality-core/tests/test_fulfillment_readiness.py`, `packages/reality-core/tests/test_chat_mcp_orders.py`, and `packages/reality-core/tests/scenarios/test_fulfillment_safety_parity.py`

## Final Phase: Cross-Cutting Review

- [x] T016 [FR-012] Run `make docs-catalog-check` and confirm the public MCP catalog has no generated change
- [x] T017 Run `make spec-check` and update requirement coverage below only with green evidence
- [x] T018 Run Ruff and the focused PostgreSQL Chat/security/review test suite from `specs/278-human-chat-confirmation/quickstart.md`
- [x] T019 Run the broader required backend suite and applicable Web build/tests
- [x] T020 Review final diff against the Constitution, `docs/WEB_SPEC.md`, specs 275/276 and all FR/DR requirements

## Dependencies

```text
Specification/design (T001-T003)
  → failing proof (T004-T008)
  → US1 authority boundary (T009-T011)
  → US2 human review regression (T012-T013)
  → US3 operational awareness (T014-T015)
  → final gates (T016-T020)
```

T004-T008 may be prepared in parallel. US2 and US3 may be verified in parallel after US1 establishes the access boundary.

## Requirement Coverage

| Requirement | Test task(s) | Implementation/documentation task(s) | Status |
|---|---|---|---|
| FR-001–FR-003 | T004-T006 | T009 | Complete |
| FR-004–FR-005 | T006 | T010 | Complete |
| FR-006–FR-007 | T007, T013 | T012 | Complete |
| FR-008 | T004-T005 | T009 | Complete |
| FR-009 | T008, T014 | T014 | Complete |
| FR-010–FR-011 | T008, T015 | T014-T015 | Complete |
| FR-012 | T016 | T016 | Complete |
| DR-001 | T006-T007, T011-T012 | T009, T012 | Complete |
| DR-002 | T014-T015 | T015 | Complete |
| DR-003–DR-004 | T005, T007, T011 | T009, T012 | Complete |

## Implementation Strategy

The MVP is US1: remove built-in model settlement authority and make pending human handoff truthful.
US2 proves the existing human path remains usable. US3 proves safety did not make the agent blind.
