# Tasks: Composable Analytics and Reports Workspace

**Input**: approved `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/agent-tools.md`, `question-coverage.md`, `ui-review.md`.
**Gate**: Product scope approved on 2026-09-13. Design Constitution Check passes; architecture/schema accepted by the owner and reviewer checklist evaluated on 2026-09-13. Implementation and verification completed on 2026-09-13.

All repository work is English. Tests use isolated PostgreSQL and normal business services. Failures remain visible; completion markers require corresponding evidence.

## Phase 1: Specification and Design Gates

- [x] T001 Record owner product-scope approval and explicit defaults in `specs/185-analytics-workspace/spec.md` and `checklists/requirements.md`.
- [x] T002 Record architecture/schema review of trusted private identity and the additive table in `specs/185-analytics-workspace/plan.md`, `data-model.md` and `checklists/analytics-review.md`; recheck migration heads.
- [x] T003 Run consistency analysis of `specs/185-analytics-workspace/spec.md`, `plan.md`, `tasks.md` and contracts; resolve critical findings before implementation.

## Phase 2: Foundational Failing Proof and Domain

- [x] T004 [FR-001] [FR-002] [FR-003] [FR-005] [DR-004] [DR-005] Add failing strict grammar, compatibility, time-window, null/currency/unit and grain tests in `packages/reality-core/tests/test_analytics_definitions.py`.
- [x] T005 [FR-006] [FR-018] [DR-003] Add failing foreign-tenant/forged-principal, cursor, timeout/cancel and no-business-write tests in `packages/reality-core/tests/test_analytics_execution.py`.
- [x] T006 [FR-001] [FR-002] [FR-003] [FR-005] [DR-004] [DR-005] Implement strict domain schemas, time resolution and catalog descriptors in `packages/reality-core/src/reality/domain/analytics.py` and `services/analytics/catalog.py`.

## Phase 3: US1 — Shared Analytical Execution

Independent criterion: resolve a product, query customers in an ISO week, change period/grouping and inspect exact results through the same application capability.

- [x] T007 [US1] [FR-004] [FR-019] [DR-001] [DR-002] [DR-004] [DR-005] Add failing Q01–Q30 deterministic business cases in `packages/reality-core/tests/test_analytics_questions.py`, including restricted meanings, source replay/pending versions and stated-zero versus defaulted-zero coverage.
- [x] T008 [US1] [FR-007] [FR-010] [DR-001] [DR-004] Add failing contributor/population/non-additive totals tests in `packages/reality-core/tests/test_analytics_contributors.py`.
- [x] T009 [US1] [FR-001] [FR-002] [FR-003] [FR-004] [FR-005] [FR-019] [DR-001] [DR-004] [DR-005] Implement order/header/customer-history/pair perspectives and starter definitions in `packages/reality-core/src/reality/services/analytics/orders.py` and `catalog.py`; apply evidenced per-intake eligibility and preserve measure grain.
- [x] T010 [US1] [FR-004] [FR-019] [DR-001] [DR-002] [DR-004] [DR-005] Implement current operational/financial/returns providers in `packages/reality-core/src/reality/services/analytics/operations.py` and `finance.py`, extracting shared helpers from `services/delivery_reads.py` or `services/core.py` only with canonical parity proof.
- [x] T011 [US1] [FR-006] [FR-010] [FR-018] [DR-003] [DR-004] Implement owned read-only observation, aggregation/comparison/pivot totals, admission/deadline/cancellation and fresh continuation in `packages/reality-core/src/reality/services/analytics/execution.py`; cover CPU and SQL bounds.
- [x] T012 [US1] [FR-007] [DR-001] [DR-003] [DR-004] Implement scoped group/measure explanations and fresh-observation contributor navigation in `packages/reality-core/src/reality/services/analytics/contributors.py`.
- [x] T013 [US1] [FR-001] [FR-002] [FR-017] [FR-018] [DR-003] Add failing MCP/CLI/Web parity and trusted-context tests in `packages/reality-core/tests/test_analytics_adapters.py`.
- [x] T014 [US1] [FR-001] [FR-002] [FR-017] [FR-018] [DR-003] Register shared contextual read tools in `packages/reality-core/src/reality/tools/analytics.py` and `tools/application.py`; adapt `storyline/recorder.py` so tracing cannot commit the analytical transaction and metadata remains truthful.
- [x] T015 [US1] [FR-001] [FR-002] [FR-017] [FR-018] [DR-003] Expose catalog/query/contributors in `packages/reality-core/src/reality/mcp/catalog.py`, `mcp/server.py`, `cli/app.py`, `web/analytics_api.py` and route registration in `web/api.py`; classify POST diagnostics narrowly under existing company policy.
- [x] T016 [US1] [SC-005] Add and run isolated 100,000-order-line benchmark and timeout tests in `packages/reality-core/benchmarks/analytics/run.py` and `tests/test_analytics_performance.py`; record exact query set, EXPLAIN evidence and cold/warm p95 in `specs/185-analytics-workspace/verification.md`.
- [x] T017 [US1] Record the focused US1 test results and canonical regression results in `specs/185-analytics-workspace/verification.md`; do not count unavailable DB/setup failures as expected red tests.

