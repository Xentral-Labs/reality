---
description: "Requirement-traceable Reality Gap implementation tasks"
---

# Tasks: Reality Gap Workflow

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`
**Gate**: Constitution Check passed, no unresolved clarification, reviewer checklist approved

## Phase 1: Specification and Design Gates

- [x] T001 Confirm owner scope approval and close clarification markers in `specs/067-reality-gap-workflow/spec.md`
- [x] T002 Confirm all Constitution Check rows are PASS in `specs/067-reality-gap-workflow/plan.md`
- [x] T003 Run `$speckit-analyze` and resolve all CRITICAL findings across `specs/067-reality-gap-workflow/`

## Phase 2: Foundational Failing Proof and Storage

- [x] T004 [P] [US1] [FR-001] [FR-002] [FR-003] [FR-014] [DR-001] [DR-003] Add failing capture, idempotency, history, stale revision, and tenant tests in `packages/reality-core/tests/test_reality_gaps.py`
- [x] T005 [P] [US3] [FR-021] [FR-022] [FR-023] [FR-024] [FR-025] [FR-026] [DR-005] [DR-009] Add failing declarative evaluator, simulation, activation, disable, provenance, and replay tests in `packages/reality-core/tests/test_reality_gap_rules.py`
- [x] T006 [P] [US1] [DR-001] [DR-002] [DR-003] Add failing migration upgrade/downgrade and constraint proof in `packages/reality-core/tests/test_migrations.py`
- [x] T007 [US1] [DR-001] [DR-002] [DR-003] Implement RealityGap, entries, rules, outcomes, Fact provenance, constraints, and indexes in `packages/reality-core/src/reality/db/core.py` and `packages/reality-core/migrations/versions/0035_reality_gaps.py`
- [x] T008 [US1] [FR-001] [FR-002] [FR-003] [FR-014] [DR-003] Implement tenant-scoped gap capture/detail/list/history and revision primitives in `packages/reality-core/src/reality/services/reality_gaps.py`

## Phase 3: User Story 1 — Capture a Missing Answer (P1)

- [x] T009 [P] [US1] [FR-001] [FR-005] [FR-012] [DR-004] Add failing application-tool, proposal, MCP schema, Chat capture, and tenant parity tests in `packages/reality-core/tests/test_reality_gap_tools.py`
- [x] T010 [P] [US1] [FR-001] [FR-003] [FR-005] [FR-019] Add failing HTTP member capture/list/detail and foreign-context tests in `packages/reality-core/tests/test_master_data_api.py`
- [x] T011 [US1] [FR-001] [FR-005] [FR-012] [DR-004] Register gap capture/read operations in `packages/reality-core/src/reality/tools/application.py`, `packages/reality-core/src/reality/mcp/catalog.py`, and `packages/reality-core/config/command_catalog.yaml`
- [x] T012 [US1] [FR-001] [FR-003] [FR-005] [FR-019] Expose gap capture/list/detail HTTP transport in `packages/reality-core/src/reality/web/api.py`
- [x] T013 [US1] [FR-001] [FR-005] Add explicit unsupported-answer capture affordance and gap linkage to Chat in `packages/reality-core/src/reality/services/core.py` and `packages/reality-core/src/reality/web/api.py`

## Phase 4: User Story 2 — Investigate and Classify (P1)

- [x] T014 [P] [US2] [FR-004] [FR-006] [FR-007] [FR-009] [FR-016] [FR-019] Add failing guided answers, evidence bounds, recommendations, duplicate hints, stale, and privacy tests in `packages/reality-core/tests/test_reality_gaps.py`
- [x] T015 [P] [US2] [FR-005] [FR-008] [FR-009] [FR-010] [DR-004] Add failing MCP/Chat/Web recommendation and owner-decision parity tests in `packages/reality-core/tests/test_reality_gap_tools.py` and `packages/reality-core/tests/test_master_data_api.py`
- [x] T016 [US2] [FR-004] [FR-006] [FR-007] [FR-008] [FR-009] [FR-016] [FR-019] Implement guided investigation, bounded evidence, deterministic recommendation, duplicate hints, and classification in `packages/reality-core/src/reality/services/reality_gaps.py`
- [x] T017 [US2] [FR-005] [FR-010] [FR-012] [DR-004] Register investigation/recommendation/decision tools and schemas in `packages/reality-core/src/reality/tools/application.py`, `packages/reality-core/src/reality/mcp/catalog.py`, and `packages/reality-core/config/command_catalog.yaml`
- [x] T018 [US2] [FR-005] [FR-010] [FR-019] Expose shared investigation, recommendation, simulation, and owner-decision HTTP routes in `packages/reality-core/src/reality/web/api.py`

## Phase 5: User Story 3 — Implement an Accepted Gap (P1)

- [x] T019 [US3] [FR-021] [FR-022] [FR-023] [FR-024] [FR-025] Implement closed path parsing, normalization, subject resolution, simulation, and immutable rule versions in `packages/reality-core/src/reality/services/reality_gaps.py`
- [x] T020 [US3] [FR-025] [FR-026] [DR-005] Split canonical Fact persistence from transaction commit and retain manual behavior in `packages/reality-core/src/reality/services/core.py`
- [x] T021 [US3] [FR-024] [FR-025] [FR-026] [DR-008] [DR-010] Evaluate active rules after source interpretation and implement retry-safe replay/outcomes in `packages/reality-core/src/reality/services/core.py` and `packages/reality-core/src/reality/services/reality_gaps.py`
- [x] T022 [US3] [FR-011] [FR-017] [FR-018] [FR-027] [DR-006] [DR-007] Implement Fact rule preparation, developer-package generation, implementation receipts, governed terminal settlement, and shortest-link receipts in `packages/reality-core/src/reality/services/reality_gaps.py`
- [x] T023 [P] [US3] [FR-011] [FR-012] [FR-013] [FR-021] [FR-026] Add failing proposal-before-effect, owner reauthorization, stale, replay, disable, and reconciliation tests in `packages/reality-core/tests/test_reality_gap_tools.py`
- [x] T024 [US3] [FR-011] [FR-012] [FR-013] [FR-021] [FR-026] Register prepare/activate/disable/replay application tools and MCP schemas in `packages/reality-core/src/reality/tools/application.py`, `packages/reality-core/src/reality/mcp/catalog.py`, and `packages/reality-core/config/command_catalog.yaml`
- [x] T025 [US3] [FR-011] [FR-012] [FR-013] [FR-021] [FR-026] Expose owner-authorized prepare/activate/disable/replay HTTP routes in `packages/reality-core/src/reality/web/api.py`

## Phase 6: User Story 4 — Shared Queue and Complete Web Workflow (P2)

- [x] T026 [P] [US4] [FR-005] [FR-014] [FR-015] [FR-020] Add API queue filter/order/page/detail tests and Web contract tests in `packages/reality-core/tests/test_master_data_api.py` and `apps/web/scripts/ux-operational-contract.test.mjs`
- [x] T027 [P] [US4] [FR-015] [SC-007] Add bounded PostgreSQL 10k-gap/100k-entry benchmark in `packages/reality-core/tests/test_postgresql_integration.py`
- [x] T028 [US4] [FR-005] [FR-014] [FR-015] Add typed gap client, pagination, and mutation methods in `apps/web/src/api.ts`
- [x] T029 [US4] [FR-001] [FR-005] [FR-006] [FR-008] [FR-011] [FR-014] [FR-015] [FR-020] Build the responsive Open questions queue, capture dialog, detail workflow, evidence, recommendation, simulation, and actions in `apps/web/src/App.tsx`
- [x] T030 [US4] [FR-003] [FR-004] [FR-019] Add contextual missing-information entry points from Facts and Source inspector in `apps/web/src/App.tsx`
- [x] T031 [US4] [FR-020] Add complete English/German/Dutch/Spanish product copy in `apps/web/src/localization.tsx`

## Phase 7: Documentation and Cross-Cutting Verification

- [x] T032 [P] [FR-001] [FR-005] [FR-020] [DR-001] Document product behavior and terminology in `docs/features/reality_gaps.md`, `docs/WEB_SPEC.md`, and `docs/WEB_UX_MATRIX.md`
- [x] T033 [P] [FR-001] [FR-005] [FR-027] Update public application reference and capability validation in `packages/reality-core/config/command_catalog.yaml` and `packages/reality-core/tests/test_application_catalog.py`
- [x] T034 Run `make spec-check` and close traceability gaps in `specs/067-reality-gap-workflow/`
- [x] T035 Run focused Reality Gap, proposal, API, migration, and PostgreSQL tests and record evidence in `specs/067-reality-gap-workflow/quickstart.md`
- [x] T036 Run `make lint` and `make test`
- [x] T037 Run `make web-build` and `cd apps/web && npm run i18n:audit`
- [ ] T038 Perform desktop/mobile visual review of capture, queue, detail, simulation, empty, error, and confirmation states and record evidence in `specs/067-reality-gap-workflow/quickstart.md`
- [x] T039 Review final diff against the Constitution, all FR/DR requirements, migration rollback, and shortest links in `specs/067-reality-gap-workflow/quickstart.md`
- [x] T040 [P] [US2] [FR-028] [SC-008] Add a failing Chat-entrypoint and register-only Web contract test in `apps/web/scripts/ux-operational-contract.test.mjs`
- [x] T041 [US2] [FR-028] [SC-008] Replace the competing Web capture form with an explanatory register and a prefilled Ask Reality handoff in `apps/web/src/App.tsx`
- [x] T042 [US2] [FR-020] [FR-028] Localize all guided-capture copy in `apps/web/src/localization.tsx`
- [x] T043 [FR-028] [SC-008] Run Web contracts, localization audit, production build, and verify the updated live page on port 8080
- [x] T044 [US1] [FR-029] Replace serialized Reality Gap confirmation and execution receipts with business fields and a direct queue next step in `apps/web/src/App.tsx`
- [x] T045 [US2] [FR-030] Replace the exposed technical detail form with a progressive case assistant and keep implementation controls and raw history secondary in `apps/web/src/App.tsx`
- [x] T046 [US2] [FR-030] Replace abstract progress-stage names with explicit completed, current, and upcoming user actions in `apps/web/src/App.tsx`
- [x] T047 [US2] [FR-030] Render progress as an accessible responsive stepper whose sequence and state do not depend on color in `apps/web/src/App.tsx` and `apps/web/src/styles.css`
- [x] T048 [US2] [FR-031] Add failing tenant-bound source-example search and candidate extraction service tests in `packages/reality-core/tests/test_reality_gaps.py`
- [x] T049 [US2] [FR-031] Implement bounded source-example search and expose it through the Reality Gap HTTP and Web clients
- [x] T050 [US2] [FR-031] Add the in-context source finder, linked-evidence confirmation, manual fallback, localization, and Web contract coverage
- [x] T051 [US2] [FR-032] Preserve selected source-field metadata and prefill the implementation draft without overwriting operator edits
- [x] T052 [US3] [FR-033] Replace the raw simulation alert with an inline business-readable summary and bounded result details
- [x] T053 [US3] [FR-034] Add a fifth activation step, prefilled immutable rule revision flow, mandatory fresh simulation, and explicit problem acceptance
- [x] T054 [US3] [FR-035] Expose immutable rule-version history in gap detail and generating rule name/version on Facts
- [x] T055 [US3] [FR-036] Replace native rule-activation confirmation with a business-readable product dialog
- [x] T056 [US3] [FR-037] Keep current rule actions visible and move version editing into a dedicated product dialog
- [x] T057 [US4] [FR-038] Add a failing Web contract for actionable/completed separation and explicit overview/detail navigation
- [x] T058 [US4] [FR-038] Render actionable gaps as a work queue, terminal gaps as a completed table, and detail as a dedicated view with a back action
- [x] T059 [US4] [FR-038] Bound completed-table columns so long questions wrap and lifecycle actions remain visible without horizontal desktop scrolling
- [x] T060 [US4] [FR-039] Add failing service and Web contracts for tenant-scoped lifecycle counts, search, status filtering, and bounded register pages
- [x] T061 [US4] [FR-039] Extend the shared gap list service, HTTP adapter, and Web client with lifecycle, query, counts, and pagination parameters
- [x] T062 [US4] [FR-039] Replace separate overview cards with one full-width searchable and filterable paged register with open, completed, and all tabs, reusing the Open items table and control patterns

## Phase 8: User Story 5 — ERP-Ready Conditional Rules (P1)

**Goal**: Make the safe user-space rule boundary complete for common ERP conditions, line-level sources, effective time, conflicts, resumable replay, and operational support without introducing executable expressions.

**Independent test**: Activate one constant-output conditional order rule and one extracted-output line rule, evaluate positive, negative, missing, invalid, ambiguous, and conflicting sources through simulation, ingestion, and resumed replay, and reconstruct every result through HTTP, MCP, Chat, and Web.

- [x] T063 [US5] [FR-040] [FR-055] Record the approved ERP-ready scope in `specs/067-reality-gap-workflow/spec.md`, `plan.md`, `research.md`, `data-model.md`, and `contracts/http-mcp.md`
- [x] T064 [US5] [FR-040] [FR-055] Revalidate feature checklists for the expanded rule scope in `specs/067-reality-gap-workflow/checklists/`
- [x] T065 [US5] [FR-040] [DR-013] Run `$speckit-analyze` and resolve all CRITICAL expanded-scope findings in `specs/067-reality-gap-workflow/`
- [x] T066 [P] [US5] [FR-040] [FR-041] [FR-042] [FR-045] [FR-052] [FR-053] [DR-011] Add failing closed operator/type, output-mode, three-way result, effective-time, and bounds tests in `packages/reality-core/tests/test_reality_gap_rules.py`
- [x] T067 [P] [US5] [FR-043] [FR-044] [DR-012] Add failing controlled line-iteration, opaque DocumentLine resolution, per-element provenance, ambiguity, and bound tests in `packages/reality-core/tests/test_reality_gap_rules.py`
- [x] T068 [P] [US5] [FR-046] [DR-013] Add failing competing-rule conflict and no-hidden-precedence tests in `packages/reality-core/tests/test_reality_gap_rules.py`
- [x] T069 [P] [US5] [FR-047] [FR-052] [FR-055] [SC-010] Add failing deterministic replay cursor, scope binding, resume, retry, cumulative count, and 10k-source PostgreSQL tests in `packages/reality-core/tests/test_reality_gap_rules.py` and `packages/reality-core/tests/test_postgresql_integration.py`
- [x] T070 [P] [US5] [FR-048] [FR-050] [FR-054] Add failing application-tool, MCP schema, HTTP summary, owner authorization, and proposal confirmation tests in `packages/reality-core/tests/test_reality_gap_tools.py` and `packages/reality-core/tests/test_master_data_api.py`
- [x] T071 [P] [US5] [FR-049] [FR-055] Add failing migration upgrade/backfill/downgrade, rule immutability, outcome uniqueness, and index tests in `packages/reality-core/tests/test_migrations.py`
- [x] T072 [US5] [FR-040] [FR-041] [FR-043] [FR-044] [FR-049] [FR-055] Add versioned condition, output, iteration, and per-element outcome storage with compatibility backfill in `packages/reality-core/src/reality/db/core.py` and `packages/reality-core/migrations/versions/0036_erp_interpretation_rules.py`
- [x] T073 [US5] [FR-040] [FR-041] [FR-042] [FR-045] [FR-052] [FR-053] [DR-011] Implement strict condition validation, typed comparisons, explicit output modes, effective-time parsing, and shared three-way evaluation in `packages/reality-core/src/reality/services/reality_gaps.py`
- [x] T074 [US5] [FR-043] [FR-044] [DR-012] Implement bounded source-array iteration, exact same-tenant DocumentLine resolution, and per-element Fact identity in `packages/reality-core/src/reality/services/reality_gaps.py`
- [x] T075 [US5] [FR-046] [DR-013] Implement competing-rule conflict detection and durable visible conflict outcomes without Fact mutation in `packages/reality-core/src/reality/services/reality_gaps.py`
- [x] T076 [US5] [FR-047] [FR-052] [FR-055] Implement opaque scope-bound keyset replay cursors, cumulative summaries, retry, and resume in `packages/reality-core/src/reality/services/reality_gaps.py`
- [x] T077 [US5] [FR-048] [FR-050] [FR-054] Expose rule summaries, conditional drafts, cursored replay, and exact authorization through shared application and MCP tools in `packages/reality-core/src/reality/tools/application.py`, `packages/reality-core/src/reality/mcp/catalog.py`, and `packages/reality-core/config/command_catalog.yaml`
- [x] T078 [US5] [FR-048] [FR-050] [FR-054] Expose the shared conditional draft, simulation, replay, and operational summary through `packages/reality-core/src/reality/web/api.py` and `apps/web/src/api.ts`
- [x] T079 [US5] [FR-048] [FR-050] [FR-051] Build structured business-language condition/output/subject/time controls and explainable execution summaries in `apps/web/src/App.tsx`, `apps/web/src/styles.css`, and `apps/web/src/localization.tsx`
- [x] T080 [US5] [FR-040] [FR-055] [SC-009] [SC-011] Add and run shared Shopify fixtures proving simulation and replay parity in `packages/reality-core/fixtures/` and `packages/reality-core/tests/test_reality_gap_rules.py`
- [x] T081 [US5] [FR-048] [FR-051] Update durable operator guidance and troubleshooting in `docs/features/reality_gaps.md`, `docs/WEB_SPEC.md`, and `docs/WEB_UX_MATRIX.md`
- [x] T082 [US5] [FR-040] [FR-055] Run the complete US5 acceptance story and record results in `specs/067-reality-gap-workflow/quickstart.md`
- [x] T083 Run `make spec-check`, `make lint`, the complete PostgreSQL backend suite, Web/Site/Docs builds, i18n audit, and migration upgrade/downgrade checks
- [ ] T084 Perform desktop and mobile visual review of rule editing, simulation, conflicts, replay progress, summaries, empty/error/loading states, and record evidence in `specs/067-reality-gap-workflow/quickstart.md`
- [x] T085 Review the complete diff against the Constitution, FR-001–FR-055, DR-001–DR-013, migration rollback, tenant isolation, and shortest true links in `specs/067-reality-gap-workflow/quickstart.md`
- [x] T086 [US5] [FR-040] [FR-056] [FR-057] Add failing validation and evaluator truth-table tests for nested ALL/ANY groups, compatibility, depth, leaf, and empty-group bounds.
- [x] T087 [US5] [FR-040] [FR-055] [FR-056] Implement one canonical bounded condition-tree validator and evaluator shared by simulation, ingestion, and replay.
- [x] T088 [US5] [FR-057] [FR-058] Expose the canonical condition tree through application, MCP, HTTP, and Web contracts without adapter evaluation or flattening.
- [x] T089 [US5] [FR-040] [FR-051] [FR-056] Add a business-readable nested group editor with explicit ALL/ANY labels, indentation, group removal, and limits.
- [x] T090 [US5] [FR-040] [FR-055] [FR-058] Verify nested grouping end to end, update operator guidance, and record release evidence.
- [x] T091 [US1] [US4] [FR-059] Enforce concise new gap questions in the shared service and MCP schema, guide Chat to separate queue label from intended use, and clamp register text with regression coverage.

## Dependencies

- Phase 2 blocks all stories.
- US1 capture is the smallest deployable slice and blocks investigation linkage.
- US2 classification blocks implementation preparation.
- US3 rule activation blocks the complete US4 action surface.
- Tests precede the implementation they prove; schema precedes services; services precede tools; tools precede adapters.
- US5 extends US3's rule model and therefore follows the existing capture, review, and immutable-version foundation. T066–T071 are written and observed failing before T072–T079; T080–T085 are final acceptance and release gates.

## Requirement Coverage

Every FR-001–FR-039 and DR-001–DR-010 appears in at least one test or contract task and one implementation or documentation task above. T034 performs the executable coverage audit.

FR-040–FR-058, DR-011–DR-013, and SC-009–SC-011 are covered by T063–T090. T065 performs the expanded pre-implementation analysis and T085/T090 perform the final traceability review.
