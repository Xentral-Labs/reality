---
description: "Requirement-traceable Agent Capability Guidance implementation tasks"
---

# Tasks: Agent Capability Guidance

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, and `quickstart.md`
**Gate**: Constitution Check passed, owner approved scope, and no unresolved clarification

## Phase 1: Specification and Design Gates

- [x] T001 Confirm owner scope approval and close clarification markers in `specs/044-agent-capability-guidance/spec.md`
- [x] T002 Confirm every Constitution Check row is PASS in `specs/044-agent-capability-guidance/plan.md`
- [x] T003 Run `$speckit-analyze` and resolve all CRITICAL findings across `specs/044-agent-capability-guidance/`

## Phase 2: Foundational Failing Proof

- [x] T004 [P] [US1] [FR-001] [FR-002] [FR-006] [FR-007] [FR-008] [FR-009] [DR-001] [DR-002] Add four-capability completeness and twelve-case command-selection tests in `packages/reality-core/tests/test_capability_guidance.py`
- [x] T005 [P] [US3] [FR-012] [DR-004] [DR-005] Add planted missing, stale, unresolved-reference, and confirmation-drift catalog tests in `packages/reality-core/tests/test_capability_guidance.py`
- [x] T006 [P] [US2] [FR-003] [FR-004] [FR-005] [FR-010] [DR-003] Add read-only application/MCP lookup, bounded unknown, tenant, and proposal-boundary tests in `packages/reality-core/tests/test_capability_guidance.py` and `packages/reality-core/tests/test_agent_command_parity.py`
- [x] T007 [P] [US2] [FR-011] Add verification-reference and post-command re-read story assertions in `packages/reality-core/tests/test_capability_guidance.py`
- [x] T008 [P] [US1] [FR-013] Add a failing public guidance contract in `apps/docs/scripts/docs-contract.test.mjs`

## Phase 3: User Story 1 — Understand the Correct Capability (P1)

**Independent test**: Descriptions for the four initial proposal tools make all twelve observation/promise/allocation/movement cases select or decline safely.

- [x] T009 [US1] [FR-001] [FR-002] [FR-006] [FR-007] [FR-008] [FR-009] [DR-001] [DR-002] Add complete semantic guidance for the four initial commands in `packages/reality-core/config/command_catalog.yaml`
- [x] T010 [US1] [FR-001] [FR-002] [DR-004] [DR-005] Parse, normalize, and compose capability descriptions without persistence changes in `packages/reality-core/src/reality/catalogs.py`
- [x] T011 [US1] Run the four-description and twelve-case selection tests in `packages/reality-core/tests/test_capability_guidance.py` and record focused evidence in `specs/044-agent-capability-guidance/quickstart.md`

## Phase 4: User Story 2 — Review a Complete Proposal and Verification Path (P2)

**Independent test**: Chat and MCP retrieve the same read-only description, existing proposals remain confirmation-bound, and each declared read exposes the expected post-command Reality.

- [x] T012 [US2] [FR-003] [FR-004] [FR-005] [DR-003] Implement bounded `capability_describe` as a non-mutating shared application tool in `packages/reality-core/src/reality/tools/application.py`
- [x] T013 [US2] [FR-003] [FR-004] [FR-005] [DR-003] Expose the same `capability_describe` handler and schema to MCP/Chat in `packages/reality-core/src/reality/mcp/catalog.py`
- [x] T014 [US2] [FR-010] [DR-003] Extend agent parity and tenant-operation registration for the read tool in `packages/reality-core/config/tenant_isolation_catalog.yaml` and `packages/reality-core/tests/test_agent_command_parity.py`
- [x] T015 [US2] [FR-011] [DR-001] Validate declared verification reads and preserve the existing proposal/confirmation execution path in `packages/reality-core/src/reality/catalogs.py`
- [x] T016 [US2] Run application, MCP, proposal-boundary, and verification-read acceptance tests and record evidence in `specs/044-agent-capability-guidance/quickstart.md`

## Phase 5: User Story 3 — Prevent Guidance Drift (P3)

**Independent test**: Every planted incomplete, stale, unknown-reference, duplicate, or confirmation-drift contract fails before advertisement.

- [x] T017 [US3] [FR-012] [DR-004] [DR-005] Enforce completeness, uniqueness, registry-reference, read-only verification, and confirmation parity in `packages/reality-core/src/reality/catalogs.py`
- [x] T018 [US3] Run planted-drift and complete application-catalog tests in `packages/reality-core/tests/test_capability_guidance.py` and `packages/reality-core/tests/test_application_catalog.py`

## Phase 6: Public Guidance and Cross-Cutting Review

- [x] T019 [P] [US1] [FR-013] [DR-001] [DR-002] Publish the agent loop, Fact decision rule, four capability examples, and extension instructions in `apps/docs/content/concepts/agent-capabilities.md`
- [x] T020 [P] [US1] [FR-013] Link Agent capabilities from the Concepts navigation and overview in `apps/docs/.vitepress/config.mts` and `apps/docs/content/concepts/index.md`
- [x] T900 Run `make spec-check` and verify all FR/DR coverage in `specs/044-agent-capability-guidance/`
- [x] T901 Run `make lint` and the complete `make test` PostgreSQL suite
- [x] T902 Run `make docs-build` and `make web-build`
- [x] T903 Confirm no SQLAlchemy model or Alembic migration changed and document rollback evidence in `specs/044-agent-capability-guidance/quickstart.md`
- [x] T904 Review the final diff against `.specify/memory/constitution.md` and `specs/044-agent-capability-guidance/spec.md`
- [x] T905 Mark tasks complete only after every required check is green and record final results in `specs/044-agent-capability-guidance/quickstart.md`

## Dependencies

- T003 blocks implementation.
- T004–T008 are failing proofs and precede T009–T020.
- US1 establishes the canonical guidance required by US2 and US3.
- US2 and US3 may proceed independently after US1, except T015 and T017 both modify catalog validation and therefore run sequentially.
- T019 and T020 may run in parallel with backend work after the Docs contract fails as expected.
- T900–T905 run only after every story task passes independently.

## Parallel examples

- T004, T005, T006, T007, and T008 affect separable tests and may be prepared together before implementation.
- After T011, T012 and T019 can proceed independently because they affect application code and Docs content respectively.
- T013 and T020 affect separate MCP and Docs navigation files.

## Requirement Coverage

| Requirement | Test task(s) | Implementation/documentation task(s) | Status |
|---|---|---|---|
| FR-001–FR-002 | T004, T011 | T009–T010 | Complete |
| FR-003–FR-005 | T006, T016 | T012–T013 | Complete |
| FR-006–FR-009 | T004, T011 | T009 | Complete |
| FR-010 | T006, T016 | T014 | Complete |
| FR-011 | T007, T016 | T015 | Complete |
| FR-012 | T005, T018 | T017 | Complete |
| FR-013 | T008, T902 | T019–T020 | Complete |
| DR-001–DR-002 | T004, T007, T011 | T009, T015, T019 | Complete |
| DR-003 | T006, T016 | T012–T014 | Complete |
| DR-004–DR-005 | T005, T018, T903 | T010, T017 | Complete |

## Implementation strategy

The MVP is US1: four validated descriptions and the selection matrix. US2 adds the
shared read boundary and verifiable proposal context. US3 hardens catalog evolution.
Public documentation completes the feature only after executable contracts are green.