## Phase 4: US2 — Visual Explorer

Independent criterion: build and rerun a report, change table/chart/pivot display, trace a value, and retain existing Overview/Home behavior.

- [x] T018 [US2] [FR-008] [FR-009] [FR-010] [FR-011] [FR-016] Add failing UI state/routing/presentation contracts and browser scenarios in `apps/web/scripts/analytics-contracts.test.mjs` and `analytics-browser.mjs`.
- [x] T019 [US2] [FR-008] [FR-009] [FR-011] Implement Overview/Explore/My reports shell and draft/executed lifecycle in `apps/web/src/unified/AnalyticsPage.tsx`, `unified/analytics/AnalyticsExplorer.tsx`, `unified/analytics/useAnalyticsExecution.ts`, `unified/routing.ts` and typed client methods in `api.ts`; preserve AnalyticsPreview and old explicit metric/day links.
- [x] T020 [US2] [FR-007] [FR-010] [FR-016] Implement typed table, accessible SVG bar/line and service-provided pivot presentation in `apps/web/src/unified/analytics/AnalyticsTable.tsx`, `AnalyticsChart.tsx` and `AnalyticsPivot.tsx`; contributor actions reuse `unified/Inspector.tsx`.
- [x] T021 [US2] [FR-009] [FR-016] Localize catalog labels, validation errors and controls in `apps/web/src/localization.tsx` and `packages/reality-core/src/reality/services/analytics/catalog.py`; prove supported-language coverage without untranslated dynamic fallbacks.
- [x] T022 [US2] [FR-008] [FR-011] [FR-016] Run legacy workspace, new analytics, keyboard/mobile/desktop and stale-response browser cases; record screenshots and results in `specs/185-analytics-workspace/verification.md`.

## Phase 5: US3 — Private Reports and CSV

Independent criterion: save/reopen/duplicate/rename/delete a private definition, recover retries safely, and export a complete bounded result.

- [x] T023 [US3] [FR-012] [FR-013] [FR-018] [DR-003] [DR-006] Add failing lifecycle, ownership, membership, concurrency, tombstone/retry and migration tests in `packages/reality-core/tests/test_analytics_reports.py`.
- [x] T024 [US3] [FR-014] [DR-001] [DR-003] Add failing complete-population, bounds, decimal, formula-text and observation CSV tests in `packages/reality-core/tests/test_analytics_exports.py`.
- [x] T025 [US3] [FR-012] [FR-013] [DR-003] [DR-006] Add the reviewed model in `packages/reality-core/src/reality/db/analytics.py`, metadata import in `db/core.py`, and migration `packages/reality-core/migrations/versions/0060_analytics_reports.py`; do not change existing business tables without separately proven index need.
- [x] T026 [US3] [FR-012] [FR-013] [FR-018] [DR-003] [DR-006] Implement authenticated private definition lifecycle and recovery in `packages/reality-core/src/reality/services/analytics/reports.py`; bind owner, payload, expected revision and idempotency to shared proposal services in `tools/application.py`.
- [x] T027 [US3] [FR-014] [DR-001] [DR-003] Implement bounded fresh-observation CSV in `packages/reality-core/src/reality/services/analytics/exports.py`; register its shared tool/MCP/CLI/Web adapters in the existing analytics adapter files.
- [x] T028 [US3] [FR-012] [FR-013] [FR-014] [FR-016] Implement My reports, save dialogs, retry/conflict/deletion recovery and explicit export in `apps/web/src/unified/analytics/ReportLibrary.tsx` and `AnalyticsExplorer.tsx`; add corresponding `api.ts` client methods and translations.
- [x] T029 [US3] [FR-012] [FR-013] [FR-014] [FR-016] Run browser private lifecycle and export cases in `apps/web/scripts/analytics-browser.mjs` and record results in `specs/185-analytics-workspace/verification.md`.

