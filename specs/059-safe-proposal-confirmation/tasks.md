# Tasks: Safe Proposal Confirmation

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`
**Gate**: Constitution Check passed; no unresolved clarification markers.

## Phase 1: Specification and Design Gates

- [x] T001 Confirm issues #80–#82 and all requirements are captured in `spec.md`.
- [x] T002 Confirm every Constitution Check row is PASS in `plan.md`.
- [x] T003 Analyze artifacts for coverage, ambiguity, and schema drift; resolve all critical findings.

## Phase 2: Failing Proof

- [x] T004 [US1] [FR-001–FR-005] Add claim, replay, and bounded-refusal service tests in `packages/reality-core/tests/test_application_tools.py`.
- [x] T005 [US1] [FR-001–FR-003] Add a real two-session PostgreSQL double-confirmation test in `packages/reality-core/tests/test_postgresql_integration.py`.
- [x] T006 [US2] [FR-006–FR-007] Add reservation receipt and planted verification-defect tests in `packages/reality-core/tests/test_application_tools.py`.
- [x] T007 [US3] [FR-008–FR-010] Add discovery/model-exposure/MCP tests in `packages/reality-core/tests/test_capability_guidance.py`.

## Phase 3: Single-Use Confirmation

- [x] T008 [US1] [FR-001–FR-005] Implement the tenant-scoped conditional claim and replay/refusal lifecycle in `packages/reality-core/src/reality/tools/application.py`.
- [x] T009 [US1] [DR-003] Preserve shared API, MCP, chat, and CLI execution through the same application service.

## Phase 4: Receipt and Verification

- [x] T010 [US2] [FR-006] Correlate reservation execution and return a stable receipt in `packages/reality-core/src/reality/services/core.py` and `packages/reality-core/src/reality/tools/application.py`.
- [x] T011 [US2] [FR-007] Implement tenant-scoped `proposal_execution_status` verification in `packages/reality-core/src/reality/tools/application.py`.
- [x] T012 [US2] [DR-001–DR-004] Bind the reconciliation read through MCP without schema duplication in `packages/reality-core/src/reality/mcp/catalog.py`.

## Phase 5: Contract Discovery

- [x] T013 [US3] [FR-008] Add complete confirmation and reconciliation guidance in `packages/reality-core/config/command_catalog.yaml`.
- [x] T014 [US3] [FR-009–FR-010] Keep confirm absent from model schemas and unknown/internal discovery bounded in catalogs and tests.
- [x] T015 [US2–US3] Update `apps/docs/content/concepts/agent-capabilities.md` with replay, unknown, receipt, and verification examples.

## Final Phase: Cross-Cutting Review

- [x] T900 Run spec/traceability audit and `make spec-check`.
- [x] T901 Run Ruff and the complete PostgreSQL backend suite.
- [x] T902 Run applicable API/MCP contract tests and repository packaging checks.
- [x] T903 Confirm no migration/schema expansion and document rollback handling for `executing` proposals.
- [x] T904 Review final diff against every FR/DR and linked issue acceptance criterion.
- [x] T905 Record verification in `quickstart.md` only after all required checks are green.

## Requirement Coverage

| Requirement | Test task(s) | Implementation/documentation task(s) |
|---|---|---|
| FR-001–FR-005 | T004–T005 | T008–T009 |
| FR-006–FR-007 | T006 | T010–T012, T015 |
| FR-008–FR-010 | T007 | T013–T015 |
| DR-001–DR-004 | T005–T007 | T009–T012, T015 |
