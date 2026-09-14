---
description: "Requirement-traceable Chat master-data proposal implementation tasks"
---

# Tasks: Chat Master Data Proposals

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

## Phase 1: Specification and Design Gates

- [x] T001 Confirm product-owner scope, required fields, defaults, batching, and optional provenance in `specs/038-chat-master-data-proposals/spec.md`
- [x] T002 Confirm all Constitution Check rows and post-design re-check are PASS in `specs/038-chat-master-data-proposals/plan.md`
- [x] T003 Run `$speckit-analyze` over `specs/038-chat-master-data-proposals/spec.md`, `plan.md`, and `tasks.md` and resolve all CRITICAL findings

## Phase 2: Failing Proof

- [x] T004 [P] [US1] [FR-001] [FR-002] [FR-003] [FR-004] [FR-005] Add failing typed schema/default/optional-provenance catalog tests in `packages/reality-core/tests/test_ai_mcp.py`
- [x] T005 [US1] [FR-006] [FR-007] [FR-010] [DR-001] [DR-003] Add failing proposal-before-confirmation and confirmed shared-service creation stories for all three families in `packages/reality-core/tests/test_chat_master_data.py`
- [x] T006 [US1] [FR-008] [DR-002] [DR-004] [DR-005] Add failing atomic batch, optional lossless SourceRecord, replay, and foreign-relationship stories in `packages/reality-core/tests/test_chat_master_data.py`

## Phase 3: User Story 1 — Propose and Confirm Manual Master Data (P1)

**Independent test**: Complete no-source Party, Item, and Location requests create exact pending proposals and only create canonical records after confirmation.

- [x] T007 [US1] [FR-002] [FR-003] [FR-004] [FR-005] [FR-007] [FR-008] [DR-001] [DR-002] [DR-003] [DR-004] [DR-005] Refactor shared single-record builders and add atomic family batch services in `packages/reality-core/src/reality/services/core.py`
- [x] T008 [US1] [FR-001] [FR-006] [FR-007] [FR-008] Register family batch creation handlers through the canonical mutation boundary in `packages/reality-core/src/reality/tools/application.py`
- [x] T009 [US1] [FR-001] [FR-002] [FR-003] [FR-004] [FR-005] [FR-010] Add explicit `party_create_propose`, `item_create_propose`, and `location_create_propose` schemas in `packages/reality-core/src/reality/mcp/catalog.py`
- [x] T010 [US1] [FR-001] [FR-006] [FR-007] [DR-003] [DR-004] Extend MCP/runtime exposure and tenant-operation classification in `packages/reality-core/tests/test_ai_mcp.py`, `packages/reality-core/tests/test_chat_master_data.py`, `packages/reality-core/tests/test_application_catalog.py`, `packages/reality-core/config/tenant_isolation_catalog.yaml`, and `packages/reality-core/src/reality/catalogs.py`

## Phase 4: User Story 2 — Collect Missing Required Details (P2)

**Independent test**: Tool schemas and Copilot instructions identify missing name, role, or SKU without requiring Source or Evidence and create no proposal from incomplete tool input.

- [x] T011 [P] [US2] [FR-009] Add failing Copilot instruction and provider-schema regression assertions in `packages/reality-core/tests/test_mcp_chat.py`
- [x] T012 [US2] [FR-005] [FR-009] Clarify manual operational-reference creation, required fields, established defaults, and optional provenance in `packages/reality-core/src/reality/agent/mcp_chat.py`
- [x] T013 [US2] [FR-009] Run missing-field and import-misdirection regression tests in `packages/reality-core/tests/test_mcp_chat.py`

## Phase 5: User Story 3 — Preserve Optional Source Provenance (P3)

**Independent test**: A confirmed source-backed proposal creates one immutable lossless SourceRecord per input identity and links it through the existing shortest master-record relationship.

- [x] T014 [US3] [FR-005] [FR-007] [DR-002] Run source-backed and incomplete-source-pair service stories in `packages/reality-core/tests/test_chat_master_data.py`
- [x] T015 [US3] [FR-005] [FR-009] [DR-001] [DR-002] [DR-003] Update the durable Chat contract in `docs/features/chat.md`

## Final Phase: Cross-Cutting Verification and Review

- [x] T016 Run `make spec-check` and verify every FR/DR maps to a test and implementation/documentation task
- [x] T017 Run Ruff and the focused Chat/MCP pytest suite from `specs/038-chat-master-data-proposals/quickstart.md`
- [x] T018 Run the complete required backend PostgreSQL suite with the documented test database URL
- [x] T019 Run frontend build, i18n audit, and applicable UI tests because the shared MCP catalog is rendered in Product Web
- [x] T020 Confirm no Alembic/schema change and review rollback behavior against `specs/038-chat-master-data-proposals/plan.md`
- [x] T021 Review the final diff against the Constitution, shortest-link rule, tenant boundary, and every FR/DR; then record verification in `specs/038-chat-master-data-proposals/quickstart.md`
- [x] T022 [US1] [FR-010] Add a failing nested-proposal rendering regression in `apps/web/scripts/ux-support-trace-contract.test.mjs`, render batch records readably in `apps/web/src/App.tsx`, and rerun Product Web verification
- [x] T023 [US1] [FR-004] [FR-011] [DR-003] Add failing intra-batch Location hierarchy and approval-label regressions, resolve `ref`/`parent_ref` atomically to opaque IDs, clarify review versus execution, and rerun backend/Web verification

## Dependencies

- Phase 1 blocks all implementation.
- T004–T006 must be observed failing before T007–T010.
- T007 blocks T008; T008 blocks T009–T010.
- US2 depends on the US1 tool schemas but is independently testable through prompt and schema behavior.
- US3 depends on US1 execution and is independently testable with source-backed inputs.
- Final verification begins only after US1–US3 pass.

## Requirement Coverage

| Requirement | Test task(s) | Implementation/documentation task(s) |
|---|---|---|
| FR-001 | T004, T005, T010 | T008, T009 |
| FR-002 | T004, T005 | T007, T009 |
| FR-003 | T004, T005 | T007, T009 |
| FR-004 | T004, T005 | T007, T009 |
| FR-005 | T004, T014 | T007, T009, T012, T015 |
| FR-006 | T005, T010 | T008 |
| FR-007 | T005, T010, T014 | T007, T008 |
| FR-008 | T006 | T007, T008 |
| FR-009 | T011, T013 | T012, T015 |
| FR-010 | T004, T005 | T009 |
| FR-011 | T023 | T023 |
| DR-001 | T005, T006 | T007, T015 |
| DR-002 | T006, T014 | T007, T015 |
| DR-003 | T005, T010 | T007, T008, T015 |
| DR-004 | T006 | T007 |
| DR-005 | T006, T020 | T007 |

## Implementation Strategy

Deliver US1 first as the smallest usable slice: one typed same-family proposal, explicit
confirmation, and shared-service creation. Then harden conversational missing-field
guidance and source-backed provenance. No task expands into generic CRUD or schema work.