## Phase 6: US4 — Agent / Explorer Handoff

Independent criterion: agent → Reports → edited definition → existing chat, with trusted identity and confirmation for private changes.

- [x] T030 [US4] [FR-015] [FR-017] [FR-018] [DR-003] Add failing typed-context, foreign handoff, user-context absence and private mutation confirmation tests in `packages/reality-core/tests/test_analytics_chat.py`; add matching UI cases in `apps/web/scripts/analytics-browser.mjs`.
- [x] T031 [US4] [FR-013] [FR-015] [FR-017] [FR-018] [DR-003] Propagate trusted Principal outside arguments and validated analytics context through `packages/reality-core/src/reality/web/api.py`, `services/core.py`, `agent/mcp_chat.py`, `mcp/catalog.py` and `tools/application.py`; preserve existing commitment chat and unrelated approval behavior.
- [x] T032 [US4] [FR-015] [FR-016] Implement typed visible composer attachment and validated Open in Reports navigation in `apps/web/src/unified/context.ts`, `ChatPage.tsx`, `Shell.tsx`, `routing.ts`, `api.ts` and `analytics/AnalyticsExplorer.tsx`; reset on company switch.
- [x] T033 [US4] [FR-015] [FR-016] [FR-017] Run existing shell/chat composer and new bidirectional handoff tests; record all-language results in `specs/185-analytics-workspace/verification.md`.

## Final Phase: Documentation, Verification and Review

- [x] T034 [FR-001] [FR-017] [DR-003] Update command/resource/tenant-isolation vocabulary and German labels in `packages/reality-core/config/command_catalog.yaml`, `resource_catalog.yaml`, `tenant_isolation_catalog.yaml`; use catalog generation errors to identify every required entry rather than weakening validation.
- [x] T035 [FR-001] [FR-008] [FR-012] [FR-015] [FR-017] [DR-001] [DR-002] [DR-006] Document implemented contracts in `docs/features/analytics.md`, `docs/WEB_SPEC.md`, `docs/DATA_MODEL.md`; run `make docs-generate` and retain generated Tool Usage pages plus `apps/docs/.vitepress/data/tool-usage.json`.
- [x] T036 Run spec/traceability audit, Ruff, full PostgreSQL/migration suite, Web/Site builds, Web contract/localization/browser tests and docs catalog/build gates; record commands/outcomes in `specs/185-analytics-workspace/verification.md`.
- [x] T037 Review final diff against all FR/DR and SC criteria, architecture decision and benchmark evidence; mark `specs/185-analytics-workspace/tasks.md` and completion evidence only when required checks pass. No merge/deployment authorization is inferred.

## Dependencies and execution strategy

T001 → T002/T003 → T004–T006 → US1 → US2 → US3 → US4 → final gates. US3 persistence tests/model can run alongside presentation work after foundational execution and architecture review; US4 Principal research is already available but its code must not race with shared dispatch changes. Domain and service tasks precede tools/adapters. A working US1 slice is useful but is not completion of the approved feature.

Parallel execution examples (file-disjoint work only): US1 grammar and contributor test preparation; US2 chart/table component work after result contract stability; US3 export tests and migration tests; US4 backend context tests and browser handoff tests. Shared registry/API/localization files have one writer at a time. Research delegation has completed; this list does not itself authorize additional agent delegation.

## Requirement Coverage

