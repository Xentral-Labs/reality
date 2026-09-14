---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: Complete Chat and MCP Command Coverage

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/agent-tools.md`, `quickstart.md`
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

## Phase 1: Specification and Design Gates

- [X] T001 Confirm owner scope approval and no clarification markers in `specs/042-chat-mcp-command-parity/spec.md`
- [X] T002 Confirm all Constitution Check rows and post-design recheck are PASS in `specs/042-chat-mcp-command-parity/plan.md`
- [X] T003 Run `speckit-analyze` and resolve all CRITICAL findings across `specs/042-chat-mcp-command-parity/`

## Phase 2: Foundational Parity Contract

- [X] T004 [P] [FR-001] [FR-019] Add failing completeness, stale, duplicate, and unjustified-classification tests in `packages/reality-core/tests/test_agent_command_parity.py`
- [X] T005 [P] [FR-017] [FR-021] Add failing compatibility and Chat/MCP shared-schema tests in `packages/reality-core/tests/test_agent_command_parity.py`
- [X] T006 [FR-001] [FR-016] Classify every command and related lifecycle service in `packages/reality-core/config/command_catalog.yaml`
- [X] T007 [FR-001] [FR-019] Implement executable agent parity validation in `packages/reality-core/src/reality/catalogs.py`
- [X] T008 [FR-017] [FR-021] Refactor tool metadata so MCP and managed Chat derive one canonical registry in `packages/reality-core/src/reality/tools/application.py` and `packages/reality-core/src/reality/mcp/catalog.py`

## Phase 3: User Story 1 — Discover and inspect business records (P1)

- [X] T009 [P] [US1] [FR-002] [FR-004] [DR-004] Add failing bounded discovery and tenant-isolation tests in `packages/reality-core/tests/test_agent_discovery.py`
- [X] T010 [P] [US1] [FR-005] [DR-006] Add failing opaque-ID/detail/current-value contract tests in `packages/reality-core/tests/test_agent_discovery.py`
- [X] T011 [US1] [FR-002] [FR-004] Implement tenant-scoped bounded discovery/detail service queries in `packages/reality-core/src/reality/services/core.py` and `packages/reality-core/src/reality/services/memberships.py`
- [X] T012 [US1] [FR-004] [FR-005] Register strict discovery schemas and handlers for every required family in `packages/reality-core/src/reality/tools/application.py` and `packages/reality-core/src/reality/mcp/catalog.py`
- [X] T013 [US1] [FR-020] Document discovery fields, defaults, maximum limits, and opaque identity use in `docs/features/chat.md`

## Phase 4: User Story 2 — Create sales and purchase orders (P1)

- [X] T014 [P] [US2] [FR-010] [DR-001] [DR-002] Add failing sales-order Source→Evidence→Reality story in `packages/reality-core/tests/test_chat_mcp_orders.py`
- [X] T015 [P] [US2] [FR-010] [FR-011] [DR-004] Add failing purchase-order, required-field, tenant, and atomic rollback stories in `packages/reality-core/tests/test_chat_mcp_orders.py`
- [X] T016 [US2] [FR-008] [FR-009] [FR-010] Implement one transactional manual-order application service in `packages/reality-core/src/reality/services/core.py`
- [X] T017 [US2] [FR-003] [FR-006] [FR-011] Register exact order proposal preview and approval output in `packages/reality-core/src/reality/tools/application.py` and `packages/reality-core/src/reality/mcp/catalog.py`
- [X] T018 [US2] [DR-001] [DR-002] [DR-005] Expose order creation through the canonical command metadata and preserve the existing explanation path in `packages/reality-core/config/command_catalog.yaml` and `docs/features/chat.md`

## Phase 5: User Story 3 — Perform warehouse and commitment operations (P1)

- [X] T019 [P] [US3] [FR-012] [DR-003] Add failing handling-unit, lot, serial, and immutable movement proposal stories in `packages/reality-core/tests/test_chat_mcp_business_commands.py`
- [X] T020 [P] [US3] [FR-007] [FR-009] [FR-012] Add failing reserve/release, commitment hold/release, document hold/release, and party delivery hold/release stories in `packages/reality-core/tests/test_chat_mcp_business_commands.py`
- [X] T021 [US3] [FR-008] [FR-012] Register existing warehouse identity and movement services as proposal handlers in `packages/reality-core/src/reality/tools/application.py`
- [X] T022 [US3] [FR-003] [FR-006] [FR-012] Register strict warehouse proposal schemas/previews in `packages/reality-core/src/reality/mcp/catalog.py`
- [X] T023 [US3] [FR-007] [FR-009] [DR-003] Register reservation release and hold/release services with stale/atomic execution checks in `packages/reality-core/src/reality/tools/application.py`

## Phase 6: User Story 4 — Perform finance and pricing operations (P2)

- [X] T024 [P] [US4] [FR-013] [DR-003] Add failing payment and immutable ledger correction/reversal proposal stories in `packages/reality-core/tests/test_chat_mcp_business_commands.py`
- [X] T025 [P] [US4] [FR-006] [FR-009] [FR-013] Add failing payment-term, price-list/tier, party assignment, and group-pricing stories in `packages/reality-core/tests/test_chat_mcp_business_commands.py`
- [X] T026 [US4] [FR-008] [FR-013] Register existing payment, term, and pricing services as proposal handlers in `packages/reality-core/src/reality/tools/application.py`
- [X] T027 [US4] [FR-003] [FR-006] [FR-013] Register strict finance/pricing schemas and exact previews in `packages/reality-core/src/reality/mcp/catalog.py`

## Phase 7: User Story 5 — Configure sources and govern membership (P2)

- [X] T028 [P] [US5] [FR-014] [DR-001] Add failing connector/source/capability lifecycle and ingestion proposal stories in `packages/reality-core/tests/test_chat_mcp_business_commands.py`
- [X] T029 [P] [US5] [FR-015] [FR-022] Add failing current-owner, token-only, reject, stale, and replay authorization stories in `packages/reality-core/tests/test_chat_mcp_business_commands.py`
- [X] T030 [US5] [FR-008] [FR-014] Register existing connector, source-system, capability, activation, and ingestion services in `packages/reality-core/src/reality/tools/application.py`
- [X] T031 [US5] [FR-006] [FR-014] Register strict source configuration proposal schemas/previews in `packages/reality-core/src/reality/mcp/catalog.py`
- [X] T032 [US5] [FR-007] [FR-015] Preserve approval-time human-owner reauthorization across Chat and MCP dispatch in `packages/reality-core/src/reality/tools/application.py` and `packages/reality-core/src/reality/mcp/catalog.py`

## Phase 8: User Story 6 — Prevent capability drift (P2)

- [X] T033 [P] [US6] [FR-018] [FR-022] Add failing proposal audit/result, error-safety, and event-linkage tests in `packages/reality-core/tests/test_agent_command_parity.py`
- [X] T034 [P] [US6] [FR-020] [FR-021] Add failing public metadata and MCP HTTP catalog contract tests in `packages/reality-core/tests/test_mcp_http_runtime.py`
- [X] T035 [US6] [FR-018] [FR-022] Harden proposal execution result/audit and safe failure behavior in `packages/reality-core/src/reality/tools/application.py`
- [X] T036 [US6] [FR-019] Wire parity validation into catalog/spec policy tests in `packages/reality-core/tests/test_catalogs.py` and `scripts/check_spec_policy.py`
- [X] T037 [US6] [FR-020] [FR-021] Update durable Chat/MCP and Web approval contracts in `docs/features/chat.md`, `docs/CLI_SPEC.md`, and `docs/WEB_SPEC.md`

## Final Phase: Cross-Cutting Verification and Review

- [X] T038 Run `make spec-check` and update requirement traceability evidence in `specs/042-chat-mcp-command-parity/quickstart.md`
- [X] T039 Run focused tests from `specs/042-chat-mcp-command-parity/quickstart.md` and record results there
- [X] T040 Run `make lint` and the complete PostgreSQL-backed `make test` suite
- [X] T041 Run `make web-build` and `cd apps/web && npm run i18n:audit`
- [X] T042 Review no-migration decision, rollback, tenant scoping, shortest links, proposal atomicity, and final diff against `specs/042-chat-mcp-command-parity/spec.md`
- [X] T043 Mark implementation tasks/checklists complete only after all required evidence is green and prepare the English pull request description

## Dependencies

- Phase 2 blocks all user stories because it defines executable eligibility and the shared registry.
- US1 supplies discovery IDs needed by US2–US5 but is independently testable as read-only capability.
- US2, US3, US4, and US5 are otherwise separable after Phase 2 and can be verified by family.
- US6 depends on all eligible mappings to prove complete parity and is the final implementation gate.

## Parallel opportunities

- Catalog parity tests (T004–T005) can be written in parallel before foundational implementation.
- Each story's first two failing-test tasks can be written in parallel.
- After Phase 2, service/schema work for US2–US5 touches shared registries and must be integrated serially even if test design is parallel.
- Documentation updates can follow stable schemas without blocking service implementation.

## Independent acceptance criteria

- **US1**: An agent discovers opaque IDs/current fields for every family with bounded tenant-safe results.
- **US2**: Sales and purchase proposals create no early effects and approval yields a complete Source→Evidence→Commitment trace.
- **US3**: A representative identity, movement, reservation/release, and hold/release action uses proposal approval and preserves immutable Reality history.
- **US4**: Payments and pricing changes use exact previews and shared finance/pricing services.
- **US5**: Source lifecycle actions are proposal-governed and membership remains current-owner-only.
- **US6**: Adding/removing/changing a canonical command or tool without matching classification/schema makes parity validation fail.

## Requirement Coverage

| Requirement | Test task(s) | Implementation/documentation task(s) |
|---|---|---|
| FR-001, FR-016, FR-019 | T004 | T006–T007, T036 |
| FR-002, FR-004, FR-005 | T009–T010 | T011–T013 |
| FR-003, FR-006, FR-007 | T015, T020, T025, T029 | T017, T022–T023, T027, T031–T032 |
| FR-008, FR-009 | T015, T020, T025 | T016, T021, T023, T026, T030 |
| FR-010, FR-011 | T014–T015 | T016–T018 |
| FR-012 | T019–T020 | T021–T023 |
| FR-013 | T024–T025 | T026–T027 |
| FR-014, FR-015 | T028–T029 | T030–T032 |
| FR-017, FR-021 | T005, T034 | T008, T037 |
| FR-018, FR-020, FR-022 | T029, T033–T034 | T013, T035, T037 |
| DR-001, DR-002 | T014–T015, T028 | T016, T018, T030 |
| DR-003 | T019, T024 | T021, T026 |
| DR-004, DR-006 | T009–T010, T015 | T011–T012, T016–T017 |
| DR-005 | T005, T014 | T008, T018, T021, T026, T030 |

## Implementation strategy

Deliver foundations and discovery first, then orders as the first mutation-complete
vertical slice. Add warehouse, finance/pricing, and source/membership families in that
order. Run the drift validator only as final parity proof after all eligible mappings
exist. Existing tools remain operational throughout additive delivery.
