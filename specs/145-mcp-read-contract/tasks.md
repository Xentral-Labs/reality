# Tasks: Seven MCP Read Improvements

Input: approved spec.md and plan.md. All Constitution checks PASS. Tests before implementation.

## Phase 1: Design gates
- [x] T001 Review spec.md, plan.md and contracts/mcp-reads.md against the seven owner decisions.
- [x] T002 Run read-only cross-artifact analysis and review checklists/requirements.md.

## Phase 2: Foundational contract proofs
- [x] T003 [US3] [FR-006 FR-007 FR-008 FR-009 DR-002] Add paging, cursor, metadata, no-write and legacy tests in packages/reality-core/tests/test_mcp_read_contract.py; observe failures.
- [x] T004 [US3] [FR-006 FR-007 FR-008 FR-009 DR-002] Implement shared pagination/metadata and discovery queries in packages/reality-core/src/reality/services/read_contracts.py and services/core.py.

## Phase 3: Money and discovery
- [x] T005 [US1] [FR-001 FR-002 DR-003] Add currency/direction/tenant regressions in packages/reality-core/tests/test_mcp_read_contract.py; observe failures.
- [x] T006 [US1] [FR-001 FR-002 DR-003] Implement currency grouping and canonical ledger direction in packages/reality-core/src/reality/services/read_contracts.py and services/core.py.

## Phase 4: Operational and retained evidence
- [x] T007 [US2] [FR-003 FR-004 FR-005 DR-001 DR-002 DR-003] Add units/revisions, location/filter and closed-order/source regressions in packages/reality-core/tests/test_mcp_read_contract.py; observe failures.
- [x] T008 [US2] [FR-003 FR-004 DR-001 DR-002 DR-003] Add shared unit/revision derivations and location stock reads in packages/reality-core/src/reality/services/projections.py and services/read_contracts.py.
- [x] T009 [US2] [FR-005 DR-001 DR-002] Reuse delivery_case/document_detail for retained-order explanation in packages/reality-core/src/reality/services/projections.py.

## Phase 5: Application and MCP contracts
- [x] T010 [US3] [FR-001 FR-002 FR-003 FR-004 FR-005 FR-006 FR-007 FR-008 FR-009] Wire shared reads and public schemas/defaults in packages/reality-core/src/reality/tools/application.py and mcp/catalog.py; migrate public discovery assertions in tests/test_agent_discovery.py and prove real MCP defaults.
- [x] T011 [US3] [FR-007 FR-008 FR-009] Document output migration/persistence in docs/features/mcp_reads.md and docs/features/chat.md; update config/command_catalog.yaml guidance and tenant_isolation_catalog.yaml boundaries with executable evidence and generated apps/docs/content/catalogs/mcp-tools.md plus its de counterpart.

## Phase 6: Verification and review
- [x] T012 Run focused contract tests and record evidence in specs/145-mcp-read-contract/verification.md.
- [x] T013 Run complete backend/PostgreSQL/migration tests and Ruff, spec policy, frontend and docs quality gates; record results in verification.md.
- [x] T014 Review final diff against all FR/DR, verify no schema/authority/mutation scope expansion and update tasks.md only after checks pass.

## Dependencies and parallel opportunities
T001 → T002 → tests T003/T005/T007 → services T004/T006/T008/T009 → T010 → T011 → T012 → T013 → T014. Foundational, money and operational tests may be authored independently, but shared-file implementation stays sequential. Verification tools for backend/frontend/docs may run concurrently after implementation. No independent agent implementation is required.

## Requirement Coverage
| Requirements | Test tasks | Implementation/documentation tasks |
|---|---|---|
| FR-001 FR-002 | T005 | T006 T010 |
| FR-003 FR-004 | T007 | T008 T010 |
| FR-005 | T007 | T009 T010 |
| FR-006 | T003 | T004 T010 |
| FR-007 FR-008 FR-009 | T003 | T004 T010 T011 |
| DR-001 | T007 | T008 T009 |
| DR-002 | T003 T007 | T004 T008 T009 |
| DR-003 | T005 T007 | T006 T008 |