| Requirement | Test tasks | Implementation tasks | Status |
|---|---|---|---|
| FR-001 | T004,T013 | T006,T009,T014,T015,T034 | Complete |
| FR-002 | T004,T013 | T006,T009,T014,T015 | Complete |
| FR-003 | T004,T007 | T006,T009 | Complete |
| FR-004 | T007 | T009,T010 | Complete |
| FR-005 | T004,T007 | T006,T009 | Complete |
| FR-006 | T005,T008 | T011 | Complete |
| FR-007 | T008,T018 | T012,T020 | Complete |
| FR-008 | T018,T022 | T019 | Complete |
| FR-009 | T018 | T019,T021 | Complete |
| FR-010 | T008,T018 | T011,T020 | Complete |
| FR-011 | T018,T022 | T019 | Complete |
| FR-012 | T023,T029 | T025,T026,T028 | Complete |
| FR-013 | T023,T030 | T025,T026,T028,T031 | Complete |
| FR-014 | T024,T029 | T027,T028 | Complete |
| FR-015 | T030,T033 | T031,T032 | Complete |
| FR-016 | T018,T022,T029,T033 | T020,T021,T028,T032 | Complete |
| FR-017 | T013,T030,T033 | T014,T015,T031 | Complete |
| FR-018 | T005,T013,T023,T030 | T011,T015,T026,T031 | Complete |
| FR-019 | T007 | T009,T010 | Complete |
| DR-001 | T007,T008,T024 | T009,T010,T012,T027 | Complete |
| DR-002 | T007 | T010 | Complete |
| DR-003 | T005,T013,T023,T024,T030 | T011,T012,T014,T015,T026,T027,T031 | Complete |
| DR-004 | T004,T007,T008 | T006,T009,T010,T011,T012 | Complete |
| DR-005 | T004,T007 | T006,T009,T010 | Complete |
| DR-006 | T023 | T025,T026,T035 | Complete |
| SC-005 | T016 | T011,T016 | Complete |

SC-001–004,006–007 are assessed by the mapped story tests, timed UI walkthrough, full requirement audit and final gates rather than separate product telemetry.

## Chart guidance defect correction (2026-09-13)

- [x] T038 [FR-010] [FR-016] Add and observe failing rendered chart regression tests in `apps/web/scripts/analytics-chart.test.mjs` for each blocker and compatible results.
- [x] T039 [FR-010] [FR-016] Distinguish blockers in `apps/web/src/unified/analytics/AnalyticsChart.tsx`; provide actionable en/de/nl/es messages in `apps/web/src/localization.tsx`.
- [x] T040 Verify frontend contracts, localization audit, web build, spec check and final diff; record evidence in `verification.md`.

Pre-implementation analysis: all correction acceptance cases map to T038/T039;
T040 covers verification. No ambiguity, schema impact, constitutional conflict or
critical finding. The correction changes guidance only, not chart eligibility.

## Recognizable Explorer controls (2026-09-13)

- [x] T041 [FR-009] [FR-016] Add browser acceptance checks for bordered 44px dataset/sort controls and keyboard selection in `apps/web/scripts/analytics-browser.mjs`; observe failure before the fix.
- [x] T042 [FR-009] [FR-016] Apply shared controls and visible select/disclosure affordances in the Explorer; verify browser flow, light/dark/mobile appearance, contracts, build, localization and spec gates.

Pre-implementation review: T041/T042 cover every presentation acceptance case;
no unresolved clarification or critical consistency/Constitution findings. Native
controls retain accessibility; data semantics and explicit execution are preserved.

## Direct chart partition selection (2026-09-13)

- [x] T043 [FR-010] [FR-016] Replace blocked-chart tests with immediate-render/partition isolation, unknown and post-bound selection tests in `analytics-chart.test.mjs`; add browser switching/query-count checks.
- [x] T044 [FR-010] [FR-016] Implement local partition buttons and localization, preserving data and execution semantics; verify contracts/browser/build/i18n/spec and local deployment.

Analysis before implementation: T043/T044 cover all new acceptance cases; explicit
supersession resolves the old narrowing requirement. No critical findings, missing
business design or unresolved clarification. No new service or persistence behavior.

## Dedicated analysis chat (2026-09-13)

- [x] T045 [FR-015] [FR-016] Extend analytics browser fixtures for existing/new sessions, creation failure, first-message attachment and history isolation; observe pre-fix failure.
- [ ] T046 [FR-015] [FR-016] Share guarded new-conversation creation in ChatPage, bind analytics context to the selected new session, relabel the Explorer action in four languages; verify browser/contracts/build/i18n/spec and local deployment.

Pre-implementation analysis: the accepted new-session requirement supersedes
attachment to the currently open conversation. T045/T046 cover success/failure and
session/tenant boundaries. No unresolved clarification or critical finding.
