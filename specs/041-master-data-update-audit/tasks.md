---
description: "Requirement-traceable auditable master-data update tasks"
---

# Tasks: Auditable Master Data Updates

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`
**Gate**: Constitution Check passed and no unresolved clarification

## Phase 1: Specification and Design Gates

- [x] T001 Confirm product scope approval and close clarification markers in `specs/041-master-data-update-audit/spec.md`
- [x] T002 Confirm all Constitution Check rows are PASS in `specs/041-master-data-update-audit/plan.md`
- [x] T003 Run `$speckit-analyze` and resolve all CRITICAL findings across `specs/041-master-data-update-audit/`

## Phase 2: Failing Audit Proof

- [x] T004 [P] [US2] [FR-008] [FR-009] [FR-011] [FR-014] Add failing effective-diff, normalization, rollback, and no-op event tests in `packages/reality-core/tests/test_master_data_update_audit.py`
- [x] T005 [P] [US2] [FR-010] Add failing activation/deactivation before/after tests in `packages/reality-core/tests/test_master_data_update_audit.py`
- [x] T006 [P] [US2] [FR-012] [DR-002] Add failing event inspection and stable-subject contract proof in `packages/reality-core/tests/test_master_data_api.py` and `apps/web/scripts/ux-support-trace-contract.test.mjs`

## Phase 3: User Story 2 — Exact History (P1)

**Independent test**: Update every supported field across the three families and inspect exact normalized diffs, action/source context, no-op behavior, and rollback.

- [x] T007 [US2] [FR-008] [FR-009] [FR-014] Implement canonical family snapshots and effective diff construction in `packages/reality-core/src/reality/services/core.py`
- [x] T008 [US2] [FR-008] [FR-010] [FR-011] Add transactional event emission, lifecycle diffs, optional `action_id`, and no-op behavior in `packages/reality-core/src/reality/services/core.py`
- [x] T009 [US2] [FR-012] [DR-002] Expose structured changes compatibly through existing event/Inspector serialization in `packages/reality-core/src/reality/web/api.py` and `apps/web/src/App.tsx` only where current generic JSON rendering is insufficient
- [x] T010 [US2] [DR-001] [DR-004] Prove immutable SourceRecord version links and unchanged operational Reality in `packages/reality-core/tests/test_master_data_update_audit.py`

## Phase 4: Failing Chat/MCP Update Proof

- [x] T011 [P] [US1] [FR-001] [FR-002] [FR-004] Add failing strict Party/Item/Location update proposal schema tests in `packages/reality-core/tests/test_ai_mcp.py`
- [x] T012 [P] [US1] [FR-003] [FR-006] [FR-007] Add failing preview, no-mutation, atomic batch, duplicate-target, stale-confirmation, and cross-tenant stories in `packages/reality-core/tests/test_chat_master_data_updates.py`
- [x] T013 [P] [US1] [FR-005] [DR-003] Add failing application-tool registration and delegation tests in `packages/reality-core/tests/test_application_tools.py`

## Phase 5: User Story 1 — Confirmed Chat Updates (P1)

**Independent test**: For each family, Chat/MCP creates a non-mutating opaque-ID proposal and one approval applies the canonical update exactly once; stale/invalid batches apply nothing.

- [x] T014 [US1] [FR-005] [FR-006] [FR-011] Add `_commit=False` support and atomic `update_parties`, `update_items`, and `update_locations` services in `packages/reality-core/src/reality/services/core.py`
- [x] T015 [US1] [FR-003] [FR-006] [FR-007] Implement reviewed snapshot revisions, exact preview, stale checks, and proposal action context in `packages/reality-core/src/reality/tools/application.py`
- [x] T016 [US1] [FR-001] [FR-002] [FR-004] Add strict `party_update_propose`, `item_update_propose`, and `location_update_propose` schemas in `packages/reality-core/src/reality/mcp/catalog.py`
- [x] T017 [US1] [FR-001] [FR-002] Add Chat discovery/opaque-identity/update guidance in `packages/reality-core/src/reality/agent/mcp_chat.py`
- [x] T018 [US1] [FR-001] [FR-004] Register update commands/events in `packages/reality-core/config/command_catalog.yaml` and `packages/reality-core/config/business_event_catalog.yaml`

## Phase 6: User Story 3 — Surface Parity (P2)

**Independent test**: Equivalent representative CLI, API, Web, and proposal updates share normalization, validation, and diff structure.

- [x] T019 [P] [US3] [FR-005] [FR-013] Add CLI/API/Web/application parity regressions in `packages/reality-core/tests/test_cli.py`, `packages/reality-core/tests/test_master_data_api.py`, and `packages/reality-core/tests/test_master_data_parity.py`
- [x] T020 [US3] [FR-005] [FR-013] Route any discovered adapter gaps through canonical update services in `packages/reality-core/src/reality/cli/app.py`, `packages/reality-core/src/reality/web/api.py`, and `apps/web/src/api.ts`
- [x] T021 [US3] [FR-012] [DR-003] Preserve tenant-scoped event inspection and browser-only presentation in `packages/reality-core/src/reality/web/api.py` and `apps/web/src/App.tsx`

## Final Phase: Cross-Cutting Verification and Review

- [x] T022 [DR-001] [DR-002] [DR-003] [DR-004] Update durable behavior in `docs/features/chat.md` and relevant machine-readable catalogs without introducing schema claims
- [x] T023 Run `make spec-check` and audit every FR/DR against tests and implementation
- [x] T024 Run `make lint` and the complete backend PostgreSQL suite with `make test`
- [x] T025 Run `make web-build`, locale audits, and applicable UI contracts
- [x] T026 Review migration chain and confirm no schema migration is required
- [x] T027 Review final diff against Constitution, shortest links, tenant boundaries, rollback, and approved scope
- [x] T028 Record acceptance results in `specs/041-master-data-update-audit/quickstart.md` and mark implementation tasks complete only after green evidence

## Dependencies and Parallel Opportunities

- T003 gates implementation.
- T004–T006 can be authored in parallel, then T007–T010 complete the audit foundation.
- T011–T013 can be authored in parallel after the audit contract is fixed; T014–T018 then complete Chat/MCP updates.
- US3 depends on the canonical audit and proposal services but its adapter test files can be prepared independently.
- Final verification depends on all story phases.

## Requirement Coverage

| Requirement | Test task(s) | Implementation/documentation task(s) |
|---|---|---|
| FR-001–FR-004 | T011–T012 | T015–T018 |
| FR-005–FR-007 | T012–T013, T019 | T014–T017, T020 |
| FR-008–FR-011 | T004–T005, T010 | T007–T008, T014 |
| FR-012 | T006 | T009, T021 |
| FR-013–FR-014 | T004, T019 | T007–T008, T020 |
| DR-001–DR-004 | T006, T010, T012, T019 | T008–T009, T014–T015, T021–T022 |

## Implementation Strategy

First deliver the independently testable event-diff foundation (US2), then confirmed Chat/MCP updates (US1), then verify adapter parity (US3). No schema migration or generic mutation abstraction is introduced.
